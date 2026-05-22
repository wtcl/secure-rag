#!/usr/bin/env python3
"""
测试不同类型问题的回答质量
"""
import os
import sys
import asyncio
sys.path.append('./backend')

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

from rag_service import RAGService

async def test_answer_quality():
    """测试不同问题的回答质量"""
    print("🔧 初始化RAG服务...")
    service = RAGService()

    test_cases = [
        ("什么是人工智能？", []),
        ("什么是机器学习？", []),
        ("什么是深度学习？", []),
        ("什么是量子计算？", []),
        ("什么是区块链？", []),  # 测试通用回答
    ]

    print("\n🧪 测试不同问题的回答质量：\n")

    for query, context in test_cases:
        try:
            answer = await service.generate_answer(query, context)
            print(f"❓ {query}")
            print(f"💡 {answer}")
            print("-" * 80)
        except Exception as e:
            print(f"❌ 测试失败 {query}: {e}")

if __name__ == "__main__":
    asyncio.run(test_answer_quality())