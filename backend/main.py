import asyncio
import json
import logging
import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional

try:
    from dotenv import load_dotenv

    _backend_dir = Path(__file__).resolve().parent
    load_dotenv(_backend_dir / ".env")
    load_dotenv(_backend_dir.parent / ".env")
except ImportError:
    pass

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import uvicorn

logger = logging.getLogger("secure_rag.api")

from database import SessionLocal, engine, Base
from models import User, Document
from schemas import (
    UserCreate, UserResponse, Token, DocumentCreate, DocumentResponse,
    QueryRequest, QueryResponse
)
from auth import get_current_user, create_access_token, verify_password, get_password_hash
from rag_service import RAGService
from encrypted_vector_search import EncryptedVectorSearch

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(title="安全加密向量RAG系统")


@app.on_event("startup")
async def _configure_secure_rag_logging():
    """验收用：保证 secure_rag 命名空间日志以 INFO 输出到终端。"""
    log = logging.getLogger("secure_rag")
    log.setLevel(logging.INFO)
    if not log.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        )
        log.addHandler(handler)
    log.propagate = False


# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# 依赖注入：获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

rag_service = RAGService()
encrypted_search = EncryptedVectorSearch()

# 后台任务管理：task_id -> {status, summary}
rebuild_tasks: Dict[str, Dict] = {}

# 任务状态持久化文件
TASKS_CACHE_DIR = os.path.join(os.path.dirname(__file__), 'vector_cache')
os.makedirs(TASKS_CACHE_DIR, exist_ok=True)
TASKS_CACHE_PATH = os.path.join(TASKS_CACHE_DIR, 'rebuild_tasks.json')

# 并发控制：重建时同时处理的用户数量
CONCURRENCY_LIMIT = 3

# 保护重建任务结构的锁
rebuild_tasks_lock = asyncio.Lock()

