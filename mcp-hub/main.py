import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from tools.semantic_tool import semantic_parse
from tools.metrics_tool import execute_metrics

SEMANTIC_SERVICE_URL = "http://127.0.0.1:8001"


class SemanticRequest(BaseModel):
    query: str

app = FastAPI(
    title="MCP Hub",
    description="Natural Language → Semantic Layer → Metrics Engine",
    version="0.1.0"
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
        "status": "running"
    }


@app.get("/health")
async def health():
    return {
        "status": "ok"
    }


@app.get("/nl2sql")
async def nl2sql(query: str):

    try:

        # ====================
        # Step1 Semantic Layer
        # ====================
        semantic_result = await semantic_parse(query)

        # ====================
        # Step2 Metrics Engine
        # ====================
        metrics_result = await execute_metrics(
            semantic_result
        )

        return {
            "query": query,
            "semantic": semantic_result,
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
