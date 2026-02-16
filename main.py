"""
新闻聚合器主入口
"""
from datetime import datetime
import hashlib
from typing import Dict, List

from backend.config import Config
from backend.database import Database
from backend.integrations.notion import NotionIntegration, NotionOutputIntegration
from backend.scrapers.rss import create_rss_scraper
from backend.scrapers.twitter import create_twitter_scraper
from backend.scrapers.youtube import create_youtube_scraper
from backend.scrapers.blog import create_blog_scraper
from backend.processors.dedup import deduplicate_articles
from backend.processors.translator import create_translator, translate_articles
from backend.generators.static import generate_static_pages
from backend.generators.markdown import generate_daily_markdown, generate_latest_markdown, cleanup_old_markdown_files
from backend.utils.logger import logger


class NewsAggregator:
    """新闻聚合器主类"""

    def __init__(self):
        self.db = Database()
        self.notion = NotionIntegration()
        self.translator = create_translator()

    def run(self):
        """运行聚合任务"""
        logger.info("=" * 50)
        logger.info("News Aggregator Started")
        logger.info("=" * 50)

        start_time = datetime.now()

        try:
            # 1. 从Notion获取订阅源
            sources = self.notion.get_active_sources()
            logger.info(f"Found {len(sources)} active sources from Notion")

            if not sources:
                logger.warning("No active sources found, exiting...")
                return

            # 2. 同步订阅源到数据库
            self.sync_sources_to_db(sources)

            # 3. 抓取内容
            all_articles = []
            for source in sources:
                articles = self.scrape_source(source)
                all_articles.extend(articles)

                # 更新Notion抓取时间
                self.notion.update_last_fetched(source['notion_id'])

            logger.info(f"Total articles scraped: {len(all_articles)}")

            # 4. 去重
            existing_urls = set()
            existing_titles = set()

            # 获取数据库中已存在的URL和标题
            db_articles = self.db.get_articles(limit=10000)
            for article in db_articles:
                if article.get('url'):
                    existing_urls.add(article['url'])
                if article.get('title'):
                    title_hash = hashlib.md5(article['title'].encode()).hexdigest()
                    existing_titles.add(title_hash)

            unique_articles = deduplicate_articles(
                all_articles,
                existing_urls=existing_urls,
                existing_titles=existing_titles,
                method='both'
            )

            logger.info(f"Unique articles after deduplication: {len(unique_articles)}")

            # 5. 翻译处理
            # Twitter订阅源：总结+翻译内容
            # 其他订阅源：只翻译英文标题
            twitter_articles = [a for a in unique_articles if a.get('source_type') == 'twitter']
            other_articles = [a for a in unique_articles if a.get('source_type') != 'twitter']

            # 处理Twitter文章：总结+翻译
            if twitter_articles and self.translator:
                logger.info(f"Processing {len(twitter_articles)} Twitter articles (summarize + translate)...")
                for article in twitter_articles:
                    content = article.get('content', '')
                    if content and len(content) > 30:
                        result = self.translator.summarize_and_translate(content)
                        if result.get('summary'):
                            article['summary'] = result['summary']
                        if result.get('translated'):
                            article['translated_content'] = result['translated']
                    # 标题翻译
                    title = article.get('title', '')
                    if title and self._needs_translation(title):
                        translated_title = self.translator.translate(title)
                        if translated_title:
                            article['translated_title'] = translated_title

            # 处理其他订阅源：只翻译英文标题
            if other_articles and self.translator:
                logger.info(f"Processing {len(other_articles)} non-Twitter articles (translate titles only)...")
                for article in other_articles:
                    title = article.get('title', '')
                    if title and self._needs_translation(title):
                        translated_title = self.translator.translate(title)
                        if translated_title:
                            article['translated_title'] = translated_title

            logger.info(f"Translation completed")

            # 6. 保存到数据库
            saved_count = 0
            for article_dict in unique_articles:
                source = self.db.get_source_by_notion_id(article_dict.get('notion_id'))
                if source:
                    article_id = self.db.upsert_article(
                        source_id=source['id'],
                        title=article_dict.get('title', ''),
                        url=article_dict.get('url', ''),
                        content=article_dict.get('content', ''),
                        published_at=article_dict.get('published_at'),
                        summary=article_dict.get('summary'),
                        translated_content=article_dict.get('translated_content'),
                        translated_title=article_dict.get('translated_title'),
                        image_url=article_dict.get('image_url'),
                        video_thumbnail=article_dict.get('video_thumbnail'),
                        media_type=article_dict.get('media_type'),
                        author=article_dict.get('author'),
                        author_name=article_dict.get('author_name'),
                        author_avatar=article_dict.get('author_avatar')
                    )
                    saved_count += 1

            logger.info(f"Saved {saved_count} new articles to database")

            # 7. 生成静态页面
            articles_for_frontend = self.db.get_articles(limit=200)
            stats = self.db.get_statistics()

            generate_static_pages(articles_for_frontend, stats)
            logger.info("Static pages generated")

            # 8. 生成 Markdown 文件
            daily_md_path = generate_daily_markdown(articles_for_frontend)
            logger.info(f"Generated daily markdown: {daily_md_path}")

            latest_md_path = generate_latest_markdown(articles_for_frontend)
            logger.info(f"Generated latest markdown: {latest_md_path}")

            # 清理旧文件（保留最近30天）
            cleanup_old_markdown_files(days=30)

            # 9. 保存到 Notion 输出数据库
            date_str = datetime.now().strftime('%Y年%m月%d日')

            # 读取并保存 latest.md
            try:
                with open(latest_md_path, 'r', encoding='utf-8') as f:
                    latest_content = f.read()
                notion_output = NotionOutputIntegration()
                notion_output.save_markdown(f"今日新闻 - {date_str}", latest_content, date_str)
            except Exception as e:
                logger.error(f"Error saving to Notion: {e}")

            # 打印统计
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Task completed in {elapsed:.2f} seconds")
            logger.info(f"Statistics: {stats}")

        except Exception as e:
            logger.error(f"Error during aggregation: {e}", exc_info=True)
            raise

        logger.info("=" * 50)
        logger.info("News Aggregator Finished")
        logger.info("=" * 50)

    def sync_sources_to_db(self, sources: List[Dict]):
        """
        同步订阅源到数据库

        Args:
            sources: Notion订阅源列表
        """
        for source in sources:
            self.db.upsert_source(
                notion_id=source['notion_id'],
                source_type=source.get('type', 'rss'),
                name=source.get('name', ''),
                feed_url=source.get('feed_url', ''),
                url=source.get('url', ''),
                limit=source.get('limit', 0),
                deep_read=source.get('deep_read', False),
                translate=source.get('translate', False),
                category=','.join(source.get('category', [])),
                description=source.get('description', ''),
                active=True
            )

    def scrape_source(self, source: Dict) -> List[Dict]:
        """
        抓取单个订阅源

        Args:
            source: 订阅源字典

        Returns:
            文章列表
        """
        source_type = source.get('type', '').lower()
        name = source.get('name', '')

        # 优先使用feed_url，如果没有则使用url
        url = source.get('feed_url') or source.get('url', '')
        limit = source.get('limit', 0)
        translate = source.get('translate', False)
        deep_read = source.get('deep_read', False)

        if not url:
            logger.warning(f"No URL found for source: {name}")
            return []

        logger.info(f"Scraping {source_type} source: {name} (limit={limit}, translate={translate})")

        try:
            # 如果没有Feed URL且类型不是YouTube/Twitter，尝试自动发现RSS
            actual_url = url
            actual_type = source_type

            if not source.get('feed_url') and source_type not in ['youtube', 'twitter']:
                # 尝试自动发现RSS feed
                from backend.utils.rss_discoverer import discover_rss_feed
                discovered_feed = discover_rss_feed(url)

                if discovered_feed:
                    logger.info(f"Auto-discovered RSS feed: {discovered_feed}")
                    actual_url = discovered_feed
                    actual_type = 'rss'
                else:
                    logger.info(f"No RSS feed found, using blog scraper")
                    actual_type = 'blog'

            # 根据类型创建对应的抓取器
            config = {'max_articles': limit} if limit > 0 else {}

            if actual_type == 'rss':
                scraper = create_rss_scraper(name, actual_url, config)
            elif actual_type == 'twitter':
                scraper = create_twitter_scraper(name, actual_url, config)
            elif actual_type == 'youtube':
                scraper = create_youtube_scraper(name, actual_url, config)
            elif actual_type == 'blog':
                scraper = create_blog_scraper(name, actual_url, config)
            else:
                logger.warning(f"Unknown source type: {actual_type}")
                return []

            # 抓取内容
            articles = scraper.scrape()

            # 添加源信息到文章
            for article in articles:
                article['notion_id'] = source['notion_id']
                article['source_type'] = actual_type
                article['translate'] = translate
                article['deep_read'] = deep_read

            logger.info(f"Scraped {len(articles)} articles from {name} (type: {actual_type})")
            return articles

        except Exception as e:
            logger.error(f"Error scraping {name}: {e}")
            return []

    def _needs_translation(self, text: str) -> bool:
        """判断文本是否需要翻译（检测是否为英文）"""
        import string
        if not text:
            return False
        english_chars = sum(1 for c in text if c in string.ascii_letters)
        total_chars = sum(1 for c in text if c.isalnum())
        if total_chars == 0:
            return False
        return english_chars / total_chars > 0.3


def main():
    """主函数"""
    aggregator = NewsAggregator()
    aggregator.run()


if __name__ == '__main__':
    main()