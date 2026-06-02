#!/bin/bash

CMD="python -m uvicorn main:app --host 0.0.0.0 --port 8003"
DIR="$(dirname "$0")"

echo "===== 关闭旧的 agent-service 进程 ====="
pid=$(pgrep -f "$CMD")

if [ -n "$pid" ]; then
  kill -9 $pid
  echo "已杀死进程 PID: $pid"
  sleep 1
fi

echo "===== 启动新的 agent-service 进程 ====="
cd "$DIR"
nohup $CMD > app.log 2>&1 &

echo "启动成功！日志：$DIR/app.log"
echo "最新进程："
pgrep -af "$CMD"
