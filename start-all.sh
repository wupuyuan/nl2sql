#!/bin/bash

ROOT_DIR="$(dirname "$0")"
SERVICES=(
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
echo "  semantic-layer: http://127.0.0.1:8001"
echo "  metrics-engine: http://127.0.0.1:8002"
echo "  mcp-hub:        http://127.0.0.1:8000"
echo "  agent-service:  http://127.0.0.1:8003"
echo "  webUI:          http://127.0.0.1:3100"
echo
