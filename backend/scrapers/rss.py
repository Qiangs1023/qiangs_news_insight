"""
RSS抓取模块
"""
import feedparser
from typing import List
from datetime import datetime
from .base import BaseScraper, Article


class RSSScraper(BaseScraper):
    """RSS抓取器"""

    def __init__(self, name: str, url: str, config: Dict = None):
        super().__init__(name, url, config)
        self.max_articles = config.get('max_articles', 50) if config else 50

    def fetch(self) -> List[Article]:
        """
        从RSS源抓取文章

        Returns:
            文章列表
        """
        print(f"Fetching RSS from {self.name}: {self.url}")

        # 解析RSS
        feed = feedparser.parse(self.url)

        # 检查是否有错误
        if feed.bozo:
            print(f"Warning: RSS feed may have issues: {feed.bozo_exception}")

        articles = []

        # 遍历条目
        for entry in feed.entries[:self.max_articles]:
            try:
                # 提取标题
                title = entry.get('title', 'No Title')

                # 提取链接
                url = entry.get('link', '')
                if not url:
                    continue

                # 提取内容
                content = self._extract_content(entry)

                # 提取发布时间
                published_at = self._extract_published_at(entry)

                # 提取作者
                author = entry.get('author', '')

                article = Article(
                    title=title,
                    url=url,
                    content=content,
                    published_at=published_at,
                    author=author
                )
                articles.append(article)

            except Exception as e:
                print(f"Error parsing RSS entry: {e}")
                continue

        print(f"Found {len(articles)} articles from {self.name}")
        return articles

    def _extract_content(self, entry) -> str:
        """提取文章内容"""
        # 优先使用content
        if hasattr(entry, 'content') and entry.content:
            content = entry.content[0].value
            return self._strip_html(content)

        # 其次使用summary
        if hasattr(entry, 'summary'):
            return self._strip_html(entry.summary)

        # 最后使用description
        if hasattr(entry, 'description'):
            return self._strip_html(entry.description)

        return ''

    def _extract_published_at(self, entry) -> datetime:
        """提取发布时间"""
        # 尝试多种时间字段
        time_fields = ['published_parsed', 'updated_parsed']

        for field in time_fields:
            if hasattr(entry, field):
                time_struct = getattr(entry, field)
                if time_struct:
                    try:
                        return datetime(*time_struct[:6])
                    except:
                        pass

        # 默认返回当前时间
        return datetime.now()

    def _strip_html(self, html: str) -> str:
        """移除HTML标签"""
        # 简单的HTML标签移除
        import re
        # 移除script和style标签及其内容
        html = re.sub(r'<(script|style).*?>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
        # 移除所有HTML标签
        html = re.sub(r'<[^>]+>', '', html)
        # 清理空白字符
        html = ' '.join(html.split())
        return html[:500]  # 限制长度


def create_rss_scraper(name: str, url: str, config: Dict = None) -> RSSScraper:
    """创建RSS抓取器"""
    return RSSScraper(name, url, config)