#!/bin/bash
# 手动下载 SentenceTransformer 模型文件到本地
# 使用国内镜像源

set -e

MODEL_NAME="paraphrase-multilingual-MiniLM-L12-v2"
LOCAL_DIR="./models/$MODEL_NAME"
BASE_URL="https://hf-mirror.com/sentence-transformers/$MODEL_NAME/resolve/main"

echo "Downloading model files to $LOCAL_DIR..."

mkdir -p "$LOCAL_DIR"

# 模型文件列表（基于 SentenceTransformer 模型结构）
FILES=(
    "config_sentence_transformers.json"
    "sentence_bert_config.json"
    "config.json"
    "pytorch_model.bin"
    "tokenizer_config.json"
    "vocab.txt"
    "special_tokens_map.json"
    "tokenizer.json"
    "modules.json"
)

for file in "${FILES[@]}"; do
    echo "Downloading $file..."
    if curl -L -o "$LOCAL_DIR/$file" "$BASE_URL/$file"; then
        echo "✓ Downloaded $file"
    else
        echo "✗ Failed to download $file"
    fi
done

echo "Download complete. Check $LOCAL_DIR for files."