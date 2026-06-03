"""
Policy Tool - 调用 Policy Engine 进行 ABAC 策略评估
"""

import httpx
import os

POLICY_ENGINE_URL = os.getenv("POLICY_ENGINE_URL", "http://127.0.0.1:8005")


async def evaluate_policy(user: dict, semantic_dsl: dict) -> dict:
    """
    评估 ABAC 策略，返回增强后的 DSL

    参数：
        user: 用户信息（username, role, areas, department）
        semantic_dsl: Semantic Layer 解析出的 DSL

    返回：
        {
            "allowed": True/False,
            "enhanced_dsl": {...},
            "reason": "...",
            "abac_applied": True/False
        }
    """
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{POLICY_ENGINE_URL}/policy/evaluate",
            json={
                "user": user,
                "semantic_dsl": semantic_dsl,
            }
        )
        return resp.json()
