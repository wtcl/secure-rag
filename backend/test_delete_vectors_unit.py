#!/usr/bin/env python3
"""
Unit-style test for delete_document_vectors in RAGService
"""
import asyncio
import os
import sys
sys.path.append('.')

from rag_service import RAGService

async def run_tests():
    r = RAGService()
    user_id = 12345

    # Prepare metadata: two vectors from file_a, one from file_b
    file_a = '/tmp/file_a.txt'
    file_b = '/tmp/file_b.txt'
    r.user_metadata_mapping[user_id] = {
        0: {'source': file_a, 'text': 'text a0'},
        1: {'source': file_a, 'text': 'text a1'},
        2: {'source': file_b, 'text': 'text b0'}
    }

    # Prepare cumulative data with correct embedding dimension
    dim = r.vector_dim
    texts = ['text a0', 'text a1', 'text b0']
    embeddings = [[0.0]*dim for _ in texts]
    tags = [0,1,2]

    r.encrypted_search.user_cumulative_data[user_id] = {
        'texts': list(texts),
        'embeddings': list(embeddings),
        'tags': list(tags)
    }

    print('Before deletion:')
    print('metadata:', r.user_metadata_mapping[user_id])
    print('cumulative texts:', r.encrypted_search.user_cumulative_data[user_id]['texts'])
    print('cumulative tags:', r.encrypted_search.user_cumulative_data[user_id]['tags'])

    # Delete file_a
    deleted = await r.delete_document_vectors(file_a, user_id)
    print('\nDeleted count for file_a:', deleted)

    print('\nAfter deletion:')
    print('metadata:', r.user_metadata_mapping.get(user_id))
    cum = r.encrypted_search.user_cumulative_data.get(user_id)
    print('cumulative:', cum)

    # Assertions (manual)
    assert deleted == 2, f'expected 2 deleted, got {deleted}'
    remaining_meta_keys = sorted(list(r.user_metadata_mapping[user_id].keys()))
    assert remaining_meta_keys == [2], f'expected remaining metadata key [2], got {remaining_meta_keys}'
    assert cum is not None
    assert cum['texts'] == ['text b0'] or cum['tags'] == [2]

    # Delete non-existent file
    deleted2 = await r.delete_document_vectors('/tmp/nonexistent.txt', user_id)
    print('\nDeleted count for nonexistent:', deleted2)
    assert deleted2 == 0

    print('\nAll unit checks passed!')

if __name__ == '__main__':
    asyncio.run(run_tests())
