#!/bin/bash
# Daily Report 开机自启动配置脚本

set -e

echo "🔧 配置开机自启动..."

SERVICE_NAME="dailyreport"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
WORK_DIR="/home/jun663/.openclaw/workspace/dailyreport-claw"

# 检查是否已有root权限
if [ "$EUID" -ne 0 ]; then 
    echo "❌ 需要sudo权限来配置systemd服务"
    echo "请运行: sudo bash $0"
    exit 1
fi

echo "📝 创建systemd服务文件..."

cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Daily Report Web Dashboard - 阿呆控制台
After=network.target

[Service]
Type=simple
User=jun663
WorkingDirectory=$WORK_DIR
ExecStart=/usr/bin/python3 $WORK_DIR/server.py
Restart=always
RestartSec=10
Environment="PYTHONUNBUFFERED=1"
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "🔄 重新加载systemd配置..."
systemctl daemon-reload

echo "✅ 启用开机自启动..."
systemctl enable $SERVICE_NAME

echo "🚀 启动服务..."
systemctl restart $SERVICE_NAME

sleep 2

echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║   ✅ 开机自启动配置完成！                             ║"
echo "╠═══════════════════════════════════════════════════════╣"
echo "║   常用命令:                                           ║"
echo "║   启动服务: sudo systemctl start dailyreport          ║"
echo "║   停止服务: sudo systemctl stop dailyreport           ║"
echo "║   重启服务: sudo systemctl restart dailyreport        ║"
echo "║   查看状态: sudo systemctl status dailyreport         ║"
echo "║   查看日志: sudo journalctl -u dailyreport -f         ║"
echo "╠═══════════════════════════════════════════════════════╣"
echo "║   访问地址:                                           ║"
echo "║   http://localhost:8080                               ║"
echo "║   http://10.10.1.9:8080                               ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# 显示服务状态
systemctl status $SERVICE_NAME --no-pager
