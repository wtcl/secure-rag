import numpy as np
import pickle
from typing import List
from sklearn.metrics.pairwise import cosine_similarity

def encrypt_vector(vec: List[float]) -> bytes:
    """模拟加密：实际替换为你的加密方案"""
    arr = np.array(vec, dtype=np.float32)
    return pickle.dumps(arr)

def encrypted_similarity_search(
    encrypted_query: bytes,
    encrypted_corpus: List[bytes],
    top_k: int = 4
) -> List[int]:
    """模拟密文检索（实际应避免解密）"""
    query = pickle.loads(encrypted_query)
    corpus = [pickle.loads(e) for e in encrypted_corpus]
    sims = cosine_similarity([query], corpus)[0]
    top_indices = sims.argsort()[-top_k:][::-1].tolist()
    return top_indices
