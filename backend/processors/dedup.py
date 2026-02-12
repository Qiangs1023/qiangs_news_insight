"""
去重模块
"""
from typing import List, Dict, Set
from hashlib import md5


class Deduplicator:
    """去重器"""

    def __init__(self):
        self.seen_urls: Set[str] = set()
        self.seen_titles: Set[str] = set()

    def deduplicate_by_url(self, articles: List[Dict], existing_urls: Set[str] = None) -> List[Dict]:
        """
        根据URL去重

        Args:
            articles: 文章列表
            existing_urls: 已存在的URL集合

        Returns:
            去重后的文章列表
        """
        if existing_urls is None:
            existing_urls = set()

        unique_articles = []
        for article in articles:
            url = article.get('url', '')
            if url and url not in existing_urls:
                unique_articles.append(article)
                existing_urls.add(url)

        print(f"Deduplicated by URL: {len(articles)} -> {len(unique_articles)}")
        return unique_articles

    def deduplicate_by_title(self, articles: List[Dict], existing_titles: Set[str] = None) -> List[Dict]:
        """
        根据标题去重（使用标题的MD5哈希）

        Args:
            articles: 文章列表
            existing_titles: 已存在的标题集合

        Returns:
            去重后的文章列表
        """
        if existing_titles is None:
            existing_titles = set()

        unique_articles = []
        for article in articles:
            title = article.get('title', '')
            title_hash = md5(title.encode()).hexdigest()

            if title and title_hash not in existing_titles:
                unique_articles.append(article)
                existing_titles.add(title_hash)

        print(f"Deduplicated by title: {len(articles)} -> {len(unique_articles)}")
        return unique_articles

    def deduplicate(self, articles: List[Dict], existing_urls: Set[str] = None,
                    existing_titles: Set[str] = None, method: str = 'both') -> List[Dict]:
        """
        综合去重

        Args:
            articles: 文章列表
            existing_urls: 已存在的URL集合
            existing_titles: 已存在的标题集合
            method: 去重方法（url/title/both）

        Returns:
            去重后的文章列表
        """
        if existing_urls is None:
            existing_urls = set()
        if existing_titles is None:
            existing_titles = set()

        if method == 'url':
            return self.deduplicate_by_url(articles, existing_urls)
        elif method == 'title':
            return self.deduplicate_by_title(articles, existing_titles)
        else:  # both
            articles = self.deduplicate_by_url(articles, existing_urls)
            articles = self.deduplicate_by_title(articles, existing_titles)
            return articles


def deduplicate_articles(articles: List[Dict], existing_urls: Set[str] = None,
                         existing_titles: Set[str] = None, method: str = 'both') -> List[Dict]:
    """
    去重文章列表的便捷函数

    Args:
        articles: 文章列表
        existing_urls: 已存在的URL集合
        existing_titles: 已存在的标题集合
        method: 去重方法（url/title/both）

    Returns:
        去重后的文章列表
    """
    deduplicator = Deduplicator()
    return deduplicator.deduplicate(articles, existing_urls, existing_titles, method)