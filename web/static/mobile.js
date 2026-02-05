// 📱 移动端优化交互逻辑

// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', () => {
    initMobileFeatures();
});

function initMobileFeatures() {
    // 检测是否为移动设备
    const isMobile = window.innerWidth <= 768;

    if (!isMobile) return;

    console.log('📱 移动端模式已激活');

    // 初始化各个功能
    initBottomNavigation();
    initCardToggle();
    initQuickFilter();
    initScrollToTop();
    initPullToRefresh();
    initTouchOptimizations();
}

// ========== 底部导航 ==========
function initBottomNavigation() {
    const navItems = document.querySelectorAll('.nav-item');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();

            // 移除所有active状态
            navItems.forEach(nav => nav.classList.remove('active'));

            // 添加当前active状态
            item.classList.add('active');

            // 获取目标section
            const section = item.dataset.section;

            // 滚动到对应区域
            scrollToSection(section);
        });
    });
}

function scrollToSection(section) {
    let targetElement;

    switch(section) {
        case 'all':
            targetElement = document.querySelector('.dashboard');
            break;
        case 'tasks':
            targetElement = document.querySelector('.main-panel');
            break;
        case 'interactions':
            targetElement = document.querySelector('.interactions-card');
            break;
        case 'reflection':
            targetElement = document.querySelector('.reflection-card');
            break;
        default:
            targetElement = document.querySelector('.dashboard');
    }

    if (targetElement) {
        targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// ========== 卡片折叠功能 ==========
function initCardToggle() {
    const toggles = document.querySelectorAll('.card-toggle');

    toggles.forEach(toggle => {
        toggle.addEventListener('click', (e) => {
            const card = toggle.closest('.card');
            const content = card.querySelector('.card-content');

            if (!content) return;

            // 切换collapsed状态
            card.classList.toggle('collapsed');

            // 添加动画效果
            if (card.classList.contains('collapsed')) {
                content.style.display = 'none';
            } else {
                content.style.display = 'block';
            }
        });
    });
}

// ========== 快速筛选 ==========
function initQuickFilter() {
    // 在任务卡片前添加快速筛选按钮
    const tasksCard = document.querySelector('.tasks-card');
    if (!tasksCard) return;

    const quickFilterHTML = `
        <div class="quick-filter">
            <button class="quick-filter-btn active" data-filter="all">全部</button>
            <button class="quick-filter-btn" data-filter="completed">✅ 完成</button>
            <button class="quick-filter-btn" data-filter="running">🔄 执行中</button>
            <button class="quick-filter-btn" data-filter="scheduled">🕐 计划</button>
            <button class="quick-filter-btn" data-filter="failed">❌ 失败</button>
        </div>
    `;

    const tasksTitle = tasksCard.querySelector('h2');
    tasksTitle.insertAdjacentHTML('afterend', quickFilterHTML);

    // 绑定筛选事件
    const filterBtns = tasksCard.querySelectorAll('.quick-filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // 移除所有active
            filterBtns.forEach(b => b.classList.remove('active'));

            // 添加当前active
            btn.classList.add('active');

            // 执行筛选
            const filter = btn.dataset.filter;
            filterTasks(filter);
        });
    });
}

function filterTasks(filter) {
    const tasks = document.querySelectorAll('.task-item');

    tasks.forEach(task => {
        const status = task.classList.contains(`status-${filter}`) || task.dataset.status === filter;

        if (filter === 'all') {
            task.style.display = '';
        } else if (task.classList.contains(`status-${filter}`)) {
            task.style.display = '';
        } else {
            task.style.display = 'none';
        }
    });
}

