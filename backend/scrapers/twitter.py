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
        从Twitter List或用户主页抓取推文

        Returns:
            文章列表
        """
        print(f"Fetching Twitter from {self.name}: {self.url}")

        # 检查API密钥
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
            client = tweepy.Client(bearer_token=bearer_token)

            # 优先检查是否为 List URL
            list_id = self._extract_list_id(self.url)
            if list_id:
                return self._fetch_list_tweets(client, list_id)

            # 否则尝试用户主页
            username = self._extract_username(self.url)
            if username:
                return self._fetch_user_tweets(client, username)

            print(f"Could not extract list ID or username from URL: {self.url}")
            return []

        except Exception as e:
            print(f"Error fetching Twitter: {e}")
            return []

    def _fetch_list_tweets(self, client, list_id: str) -> List[Article]:
        """获取List推文"""
        tweets = client.get_list_tweets(
            id=list_id,
            max_results=min(self.max_tweets, 100),
            tweet_fields=['created_at', 'author_id', 'public_metrics']
        )

        articles = []
        if tweets.data:
            for tweet in tweets.data:
                author_name = ""
                if tweet.author_id:
                    users = client.get_users(ids=[tweet.author_id])
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

        print(f"Fetched {len(articles)} tweets from list")
        return articles

    def _fetch_user_tweets(self, client, username: str) -> List[Article]:
        """获取用户推文"""
        # 获取用户ID
        user = client.get_user(username=username)
        if not user.data:
            print(f"User not found: {username}")
            return []

        user_id = user.data.id

        # 获取用户推文
        tweets = client.get_users_tweets(
            id=user_id,
            max_results=min(self.max_tweets, 100),
            tweet_fields=['created_at', 'public_metrics']
        )

        articles = []
        if tweets.data:
            for tweet in tweets.data:
                article = Article(
                    title=self._truncate_text(tweet.text, 100),
                    url=f"https://twitter.com/{username}/status/{tweet.id}",
                    content=tweet.text,
                    published_at=tweet.created_at,
                    author=username
                )
                articles.append(article)

        print(f"Fetched {len(articles)} tweets from @{username}")
        return articles

    def _extract_list_id(self, url: str) -> str:
        """从URL提取List ID"""
        patterns = [
            r'(?:twitter|x)\.com/i/lists/(\d+)',
            r'(?:twitter|x)\.com/[^/]+/lists/(\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return ''

    def _extract_username(self, url: str) -> str:
        """从URL提取用户名"""
        # 示例URL格式:
        # https://twitter.com/vista8
        # https://x.com/vista8
        # https://www.twitter.com/vista8
        pattern = r'(?:twitter|x|www\.twitter)\.com/([^/?]+)'
        match = re.search(pattern, url)
        if match:
            username = match.group(1)
            # 排除已经是列表或特定路径的用户名
            if username and username not in ['i', 'intent', 'search']:
                return username
        return ''

    def _truncate_text(self, text: str, max_length: int) -> str:
        """截断文本"""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + '...'


def create_twitter_scraper(name: str, url: str, config: Dict = None) -> TwitterScraper:
    """创建Twitter抓取器"""
    return TwitterScraper(name, url, config)
