#!/usr/bin/env python3
"""
依赖检查和安装指南
"""
import sys
import subprocess

def check_dependency(module_name, package_name):
    """检查依赖是否已安装"""
    try:
        __import__(module_name)
        print(f"✅ {module_name} 已安装")
        return True
    except ImportError:
        print(f"❌ {module_name} 未安装")
        return False

def main():
    print("🔍 检查Python依赖...")
    print("")

    dependencies = [
        ("flask", "flask"),
        ("flask_cors", "flask-cors"),
        ("psutil", "psutil")
    ]

    missing = []
    for module, package in dependencies:
        if not check_dependency(module, package):
            missing.append(package)

    print("")
    if missing:
        print("⚠️  缺少以下依赖：")
        for pkg in missing:
            print(f"   - {pkg}")
        print("")
        print("📦 安装命令：")
        print(f"   pip3 install --user {' '.join(missing)}")
        print("")
        print("💡 如果没有pip3，请先安装：")
        print("   sudo apt update && sudo apt install python3-pip")
        sys.exit(1)
    else:
        print("✅ 所有依赖已安装！可以启动服务器了：")
        print("   python3 server.py")
        sys.exit(0)

if __name__ == '__main__':
    main()
