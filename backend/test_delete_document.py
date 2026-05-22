import requests
import time

base_url = 'http://localhost:8000'

def delete_last_document():
    # login
    login_data = {'username': 'testuser3', 'password': 'testpass123'}
    r = requests.post(f'{base_url}/api/auth/login', data=login_data)
    if r.status_code != 200:
        print('login failed', r.text); return
    token = r.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    # list documents
    r = requests.get(f'{base_url}/api/documents', headers=headers)
    if r.status_code != 200:
        print('list failed', r.text); return
    docs = r.json()
    if not docs:
        print('no docs')
        return
    # pick last
    doc = docs[-1]
    print('deleting', doc)
    r = requests.delete(f"{base_url}/api/documents/{doc['id']}", headers=headers)
    print('delete status', r.status_code, r.text)

if __name__ == '__main__':
    delete_last_document()
