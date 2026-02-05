#!/bin/bash
# 启动任务监听器

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

echo "🎯 启动任务监听器..."

# 检查是否已经在运行
if pgrep -f "python3.*task_listener.py" > /dev/null; then
    echo "⚠️  任务监听器已在运行"
    echo "PID: $(pgrep -f 'python3.*task_listener.py')"
    exit 0
fi

# 启动监听器
nohup python3 scripts/task_listener.py > logs/task_listener.log 2>&1 &
LISTENER_PID=$!

# 等待启动
sleep 2

# 检查是否成功启动
if ps -p $LISTENER_PID > /dev/null; then
    echo "✅ 任务监听器启动成功"
    echo "PID: $LISTENER_PID"
    echo "日志: logs/task_listener.log"
else
    echo "❌ 任务监听器启动失败"
    echo "查看日志: cat logs/task_listener.log"
    exit 1
fi
