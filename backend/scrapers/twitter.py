"""
Twitter抓取模块 - 增强版，支持图片、视频封面抓取
"""
import re
from typing import List, Dict, Optional
from datetime import datetime
from .base import BaseScraper, Article
from backend.config import Config


class TwitterScraper(BaseScraper):
    """Twitter抓取器 - 支持图片和视频封面"""

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
        """获取List推文（包含媒体信息）"""
        tweets = client.get_list_tweets(
            id=list_id,
            max_results=min(self.max_tweets, 100),
            tweet_fields=['created_at', 'author_id', 'public_metrics', 'attachments', 'entities'],
            expansions=['attachments.media_keys', 'author_id'],
            media_fields=['url', 'preview_image_url', 'type', 'alt_text'],
            user_fields=['username', 'name', 'profile_image_url']
        )

        articles = []
        if not tweets.data:
            return articles

        # 构建媒体映射
        media_map = self._build_media_map(tweets)
        # 构建用户映射
        user_map = self._build_user_map(tweets)

        for tweet in tweets.data:
            author_info = user_map.get(tweet.author_id, {})
            media_info = self._get_tweet_media(tweet, media_map)

            article = Article(
                title=self._truncate_text(tweet.text, 100),
                url=f"https://twitter.com/i/web/status/{tweet.id}",
                content=tweet.text,
                published_at=tweet.created_at,
                author=author_info.get('username', ''),
                author_name=author_info.get('name', ''),
                author_avatar=author_info.get('profile_image_url', ''),
                image_url=media_info.get('image_url'),
                video_thumbnail=media_info.get('video_thumbnail'),
                media_type=media_info.get('media_type'),
                media_urls=media_info.get('media_urls', [])
            )
            articles.append(article)

        print(f"Fetched {len(articles)} tweets from list")
        return articles

    def _fetch_user_tweets(self, client, username: str) -> List[Article]:
        """获取用户推文（包含媒体信息）"""
        # 获取用户ID
        user = client.get_user(username=username, user_fields=['profile_image_url'])
        if not user.data:
            print(f"User not found: {username}")
            return []

        user_id = user.data.id
        author_info = {
            'username': username,
            'name': user.data.name,
            'profile_image_url': getattr(user.data, 'profile_image_url', '')
        }

        # 获取用户推文
        tweets = client.get_users_tweets(
            id=user_id,
            max_results=min(self.max_tweets, 100),
            tweet_fields=['created_at', 'public_metrics', 'attachments', 'entities'],
            expansions=['attachments.media_keys'],
            media_fields=['url', 'preview_image_url', 'type', 'alt_text']
        )

        articles = []
        if not tweets.data:
            return articles

        # 构建媒体映射
        media_map = self._build_media_map(tweets)

        for tweet in tweets.data:
            media_info = self._get_tweet_media(tweet, media_map)

            article = Article(
                title=self._truncate_text(tweet.text, 100),
                url=f"https://twitter.com/{username}/status/{tweet.id}",
                content=tweet.text,
                published_at=tweet.created_at,
                author=username,
                author_name=author_info.get('name', ''),
                author_avatar=author_info.get('profile_image_url', ''),
                image_url=media_info.get('image_url'),
                video_thumbnail=media_info.get('video_thumbnail'),
                media_type=media_info.get('media_type'),
                media_urls=media_info.get('media_urls', [])
            )
            articles.append(article)

        print(f"Fetched {len(articles)} tweets from @{username}")
        return articles

    def _build_media_map(self, response) -> Dict:
        """构建媒体映射表"""
        media_map = {}
        if hasattr(response, 'includes') and response.includes:
            media_list = response.includes.get('media', [])
            for media in media_list:
                media_key = getattr(media, 'media_key', None)
                if media_key:
                    media_map[media_key] = {
                        'type': getattr(media, 'type', 'photo'),
                        'url': getattr(media, 'url', ''),
                        'preview_image_url': getattr(media, 'preview_image_url', ''),
                        'alt_text': getattr(media, 'alt_text', '')
                    }
        return media_map

    def _build_user_map(self, response) -> Dict:
        """构建用户映射表"""
        user_map = {}
        if hasattr(response, 'includes') and response.includes:
            users = response.includes.get('users', [])
            for user in users:
                user_id = getattr(user, 'id', None)
                if user_id:
                    user_map[user_id] = {
                        'username': getattr(user, 'username', ''),
                        'name': getattr(user, 'name', ''),
                        'profile_image_url': getattr(user, 'profile_image_url', '')
                    }
        return user_map

    def _get_tweet_media(self, tweet, media_map: Dict) -> Dict:
        """获取推文的媒体信息"""
        result = {
            'image_url': None,
            'video_thumbnail': None,
            'media_type': None,
            'media_urls': []
        }

        # 获取附件中的媒体
        attachments = getattr(tweet, 'attachments', None)
        if not attachments:
            return result

        media_keys = attachments.get('media_keys', [])
        if not media_keys:
            return result

        for key in media_keys:
            media = media_map.get(key)
            if not media:
                continue

            media_type = media.get('type', 'photo')
            result['media_type'] = media_type

            if media_type == 'photo':
                url = media.get('url', '')
                if url:
                    result['media_urls'].append(url)
                    if not result['image_url']:
                        result['image_url'] = url
            elif media_type == 'video':
                # 视频缩略图
                preview = media.get('preview_image_url', '')
                if preview:
                    result['video_thumbnail'] = preview
                    if not result['image_url']:
                        result['image_url'] = preview
                    result['media_urls'].append(preview)
            elif media_type == 'animated_gif':
                preview = media.get('preview_image_url', '')
                if preview:
                    result['image_url'] = preview
                    result['media_urls'].append(preview)

        return result

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
