"""
Policy Engine 数据模型
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class PolicyRequest(BaseModel):
    """策略评估请求"""
    user: dict
    semantic_dsl: dict


class PolicyResponse(BaseModel):
    """策略评估响应"""
    allowed: bool
    enhanced_dsl: Optional[dict] = None
    reason: str = ""
    abac_applied: bool = False


class UserInfo(BaseModel):
    """用户信息（简化版）"""
    username: str
    role: str
    areas: List[str]
    department: Optional[str] = None
