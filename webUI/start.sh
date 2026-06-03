#!/bin/bash

CMD="python -m chainlit run chainlit_app.py --port 3010 --host 0.0.0.0"
DIR="$(dirname "$0")"

echo "===== 关闭旧的 webUI 进程 ====="
pid=$(ps -ef | grep "python -m chainlit run chainlit_app.py" | grep -v grep | awk '{print $2}')

if [ -n "$pid" ]; then
  kill -9 $pid
  echo "已杀死进程 PID: $pid"
  sleep 1
fi

echo "===== 启动新的 Chainlit webUI ====="
cd "$DIR"
nohup $CMD > app.log 2>&1 &

echo "启动成功！日志：$DIR/app.log"
echo "访问地址：http://127.0.0.1:3010"
echo "最新进程："
ps -ef | grep "chainlit" | grep -v grep
