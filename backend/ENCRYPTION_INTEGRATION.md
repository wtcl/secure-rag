# 加密向量检索算法集成指南

本文档说明如何将您的加密向量检索算法集成到RAG系统中。

## 接口说明

您的加密算法需要实现 `EncryptedVectorSearch` 类中的以下方法：

### 1. `encrypt_vector(vector: np.ndarray) -> Any`

**功能**：加密单个向量

**参数**：
- `vector`: 原始向量（numpy数组）

**返回**：加密后的向量（格式由您的算法决定）

**示例**：
```python
def encrypt_vector(self, vector: np.ndarray) -> Any:
    # 实现您的加密算法
    encrypted = your_encryption_algorithm(vector)
    return encrypted
```

### 2. `search_encrypted(query_vector, encrypted_vectors, top_k) -> List[Dict]`

**功能**：在加密向量中搜索近似最近邻

**参数**：
- `query_vector`: 查询向量（可能是加密的，取决于算法）
- `encrypted_vectors`: 加密向量列表
- `top_k`: 返回最相似的k个结果

**返回**：搜索结果列表，每个结果包含：
- `index`: 结果索引
- `score`: 相似度分数
- `encrypted_vector`: 加密向量（可选）

**示例**：
```python
def search_encrypted(
    self,
    query_vector: np.ndarray,
    encrypted_vectors: List[Any],
    top_k: int = 5
) -> List[Dict[str, Any]]:
    # 实现您的加密向量检索算法
    results = your_encrypted_search_algorithm(
        query_vector, 
        encrypted_vectors, 
        top_k
    )
    return results
```

### 3. `batch_encrypt(vectors: List[np.ndarray]) -> List[Any]`

**功能**：批量加密向量（可选，用于性能优化）

**参数**：
- `vectors`: 向量列表

**返回**：加密后的向量列表

## 集成步骤

### 步骤1：实现加密算法

在 `encrypted_vector_search.py` 中实现您的算法：

```python
class EncryptedVectorSearch:
    def __init__(self):
        # 初始化您的加密参数
        self.encryption_key = load_your_key()
        # ... 其他初始化
    
    def encrypt_vector(self, vector: np.ndarray) -> Any:
        # 您的加密实现
        pass
    
    def search_encrypted(self, ...):
        # 您的检索实现
        pass
```

### 步骤2：在RAG服务中集成

在 `rag_service.py` 中，有两个地方可以集成：

#### 位置1：文档处理时加密向量

在 `process_document()` 方法中：

```python
# 生成向量
embeddings = self.embedding_model.encode(texts).tolist()

# 加密向量（可选）
encrypted_embeddings = [
    self.encrypted_search.encrypt_vector(np.array(emb)) 
    for emb in embeddings
]

# 存储加密向量或原始向量
collection.add(
    embeddings=encrypted_embeddings,  # 或 embeddings
    ...
)
```

#### 位置2：查询时使用加密检索

在 `vector_search()` 或 `hybrid_search()` 方法中：

```python
# 生成查询向量
query_embedding = self.embedding_model.encode([query])[0]

# 加密查询向量（如果需要）
encrypted_query = self.encrypted_search.encrypt_vector(query_embedding)

# 使用加密检索
results = self.encrypted_search.search_encrypted(
    encrypted_query,
    encrypted_vectors_from_db,
    top_k
)
```

## 注意事项

1. **向量格式**：确保您的算法与numpy数组兼容
2. **性能**：考虑批量加密以提高性能
3. **存储**：决定是存储加密向量还是原始向量
4. **检索精度**：确保加密检索的精度满足需求
5. **密钥管理**：妥善管理加密密钥，不要硬编码

## 测试

集成后，建议进行以下测试：

1. 单元测试：测试加密/解密功能
2. 检索测试：验证检索结果的准确性
3. 性能测试：评估加密检索的性能影响
4. 端到端测试：完整的RAG流程测试

## 示例：简单的同态加密集成

```python
class EncryptedVectorSearch:
    def __init__(self):
        # 初始化同态加密库
        self.public_key, self.private_key = generate_keys()
    
    def encrypt_vector(self, vector: np.ndarray):
        # 使用同态加密
        encrypted = []
        for v in vector:
            encrypted.append(encrypt(v, self.public_key))
        return encrypted
    
    def search_encrypted(self, query_vector, encrypted_vectors, top_k):
        # 在密文下计算相似度
        scores = []
        for enc_vec in encrypted_vectors:
            # 使用同态运算计算相似度
            score = homomorphic_similarity(query_vector, enc_vec)
            scores.append(score)
        
        # 返回top_k结果
        top_indices = np.argsort(scores)[-top_k:][::-1]
        return [
            {"index": idx, "score": scores[idx], "encrypted_vector": encrypted_vectors[idx]}
            for idx in top_indices
        ]
```

## 支持

如有问题，请参考：
- 系统文档：`README.md`
- API文档：启动后端后访问 `http://localhost:8000/docs`
