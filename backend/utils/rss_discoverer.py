"""
RSS自动发现模块
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from urllib.parse import urljoin, urlparse
from backend.config import Config


class RSSDiscoverer:
    """RSS发现器"""

    # 常见的RSS路径
    COMMON_RSS_PATHS = [
        '/feed',
        '/rss',
        '/rss.xml',
        '/atom.xml',
        '/feed.xml',
        '/index.rss',
        '/index.xml',
        '/?feed=rss',
        '/?feed=rss2',
        '/?feed=atom',
        '/blog/feed',
        '/blog/rss',
        '/news/feed',
        '/rss-feed',
        '/posts.rss',
    ]

    def __init__(self):
        self.timeout = Config.REQUEST_TIMEOUT

    def discover(self, url: str) -> Optional[str]:
        """
        从网站URL自动发现RSS feed

        Args:
            url: 网站URL

        Returns:
            RSS feed URL，如果未找到返回None
        """
        print(f"Discovering RSS feed for: {url}")

        # 1. 首先尝试从HTML头部提取RSS链接
        feed_url = self._discover_from_html(url)
        if feed_url:
            print(f"Found RSS feed in HTML head: {feed_url}")
            return feed_url

        # 2. 尝试常见RSS路径
        feed_url = self._discover_from_common_paths(url)
        if feed_url:
            print(f"Found RSS feed in common paths: {feed_url}")
            return feed_url

        print(f"No RSS feed found for: {url}")
        return None

    def _discover_from_html(self, url: str) -> Optional[str]:
        """
        从HTML页面头部提取RSS链接

        Args:
            url: 网站URL

        Returns:
            RSS feed URL，如果未找到返回None
        """
        try:
            # 获取HTML页面
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            # 解析HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # 查找RSS/Atom链接
            link_types = [
                'application/rss+xml',
                'application/atom+xml',
                'application/rdf+xml',
                'text/xml',
                'application/xml'
            ]

            for link_type in link_types:
                links = soup.find_all('link', rel='alternate', type=link_type)
                for link in links:
                    href = link.get('href')
                    if href:
                        # 转换为绝对URL
                        feed_url = urljoin(url, href)
                        # 验证RSS feed是否有效
                        if self._validate_feed(feed_url):
                            return feed_url

            return None

        except Exception as e:
            print(f"Error discovering RSS from HTML: {e}")
            return None

    def _discover_from_common_paths(self, url: str) -> Optional[str]:
        """
        尝试常见RSS路径

        Args:
            url: 网站URL

        Returns:
            RSS feed URL，如果未找到返回None
        """
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        for path in self.COMMON_RSS_PATHS:
            feed_url = urljoin(base_url, path)

            # 验证RSS feed是否有效
            if self._validate_feed(feed_url):
                return feed_url

        return None

    def _validate_feed(self, feed_url: str) -> bool:
        """
        验证RSS feed是否有效

        Args:
            feed_url: RSS feed URL

        Returns:
            是否有效
        """
        try:
            response = requests.get(feed_url, timeout=self.timeout, allow_redirects=True)

            if response.status_code != 200:
                return False

            # 检查内容类型
            content_type = response.headers.get('Content-Type', '').lower()
            if 'xml' not in content_type and 'rss' not in content_type:
                # 有些服务器不返回正确的Content-Type，检查内容
                content = response.text[:1000].lower()
                if '<rss' not in content and '<feed' not in content and '<rdf' not in content:
                    return False

            return True

        except Exception:
            return False

    def discover_all(self, url: str) -> List[str]:
        """
        发现所有可能的RSS feed

        Args:
            url: 网站URL

        Returns:
            RSS feed URL列表
        """
        feeds = []

        # 从HTML头部发现
        feed_url = self._discover_from_html(url)
        if feed_url and feed_url not in feeds:
            feeds.append(feed_url)

        # 从常见路径发现
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        for path in self.COMMON_RSS_PATHS:
            feed_url = urljoin(base_url, path)
            if self._validate_feed(feed_url) and feed_url not in feeds:
                feeds.append(feed_url)

        return feeds


def discover_rss_feed(url: str) -> Optional[str]:
    """
    发现RSS feed的便捷函数

    Args:
        url: 网站URL

    Returns:
        RSS feed URL，如果未找到返回None
    """
    discoverer = RSSDiscoverer()
    return discoverer.discover(url)


def discover_all_rss_feeds(url: str) -> List[str]:
    """
    发现所有RSS feed的便捷函数

    Args:
        url: 网站URL

    Returns:
        RSS feed URL列表
    """
    discoverer = RSSDiscoverer()
    return discoverer.discover_all(url)