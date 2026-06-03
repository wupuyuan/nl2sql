"""
Auth Service 数据模型
"""
from pydantic import BaseModel
from typing import Optional, List


class User(BaseModel):
    """用户信息模型"""
    username: str
    role: str
    areas: List[str]
    department: Optional[str] = None


class AuthRequest(BaseModel):
    """认证请求"""
    token: str


class AuthResponse(BaseModel):
    """认证响应"""
    success: bool
    user: Optional[User] = None
    message: str = ""


class ExternalAuthConfig(BaseModel):
    """第三方认证配置"""
    url: str
    timeout: int = 10
    headers: dict = {}
