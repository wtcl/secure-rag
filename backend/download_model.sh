#!/bin/bash
# 下载 SentenceTransformer 模型到本地
# 使用国内镜像源（hf-mirror.com）

set -e

MODEL_NAME="paraphrase-multilingual-MiniLM-L12-v2"
LOCAL_DIR="./models"

echo "Downloading model $MODEL_NAME to $LOCAL_DIR using hf-mirror.com..."

# 设置 Hugging Face 镜像源
export HF_ENDPOINT="https://hf-mirror.com"

# 激活虚拟环境（如果存在）
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
fi

# 下载模型
python -c "
from sentence_transformers import SentenceTransformer
import os
os.makedirs('$LOCAL_DIR', exist_ok=True)
print('Downloading model...')
model = SentenceTransformer('$MODEL_NAME', cache_folder='$LOCAL_DIR')
print('Model downloaded successfully!')
print('Model path:', '$LOCAL_DIR/$MODEL_NAME')
"

echo "Model downloaded to $LOCAL_DIR/$MODEL_NAME"