"""认证相关 Pydantic schemas。"""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """用户注册请求。"""

    username: str = Field(..., min_length=3, max_length=128, description="用户名")
    email: str = Field(..., min_length=5, max_length=255, description="邮箱")
    password: str = Field(..., min_length=8, max_length=128, description="密码")


class LoginRequest(BaseModel):
    """登录请求。"""

    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    """JWT Token 响应。"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


class UserOut(BaseModel):
    """用户公开信息。"""

    id: str
    username: str
    email: str
    is_active: bool

    class Config:
        from_attributes = True
