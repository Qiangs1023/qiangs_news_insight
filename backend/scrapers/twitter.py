"""
Twitter抓取模块
"""
import re
from typing import List, Dict
from datetime import datetime
from .base import BaseScraper, Article
from backend.config import Config


class TwitterScraper(BaseScraper):
    """Twitter抓取器"""

    def __init__(self, name: str, url: str, config: Dict = None):
        super().__init__(name, url, config)
        self.max_tweets = config.get('max_tweets', 50) if config else 50

    def fetch(self) -> List[Article]:
        """
        从Twitter List抓取推文

        Returns:
            文章列表
        """
        print(f"Fetching Twitter from {self.name}: {self.url}")

        # 检查API密钥 - 优先使用 BEARER_TOKEN
        bearer_token = Config.TWITTER_BEARER_TOKEN or Config.TWITTER_API_KEY
        if not bearer_token:
            print("Twitter Bearer Token not configured, skipping...")
            return []

        # 尝试使用 tweepy
        try:
            import tweepy
        except ImportError:
            print("tweepy not installed, skipping Twitter scraping...")
            return []

        try:
            # 使用 Twitter API v2 (Bearer Token)
            client = tweepy.Client(bearer_token=bearer_token)

            # 从URL提取list_id
            list_id = self._extract_list_id(self.url)
            if not list_id:
                print(f"Could not extract list ID from URL: {self.url}")
                return []

            # 获取 List 推文
            tweets = client.get_list_tweets(
                id=list_id,
                max_results=min(self.max_tweets, 100),
                tweet_fields=['created_at', 'author_id', 'public_metrics']
            )

            articles = []
            if tweets.data:
                for tweet in tweets.data:
                    # 获取用户信息
                    author_id = tweet.author_id
                    author_name = ""
                    if author_id:
                        users = client.get_users(ids=[author_id])
                        if users.data:
                            author_name = users.data[0].username

                    article = Article(
                        title=self._truncate_text(tweet.text, 100),
                        url=f"https://twitter.com/i/web/status/{tweet.id}",
                        content=tweet.text,
                        published_at=tweet.created_at,
                        author=author_name
                    )
                    articles.append(article)

            print(f"Fetched {len(articles)} tweets from {self.name}")
            return articles

        except Exception as e:
            print(f"Error fetching Twitter: {e}")
            return []

    def _extract_list_id(self, url: str) -> str:
        """从URL提取List ID"""
        # 示例URL格式:
        # https://twitter.com/i/lists/123456789
        # https://x.com/i/lists/123456789
        # https://twitter.com/{username}/lists/{list_id}
        # https://x.com/{username}/lists/{list_id}

        patterns = [
            r'(?:twitter|x)\.com/i/lists/(\d+)',
            r'(?:twitter|x)\.com/[^/]+/lists/(\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return ''

    def _truncate_text(self, text: str, max_length: int) -> str:
        """截断文本"""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + '...'


def create_twitter_scraper(name: str, url: str, config: Dict = None) -> TwitterScraper:
    """创建Twitter抓取器"""
    return TwitterScraper(name, url, config)