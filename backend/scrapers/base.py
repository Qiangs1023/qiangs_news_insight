"""
抓取器基类
"""
from abc import ABC, abstractmethod
from typing import List, Dict
from datetime import datetime, timedelta
import time
import random


class Article:
    """文章数据模型"""

    def __init__(self, title: str, url: str, content: str = None,
                 published_at: datetime = None, author: str = None,
                 author_name: str = None, author_avatar: str = None,
                 image_url: str = None, video_thumbnail: str = None,
                 media_type: str = None, media_urls: List[str] = None):
        self.title = title
        self.url = url
        self.content = content or ''
        self.published_at = published_at or datetime.now()
        self.author = author  # 用户名 @username
        self.author_name = author_name  # 显示名称
        self.author_avatar = author_avatar  # 头像URL
        self.image_url = image_url  # 主图片/视频封面
        self.video_thumbnail = video_thumbnail  # 视频缩略图
        self.media_type = media_type  # photo, video, animated_gif
        self.media_urls = media_urls or []  # 所有媒体URL列表

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'title': self.title,
            'url': self.url,
            'content': self.content,
            'published_at': self.published_at,
            'author': self.author,
            'author_name': self.author_name,
            'author_avatar': self.author_avatar,
            'image_url': self.image_url,
            'video_thumbnail': self.video_thumbnail,
            'media_type': self.media_type,
            'media_urls': self.media_urls
        }


class BaseScraper(ABC):
    """抓取器基类"""

    # 反反爬虫设置（子类可覆盖）
    MIN_DELAY = 1.0
    MAX_DELAY = 3.0

    def __init__(self, name: str, url: str, config: Dict = None):
        self.name = name
        self.url = url
        self.config = config or {}
        self.max_retries = 3
        self.retry_delay = 2
        self._last_request_time: float = 0

    def _get_random_delay(self) -> float:
        """获取随机延迟"""
        return random.uniform(self.MIN_DELAY, self.MAX_DELAY)

    def _wait_before_request(self):
        """请求前等待"""
        elapsed = time.time() - self._last_request_time
        delay = self._get_random_delay()
        if elapsed < delay:
            time.sleep(delay - elapsed)
        self._last_request_time = time.time()

    @abstractmethod
    def fetch(self) -> List[Article]:
        """
        抓取内容（抽象方法，子类必须实现）

        Returns:
            文章列表
        """
        pass

    def fetch_with_retry(self) -> List[Article]:
        """
        带重试的抓取

        Returns:
            文章列表，失败返回空列表
        """
        for attempt in range(self.max_retries):
            try:
                return self.fetch()
            except Exception as e:
                print(f"Error fetching {self.name} (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    print(f"Failed to fetch {self.name} after {self.max_retries} attempts")
                    return []

    def filter_recent(self, articles: List[Article], hours: int = 48) -> List[Article]:
        """
        只保留最近N小时内的文章

        Args:
            articles: 文章列表
            hours: 小时数，默认48小时

        Returns:
            只包含最近发布文章的列表
        """
        now = datetime.now()
        cutoff_time = now - timedelta(hours=hours)

        filtered = []
        for article in articles:
            if article.published_at:
                # 处理时区
                pub_date = article.published_at
                if pub_date.tzinfo is not None:
                    pub_date = pub_date.replace(tzinfo=None)
                if pub_date >= cutoff_time:
                    filtered.append(article)

        if len(articles) != len(filtered):
            print(f"Filtered {len(articles)} -> {len(filtered)} articles (last {hours} hours)")
        return filtered

    def scrape(self) -> List[Dict]:
        """
        抓取并返回文章字典列表（只保留最近36小时的内容）

        Returns:
            文章字典列表
        """
        articles = self.fetch_with_retry()
        # 过滤只保留最近36小时的文章
        recent_articles = self.filter_recent(articles, hours=36)
        return [article.to_dict() for article in recent_articles]
