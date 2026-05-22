from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# 用户相关Schema
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# 文档相关Schema
class DocumentCreate(BaseModel):
    filename: str
    file_path: str

class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    file_size: int
    user_id: int
    doc_metadata: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True

# 查询相关Schema
class QueryRequest(BaseModel):
    query: str
    search_mode: str  # "vector_only" 或 "hybrid"
    scalar_filters: Optional[Dict[str, Any]] = None  # 标量查询范围，用于混合检索
    time_range: Optional[Dict[str, int]] = None  # 时间范围过滤，格式: {"start_days": 0, "end_days": 365}
    top_k: Optional[int] = 5

class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    search_mode: str
