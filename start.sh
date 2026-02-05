#!/bin/bash
# 启动阿呆控制台

cd /home/jun663/.openclaw/workspace/dailyreport-claw

echo "========================================"
echo "  🤖 阿呆控制台 - 启动中..."
echo "========================================"
echo ""

# 检查依赖
echo "📦 检查Python依赖..."
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Flask未安装！"
    echo ""
    echo "请先运行以下命令安装依赖："
    echo "  bash scripts/install_deps.sh"
    echo ""
    exit 1
fi

python3 -c "import psutil" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ psutil未安装！"
    echo ""
    echo "请先运行以下命令安装依赖："
    echo "  bash scripts/install_deps.sh"
    echo ""
    exit 1
fi

echo "✅ 依赖检查通过！"
echo ""

# 启动服务器
echo "🚀 启动Web服务器（端口8080）..."
echo ""
echo "访问地址："
echo "  - 本地: http://localhost:8080"
echo "  - 局域网: http://$(hostname -I | awk '{print $1}'):8080"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""
echo "========================================"
echo ""

python3 server.py
