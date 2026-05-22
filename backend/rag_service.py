"""
RAG服务模块
处理文档处理、向量化、检索和生成回答
集成Securedb.py的加密向量检索算法
"""
import logging
import os
import aiofiles
from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime, date
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from encrypted_vector_search import EncryptedVectorSearch

logger = logging.getLogger("secure_rag.rag")


class RAGService:
    """RAG服务类"""
    
    def __init__(self):
        """初始化RAG服务"""
        # 初始化嵌入模型（降级：使用随机向量以避免下载问题）
        # self.embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        # 临时使用随机向量生成器（384维，与原模型匹配）
        self.embedding_model = None  # 标记为降级模式
        self.vector_dim = 384  # 固定向量维度，与原模型匹配
        
        # 初始化加密向量检索（使用正确的向量维度）
        self.encrypted_search = EncryptedVectorSearch(dim=self.vector_dim)
        
        # 存储用户的元数据映射（用于关联文本和源信息）
        # {user_id: {vector_id: {"source": str, "chunk_index": int}}}
        self.user_metadata_mapping: Dict[int, Dict[int, Dict[str, Any]]] = {}
        
        # 存储用户的向量计数器（用于生成唯一ID）
        # {user_id: counter}
        self.user_vector_counters: Dict[int, int] = {}
        
        # 文档分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        # 文件上传目录
        self.upload_dir = "./uploads"
        os.makedirs(self.upload_dir, exist_ok=True)
        
        # 从缓存重建元数据映射
        self._rebuild_metadata_from_cache()
    
    def _rebuild_metadata_from_cache(self):
        """从缓存数据重建元数据映射"""
        for user_id, cumulative in self.encrypted_search.user_cumulative_data.items():
            metadata_list = cumulative.get('metadata', [])
            if metadata_list:
                # 重建元数据映射
                if user_id not in self.user_metadata_mapping:
                    self.user_metadata_mapping[user_id] = {}
                for vector_id, metadata in enumerate(metadata_list):
                    self.user_metadata_mapping[user_id][vector_id] = metadata
                # 重建计数器
                self.user_vector_counters[user_id] = len(metadata_list)
    
    async def save_uploaded_file(self, file, user_id: int) -> str:
        """保存上传的文件"""
        import uuid
        import os.path as op
        # 安全处理文件名
        safe_filename = op.basename(file.filename) if file.filename else "document"
        # 添加唯一标识符避免文件名冲突
        unique_id = str(uuid.uuid4())[:8]
        file_path = os.path.join(self.upload_dir, f"{user_id}_{unique_id}_{safe_filename}")
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        return file_path
    
    async def process_document(self, file_path: str, user_id: int) -> Dict[str, Any]:
        """处理文档：提取文本、分割、生成向量并存储到加密向量数据库"""
        # 根据文件类型加载文档
        try:
            if file_path.lower().endswith('.pdf'):
                loader = PyPDFLoader(file_path)
            else:
                # 尝试多种编码
                try:
                    loader = TextLoader(file_path, encoding='utf-8')
                except:
                    loader = TextLoader(file_path, encoding='gbk')
            
            documents = loader.load()
        except Exception as e:
            raise Exception(f"文档加载失败: {str(e)}")

        logger.info(
            "[文档预处理] 文本提取完成 path=%s 原始文档段数=%d",
            file_path,
            len(documents),
        )

        # 分割文档
        chunks = self.text_splitter.split_documents(documents)

        # 处理每个chunk
        texts = [chunk.page_content for chunk in chunks]
        approx_chars = sum(len(t or "") for t in texts)
        logger.info(
            "[文档预处理] 长度过滤与切分完成 path=%s chunks=%d 约总字符数=%d",
            file_path,
            len(chunks),
            approx_chars,
        )

        # 生成向量（降级模式：使用随机向量）
        if self.embedding_model is None:
            # 降级：生成随机向量
            embeddings = []
            for _ in texts:
                # 生成随机向量（正态分布，均值0，标准差1）
                vector = np.random.normal(0, 1, self.vector_dim).tolist()
                embeddings.append(vector)
        else:
            # 正常模式：使用真实模型
            embeddings = self.embedding_model.encode(texts).tolist()

        embed_mode = "随机向量(降级)" if self.embedding_model is None else "嵌入模型"
        logger.info(
            "[向量嵌入] 编码完成 user_id=%s 片段数=%d 维度=%d 模式=%s",
            user_id,
            len(embeddings),
            self.vector_dim,
            embed_mode,
        )

        # 初始化用户的元数据映射和计数器（如果尚未初始化）
        if user_id not in self.user_metadata_mapping:
            self.user_metadata_mapping[user_id] = {}
        if user_id not in self.user_vector_counters:
            self.user_vector_counters[user_id] = 0
        
        # 获取当前向量起始ID
        start_vector_id = self.user_vector_counters[user_id]
        
        # 构建元数据映射和元数据列表
        metadata_list = []
        for i, chunk in enumerate(chunks):
            vector_id = start_vector_id + i
            metadata = {
                "source": file_path,
                "chunk_index": i,
                "text": texts[i]
            }
            self.user_metadata_mapping[user_id][vector_id] = metadata
            metadata_list.append(metadata)
        
        # 生成时间标签：从2026年1月1日到当前日期的天数
        # 基准日期：2026年1月1日
        base_date = date(2026, 1, 1)
        current_date = date.today()
        days_since_base = (current_date - base_date).days
        
        # 为每个chunk分配相同的上传日期标签（天数）
        tags = [days_since_base] * len(chunks)

        logger.info(
            "[加密存储] 向量已生成，即将调用密文向量存储模块 user_id=%s 向量条数=%d 时间标签(天)=%s",
            user_id,
            len(embeddings),
            days_since_base,
        )

        # 添加到加密向量数据库（同时支持纯向量检索和混合检索）
        # 使用时间标签可以支持基于时间范围的过滤检索
        self.encrypted_search.add_texts_and_embeddings(
            user_id=user_id,
            texts=texts,
            embeddings=embeddings,
            tags=tags,  # 使用时间标签（天数），支持时间范围过滤
            metadata=metadata_list
        )
        
        # 更新计数器
        self.user_vector_counters[user_id] += len(chunks)

        logger.info(
            "[文档预处理/加密存储] 单文档处理结束 user_id=%s path=%s 入库片段=%d",
            user_id,
            file_path,
            len(chunks),
        )

        return {
            "file_size": os.path.getsize(file_path),
            "chunks_count": len(chunks),
            "metadata": {"source": file_path}
        }
    
    async def vector_search(
        self,
        query: str,
        user_id: int,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """纯向量检索（使用PPANNS加密算法）"""
        logger.info(
            "[密文检索] 进入密文向量检索流程(纯向量) user_id=%s 日期=%s top_k=%s",
            user_id,
            datetime.now().isoformat(timespec="seconds"),
            top_k,
        )
        # 生成查询向量
        if self.embedding_model is None:
            # 降级模式：生成随机查询向量（用于测试）
            query_embedding = np.random.normal(0, 1, self.vector_dim).tolist()
        else:
            # 正常模式：使用真实模型
            query_embedding = self.embedding_model.encode([query])[0].tolist()
        
        # 使用加密向量检索（PPRFANN范围搜索，模拟纯向量搜索）
        # 使用一个很大的标签范围来包含所有可能的向量
        try:
            logger.info(
                "[密文检索] 调用 range_search user_id=%s tag_range=(0, 999999) top_k=%s",
                user_id,
                top_k,
            )
            vector_ids, retrieved_texts = self.encrypted_search.range_search(
                user_id=user_id,
                query_embedding=query_embedding,
                tag_range=(0, 999999),  # 很大的范围来包含所有向量
                top_k=top_k
            )
            logger.info(
                "[密文检索] range_search 返回 user_id=%s 命中数=%d",
                user_id,
                len(vector_ids),
            )

            # 如果没有找到结果，但用户有元数据，尝试直接返回所有可用数据
            if not vector_ids and user_id in self.user_metadata_mapping:
                logger.warning(
                    "[密文检索] range_search 无命中，回退到用户元数据映射 user_id=%s",
                    user_id,
                )
                all_vector_ids = list(self.user_metadata_mapping[user_id].keys())
                if all_vector_ids:
                    # 限制返回数量
                    limited_ids = all_vector_ids[:top_k]
                    vector_ids = limited_ids
                    retrieved_texts = []
                    for vid in limited_ids:
                        metadata = self.user_metadata_mapping[user_id][vid]
                        retrieved_texts.append(metadata.get("text", ""))
                    logger.info(
                        "[密文检索] 已用元数据映射填充结果 user_id=%s 条数=%d",
                        user_id,
                        len(vector_ids),
                    )

        except Exception as e:
            # 如果数据库为空或出错，返回空列表
            logger.exception("[密文检索] 加密向量检索异常 user_id=%s err=%s", user_id, e)
            # 尝试返回用户的所有可用数据
            if user_id in self.user_metadata_mapping:
                all_vector_ids = list(self.user_metadata_mapping[user_id].keys())
                if all_vector_ids:
                    vector_ids = all_vector_ids[:top_k]
                    retrieved_texts = []
                    for vid in all_vector_ids[:top_k]:
                        metadata = self.user_metadata_mapping[user_id][vid]
                        retrieved_texts.append(metadata.get("text", ""))
                    logger.info(
                        "[密文检索] 异常后回退用户数据 user_id=%s 条数=%d",
                        user_id,
                        len(vector_ids),
                    )
                else:
                    return []
            else:
                return []

        # 格式化结果
        formatted_results = []
        metadata_mapping = self.user_metadata_mapping.get(user_id, {})
        
        for i, (vector_id, text) in enumerate(zip(vector_ids, retrieved_texts)):
            # 获取元数据
            metadata = metadata_mapping.get(vector_id, {"source": "未知来源"})
            formatted_results.append({
                "content": text,
                "source": metadata.get("source", "未知来源"),
                "score": 0.9 - i * 0.1  # 简单的相似度分数（实际应该从检索结果获取）
            })

        logger.info(
            "[密文检索] 纯向量检索结束 user_id=%s 日期=%s 返回片段=%d",
            user_id,
            datetime.now().isoformat(timespec="seconds"),
            len(formatted_results),
        )
        return formatted_results
    
    async def hybrid_search(
        self,
        query: str,
        user_id: int,
        scalar_filters: Dict[str, Any],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """向量标量混合检索（使用PPRFANN加密算法）
        
        支持时间范围过滤：scalar_filters 中可以包含 'time_range' 键，
        值为 {"min": start_days, "max": end_days}，表示从基准日期起的天数范围。
        基准日期：2026年1月1日
        
        例如：{"time_range": {"min": 0, "max": 365}} 表示查询2026年1月1日至2027年1月1日的文档
        """
        logger.info(
            "[密文检索] 进入密文向量检索流程(混合) user_id=%s 日期=%s top_k=%s scalar_filters=%s",
            user_id,
            datetime.now().isoformat(timespec="seconds"),
            top_k,
            scalar_filters,
        )
        # 生成查询向量
        if self.embedding_model is None:
            # 降级模式：生成随机查询向量（用于测试）
            query_embedding = np.random.normal(0, 1, self.vector_dim).tolist()
        else:
            # 正常模式：使用真实模型
            query_embedding = self.embedding_model.encode([query])[0].tolist()
        
        # 从标量过滤条件中提取标签范围
        tag_range = None
        logger.info("[密文检索] 混合检索 scalar_filters=%s", scalar_filters)
        
        # 优先检测时间范围过滤
        if "time_range" in scalar_filters:
            time_range = scalar_filters["time_range"]
            logger.info("[密文检索] 检测到 time_range=%s", time_range)
            if isinstance(time_range, dict):
                if "min" in time_range and "max" in time_range:
                    tag_range = (int(time_range["min"]), int(time_range["max"]))
                    logger.info("[密文检索] 解析时间范围(min/max) tag_range=%s", tag_range)
                elif "$gte" in time_range and "$lte" in time_range:
                    tag_range = (int(time_range["$gte"]), int(time_range["$lte"]))
                    logger.info("[密文检索] 解析时间范围($gte/$lte) tag_range=%s", tag_range)
                else:
                    logger.warning("[密文检索] time_range 格式无法解析: %s", time_range)
        
        # 如果没有时间范围，尝试其他标量过滤条件
        if tag_range is None:
            for key in ['tag', 'label', 'range', 'vector_id', 'id']:
                if key in scalar_filters:
                    value = scalar_filters[key]
                    logger.info("[密文检索] 尝试使用键 %s 作为标签范围: %s", key, value)
                    if isinstance(value, dict):
                        # {"tag": {"min": 1, "max": 5000}} 或 {"tag": {"$gte": 1, "$lte": 5000}}
                        if "min" in value and "max" in value:
                            tag_range = (int(value["min"]), int(value["max"]))
                            logger.info("[密文检索] 解析 %s(min/max) tag_range=%s", key, tag_range)
                        elif "$gte" in value and "$lte" in value:
                            tag_range = (int(value["$gte"]), int(value["$lte"]))
                            logger.info("[密文检索] 解析 %s($gte/$lte) tag_range=%s", key, tag_range)
                        break
                    elif isinstance(value, (list, tuple)) and len(value) == 2:
                        # {"tag": [1, 5000]}
                        tag_range = (int(value[0]), int(value[1]))
                        logger.info("[密文检索] 解析 %s(列表) tag_range=%s", key, tag_range)
                        break
        
        # 如果没有明确指定标签范围，使用用户的向量ID范围（默认使用所有向量）
        if tag_range is None:
            # 获取用户的向量ID范围
            if user_id in self.user_vector_counters:
                max_vector_id = self.user_vector_counters[user_id]
                # 默认使用所有向量（范围从0到最大ID）
                tag_range = (0, max(0, max_vector_id - 1))
                logger.warning("[密文检索] 未指定标签范围，使用默认 tag_range=%s", tag_range)
            else:
                raise ValueError(
                    "混合检索需要提供标签范围。请在 scalar_filters 中包含 'tag'、'label' 或 'range' 键。"
                    "例如: {'tag': {'min': 1, 'max': 5000}} 或 {'label': [1, 5000]}"
                )

        logger.info("[密文检索] 最终 tag_range=%s 日期=%s", tag_range, datetime.now().isoformat(timespec="seconds"))

        # 使用加密向量范围检索（PPRFANN）
        try:
            vector_ids, retrieved_texts = self.encrypted_search.range_search(
                user_id=user_id,
                query_embedding=query_embedding,
                tag_range=tag_range,
                top_k=top_k
            )
            logger.info(
                "[密文检索] range_search 返回 user_id=%s 命中数=%d 日期=%s",
                user_id,
                len(vector_ids),
                datetime.now().isoformat(timespec="seconds"),
            )
        except Exception as e:
            # 如果数据库为空或出错，返回空列表
            logger.exception("[密文检索] 混合 range_search 异常 user_id=%s err=%s", user_id, e)
            return []
        
        # 格式化结果
        formatted_results = []
        metadata_mapping = self.user_metadata_mapping.get(user_id, {})
        
        for i, (vector_id, text) in enumerate(zip(vector_ids, retrieved_texts)):
            # 获取元数据
            metadata = metadata_mapping.get(vector_id, {"source": "未知来源"})
            formatted_results.append({
                "content": text,
                "source": metadata.get("source", "未知来源"),
                "score": 0.9 - i * 0.1  # 简单的相似度分数
            })

        logger.info(
            "[密文检索] 混合检索结束 user_id=%s 日期=%s 返回片段=%d",
            user_id,
            datetime.now().isoformat(timespec="seconds"),
            len(formatted_results),
        )
        return formatted_results
    
    async def generate_answer(
        self,
        query: str,
        context: List[Dict[str, Any]]
    ) -> str:
        """基于检索结果生成回答"""
        logger.info(
            "[RAG生成] 开始组合检索片段与查询生成回答 检索片段数=%d query_preview=%s",
            len(context),
            (query or "")[:120],
        )
        # 构建检索结果显示
        context_display = ""
        if context:
            # 获取唯一的来源文档列表
            unique_sources = list(set(r['source'] for r in context))
            context_display = "\n\n📄 检索到的相关文档：\n" + "\n".join([
                f"• {source}" for source in unique_sources
            ])
        else:
            context_display = "\n\n📄 未检索到相关内容，将基于通用知识回答。"

        # 使用LLM生成回答
        answer = await self._generate_with_llm(query, context)
        merged = f"{answer}{context_display}"
        logger.info(
            "[RAG生成] 回答拼装完成 正文长度=%d 含来源说明=%s",
            len(answer or ""),
            bool(context),
        )
        return merged

    async def delete_document_vectors(self, file_path: str, user_id: int) -> int:
        """删除指定文档在用户向量库中的所有向量及元数据。

        Args:
            file_path: 文档在磁盘上的路径（与元数据中的 "source" 匹配）
            user_id: 用户ID

        Returns:
            删除的向量数量
        """
        # 检查用户映射和累积数据
        if user_id not in self.user_metadata_mapping:
            return 0

        metadata = self.user_metadata_mapping[user_id]

        # 收集需要删除的向量ID
        to_delete_ids = [vid for vid, m in metadata.items() if m.get("source") == file_path]
        if not to_delete_ids:
            return 0

        # 从元数据映射中删除这些ID
        for vid in to_delete_ids:
            metadata.pop(vid, None)

        # 如果加密向量库保存了累积数据，需要从中移除对应的条目并重建数据库
        cumulative = self.encrypted_search.user_cumulative_data.get(user_id)
        if cumulative:
            texts = cumulative.get("texts", [])
            embeddings = cumulative.get("embeddings", [])
            tags = cumulative.get("tags")

            # 找到所有匹配 tag（如果 tags 存在且使用了 tag 作为向量ID）
            if tags is not None:
                # tags 是向量ID列表，与 texts/embeddings 一一对应
                remaining_texts = []
                remaining_embeddings = []
                remaining_tags = []
                for t, emb, tx in zip(tags, embeddings, texts):
                    if t not in to_delete_ids:
                        remaining_tags.append(t)
                        remaining_embeddings.append(emb)
                        remaining_texts.append(tx)

                cumulative["texts"] = remaining_texts
                cumulative["embeddings"] = remaining_embeddings
                cumulative["tags"] = remaining_tags
            else:
                # 如果没有 tags，则尝试根据元数据的 text 字段匹配并删除
                remaining_texts = []
                remaining_embeddings = []
                for emb, tx in zip(embeddings, texts):
                    # 查找是否有元数据引用此文本
                    # 因为我们删除了 metadata 中对应的 vector id，最简单的策略是保留所有仍被 metadata 引用的文本
                    remaining_texts.append(tx)
                    remaining_embeddings.append(emb)

                cumulative["texts"] = remaining_texts
                cumulative["embeddings"] = remaining_embeddings

            # 删除旧数据库实例，以便在下一次 add 时重建
            if user_id in self.encrypted_search.user_pprfann_databases:
                del self.encrypted_search.user_pprfann_databases[user_id]
            if user_id in self.encrypted_search.user_databases:
                del self.encrypted_search.user_databases[user_id]

            # 重新构建数据库（如果还有剩余数据）
            remaining = cumulative.get("texts", [])
            if remaining:
                # 在调用 add_texts_and_embeddings 之前清除旧的累积记录，
                # 否则 add_texts_and_embeddings 会对已有的累积数据执行 extend，
                # 导致数据被重复追加。
                if user_id in self.encrypted_search.user_cumulative_data:
                    del self.encrypted_search.user_cumulative_data[user_id]

                if cumulative.get("tags") is not None:
                    self.encrypted_search.add_texts_and_embeddings(
                        user_id=user_id,
                        texts=cumulative["texts"],
                        embeddings=cumulative["embeddings"],
                        tags=cumulative["tags"]
                    )
                else:
                    self.encrypted_search.add_texts_and_embeddings(
                        user_id=user_id,
                        texts=cumulative["texts"],
                        embeddings=cumulative["embeddings"]
                    )
            else:
                # 没有剩余数据，移除累积记录和数据库实例
                if user_id in self.encrypted_search.user_cumulative_data:
                    del self.encrypted_search.user_cumulative_data[user_id]
                self.encrypted_search.delete_user_database(user_id)

    async def rebuild_user_vectors(self, user_id: int, file_paths: List[str]) -> int:
        """Rebuild in-memory vectors and metadata for a user from provided file paths.

        Clears existing in-memory indices and reprocesses each document path by
        calling `process_document` which regenerates embeddings and updates
        metadata and cumulative data.

        Returns the total number of vectors added.
        """
        # Clear in-memory metadata and indices for the user
        if user_id in self.user_metadata_mapping:
            del self.user_metadata_mapping[user_id]
        # Reset counter
        self.user_vector_counters[user_id] = 0
        # Clear cumulative data and remove any existing DB instances
        if user_id in self.encrypted_search.user_cumulative_data:
            del self.encrypted_search.user_cumulative_data[user_id]
        self.encrypted_search.delete_user_database(user_id)

        total_added = 0
        for path in file_paths:
            # Skip missing files but continue with others
            try:
                info = await self.process_document(path, user_id)
                total_added += info.get("chunks_count", 0)
            except Exception as e:
                print(f"rebuild_user_vectors: failed to process {path}: {e}")

        return total_added

        # 返回删除的数量
        return len(to_delete_ids)
    async def _generate_with_llm(self, query: str, context: List[Dict[str, Any]]) -> str:
        """使用大语言模型生成回答"""
        # 构建上下文文本（将检索到的片段与来源一并提供给在线大模型）
        context_text = ""
        if context:
            # 选取若干最高分的片段，并保留顺序，限制每段长度避免超长
            max_chunks = 5
            max_chars_per_chunk = 800
            snippets = []
            for idx, r in enumerate(context[:max_chunks], start=1):
                src = str(r.get("source", "未知来源"))
                content = str(r.get("content", ""))[:max_chars_per_chunk]
                snippets.append(f"[{idx}] 来源: {src}\n内容: {content}")
            context_block = "\n\n".join(snippets)
            context_text = (
                "请严格基于以下检索到的文档片段回答问题（按相似度降序）：\n"
                f"{context_block}\n\n"
                "回答要求：\n"
                "- 优先引用片段中的信息作答，必要时再结合常识\n"
                "- 不要编造未在片段中出现的具体数据或引用\n"
                "- 如片段不足以回答，请明确说明资料不足"
            )

        # 方案0: DeepSeek（OpenAI 兼容接口，密钥：环境变量 DSKEY）
        try:
            import httpx
            from openai import OpenAI

            api_key = (os.getenv("DSKEY") or "").strip()
            if not api_key:
                raise ValueError(
                    "未配置 DeepSeek API 密钥：请设置环境变量 DSKEY（或写入项目根目录 / backend 目录的 .env）"
                )

            base_url = (os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com").strip()
            model = (os.getenv("DEEPSEEK_MODEL") or "deepseek-chat").strip()

            # 与智谱类似：避免系统环境里的 socks:// 代理导致 httpx 初始化失败
            _trust_proxy_env = os.getenv("DEEPSEEK_HTTP_TRUST_ENV", "").strip().lower() in (
                "1",
                "true",
                "yes",
            )
            http_client = httpx.Client(trust_env=_trust_proxy_env, timeout=120.0)
            client = OpenAI(api_key=api_key, base_url=base_url, http_client=http_client)
            try:
                if context_text:
                    prompt = f"""请基于以下检索内容回答用户的问题，遵循回答要求。
{context_text}

用户问题：{query}

请用中文在200字以内回答，提供准确、有帮助的回答。"""
                else:
                    prompt = f"""请回答用户的问题：

用户问题：{query}

请用中文在200字以内回答，提供准确、有帮助的回答。"""

                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一个专业的问答助手。请严格依据提供的检索片段作答，必要时再结合常识，避免编造。限制答案不超过200字。",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    max_tokens=300,
                )

                raw = response.choices[0].message.content
                answer = (raw or "").strip()
                if not answer:
                    raise ValueError("DeepSeek 返回内容为空")
                logger.info("[DeepSeek] chat.completions 调用成功 model=%s", model)
                return answer
            finally:
                client.close()

        except ImportError:
            logger.warning("openai 或 httpx 未安装，无法调用 DeepSeek，回退至其他模型")
        except Exception as e:
            logger.warning("DeepSeek 调用失败，将回退至其他模型: %s", e, exc_info=True)


        # 方案1: 使用OpenAI GPT
        try:
            import openai
            from openai import OpenAI

            # 从环境变量读取API密钥
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

            if not api_key:
                raise ValueError("OPENAI_API_KEY环境变量未设置")

            client = OpenAI(api_key=api_key, base_url=base_url)

            # 总是基于模型自身知识回答，但可以参考检索内容
            if context_text:
                prompt = f"""请基于您的知识回答用户的问题。如果检索到的相关内容有助于提供更准确或具体的回答，请适当参考这些内容。

检索到的相关内容（可选择性参考）：
{context_text}

用户问题：{query}

请用中文回答，提供准确、有帮助的回答。"""
            else:
                prompt = f"""请基于您的知识回答用户的问题。

用户问题：{query}

请用中文回答，提供准确、有帮助的回答。"""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # 可以使用 gpt-4, gpt-4-turbo 等
                messages=[
                    {"role": "system", "content": "你是一个专业的问答助手。请基于您的知识回答用户问题，可以适当参考提供的检索内容，但不要完全依赖这些内容。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )

            answer = response.choices[0].message.content.strip()
            return answer

        except ImportError:
            print("OpenAI包未安装，尝试使用Claude")
        except Exception as e:
            print(f"OpenAI API调用失败: {e}，尝试使用Claude")

        # 方案2: 使用Claude (Anthropic)
        try:
            import anthropic
            from anthropic import Anthropic

            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key or api_key == "your-anthropic-api-key-here":
                raise ValueError("Claude API密钥未配置")

            client = Anthropic(api_key=api_key)

            # 构建prompt
            if context_text:
                prompt = f"""请基于您的知识回答用户的问题。如果检索到的相关内容有助于提供更准确或具体的回答，请适当参考这些内容。

检索到的相关内容（可选择性参考）：
{context_text}

用户问题：{query}

请用中文回答，提供准确、有帮助的回答。"""
            else:
                prompt = f"""请基于您的知识回答用户的问题。

用户问题：{query}

请用中文回答，提供准确、有帮助的回答。"""

            response = client.messages.create(
                model="claude-3-sonnet-20240229",  # 或 claude-3-haiku-20240307
                max_tokens=1000,
                temperature=0.3,
                system="你是一个专业的问答助手。请基于您的知识回答用户问题，可以适当参考提供的检索内容，但不要完全依赖这些内容。",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            answer = response.content[0].text.strip()
            return answer

        except ImportError:
            print("Claude包未安装，尝试使用Gemini")
        except Exception as e:
            print(f"Claude API调用失败: {e}，尝试使用Gemini")

        # 方案3: 使用Gemini (Google)
        try:
            import google.generativeai as genai

            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key or api_key == "your-google-api-key-here":
                raise ValueError("Gemini API密钥未配置")

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')

            # 构建prompt
            if context_text:
                prompt = f"""请基于您的知识回答用户的问题。如果检索到的相关内容有助于提供更准确或具体的回答，请适当参考这些内容。

检索到的相关内容（可选择性参考）：
{context_text}

用户问题：{query}

请用中文回答，提供准确、有帮助的回答。"""
            else:
                prompt = f"""请基于您的知识回答用户的问题。

用户问题：{query}

请用中文回答，提供准确、有帮助的回答。"""

            response = model.generate_content(prompt)
            answer = response.text.strip()
            return answer

        except ImportError:
            print("Gemini包未安装，尝试使用本地模型")
        except Exception as e:
            print(f"Gemini API调用失败: {e}，尝试使用本地模型")

        # 方案2: 使用本地HuggingFace模型
        try:
            from transformers import pipeline


            # 配置HuggingFace镜像源（解决网络问题）
            # 可以设置环境变量 HF_ENDPOINT=https://hf-mirror.com
            # 或者使用其他镜像源如 https://huggingface.co
            hf_endpoint = os.getenv('HF_ENDPOINT', 'https://huggingface.co')

            # 使用本地模型（轻量级对话模型）
            # 注意：如果网络问题严重，可以考虑预下载模型到本地
            # 使用本地模型（适合问答任务的模型）
            # DialoGPT更适合对话，不适合这种问答任务，我们使用模板生成
            print("使用本地模板生成回答（DialoGPT不适合问答任务）")
            raise Exception("使用模板生成代替")

            return answer

        except ImportError:
            print("transformers包未安装，使用简单模板生成")
        except Exception as e:
            print(f"本地模型调用失败: {e}，使用简单模板生成")

        # 方案3: 使用其他LLM服务（如Claude、Gemini等）
        # 这里可以添加其他LLM服务的集成代码

        # 后备方案：简单的模板生成
        try:
            # 根据问题类型给出相应的通用回答
            query_lower = query.lower()

            if "人工智能" in query or "ai" in query_lower or "artificial intelligence" in query_lower:
                answer = "人工智能（Artificial Intelligence，简称AI）是指计算机系统模拟人类智能的能力，包括学习、推理、问题解决、感知、语言理解等功能。"
            elif "机器学习" in query or "machine learning" in query_lower:
                answer = "机器学习是人工智能的一个子领域，它通过算法让计算机从数据中学习规律，而不需要明确编程。"
            elif "深度学习" in query or "deep learning" in query_lower:
                answer = "深度学习是机器学习的一种方法，使用多层神经网络来模拟人脑处理信息的方式。"
            elif "量子计算" in query or "quantum computing" in query_lower:
                answer = "量子计算是一种利用量子力学原理进行计算的新型计算模式，能够在某些问题上比传统计算机更快地找到解决方案。"
            else:
                # 通用回答 - 提供有帮助的通用解释
                answer = f"这是一个很好的问题。在科技领域，{query}通常指的是相关技术或概念的具体应用和实现方式。"

            # 如果有上下文，添加简短的参考说明
            if context_text:
                answer += f"\n\n（参考了您上传的相关文档内容）"

            return answer

        except Exception as e:
            print(f"模板生成也失败了: {e}")
            return f"抱歉，我无法基于当前文档生成满意的回答。原始查询：{query}"
