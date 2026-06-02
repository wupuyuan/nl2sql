import json
import os
import time
from collections import defaultdict
from typing import Any

import httpx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import chainlit as cl

# ========================
# Auth Config
# ========================
DEFAULT_TOKEN = os.getenv("CHAINLIT_TOKEN", "550e8400-e29b-41d4-a716-446655440000")
MAX_AUTH_FAILURES = 3
BAN_WINDOW_SECONDS = 3600

_ip_failures: dict[str, list[float]] = defaultdict(list)
_banned_ips: set[str] = set()


def _get_client_ip() -> str:
    try:
        req = cl.context.session.http_request
        forwarded = req.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if req.client:
            return req.client.host
    except Exception:
        pass
    return "unknown"


def _is_ip_banned(ip: str) -> bool:
    if ip in _banned_ips:
        return True
    now = time.time()
    failures = _ip_failures[ip]
    failures[:] = [t for t in failures if now - t < BAN_WINDOW_SECONDS]
    if len(failures) >= MAX_AUTH_FAILURES:
        _banned_ips.add(ip)
        return True
    return False


def _record_failure(ip: str):
    _ip_failures[ip].append(time.time())


def _clear_ban(ip: str):
    if ip in _banned_ips:
        _banned_ips.discard(ip)
    _ip_failures.pop(ip, None)


@cl.password_auth_callback
async def auth_callback(username: str, password: str):
    ip = _get_client_ip()
    if _is_ip_banned(ip):
        return None
    if username == "cipher_op" and password == DEFAULT_TOKEN:
        _clear_ban(ip)
        return cl.User(identifier="cipher_op", metadata={"role": "admin"})
    _record_failure(ip)
    if _is_ip_banned(ip):
        print(f"[SECURITY] IP {ip} banned after {MAX_AUTH_FAILURES} failed login attempts")
    return None


# 尝试挂载 IP 封禁中间件（在 HTTP 层彻底阻止被封禁 IP）
try:
    from chainlit.server import app as _cl_app
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import Response

    class IPBanMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            ip = request.headers.get("x-forwarded-for", "")
            if ip:
                ip = ip.split(",")[0].strip()
            elif request.client:
                ip = request.client.host
            else:
                ip = "unknown"
            if ip in _banned_ips:
                return Response("Access denied: IP banned", status_code=403)
            return await call_next(request)

    _cl_app.add_middleware(IPBanMiddleware)
except Exception:
    pass


# ========================
# Config
# ========================
AGENT_URL = os.getenv("AGENT_URL", "http://127.0.0.1:8003")
SEMANTIC_URL = os.getenv("SEMANTIC_URL", "http://127.0.0.1:8000")

EXAMPLES = [
    "查询总销售额",
    "按产品统计销售额",
    "本月采购订单数",
    "查询利润",
    "北京地区正常订单",
]

# ========================
# API Clients
# ========================
async def call_agent_chat(message: str, history: list, temperature: float = 0.2):
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{AGENT_URL}/chat",
            json={
                "message": message,
                "history": history,
                "with_llm": True,
                "temperature": temperature,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def call_semantic_parse(query: str, method: str = "rule"):
    endpoint = {
        "llm": "/semantic/parse-llm",
        "hybrid": "/semantic/parse-hybrid",
    }.get(method, "/semantic/parse")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{SEMANTIC_URL}{endpoint}",
            json={"query": query},
        )
        resp.raise_for_status()
        return resp.json()


# ========================
# Visualization
# ========================
def build_chart(data: list[dict], metrics: list[str], dimensions: list[str]):
    if not data:
        return None

    df = pd.DataFrame(data)

    # Single row + no dimensions => KPI metrics
    if len(df) == 1 and not dimensions:
        return None  # handled separately

    # Has dimensions => bar chart
    if dimensions and metrics:
        dim = dimensions[0]
        metric = metrics[0]
        if dim in df.columns and metric in df.columns:
            fig = px.bar(
                df, x=dim, y=metric,
                title=f"{metric} 按 {dim} 分布",
                text_auto=True,
                color=metric,
                color_continuous_scale="Blues",
            )
            fig.update_layout(height=400)
            return fig

    # Multiple metrics, single row => pie
    if len(df) == 1 and metrics:
        vals = [df[m].iloc[0] for m in metrics if m in df.columns]
        labels = [m for m in metrics if m in df.columns]
        if vals:
            fig = px.pie(names=labels, values=vals, title="指标占比", hole=0.4)
            fig.update_layout(height=400)
            return fig

    # Time-ish column => line
    time_cols = [c for c in df.columns if any(k in c.lower() for k in ("time", "date", "month", "day"))]
    if time_cols and metrics:
        fig = px.line(
            df, x=time_cols[0],
            y=[m for m in metrics if m in df.columns],
            title="趋势图",
        )
        fig.update_layout(height=400)
        return fig

    return None


# ========================
# Chainlit Events
# ========================
SCHEMA_DOC = """
### 📋 数据表结构：`demo_orders`

| 字段 | 类型 | 说明 |
|------|------|------|
| `order_id` | INT | 订单号（主键） |
| `order_name` | VARCHAR(100) | 订单名称 |
| `order_detail` | TEXT | 订单明细 |
| `order_type` | TINYINT | 1=采购，2=销售 |
| `amount` | DECIMAL(12,2) | 金额 |
| `order_status` | TINYINT | 1=正常，-1=作废 |
| `create_time` | DATETIME | 创建时间 |

### 📊 可用指标
| 指标 | 含义 |
|------|------|
| `order_cnt` | 订单数量 |
| `amount` | 订单总金额 |
| `avg_amount` | 平均订单金额 |
| `max_amount` | 最大订单金额 |
| `min_amount` | 最小订单金额 |
| `cost` | 成本（有效采购订单总金额） |
| `profit` | 利润（有效销售 - 有效采购） |

### 🔍 可用维度
`order_name`（订单名称）、`order_detail`（订单明细）、`order_status`（订单状态）、`order_type`（订单类型）、`create_time`（创建时间）

### 📝 常用查询示例
- "查一下总销售额"
- "本月采购订单数"
- "利润是多少"
- "成本统计"
"""


