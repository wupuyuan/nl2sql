#!/bin/bash

CMD="uvicorn main:app --host 0.0.0.0 --port 8005"
DIR="$(dirname "$0")"

echo "===== 关闭旧的 policy-engine 进程 ====="
pid=$(ps -ef | grep "$CMD" | grep -v grep | awk '{print $2}')

if [ -n "$pid" ]; then
  kill -9 $pid
  echo "已杀死进程 PID: $pid"
  sleep 1
fi

echo "===== 启动新的 policy-engine 进程 ====="
cd "$DIR"
nohup python -m $CMD > app.log 2>&1 &

echo "启动成功！日志：$DIR/app.log"
echo "最新进程："
ps -ef | grep "$CMD" | grep -v grep
