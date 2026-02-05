#!/bin/bash
# Daily Report 安装脚本

set -e

echo "🔧 安装依赖..."

# 检查并安装Python依赖
if ! python3 -c "import flask" 2>/dev/null; then
    echo "安装 Python3-pip..."
    sudo apt-get update -qq
    sudo apt-get install -y python3-pip python3-flask python3-psutil 2>/dev/null || {
        echo "尝试使用pip安装..."
        python3 -m pip install --user flask flask-cors psutil 2>/dev/null || {
            echo "❌ 无法安装依赖，请手动安装:"
            echo "   sudo apt-get install python3-pip"
            echo "   python3 -m pip install flask flask-cors psutil"
            exit 1
        }
    }
fi

echo "✅ 依赖安装完成"

# 创建systemd服务
echo "🔧 配置开机自启动..."

SERVICE_FILE="/etc/systemd/system/dailyreport.service"
WORK_DIR="/home/jun663/.openclaw/workspace/dailyreport-claw"

sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Daily Report Web Dashboard
After=network.target

[Service]
Type=simple
User=jun663
WorkingDirectory=$WORK_DIR
ExecStart=/usr/bin/python3 $WORK_DIR/server.py
Restart=always
RestartSec=10
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
EOF

# 重新加载systemd
sudo systemctl daemon-reload

echo "✅ systemd服务配置完成"
echo ""
echo "📝 后续步骤:"
echo "   1. 启动服务: sudo systemctl start dailyreport"
echo "   2. 开机自启: sudo systemctl enable dailyreport"
echo "   3. 查看状态: sudo systemctl status dailyreport"
echo "   4. 访问页面: http://localhost:8080"
echo ""
