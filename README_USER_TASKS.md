# 用户任务追踪系统 - 使用说明

## 🎯 功能说明

### 核心功能
1. **实时任务追踪**：当你给阿呆发送任务时，立即在控制台看到任务列表
2. **智能任务总结**：使用LLM自动总结任务描述（30字以内）
3. **状态实时更新**：执行中 → 完成/失败
4. **按时间排序**：最新的任务在最上面

### 任务状态
- 🔄 **执行中**：任务刚创建，正在处理
- ✅ **完成**：任务已成功完成
- ❌ **失败**：任务执行失败

## 📂 项目结构

```
dailyreport-claw/
├── scripts/
│   ├── task_listener.py      # 任务监听器（后台运行）
│   ├── start_listener.sh     # 启动监听器
│   └── stop_listener.sh      # 停止监听器
├── src/
│   └── data_collector.py     # 数据收集器（已更新）
├── web/
│   ├── index.html            # 前端页面
│   └── static/
│       ├── app.js            # 前端逻辑（已更新）
│       └── style.css         # 样式
├── server.py                 # Web服务器（已更新）
└── README_USER_TASKS.md      # 本文档
```

## 🚀 快速开始

### 1. 启动任务监听器

```bash
cd /home/jun663/.openclaw/workspace/dailyreport-claw
./scripts/start_listener.sh
```

### 2. 确认监听器运行

```bash
ps aux | grep task_listener
```

应该看到类似输出：
```
jun663  xxxxx  python3 scripts/task_listener.py
```

### 3. 访问控制台

打开浏览器访问：http://10.10.1.9:8080

## 📝 使用示例

### 示例1：研究任务

**你发送：**
```
帮我了解一下旺财狗项目，通过其官网和网络信息，为后面我让你写插件做准备。
```

**控制台显示（1秒内）：**
```
🔄 [刚刚] 了解旺财狗项目，为写插件做准备
```

**完成后：**
```
✅ [2分钟前] 了解旺财狗项目，为写插件做准备
```

### 示例2：文件操作

**你发送：**
```
帮我创建一个Python脚本，用来监控文件变化。
```

**控制台显示：**
```
🔄 [刚刚] 创建文件监控脚本
```

## 🔧 技术细节

### 任务记录结构

```json
{
  "id": "user_task_xxx",
  "description": "了解旺财狗项目，为写插件做准备",
  "user_message": "帮我了解一下旺财狗项目...",
  "status": "running",
  "created_at": "2026-02-05T09:10:00",
  "updated_at": "2026-02-05T09:12:30",
  "result_summary": "已了解项目基本信息...",
  "task_type": "user_task"
}
```

### LLM提示词

监听器会自动使用以下提示词总结任务：

```
请将以下用户消息总结为一个简洁的任务描述（30字以内）：

用户消息：[用户的消息]

要求：
1. 提取核心任务
2. 去除客套话（帮我、请等）
3. 简洁明了
4. 只要任务描述，不要其他内容

任务描述：
```

## ⚙️ 管理命令

### 启动监听器
```bash
./scripts/start_listener.sh
```

### 停止监听器
```bash
./scripts/stop_listener.sh
```

### 查看监听器日志
```bash
tail -f logs/task_listener.log
```

### 重启Web服务器
```bash
pkill -f "python3.*server.py"
cd /home/jun663/.openclaw/workspace/dailyreport-claw
python3 server.py > server.log 2>&1 &
```

## 🐛 故障排查

### 问题1：控制台没有显示任务

**检查：**
1. 监听器是否运行？
   ```bash
   ps aux | grep task_listener
   ```

2. 任务文件是否有数据？
   ```bash
   cat data/tasks.json | grep user_task
   ```

**解决：**
```bash
# 重启监听器
./scripts/stop_listener.sh
./scripts/start_listener.sh
```

### 问题2：任务状态一直是"执行中"

**原因：**任务状态判断需要监听器持续追踪

**解决：**
- 等待几秒钟，状态会自动更新
- 如果长时间不变，检查监听器日志

### 问题3：任务描述不准确

**原因：**LLM总结可能不完美

**解决：**
- 监听器会自动重试
- 如果失败，会使用原始消息的前30字

## 📊 与旧系统的区别

### 旧系统（工具调用记录）
- ❌ 显示：`exec - exec`、`read - read`
- ❌ 不直观，难以理解
- ❌ 不是用户真正关心的

### 新系统（用户任务）
- ✅ 显示：`了解旺财狗项目`、`创建文件监控脚本`
- ✅ 直观清晰
- ✅ 符合用户需求

## 🎉 下一步

### 已实现
- ✅ 用户任务提取
- ✅ LLM智能总结
- ✅ 实时监听和创建
- ✅ 状态追踪
- ✅ 前端显示

### 可选优化
- ⏳ 任务优先级
- ⏳ 任务分组/标签
- ⏳ 任务搜索
- ⏳ 任务详情弹窗
- ⏳ 手动编辑任务

---

**有任何问题随时告诉我！** 🤖
