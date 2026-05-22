import requests
import json

base_url = 'http://localhost:8000'

# 1. 注册用户
print('=== 1. 用户注册 ===')
register_data = {
    'username': 'testuser',
    'email': 'test@example.com',
    'password': 'testpass123'
}
response = requests.post(f'{base_url}/api/auth/register', json=register_data)
print(f'注册状态码: {response.status_code}')
if response.status_code == 200:
    print('注册成功!')
    print('响应:', response.json())
else:
    print(f'注册失败: {response.text}')
    exit(1)

# 2. 用户登录
print('\n=== 2. 用户登录 ===')
login_data = {
    'username': 'testuser',
    'password': 'testpass123'
}
response = requests.post(f'{base_url}/api/auth/login', data=login_data)
print(f'登录状态码: {response.status_code}')
if response.status_code == 200:
    token_data = response.json()
    access_token = token_data['access_token']
    print('登录成功!')
    print(f'Access Token: {access_token[:50]}...')
else:
    print(f'登录失败: {response.text}')
    exit(1)

# 3. 获取用户信息
print('\n=== 3. 获取用户信息 ===')
headers = {'Authorization': f'Bearer {access_token}'}
response = requests.get(f'{base_url}/api/auth/me', headers=headers)
print(f'获取用户信息状态码: {response.status_code}')
if response.status_code == 200:
    user_info = response.json()
    print('用户信息:', user_info)
else:
    print(f'获取用户信息失败: {response.text}')

print('\n认证测试完成!')