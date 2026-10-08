"""用户配置 schemas。"""

from typing import Optional

from pydantic import BaseModel, Field


class UserConfigOut(BaseModel):
    """用户配置响应。"""

    id: str
    llm_provider: str = "openai"
    llm_model: str = ""
    llm_base_url: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 16384
    default_max_rounds: int = 20
    default_output_dir: str = "outputs"
    # 注意: API Key 不返回给前端

    class Config:
        from_attributes = True


class UserConfigUpdate(BaseModel):
    """用户配置更新请求。"""

    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_api_key: Optional[str] = None  # 允许更新 API Key
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=100, le=128000)
    default_max_rounds: Optional[int] = Field(default=None, ge=5, le=50)
    default_output_dir: Optional[str] = None
