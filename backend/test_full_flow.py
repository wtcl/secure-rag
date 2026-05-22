import requests
import json
import time

base_url = 'http://localhost:8000'

def test_full_flow():
    print("=== 完整的端到端测试 ===")

    # 1. 尝试注册用户（如果已存在则跳过）
    print("\n1. 用户注册")
    register_data = {
        'username': 'testuser3',  # 使用不同的用户名
        'email': 'test3@example.com',
        'password': 'testpass123'
    }
    response = requests.post(f'{base_url}/api/auth/register', json=register_data)
    print(f'注册状态码: {response.status_code}')
    if response.status_code == 200:
        print('注册成功!')
    elif response.status_code == 400 and "用户名已存在" in response.text:
        print('用户已存在，使用现有用户')
        # 切换回原来的用户名
        register_data['username'] = 'testuser3'
        register_data['email'] = 'test3@example.com'
    else:
        print(f'注册失败: {response.text}')
        return

    # 2. 用户登录
    print("\n2. 用户登录")
    login_data = {
        'username': register_data['username'],  # 使用注册时用的用户名
        'password': register_data['password']
    }
    print(f"登录数据: {login_data}")
    response = requests.post(f'{base_url}/api/auth/login', data=login_data)
    print(f'登录状态码: {response.status_code}')
    print(f'登录响应: {response.text}')
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data['access_token']
        print('登录成功!')
    else:
        print(f'登录失败: {response.text}')
        return

    headers = {'Authorization': f'Bearer {access_token}'}

    # 3. 获取用户信息
    print("\n3. 获取用户信息")
    response = requests.get(f'{base_url}/api/auth/me', headers=headers)
    print(f'获取用户信息状态码: {response.status_code}')
    if response.status_code == 200:
        user_info = response.json()
        print('用户信息:', user_info)
    else:
        print(f'获取用户信息失败: {response.text}')

    # 4. 创建测试文件
    print("\n4. 创建测试文档")
    test_content = """This is a test document for RAG system. It contains some information about artificial intelligence and machine learning. The system should be able to retrieve this information when queried about AI or machine learning topics."""
    with open('/tmp/test_doc.txt', 'w') as f:
        f.write(test_content)
    print("测试文档已创建")

    # 5. 上传文档
    print("\n5. 上传文档")
    with open('/tmp/test_doc.txt', 'rb') as f:
        files = {'file': ('test_doc.txt', f, 'text/plain')}
        response = requests.post(f'{base_url}/api/documents/upload', headers=headers, files=files)
    print(f'上传状态码: {response.status_code}')
    if response.status_code == 200:
        upload_result = response.json()
        print('上传成功:', upload_result)
    else:
        print(f'上传失败: {response.text}')
        return

    # 等待一下，让系统处理文档
    print("\n6. 等待文档处理...")
    time.sleep(2)

    # 6. 查询文档
    print("\n7. 查询文档")
    query_data = {
        'query': 'What is artificial intelligence?',
        'search_mode': 'vector_only',
        'top_k': 3
    }
    response = requests.post(f'{base_url}/api/query', headers=headers, json=query_data)
    print(f'查询状态码: {response.status_code}')
    if response.status_code == 200:
        query_result = response.json()
        print('查询结果:')
        print(f'回答: {query_result["answer"]}')
        print(f'来源: {query_result["sources"]}')
        print(f'检索模式: {query_result["search_mode"]}')
    else:
        print(f'查询失败: {response.text}')

    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_full_flow()