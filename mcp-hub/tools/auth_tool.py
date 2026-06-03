"""
Auth Tool - 调用 Auth Service 进行认证鉴权
"""

import httpx
import os

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:8004")


async def verify_token(token: str) -> dict:
    """
    验证用户 Token

    返回：
        {"success": True, "user": {...}} 或 {"success": False, "message": "..."}
    """
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{AUTH_SERVICE_URL}/auth/verify",
            headers={"X-Auth-Token": token}
        )
        return resp.json()


async def check_permission(token: str, action: str = "query") -> dict:
    """
    RBAC 权限检查

    返回：
        {"allowed": True/False, "username": "...", "role": "...", "action": "..."}
    """
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{AUTH_SERVICE_URL}/auth/check",
            params={"action": action},
            headers={"X-Auth-Token": token}
        )
        return resp.json()
