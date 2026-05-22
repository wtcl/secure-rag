# 安全加密向量RAG系统

一个集成了加密向量检索算法的RAG（检索增强生成）系统，支持在密文状态下进行近似最近邻检索。

## 功能特性

- 🔐 用户认证系统（登录/注册）
- 📚 知识库管理（文档上传、管理）
- 💬 智能问答界面
- 🤖 **智能问答**：大语言模型基于自身知识回答问题，可选择性参考检索内容，提供自然、专业的回答
- 📋 **内容展示**：每次回答都显示检索到的相关文档内容作为参考
- 🧠 **知识驱动**：无论是否有检索内容，都提供基于模型知识的完整回答
- 🔍 多种检索模式：
  - 纯向量检索
  - 向量标量混合检索
- 🔒 加密向量检索算法集成

## 技术栈

### 前端
- React 18 + TypeScript
- Vite
- Tailwind CSS
- Axios

### 后端
- Python 3.10+
- FastAPI
- SQLAlchemy
- LangChain
- 向量数据库（支持加密检索）

## 项目结构

```
.
├── frontend/          # React前端应用
├── backend/           # FastAPI后端服务
├── requirements.txt   # Python依赖
└── README.md
```

## 快速开始

### 后端启动

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

## 快速开始

### 1. 安装依赖

#### 后端
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r ../requirements.txt
```

#### 前端
```bash
cd frontend
npm install
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置API密钥
nano .env
```

#### 必需的环境变量
```bash
# 数据库配置
DATABASE_URL=sqlite:///./rag_system.db

# JWT配置
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI配置（推荐）
OPENAI_API_KEY=your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选：使用代理

# 可选：其他LLM提供商
ANTHROPIC_API_KEY=your-anthropic-key  # Claude
GOOGLE_API_KEY=your-google-key        # Gemini
```

### 3. 启动服务

#### 启动后端（终端1）
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端API文档：http://localhost:8000/docs

#### 启动前端（终端2）
```bash
cd frontend
npm run dev
```

前端访问地址：http://localhost:5173

### 4. 测试LLM集成

```bash
# 运行端到端测试
cd backend
python test_full_flow.py
```

## 大语言模型集成

系统支持多种LLM提供商，按优先级尝试：

### 支持的LLM提供商

系统按优先级尝试不同的LLM服务，确保高可用性：

1. **OpenAI GPT** (推荐)
   - 支持 GPT-4, GPT-3.5-turbo
   - 需要配置 `OPENAI_API_KEY`
   - 可选配置 `OPENAI_BASE_URL` 使用代理

2. **Claude (Anthropic)**
   - 使用 Claude-3-Sonnet 模型
   - 需要配置 `ANTHROPIC_API_KEY`
   - 优秀的中文理解和生成能力

3. **Gemini (Google)**
   - 使用 Gemini Pro 模型
   - 需要配置 `GOOGLE_API_KEY`
   - 强大的多模态和推理能力

4. **本地模板生成**
   - 无需网络连接的后备方案
   - 基于检索内容生成结构化回答
   - 自动提取关键信息并组织回答

3. **可扩展支持**
   - Claude (Anthropic) - 可通过环境变量配置
   - Gemini (Google) - 可通过环境变量配置
   - 其他兼容OpenAI格式的API

## 模型配置指南

### 1. OpenAI GPT (推荐)
```bash
# 获取API密钥：https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-actual-openai-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
```

### 2. Claude (Anthropic)
```bash
# 获取API密钥：https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-claude-key-here
```

### 3. Gemini (Google)
```bash
# 获取API密钥：https://makersuite.google.com/app/apikey
GOOGLE_API_KEY=your-actual-gemini-key-here
```

### 配置示例
```bash
# 复制配置模板
cp .env.example .env

