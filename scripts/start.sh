#!/bin/bash
# Daily Report 启动脚本

WORK_DIR="/home/jun663/.openclaw/workspace/dailyreport-claw"
cd "$WORK_DIR"

echo "🚀 启动阿呆控制台..."
python3 server.py
