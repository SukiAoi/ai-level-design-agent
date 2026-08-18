"""DeepSeek LLM 封装（OpenAI 兼容协议）"""
from langchain_openai import ChatOpenAI

from . import config


def get_llm(temperature: float | None = None) -> ChatOpenAI:
    """构建 DeepSeek 聊天模型（支持工具调用）"""
    if not config.DEEPSEEK_API_KEY:
        raise RuntimeError(
            "未设置 DEEPSEEK_API_KEY，请复制 .env.example 为 .env 并填入 Key"
        )
    return ChatOpenAI(
        model=config.DEEPSEEK_MODEL,
        api_key=config.DEEPSEEK_API_KEY,
        base_url=config.DEEPSEEK_BASE_URL,
        temperature=config.LLM_TEMPERATURE if temperature is None else temperature,
    )