def _load_tasks_from_disk():
    try:
        if os.path.exists(TASKS_CACHE_PATH):
            with open(TASKS_CACHE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
    except Exception as e:
        print(f'Failed to load rebuild tasks from disk: {e}')
    return {}

def _save_tasks_to_disk():
    try:
        with open(TASKS_CACHE_PATH, 'w', encoding='utf-8') as f:
            json.dump(rebuild_tasks, f, ensure_ascii=False)
    except Exception as e:
        print(f'Failed to save rebuild tasks to disk: {e}')

# 初始化时尝试加载持久化任务状态
try:
    disk_tasks = _load_tasks_from_disk()
    if disk_tasks:
        rebuild_tasks.update(disk_tasks)
except Exception:
    pass

async def _run_rebuild_all(task_id: str):
    """后台协程：并发为所有用户重建索引并更新任务状态。"""
    async with rebuild_tasks_lock:
        rebuild_tasks[task_id] = {"status": "running", "summary": []}
        _save_tasks_to_disk()

    db = SessionLocal()
    try:
        users = db.query(User).all()

        sem = asyncio.Semaphore(CONCURRENCY_LIMIT)

        async def _process_user(u):
            entry = {"user_id": u.id, "username": u.username, "status": "started"}
            async with rebuild_tasks_lock:
                rebuild_tasks[task_id]["summary"].append(entry)
                _save_tasks_to_disk()

            documents = db.query(Document).filter(Document.user_id == u.id).all()
            file_paths = [d.file_path for d in documents]
            try:
                async with sem:
                    added = await rag_service.rebuild_user_vectors(u.id, file_paths)
                async with rebuild_tasks_lock:
                    rebuild_tasks[task_id]["summary"][-1].update({"status": "done", "documents": len(file_paths), "added_vectors": added})
                    _save_tasks_to_disk()
            except Exception as e:
                async with rebuild_tasks_lock:
                    rebuild_tasks[task_id]["summary"][-1].update({"status": "failed", "error": str(e)})
                    _save_tasks_to_disk()

        tasks = [asyncio.create_task(_process_user(u)) for u in users]
        if tasks:
            await asyncio.gather(*tasks)

        async with rebuild_tasks_lock:
            rebuild_tasks[task_id]["status"] = "completed"
            _save_tasks_to_disk()
    except Exception as e:
        async with rebuild_tasks_lock:
            rebuild_tasks[task_id]["status"] = "failed"
            rebuild_tasks[task_id]["error"] = str(e)
            _save_tasks_to_disk()
    finally:
        db.close()

# ========== 认证相关接口 ==========

@app.post("/api/auth/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户是否已存在
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 创建新用户
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """用户登录"""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user

# ========== 知识库管理接口 ==========

@app.post("/api/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传文档"""
    # 保存文件
    file_path = await rag_service.save_uploaded_file(file, current_user.id)
    
    # 处理文档（提取文本、生成向量）
    document_info = await rag_service.process_document(file_path, current_user.id)
    
    # 保存文档记录到数据库
    db_document = Document(
        filename=file.filename,
        file_path=file_path,
        file_size=document_info.get("file_size", 0),
        user_id=current_user.id,
        doc_metadata=document_info.get("metadata", {})
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)

    logger.info(
        "[文档预处理] 上传成功并已触发解析与入库 user_id=%s filename=%s doc_id=%s path=%s",
        current_user.id,
        file.filename,
        db_document.id,
        file_path,
    )

    return db_document

@app.get("/api/documents", response_model=List[DocumentResponse])
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的所有文档"""
    documents = db.query(Document).filter(Document.user_id == current_user.id).all()
    return documents

@app.get("/api/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单个文档信息"""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    return document

@app.delete("/api/documents/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除文档"""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 删除向量数据（按文件路径删除）
    await rag_service.delete_document_vectors(document.file_path, current_user.id)
    
    # 删除文件
    import os
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    db.delete(document)
    db.commit()
    return {"message": "文档已删除"}


@app.post("/api/rebuild_vectors")
async def rebuild_vectors(
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rebuild in-memory vector indices for the current user from stored documents.

    This reads the user's documents from the database and reprocesses each file
    to recreate embeddings and in-memory indices. Useful after a backend restart
    or index loss.
    """
    target_user_id = current_user.id
    # 如果提供了 user_id 参数，只有管理员可为任意用户重建
    if user_id is not None:
        # 简单管理员检查：用户名为 'admin' 或 用户ID 为 1
        if not (current_user.username == 'admin' or current_user.id == 1):
            raise HTTPException(status_code=403, detail="仅管理员可为其他用户重建索引")
        target_user_id = user_id

    documents = db.query(Document).filter(Document.user_id == target_user_id).all()
    file_paths = [d.file_path for d in documents]
    added = await rag_service.rebuild_user_vectors(target_user_id, file_paths)
    return {"message": "rebuild_completed", "user_id": target_user_id, "documents": len(file_paths), "added_vectors": added}


@app.post("/api/rebuild_all_vectors")
async def rebuild_all_vectors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rebuild vectors for all users in the system (no admin required).

    WARNING: this will process every stored document and may take time depending
    on the number of users/documents.
    """
    # 启动后台任务并立即返回 task_id
    task_id = str(uuid.uuid4())
    loop = asyncio.get_event_loop()
    loop.create_task(_run_rebuild_all(task_id))
    return {"message": "rebuild_all_started", "task_id": task_id}


@app.get("/api/rebuild_status/{task_id}")
async def rebuild_status(task_id: str):
    task = rebuild_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return task

# ========== 问答接口 ==========

@app.post("/api/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """RAG查询接口"""
    logger.info(
        "[RAG] 收到问答请求 user_id=%s mode=%s top_k=%s query_preview=%s",
        current_user.id,
        request.search_mode,
        request.top_k or 5,
        (request.query or "")[:120],
    )
    # 根据检索模式和时间范围选择不同的检索方法
    if request.search_mode == "vector_only" and not request.time_range:
        # 纯向量检索（无时间过滤）
        results = await rag_service.vector_search(
            query=request.query,
            user_id=current_user.id,
            top_k=request.top_k or 5
        )
    elif request.search_mode == "hybrid" or request.time_range:
        # 向量标量混合检索（支持时间范围过滤）
        # 如果提供了时间范围，将其转换为标量过滤条件
        scalar_filters = request.scalar_filters or {}
        if request.time_range:
            # 时间范围：{"start_days": 0, "end_days": 365}
            start_days = request.time_range.get("start_days", 0)
            end_days = request.time_range.get("end_days", 999999)  # 默认包含所有未来日期
            scalar_filters["time_range"] = {"min": start_days, "max": end_days}
        
        results = await rag_service.hybrid_search(
            query=request.query,
            user_id=current_user.id,
            scalar_filters=scalar_filters,
            top_k=request.top_k or 5
        )
    else:
        raise HTTPException(status_code=400, detail="不支持的检索模式")
    
    # 生成回答
    answer = await rag_service.generate_answer(
        query=request.query,
        context=results
    )

    # 去重参考文档（按出现顺序保留）
    seen = set()
    unique_sources: List[str] = []
    for r in results:
        src = r.get("source", "")
        if src and src not in seen:
            seen.add(src)
            unique_sources.append(src)
    
    logger.info(
        "[RAG] 回答已生成 user_id=%s 检索片段数=%d 独立来源数=%d answer_len=%d",
        current_user.id,
        len(results),
        len(unique_sources),
        len(answer or ""),
    )

    return QueryResponse(
        answer=answer,
        sources=unique_sources,
        search_mode=request.search_mode
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