@cl.on_chat_start
async def on_chat_start():
    actions = [
        cl.Action(name="schema", value="show", label="📋 查看数据结构", payload={"value": "show"})
    ]
    await cl.Message(
        content="👋 你好！我是 **AI 数据分析助手**。\n\n"
                "输入你的业务问题，我会自动解析语义、生成 SQL 并给出分析结论。",
        actions=actions,
    ).send()


@cl.action_callback("schema")
async def on_schema(action: cl.Action):
    await cl.Message(content=SCHEMA_DOC).send()


@cl.on_message
async def on_message(message: cl.Message):
    query = message.content.strip()
    if not query:
        return

    # 帮助/数据结构关键词
    if query.lower() in ("help", "?", "数据结构", "schema", "数据说明"):
        await cl.Message(content=SCHEMA_DOC).send()
        return

    # Gather history
    history = []
    for m in cl.chat_context.to_openai():
        if m["role"] in ("user", "assistant"):
            history.append({"role": m["role"], "content": m["content"]})
    # Remove current message from history
    if history and history[-1]["role"] == "user" and history[-1]["content"] == query:
        history = history[:-1]

    # Mode: if message starts with /sql, use SQL mode
    mode = "sql" if query.startswith("/sql ") else "chat"
    if mode == "sql":
        query = query[5:].strip()

    msg = cl.Message(content="")
    await msg.send()

    try:
        if mode == "chat":
            async with cl.Step(name="🤖 调用 AI Agent...") as step:
                result = await call_agent_chat(query, history)
                answer = result.get("answer", "无回答")
                semantic = result.get("semantic")
                sql = result.get("sql")
                data = result.get("data")
                llm_info = result.get("llm")

            # Send answer
            msg.content = answer
            await msg.update()

            # Details as nested steps
            if semantic:
                async with cl.Step(name="📊 语义解析") as s:
                    s.output = json.dumps(semantic, ensure_ascii=False, indent=2)

            if sql:
                async with cl.Step(name="💻 生成 SQL") as s:
                    await cl.Message(content=f"```sql\n{sql}\n```", parent_id=s.id).send()

            if data is not None:
                async with cl.Step(name="📈 数据与图表") as s:
                    df = pd.DataFrame(data)
                    await cl.Message(
                        content=f"返回 **{len(df)}** 条记录",
                        parent_id=s.id,
                    ).send()

                    # KPI cards for single row
                    if len(df) == 1 and semantic:
                        metrics = semantic.get("metrics", [])
                        for metric in metrics:
                            if metric in df.columns:
                                val = df[metric].iloc[0]
                                await cl.Message(
                                    content=f"**{metric}**: `{val}`",
                                    parent_id=s.id,
                                ).send()

                    # Auto chart
                    fig = build_chart(data, semantic.get("metrics", []) if semantic else [], semantic.get("dimensions", []) if semantic else [])
                    if fig:
                        await cl.Message(
                            content="自动生成的图表：",
                            parent_id=s.id,
                        ).send()
                        await cl.Plotly(fig, parent_id=s.id).send()

                    # Data table
                    try:
                        await cl.Dataframe(data=df.to_dict("records"), name="数据", parent_id=s.id).send()
                    except Exception:
                        await cl.Message(content=df.to_markdown(index=False), parent_id=s.id).send()

            if llm_info:
                async with cl.Step(name="🧠 LLM 信息") as s:
                    s.output = json.dumps(llm_info, ensure_ascii=False, indent=2)

        else:
            # SQL mode
            async with cl.Step(name="⚡ 语义解析") as step:
                result = await call_semantic_parse(query, "rule")

            if result.get("error"):
                msg.content = f"❌ 解析错误：{result['error']}"
                await msg.update()
                return

            sql = result.get("sql", "")
            metrics = result.get("metrics", [])
            filters = result.get("filters", [])

            msg.content = (
                f"✅ 已生成 SQL，识别到 **{len(metrics)}** 个指标、"
                f"**{len(filters)}** 个过滤条件。"
            ) if sql else "语义解析完成，但未生成 SQL。"
            await msg.update()

            async with cl.Step(name="📊 语义解析结果") as s:
                s.output = json.dumps(result, ensure_ascii=False, indent=2)

            if sql:
                async with cl.Step(name="💻 SQL") as s:
                    await cl.Message(content=f"```sql\n{sql}\n```", parent_id=s.id).send()

            if result.get("data") is not None:
                data = result["data"]
                df = pd.DataFrame(data)
                async with cl.Step(name="📈 数据") as s:
                    await cl.Message(content=f"返回 **{len(df)}** 条记录", parent_id=s.id).send()
                    fig = build_chart(data, metrics, result.get("dimensions", []))
                    if fig:
                        await cl.Plotly(fig, parent_id=s.id).send()
                    try:
                        await cl.Dataframe(data=df.to_dict("records"), name="数据", parent_id=s.id).send()
                    except Exception:
                        await cl.Message(content=df.to_markdown(index=False), parent_id=s.id).send()

    except Exception as e:
        msg.content = f"❌ 请求失败：{e}"
        await msg.update()


