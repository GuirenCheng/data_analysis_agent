"""LangChain Chat Model 工厂 — 支持 OpenAI / 兼容 API，含自动故障转移。"""

from langchain_openai import ChatOpenAI

from daa.settings import get_settings


def create_chat_model(
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    streaming: bool = False,
    llm_config: dict | None = None,
) -> ChatOpenAI:
    """创建 LangChain ChatOpenAI 实例。

    根据 settings 自动配置 API 密钥和基础 URL，
    如果有备用 API 配置，通过 .with_fallbacks() 实现故障转移。

    Args:
        model: LLM 模型名称，默认使用 settings 中的配置
        temperature: 温度参数
        max_tokens: 最大 token 数
        streaming: 是否启用流式输出
        llm_config: 用户级覆盖配置（model/base_url/api_key/temperature/max_tokens），
            为空或字段为空时回退到全局 settings

    Returns:
        ChatOpenAI 实例（可能带有 fallback 链）
    """
    settings = get_settings()
    cfg = llm_config or {}

    final_model = model or cfg.get("model") or settings.LLM_MODEL
    if temperature is not None:
        final_temperature = temperature
    elif cfg.get("temperature") is not None:
        final_temperature = cfg["temperature"]
    else:
        final_temperature = settings.LLM_TEMPERATURE
    final_max_tokens = max_tokens or cfg.get("max_tokens") or settings.LLM_MAX_TOKENS
    final_api_key = cfg.get("api_key") or settings.LLM_API_KEY
    final_base_url = cfg.get("base_url") or settings.LLM_BASE_URL

    primary = ChatOpenAI(
        model=final_model,
        temperature=final_temperature,
        max_tokens=final_max_tokens,
        api_key=final_api_key,
        base_url=final_base_url,
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


def create_report_chat_model(llm_config: dict | None = None) -> ChatOpenAI:
    """创建用于报告生成的 LLM，使用更大的 max_tokens 与更稳定的低温。

    报告生成沿用用户配置的模型 / 接口 / 密钥，但 temperature 与 max_tokens
    保持报告专用值（0.3 / 16384），保证输出稳定。
    """
    cfg = llm_config or {}
    return create_chat_model(
        model=cfg.get("model") or None,
        temperature=0.3,
        max_tokens=16384,
        llm_config={
            "api_key": cfg.get("api_key") or "",
            "base_url": cfg.get("base_url") or "",
        },
    )
