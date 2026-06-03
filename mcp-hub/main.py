import httpx
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from tools.semantic_tool import semantic_parse
from tools.metrics_tool import execute_metrics
from tools.auth_tool import verify_token, check_permission
from tools.policy_tool import evaluate_policy

SEMANTIC_SERVICE_URL = "http://127.0.0.1:8001"


class SemanticRequest(BaseModel):
    query: str


app = FastAPI(
    title="MCP Hub",
    description="Natural Language → Auth → Semantic Layer → Policy → Metrics Engine",
    version="0.2.0"
)

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "service": "mcp-hub",
        "status": "running",
        "version": "0.2.0"
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "modules": ["auth", "semantic", "policy", "metrics"]
    }


@app.get("/nl2sql")
async def nl2sql(
    query: str,
    x_auth_token: str = Header(None, alias="X-Auth-Token")
):
    """
    统一 NL2SQL 查询入口（带权限控制）

    请求头：
        X-Auth-Token: token_cipher_op / token_beijing / token_shanghai

    流程：
        1. Auth Module 认证 + RBAC 检查
        2. Semantic Layer 语义解析
        3. Policy Engine ABAC 数据级权限过滤
        4. Metrics Engine SQL 生成与执行
    """
    try:
        # ====================
        # Step0 Auth Module（认证 + RBAC）
        # ====================
        token = x_auth_token
        if not token:
            return {
                "query": query,
                "status": "error",
                "message": "缺少认证 Token，请在请求头中设置 X-Auth-Token"
            }

        auth_result = await verify_token(token)
        if not auth_result.get("success"):
            return {
                "query": query,
                "status": "error",
                "message": f"认证失败: {auth_result.get('message')}"
            }

        user = auth_result.get("user", {})

        # RBAC 权限检查
        rbac_result = await check_permission(token, action="query")
        if not rbac_result.get("allowed"):
            return {
                "query": query,
                "status": "error",
                "message": f"权限不足: {rbac_result.get('reason', '无权执行查询操作')}"
            }

        # ====================
        # Step1 Semantic Layer
        # ====================
        semantic_result = await semantic_parse(query)

        # ====================
        # Step2 Policy Engine（ABAC）
        # ====================
        policy_result = await evaluate_policy(user, semantic_result)
        if not policy_result.get("allowed"):
            return {
                "query": query,
                "status": "error",
                "message": f"策略拒绝: {policy_result.get('reason')}"
            }

        enhanced_dsl = policy_result.get("enhanced_dsl", semantic_result)

        # ====================
        # Step3 Metrics Engine
        # ====================
        metrics_result = await execute_metrics(enhanced_dsl)

        return {
            "query": query,
            "user": {
                "username": user.get("username"),
                "role": user.get("role"),
                "areas": user.get("areas"),
            },
            "semantic": semantic_result,
            "abac": {
                "applied": policy_result.get("abac_applied", False),
                "reason": policy_result.get("reason", ""),
            },
            "sql": metrics_result.get("sql"),
            "data": metrics_result.get("data"),
            "status": metrics_result.get("status")
        }

    except Exception as e:
        return {
            "query": query,
            "status": "error",
            "message": str(e)
        }


@app.post("/tool/semantic_parse")
async def semantic_parse_api(payload: dict):
    query = payload.get("query", "")
    result = await semantic_parse(query)
    return result


@app.post("/tool/metrics_execute")
async def metrics_execute_api(payload: dict):
    result = await execute_metrics(payload)
    return result


# ========================
# Semantic Layer Proxy
# ========================

@app.post("/semantic/parse")
async def semantic_parse_proxy(req: SemanticRequest):
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{SEMANTIC_SERVICE_URL}/semantic/parse",
            json={"query": req.query}
        )
        result = resp.json()
        metrics_result = await execute_metrics(result)
        result["sql"] = metrics_result.get("sql", "")
        return result


@app.post("/semantic/parse-llm")
async def semantic_parse_llm_proxy(req: SemanticRequest):
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{SEMANTIC_SERVICE_URL}/semantic/parse-llm",
            json={"query": req.query}
        )
        result = resp.json()
        metrics_result = await execute_metrics(result)
        result["sql"] = metrics_result.get("sql", "")
        return result


@app.post("/semantic/parse-hybrid")
async def semantic_parse_hybrid_proxy(req: SemanticRequest):
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{SEMANTIC_SERVICE_URL}/semantic/parse-hybrid",
            json={"query": req.query}
        )
        result = resp.json()
        metrics_result = await execute_metrics(result)
        result["sql"] = metrics_result.get("sql", "")
        return result
