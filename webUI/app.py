import json
import urllib.parse
from typing import Any

import httpx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ========================
# Page Config
# ========================
st.set_page_config(
    page_title="AI 自然语言转 SQL",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ========================
# CSS
# ========================
st.markdown(
    """
<style>
    .stChatMessage { padding: 0.5rem 0; }
    .sql-code {
        background: #1e293b;
        color: #e2e8f0;
        padding: 1rem;
        border-radius: 0.5rem;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 13px;
        overflow-x: auto;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .metric-card h3 { margin: 0; font-size: 24px; }
    .metric-card p { margin: 0; font-size: 12px; opacity: 0.9; }
</style>
""",
    unsafe_allow_html=True,
)

# ========================
# Constants
# ========================
DEFAULT_SEMANTIC_URL = "http://127.0.0.1:8000"
DEFAULT_AGENT_URL = "http://127.0.0.1:8003"

EXAMPLES = [
    "查询总销售额",
    "按产品统计销售额",
    "本月采购订单数",
    "查询利润",
    "北京地区正常订单",
]

# ========================
# State Init
# ========================
if "sessions" not in st.session_state:
    st.session_state.sessions = []
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "mode" not in st.session_state:
    st.session_state.mode = "chat"


# ========================
# Session Helpers
# ========================
def get_or_create_session():
    sid = st.session_state.current_session_id
    if not sid or not any(s["id"] == sid for s in st.session_state.sessions):
        session = {
            "id": str(pd.Timestamp.now().value),
            "title": "新会话",
            "mode": st.session_state.mode,
            "messages": [],
        }
        st.session_state.sessions.insert(0, session)
        st.session_state.current_session_id = session["id"]
    return st.session_state.current_session_id


def current_session():
    sid = get_or_create_session()
    for s in st.session_state.sessions:
        if s["id"] == sid:
            return s
    return None


def new_session():
    st.session_state.current_session_id = None
    get_or_create_session()


def update_session_title(text: str):
    sess = current_session()
    if sess and sess["title"] == "新会话":
        sess["title"] = text[:20] or "新会话"


def add_message(role: str, content: str, details: dict | None = None):
    sess = current_session()
    if sess:
        sess["messages"].append({"role": role, "content": content, "details": details})
        sess["mode"] = st.session_state.mode


# ========================
# API Clients
# ========================
async def call_agent_chat(message: str, history: list, temperature: float, agent_url: str):
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{agent_url}/chat",
            json={
                "message": message,
                "history": history,
                "with_llm": True,
                "temperature": temperature,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def call_semantic_parse(query: str, method: str, semantic_url: str):
    endpoint = {
        "llm": "/semantic/parse-llm",
        "hybrid": "/semantic/parse-hybrid",
    }.get(method, "/semantic/parse")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{semantic_url}{endpoint}",
            json={"query": query},
        )
        resp.raise_for_status()
        return resp.json()


# ========================
# Visualization
# ========================
def auto_chart(data: list[dict], metrics: list[str], dimensions: list[str]):
    """根据数据自动推荐图表"""
    if not data:
        return None

    df = pd.DataFrame(data)

    # 如果只有一个数值结果（无维度），展示 KPI 卡片
    if len(df) == 1 and not dimensions:
        cols = st.columns(min(len(metrics), 4))
        for idx, metric in enumerate(metrics):
            if metric in df.columns:
                val = df[metric].iloc[0]
                with cols[idx % 4]:
                    st.metric(label=metric, value=f"{val:,.2f}" if isinstance(val, float) else str(val))
        return None

    # 有维度的情况
    if dimensions and metrics:
        dim = dimensions[0]
        metric = metrics[0]
        if dim in df.columns and metric in df.columns:
            # 条形图
            fig = px.bar(
                df,
                x=dim,
                y=metric,
                title=f"{metric} 按 {dim} 分布",
                text_auto=True,
                color=metric,
                color_continuous_scale="Blues",
            )
            fig.update_layout(height=400)
            return fig

    # 多指标对比（无维度）
    if len(df) == 1 and metrics:
        vals = [df[m].iloc[0] for m in metrics if m in df.columns]
        labels = [m for m in metrics if m in df.columns]
        if vals:
            fig = px.pie(
                names=labels,
                values=vals,
                title="指标占比",
                hole=0.4,
            )
            fig.update_layout(height=400)
            return fig

    # 默认折线图（如果有时间感知的列）
    time_cols = [c for c in df.columns if any(k in c.lower() for k in ["time", "date", "month", "day"])]
    if time_cols and metrics:
        fig = px.line(
            df,
            x=time_cols[0],
            y=[m for m in metrics if m in df.columns],
            title="趋势图",
        )
        fig.update_layout(height=400)
        return fig

    return None


def render_data_and_charts(data: list[dict], metrics: list[str], dimensions: list[str]):
    if not data:
        st.info("暂无查询数据")
        return

    df = pd.DataFrame(data)

    tab1, tab2 = st.tabs(["📊 数据表格", "📈 可视化"])

    with tab1:
        st.dataframe(df, use_container_width=True)

    with tab2:
        fig = auto_chart(data, metrics, dimensions)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("当前数据暂无合适的自动图表")

        # 用户自选图表
        if not df.empty:
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            all_cols = df.columns.tolist()
            if numeric_cols and len(all_cols) >= 2:
                st.divider()
                c1, c2 = st.columns(2)
                with c1:
                    x_col = st.selectbox("X 轴", all_cols, key="custom_x")
                with c2:
                    y_col = st.selectbox("Y 轴", numeric_cols, key="custom_y")
                chart_type = st.radio(
                    "图表类型",
                    ["条形图", "折线图", "散点图", "面积图"],
                    horizontal=True,
                    key="custom_type",
                )

                if chart_type == "条形图":
                    fig2 = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
                elif chart_type == "折线图":
                    fig2 = px.line(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
                elif chart_type == "散点图":
                    fig2 = px.scatter(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
                else:
                    fig2 = px.area(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")

                fig2.update_layout(height=400)
                st.plotly_chart(fig2, use_container_width=True)


# ========================
# Sidebar
# ========================
with st.sidebar:
    st.title("🤖 NL2SQL")

    if st.button("➕ 新建会话", use_container_width=True):
        new_session()
        st.rerun()

    st.divider()
    st.caption("工作模式")
    mode = st.radio(
        "mode",
        ["💬 AI 对话", "⚡ SQL 生成"],
        index=0 if st.session_state.mode == "chat" else 1,
        label_visibility="collapsed",
    )
    st.session_state.mode = "chat" if mode.startswith("💬") else "sql"

    st.divider()
    st.caption("服务配置")
    semantic_url = st.text_input("语义层地址", value=DEFAULT_SEMANTIC_URL)
    agent_url = st.text_input("Agent 地址", value=DEFAULT_AGENT_URL)

    if st.session_state.mode == "sql":
        parse_method = st.selectbox("解析方式", ["rule", "llm", "hybrid"])
    else:
        parse_method = "rule"
        temperature = st.slider("温度", 0.0, 2.0, 0.2, 0.1)

    st.divider()
    st.caption("会话历史")
    for s in st.session_state.sessions:
        icon = "💬" if s.get("mode") == "chat" else "⚡"
        label = f"{icon} {s['title']}"
        if st.button(label, key=f"sess_{s['id']}", use_container_width=True):
            st.session_state.current_session_id = s["id"]
            st.session_state.mode = s.get("mode", "chat")
            st.rerun()

# ========================
# Main Area
# ========================
sess = current_session()

# Title
if st.session_state.mode == "chat":
    st.header("💬 AI 数据分析助手")
    st.caption("输入业务问题，AI 会自动解析语义、生成 SQL 并给出分析结论")
else:
    st.header("⚡ SQL 生成器")
    st.caption("输入查询指令，快速获取语义解析和生成的 SQL")

# Examples
st.caption("试试这些例子：")
cols = st.columns(len(EXAMPLES))
for idx, ex in enumerate(EXAMPLES):
    with cols[idx]:
        if st.button(ex, key=f"ex_{idx}"):
            st.session_state["pending_query"] = ex
            st.rerun()

st.divider()

# Chat display
if sess and sess["messages"]:
    for msg in sess["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

            details = msg.get("details")
            if details and msg["role"] == "assistant":
                with st.expander("🔍 查看技术详情（语义解析 / SQL / 数据）"):
                    if details.get("semantic"):
                        st.subheader("语义解析")
                        st.json(details["semantic"])

                    if details.get("sql"):
                        st.subheader("生成 SQL")
                        st.code(details["sql"], language="sql")

                    if details.get("data") is not None:
                        st.subheader("查询数据")
                        semantic = details.get("semantic", {})
                        render_data_and_charts(
                            details["data"],
                            semantic.get("metrics", []),
                            semantic.get("dimensions", []),
                        )

                    if details.get("llm"):
                        st.subheader("LLM 信息")
                        st.json(details["llm"])
else:
    st.info("👋 开始一个新的对话吧！")

# Input
query = st.chat_input("输入你的问题...")
if not query and "pending_query" in st.session_state:
    query = st.session_state.pop("pending_query")

if query:
    add_message("user", query)
    update_session_title(query)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("🤔 思考中...")

        try:
            if st.session_state.mode == "chat":
                history = [
                    {"role": m["role"], "content": m["content"]}
                    for m in sess["messages"][:-1]
                    if m["role"] in ("user", "assistant")
                ]

                import asyncio

                result = asyncio.run(
                    call_agent_chat(
                        query, history, temperature, agent_url
                    )
                )

                answer = result.get("answer", "无回答")
                details = {
                    "semantic": result.get("semantic"),
                    "sql": result.get("sql"),
                    "data": result.get("data"),
                    "llm": result.get("llm"),
                }

                placeholder.markdown(answer)

                with st.expander("🔍 查看技术详情"):
                    if details["semantic"]:
                        st.subheader("语义解析")
                        st.json(details["semantic"])
                    if details["sql"]:
                        st.subheader("生成 SQL")
                        st.code(details["sql"], language="sql")
                    if details["data"] is not None:
                        st.subheader("查询数据")
                        render_data_and_charts(
                            details["data"],
                            details["semantic"].get("metrics", []) if details["semantic"] else [],
                            details["semantic"].get("dimensions", []) if details["semantic"] else [],
                        )
                    if details["llm"]:
                        st.subheader("LLM 信息")
                        st.json(details["llm"])

                add_message("assistant", answer, details)

            else:
                import asyncio

                result = asyncio.run(
                    call_semantic_parse(query, parse_method, semantic_url)
                )

                if result.get("error"):
                    placeholder.error(f"解析错误：{result['error']}")
                    add_message("assistant", f"解析错误：{result['error']}", {"error": True})
                else:
                    sql = result.get("sql", "")
                    content = (
                        f"✅ 已生成 SQL，共识别 **{len(result.get('metrics', []))}** 个指标、"
                        f"**{len(result.get('filters', []))}** 个过滤条件。"
                    ) if sql else "语义解析完成，但未生成 SQL。"

                    placeholder.markdown(content)

                    details = {
                        "semantic": {
                            "intent": result.get("intent"),
                            "metrics": result.get("metrics"),
                            "dimensions": result.get("dimensions"),
                            "filters": result.get("filters"),
                            "time_range": result.get("time_range"),
                            "warnings": result.get("warnings"),
                            "limit": result.get("limit"),
                        },
                        "sql": sql,
                        "data": result.get("data"),
                    }

                    with st.expander("🔍 查看技术详情"):
                        st.subheader("语义解析")
                        st.json(details["semantic"])
                        if sql:
                            st.subheader("生成 SQL")
                            st.code(sql, language="sql")
                        if details["data"] is not None:
                            st.subheader("查询数据")
                            render_data_and_charts(
                                details["data"],
                                result.get("metrics", []),
                                result.get("dimensions", []),
                            )

                    add_message("assistant", content, details)

        except Exception as e:
            placeholder.error(f"请求失败：{e}")
            add_message("assistant", f"请求失败：{e}", {"error": True})

    st.rerun()
