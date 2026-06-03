#!/bin/bash

ROOT_DIR="$(dirname "$0")"
SERVICES=(
  "auth-service"
  "policy-engine"
  "semantic-layer"
  "metrics-engine"
  "mcp-hub"
  "agent-service"
  "webUI"
)

echo "===== 开始一键启动 AI Platform 服务 ====="

for service in "${SERVICES[@]}"; do
  SCRIPT_PATH="$ROOT_DIR/$service/start.sh"

  echo
  echo "===== 处理服务: $service ====="

  if [ ! -f "$SCRIPT_PATH" ]; then
    echo "启动脚本不存在: $SCRIPT_PATH，跳过"
    continue
  fi

  bash "$SCRIPT_PATH"
  sleep 2
done

echo
echo "===== 全部服务启动完成 ====="
echo
echo "服务端口:"
echo "  auth-service:   http://127.0.0.1:8004  (认证鉴权服务)"
echo "  policy-engine:  http://127.0.0.1:8005  (ABAC 策略引擎)"
echo "  semantic-layer: http://127.0.0.1:8001  (语义解析服务)"
echo "  metrics-engine: http://127.0.0.1:8002  (指标执行服务)"
echo "  mcp-hub:        http://127.0.0.1:8000  (统一网关)"
echo "  agent-service:  http://127.0.0.1:8003  (AI 智能编排)"
echo "  webUI:          http://127.0.0.1:3010  (AI 对话界面)"
echo
echo "测试用户 Token:"
echo "  token_cipher_op  (最高权限，北京+上海)"
echo "  token_beijing    (仅北京区域)"
echo "  token_shanghai   (仅上海区域)"
echo
