"""
博客抓取模块
"""
import requests
from bs4 import BeautifulSoup
from typing import List
from datetime import datetime
from .base import BaseScraper, Article
from config import Config


class BlogScraper(BaseScraper):
    """博客抓取器"""

    def __init__(self, name: str, url: str, config: Dict = None):
        super().__init__(name, url, config)
        self.max_articles = config.get('max_articles', 20) if config else 20

    def fetch(self) -> List[Article]:
        """
        从博客网站抓取文章

        Returns:
            文章列表
        """
        print(f"Fetching Blog from {self.name}: {self.url}")

        try:
            # 获取页面内容
            response = requests.get(self.url, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            articles = []

            # 尝试通用的文章选择器
            article_selectors = [
                'article',
                '.post',
                '.entry',
                '.blog-post',
                '[itemtype="http://schema.org/BlogPosting"]'
            ]

            for selector in article_selectors:
                article_elements = soup.select(selector)

                if article_elements:
                    print(f"Found {len(article_elements)} articles with selector: {selector}")

                    for element in article_elements[:self.max_articles]:
                        try:
                            article = self._parse_article_element(element)
                            if article:
                                articles.append(article)
                        except Exception as e:
                            print(f"Error parsing article element: {e}")
                            continue

                    if articles:
                        break

            print(f"Successfully parsed {len(articles)} articles from {self.name}")
            return articles

        except Exception as e:
            print(f"Error fetching blog {self.name}: {e}")
            return []

    def _parse_article_element(self, element) -> Article:
        """解析文章元素"""
        # 提取标题
        title = ''
        title_selectors = ['h1', 'h2', 'h3', '.title', '.post-title', '[itemprop="headline"]']
        for selector in title_selectors:
            title_elem = element.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                break

        if not title:
            return None

        # 提取链接
        url = ''
        link_elem = element.select_one('a')
        if link_elem and link_elem.get('href'):
            url = link_elem['href']
            # 处理相对URL
            if url.startswith('/'):
                base_url = '/'.join(self.url.split('/')[:3])
                url = base_url + url
        else:
            url = self.url

        # 提取内容
        content = ''
        content_selectors = ['.content', '.post-content', '.entry-content', '[itemprop="articleBody"]', 'p']
        for selector in content_selectors:
            content_elem = element.select_one(selector)
            if content_elem:
                content = content_elem.get_text(strip=True)[:500]
                break

        # 提取发布时间
        published_at = datetime.now()
        time_selectors = ['time', '.date', '.published', '[itemprop="datePublished"]']
        for selector in time_selectors:
            time_elem = element.select_one(selector)
            if time_elem:
                time_str = time_elem.get('datetime') or time_elem.get_text(strip=True)
                if time_str:
                    try:
                        published_at = self._parse_date(time_str)
                    except:
                        pass
                    break

        # 提取作者
        author = ''
        author_selectors = ['.author', '[itemprop="author"]', '.byline']
        for selector in author_selectors:
            author_elem = element.select_one(selector)
            if author_elem:
                author = author_elem.get_text(strip=True)
                break

        return Article(
            title=title,
            url=url,
            content=content,
            published_at=published_at,
            author=author
        )

    def _parse_date(self, date_str: str) -> datetime:
        """解析日期字符串"""
        # 尝试多种日期格式
        date_formats = [
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%B %d, %Y',
            '%d %B %Y',
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                pass

        # 尝试使用dateutil
        try:
            from dateutil import parser
            return parser.parse(date_str)
        except:
            pass

        return datetime.now()


def create_blog_scraper(name: str, url: str, config: Dict = None) -> BlogScraper:
    """创建博客抓取器"""
    return BlogScraper(name, url, config)