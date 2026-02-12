"""
抓取器基类
"""
from abc import ABC, abstractmethod
from typing import List, Dict
from datetime import datetime
import time


class Article:
    """文章数据模型"""

    def __init__(self, title: str, url: str, content: str = None,
                 published_at: datetime = None, author: str = None):
        self.title = title
        self.url = url
        self.content = content or ''
        self.published_at = published_at or datetime.now()
        self.author = author

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'title': self.title,
            'url': self.url,
            'content': self.content,
            'published_at': self.published_at,
            'author': self.author
        }


class BaseScraper(ABC):
    """抓取器基类"""

    def __init__(self, name: str, url: str, config: Dict = None):
        self.name = name
        self.url = url
        self.config = config or {}
        self.max_retries = 3
        self.retry_delay = 2

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

    def scrape(self) -> List[Dict]:
        """
        抓取并返回文章字典列表

        Returns:
            文章字典列表
        """
        articles = self.fetch_with_retry()
        return [article.to_dict() for article in articles]