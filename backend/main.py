import bcrypt  # 👈 必须在 passlib 之前导入！

# 预加载 bcrypt，模拟 __about__ 属性（workaround for passlib 1.7.4）
if not hasattr(bcrypt, "__about__"):
    import types
    bcrypt.__about__ = types.ModuleType("__about__")
    bcrypt.__about__.__version__ = bcrypt.__version__



from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import io
from pypdf import PdfReader
from auth import (
    create_access_token,
    get_current_user,
    authenticate_user,
    get_password_hash,
    get_db,
    oauth2_scheme
)
from models import User, SessionLocal
from rag import retrieve_context
from vector_store import vector_store
from sqlalchemy.orm import Session

app = FastAPI(title="Secure RAG with Encrypted Vectors")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/register")
def register(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    print("username = "+username+" password = "+password+" len = "+str(len(password)))
    #hashed = get_password_hash(password)
    user = User(username=username, hashed_password=password)
    db.add(user)
    db.commit()
    return {"msg": "User created"}

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/upload")
def upload_file(file: UploadFile = File(...), current_user=Depends(get_current_user)):
    content = ""
    if file.filename.endswith(".pdf"):
        pdf = PdfReader(io.BytesIO(file.file.read()))
        for page in pdf.pages:
            content += page.extract_text() or ""
    elif file.filename.endswith(".txt"):
        content = file.file.read().decode("utf-8")
    else:
        raise HTTPException(status_code=400, detail="Only PDF/TXT supported")

    chunks = [s.strip() for s in content.replace("\n", " ").split(".") if len(s.strip()) > 30]
    for chunk in chunks:
        emb = vector_store.__class__.__bases__[0].__dict__['__module__']  # dummy to avoid warning
        from .rag import embed_text
        emb = embed_text(chunk)
        vector_store.add_document(chunk, emb, {"source": file.filename})
    return {"msg": f"Uploaded {len(chunks)} chunks"}

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat(req: ChatRequest, current_user=Depends(get_current_user)):
    context = retrieve_context(req.message)
    answer = f"（Demo 模拟回答）基于知识库内容：\n{context[:400]}...\n\n回答你的问题：{req.message}"
    return {"answer": answer}
