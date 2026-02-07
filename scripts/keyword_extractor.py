#!/usr/bin/env python3
"""
关键词提取器 - 从互动消息中提取核心关键词
完全不显示对话内容，100%安全
"""
import re
from collections import Counter

class KeywordExtractor:
    """关键词提取器"""

    # 敏感信息模式
    SENSITIVE_PATTERNS = [
        r'密码|pass|password|passwd',
        r'token|key|secret|api[_-]?key',
        r'\d{11}',  # 手机号
        r'账号|account|user[_-]?id',
        r'Bearer\s+\S+',
        r'session[_-]?id',
        r'auth',
        r'cookie',
    ]

    # 技术关键词（保留）
    TECH_KEYWORDS = {
        '任务', '追踪', '优化', '修复', 'bug',
        '系统', '性能', '缓存', '浏览器',
        '文档', '更新', '同步', 'github',
        '测试', '部署', '启动', '配置',
        'api', '数据库', '查询', '日志',
        '错误', '失败', '超时', '重试',
        '前端', '后端', '服务', '端口',
        '代码', '提交', '推送', '分支',
        '反思', '计划', '建议', '收获',
        '定时', '调度', 'cron', '任务',
        '监控', '状态', '健康', '检查',
    }

    @classmethod
    def sanitize(cls, text):
        """脱敏处理 - 用占位符替换敏感信息"""
        if not text:
            return ''

        # 用占位符替换敏感信息（保持句子结构）
        text = re.sub(r'密码|pass|password|passwd', '***', text, flags=re.IGNORECASE)
        text = re.sub(r'token|key|secret|api[_-]?key', '***', text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d{11}\b', '***', text)  # 手机号
        text = re.sub(r'账号|account|user[_-]?id', '***', text, flags=re.IGNORECASE)
        text = re.sub(r'Bearer\s+\S+', '***', text, flags=re.IGNORECASE)
        text = re.sub(r'session[_-]?id', '***', text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d{8,}\b', '***', text)  # 长数字
        text = re.sub(r'\b[a-f0-9]{32,}\b', '***', text, flags=re.IGNORECASE)  # token
        text = re.sub(r'https?://\S+', '***', text)  # URL
        text = re.sub(r'/[\w\-./]+', '***', text)  # 文件路径

        return text.strip()

    @classmethod
    def extract_from_message(cls, message, max_keywords=5):
        """从消息中提取关键词"""
        if not message:
            return []

        # 先脱敏（用占位符替换）
        safe_message = cls.sanitize(message)

        # 优先匹配技术关键词
        found_tech_keywords = []
        for tech_kw in cls.TECH_KEYWORDS:
            if tech_kw.lower() in safe_message.lower():
                found_tech_keywords.append(tech_kw)

        if found_tech_keywords:
            return found_tech_keywords[:max_keywords]

        # 如果没有技术关键词，智能提取短语
        # 按标点符号和空格分割
        phrases = re.split(r'[，。！？、,!?\s]+', safe_message)

        # 过滤有效短语
        valid_phrases = []
        for phrase in phrases:
            phrase = phrase.strip()
            # 长度在2-15个字符之间
            if 2 <= len(phrase) <= 15:
                # 不全是占位符
                if '***' not in phrase or phrase.replace('***', '').strip():
                    # 不包含太多占位符
                    if phrase.count('***') < 2:
                        valid_phrases.append(phrase)

        # 返回前几个短语
        keywords = valid_phrases[:max_keywords] if valid_phrases else ['系统操作']

        return keywords

    @classmethod
    def extract_from_interaction(cls, user_message, bot_response, max_keywords=3):
        """从一对互动中提取关键词"""
        keywords = []

        # 从用户消息提取
        if user_message:
            user_keywords = cls.extract_from_message(user_message, max_keywords=2)
            keywords.extend(user_keywords)

        # 从AI回复提取
        if bot_response and len(keywords) < max_keywords:
            remaining = max_keywords - len(keywords)
            bot_keywords = cls.extract_from_message(bot_response, remaining)
            keywords.extend(bot_keywords)

        # 去重并限制数量
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)
                if len(unique_keywords) >= max_keywords:
                    break

        return unique_keywords


if __name__ == '__main__':
    # 测试
    extractor = KeywordExtractor()

    # 测试1：普通消息
    test_msg1 = "优化任务追踪系统的显示功能，修复浏览器缓存问题"
    keywords1 = extractor.extract_from_message(test_msg1)
    print(f"测试1: {keywords1}")

    # 测试2：包含敏感信息
    test_msg2 = "我的密码是12345678，token是abc123def456，手机号13800138000"
    keywords2 = extractor.extract_from_message(test_msg2)
    print(f"测试2（敏感信息应被过滤）: {keywords2}")

    # 测试3：互动消息
    user_msg = "检查一下系统状态，看看有没有错误"
    bot_resp = "系统运行正常，没有发现错误日志"
    keywords3 = extractor.extract_from_interaction(user_msg, bot_resp)
    print(f"测试3（互动）: {keywords3}")
