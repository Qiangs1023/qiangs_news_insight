"""
辅助工具模块
"""
from typing import List, Dict
from datetime import datetime, timedelta


def normalize_url(url: str) -> str:
    """
    标准化URL

    Args:
        url: 原始URL

    Returns:
        标准化后的URL
    """
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url


def truncate_text(text: str, max_length: int = 200, suffix: str = '...') -> str:
    """
    截断文本

    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 后缀

    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_date(date: datetime, format_str: str = '%Y-%m-%d %H:%M') -> str:
    """
    格式化日期

    Args:
        date: 日期对象
        format_str: 格式字符串

    Returns:
        格式化后的日期字符串
    """
    if date is None:
        return ''
    if isinstance(date, str):
        try:
            date = datetime.fromisoformat(date)
        except:
            return date
    return date.strftime(format_str)


def get_time_ago(date: datetime) -> str:
    """
    获取相对时间描述

    Args:
        date: 日期对象

    Returns:
        相对时间字符串（如"2 hours ago"）
    """
    if date is None:
        return ''

    if isinstance(date, str):
        try:
            date = datetime.fromisoformat(date)
        except:
            return ''

    now = datetime.now()
    delta = now - date

    if delta < timedelta(minutes=1):
        return 'just now'
    elif delta < timedelta(hours=1):
        minutes = int(delta.total_seconds() / 60)
        return f'{minutes} minute{"s" if minutes > 1 else ""} ago'
    elif delta < timedelta(days=1):
        hours = int(delta.total_seconds() / 3600)
        return f'{hours} hour{"s" if hours > 1 else ""} ago'
    elif delta < timedelta(days=7):
        days = delta.days
        return f'{days} day{"s" if days > 1 else ""} ago'
    else:
        return format_date(date, '%Y-%m-%d')


def group_articles_by_date(articles: List[Dict]) -> Dict[str, List[Dict]]:
    """
    按日期分组文章

    Args:
        articles: 文章列表

    Returns:
        按日期分组的文章字典
    """
    grouped = {}

    for article in articles:
        date_str = format_date(article.get('published_at'), '%Y-%m-%d')

        if date_str not in grouped:
            grouped[date_str] = []

        grouped[date_str].append(article)

    return grouped


def get_unique_sources(articles: List[Dict]) -> List[Dict]:
    """
    获取唯一的订阅源列表

    Args:
        articles: 文章列表

    Returns:
        订阅源列表
    """
    sources = {}

    for article in articles:
        source_id = article.get('source_id')
        source_name = article.get('source_name')
        source_type = article.get('source_type')

        if source_id and source_id not in sources:
            sources[source_id] = {
                'id': source_id,
                'name': source_name,
                'type': source_type,
                'count': 0
            }

        if source_id in sources:
            sources[source_id]['count'] += 1

    return list(sources.values())