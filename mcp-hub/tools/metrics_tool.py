# mcp-hub/tools/metrics_tool.py

import httpx

METRICS_ENGINE_URL = "http://127.0.0.1:8002/execute"


async def execute_metrics(dsl: dict):

    async with httpx.AsyncClient(timeout=30) as client:

        resp = await client.post(
            METRICS_ENGINE_URL,
            json=dsl
        )

        resp.raise_for_status()

        return resp.json()
