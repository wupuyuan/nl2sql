import json
import os
from pathlib import Path
from typing import Any, List, Optional

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


_CONFIG_PATH = Path(__file__).with_name("config.json")


def _load_config() -> dict:
    if _CONFIG_PATH.exists():
        return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


_config = _load_config()

MCP_HUB_URL = os.getenv("MCP_HUB_URL", "http://127.0.0.1:8000")
LLM_BASE_URL = os.getenv(
    "LLM_BASE_URL",
    _config.get("base_url", "http://localhost:1234"),
)
LLM_MODEL = os.getenv(
    "LLM_MODEL",
    _config.get("model", "qwen/qwen3.6-35b-a3b"),
)
LLM_API_KEY = os.getenv(
    "LLM_API_KEY",
    _config.get("api_key") or "",
)

_api_url = _config.get("api_url")
if _api_url:
    LLM_API_URL = os.getenv("LLM_API_URL", _api_url)
elif "/v1/chat/completions" in LLM_BASE_URL:
    LLM_API_URL = os.getenv("LLM_API_URL", LLM_BASE_URL)
else:
    LLM_API_URL = os.getenv("LLM_API_URL", f"{LLM_BASE_URL}/v1/chat/completions")

LLM_PROVIDER = "openai" if "/v1/chat/completions" in LLM_API_URL else "local"


app = FastAPI(
    title="Agent Service",
    description="Local LLM + MCP Hub orchestration service",
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
    with_llm: bool = Field(True, description="是否调用本地模型生成自然语言答案")
    temperature: float = Field(0.2, ge=0.0, le=2.0)
    token: str = Field("", description="认证 Token (X-Auth-Token)")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="当前用户消息")
    history: List[ChatMessage] = Field(default_factory=list, description="历史对话")
    with_llm: bool = Field(True, description="是否调用本地模型生成自然语言答案")
    temperature: float = Field(0.2, ge=0.0, le=2.0)
    token: str = Field("", description="认证 Token (X-Auth-Token)")


async def call_mcp_hub(query: str, token: str = "") -> dict:
    headers = {}
    if token:
        headers["X-Auth-Token"] = token
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"{MCP_HUB_URL}/nl2sql",
            params={"query": query},
            headers=headers,
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


def build_user_prompt(
    query: str,
    mcp_result: dict,
    history: Optional[List[ChatMessage]] = None,
) -> str:
    prompt_parts: List[str] = []

    history_lines: List[str] = []
    for item in history or []:
        if item.role not in {"system", "user", "assistant"}:
            continue
        if not item.content.strip():
            continue
        role_map = {
            "system": "系统",
            "user": "用户",
            "assistant": "助手",
        }
        history_lines.append(f"{role_map.get(item.role, item.role)}：{item.content}")

    if history_lines:
        prompt_parts.append("历史对话：\n" + "\n".join(history_lines))

    prompt_parts.append(
        "用户问题：\n"
        f"{query}\n\n"
        "系统查询结果：\n"
        f"{mcp_result}\n\n"
        "请基于以上结果给出最终回答。"
    )

    return "\n\n".join(prompt_parts)


def extract_local_llm_content(data: Any) -> str:
    if isinstance(data, str):
        return data.strip()

    if not isinstance(data, dict):
        raise RuntimeError("本地模型返回格式不支持")

    direct_fields = [
        data.get("output"),
        data.get("text"),
        data.get("response"),
        data.get("answer"),
        data.get("content"),
    ]
    for value in direct_fields:
        if isinstance(value, str) and value.strip():
            return value.strip()

    output = data.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "message":
                content = item.get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip()
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()

    message = data.get("message")
    if isinstance(message, str) and message.strip():
        return message.strip()
    if isinstance(message, dict):
        for key in ("content", "text"):
            value = message.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    choices = data.get("choices") or []
    if choices and isinstance(choices[0], dict):
        first_choice = choices[0]
        first_message = first_choice.get("message") or {}
        if isinstance(first_message, dict):
            content = first_message.get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()
        text = first_choice.get("text")
        if isinstance(text, str) and text.strip():
            return text.strip()

    raise RuntimeError("本地模型未返回有效内容")


def extract_local_llm_model(data: Any) -> str:
    if not isinstance(data, dict):
        return LLM_MODEL
    model = data.get("model") or data.get("model_instance_id")
    if isinstance(model, str) and model.strip():
        return model.strip()
    return LLM_MODEL


def extract_local_llm_usage(data: Any) -> Optional[dict[str, Any]]:
    if not isinstance(data, dict):
        return None

    usage = data.get("usage")
    if isinstance(usage, dict):
        return usage

    stats = data.get("stats")
    if not isinstance(stats, dict):
        return None

    return {
        "prompt_tokens": stats.get("input_tokens"),
        "completion_tokens": stats.get("total_output_tokens"),
        "reasoning_tokens": stats.get("reasoning_output_tokens"),
        "tokens_per_second": stats.get("tokens_per_second"),
        "time_to_first_token_seconds": stats.get("time_to_first_token_seconds"),
    }


async def call_llm(
    query: str,
    mcp_result: dict,
    history: Optional[List[ChatMessage]] = None,
    temperature: float = 0.2,
) -> dict:
    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(query, mcp_result, history)

    headers = {"Content-Type": "application/json"}
    if LLM_API_KEY:
        headers["Authorization"] = f"Bearer {LLM_API_KEY}"

    if LLM_PROVIDER == "openai":
        payload = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
        }
    else:
        payload = {
            "model": LLM_MODEL,
            "system_prompt": system_prompt,
            "input": user_prompt,
        }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            LLM_API_URL,
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    content = extract_local_llm_content(data)
    model = extract_local_llm_model(data)
    usage = extract_local_llm_usage(data)

    return {
        "answer": content,
        "model": model,
        "usage": usage,
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
    token: str = "",
) -> dict[str, Any]:
    mcp_result = await call_mcp_hub(query, token=token)

    llm_result: Optional[dict[str, Any]] = None
    answer = build_fallback_answer(query, mcp_result)

    if with_llm and mcp_result.get("status") == "success":
        try:
            llm_result = await call_llm(
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
            "provider": LLM_PROVIDER,
            "model": (llm_result or {}).get("model", LLM_MODEL if with_llm else None),
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
        "config_file": str(_CONFIG_PATH),
        "config_loaded": _CONFIG_PATH.exists(),
        "mcp_hub_url": MCP_HUB_URL,
        "llm_provider": LLM_PROVIDER,
        "llm_api_url": LLM_API_URL,
        "llm_model": LLM_MODEL,
    }


@app.post("/query")
async def query_api(payload: QueryRequest):
    return await run_agent(
        query=payload.query,
        with_llm=payload.with_llm,
        temperature=payload.temperature,
        token=payload.token,
    )


@app.post("/chat")
async def chat_api(payload: ChatRequest):
    result = await run_agent(
        query=payload.message,
        with_llm=payload.with_llm,
        temperature=payload.temperature,
        history=payload.history,
        token=payload.token,
    )
    return {
        "message": payload.message,
        "history_count": len(payload.history),
        **result,
    }
