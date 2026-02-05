// 阿呆控制台 - 实时数据刷新

let currentFilter = 'today';
let autoRefresh = null;

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 初始加载数据
    refreshData();

    // 设置自动刷新（30秒）
    autoRefresh = setInterval(refreshData, 30000);

    // 绑定筛选按钮
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            // 移除其他按钮的active状态
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            // 激活当前按钮
            e.target.classList.add('active');
            // 更新筛选条件
            currentFilter = e.target.dataset.filter;
            refreshData();
        });
    });

    // 更新当前时间
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);
});

// 刷新数据
async function refreshData() {
    try {
        console.log('🔄 开始刷新数据，筛选条件:', currentFilter);
        const url = `/api/data/${currentFilter}`;
        console.log('📡 请求URL:', url);

        const response = await fetch(url);
        console.log('📡 响应状态:', response.status);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        console.log('✅ 数据接收成功:', {
            taskCount: data.tasks?.length || 0,
            completed: data.stats?.completed || 0,
            failed: data.stats?.failed || 0
        });

        updateSystemStatus(data.system);
        updateStats(data.stats);
        updateTasks(data.tasks);
        updateInteractions(data.interactions);
        updateReflection(data.reflection);

        console.log('✅ 页面更新完成');
    } catch (error) {
        console.error('❌ 刷新数据失败:', error);
        console.error('错误堆栈:', error.stack);
    }
}

// 更新当前时间
function updateCurrentTime() {
    const now = new Date();
    const timeStr = now.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });
    document.getElementById('current-time').textContent = timeStr;
}

// 更新系统状态
function updateSystemStatus(system) {
    // 安全地更新元素（添加null检查）
    const setText = (id, text) => {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    };

    const setClass = (id, className) => {
        const el = document.getElementById(id);
        if (el) el.className = className;
    };

    // OpenClaw版本
    setText('oc-version', system.openclaw_version || '--');
    const ocStatus = document.getElementById('oc-status');
    if (ocStatus) {
        ocStatus.className = 'status-indicator ' + (system.openclaw_version ? 'online' : 'offline');
    }

    // Gateway状态
    const gwStatus = system.gateway_status;
    setText('gw-status', gwStatus === 'running' ? '运行中' : (gwStatus === 'stopped' ? '已停止' : '未知'));
    const gwIndicator = document.getElementById('gw-indicator');
    if (gwIndicator) {
        gwIndicator.className = 'status-indicator ' + (gwStatus === 'running' ? 'online' : 'offline');
    }

    // Telegram状态
    const tgConnected = system.telegram_connected;
    setText('tg-status', tgConnected ? '已连接' : '未连接');
    const tgIndicator = document.getElementById('tg-indicator');
    if (tgIndicator) {
        tgIndicator.className = 'status-indicator ' + (tgConnected ? 'online' : 'offline');
    }

    // 模型信息
    setText('model-info', system.model || '--');

    // CPU
    const cpu = system.cpu_percent || 0;
    const cpuBar = document.getElementById('cpu-bar');
    const cpuValue = document.getElementById('cpu-value');
    if (cpuBar) cpuBar.style.width = cpu + '%';
    if (cpuValue) cpuValue.textContent = cpu + '%';

    if (cpuBar) {
        if (cpu > 80) {
            cpuBar.style.background = 'var(--neon-red)';
        } else if (cpu > 50) {
            cpuBar.style.background = 'var(--neon-yellow)';
        } else {
            cpuBar.style.background = 'linear-gradient(90deg, var(--neon-blue), var(--neon-purple))';
        }
    }

    // 内存
    const mem = system.memory_percent || 0;
    const memBar = document.getElementById('mem-bar');
    const memValue = document.getElementById('mem-value');
    if (memBar) memBar.style.width = mem + '%';
    if (memValue) memValue.textContent = mem + '%';

    if (memBar) {
        if (mem > 80) {
            memBar.style.background = 'var(--neon-red)';
        } else if (mem > 50) {
            memBar.style.background = 'var(--neon-yellow)';
        } else {
            memBar.style.background = 'linear-gradient(90deg, var(--neon-blue), var(--neon-purple))';
        }
    }

    // 运行时间
    setText('uptime', system.uptime || '--');

    // TOKENS总量
    const tokens = system.tokens_total || 0;
    const tokensText = tokens >= 1000000
        ? (tokens / 1000000).toFixed(1) + 'M'
        : (tokens / 1000).toFixed(0) + 'K';
    setText('tokens-total', tokensText);
}

// 更新统计数据
function updateStats(stats) {
    const setText = (id, text) => {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    };

    setText('stat-completed', stats.completed || 0);
    setText('stat-failed', stats.failed || 0);
    setText('stat-running', stats.running || 0);
    setText('stat-interactions', stats.interactions || 0);
    setText('stat-files', stats.files_created || 0);
    setText('stat-avg-time', (stats.avg_response_time || 0) + 's');
}

