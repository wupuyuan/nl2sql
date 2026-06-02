import httpx

SEMANTIC_SERVICE_URL = "http://127.0.0.1:8001"

async def semantic_parse(query: str):
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{SEMANTIC_SERVICE_URL}/semantic/parse",
            json={"query": query}
        )
        return resp.json()
