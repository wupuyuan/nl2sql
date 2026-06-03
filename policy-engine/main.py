"""
Policy Engine - ABAC 策略引擎服务

职责：
- 接收用户信息和语义 DSL
- 根据用户属性评估 ABAC 策略
- 返回增强后的 DSL（包含数据级权限过滤）

说明：
- 当前使用本地配置模拟策略
- 生产环境可接入 Casbin、Oso 等开源策略引擎
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from schema import PolicyRequest, PolicyResponse
from engine import evaluate_abac_policy

app = FastAPI(
    title="Policy Engine",
    description="ABAC Policy Engine for Data Access Control",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"service": "policy-engine", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/policy/evaluate", response_model=PolicyResponse)
async def evaluate_policy(req: PolicyRequest):
    """
    评估 ABAC 策略

    请求体示例：
        {
            "user": {
                "username": "beijing",
                "role": "viewer",
                "areas": ["beijing"]
            },
            "semantic_dsl": {
                "intent": "query",
                "metrics": ["amount"],
                "filters": [],
                "dimensions": [],
                "warnings": [],
                "limit": 100
            }
        }

    响应示例：
        {
            "allowed": true,
            "enhanced_dsl": {
                "intent": "query",
                "metrics": ["amount"],
                "filters": [
                    {"field": "area", "op": "=", "value": "beijing"}
                ],
                "abac_applied": true,
                "abac_reason": "用户 beijing 只能访问区域: ['beijing']"
            },
            "reason": "策略评估通过",
            "abac_applied": true
        }
    """
    try:
        user = req.user
        semantic_dsl = req.semantic_dsl

        # 检查用户是否至少有一个可见区域
        areas = user.get("areas", [])
        if not areas:
            return PolicyResponse(
                allowed=False,
                reason="用户没有配置数据访问区域",
                abac_applied=False
            )

        # 评估 ABAC 策略
        enhanced_dsl = evaluate_abac_policy(user, semantic_dsl)

        return PolicyResponse(
            allowed=True,
            enhanced_dsl=enhanced_dsl,
            reason="策略评估通过",
            abac_applied=enhanced_dsl.get("abac_applied", False)
        )

    except Exception as e:
        return PolicyResponse(
            allowed=False,
            reason=f"策略评估异常: {str(e)}",
            abac_applied=False
        )


@app.post("/policy/check")
async def check_policy(req: PolicyRequest):
    """简化版策略检查，只返回是否允许"""
    result = await evaluate_policy(req)
    return {
        "allowed": result.allowed,
        "reason": result.reason,
    }


@app.get("/policy/config")
async def get_policy_config():
    """获取当前策略配置"""
    from config import ABAC_POLICIES
    return {
        "policies": ABAC_POLICIES,
        "note": "当前为本地模拟配置，生产环境可对接 Casbin / Oso",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