// 更新任务列表
function updateTasks(tasks) {
    console.log('📋 updateTasks 被调用，任务数:', tasks?.length || 0);

    const container = document.getElementById('tasks-list');

    if (!container) {
        console.error('❌ 找不到 tasks-list 容器元素');
        return;
    }

    if (!tasks || tasks.length === 0) {
        console.log('⚠️  任务列表为空');
        container.innerHTML = '<div style="text-align: center; color: var(--text-secondary); padding: 20px;">暂无任务记录</div>';
        return;
    }

    console.log('✅ 开始渲染', tasks.length, '个任务');
    console.log('任务类型:', tasks.map(t => t.task_type));

    // 后端已经按时间倒序排列，直接使用
    container.innerHTML = tasks.map(task => {
        const statusIcon = {
            'completed': '✅',
            'failed': '❌',
            'running': '🔄',
            'scheduled': '🕐'
        }[task.status] || '⏸️';

        const statusClass = {
            'completed': 'status-completed',
            'failed': 'status-failed',
            'running': 'status-running',
            'scheduled': 'status-scheduled'
        }[task.status] || '';

        // 兼容新旧字段名
        const time = formatTime(task.created_at || task.start_time || task.timestamp);
        const isUserTask = task.task_type === 'user_task';
        const isSystemTask = task.task_type === 'system_task';

        // 任务类型标签
        let taskTypeLabel = '';
        if (isUserTask) {
            taskTypeLabel = '<span class="task-type">用户</span>';
        } else if (isSystemTask) {
            taskTypeLabel = '<span class="task-type">系统</span>';
        }

        // 用户任务显示描述，工具任务显示描述
        const description = escapeHtml(task.description || '无描述');

        return `
            <div class="task-item ${statusClass}" data-status="${task.status}">
                <div style="display: flex; justify-content: space-between; align-items: start; gap: 8px;">
                    <div class="task-time">${time}</div>
                    <div class="task-status">${statusIcon}</div>
                </div>
                <div class="task-description">${description}</div>
                ${taskTypeLabel}
            </div>
        `;
    }).join('');

    console.log('✅ 任务渲染完成');
}

// 更新互动列表
function updateInteractions(interactions) {
    const container = document.getElementById('interactions-list');

    if (!interactions || interactions.length === 0) {
        container.innerHTML = '<div style="text-align: center; color: var(--text-secondary); padding: 20px;">暂无互动记录</div>';
        return;
    }

    container.innerHTML = interactions.slice(0, 10).map(interaction => {
        const time = formatTime(interaction.timestamp);
        const userMsg = escapeHtml(interaction.user_message || '');
        const botMsg = escapeHtml(interaction.bot_response || '');

        // 截断过长的消息
        const maxLen = 80;
        const truncatedUserMsg = userMsg.length > maxLen ? userMsg.substring(0, maxLen) + '...' : userMsg;
        const truncatedBotMsg = botMsg.length > maxLen ? botMsg.substring(0, maxLen) + '...' : botMsg;

        return `
            <div class="interaction-item">
                <div style="font-size: 11px; color: var(--neon-blue); margin-bottom: 6px; font-weight: 600;">${time}</div>
                ${truncatedUserMsg ? `<div style="font-size: 12px; color: var(--text-primary); margin-bottom: 4px;">💬 ${truncatedUserMsg}</div>` : ''}
                ${truncatedBotMsg ? `<div style="font-size: 12px; color: var(--text-secondary);">🤖 ${truncatedBotMsg}</div>` : ''}
            </div>
        `;
    }).join('');
}

// 更新反思内容
function updateReflection(reflection) {
    const container = document.getElementById('reflection-content');

    if (!reflection) {
        container.innerHTML = '<div style="text-align: center; color: var(--text-secondary); padding: 20px;">暂无反思内容</div>';
        return;
    }

    let html = '';

    // 今日收获
    if (reflection.learnings && reflection.learnings.length > 0) {
        html += `
            <div class="reflection-section">
                <h4>📚 今日收获</h4>
                <ul>
                    ${reflection.learnings.map(item => `<li>${escapeHtml(item)}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    // 明日计划
    if (reflection.tomorrow && reflection.tomorrow.length > 0) {
        html += `
            <div class="reflection-section">
                <h4>📅 明日计划</h4>
                <ul>
                    ${reflection.tomorrow.map(item => `<li>${escapeHtml(item)}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    // 改进建议
    if (reflection.improvements && reflection.improvements.length > 0) {
        html += `
            <div class="reflection-section">
                <h4>💡 改进建议</h4>
                <ul>
                    ${reflection.improvements.map(item => `<li>${escapeHtml(item)}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    container.innerHTML = html || '<div style="text-align: center; color: var(--text-secondary); padding: 20px;">暂无反思内容</div>';
}

// 格式化时间
function formatTime(isoString) {
    if (!isoString) return '--';

    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return '刚刚';
    if (diffMins < 60) return diffMins + '分钟前';
    if (diffMins < 1440) return Math.floor(diffMins / 60) + '小时前';

    return date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// HTML转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
