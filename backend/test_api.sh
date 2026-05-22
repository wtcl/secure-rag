#!/bin/bash

BASE_URL="http://localhost:8000"

echo "=== 1. 用户注册 ==="
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "testpass123"}')

echo "注册响应: $REGISTER_RESPONSE"

echo -e "\n=== 2. 用户登录 ==="
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123")

echo "登录响应: $LOGIN_RESPONSE"

# 提取token
ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
echo "Access Token: ${ACCESS_TOKEN:0:50}..."

if [ -n "$ACCESS_TOKEN" ]; then
    echo -e "\n=== 3. 获取用户信息 ==="
    ME_RESPONSE=$(curl -s -X GET "$BASE_URL/api/auth/me" \
      -H "Authorization: Bearer $ACCESS_TOKEN")

    echo "用户信息响应: $ME_RESPONSE"
else
    echo "无法获取access token"
fi

echo -e "\n测试完成!"