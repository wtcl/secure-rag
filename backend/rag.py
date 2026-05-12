from sentence_transformers import SentenceTransformer
from vector_store import vector_store

embedder = SentenceTransformer('all-MiniLM-L6-v2')

def embed_text(text: str) -> list:
    return embedder.encode(text).tolist()

def retrieve_context(query: str, top_k: int = 3):
    query_emb = embed_text(query)
    docs = vector_store.search(query_emb, top_k=top_k)
    return "\n".join([d.content for d in docs])
