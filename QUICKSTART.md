# 快速启动指南

## 前置要求

- Python 3.10+
- Node.js 16+
- npm 或 yarn

## 一键启动

### 方式1：使用启动脚本

```bash
# 终端1：启动后端
./start_backend.sh

# 终端2：启动前端
./start_frontend.sh
```

### 方式2：手动启动

#### 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r ../requirements.txt
uvicorn main:app --reload
```

#### 前端

```bash
cd frontend
npm install
npm run dev
```

## 访问系统

- 前端：http://localhost:5173
- 后端API文档：http://localhost:8000/docs
- 后端API：http://localhost:8000

## 首次使用

1. 访问 http://localhost:5173
2. 点击"立即注册"创建账户
3. 登录后进入仪表盘
4. 点击"知识库管理"上传文档（支持PDF、TXT等）
5. 点击"智能问答"开始使用RAG功能

## 功能说明

### 知识库管理
- 上传文档：支持PDF、TXT、DOC、DOCX格式
- 查看文档列表：显示所有已上传的文档
- 删除文档：删除不需要的文档

### 智能问答
- **纯向量检索**：基于向量相似度检索相关文档
- **向量标量混合检索**：
  - 选择此模式后，点击"+ 添加标量条件"
  - 输入字段名（如：date, category等）
  - 选择值类型（number/string/range）
  - 输入相应的值或范围
  - 系统将结合向量相似度和标量条件进行检索

## 常见问题

### 后端启动失败
- 检查Python版本：`python --version`（需要3.10+）
- 检查依赖安装：`pip list`
- 查看错误日志

### 前端启动失败
- 检查Node.js版本：`node --version`（需要16+）
- 删除node_modules重新安装：`rm -rf node_modules && npm install`

### 文档上传失败
- 检查文件格式是否支持
- 检查文件大小（建议小于10MB）
- 查看后端日志

### 查询无结果
- 确认已上传文档
- 检查查询文本是否与文档内容相关
- 尝试调整检索模式

## 下一步

- 集成您的加密向量检索算法（参考 `backend/ENCRYPTION_INTEGRATION.md`）
- 配置生产环境（修改SECRET_KEY、数据库等）
- 集成LLM生成更智能的回答（在 `rag_service.py` 的 `generate_answer()` 方法中）
