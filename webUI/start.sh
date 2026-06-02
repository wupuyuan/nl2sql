#!/bin/bash

CMD="python -m http.server 8080 --bind 127.0.0.1"
DIR="$(dirname "$0")"

echo "===== 关闭旧的 webUI 静态服务进程 ====="
pid=$(ps -ef | grep "$CMD" | grep -v grep | awk '{print $2}')

if [ -n "$pid" ]; then
  kill -9 $pid
  echo "已杀死进程 PID: $pid"
  sleep 1
fi

echo "===== 启动新的 webUI 静态服务 ====="
cd "$DIR"
nohup $CMD > app.log 2>&1 &

echo "启动成功！日志：$DIR/app.log"
echo "访问地址：http://127.0.0.1:8080/index.html"
echo "最新进程："
ps -ef | grep "$CMD" | grep -v grep
