"""
数据库操作模块
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from contextlib import contextmanager
from backend.config import Config
from backend.utils.logger import logger


class Database:
    """数据库管理类"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DATABASE_PATH
        self.init_database()

    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def init_database(self):
        """初始化数据库表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 创建订阅源表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    notion_id TEXT UNIQUE,
                    type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    feed_url TEXT,
                    url TEXT,
                    "limit" INTEGER DEFAULT 0,
                    deep_read BOOLEAN DEFAULT 0,
                    translate BOOLEAN DEFAULT 0,
                    category TEXT,
                    description TEXT,
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 创建文章表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT,
                    url TEXT UNIQUE NOT NULL,
                    published_at TIMESTAMP,
                    translated_title TEXT,
                    translated_content TEXT,
                    summary TEXT,
                    image_url TEXT,
                    video_thumbnail TEXT,
                    media_type TEXT,
                    author TEXT,
                    author_name TEXT,
                    author_avatar TEXT,
                    is_translated BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_id) REFERENCES sources(id)
                )
            ''')

            # 创建标签表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            ''')

            # 创建文章-标签关联表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS article_tags (
                    article_id INTEGER NOT NULL,
                    tag_id INTEGER NOT NULL,
                    PRIMARY KEY (article_id, tag_id),
                    FOREIGN KEY (article_id) REFERENCES articles(id),
                    FOREIGN KEY (tag_id) REFERENCES tags(id)
                )
            ''')

            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_source_id ON articles(source_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sources_notion_id ON sources(notion_id)')

            # 添加新列（如果不存在）
            self._add_column_if_not_exists(cursor, 'articles', 'translated_content', 'TEXT')
            self._add_column_if_not_exists(cursor, 'articles', 'summary', 'TEXT')
            self._add_column_if_not_exists(cursor, 'articles', 'image_url', 'TEXT')
            self._add_column_if_not_exists(cursor, 'articles', 'video_thumbnail', 'TEXT')
            self._add_column_if_not_exists(cursor, 'articles', 'media_type', 'TEXT')
            self._add_column_if_not_exists(cursor, 'articles', 'author', 'TEXT')
            self._add_column_if_not_exists(cursor, 'articles', 'author_name', 'TEXT')
            self._add_column_if_not_exists(cursor, 'articles', 'author_avatar', 'TEXT')

    def _add_column_if_not_exists(self, cursor, table: str, column: str, column_type: str):
        """添加列（如果不存在）"""
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        if column not in columns:
            try:
                cursor.execute(f'ALTER TABLE {table} ADD COLUMN {column} {column_type}')
                logger.info(f"Added column {column} to {table}")
            except Exception as e:
                logger.debug(f"Column {column} may already exist: {e}")

    def upsert_source(self, notion_id: str, source_type: str, name: str, feed_url: str = None,
                      url: str = None, limit: int = 0, deep_read: bool = False,
                      translate: bool = False, category: str = None, description: str = None,
                      active: bool = True) -> int:
        """插入或更新订阅源"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sources (
                    notion_id, type, name, feed_url, url, "limit",
                    deep_read, translate, category, description, active
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(notion_id) DO UPDATE SET
                    type = excluded.type,
                    name = excluded.name,
                    feed_url = excluded.feed_url,
                    url = excluded.url,
                    "limit" = excluded."limit",
                    deep_read = excluded.deep_read,
                    translate = excluded.translate,
                    category = excluded.category,
                    description = excluded.description,
                    active = excluded.active,
                    updated_at = CURRENT_TIMESTAMP
            ''', (
                notion_id, source_type, name, feed_url, url, limit,
                deep_read, translate, category, description, active
            ))
            return cursor.lastrowid

    def get_source_by_notion_id(self, notion_id: str) -> Optional[Dict]:
        """根据Notion ID获取订阅源"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM sources WHERE notion_id = ?', (notion_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_active_sources(self) -> List[Dict]:
        """获取所有启用的订阅源"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM sources WHERE active = 1')
            return [dict(row) for row in cursor.fetchall()]

    def upsert_article(self, source_id: int, title: str, url: str, content: str = None,
                       published_at: datetime = None, summary: str = None,
                       translated_content: str = None, translated_title: str = None,
                       image_url: str = None, video_thumbnail: str = None,
                       media_type: str = None, author: str = None,
                       author_name: str = None, author_avatar: str = None) -> Optional[int]:
        """插入或更新文章"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            published_at_str = published_at.isoformat() if published_at else None
            try:
                cursor.execute('''
                    INSERT INTO articles (
                        source_id, title, url, content, published_at, 
                        summary, translated_content, translated_title,
                        image_url, video_thumbnail, media_type,
                        author, author_name, author_avatar
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    source_id, title, url, content, published_at_str,
                    summary, translated_content, translated_title,
                    image_url, video_thumbnail, media_type,
                    author, author_name, author_avatar
                ))
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                # URL已存在，更新内容
                logger.debug(f"Article already exists, updating: {url}")
                cursor.execute('''
                    UPDATE articles SET
                        content = COALESCE(?, content),
                        summary = COALESCE(?, summary),
                        translated_content = COALESCE(?, translated_content),
                        translated_title = COALESCE(?, translated_title),
                        image_url = COALESCE(?, image_url),
                        video_thumbnail = COALESCE(?, video_thumbnail),
                        media_type = COALESCE(?, media_type),
                        author = COALESCE(?, author),
                        author_name = COALESCE(?, author_name),
                        author_avatar = COALESCE(?, author_avatar)
                    WHERE url = ?
                ''', (
                    content, summary, translated_content, translated_title,
                    image_url, video_thumbnail, media_type,
                    author, author_name, author_avatar, url
                ))
                return None

    def update_article_translation(self, article_id: int, translated_title: str):
        """更新文章翻译"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE articles SET translated_title = ?, is_translated = 1
                WHERE id = ?
            ''', (translated_title, article_id))

    def get_articles(self, limit: int = 100, source_id: int = None,
                     start_date: datetime = None, end_date: datetime = None) -> List[Dict]:
        """获取文章列表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = '''
                SELECT 
                    a.*, 
                    s.name as source_name, 
                    s.type as source_type,
                    s.category,
                    s.description,
                    s.deep_read,
                    s.translate as source_translate
                FROM articles a
                JOIN sources s ON a.source_id = s.id
                WHERE 1=1
            '''
            params = []

            if source_id:
                query += ' AND a.source_id = ?'
                params.append(source_id)

            if start_date:
                query += ' AND a.published_at >= ?'
                params.append(start_date.isoformat())

            if end_date:
                query += ' AND a.published_at <= ?'
                params.append(end_date.isoformat())

            query += ' ORDER BY a.published_at DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 订阅源统计
            cursor.execute('SELECT COUNT(*) as total_sources, SUM(CASE WHEN active=1 THEN 1 ELSE 0 END) as active_sources FROM sources')
            sources_row = cursor.fetchone()
            sources_stats = {
                'total_sources': sources_row['total_sources'] if sources_row else 0,
                'active_sources': sources_row['active_sources'] if sources_row else 0
            }

            # 文章统计
            cursor.execute('SELECT COUNT(*) as total_articles, MAX(published_at) as latest_article FROM articles')
            articles_row = cursor.fetchone()
            articles_stats = {
                'total_articles': articles_row['total_articles'] if articles_row else 0,
                'latest_article': articles_row['latest_article'] if articles_row else None
            }

            # 按类型统计
            cursor.execute('SELECT type, COUNT(*) as count FROM sources GROUP BY type')
            by_type = {row['type']: row['count'] for row in cursor.fetchall()}

            # 按分类统计
            cursor.execute('SELECT category, COUNT(*) as count FROM sources WHERE category IS NOT NULL GROUP BY category')
            by_category = {row['category']: row['count'] for row in cursor.fetchall()}

            # 翻译统计
            cursor.execute('SELECT COUNT(*) as translated FROM articles WHERE is_translated = 1')
            translated_row = cursor.fetchone()
            translated_count = translated_row['translated'] if translated_row else 0

            return {
                'sources': sources_stats,
                'articles': articles_stats,
                'by_type': by_type,
                'by_category': by_category,
                'translated_count': translated_count
            }