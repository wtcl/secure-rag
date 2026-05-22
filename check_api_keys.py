#!/usr/bin/env python3
"""
验证LLM API密钥配置
"""
import os
import sys
sys.path.append('./backend')

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

def check_api_keys():
    """检查API密钥配置"""
    print("🔍 检查LLM API密钥配置...\n")

    # 检查OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and openai_key != "sk-test-key-for-testing-only":
        print("✅ OpenAI API密钥：已配置")
    else:
        print("❌ OpenAI API密钥：未配置或为测试密钥")

    # 检查Claude
    claude_key = os.getenv("ANTHROPIC_API_KEY")
    if claude_key and claude_key != "your-anthropic-api-key-here":
        print("✅ Claude API密钥：已配置")
    else:
        print("❌ Claude API密钥：未配置")

    # 检查Gemini
    gemini_key = os.getenv("GOOGLE_API_KEY")
    if gemini_key and gemini_key != "your-google-api-key-here":
        print("✅ Gemini API密钥：已配置")
    else:
        print("❌ Gemini API密钥：未配置")

    print("\n💡 配置建议：")
    print("1. 推荐配置OpenAI API密钥（稳定可靠）")
    print("2. Claude适合中文内容，Gemini适合推理任务")
    print("3. 至少配置一个API密钥以获得最佳体验")

    # 检查优先级
    print("\n🔄 模型使用优先级：")
    if openai_key and openai_key != "sk-test-key-for-testing-only":
        print("1. OpenAI GPT (✅ 已配置)")
    else:
        print("1. OpenAI GPT (❌ 未配置)")

    if claude_key and claude_key != "your-anthropic-api-key-here":
        print("2. Claude (✅ 已配置)")
    else:
        print("2. Claude (❌ 未配置)")

    if gemini_key and gemini_key != "your-google-api-key-here":
        print("3. Gemini (✅ 已配置)")
    else:
        print("3. Gemini (❌ 未配置)")

    print("4. 本地模板生成 (✅ 始终可用)")

if __name__ == "__main__":
    check_api_keys()