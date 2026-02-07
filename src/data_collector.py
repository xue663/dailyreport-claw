#!/usr/bin/env python3
"""
数据收集模块 - 从OpenClaw会话历史收集数据
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加scripts目录到路径，用于导入keyword_extractor
scripts_dir = Path(__file__).parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

class DataCollector:
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        self.data_dir = Path(__file__).parent.parent / 'data'
        self.data_dir.mkdir(exist_ok=True)

        # 导入关键词提取器
        from keyword_extractor import KeywordExtractor
        self.keyword_extractor = KeywordExtractor

    def create_task(self, description, user_message='', status='running', scheduled_time=None):
        """创建新任务

        Args:
            description: 任务描述（AI理解后的总结）
            user_message: 原始用户消息
            status: 初始状态 (running/scheduled)
            scheduled_time: 计划执行时间（ISO格式）

        Returns:
            task_id: 创建的任务ID
        """
        import time

        # 调试输出
        print(f"🔍 [DEBUG] create_task收到参数: status={repr(status)}, scheduled_time={repr(scheduled_time)}")

        task_id = f"task_{int(time.time() * 1000)}"

        task = {
            "id": task_id,
            "description": description,
            "user_message": user_message,
            "status": status,
            "created_at": datetime.now().isoformat(),
            "start_time": None if status == 'scheduled' else datetime.now().isoformat(),
            "end_time": None,
            "duration": None,
            "result": "",
            "task_type": "system_task" if status == 'scheduled' else "user_task"
        }

        print(f"🔍 [DEBUG] task对象创建后: status={task['status']}, start_time={task['start_time']}")

        # 如果是计划任务，添加计划时间
        if status == 'scheduled' and scheduled_time:
            task['scheduled_time'] = scheduled_time

        # 保存到独立的用户任务文件
        self._save_user_task(task)

        status_text = "🕐 计划任务" if status == 'scheduled' else "执行中"
        print(f"✅ 创建任务: {description} (ID: {task_id}, {status_text})")
        return task_id

    def update_task(self, task_id, status, result=''):
        """更新任务状态（带文件锁）

        Args:
            task_id: 任务ID
            status: 新状态 (running/completed/failed)
            result: 结果摘要

        Returns:
            bool: 更新是否成功
        """
        try:
            import fcntl
            user_tasks_file = self.data_dir / 'user_tasks.json'

            if not user_tasks_file.exists():
                return False

            # 读取（带共享锁）
            with open(user_tasks_file, 'r', encoding='utf-8') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    tasks = json.load(f)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            # 查找并更新任务
            for task in tasks:
                if task.get('id') == task_id:
                    task['status'] = status
                    task['result'] = result

                    # 如果是完成或失败，记录结束时间和持续时间
                    if status in ['completed', 'failed']:
                        task['end_time'] = datetime.now().isoformat()
                        if task.get('start_time'):
                            try:
                                start = datetime.fromisoformat(task['start_time'])
                                end = datetime.fromisoformat(task['end_time'])
                                task['duration'] = round((end - start).total_seconds(), 2)
                            except:
                                pass

                    # 保存回文件（带排他锁）
                    with open(user_tasks_file, 'w', encoding='utf-8') as f:
                        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                        try:
                            json.dump(tasks, f, indent=2, ensure_ascii=False)
                        finally:
                            fcntl.flock(f.fileno(), fcntl.LOCK_UN)

                    print(f"✅ 更新任务 {task_id}: {status}")
                    return True

            return False

        except Exception as e:
            print(f"❌ 更新任务失败: {e}")
            return False

    def get_system_status(self):
        """收集系统状态"""
        try:
            # 获取系统资源
            cpu, memory = self._get_system_resources()
            uptime = self._get_uptime()

            # 获取TOKENS使用量
            tokens = self._get_tokens_usage()

            # 获取OpenClaw版本
            version = self._get_openclaw_version()

            return {
                "openclaw_version": version,
                "gateway_status": "running",
                "telegram_connected": True,
                "model": "GLM-4.7",
                "model_provider": "zai",
                "cpu_percent": cpu,
                "memory_percent": memory,
                "uptime": uptime,
                "tokens_total": tokens,
                "last_update": datetime.now().strftime("%H:%M:%S")
            }
        except Exception as e:
            print(f"Error collecting system status: {e}")
            return self._get_default_system_status()

    def _get_default_system_status(self):
        """返回默认系统状态"""
        return {
            "openclaw_version": "unknown",
            "gateway_status": "unknown",
            "telegram_connected": False,
            "model": "unknown",
            "model_provider": "unknown",
            "cpu_percent": 0,
            "memory_percent": 0,
            "uptime": "unknown",
            "tokens_total": 0,
            "last_update": datetime.now().strftime("%H:%M:%S")
        }

    def _get_openclaw_version(self):
        """获取OpenClaw版本"""
        try:
            # 使用 shell=True 执行命令
            result = subprocess.run(
                'openclaw --version',
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                return version
        except subprocess.TimeoutExpired:
            print("Warning: openclaw --version timed out")
        except Exception as e:
            print(f"Error getting OpenClaw version: {e}")

        # 如果 openclaw 命令失败，尝试从 npm 获取
        try:
            result = subprocess.run(
                'npm list -g openclaw',
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'openclaw@' in line:
                        version = line.split('@')[1].strip()
                        return version
        except Exception as e:
            print(f"Error getting version from npm: {e}")

        return "unknown"

    def _get_tokens_usage(self):
        """获取TOKENS使用量"""
        try:
            # 从会话文件中读取
            sessions_file = Path.home() / '.openclaw' / 'agents' / 'main' / 'sessions' / 'sessions.json'

            if not sessions_file.exists():
                return 0

            with open(sessions_file, 'r', encoding='utf-8') as f:
                sessions_data = json.load(f)

            # 遍历所有会话，累加 totalTokens
            total_tokens = 0
            for session_key, session_data in sessions_data.items():
                if isinstance(session_data, dict) and 'totalTokens' in session_data:
                    total_tokens += session_data['totalTokens']

            return total_tokens

        except Exception as e:
            print(f"Error reading tokens usage: {e}")
            return 0

    def _get_system_resources(self):
        """获取CPU和内存使用率"""
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory().percent
            return cpu, memory
        except:
            return 12, 45

    def _get_uptime(self):
        """获取系统运行时间"""
        try:
            uptime_seconds = open('/proc/uptime').read().split()[0]
            uptime_hours = int(float(uptime_seconds) // 3600)
            uptime_minutes = int((float(uptime_seconds) % 3600) // 60)
            return f"{uptime_hours}h {uptime_minutes}m"
        except:
            return "unknown"

    def get_tasks(self, time_filter='today', save_to_file=True, include_user_tasks=True, include_tool_calls=False):
        """从会话历史获取任务列表（带去重和时间统一）

        Args:
            time_filter: 时间筛选器 (today/week/month/all)
            save_to_file: 是否保存新任务到文件 (默认True)
            include_user_tasks: 是否包含用户任务 (默认True)
            include_tool_calls: 是否包含工具调用 (默认False) ← 新增参数
        """
        try:
            # 先检查并清理僵尸任务
            self.check_stale_tasks()

            # 读取用户任务
            user_tasks = self._get_user_tasks(time_filter) if include_user_tasks else []
            
            # 记录已见任务ID（用于去重）
            seen_task_ids = {task.get('id') for task in user_tasks}
            
            # 会话目录
            sessions_dir = Path.home() / '.openclaw' / 'agents' / 'main' / 'sessions'

            if not sessions_dir.exists():
                return self._filter_and_sort_tasks(user_tasks, time_filter)

            tasks = user_tasks[:]  # 复制一份

            # 只有在明确要求时才提取工具调用
            if not include_tool_calls:
                # 直接返回用户任务，不提取工具调用
                print(f"✅ 仅返回用户任务 {len(tasks)} 个（不包含工具调用）")
                return self._filter_and_sort_tasks(tasks, time_filter)

            # 读取所有.jsonl文件（提取工具调用）
            for jsonl_file in sessions_dir.glob('*.jsonl'):
                if jsonl_file.name.endswith('.lock'):
                    continue

                try:
                    with open(jsonl_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            if not line.strip():
                                continue

                            try:
                                msg_data = json.loads(line)

                                # 只处理消息类型
                                if msg_data.get('type') != 'message':
                                    continue

                                message = msg_data.get('message', {})
                                role = message.get('role')
                                task_id = msg_data.get('id', '')

                                # 去重：跳过已存在的任务ID
                                if task_id in seen_task_ids:
                                    continue

                                # 从assistant消息中提取工具调用
                                if role == 'assistant':
                                    tool_calls = self._extract_tool_calls_from_content(message.get('content', []))
                                    timestamp = msg_data.get('timestamp', '')

                                    for tool_call in tool_calls:
                                        task = {
                                            "id": task_id or f"session_{len(tasks)}",
                                            "description": tool_call.get('description', '执行任务'),
                                            "status": "completed",
                                            "created_at": timestamp,  # 统一使用created_at
                                            "start_time": timestamp,
                                            "end_time": timestamp,
                                            "function": tool_call.get('name', 'unknown'),
                                            "duration": 0,
                                            "task_type": "tool_call"
                                        }
                                        tasks.append(task)
                                        seen_task_ids.add(task['id'])

                                # 从toolResult消息中提取状态
                                elif role == 'toolResult':
                                    tool_name = message.get('toolName', 'unknown')
                                    details = message.get('details', {})
                                    timestamp = msg_data.get('timestamp', '')

                                    # 计算持续时间（如果有）
                                    duration = details.get('durationMs', 0) / 1000 if details.get('durationMs') else 0

                                    task = {
                                        "id": task_id or f"session_{len(tasks)}",
                                        "description": f"{tool_name} - {details.get('name', tool_name)}",
                                        "status": "completed" if details.get('status') == 'completed' else "failed",
                                        "created_at": timestamp,  # 统一使用created_at
                                        "start_time": timestamp,
                                        "end_time": timestamp,
                                        "function": tool_name,
                                        "duration": duration,
                                        "task_type": "tool_call"
                                    }
                                    tasks.append(task)
                                    seen_task_ids.add(task['id'])

                            except json.JSONDecodeError:
                                continue

                except Exception as e:
                    print(f"Error reading {jsonl_file}: {e}")
                    continue

            # 不再保存工具任务到文件（避免覆盖用户任务）
            # if save_to_file and tasks:
            #     self._save_tasks_to_file(tasks)

            # 使用统一的过滤、排序和限制方法
            return self._filter_and_sort_tasks(tasks, time_filter)

        except Exception as e:
            print(f"Error fetching tasks from history: {e}")
            return self._filter_and_sort_tasks(user_tasks, time_filter)  # 降级返回用户任务

    def _extract_tool_calls_from_content(self, content):
        """从消息内容中提取工具调用"""
        tool_calls = []

        if not isinstance(content, list):
            return tool_calls

        for item in content:
            if isinstance(item, dict) and item.get('type') == 'toolCall':
                func_name = item.get('name', 'unknown')
                arguments = item.get('arguments', {})

                # 生成描述
                description = f"调用 {func_name}"
                if isinstance(arguments, dict):
                    # 提取关键参数
                    if 'command' in arguments:
                        description = f"执行: {arguments['command'][:50]}"
                    elif 'path' in arguments:
                        description = f"读取: {arguments['path']}"
                    elif 'url' in arguments:
                        description = f"访问: {arguments['url']}"
                    elif 'message' in arguments:
                        description = f"发送: {arguments['message'][:30]}"

                tool_calls.append({
                    'name': func_name,
                    'description': description
                })

        return tool_calls

    def _load_cached_tasks(self, time_filter):
        """加载缓存的任务数据"""
        tasks_file = self.data_dir / 'tasks.json'
        if tasks_file.exists():
            with open(tasks_file, 'r') as f:
                all_tasks = json.load(f)
            filtered_tasks = self._filter_by_time(all_tasks, time_filter)
            # 按时间倒序排列（最近的在前）
            filtered_tasks.sort(key=lambda x: x.get('start_time', ''), reverse=True)
            return filtered_tasks[-50:]
        return []

    def get_interactions(self, time_filter='today'):
        """从会话历史获取互动记录"""
        try:
            # 直接读取会话文件
            sessions_dir = Path.home() / '.openclaw' / 'agents' / 'main' / 'sessions'
            session_files = list(sessions_dir.glob('*.jsonl'))

            if not session_files:
                return self._load_cached_interactions(time_filter)

            # 找到最新的会话文件
            latest_file = max(session_files, key=lambda p: p.stat().st_mtime)

            # 读取并解析会话数据
            interactions = self._parse_session_file(latest_file)

            # 时间筛选
            filtered = self._filter_by_time(interactions, time_filter)
            # 按时间倒序排列（最近的在前）
            filtered.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return filtered[-20:]

        except Exception as e:
            print(f"Error fetching interactions from history: {e}")
            return self._load_cached_interactions(time_filter)

    def _parse_session_file(self, session_file):
        """解析会话.jsonl文件"""
        interactions = []
        current_user_msg = None

        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)

                        # 只处理消息类型的记录
                        if data.get('type') != 'message':
                            continue

                        msg = data.get('message', {})
                        role = msg.get('role', '')

                        if role == 'user':
                            current_user_msg = data

                        elif role == 'assistant' and current_user_msg:
                            # 提取用户消息内容
                            user_content = current_user_msg.get('message', {})
                            user_text = self._extract_text_from_content(user_content.get('content', []))

                            # 提取AI回复内容
                            assistant_content = msg.get('content', [])
                            bot_text = self._extract_text_from_content(assistant_content)

                            # 创建互动记录（使用关键词云）
                            if user_text:
                                # 提取关键词，不存储原始消息
                                keywords = self.keyword_extractor.extract_from_interaction(
                                    user_text,
                                    bot_text,
                                    max_keywords=3
                                )

                                interaction = {
                                    "timestamp": current_user_msg.get('timestamp', datetime.now().isoformat()),
                                    "keywords": keywords,  # 只存储关键词
                                    "session_type": "telegram"
                                }
                                interactions.append(interaction)

                                # 创建任务记录
                                self._create_task_from_interaction(current_user_msg, data)

                            current_user_msg = None

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            print(f"Error parsing session file: {e}")

        return interactions

    def _extract_text_from_content(self, content):
        """从content数组中提取纯文本"""
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    item_type = item.get('type', '')
                    if item_type == 'text':
                        text = item.get('text', '')
                        if text and not text.startswith('['):  # 过滤掉 thinking
                            text_parts.append(text)
            return ' '.join(text_parts)

        return ''

    def _load_cached_interactions(self, time_filter):
        """加载缓存的互动数据"""
        interactions_file = self.data_dir / 'interactions.json'
        if interactions_file.exists():
            with open(interactions_file, 'r') as f:
                all_interactions = json.load(f)
            filtered = self._filter_by_time(all_interactions, time_filter)
            # 按时间倒序排列（最近的在前）
            filtered.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return filtered[-20:]
        return []

    def _filter_and_sort_tasks(self, tasks, time_filter):
        """过滤、排序和限制任务数量"""
        # 时间筛选
        filtered_tasks = self._filter_by_time(tasks, time_filter)
        # 按created_at时间倒序排列（最近的在前）
        filtered_tasks.sort(key=lambda x: x.get('created_at', x.get('start_time', '')), reverse=True)
        # 只返回最近50条
        return filtered_tasks[:50]

    def _filter_by_time(self, items, time_filter):
        """根据时间筛选"""
        from datetime import timezone

        now = datetime.now(timezone.utc)  # 使用UTC时间

        if time_filter == 'today':
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_filter == 'week':
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_filter == 'month':
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:  # all
            return items

        filtered = []
        for item in items:
            try:
                # 支持多个时间字段
                timestamp = (item.get('timestamp') or
                            item.get('start_time') or
                            item.get('created_at') or
                            '')

                if not timestamp:
                    # 如果没有时间戳，跳过
                    continue

                # 处理时间戳
                if isinstance(timestamp, (int, float)):
                    # Unix时间戳（毫秒）
                    item_time = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
                else:
                    # ISO格式字符串
                    timestamp_str = timestamp.replace('Z', '+00:00')
                    item_time = datetime.fromisoformat(timestamp_str)

                    # 如果没有时区信息，假设是本地时间
                    if item_time.tzinfo is None:
                        # 不添加时区，直接比较
                        pass

                # 比较时忽略时区差异
                if item_time.replace(tzinfo=None) >= start.replace(tzinfo=None):
                    filtered.append(item)
            except Exception as e:
                # 忽略过滤错误，保留该item
                filtered.append(item)
                continue
        return filtered

    def get_stats(self, time_filter='today'):
        """获取统计数据"""
        tasks = self.get_tasks(time_filter)
        interactions = self.get_interactions(time_filter)

        completed = sum(1 for t in tasks if t.get('status') == 'completed')
        failed = sum(1 for t in tasks if t.get('status') == 'failed')
        running = sum(1 for t in tasks if t.get('status') == 'running')

        # 计算平均响应时间
        response_times = [t.get('duration', 0) for t in tasks if t.get('duration')]
        avg_time = sum(response_times) / len(response_times) if response_times else 0

        # 统计创建的文件
        files_created = len([t for t in tasks if 'file' in t.get('description', '').lower() or 'write' in t.get('function', '').lower()])

        return {
            "completed": completed,
            "failed": failed,
            "running": running,
            "paused": 0,
            "interactions": len(interactions),
            "files_created": files_created,
            "avg_response_time": round(avg_time, 1)
        }

    def get_reflection(self):
        """获取AI反思（从动态生成的文件读取）"""
        reflection_file = self.data_dir / 'reflection.json'

        if reflection_file.exists():
            try:
                with open(reflection_file, 'r', encoding='utf-8') as f:
                    reflection = json.load(f)

                # 检查反思日期，如果不是今天则返回默认
                reflection_date = reflection.get('date', '')
                today = datetime.now().strftime('%Y-%m-%d')

                if reflection_date == today:
                    return reflection
                else:
                    print(f"⚠️  反思文件日期 {reflection_date} 不是今天 {today}")
            except Exception as e:
                print(f"⚠️  读取反思文件失败: {e}")

        # 返回默认反思
        return {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "improvements": ["等待生成今日反思..."],
            "learnings": ["反思将在每天下午5点自动生成"],
            "tomorrow": ["请等待明日计划生成"]
        }

    def _create_task_from_interaction(self, user_msg, assistant_msg):
        """从互动中创建任务记录"""
        try:
            # 提取任务描述
            user_content = user_msg.get('content', '')
            if not user_content or not isinstance(user_content, str):
                return

            task_description = self._extract_task_description(user_content)

            # 计算执行时间
            user_time = user_msg.get('timestamp')
            assistant_time = assistant_msg.get('timestamp')

            if user_time and assistant_time:
                try:
                    start = datetime.fromisoformat(user_time.replace('Z', '+00:00'))
                    end = datetime.fromisoformat(assistant_time.replace('Z', '+00:00'))
                    duration = round((end - start).total_seconds(), 2)
                except:
                    duration = 0
            else:
                duration = 0

            # 检查是否是简单的确认消息（不需要创建任务）
            bot_response = assistant_msg.get('content', '')
            if self._is_simple_acknowledgment(bot_response):
                return

            # 创建任务记录
            task = {
                "id": f"task_{int(datetime.now().timestamp() * 1000)}",
                "description": task_description,
                "status": "completed",
                "start_time": user_time or datetime.now().isoformat(),
                "end_time": assistant_time or datetime.now().isoformat(),
                "duration": duration,
                "function": "user_task",
                "module": "interaction",
                "result": "success"
            }

            # 保存任务
            self._save_task_record(task)

        except Exception as e:
            print(f"Error creating task from interaction: {e}")

    def _extract_task_description(self, user_message):
        """智能提取任务描述"""
        # 去除常见前缀
        prefixes_to_remove = [
            '帮我', '请', '麻烦', '能否', '可以',
            'help me', 'please', 'can you', 'could you'
        ]

        desc = user_message.strip()

        # 去除前缀
        for prefix in prefixes_to_remove:
            if desc.lower().startswith(prefix.lower()):
                desc = desc[len(prefix):].strip()
                break

        # 去除标点符号
        desc = desc.lstrip('，,。.!！')

        # 限制长度
        if len(desc) > 50:
            desc = desc[:47] + '...'

        return desc if desc else '执行任务'

    def _is_simple_acknowledgment(self, bot_response):
        """判断是否是简单的确认消息"""
        if not bot_response or not isinstance(bot_response, str):
            return False

        # 简单确认的模式
        simple_patterns = [
            '好的', '收到', '明白', 'ok', 'ok的', '知道了',
            'sure', 'got it', 'understood'
        ]

        response_lower = bot_response.lower().strip()

        # 如果回复非常短（<10字）且是确认语句
        if len(bot_response) < 10:
            for pattern in simple_patterns:
                if pattern in response_lower:
                    return True

        return False

    def _save_task_record(self, task):
        """保存任务记录到文件"""
        tasks_file = self.data_dir / 'tasks.json'

        try:
            # 读取现有任务
            if tasks_file.exists():
                with open(tasks_file, 'r', encoding='utf-8') as f:
                    tasks = json.load(f)
            else:
                tasks = []

            # 检查是否已存在相同ID的任务
            existing_index = next(
                (i for i, t in enumerate(tasks) if t.get('id') == task['id']),
                None
            )

            if existing_index is not None:
                tasks[existing_index] = task
            else:
                tasks.append(task)

            # 保持最近100条记录
            if len(tasks) > 100:
                tasks = tasks[-100:]

            # 保存
            with open(tasks_file, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Error saving task record: {e}")

    def get_task_timeout(self, description):
        """根据任务描述获取超时时间（秒）"""
        desc_lower = description.lower()

        # 开发/创建类任务：60分钟
        if any(keyword in desc_lower for keyword in
               ['开发', '创建', '实现', '构建', '部署', 'develop', 'create', 'implement', 'build', 'deploy']):
            return 3600

        # 修复/优化类任务：15分钟
        if any(keyword in desc_lower for keyword in
               ['修复', '优化', '调整', '更新', 'fix', 'optimize', 'adjust', 'update']):
            return 900

        # 分析/研究类任务：20分钟
        if any(keyword in desc_lower for keyword in
               ['分析', '研究', '检查', '审查', 'analyze', 'research', 'check', 'review']):
            return 1200

        # 查询/获取类任务：5分钟
        if any(keyword in desc_lower for keyword in
               ['查询', '获取', '读取', 'search', 'get', 'read', 'fetch']):
            return 300

        # 默认30分钟
        return 1800

    def check_stale_tasks(self):
        """检测僵尸任务，根据任务类型使用不同的超时时间"""
        try:
            user_tasks_file = self.data_dir / 'user_tasks.json'

            if not user_tasks_file.exists():
                return

            with open(user_tasks_file, 'r', encoding='utf-8') as f:
                tasks = json.load(f)

            now = datetime.now()
            has_stale = False

            for task in tasks:
                if task.get('status') == 'running':
                    start_time = task.get('start_time')
                    if start_time:
                        try:
                            start = datetime.fromisoformat(start_time)
                            # 获取该任务的超时时间
                            timeout = self.get_task_timeout(task.get('description', ''))

                            if (now - start).total_seconds() > timeout:
                                task['status'] = 'failed'
                                task['end_time'] = now.isoformat()
                                timeout_minutes = timeout // 60
                                task['result'] = f'任务超时（{timeout_minutes}分钟未响应）'
                                task['duration'] = round((now - start).total_seconds(), 2)
                                has_stale = True
                                print(f"⚠️  检测到僵尸任务: {task['id']} - {task.get('description', '')[:30]}")
                        except:
                            pass

            if has_stale:
                with open(user_tasks_file, 'w', encoding='utf-8') as f:
                    json.dump(tasks, f, indent=2, ensure_ascii=False)
                print(f"✅ 已清理僵尸任务")

        except Exception as e:
            print(f"❌ 检查僵尸任务失败: {e}")

    def _save_user_task(self, task):
        """保存用户任务到独立文件（带文件锁）"""
        user_tasks_file = self.data_dir / 'user_tasks.json'

        try:
            import fcntl

            # 读取现有用户任务（带锁）
            if user_tasks_file.exists():
                with open(user_tasks_file, 'r', encoding='utf-8') as f:
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)  # 共享锁（读）
                    try:
                        tasks = json.load(f)
                    finally:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # 释放锁
            else:
                tasks = []

            # 添加新任务到开头
            tasks.insert(0, task)

            # 保持最近100条记录
            if len(tasks) > 100:
                tasks = tasks[:100]

            # 保存（带排他锁）
            with open(user_tasks_file, 'w', encoding='utf-8') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # 排他锁（写）
                try:
                    json.dump(tasks, f, indent=2, ensure_ascii=False)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # 释放锁

        except Exception as e:
            print(f"Error saving user task: {e}")

    def _save_tasks_to_file(self, new_tasks):
        """批量保存任务到文件，避免重复

        Args:
            new_tasks: 从会话历史中提取的新任务列表（仅工具任务）
        """
        tasks_file = self.data_dir / 'tasks.json'

        try:
            # 读取现有任务
            if tasks_file.exists():
                with open(tasks_file, 'r', encoding='utf-8') as f:
                    existing_tasks = json.load(f)
            else:
                existing_tasks = []

            # 分离用户任务和工具任务
            user_tasks = [t for t in existing_tasks if t.get('task_type') == 'user_task']
            tool_tasks = [t for t in existing_tasks if t.get('task_type') != 'user_task']

            # 创建现有工具任务的ID集合
            existing_tool_ids = {t.get('id') for t in tool_tasks}

            # 只添加不存在的工具任务
            added_count = 0
            for task in new_tasks:
                task_id = task.get('id')
                if task_id and task_id not in existing_tool_ids:
                    tool_tasks.append(task)
                    existing_tool_ids.add(task_id)
                    added_count += 1
                elif task_id in existing_tool_ids:
                    # 更新已存在的任务
                    for i, existing_task in enumerate(tool_tasks):
                        if existing_task.get('id') == task_id:
                            tool_tasks[i] = task
                            break

            # 合并用户任务和工具任务（用户任务在前）
            all_tasks = user_tasks + tool_tasks

            # 保持最近100条记录，但优先保留用户任务
            if len(all_tasks) > 100:
                # 优先保留所有用户任务
                user_count = len(user_tasks)
                tool_keep = 100 - user_count
                if tool_keep > 0:
                    all_tasks = user_tasks + tool_tasks[-tool_keep:]
                else:
                    all_tasks = user_tasks[:100]

            # 保存
            with open(tasks_file, 'w', encoding='utf-8') as f:
                json.dump(all_tasks, f, indent=2, ensure_ascii=False)

            if added_count > 0:
                print(f"✅ 已保存 {added_count} 个新工具任务到文件")

        except Exception as e:
            print(f"Error saving tasks to file: {e}")

    def _get_user_tasks(self, time_filter='today'):
        """从独立的用户任务文件中读取"""
        try:
            # 使用独立的用户任务文件
            user_tasks_file = self.data_dir / 'user_tasks.json'

            if not user_tasks_file.exists():
                return []

            with open(user_tasks_file, 'r', encoding='utf-8') as f:
                user_tasks = json.load(f)

            if not user_tasks:
                return []

            # 时间筛选
            filtered_tasks = self._filter_by_time(user_tasks, time_filter)

            # 按时间倒序排列（最近的在前），使用 created_at 字段
            filtered_tasks.sort(key=lambda x: x.get('created_at', ''), reverse=True)

            print(f"✅ 从独立文件读取了 {len(filtered_tasks)} 个用户任务")
            return filtered_tasks

        except Exception as e:
            print(f"Error fetching user tasks: {e}")
            return []
