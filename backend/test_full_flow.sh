#!/bin/bash

BASE_URL="http://localhost:8000"

echo "=== 完整的端到端测试 ==="

# 1. 注册用户
echo -e "\n1. 用户注册"
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "testpass123"}')

echo "注册响应: $REGISTER_RESPONSE"

# 2. 用户登录
echo -e "\n2. 用户登录"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123")

echo "登录响应: $LOGIN_RESPONSE"

# 提取token
ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
echo "Access Token: ${ACCESS_TOKEN:0:50}..."

if [ -n "$ACCESS_TOKEN" ]; then
    # 3. 获取用户信息
    echo -e "\n3. 获取用户信息"
    ME_RESPONSE=$(curl -s -X GET "$BASE_URL/api/auth/me" \
      -H "Authorization: Bearer $ACCESS_TOKEN")

    echo "用户信息响应: $ME_RESPONSE"

    # 4. 创建测试文件
    echo -e "\n4. 创建测试文档"
    echo "This is a test document for RAG system. It contains some information about artificial intelligence and machine learning. The system should be able to retrieve this information when queried." > /tmp/test_doc.txt

    # 5. 上传文档
    echo -e "\n5. 上传文档"
    UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/api/documents/upload" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -F "file=@/tmp/test_doc.txt")

    echo "上传响应: $UPLOAD_RESPONSE"

    # 6. 查询文档
    echo -e "\n6. 查询文档"
    QUERY_RESPONSE=$(curl -s -X POST "$BASE_URL/api/query" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"query": "What is artificial intelligence?", "search_mode": "vector_only", "top_k": 3}')

    echo "查询响应: $QUERY_RESPONSE"

else
    echo "无法获取access token"
fi

echo -e "\n测试完成!"