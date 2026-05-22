#!/usr/bin/env python3
"""
测试LLM集成功能
"""
import os
import sys
import asyncio
sys.path.append('./backend')

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

from rag_service import RAGService

async def test_llm_integration():
    """测试LLM集成"""
    print("🔧 初始化RAG服务...")
    service = RAGService()

    # 测试数据1：有上下文的情况
    query1 = "什么是人工智能？"
    context_docs1 = [
        {"source": "doc1.txt", "content": "人工智能是一种模拟人类智能的技术。"},
        {"source": "doc2.txt", "content": "机器学习是人工智能的一个子领域。"},
        {"source": "doc3.txt", "content": "深度学习使用神经网络来解决问题。"}
    ]

    print(f"\n🤖 测试1：有上下文的情况（知识驱动+参考内容）")
    print(f"查询: {query1}")
    print(f"上下文文档数量: {len(context_docs1)}")

    try:
        answer1 = await service.generate_answer(query1, context_docs1)
        print("✅ 有上下文测试成功!")
        print(f"📝 生成的答案:\n{answer1}\n")

    except Exception as e:
        print(f"❌ 有上下文测试失败: {e}")
        return False

    # 测试数据2：没有上下文的情况
    query2 = "什么是量子计算？"
    context_docs2 = []  # 空上下文

    print(f"\n🤖 测试2：没有上下文的情况（纯粹知识驱动）")
    print(f"查询: {query2}")
    print(f"上下文文档数量: {len(context_docs2)}")

    try:
        answer2 = await service.generate_answer(query2, context_docs2)
        print("✅ 无上下文测试成功!")
        print(f"📝 生成的答案:\n{answer2}\n")

    except Exception as e:
        print(f"❌ 无上下文测试失败: {e}")
        return False

    return True

if __name__ == "__main__":
    success = asyncio.run(test_llm_integration())
    sys.exit(0 if success else 1)