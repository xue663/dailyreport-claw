#!/usr/bin/env python3
"""
系统监控模块 - 持续监控系统状态
"""
import json
import time
from pathlib import Path
from datetime import datetime

class SystemMonitor:
    def __init__(self, config_path):
        self.data_dir = Path(__file__).parent.parent / 'data'
        self.data_dir.mkdir(exist_ok=True)
        self.status_file = self.data_dir / 'system_status.json'

    def update_status(self, status_data):
        """更新系统状态"""
        status_data['last_update'] = datetime.now().isoformat()

        with open(self.status_file, 'w') as f:
            json.dump(status_data, f, indent=2, ensure_ascii=False)

        return status_data

    def get_status(self):
        """获取当前系统状态"""
        if self.status_file.exists():
            with open(self.status_file, 'r') as f:
                return json.load(f)
        return {}
