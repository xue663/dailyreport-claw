#!/bin/bash
# 快速安装Python依赖脚本

echo "📦 安装Python依赖..."

# 尝试使用pip安装
if command -v pip3 &> /dev/null; then
    echo "使用pip3安装..."
    pip3 install --user flask flask-cors psutil
    echo "✅ 安装完成！"
    exit 0
fi

# 如果pip不存在，尝试使用apt安装系统包
if command -v apt &> /dev/null; then
    echo "pip3未找到，尝试使用apt安装系统包..."
    echo "需要sudo权限，请输入密码："

    # 安装python3-pip和flask
    sudo apt update
    sudo apt install -y python3-pip python3-flask python3-psutil

    # 然后用pip安装flask-cors
    pip3 install --user flask-cors

    echo "✅ 安装完成！"
    exit 0
fi

echo "❌ 无法找到pip3或apt，请手动安装Python依赖："
echo "   pip3 install flask flask-cors psutil"
exit 1
