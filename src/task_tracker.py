#!/usr/bin/env python3
"""
任务追踪装饰器 - 自动记录任务执行状态
"""
import json
import time
import functools
from datetime import datetime
from pathlib import Path

class TaskTracker:
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / 'data'
        self.data_dir.mkdir(exist_ok=True)
        self.tasks_file = self.data_dir / 'tasks.json'

    def track(self, func):
        """装饰器：追踪任务执行"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            task_id = f"task_{int(time.time() * 1000)}"
            start_time = time.time()
            timestamp = datetime.now().isoformat()

            # 创建任务记录
            task = {
                "id": task_id,
                "description": self._generate_description(func, args, kwargs),
                "status": "running",
                "start_time": timestamp,
                "function": func.__name__,
                "module": func.__module__
            }

            # 保存running状态
            self._save_task(task)

            try:
                # 执行函数
                result = func(*args, **kwargs)

                # 更新为completed
                task["status"] = "completed"
                task["end_time"] = datetime.now().isoformat()
                task["duration"] = round(time.time() - start_time, 2)
                task["result"] = "success"

                self._save_task(task)
                return result

            except Exception as e:
                # 更新为failed
                task["status"] = "failed"
                task["end_time"] = datetime.now().isoformat()
                task["duration"] = round(time.time() - start_time, 2)
                task["error"] = str(e)

                self._save_task(task)
                raise

        return wrapper

    def _generate_description(self, func, args, kwargs):
        """生成任务描述（业务级别）"""
        func_name = func.__name__

        # 获取参数
        first_arg = args[0] if args else None
        first_kwarg = list(kwargs.values())[0] if kwargs else None

        # 根据函数名和参数生成业务描述
        if func_name == 'read':
            path = self._extract_path(first_arg, first_kwarg)
            return f"读取了 {path}"

        elif func_name in ['write', 'edit']:
            path = self._extract_path(first_arg, first_kwarg)
            return f"修改了 {path}"

        elif func_name == 'exec':
            command = self._extract_command(first_arg, first_kwarg)
            return self._describe_exec(command)

        elif func_name == 'web_search':
            query = self._extract_query(first_arg, first_kwarg)
            return f"搜索了 {query}"

        elif func_name == 'web_fetch':
            url = self._extract_url(first_arg, first_kwarg)
            return f"获取了网页内容 {url}"

        elif func_name == 'browser':
            action = kwargs.get('action', first_kwarg)
            return f"浏览器操作: {action}"

        else:
            # 默认：使用函数名
            if hasattr(func, '__name__'):
                desc = func.__name__
            else:
                desc = str(func)

            # 如果有参数，添加简短信息
            if first_arg:
                desc += f" - {str(first_arg)[:30]}"

            return desc

    def _extract_path(self, arg1, arg2):
        """提取文件路径"""
        path = arg1 or arg2 or "文件"

        # 如果是字符串，提取文件名
        if isinstance(path, str):
            # 只显示文件名，不显示完整路径
            if '/' in path:
                return path.split('/')[-1]
            return path

        return str(path)[:50]

    def _extract_command(self, arg1, arg2):
        """提取命令"""
        cmd = arg1 or arg2 or ""

        if isinstance(cmd, str):
            # 只显示前50个字符
            return cmd[:50]

        return str(cmd)[:50]

    def _extract_query(self, arg1, arg2):
        """提取搜索查询"""
        query = arg1 or arg2 or ""

        if isinstance(query, str):
            return query[:50]

        return str(query)[:50]

    def _extract_url(self, arg1, arg2):
        """提取URL"""
        url = arg1 or arg2 or ""

        if isinstance(url, str):
            # 只显示域名部分
            if '://' in url:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                return parsed.netloc
            return url[:50]

        return str(url)[:50]

    def _describe_exec(self, command):
        """描述exec命令的业务含义"""
        if not isinstance(command, str):
            return f"执行了命令"

        cmd_lower = command.lower()

        # 天气查询
        if 'wttr.in' in cmd_lower:
            # 提取城市名
            import re
            city_match = re.search(r'wttr\.in/(\w+)', command)
            if city_match:
                city = city_match.group(1)
                return f"查询了 {city} 的天气"
            return "查询了天气"

        # 文件操作
        elif 'git' in cmd_lower:
            return "执行了 Git 操作"
        elif 'npm' in cmd_lower or 'pnpm' in cmd_lower:
            return "执行了包管理操作"
        elif 'python' in cmd_lower or 'python3' in cmd_lower:
            return "执行了 Python 脚本"
        elif 'ls' in cmd_lower or 'll' in cmd_lower:
            return "列出了文件"

        # 默认
        else:
            return "执行了命令"

    def _save_task(self, task):
        """保存任务到JSON文件"""
        tasks = []

        # 读取现有任务
        if self.tasks_file.exists():
            with open(self.tasks_file, 'r') as f:
                try:
                    tasks = json.load(f)
                except:
                    tasks = []

        # 更新或添加任务
        existing_index = next((i for i, t in enumerate(tasks) if t.get('id') == task['id']), None)

        if existing_index is not None:
            tasks[existing_index] = task
        else:
            tasks.append(task)

        # 保存
        with open(self.tasks_file, 'w') as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)

    def record_interaction(self, user_message, bot_response, session_type='telegram'):
        """记录用户互动"""
        interactions_file = self.data_dir / 'interactions.json'

        interactions = []
        if interactions_file.exists():
            with open(interactions_file, 'r') as f:
                try:
                    interactions = json.load(f)
                except:
                    interactions = []

        interaction = {
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message[:200],  # 限制长度
            "bot_response": bot_response[:200],
            "session_type": session_type
        }

        interactions.append(interaction)

        # 保持最近100条
        if len(interactions) > 100:
            interactions = interactions[-100:]

        with open(interactions_file, 'w') as f:
            json.dump(interactions, f, indent=2, ensure_ascii=False)


# 全局实例
_tracker = TaskTracker()

def track_task(func):
    """任务追踪装饰器"""
    return _tracker.track(func)


def record_interaction(user_message, bot_response, session_type='telegram'):
    """记录用户互动"""
    _tracker.record_interaction(user_message, bot_response, session_type)
