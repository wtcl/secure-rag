from typing import List
from pydantic import BaseModel

class Document(BaseModel):
    content: str
    metadata: dict = {}

class EncryptedVectorStore:
    def __init__(self):
        self.encrypted_embeddings = []
        self.documents = []

    def add_document(self, text: str, embedding: List[float], meta: dict = None):
        from encryption_mock import encrypt_vector
        encrypted_emb = encrypt_vector(embedding)
        self.encrypted_embeddings.append(encrypted_emb)
        self.documents.append(Document(content=text, metadata=meta or {}))

    def search(self, query_embedding: List[float], top_k: int = 3) -> List[Document]:
        from encryption_mock import encrypt_vector, encrypted_similarity_search
        encrypted_query = encrypt_vector(query_embedding)
        indices = encrypted_similarity_search(
            encrypted_query,
            self.encrypted_embeddings,
            top_k=min(top_k, len(self.documents))
        )
        return [self.documents[i] for i in indices]

vector_store = EncryptedVectorStore()
