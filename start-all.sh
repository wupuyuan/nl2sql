#!/bin/bash

set -e

ROOT_DIR="$(dirname "$0")"
SERVICES=(
  "semantic-layer"
  "metrics-engine"
  "mcp-hub"
  "webUI"
  "agent-service"
)

echo "===== 开始一键启动 AI Platform 服务 ====="

for service in "${SERVICES[@]}"; do
  SCRIPT_PATH="$ROOT_DIR/$service/start.sh"

  echo
  echo "===== 处理服务: $service ====="

  if [ ! -f "$SCRIPT_PATH" ]; then
    echo "启动脚本不存在: $SCRIPT_PATH"
    exit 1
  fi

  bash "$SCRIPT_PATH"
done

echo
echo "===== 全部服务启动完成 ====="
