#!/bin/bash
# 初始化脚本 - 创建数据文件和设置权限

echo "🔧 初始化阿呆控制台..."

PROJECT_DIR="/home/jun663/.openclaw/workspace/dailyreport-clow"
cd "$PROJECT_DIR"

# 创建数据目录
mkdir -p data

# 初始化数据文件
echo '[]' > data/tasks.json
echo '[]' > data/interactions.json
echo '{}' > data/system_status.json

# 设置权限
chmod +x server.py
chmod +x scripts/*.py

echo "✅ 初始化完成！"
echo ""
echo "📋 下一步："
echo "1. 安装依赖：pip3 install --user flask flask-cors psutil"
echo "2. 测试运行：python3 server.py"
echo "3. 访问：http://localhost:8080"
echo ""
