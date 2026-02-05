#!/usr/bin/env python3
"""
Daily Report Web Server - 无依赖版本
使用Python标准库，无需安装Flask
"""
import json
import sys
import os
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs
import datetime

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

class APIHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.data_collector = None
        super().__init__(*args, **kwargs)

    def do_GET(self):
        # 初始化数据收集器
        if self.data_collector is None:
            from data_collector import DataCollector
            from system_monitor import SystemMonitor
            config_path = Path(__file__).parent / 'config.json'
            self.data_collector = DataCollector(config_path)
            self.monitor = SystemMonitor(config_path)

        # API路由
        if self.path == '/api/data' or self.path.startswith('/api/data/'):
            self.handle_api_request()
        elif self.path == '/api/system':
            self.handle_system_request()
        elif self.path == '/health':
            self.handle_health_request()
        else:
            # 静态文件
            super().do_GET()

    def do_POST(self):
        # 初始化数据收集器
        if self.data_collector is None:
            from data_collector import DataCollector
            from system_monitor import SystemMonitor
            config_path = Path(__file__).parent / 'config.json'
            self.data_collector = DataCollector(config_path)
            self.monitor = SystemMonitor(config_path)

        # POST API路由
        if self.path == '/api/task/create':
            self.handle_create_task()
        elif self.path == '/api/task/update':
            self.handle_update_task()
        else:
            self.send_error_response("Unknown API endpoint")

    def handle_api_request(self):
        """处理API数据请求"""
        try:
            # 解析时间筛选
            time_filter = 'today'
            if self.path.startswith('/api/data/'):
                time_filter = self.path.split('/')[-1]
                valid_filters = ['today', 'week', 'month', 'all']
                if time_filter not in valid_filters:
                    time_filter = 'today'

            # 收集数据
            system = self.data_collector.get_system_status()
            self.monitor.update_status(system)

            data = {
                "system": system,
                "stats": self.data_collector.get_stats(time_filter),
                "tasks": self.data_collector.get_tasks(time_filter, include_user_tasks=True),
                "interactions": self.data_collector.get_interactions(time_filter),
                "reflection": self.data_collector.get_reflection()
            }

            self.send_json_response(data)
        except Exception as e:
            self.send_error_response(str(e))

    def handle_system_request(self):
        """仅返回系统状态"""
        try:
            system = self.data_collector.get_system_status()
            self.send_json_response(system)
        except Exception as e:
            self.send_error_response(str(e))

    def handle_health_request(self):
        """健康检查"""
        self.send_json_response({
            "status": "ok",
            "service": "dailyreport-claw",
            "timestamp": datetime.datetime.now().isoformat()
        })

    def handle_create_task(self):
        """创建新任务"""
        try:
            # 读取POST数据
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            description = data.get('description', '')
            user_message = data.get('user_message', '')

            if not description:
                self.send_error_response("Missing required field: description")
                return

            # 创建任务
            task_id = self.data_collector.create_task(description, user_message)

            self.send_json_response({
                "success": True,
                "task_id": task_id,
                "message": "任务创建成功"
            })

        except Exception as e:
            self.send_error_response(str(e))

    def handle_update_task(self):
        """更新任务状态"""
        try:
            # 读取POST数据
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            task_id = data.get('task_id')
            status = data.get('status')
            result = data.get('result', '')

            if not task_id or not status:
                self.send_error_response("Missing required fields: task_id, status")
                return

            # 验证状态值
            valid_statuses = ['running', 'completed', 'failed']
            if status not in valid_statuses:
                self.send_error_response(f"Invalid status. Must be one of: {valid_statuses}")
                return

            # 更新任务
            success = self.data_collector.update_task(task_id, status, result)

            if success:
                self.send_json_response({
                    "success": True,
                    "message": "任务更新成功"
                })
            else:
                self.send_error_response("Task not found")

        except Exception as e:
            self.send_error_response(str(e))

    def send_json_response(self, data):
        """发送JSON响应"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def send_error_response(self, error):
        """发送错误响应"""
        self.send_response(500)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"error": error}).encode('utf-8'))

    def end_headers(self):
        # 添加CORS头
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def log_message(self, format, *args):
        # 自定义日志格式
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {format % args}")


def main():
    # 读取配置
    config_path = Path(__file__).parent / 'config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)

    server_config = config.get('server', {})
    host = server_config.get('host', '0.0.0.0')
    port = server_config.get('port', 8080)

    # 切换到web目录
    os.chdir(Path(__file__).parent / 'web')

    print(f"""
    ╔═══════════════════════════════════════════════════════╗
    ║   🤖 阿呆的实时控制台                                  ║
    ╠═══════════════════════════════════════════════════════╣
    ║   启动成功！                                           ║
    ║   本地访问: http://localhost:{port}                    ║
    ║   局域网访问: http://YOUR_IP:{port}                    ║
    ╚═══════════════════════════════════════════════════════╝
    """)

    # 创建服务器
    server = HTTPServer((host, port), APIHandler)
    print(f"✅ 服务器运行在 {host}:{port}")
    print("按 Ctrl+C 停止服务器")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 服务器已停止")
        server.shutdown()


if __name__ == '__main__':
    main()
