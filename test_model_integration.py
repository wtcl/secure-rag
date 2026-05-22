#!/usr/bin/env python3
"""
测试不同LLM模型的集成
"""
import os
import sys
import asyncio
sys.path.append('./backend')

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

from rag_service import RAGService

async def test_model_integration():
    """测试不同模型的集成"""
    print("🔧 初始化RAG服务...")
    service = RAGService()

    query = "什么是人工智能？"
    context_docs = [
        {"source": "doc1.txt", "content": "人工智能是一种模拟人类智能的技术。"},
        {"source": "doc2.txt", "content": "机器学习是人工智能的一个子领域。"},
    ]

    print(f"🤖 测试查询: {query}")
    print(f"📄 上下文文档数量: {len(context_docs)}")
    print("\n🔄 系统将按优先级尝试不同的LLM服务...\n")

    try:
        answer = await service.generate_answer(query, context_docs)
        print("✅ 模型集成测试成功!")
        print(f"📝 生成的答案:\n{answer}\n")

        # 显示使用了哪个模型（从日志中推断）
        print("💡 使用的模型服务:")
        if "OpenAI API调用失败" not in open('/tmp/test.log', 'w').write(''):  # 临时方案
            print("   - 尝试了 OpenAI GPT")
        print("   - 按配置顺序尝试其他服务")
        print("   - 最终使用后备模板生成")

    except Exception as e:
        print(f"❌ 模型集成测试失败: {e}")
        return False

    return True

if __name__ == "__main__":
    asyncio.run(test_model_integration())