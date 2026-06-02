import os
from typing import Any, List, Optional

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


MCP_HUB_URL = os.getenv("MCP_HUB_URL", "http://127.0.0.1:8000")
DEEPSEEK_API_URL = os.getenv(
    "DEEPSEEK_API_URL",
    "https://api.deepseek.com/chat/completions",
)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")


app = FastAPI(
    title="Agent Service",
    description="DeepSeek + MCP Hub orchestration service",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: str
    content: str


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="用户自然语言查询")
    with_llm: bool = Field(True, description="是否调用 DeepSeek 生成自然语言答案")
    temperature: float = Field(0.2, ge=0.0, le=2.0)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="当前用户消息")
    history: List[ChatMessage] = Field(default_factory=list, description="历史对话")
    with_llm: bool = Field(True, description="是否调用 DeepSeek 生成自然语言答案")
    temperature: float = Field(0.2, ge=0.0, le=2.0)


async def call_mcp_hub(query: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"{MCP_HUB_URL}/nl2sql",
            params={"query": query},
        )
        response.raise_for_status()
        return response.json()


def build_system_prompt() -> str:
    return (
        "你是一个面向业务用户的数据分析助手。"
        "你需要根据系统提供的查询结果，用中文给出简洁、准确、可读的回答。"
        "回答时优先输出业务结论，其次给出关键过滤条件。"
        "如果有 SQL，可以简要说明，不要输出过长推理过程。"
        "如果查询失败，要明确说明失败原因，并给出下一步建议。"
    )


def build_user_prompt(query: str, mcp_result: dict) -> str:
    return (
        "用户问题：\n"
        f"{query}\n\n"
        "系统查询结果：\n"
        f"{mcp_result}\n\n"
        "请基于以上结果给出最终回答。"
    )


async def call_deepseek(
    query: str,
    mcp_result: dict,
    history: Optional[List[ChatMessage]] = None,
    temperature: float = 0.2,
) -> dict:
    if not DEEPSEEK_API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY 未配置")

    messages: List[dict[str, str]] = [{"role": "system", "content": build_system_prompt()}]

    for item in history or []:
        if item.role not in {"system", "user", "assistant"}:
            continue
        messages.append({"role": item.role, "content": item.content})

    messages.append(
        {
            "role": "user",
            "content": build_user_prompt(query, mcp_result),
        }
    )

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": temperature,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            DEEPSEEK_API_URL,
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("DeepSeek 返回结果为空")

    message = choices[0].get("message") or {}
    content = message.get("content", "").strip()
    if not content:
        raise RuntimeError("DeepSeek 未返回有效内容")

    return {
        "answer": content,
        "model": data.get("model", DEEPSEEK_MODEL),
        "usage": data.get("usage"),
        "raw": data,
    }


def build_fallback_answer(query: str, mcp_result: dict) -> str:
    status = mcp_result.get("status")
    if status != "success":
        return f"查询失败：{mcp_result.get('message', '未知错误')}"

    semantic = mcp_result.get("semantic") or {}
    filters = semantic.get("filters") or []
    data = mcp_result.get("data") or []
    sql = mcp_result.get("sql") or ""

    parts = [f"已完成查询：{query}"]
    if filters:
        parts.append(f"过滤条件：{filters}")
    parts.append(f"返回记录数：{len(data)}")
    if sql:
        parts.append(f"执行 SQL：{sql}")

    if len(data) == 1:
        parts.append(f"结果：{data[0]}")
    elif len(data) > 1:
        parts.append(f"首条结果：{data[0]}")
    else:
        parts.append("当前没有查询到数据。")

    return "\n".join(parts)


async def run_agent(
    query: str,
    with_llm: bool,
    temperature: float,
    history: Optional[List[ChatMessage]] = None,
) -> dict[str, Any]:
    mcp_result = await call_mcp_hub(query)

    llm_result: Optional[dict[str, Any]] = None
    answer = build_fallback_answer(query, mcp_result)

    if with_llm and mcp_result.get("status") == "success":
        try:
            llm_result = await call_deepseek(
                query=query,
                mcp_result=mcp_result,
                history=history,
                temperature=temperature,
            )
            answer = llm_result["answer"]
        except Exception as exc:
            answer = (
                f"{answer}\n\n"
                f"LLM 增强未启用，原因：{str(exc)}"
            )

    return {
        "query": query,
        "answer": answer,
        "status": mcp_result.get("status", "unknown"),
        "semantic": mcp_result.get("semantic"),
        "sql": mcp_result.get("sql"),
        "data": mcp_result.get("data"),
        "llm": {
            "enabled": bool(with_llm),
            "provider": "deepseek",
            "model": (llm_result or {}).get("model", DEEPSEEK_MODEL if with_llm else None),
            "usage": (llm_result or {}).get("usage"),
        },
    }


@app.get("/")
async def root():
    return {
        "service": "agent-service",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "mcp_hub_url": MCP_HUB_URL,
        "deepseek_model": DEEPSEEK_MODEL,
        "deepseek_enabled": bool(DEEPSEEK_API_KEY),
    }


@app.post("/query")
async def query_api(payload: QueryRequest):
    return await run_agent(
        query=payload.query,
        with_llm=payload.with_llm,
        temperature=payload.temperature,
    )


@app.post("/chat")
async def chat_api(payload: ChatRequest):
    result = await run_agent(
        query=payload.message,
        with_llm=payload.with_llm,
        temperature=payload.temperature,
        history=payload.history,
    )
    return {
        "message": payload.message,
        "history_count": len(payload.history),
        **result,
    }
