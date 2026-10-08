"""LangChain Chat Model 工厂 — 支持 OpenAI / 兼容 API，含自动故障转移。"""

from langchain_openai import ChatOpenAI

from daa.settings import get_settings


def create_chat_model(
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    streaming: bool = False,
) -> ChatOpenAI:
    """创建 LangChain ChatOpenAI 实例。

    根据 settings 自动配置 API 密钥和基础 URL，
    如果有备用 API 配置，通过 .with_fallbacks() 实现故障转移。

    Args:
        model: LLM 模型名称，默认使用 settings 中的配置
        temperature: 温度参数
        max_tokens: 最大 token 数
        streaming: 是否启用流式输出

    Returns:
        ChatOpenAI 实例（可能带有 fallback 链）
    """
    settings = get_settings()

    primary = ChatOpenAI(
        model=model or settings.LLM_MODEL,
        temperature=temperature if temperature is not None else settings.LLM_TEMPERATURE,
        max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        streaming=streaming,
        max_retries=1,
        timeout=120,
    )

    # 配置了备用 API 时，使用 LangChain fallback 机制
    if settings.LLM_FALLBACK_API_KEY and settings.LLM_FALLBACK_BASE_URL and settings.LLM_FALLBACK_MODEL:
        fallback = ChatOpenAI(
            model=settings.LLM_FALLBACK_MODEL,
            temperature=temperature if temperature is not None else settings.LLM_TEMPERATURE,
            max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
            api_key=settings.LLM_FALLBACK_API_KEY,
            base_url=settings.LLM_FALLBACK_BASE_URL,
            streaming=streaming,
            max_retries=1,
            timeout=120,
        )
        return primary.with_fallbacks([fallback])

    return primary


def create_report_chat_model() -> ChatOpenAI:
    """创建用于报告生成的 LLM，使用更大的 max_tokens。"""
    settings = get_settings()
    return create_chat_model(max_tokens=16384, temperature=0.3)
