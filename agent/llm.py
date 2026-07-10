"""
LLM 管理模块 — 统一初始化 ChatModel，供意图路由和洞察引擎使用
"""
import os
from dotenv import load_dotenv

# 自动加载 .env
load_dotenv()


def create_chat_model(model: str = None, temperature: float = 0.3):
    """
    创建 LangChain ChatModel 实例

    Args:
        model: 模型名，默认从环境变量 LLM_MODEL 读取（qwen-max）
        temperature: 温度参数
    """
    from langchain_community.chat_models import ChatTongyi

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("请设置 DASHSCOPE_API_KEY 环境变量或在 .env 文件中配置")

    model_name = model or os.getenv("LLM_MODEL", "qwen-max")

    return ChatTongyi(
        model=model_name,
        temperature=temperature,
        dashscope_api_key=api_key,
    )
