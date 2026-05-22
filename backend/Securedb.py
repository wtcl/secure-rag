import hnswlib
import time
import numpy as np
import random
from typing import List, Tuple, Optional


class DCEScheme:
    def __init__(self, dim):
        self.dim = dim
        self.M1 = np.random.random([self.dim // 2 + 4, self.dim // 2 + 4])
        self.M2 = np.random.random([self.dim // 2 + 4, self.dim // 2 + 4])
        self.M3 = np.random.random([self.dim * 2 + 16, self.dim * 2 + 16])
        self.Mup = self.M3[: self.dim + 8]
        self.Mdown = self.M3[self.dim + 8:]
        self.Pai1 = [i for i in range(self.dim)]
        random.shuffle(self.Pai1)
        self.Pai2 = [i for i in range(self.dim + 8)]
        random.shuffle(self.Pai2)
        self.R1, self.R2, self.R3, self.R4 = random.random(), random.random(), random.random(), random.random()
        self.k = np.random.random(2 * self.dim + 16)
        self.k1 = np.random.random(2 * self.dim + 16)
        self.k2 = np.random.random(2 * self.dim + 16)
        self.k3 = self.k / self.k1
        self.k4 = self.k / self.k2

    def aspe_enc(self, m):
        newm = [m[i] + m[i + 1] if i % 2 == 0 else m[i - 1] - m[i] for i in
                range(len(m))]
        newm = [newm[i] for i in self.Pai1]
        rp1 = random.random() * 100
        rp2 = random.random() * 100
        r1, r2, r3 = random.random(), random.random(), random.random()
        m1 = newm[:self.dim // 2] + [rp1, -rp1, r1, r2]
        m2 = newm[self.dim // 2:] + [rp2, rp2, r3, (-np.linalg.norm(
            m) ** 2 - r1 * self.R1 - r2 * self.R2 - r3 * self.R3) / self.R4]
        newm = (self.M1.T @ m1).tolist() + (self.M2.T @ m2).tolist()
        newm = [newm[i] for i in self.Pai2]
        return newm

    def dce_enc(self, m):
        m = np.array(m)
        rup, rdown = np.random.random() * 10, np.random.random() * 10
        # rup, rdown = 1, 1
        return [rup * (m @ self.Mup + np.ones(2 * self.dim + 16)) / self.k1,
                rup * (m @ self.Mup - np.ones(2 * self.dim + 16)) / self.k2,
                rdown * (m @ self.Mdown + np.ones(
                    2 * self.dim + 16)) / self.k3, rdown * (
                        m @ self.Mdown - np.ones(
                    2 * self.dim + 16)) / self.k4]

    def aspe_trapdoor(self, q):
        q = [q[i] + q[i + 1] if i % 2 == 0 else q[i - 1] - q[i] for i in
             range(len(q))]
        q = [q[i] for i in self.Pai1]
        rq1 = random.random() * 100
        rq2 = random.random() * 100
        q1 = q[:self.dim // 2] + [rq1, rq1, self.R1, self.R2]
        q2 = q[self.dim // 2:] + [rq2, -rq2, self.R3, self.R4]
        q = (np.linalg.inv(self.M1) @ q1).tolist() + (
                np.linalg.inv(self.M2) @ q2).tolist()
        q = [-q[i] for i in self.Pai2]
        return q

    def dce_trapdoor(self, q):
        rq = random.random() * 10
        q = np.array(q + (-1 * np.array(q)).tolist())
        return rq * self.k * (np.linalg.inv(self.M3) @ q)

    def enc_database(self, m):
        ea = self.aspe_enc(m)
        ca = self.dce_enc(ea)
        return ca

    def enc_trapdoor(self, q):
        eq = self.aspe_trapdoor(q)
        tq = self.dce_trapdoor(eq)
        return tq

    def check(self, ca, cb, tq):
        return (ca[0] * cb[2] - ca[1] * cb[3]) @ tq <= 0


def encrypt_data(data, s=1024.0, beta_num=450.0):
    """
    Encrypt data using DCPE scheme
    """
    dim, size = data.shape
    encrypted_data = data.copy()

    for i in range(size):
        u = np.random.normal(0.0, 1.0, dim)
        x0 = random.random()
        x = s * beta_num * (x0 ** (1.0 / float(dim))) / 4.0
        lambda_vec = u * x / np.linalg.norm(u)
        encrypted_data[:, i] = s * data[:, i] + lambda_vec

    return encrypted_data


def siftdown(heap, startpos, pos, trapdoor, data_dce, dce_scheme):
    """
    Sift down operation for heap
    """
    newitem = heap[pos]
    while pos > startpos:
        parentpos = (pos - 1) >> 1
        parent = heap[parentpos]
        if not dce_scheme.check(data_dce[newitem], data_dce[parent], trapdoor):
            heap[pos] = parent
            pos = parentpos
            continue
        break
    heap[pos] = newitem


def siftup(heap, pos, trapdoor, data_dce, dce_scheme):
    """
    Sift up operation for heap
    """
    endpos = len(heap)
    startpos = pos
    newitem = heap[pos]
    childpos = 2 * pos + 1
    while childpos < endpos:
        rightpos = childpos + 1
        if rightpos < endpos and dce_scheme.check(data_dce[heap[childpos]],
                                                  data_dce[heap[rightpos]],
                                                  trapdoor):
            childpos = rightpos
        heap[pos] = heap[childpos]
        pos = childpos
        childpos = 2 * pos + 1
    heap[pos] = newitem
    siftdown(heap, startpos, pos, trapdoor, data_dce, dce_scheme)


def heapify(x, trapdoor, data_dce, dce_scheme):
    """
    Heapify a list
    """
    n = len(x)
    for i in range(n // 2 - 1, -1, -1):
        siftup(x, i, trapdoor, data_dce, dce_scheme)


def heappushpop(heap, item, trapdoor, data_dce, dce_scheme):
    """
    Push and pop operation for heap
    """
    if heap and dce_scheme.check(data_dce[item], data_dce[heap[0]], trapdoor):
        item = heap[0], item = item, heap[0]
        siftup(heap, 0, trapdoor, data_dce, dce_scheme)
    return item


def heap_k(data0, data1, trapdoor, data_dce, dce_scheme):
    """
    Perform heap operations for k smallest elements
    """
    heapify(data0, trapdoor, data_dce, dce_scheme)
    for num in data1:
        heappushpop(data0, num, trapdoor, data_dce, dce_scheme)


def second_search(graph_search_result, finalK, query_dce,
                  data_dce, dce_scheme, text_mapping=None):
    """
    Second stage search using heap operations
    """

    # 输入数量少于预期数量，则直接返回
    if len(graph_search_result) < finalK:
        return graph_search_result, \
               [text_mapping[idx] for idx in graph_search_result if
                idx in text_mapping]

    results_with_texts = []
    result_id0 = [int(label) for label in graph_search_result]

    sum_time0 = 0
    t0 = time.time()
    data_id1 = result_id0[:-finalK]
    data_id0 = result_id0[-finalK:]
    heap_k(data_id0, data_id1, query_dce, data_dce, dce_scheme)
    t1 = time.time()
    sum_time0 += int((t1 - t0) * 1000000)

    # Get corresponding texts if mapping is provided
    if text_mapping:
        retrieved_texts = [text_mapping[idx] for idx in data_id0 if
                           idx in text_mapping]
        results_with_texts.append(retrieved_texts)
    else:
        results_with_texts.append(data_id0)

    print(f"time0 = {sum_time0} microseconds")

    return data_id0, results_with_texts


def graph_build(data_base_source, M=40, ef_construction=600):
    """
    Build HNSW index using hnswlib with encrypted data
    """
    dim = len(data_base_source[0])
    points_num = len(data_base_source)

    # Create HNSW index
    p = hnswlib.Index(space='l2', dim=dim)
    p.init_index(max_elements=points_num, ef_construction=ef_construction, M=M)

    # Add all points to index
    t0 = time.time()
    for i, point in enumerate(data_base_source):
        p.add_items([point], [i])  # Add point with its index as label

    t1 = time.time()
    print(f"HNSW build time: {int((t1 - t0) * 1000)} ms")

    return p


def graph_search(data_query_source, hnsw, k_num, ef_search=10):
    """
    Search in HNSW index using hnswlib with encrypted queries
    """

    hnsw.set_ef(ef_search)

    print(f"Graph search = {k_num}, ef_search = {ef_search}")

    t2 = time.time()

    labels, distances = hnsw.knn_query([data_query_source], k=k_num)
    result = labels[0].tolist()

    t3 = time.time()
    print(f"Search time: {int((t3 - t2) * 1000)} ms")

    return result


class LabelTreeNode:
    """树节点类，用于标签范围搜索"""

    def __init__(self, l, r, dim, M, ef_construction, max_elements=0):
        self.l = l  # 左边界
        self.r = r  # 右边界
        self.hnsw = None  # HNSW索引
        self.children = []  # 子节点列表
        self.dim = dim
        self.M = M
        self.ef_construction = ef_construction
        # 初始化HNSW索引
        self.hnsw = hnswlib.Index(space='l2', dim=dim)
        self.hnsw.init_index(max_elements=max_elements,
                             ef_construction=ef_construction, M=M)

    def __repr__(self):
        return f"[{self.l}, {self.r}] points={self.hnsw.get_current_count()}"


def build_xary_tree(l, r, dim, M, ef_construction, X_arg=2):
    """构建X叉标签树"""
    # 先创建一个最大元素数为0的节点
    node = LabelTreeNode(l, r, dim, M, ef_construction, max_elements=0)
    if l == r:
        return node

    total = r - l + 1
    step = (total + X_arg - 1) // X_arg
    for i in range(X_arg):
        cl = l + i * step
        cr = min(l + (i + 1) * step - 1, r)
        if cl > cr:
            break
        node.children.append(
            build_xary_tree(cl, cr, dim, M, ef_construction, X_arg))
    return node


def insert_vector_to_tree(node, vec, global_label, tag):
    """向树中插入向量"""
    if not node or tag < node.l or tag > node.r:
        return
    node.hnsw.add_items([vec], [global_label])
    for child in node.children:
        insert_vector_to_tree(child, vec, global_label, tag)


def collect_hit_nodes(node, ql, qr, hit_list):
    """收集命中节点"""
    if not node:
        return
    # 完全包含于查询区间
    if node.l >= ql and node.r <= qr:
        hit_list.append(node)
        return
    # 否则递归子节点
    for child in node.children:
        collect_hit_nodes(child, ql, qr, hit_list)


def range_search_query(node, query, ql, qr, single_k, ef_search, rate_k=10):
    """范围搜索查询"""
    hit = []
    collect_hit_nodes(node, ql, qr, hit)
    all_results = []  # (distance, label)

    for tree_node in hit:
        current_count = tree_node.hnsw.get_current_count()
        # 动态调整ef_search，确保不超过当前节点的数据点数
        adjusted_ef = min(ef_search, max(10, current_count))
        tree_node.hnsw.set_ef(adjusted_ef)
        # 调整single_k，确保不超过当前节点的数据点数
        adjusted_k = min(single_k, current_count)
        try:
            labels, distances = tree_node.hnsw.knn_query([query], k=adjusted_k)
            for i in range(len(labels[0])):
                all_results.append((distances[0][i], int(labels[0][i])))
        except RuntimeError as e:
            print(f"Error during knn_query: {e}")
            print(
                f"Node range: [{tree_node.l}, {tree_node.r}], points: {current_count}")
            continue

    # 按距离排序并取前k个
    all_results.sort(key=lambda x: x[0])
    topk = [label for _, label in all_results[:rate_k]]
    return topk


def count_nodes_vector(node, tags, cnt_map):
    """统计每个节点即将插入的向量个数"""
    if not node:
        return
    cnt = cnt_map.get(node, 0)
    l, r = node.l, node.r
    # 单遍扫描 tags，O(points_num) 总计
    for tag in tags:
        if l <= tag <= r:
            cnt += 1
    cnt_map[node] = cnt
    # 递归孩子
    for child in node.children:
        count_nodes_vector(child, tags, cnt_map)


def rebuild_hnsw_with_count(node, cnt_map, dim, M, ef_construction):
    """按统计结果重新给每个节点分配正确 max_elements"""
    if not node:
        return
    exact_cnt = cnt_map.get(node, 0)

    # 保存当前节点中的数据
    old_labels = []
    old_points = []
    current_count = node.hnsw.get_current_count()
    if current_count > 0:
        # 由于hnswlib不直接支持导出所有数据，这里我们假设数据已提前缓存
        pass

    # 释放原来的索引并创建新的
    node.hnsw = hnswlib.Index(space='l2', dim=dim)
    node.hnsw.init_index(max_elements=exact_cnt,
                         ef_construction=ef_construction, M=M)
    # 递归孩子
    for child in node.children:
        rebuild_hnsw_with_count(child, cnt_map, dim, M, ef_construction)


class PPRFANNVectorDatabase:
    """
    基于PPRFANN算法的加密向量数据库类，支持标签范围搜索
    """

    def __init__(self, dim: int, M=40, ef_construction=600, ef_search=10,
                 s=1024, beta_num=1, rate=10, X_arg=2, single_k=5, rate_k=10):
        self.dim = dim
        self.M = M
        self.ef_construction = ef_construction
        self.ef_search = ef_search
        self.s = s
        self.beta_num = beta_num
        self.rate = rate
        self.X_arg = X_arg  # X叉树的分支数
        self.single_k = single_k  # 单个HNSW搜索的k值
        self.rate_k = rate_k  # 最终返回的k值
        self.database_vectors = None
        self.texts = {}  # 存储向量ID到文本的映射
        self.label_tree_root = None  # 标签树根节点
        self.tags = []  # 每个向量对应的标签
        self.dce_scheme = None
        self.data_dce = None

    def add_texts_and_embeddings_with_tags(self, texts: List[str],
                                           embeddings: List[List[float]],
                                           tags: List[int]):
        """
        添加文本、向量嵌入和标签到数据库
        :param texts: 文本列表
        :param embeddings: 向量嵌入列表
        :param tags: 标签列表（对应每个向量的标签）
        """
        if len(texts) != len(embeddings) or len(embeddings) != len(tags):
            raise ValueError(
                "Texts, embeddings and tags must have the same length")

        # 转换为numpy数组
        embeddings_array = np.array(embeddings, dtype=np.float32)
        if embeddings_array.shape[1] != self.dim:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.dim}, got {embeddings_array.shape[1]}")

        # 存储文本映射
        for idx, text in enumerate(texts):
            self.texts[idx] = text

        # 存储标签
        self.tags = tags.copy()

        # 加密向量用于DCE操作
        self.dce_scheme = DCEScheme(self.dim)
        self.data_dce = [[] for _ in range(len(embeddings))]
        for i in range(len(embeddings)):
            self.data_dce[i] = self.dce_scheme.enc_database(embeddings[i])

        # 加密向量用于DCPE和HNSW构建
        database_array = embeddings_array.T
        encrypted_database = encrypt_data(database_array, s=self.s,
                                          beta_num=self.beta_num).T

        # 构建标签树
        min_tag = min(tags)
        max_tag = max(tags)
        self.label_tree_root = build_xary_tree(min_tag, max_tag, self.dim,
                                               self.M, self.ef_construction,
                                               self.X_arg)

        # 统计各节点所需容量
        cnt_map = {}
        count_nodes_vector(self.label_tree_root, tags, cnt_map)
        rebuild_hnsw_with_count(self.label_tree_root, cnt_map, self.dim,
                                self.M, self.ef_construction)

        # 插入数据到标签树
        t0 = time.time()
        for i, (vec, tag) in enumerate(zip(encrypted_database, tags)):
            insert_vector_to_tree(self.label_tree_root, vec, i, tag)
        t1 = time.time()
        print(
            f"Label tree build time: {int((t1 - t0) * 1000000)} microseconds")

        self.database_vectors = embeddings_array

        print(f"Added {len(texts)} vectors, texts and tags to the database")
        print(f"Database shape: {self.database_vectors.shape}")

    def range_search(self, query_embedding: List[float],
                     tag_range: Tuple[int, int], k: int = 10) -> Tuple[
        List[int], List[str]]:
        """
        在指定标签范围内搜索最相似的向量及其对应的文本
        :param query_embedding: 查询向量
        :param tag_range: 标签范围 (start_tag, end_tag)
        :param k: 返回结果数量
        :return: (向量ID列表, 对应文本列表)
        """
        if len(query_embedding) != self.dim:
            raise ValueError(
                f"Query embedding dimension mismatch: expected {self.dim}, got {len(query_embedding)}")

        if self.label_tree_root is None:
            raise ValueError(
                "Database is empty. Please add texts, embeddings and tags first.")

        # 更新k和ef_search参数
        self.rate_k = k
        self.ef_search = self.single_k

        # 加密查询向量
        query_array = np.array([query_embedding], dtype=np.float32)
        query_dce = self.dce_scheme.enc_trapdoor(query_embedding)
        query_dcpe = encrypt_data(query_array.T, s=self.s,
                                  beta_num=self.beta_num).T[0]

        # 进行范围搜索
        start_tag, end_tag = tag_range
        range_search_result = range_search_query(self.label_tree_root,
                                                 query_dcpe, start_tag,
                                                 end_tag,
                                                 self.single_k, self.ef_search,
                                                 self.rate_k)
        print("Range search result:", range_search_result)

        # 获取最终结果
        final_ids, results_with_texts = second_search(range_search_result, k,
                                                      query_dce, self.data_dce,
                                                      self.dce_scheme,
                                                      self.texts)

        return final_ids, results_with_texts[0]

    def get_text_by_id(self, vector_id: int) -> Optional[str]:
        """
        根据向量ID获取对应的文本
        :param vector_id: 向量ID
        :return: 对应的文本
        """
        return self.texts.get(vector_id, None)

    def get_vector_by_id(self, vector_id: int) -> Optional[np.ndarray]:
        """
        根据向量ID获取对应的向量
        :param vector_id: 向量ID
        :return: 对应的向量
        """
        if self.database_vectors is not None and 0 <= vector_id < len(
                self.database_vectors):
            return self.database_vectors[vector_id]
        return None


class EncryptedVectorDatabase:
    """
    密文向量数据库类，支持文本和向量的存储与检索
    """

    def __init__(self, dim: int, M=40, ef_construction=600, ef_search=100,
                 s=1024, beta_num=1, rate=10):
        self.dim = dim
        self.M = M
        self.ef_construction = ef_construction
        self.ef_search = ef_search
        self.s = s
        self.beta_num = beta_num
        self.rate = rate
        self.database_vectors = None
        self.texts = {}  # 存储向量ID到文本的映射
        self.hnsw_index = None
        self.dce_scheme = None
        self.data_dce = None

    def add_texts_and_embeddings(self, texts: List[str],
                                 embeddings: List[List[float]]):
        """
        添加文本和对应的向量嵌入到数据库
        :param texts: 文本列表
        :param embeddings: 向量嵌入列表
        """
        if len(texts) != len(embeddings):
            raise ValueError("Texts and embeddings must have the same length")

        # 转换为numpy数组
        embeddings_array = np.array(embeddings, dtype=np.float32)
        if embeddings_array.shape[1] != self.dim:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.dim}, got {embeddings_array.shape[1]}")

        # 存储文本映射
        for idx, text in enumerate(texts):
            self.texts[idx] = text

        # 加密向量用于DCE操作
        self.dce_scheme = DCEScheme(self.dim)
        self.data_dce = [[] for _ in range(len(embeddings))]
        for i in range(len(embeddings)):
            self.data_dce[i] = self.dce_scheme.enc_database(embeddings[i])

        # 加密向量用于DCPE和HNSW构建
        database_array = embeddings_array.T
        encrypted_database = encrypt_data(database_array, s=self.s,
                                          beta_num=self.beta_num).T

        # 构建HNSW索引
        self.hnsw_index = graph_build(encrypted_database.tolist(), self.M,
                                      self.ef_construction)
        self.database_vectors = embeddings_array

        print(f"Added {len(texts)} vectors and texts to the database")
        print(f"Database shape: {self.database_vectors.shape}")

    def search(self, query_embedding: List[float], k: int = 10) -> Tuple[
        List[int], List[str]]:
        """
        搜索最相似的向量及其对应的文本
        :param query_embedding: 查询向量
        :param k: 返回结果数量
        :return: (向量ID列表, 对应文本列表)
        """
        if len(query_embedding) != self.dim:
            raise ValueError(
                f"Query embedding dimension mismatch: expected {self.dim}, got {len(query_embedding)}")

        if self.hnsw_index is None:
            raise ValueError(
                "Database is empty. Please add texts and embeddings first.")

        # 加密查询向量
        query_array = np.array([query_embedding], dtype=np.float32)
        query_dce = self.dce_scheme.enc_trapdoor(query_embedding)
        query_dcpe = encrypt_data(query_array.T, s=self.s,
                                  beta_num=self.beta_num).T[0]

        # 进行图搜索
        graph_search_result = graph_search(query_dcpe.tolist(),
                                           self.hnsw_index, self.rate * k,
                                           self.ef_search)
        print("Graph search result:", graph_search_result)

        # print("query_dce = ", query_dce)
        # print("data_dce = ", self.data_dce)
        # 获取最终结果
        final_ids, results_with_texts = second_search(graph_search_result,
                                                      k,
                                                      query_dce,
                                                      self.data_dce,
                                                      self.dce_scheme,
                                                      self.texts)

        return final_ids, results_with_texts[0]

    def get_text_by_id(self, vector_id: int) -> Optional[str]:
        """
        根据向量ID获取对应的文本
        :param vector_id: 向量ID
        :return: 对应的文本
        """
        return self.texts.get(vector_id, None)

    def get_vector_by_id(self, vector_id: int) -> Optional[np.ndarray]:
        """
        根据向量ID获取对应的向量
        :param vector_id: 向量ID
        :return: 对应的向量
        """
        if self.database_vectors is not None and 0 <= vector_id < len(
                self.database_vectors):
            return self.database_vectors[vector_id]
        return None


def main_ppanns_example():
    """
    示例：如何使用EncryptedVectorDatabase
    """
    print("=== 密文向量数据库示例 ===\n")

    # 创建示例数据
    dim = 128
    n = 1000  # 数据库大小
    texts = [f"这是文档{i + 1}的内容，包含一些有意义的信息。" for i in range(n)]
    embeddings = [np.random.rand(dim).astype(np.float32).tolist() for _ in
                  range(n)]

    # 初始化密文向量数据库
    db = EncryptedVectorDatabase(dim=dim)

    # 添加文本和嵌入
    print("正在添加文本和向量到数据库...")
    db.add_texts_and_embeddings(texts, embeddings)
    print("完成添加！\n")

    # 创建查询向量
    query_embedding = np.random.rand(dim).astype(np.float32).tolist()
    print(f"查询向量: {query_embedding[:10]}... (显示前10个元素)")

    # 执行搜索
    print("\n正在执行搜索...")
    ids, retrieved_texts = db.search(query_embedding, k=10)

    print(f"\n搜索结果 (前10个):")
    for i in range(len(retrieved_texts)):
        print(f"{i + 1}. ID: {ids[i]}, 文本: {retrieved_texts[i]}...")


def main_pprfann_example():
    """
    示例：如何使用PPRFANNVectorDatabase
    """
    print("\n=== PPRFANN向量数据库示例 ===\n")

    # 创建示例数据
    dim = 128
    n = 1000  # 数据库大小
    texts = [f"这是文档{i + 1}的内容，包含一些有意义的信息。" for i in range(n)]
    embeddings = [np.random.rand(dim).astype(np.float32).tolist() for _ in
                  range(n)]
    # 生成标签，范围从1到10000
    tags = [random.randint(1, 10000) for _ in range(n)]

    # 初始化PPRFANN向量数据库
    db = PPRFANNVectorDatabase(dim=dim, X_arg=2, single_k=10, rate_k=10)

    # 添加文本、嵌入和标签
    print("正在添加文本、向量和标签到数据库...")
    db.add_texts_and_embeddings_with_tags(texts, embeddings, tags)
    print("完成添加！\n")

    # 创建查询向量
    query_embedding = np.random.rand(dim).astype(np.float32).tolist()
    print(f"查询向量: {query_embedding[:10]}... (显示前10个元素)")

    # 执行范围搜索
    print("\n正在执行范围搜索...")
    tag_range = (1, 5000)  # 搜索标签在1到5000范围内的向量
    ids, retrieved_texts = db.range_search(query_embedding, tag_range, k=10)

    print(f"\n范围搜索结果 (前10个):")
    for i in range(len(retrieved_texts)):
        print(
            f"{i + 1}. ID: {ids[i]}, 标签: {tags[ids[i]]}, 文本: {retrieved_texts[i]}...")


if __name__ == "__main__":
    main_ppanns_example()
    main_pprfann_example()
