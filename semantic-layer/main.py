import os
from fastapi import FastAPI
from schema import SemanticRequest
from parser import parse
from parser_cube import cube_parser
from parser_llm import llm_parser

app = FastAPI(
    title="Semantic Layer API",
    description="NL2SQL Semantic Layer with Cube support",
)

# LLM 解析开关（默认启用，可通过环境变量禁用）
ENABLE_LLM_PARSER = os.getenv("ENABLE_LLM_PARSER", "true").lower() == "true"


@app.post("/semantic/parse")
def semantic_parse(req: SemanticRequest):
    """使用规则引擎解析（快速但有限）"""
    return parse(req.query)


@app.post("/semantic/parse-llm")
async def semantic_parse_llm(req: SemanticRequest):
    """使用 LLM 解析（支持复杂语义理解）"""
    if not ENABLE_LLM_PARSER:
        return {
            "error": "LLM 解析未启用，设置环境变量 ENABLE_LLM_PARSER=true",
            "hint": "可以在 parser_llm.py 中修改 LLM_API_URL 和 LLM_MODEL",
        }
    return await llm_parser.parse(req.query)


@app.post("/semantic/parse-hybrid")
async def semantic_parse_hybrid(req: SemanticRequest):
    """混合解析：先尝试 LLM，失败则回退到规则引擎"""
    try:
        if ENABLE_LLM_PARSER:
            result = await llm_parser.parse(req.query)
            return {
                "parser": "llm",
                **result.model_dump(),
            }
    except Exception as e:
        return {
            "parser": "fallback_to_rule",
            "warning": f"LLM 解析失败: {str(e)}，使用规则引擎",
            **parse(req.query).model_dump(),
        }
    return {
        "parser": "rule",
        **parse(req.query).model_dump(),
    }


# ========================
# Cube 管理接口
# ========================

@app.get("/cube/list")
def cube_list():
    """列出所有 Cube"""
    return cube_parser.list_cubes()


@app.get("/cube/{cube_name}")
def cube_detail(cube_name: str):
    """获取 Cube 详细信息"""
    detail = cube_parser.get_cube(cube_name)
    if not detail:
        return {"error": f"Cube '{cube_name}' 不存在"}
    return detail


@app.get("/cube/{cube_name}/query")
def cube_query(cube_name: str, query: str):
    """使用指定 Cube 查询"""
    result = cube_parser.build_query(query)
    result["cube_name"] = cube_name
    return result


@app.post("/cube/parse")
def cube_parse(req: SemanticRequest):
    """使用 Cube 引擎解析查询"""
    return cube_parser.parse(req.query)


@app.post("/cube/clear-cache")
def cube_clear_cache():
    """清除 Cube 缓存"""
    cube_parser.clear_cache()
    return {"message": "缓存已清除"}


@app.get("/cube/cache-stats")
def cube_cache_stats():
    """获取缓存统计"""
    return cube_parser.get_cache_stats()


@app.get("/cube/verify")
def cube_verify():
    """验证 Cube 配置"""
    cubes = cube_parser.list_cubes()
    results = []

    for cube in cubes:
        detail = cube_parser.get_cube(cube["name"])
        if detail:
            results.append({
                "cube": cube["name"],
                "valid": True,
                "metrics_count": len(detail.get("metrics", [])),
                "dimensions_count": len(detail.get("dimensions", [])),
                "filters_count": len(detail.get("filters", [])),
            })
        else:
            results.append({
                "cube": cube["name"],
                "valid": False,
                "error": "无法获取 Cube 详情",
            })

    return {
        "total": len(results),
        "valid": sum(1 for r in results if r["valid"]),
        "invalid": sum(1 for r in results if not r["valid"]),
        "results": results,
    }
