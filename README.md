# NL2SQL AI 平台

## 测试用户

| 用户名 | 密码 | Token | 角色 | 可见区域 |
|--------|------|-------|------|----------|
| `cipher_op` | `550e8400-e29b-41d4-a716-446655440000` | `token_cipher_op` | admin | 北京 + 上海 |
| `beijing` | `660e8400-e29b-41d4-a716-446655440001` | `token_beijing` | viewer | 仅北京 |
| `shanghai` | `770e8400-e29b-41d4-a716-446655440002` | `token_shanghai` | viewer | 仅上海 |

## 快速测试

```bash
# 管理员查询（看到所有数据）
curl "http://127.0.0.1:8000/nl2sql?query=查询总销售额" \
  -H "X-Auth-Token: token_cipher_op"

# 北京用户查询（仅看到北京数据）
curl "http://127.0.0.1:8000/nl2sql?query=查询总销售额" \
  -H "X-Auth-Token: token_beijing"

# 上海用户查询（仅看到上海数据）
curl "http://127.0.0.1:8000/nl2sql?query=查询总销售额" \
  -H "X-Auth-Token: token_shanghai"
```

## 服务端口

| 服务 | 端口 |
|------|------|
| MCP Hub | 8000 |
| Auth Service | 8004 |
| Policy Engine | 8005 |
| Semantic Layer | 8001 |
| Metrics Engine | 8002 |
| Agent Service | 8003 |
| Web UI (Chainlit) | 3010 |
