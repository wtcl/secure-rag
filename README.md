# Secure RAG Demo

一个基于 **FastAPI + React** 的安全检索增强生成（RAG）演示系统，核心亮点是在向量存储和检索全链路中引入了**加密机制**，实现密文环境下的语义检索。

---

## 项目概述

本项目是一个概念验证（PoC），旨在探索如何在 RAG 架构中保护敏感数据的隐私安全。系统支持用户上传 PDF/TXT 文档构建知识库，通过 SentenceTransformer 生成向量嵌入，并在存储前对向量进行加密处理。检索时，查询向量同样被加密，通过密文相似度计算返回最相关的知识片段。

---

## 核心特性

- **安全向量检索**：向量在存储和检索过程中均经过加密处理，保护数据隐私
- **用户认证系统**：基于 JWT 的注册/登录功能，实现权限隔离
- **知识库管理**：支持 PDF 和 TXT 文件上传，自动切分并构建向量索引
- **RAG 对话**：基于检索到的知识库内容生成回答（当前为 Demo 模式）
- **Docker 一键部署**：前后端分离架构，支持 Docker Compose 快速启动

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | React 18 + React Router 6 + Axios |
| **后端** | FastAPI + SQLAlchemy + Uvicorn |
| **AI/向量** | Sentence-Transformers (all-MiniLM-L6-v2) + scikit-learn |
| **认证** | JWT (python-jose) + OAuth2PasswordBearer |
| **部署** | Docker + Docker Compose + Nginx |

---

## 项目结构

```
secure-rag-demo/
├── backend/              # FastAPI 后端
│   ├── main.py           # 主入口，定义 API 路由
│   ├── auth.py           # JWT 认证逻辑
│   ├── models.py         # SQLAlchemy 用户模型（SQLite）
│   ├── rag.py            # RAG 检索逻辑（嵌入 + 检索）
│   ├── vector_store.py   # 加密向量存储
│   ├── encryption_mock.py# 模拟向量加密/解密
│   └── requirements.txt  # Python 依赖
├── frontend/             # React 前端
│   ├── src/
│   │   ├── App.jsx       # 路由配置
│   │   ├── api.js        # Axios 封装
│   │   └── components/
│   │       ├── Login.jsx # 登录/注册页面
│   │       └── Chat.jsx  # 聊天/上传页面
│   └── package.json      # Node 依赖
├── docker-compose.yml    # Docker 编排
└── README.md             # 项目说明
```

---

## 快速开始

### 环境要求

- Docker & Docker Compose
- 或 Python 3.10+ + Node.js 18+

### Docker 部署（推荐）

```bash
docker-compose up --build
```

- 前端访问：http://localhost:3000
- 后端 API：http://localhost:8000

### 本地开发

**1. 启动后端**

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**2. 启动前端**

```bash
cd frontend
npm install
npm start
```

---

## 使用说明

1. **注册/登录**：访问首页，使用用户名和密码注册账号，或使用已有账号登录
2. **上传知识库**：在聊天页面上传 PDF 或 TXT 文件，系统自动构建向量索引
3. **开始对话**：输入问题，系统会检索相关知识库内容并生成回答

---

## 加密机制说明

当前实现采用 **模拟加密** 方案（使用 pickle 序列化），用于演示安全 RAG 的架构可行性：

- **存储阶段**：文档向量通过 `encrypt_vector()` 加密后存入内存
- **检索阶段**：查询向量加密后，通过 `encrypted_similarity_search()` 在密文空间计算相似度

> ⚠️ **注意**：当前加密方案仅为演示用途，不具备真正的安全性。生产环境建议替换为同态加密（如 Microsoft SEAL）或安全多方计算方案。

---

## 未来规划

- [ ] 接入真实大语言模型（如 OpenAI、Claude 或本地 LLM）
- [ ] 替换为真正的同态加密方案
- [ ] 引入持久化向量数据库（如 Milvus、Pinecone）
- [ ] 支持多用户知识库隔离
- [ ] 添加文档管理界面（删除、更新知识库）

---

## 许可证

MIT License
