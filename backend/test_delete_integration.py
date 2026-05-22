#!/usr/bin/env python3
"""
End-to-end integration test:
1. Login
2. Upload a small text file
3. List documents and assert uploaded present
4. Delete that document
5. List documents and assert it's removed
"""
import requests
import time

base_url = 'http://localhost:8000'

USERNAME = 'testuser3'
PASSWORD = 'testpass123'


def login():
    r = requests.post(f'{base_url}/api/auth/login', data={'username': USERNAME, 'password': PASSWORD})
    r.raise_for_status()
    return r.json()['access_token']


def upload_file(token):
    headers = {'Authorization': f'Bearer {token}'}
    files = {'file': ('integration_test.txt', b'Hello integration test')}
    r = requests.post(f'{base_url}/api/documents/upload', headers=headers, files=files)
    r.raise_for_status()
    return r.json()


def list_documents(token):
    headers = {'Authorization': f'Bearer {token}'}
    r = requests.get(f'{base_url}/api/documents', headers=headers)
    r.raise_for_status()
    return r.json()


def delete_document(token, doc_id):
    headers = {'Authorization': f'Bearer {token}'}
    r = requests.delete(f'{base_url}/api/documents/{doc_id}', headers=headers)
    return r


if __name__ == '__main__':
    token = login()
    print('token acquired')

    uploaded = upload_file(token)
    print('uploaded:', uploaded)
    doc_id = uploaded['id']

    docs = list_documents(token)
    ids = [d['id'] for d in docs]
    assert doc_id in ids, f'uploaded doc id {doc_id} not in list {ids}'
    print('upload confirmed in list')

    r = delete_document(token, doc_id)
    print('delete status', r.status_code, r.text)
    r.raise_for_status()

    docs_after = list_documents(token)
    ids_after = [d['id'] for d in docs_after]
    assert doc_id not in ids_after, f'deleted doc id {doc_id} still in list {ids_after}'
    print('deletion confirmed; integration test passed')
