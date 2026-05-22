#!/usr/bin/env python3
"""
测试无相关内容查询的LLM功能
"""
import os
import sys
import asyncio
sys.path.append('./backend')

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

from rag_service import RAGService

async def test_no_context_query():
    """测试没有相关内容的查询"""
    print("🔧 初始化RAG服务...")
    service = RAGService()

    # 测试查询一个不在文档中的话题
    query = "什么是区块链技术？"
    context_docs = []  # 空上下文，模拟没有检索到相关内容

    print(f"🤖 测试查询: {query}")
    print(f"📄 上下文文档数量: {len(context_docs)} (模拟未检索到相关内容)")

    try:
        answer = await service.generate_answer(query, context_docs)
        print("✅ 无上下文查询测试成功!")
        print(f"📝 生成的答案:\n{answer}\n")

        # 验证回答中包含了相应的提示
        if "未检索到相关内容" in answer:
            print("✅ 正确显示了未检索到内容的提示")
        else:
            print("⚠️  未找到未检索到内容的提示")

        return True
    except Exception as e:
        print(f"❌ 无上下文查询测试失败: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_no_context_query())
    sys.exit(0 if success else 1)