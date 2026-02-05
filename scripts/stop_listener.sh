#!/bin/bash
# 停止任务监听器

echo "🛑 停止任务监听器..."

if pgrep -f "python3.*task_listener.py" > /dev/null; then
    pkill -f "python3.*task_listener.py"
    echo "✅ 任务监听器已停止"
else
    echo "⚠️  任务监听器未运行"
fi
