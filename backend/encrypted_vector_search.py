"""
加密向量检索模块
集成Securedb.py中的加密向量检索算法
"""
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import os
from datetime import datetime
from Securedb import EncryptedVectorDatabase, PPRFANNVectorDatabase
import json

logger = logging.getLogger("secure_rag.encrypted")

# 本地缓存目录（用于持久化 user_cumulative_data）
CACHE_DIR = os.path.join(os.path.dirname(__file__), 'vector_cache')
os.makedirs(CACHE_DIR, exist_ok=True)

class EncryptedVectorSearch:
    """
    加密向量检索类
    这是一个接口类，您可以将您的加密向量检索算法集成到这里
    """
    
    def __init__(self, dim: int = 384):
        """
        初始化加密向量检索
        
        Args:
            dim: 向量维度
        """
        self.dim = dim
        # 存储每个用户的数据库实例
        self.user_databases: Dict[int, EncryptedVectorDatabase] = {}
        self.user_pprfann_databases: Dict[int, PPRFANNVectorDatabase] = {}
        # 存储每个用户的累积数据（用于累加添加）
        # {user_id: {"texts": List[str], "embeddings": List[List[float]], "tags": List[int]}}
        self.user_cumulative_data: Dict[int, Dict[str, List]] = {}
        # 尝试从本地缓存加载已有用户的累积数据并重建数据库
        try:
            self.load_cached_users()
        except Exception as e:
            logger.warning("加载向量缓存失败: %s", e)
    
    def get_or_create_database(self, user_id: int, use_pprfann: bool = False) -> Any:
        """
        获取或创建用户的加密向量数据库
        
        Args:
            user_id: 用户ID
            use_pprfann: 是否使用PPRFANN（范围搜索）数据库
            
        Returns:
            加密向量数据库实例
        """
        if use_pprfann:
            if user_id not in self.user_pprfann_databases:
                self.user_pprfann_databases[user_id] = PPRFANNVectorDatabase(
                    dim=self.dim,
                    M=40,
                    ef_construction=600,
                    ef_search=100,
                    s=1024,
                    beta_num=1,
                    rate=10,
                    X_arg=2,
                    single_k=10,
                    rate_k=10
                )
            return self.user_pprfann_databases[user_id]
        else:
            if user_id not in self.user_databases:
                self.user_databases[user_id] = EncryptedVectorDatabase(
                    dim=self.dim,
                    M=40,
                    ef_construction=600,
                    ef_search=100,
                    s=1024,
                    beta_num=1,
                    rate=10
                )
            return self.user_databases[user_id]
    
    def add_texts_and_embeddings(
        self,
        user_id: int,
        texts: List[str],
        embeddings: List[List[float]],
        tags: Optional[List[int]] = None,
        metadata: Optional[List[Dict[str, Any]]] = None
    ):
        """
        向用户的加密向量数据库添加文本和向量（支持累加）
        
        Args:
            user_id: 用户ID
            texts: 文本列表
            embeddings: 向量嵌入列表
            tags: 标签列表（可选，用于PPRFANN范围搜索）
            metadata: 元数据列表（可选，每个文本的元数据）
        """
        # 初始化用户的累积数据（如果尚未初始化）
        if user_id not in self.user_cumulative_data:
            self.user_cumulative_data[user_id] = {
                "texts": [],
                "embeddings": [],
                "tags": [] if tags is not None else None,
                "metadata": []
            }
        
        # 累积新数据
        cumulative = self.user_cumulative_data[user_id]
        cumulative["texts"].extend(texts)
        cumulative["embeddings"].extend(embeddings)
        if tags is not None:
            if cumulative["tags"] is None:
                cumulative["tags"] = []
            cumulative["tags"].extend(tags)
        if metadata is not None:
            cumulative["metadata"].extend(metadata)

        # 持久化累积数据到本地缓存
        try:
            cache_path = os.path.join(CACHE_DIR, f'user_{user_id}.json')
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cumulative, f, ensure_ascii=False)
        except Exception as e:
            logger.warning("持久化用户 %s 累积数据失败: %s", user_id, e)
        
        n_new = len(texts)
        n_total = len(cumulative["texts"])
        logger.info(
            "[加密存储] 调用加密向量数据库模块(Securedb) user_id=%s 本次新增向量=%d 累计向量=%d 日期=%s",
            user_id,
            n_new,
            n_total,
            datetime.now().isoformat(timespec="seconds"),
        )

        # 重新构建数据库（使用所有累积的数据）
        if tags is not None:
            # 使用PPRFANN数据库（支持范围搜索）
            # 删除旧数据库实例
            if user_id in self.user_pprfann_databases:
                del self.user_pprfann_databases[user_id]
            db = self.get_or_create_database(user_id, use_pprfann=True)
            db.add_texts_and_embeddings_with_tags(
                cumulative["texts"],
                cumulative["embeddings"],
                cumulative["tags"]
            )
        else:
            # 使用纯向量检索数据库
            # 删除旧数据库实例
            if user_id in self.user_databases:
                del self.user_databases[user_id]
            db = self.get_or_create_database(user_id, use_pprfann=False)
            db.add_texts_and_embeddings(
                cumulative["texts"],
                cumulative["embeddings"]
            )

        logger.info(
            "[加密存储] 密文向量索引重建完成 user_id=%s 使用PPRFANN=%s",
            user_id,
            tags is not None,
        )

    def search(
        self,
        user_id: int,
        query_embedding: List[float],
        top_k: int = 5
    ) -> Tuple[List[int], List[str]]:
        """
        在用户的加密向量数据库中搜索（纯向量检索）
        
        Args:
            user_id: 用户ID
            query_embedding: 查询向量
            top_k: 返回结果数量
            
        Returns:
            (向量ID列表, 文本列表)
        """
        db = self.get_or_create_database(user_id, use_pprfann=False)
        if db.hnsw_index is None:
            return [], []
        return db.search(query_embedding, k=top_k)
    
    def range_search(
        self,
        user_id: int,
        query_embedding: List[float],
        tag_range: Tuple[int, int],
        top_k: int = 5
    ) -> Tuple[List[int], List[str]]:
        """
        在用户的加密向量数据库中范围搜索（向量+标量过滤）
        
        Args:
            user_id: 用户ID
            query_embedding: 查询向量
            tag_range: 标签范围 (start, end)
            top_k: 返回结果数量
            
        Returns:
            (向量ID列表, 文本列表)
        """
        logger.info(
            "[密文检索] EncryptedVectorSearch.range_search 开始 user_id=%s tag_range=%s top_k=%s 日期=%s",
            user_id,
            tag_range,
            top_k,
            datetime.now().isoformat(timespec="seconds"),
        )
        db = self.get_or_create_database(user_id, use_pprfann=True)
        if db.label_tree_root is None:
            logger.warning("[密文检索] 用户 %s 密文索引未构建(label_tree_root=None)，返回空", user_id)
            return [], []
        vector_ids, texts = db.range_search(query_embedding, tag_range, k=top_k)
        logger.info(
            "[密文检索] EncryptedVectorSearch.range_search 结束 user_id=%s 命中数=%d 日期=%s",
            user_id,
            len(vector_ids),
            datetime.now().isoformat(timespec="seconds"),
        )
        return vector_ids, texts
    
    def delete_user_database(self, user_id: int):
        """
        删除用户的数据库（用于清理）
        
        Args:
            user_id: 用户ID
        """
        if user_id in self.user_databases:
            del self.user_databases[user_id]
        if user_id in self.user_pprfann_databases:
            del self.user_pprfann_databases[user_id]

        # 删除本地缓存文件（如果存在）
        try:
            cache_path = os.path.join(CACHE_DIR, f'user_{user_id}.json')
            if os.path.exists(cache_path):
                os.remove(cache_path)
        except Exception as e:
            logger.warning("删除用户 %s 缓存失败: %s", user_id, e)

    def load_cached_users(self):
        """Load cached user cumulative data from disk and build databases."""
        for fname in os.listdir(CACHE_DIR):
            if not fname.startswith('user_') or not fname.endswith('.json'):
                continue
            try:
                user_id = int(fname[len('user_'):-len('.json')])
            except Exception:
                continue
            path = os.path.join(CACHE_DIR, fname)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    cumulative = json.load(f)
                # Validate structure
                texts = cumulative.get('texts', []) or []
                embeddings = cumulative.get('embeddings', []) or []
                tags = cumulative.get('tags', None)
                metadata = cumulative.get('metadata', []) or []
                # Store into memory
                self.user_cumulative_data[user_id] = {
                    'texts': texts,
                    'embeddings': embeddings,
                    'tags': tags,
                    'metadata': metadata
                }
                # Build database from loaded data
                if tags is not None:
                    # build pprfann
                    if user_id in self.user_pprfann_databases:
                        del self.user_pprfann_databases[user_id]
                    db = self.get_or_create_database(user_id, use_pprfann=True)
                    db.add_texts_and_embeddings_with_tags(texts, embeddings, tags)
                else:
                    if user_id in self.user_databases:
                        del self.user_databases[user_id]
                    db = self.get_or_create_database(user_id, use_pprfann=False)
                    db.add_texts_and_embeddings(texts, embeddings)
            except Exception as e:
                logger.warning("加载缓存文件失败 %s: %s", path, e)