// ========== 滚动到顶部按钮 ==========
function initScrollToTop() {
    const scrollTopBtn = document.getElementById('scroll-top');
    if (!scrollTopBtn) return;

    // 监听滚动事件
    let isScrolling;
    window.addEventListener('scroll', () => {
        clearTimeout(isScrolling);

        // 显示/隐藏按钮
        if (window.scrollY > 300) {
            scrollTopBtn.classList.add('show');
        } else {
            scrollTopBtn.classList.remove('show');
        }

        // 防抖
        isScrolling = setTimeout(() => {
            // 滚动停止后的处理
        }, 100);
    }, { passive: true });

    // 点击滚动到顶部
    scrollTopBtn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// ========== 下拉刷新 ==========
function initPullToRefresh() {
    const pullRefresh = document.getElementById('pull-to-refresh');
    if (!pullRefresh) return;

    let startY = 0;
    let currentY = 0;
    let isPulling = false;

    document.addEventListener('touchstart', (e) => {
        if (window.scrollY === 0) {
            startY = e.touches[0].clientY;
            isPulling = true;
        }
    }, { passive: true });

    document.addEventListener('touchmove', (e) => {
        if (!isPulling || window.scrollY > 0) return;

        currentY = e.touches[0].clientY;
        const diffY = currentY - startY;

        if (diffY > 0 && diffY < 150) {
            pullRefresh.style.transform = `translateY(${diffY * 0.5}px)`;

            if (diffY > 80) {
                pullRefresh.querySelector('span').textContent = '↑ 释放刷新';
            } else {
                pullRefresh.querySelector('span').textContent = '↓ 下拉刷新';
            }
        }
    }, { passive: true });

    document.addEventListener('touchend', () => {
        if (!isPulling) return;

        const diffY = currentY - startY;

        if (diffY > 80) {
            // 触发刷新
            performRefresh();
        }

        // 重置
        pullRefresh.style.transform = '';
        pullRefresh.querySelector('span').textContent = '↓ 下拉刷新';
        isPulling = false;
        startY = 0;
        currentY = 0;
    }, { passive: true });
}

function performRefresh() {
    const pullRefresh = document.getElementById('pull-to-refresh');
    const span = pullRefresh?.querySelector('span');

    if (span) {
        span.innerHTML = '<div class="loading-spinner"></div> 刷新中...';
    }

    // 调用原有刷新函数
    if (typeof refreshData === 'function') {
        refreshData().then(() => {
            setTimeout(() => {
                if (span) {
                    span.textContent = '✓ 刷新完成';
                }
                setTimeout(() => {
                    if (pullRefresh) {
                        pullRefresh.style.transform = '';
                    }
                    if (span) {
                        span.textContent = '↓ 下拉刷新';
                    }
                }, 1000);
            }, 500);
        });
    }
}

// ========== 触摸优化 ==========
function initTouchOptimizations() {
    // 增大点击区域
    const buttons = document.querySelectorAll('button, .filter-btn');
    buttons.forEach(btn => {
        const minSize = 44; // iOS推荐最小点击区域
        const rect = btn.getBoundingClientRect();

        if (rect.width < minSize || rect.height < minSize) {
            btn.style.minWidth = `${minSize}px`;
            btn.style.minHeight = `${minSize}px`;
        }
    });

    // 禁用双击缩放
    document.addEventListener('dblclick', (e) => {
        e.preventDefault();
    }, { passive: false });

    // 优化滚动性能
    const scrollElements = document.querySelectorAll('.tasks-timeline, .interactions-list, .reflection-content');
    scrollElements.forEach(el => {
        el.style.webkitOverflowScrolling = 'touch';
        el.style.overflowScrolling = 'touch';
    });
}

// ========== 横屏检测 ==========
function handleOrientationChange() {
    const isLandscape = window.innerWidth > window.innerHeight;

    if (isLandscape) {
        document.body.classList.add('landscape');
    } else {
        document.body.classList.remove('landscape');
    }
}

window.addEventListener('resize', handleOrientationChange);
window.addEventListener('orientationchange', handleOrientationChange);

// 导出给其他模块使用
window.mobileUtils = {
    scrollToSection,
    filterTasks,
    performRefresh
};
