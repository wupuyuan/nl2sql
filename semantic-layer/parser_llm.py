import os
import json
from pathlib import Path
import httpx
from typing import Optional, List, Dict, Any
from models import Filter, SemanticResponse


# 尝试读取 agent-service 的 config.json（与主服务共用配置）
_config_path = Path(__file__).resolve().parent.parent / "agent-service" / "config.json"
_shared_config = {}
if _config_path.exists():
    try:
        _shared_config = json.loads(_config_path.read_text(encoding="utf-8"))
    except Exception:
        pass

LLM_API_URL = os.getenv(
    "LLM_API_URL",
    _shared_config.get("api_url") or (_shared_config.get("base_url") or "http://192.168.0.106:1234") + "/v1/chat/completions",
)
LLM_MODEL = os.getenv("LLM_MODEL", _shared_config.get("model", "qwen/qwen3.6-35b-a3b"))
LLM_API_KEY = os.getenv("LLM_API_KEY", _shared_config.get("api_key", ""))


CUBE_SCHEMA_PROMPT = """
你是数据语义解析专家。你的任务是将用户的自然语言查询转换为结构化的语义 DSL。

## 可用的数据表：

### demo_orders（订单测试表）
描述：订单数据表，包含订单数量、金额、利润、成本等指标

**指标（Metrics）：**
- `order_cnt`: 订单数量（COUNT）
- `amount`: 订单总金额（SUM(amount)）
- `avg_amount`: 平均订单金额（AVG(amount)）
- `max_amount`: 最大订单金额（MAX(amount)）
- `min_amount`: 最小订单金额（MIN(amount)）
- `cost`: 成本（SUM(CASE WHEN order_type = 1 THEN amount ELSE 0 END)）
- `profit`: 利润（SUM(CASE WHEN order_type = 2 THEN amount ELSE 0 END) - SUM(CASE WHEN order_type = 1 THEN amount ELSE 0 END)）

**维度（Dimensions）：**
- `order_name`: 订单名称
- `order_detail`: 订单明细
- `order_status`: 订单状态（1=正常，-1=作废）
- `order_type`: 订单类型（1=采购，2=销售）
- `create_time`: 创建时间

**业务语义规则：**
- "成本" = cost（内部已固定采购订单）
- "利润" = profit（内部已处理销售-采购）
- "销售额" = amount where order_type=2
- "采购额" = amount where order_type=1
- "订单数" = order_cnt
- "平均金额" = avg_amount
- "今天/本周/本月" = create_time 时间范围过滤
- 默认只查有效订单（order_status=1），除非用户明确说"全部"或"作废"

**订单状态映射：**
- "正常" -> order_status=1
- "作废" -> order_status=-1

**订单类型映射：**
- "采购" -> order_type=1
- "销售" -> order_type=2

## 输出格式（JSON，不要输出其他内容）：
{
    "intent": "query",
    "metrics": ["metric1", "metric2"],
    "dimensions": ["dim1", "dim2"],
    "filters": [
        {"field": "field_name", "op": "=", "value": "value"}
    ],
    "time_range": null,
    "limit": 100
}

## 规则：
1. 如果用户查询"利润"或"成本"，直接返回对应的 metric（profit / cost），不要额外添加 order_type 过滤
2. 默认所有查询都加上 order_status=1，除非用户明确说"全部订单"或"作废订单"
3. 如果用户查询涉及"增长率/同比/环比"，需要识别时间范围并设置 time_range
4. 如果无法确定某些字段，使用合理的默认值
5. metrics 和 dimensions 至少有一个不为空
"""


class LLMParser:
    """基于 LLM 的语义解析器"""

    def __init__(self, api_url: str = None, model: str = None):
        self.api_url = api_url or LLM_API_URL
        self.model = model or LLM_MODEL

    async def parse(self, query: str) -> SemanticResponse:
        """使用 LLM 解析查询"""
        try:
            response = await self._call_llm(query)
            return self._parse_llm_response(response)
        except Exception as e:
            return SemanticResponse(
                intent="error",
                metrics=[],
                dimensions=[],
                filters=[],
                warnings=[f"LLM 解析失败: {str(e)}"],
                limit=100,
            )

    async def _call_llm(self, query: str) -> dict:
        """调用 LLM 服务"""
        messages = [
            {
                "role": "system",
                "content": CUBE_SCHEMA_PROMPT,
            },
            {
                "role": "user",
                "content": f"请解析以下查询：\n\n{query}",
            },
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 1000,
        }

        headers = {"Content-Type": "application/json"}
        if LLM_API_KEY:
            headers["Authorization"] = f"Bearer {LLM_API_KEY}"

        print(f"[LLM CALL] URL={self.api_url} model={self.model}")
        print(f"[LLM CALL] query={query}")

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    def _parse_llm_response(self, response: dict) -> SemanticResponse:
        """解析 LLM 返回的 JSON"""
        choices = response.get("choices") or []
        if not choices:
            raise RuntimeError("LLM 返回结果为空")

        content = choices[0].get("message", {}).get("content", "")

        # 提取 JSON 内容（可能包含在 markdown 代码块中）
        json_str = self._extract_json(content)

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            raise RuntimeError(f"无法解析 LLM 返回的 JSON: {content[:200]}")

        # 解析 filters
        filters = []
        for f in data.get("filters", []):
            filters.append(Filter(
                field=f["field"],
                op=f["op"],
                value=f["value"],
            ))

        return SemanticResponse(
            intent=data.get("intent", "query"),
            metrics=data.get("metrics", []),
            dimensions=data.get("dimensions", []),
            filters=filters,
            time_range=data.get("time_range"),
            warnings=[],
            limit=data.get("limit", 100),
        )

    @staticmethod
    def _extract_json(text: str) -> str:
        """从文本中提取 JSON"""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            json_lines = []
            in_code = False
            for line in lines:
                if line.startswith("```"):
                    in_code = not in_code
                    continue
                if in_code:
                    json_lines.append(line)
            return "\n".join(json_lines)
        return text


# 全局解析器实例
llm_parser = LLMParser()