# 编辑.env文件，填入您的API密钥
# 系统会按以下优先级使用模型：
# 1. OpenAI GPT → 2. Claude → 3. Gemini → 4. 本地模板
```

### 模型特点对比

| 模型服务 | 优势 | 适用场景 |
|----------|------|----------|
| **OpenAI GPT** | 强大的通用能力，稳定的API | 推荐用于生产环境 |
| **Claude** | 优秀的中文理解，安全可控 | 适合中文内容和安全要求高的场景 |
| **Gemini** | 多模态能力，推理能力强 | 适合复杂推理和多模态任务 |
| **本地模板** | 无需API密钥，离线可用 | 开发测试和无网络环境 |

### 智能问答流程

1. **查询预处理**：对用户查询进行向量化
2. **检索相关文档**：使用向量检索找到相关文档片段（可选参考）
3. **智能生成**：LLM基于自身知识回答问题，可选择性参考检索内容
4. **答案返回**：返回基于知识的回答，并展示检索到的内容供参考

### 3. 使用系统

1. **注册/登录**：访问 http://localhost:5173，注册新账户或登录
2. **上传文档**：在"知识库管理"页面上传PDF、TXT等文档
3. **智能问答**：在"智能问答"页面进行查询
   - 选择"纯向量检索"：仅基于向量相似度检索
   - 选择"向量标量混合检索"：结合向量相似度和标量条件（如日期范围、分类等）

## 集成加密向量检索算法

系统已预留了加密向量检索的接口，您可以在 `backend/encrypted_vector_search.py` 中集成您的算法：

1. **加密向量**：实现 `encrypt_vector()` 方法
2. **密文检索**：实现 `search_encrypted()` 方法，在密文状态下进行近似最近邻检索
3. **批量加密**：实现 `batch_encrypt()` 方法用于批量处理

在 `backend/rag_service.py` 中，您可以在以下位置集成加密功能：
- 文档处理时：对生成的向量进行加密存储
- 查询时：对查询向量进行加密，然后使用加密检索算法

## API接口说明

### 认证接口
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息

### 知识库接口
- `POST /api/documents/upload` - 上传文档
- `GET /api/documents` - 获取文档列表
- `GET /api/documents/{id}` - 获取文档详情
- `DELETE /api/documents/{id}` - 删除文档

### 问答接口
- `POST /api/query` - RAG查询
  - `query`: 查询文本
  - `search_mode`: "vector_only" 或 "hybrid"
  - `scalar_filters`: 标量过滤条件（混合检索时必需）
  - `top_k`: 返回结果数量

## 项目结构详解

```
.
├── backend/
│   ├── main.py                    # FastAPI主应用
│   ├── database.py                # 数据库配置
│   ├── models.py                   # 数据模型
│   ├── schemas.py                  # Pydantic模式
│   ├── auth.py                     # 认证相关
│   ├── rag_service.py              # RAG服务核心逻辑
│   └── encrypted_vector_search.py  # 加密向量检索接口（待集成）
├── frontend/
│   ├── src/
│   │   ├── pages/                  # 页面组件
│   │   │   ├── Login.tsx           # 登录页
│   │   │   ├── Register.tsx        # 注册页
│   │   │   ├── Dashboard.tsx       # 仪表盘
│   │   │   ├── KnowledgeBase.tsx   # 知识库管理
│   │   │   └── Chat.tsx            # 问答界面
│   │   ├── contexts/
│   │   │   └── AuthContext.tsx     # 认证上下文
│   │   └── App.tsx                 # 主应用组件
│   └── package.json
├── requirements.txt                # Python依赖
└── README.md
```

## 注意事项

1. **生产环境配置**：
   - 修改 `backend/auth.py` 中的 `SECRET_KEY`
   - 配置数据库连接（支持PostgreSQL、MySQL等）
   - 配置环境变量（见上方LLM配置部分）

2. **向量模型**：
   - 当前使用 `paraphrase-multilingual-MiniLM-L12-v2`
   - 可根据需要更换为其他embedding模型

3. **文件存储**：
   - 上传的文件存储在 `backend/uploads/` 目录
   - 向量数据存储在 `backend/chroma_db/` 目录

4. **性能优化**：
   - LLM调用可能需要API密钥和网络连接
   - 本地模型作为后备方案，无需网络依赖
   - 向量检索支持加密算法集成
