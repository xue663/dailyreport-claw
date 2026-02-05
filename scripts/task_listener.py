#!/usr/bin/env python3
"""
任务监听器 - 实时监听会话文件，创建和更新用户任务
"""
import json
import time
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from data_collector import DataCollector

class TaskListener:
    def __init__(self, config_path):
        self.collector = DataCollector(config_path)
        self.sessions_dir = Path.home() / '.openclaw' / 'agents' / 'main' / 'sessions'
        self.processed_messages = set()
        self.running = True

    def get_session_files(self):
        """获取所有会话文件"""
        return list(self.sessions_dir.glob('*.jsonl'))

    def get_last_position(self, file_path):
        """获取文件上次读取的位置"""
        pos_file = Path('/tmp/task_listener_positions.json')
        if pos_file.exists():
            with open(pos_file, 'r') as f:
                positions = json.load(f)
            return positions.get(str(file_path), 0)
        return 0

    def save_last_position(self, file_path, position):
        """保存文件读取位置"""
        pos_file = Path('/tmp/task_listener_positions.json')
        if pos_file.exists():
            with open(pos_file, 'r') as f:
                positions = json.load(f)
        else:
            positions = {}

        positions[str(file_path)] = position
        with open(pos_file, 'w') as f:
            json.dump(positions, f)

    def extract_task_with_llm(self, user_message):
        """使用 LLM 总结任务描述"""
        try:
            # 构造提示词
            prompt = f"""请将以下用户消息总结为一个简洁的任务描述（30字以内）：

用户消息：{user_message}

要求：
1. 提取核心任务
2. 去除客套话（帮我、请等）
3. 简洁明了
4. 只要任务描述，不要其他内容

任务描述："""

            # 调用 OpenClaw API
            result = subprocess.run(
                ['openclaw', 'message', '--channel', 'telegram', '--to', 'main', '--message', prompt],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                task_desc = result.stdout.strip()
                # 清理可能的输出
                if len(task_desc) > 50:
                    task_desc = task_desc[:47] + '...'
                return task_desc if task_desc else user_message[:30]
            else:
                return user_message[:30]

        except Exception as e:
            print(f"LLM总结失败: {e}")
            return user_message[:30]

    def determine_task_status(self, user_msg, assistant_msgs):
        """判断任务状态"""
        # 检查是否有失败的工具调用
        for msg in assistant_msgs:
            if msg.get('role') == 'toolResult':
                details = msg.get('details', {})
                if details.get('status') == 'failed':
                    return 'failed'

        # 检查是否有成功的回复
        for msg in assistant_msgs:
            if msg.get('role') == 'assistant':
                content = msg.get('content', [])
                # 有文本回复说明有结果
                if any(isinstance(c, dict) and c.get('type') == 'text' for c in content):
                    return 'completed'

        # 默认为执行中
        return 'running'

    def create_user_task(self, user_message, message_id, timestamp):
        """创建用户任务记录"""
        try:
            # 使用 LLM 总结任务
            task_desc = self.extract_task_with_llm(user_message)

            task = {
                "id": f"user_task_{message_id}",
                "description": task_desc,
                "user_message": user_message,
                "status": "running",
                "created_at": timestamp,
                "updated_at": timestamp,
                "task_type": "user_task"
            }

            # 保存任务
            self.collector._save_task_record(task)

            print(f"✅ 创建任务: {task_desc}")
            return task

        except Exception as e:
            print(f"❌ 创建任务失败: {e}")
            return None

    def update_task_status(self, message_id, status, result_summary=None):
        """更新任务状态"""
        try:
            tasks_file = self.collector.data_dir / 'tasks.json'

            if not tasks_file.exists():
                return

            with open(tasks_file, 'r', encoding='utf-8') as f:
                tasks = json.load(f)

            # 查找并更新任务
            for task in tasks:
                if task.get('id') == f"user_task_{message_id}":
                    task['status'] = status
                    task['updated_at'] = datetime.now().isoformat()
                    if result_summary:
                        task['result_summary'] = result_summary
                    break

            # 保存
            with open(tasks_file, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, indent=2, ensure_ascii=False)

            print(f"✅ 更新任务状态: {message_id} -> {status}")

        except Exception as e:
            print(f"❌ 更新任务状态失败: {e}")

    def monitor_session_file(self, session_file):
        """监听单个会话文件"""
        last_position = self.get_last_position(session_file)

        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                # 跳到上次读取的位置
                f.seek(last_position)

                current_user_msg = None
                assistant_msgs = []

                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)

                        if data.get('type') != 'message':
                            continue

                        msg = data.get('message', {})
                        role = msg.get('role')
                        msg_id = data.get('id', '')

                        if role == 'user':
                            # 保存上一个任务的状态
                            if current_user_msg:
                                status = self.determine_task_status({}, assistant_msgs)
                                self.update_task_status(current_user_msg['id'], status)

                            # 创建新任务
                            content = self._extract_text_from_content(msg.get('content', []))
                            if content and msg_id not in self.processed_messages:
                                self.create_user_task(content, msg_id, data.get('timestamp', ''))
                                self.processed_messages.add(msg_id)

                            current_user_msg = {'id': msg_id, 'content': content}
                            assistant_msgs = []

                        elif role == 'assistant':
                            if current_user_msg:
                                assistant_msgs.append(msg)

                        elif role == 'toolResult':
                            if current_user_msg:
                                assistant_msgs.append(msg)

                    except json.JSONDecodeError:
                        continue

                # 更新文件读取位置
                current_position = f.tell()
                self.save_last_position(session_file, current_position)

        except Exception as e:
            print(f"❌ 监听文件失败 {session_file}: {e}")

    def _extract_text_from_content(self, content):
        """从content中提取文本"""
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'text':
                    text = item.get('text', '')
                    if text and not text.startswith('[['):
                        return text
        return ''

    def run(self):
        """运行监听器"""
        print("🎯 任务监听器启动...")

        # 加载已处理的消息ID
        for session_file in self.get_session_files():
            try:
                with open(session_file, 'r') as f:
                    for line in f:
                        try:
                            data = json.loads(line)
                            if data.get('message', {}).get('role') == 'user':
                                self.processed_messages.add(data.get('id', ''))
                        except:
                            continue
            except:
                continue

        print(f"✅ 已加载 {len(self.processed_messages)} 条历史消息")

        # 监听循环
        while self.running:
            try:
                for session_file in self.get_session_files():
                    self.monitor_session_file(session_file)

                # 每5秒检查一次
                time.sleep(5)

            except KeyboardInterrupt:
                print("\n🛑 监听器已停止")
                break
            except Exception as e:
                print(f"❌ 监听错误: {e}")
                time.sleep(5)

if __name__ == '__main__':
    import sys
    config_path = Path(__file__).parent.parent / 'config.json'
    listener = TaskListener(str(config_path))
    listener.run()
