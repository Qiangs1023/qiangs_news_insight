"""
YouTube抓取模块
"""
import re
from typing import List, Dict
from datetime import datetime
from .base import BaseScraper, Article
from backend.config import Config


class YouTubeScraper(BaseScraper):
    """YouTube抓取器"""

    def __init__(self, name: str, url: str, config: Dict = None):
        super().__init__(name, url, config)
        self.max_videos = config.get('max_videos', 20) if config else 20

    def fetch(self) -> List[Article]:
        """
        从YouTube频道抓取视频

        Returns:
            文章列表
        """
        print(f"Fetching YouTube from {self.name}: {self.url}")

        # 检查API密钥
        if not Config.YOUTUBE_API_KEY:
            print("YouTube API key not configured, skipping...")
            return []

        # 尝试使用 google-api-python-client
        try:
            from googleapiclient.discovery import build
        except ImportError:
            print("google-api-python-client not installed, skipping YouTube scraping...")
            return []

        try:
            # 创建 YouTube service
            youtube = build('youtube', 'v3', developerKey=Config.YOUTUBE_API_KEY)

            # 从URL提取 channel_id
            channel_id = self._extract_channel_id(self.url)
            if not channel_id:
                print(f"Could not extract channel ID from URL: {self.url}")
                return []

            # 获取频道视频
            request = youtube.search().list(
                part='snippet',
                channelId=channel_id,
                maxResults=min(self.max_videos, 50),
                order='date',
                type='video'
            )
            response = request.execute()

            articles = []
            for item in response.get('items', []):
                if item['id']['kind'] == 'youtube#video':
                    video_id = item['id']['videoId']
                    snippet = item['snippet']

                    published_at = datetime.fromisoformat(
                        snippet['publishedAt'].replace('Z', '+00:00')
                    )

                    article = Article(
                        title=snippet['title'],
                        url=f"https://www.youtube.com/watch?v={video_id}",
                        content=snippet['description'][:500],
                        published_at=published_at,
                        author=snippet['channelTitle']
                    )
                    articles.append(article)

            print(f"Fetched {len(articles)} videos from {self.name}")
            return articles

        except Exception as e:
            print(f"Error fetching YouTube: {e}")
            return []

    def _extract_channel_id(self, url: str) -> str:
        """从URL提取Channel ID

        支持多种URL格式:
        - https://www.youtube.com/channel/UCxxxxxxxxxxxxxx
        - https://www.youtube.com/@username
        - https://www.youtube.com/user/username
        - https://www.youtube.com/c/customurl
        """
        # 提取 channel ID
        patterns = [
            (r'youtube\.com/channel/([A-Za-z0-9_-]{24})', 1),
            (r'youtube\.com/[@/]?([A-Za-z0-9_-]+)', 1),
            (r'youtube\.com/c/([A-Za-z0-9_-]+)', 1),
            (r'youtube\.com/user/([A-Za-z0-9_-]+)', 1),
        ]

        for pattern, group in patterns:
            match = re.search(pattern, url)
            if match:
                identifier = match.group(group)

                # 如果是 @username 或 custom URL，需要先调用 API 获取 channel ID
                if not identifier.startswith('UC'):
                    channel_id = self._resolve_username(identifier)
                    return channel_id

                return identifier

        return ''

    def _resolve_username(self, username: str) -> str:
        """将用户名解析为 Channel ID"""
        try:
            from googleapiclient.discovery import build

            youtube = build('youtube', 'v3', developerKey=Config.YOUTUBE_API_KEY)

            request = youtube.search().list(
                part='id',
                q=username,
                type='channel',
                maxResults=1
            )
            response = request.execute()

            if response.get('items'):
                return response['items'][0]['id']['channelId']

        except Exception as e:
            print(f"Error resolving username {username}: {e}")

        return ''


def create_youtube_scraper(name: str, url: str, config: Dict = None) -> YouTubeScraper:
    """创建YouTube抓取器"""
    return YouTubeScraper(name, url, config)