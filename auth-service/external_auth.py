"""
外部认证接口调用模块

说明：
- 本模块保留调用第三方认证服务的代码框架
- 当前使用本地模拟数据（users.py）进行认证
- 生产环境可替换为对接企业 IAM、SSO、OAuth2 等服务
"""

import os
import httpx
from typing import Optional


# 第三方认证服务配置（生产环境使用）
EXTERNAL_AUTH_URL = os.getenv("EXTERNAL_AUTH_URL", "")
EXTERNAL_AUTH_TIMEOUT = int(os.getenv("EXTERNAL_AUTH_TIMEOUT", "10"))


async def call_external_auth(token: str) -> Optional[dict]:
    """
    调用第三方认证接口验证 Token

    参数：
        token: 用户认证 Token

    返回：
        认证成功返回用户信息 dict，失败返回 None

    示例（对接企业 IAM）：
        async with httpx.AsyncClient(timeout=EXTERNAL_AUTH_TIMEOUT) as client:
            resp = await client.post(
                f"{EXTERNAL_AUTH_URL}/verify",
                headers={"Authorization": f"Bearer {token}"}
            )
            if resp.status_code == 200:
                return resp.json()
            return None
    """
    # ============================================================
    # 生产环境：取消下方注释，接入第三方认证服务
    # ============================================================
    # if not EXTERNAL_AUTH_URL:
    #     return None
    #
    # async with httpx.AsyncClient(timeout=EXTERNAL_AUTH_TIMEOUT) as client:
    #     resp = await client.post(
    #         f"{EXTERNAL_AUTH_URL}/verify",
    #         headers={"Authorization": f"Bearer {token}"}
    #     )
    #     if resp.status_code == 200:
    #         data = resp.json()
    #         return {
    #             "username": data.get("username"),
    #             "role": data.get("role", "viewer"),
    #             "areas": data.get("areas", []),
    #             "department": data.get("department"),
    #         }
    #     return None
    # ============================================================

    # 当前：本地模拟，返回 None 表示未启用外部认证
    return None


async def call_external_permission_check(
    username: str,
    resource: str,
    action: str
) -> bool:
    """
    调用第三方权限服务进行细粒度权限检查

    生产环境可对接：
        - 企业 IAM 系统
        - Casbin 策略中心
        - Oso 策略引擎
        - 自研权限中台
    """
    # ============================================================
    # 生产环境：取消下方注释，接入第三方权限服务
    # ============================================================
    # if not EXTERNAL_AUTH_URL:
    #     return True
    #
    # async with httpx.AsyncClient(timeout=EXTERNAL_AUTH_TIMEOUT) as client:
    #     resp = await client.post(
    #         f"{EXTERNAL_AUTH_URL}/permission/check",
    #         json={
    #             "username": username,
    #             "resource": resource,
    #             "action": action,
    #         }
    #     )
    #     if resp.status_code == 200:
    #         return resp.json().get("allowed", False)
    #     return False
    # ============================================================

    # 当前：本地模拟，返回 True 表示未启用外部权限检查
    return True
