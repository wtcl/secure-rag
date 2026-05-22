#!/usr/bin/env python3
"""
Diagnostic script for retrieval failures for a specific user.
- Finds user in DB and prints id
- Lists user's documents from DB
- Calls API login and /api/query to see retrieval response
"""
import sys
sys.path.append('.')
from database import SessionLocal
from models import User, Document
import requests

USERNAME = 'zyd'
PASSWORD = '123456'
BASE = 'http://localhost:8000'


def inspect_db_user(username):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            print(f'User {username} not found in DB')
            return None
        print('DB user:', {'id': user.id, 'username': user.username, 'email': user.email})
        docs = db.query(Document).filter(Document.user_id == user.id).all()
        print(f'Found {len(docs)} documents for user {username}')
        for d in docs:
            print('-', {'id': d.id, 'filename': d.filename, 'file_path': d.file_path, 'doc_metadata': d.doc_metadata})
        return user.id
    finally:
        db.close()


def api_login(username, password):
    r = requests.post(f'{BASE}/api/auth/login', data={'username': username, 'password': password})
    print('login status', r.status_code, r.text)
    if r.status_code != 200:
        return None
    return r.json()['access_token']


def api_query(token, query_text='测试'):
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    payload = {'query': query_text, 'search_mode': 'vector_only', 'top_k': 5}
    r = requests.post(f'{BASE}/api/query', headers=headers, json=payload)
    print('/api/query status', r.status_code)
    try:
        print('response:', r.json())
    except Exception:
        print('response text:', r.text)
    return r


if __name__ == '__main__':
    uid = inspect_db_user(USERNAME)
    token = api_login(USERNAME, PASSWORD)
    if token:
        api_query(token, query_text='Hello')
