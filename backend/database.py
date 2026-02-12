"""
数据库操作模块
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from contextlib import contextmanager
from config import Config


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
                       published_at: datetime = None) -> Optional[int]:
        """插入或更新文章"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            published_at_str = published_at.isoformat() if published_at else None
            try:
                cursor.execute('''
                    INSERT INTO articles (source_id, title, url, content, published_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (source_id, title, url, content, published_at_str))
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                # URL已存在，跳过
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
            sources_stats = dict(cursor.fetchone())

            # 文章统计
            cursor.execute('SELECT COUNT(*) as total_articles, MAX(published_at) as latest_article FROM articles')
            articles_stats = dict(cursor.fetchone())

            # 按类型统计
            cursor.execute('SELECT type, COUNT(*) as count FROM sources GROUP BY type')
            by_type = {row['type']: row['count'] for row in cursor.fetchall()}

            # 按分类统计
            cursor.execute('SELECT category, COUNT(*) as count FROM sources WHERE category IS NOT NULL GROUP BY category')
            by_category = {row['category']: row['count'] for row in cursor.fetchall()}

            # 翻译统计
            cursor.execute('SELECT COUNT(*) as translated FROM articles WHERE is_translated = 1')
            translated_count = cursor.fetchone()['translated']

            return {
                'sources': sources_stats,
                'articles': articles_stats,
                'by_type': by_type,
                'by_category': by_category,
                'translated_count': translated_count
            }