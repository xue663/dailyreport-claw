#!/usr/bin/env python3
"""
简化版任务监听器 - 快速创建用户任务
"""
import json
import time
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from data_collector import DataCollector

class SimpleTaskListener:
    def __init__(self, config_path):
        self.collector = DataCollector(config_path)
        self.sessions_dir = Path.home() / '.openclaw' / 'agents' / 'main' / 'sessions'
        self.user_tasks_file = Path(__file__).parent.parent / 'data' / 'user_tasks.json'
        self.processed_ids = set()
        self.running = True

    def load_user_tasks(self):
        """加载现有用户任务"""
        if self.user_tasks_file.exists():
            with open(self.user_tasks_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def save_user_tasks(self, tasks):
        """保存用户任务"""
        with open(self.user_tasks_file, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)

    def extract_text_from_content(self, content):
        """从content中提取纯文本"""
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'text':
                    text = item.get('text', '')
                    if text and not text.startswith('[['):
                        text_parts.append(text)
            return ' '.join(text_parts)

        return ''

    def summarize_task(self, user_message):
        """简单规则总结任务"""
        # 去除常见前缀
        prefixes = ['帮我', '请', '麻烦', '能否', '可以', '帮我查下', '帮我查']
        desc = user_message.strip()

        for prefix in prefixes:
            if desc.startswith(prefix):
                desc = desc[len(prefix):].strip()
                break

        # 去除标点
        desc = desc.lstrip('，,。.!！')

        # 限制长度
        if len(desc) > 40:
            desc = desc[:37] + '...'

        return desc if desc else user_message[:30]

    def check_new_messages(self):
        """检查新的用户消息"""
        try:
            # 读取所有会话文件
            session_files = list(self.sessions_dir.glob('*.jsonl'))

            for session_file in session_files:
                if session_file.name.endswith('.lock'):
                    continue

                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue

                            try:
                                data = json.loads(line)

                                # 只处理消息类型
                                if data.get('type') != 'message':
                                    continue

                                msg = data.get('message', {})
                                role = msg.get('role')

                                # 处理用户消息
                                if role == 'user':
                                    msg_id = data.get('id')

                                    # 跳过已处理的
                                    if msg_id in self.processed_ids:
                                        continue

                                    # 提取消息内容
                                    content = msg.get('content', '')
                                    user_message = self.extract_text_from_content(content)

                                    # 过滤掉系统消息
                                    if not user_message or user_message.startswith('System:') or len(user_message) < 5:
                                        self.processed_ids.add(msg_id)
                                        continue

                                    # 创建任务
                                    timestamp = data.get('timestamp', datetime.now().isoformat())
                                    task_desc = self.summarize_task(user_message)

                                    task = {
                                        'id': f'user_task_{msg_id}',
                                        'description': task_desc,
                                        'user_message': user_message,
                                        'status': 'running',
                                        'created_at': timestamp,
                                        'updated_at': timestamp,
                                        'task_type': 'user_task'
                                    }

                                    # 保存任务
                                    user_tasks = self.load_user_tasks()

                                    # 检查是否已存在
                                    existing_ids = {t.get('id') for t in user_tasks}
                                    if task['id'] not in existing_ids:
                                        user_tasks.insert(0, task)

                                        # 保持100条
                                        if len(user_tasks) > 100:
                                            user_tasks = user_tasks[:100]

                                        self.save_user_tasks(user_tasks)
                                        print(f"✅ 创建任务: {task_desc}")

                                    self.processed_ids.add(msg_id)

                            except json.JSONDecodeError:
                                continue

                except Exception as e:
                    print(f"❌ 读取文件失败 {session_file}: {e}")
                    continue

        except Exception as e:
            print(f"❌ 检查消息失败: {e}")

    def run(self):
        """运行监听器"""
        print("🎯 简化版任务监听器启动...")

        # 加载已处理的ID
        self.check_new_messages()

        print(f"✅ 已处理 {len(self.processed_ids)} 条历史消息")

        # 监听循环
        while self.running:
            try:
                self.check_new_messages()
                time.sleep(5)  # 每5秒检查一次

            except KeyboardInterrupt:
                print("\n🛑 监听器已停止")
                break
            except Exception as e:
                print(f"❌ 监听错误: {e}")
                time.sleep(5)

if __name__ == '__main__':
    config_path = Path(__file__).parent.parent / 'config.json'
    listener = SimpleTaskListener(str(config_path))
    listener.run()
