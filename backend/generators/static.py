"""
静态页面生成模块
"""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from backend.config import Config


class StaticPageGenerator:
    """静态页面生成器 - 只生成JSON数据，HTML为静态模板"""

    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir or Config.FRONTEND_DIST_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_all(self, articles: List[Dict], stats: Dict = None):
        """
        生成JSON数据文件

        Args:
            articles: 文章列表
            stats: 统计信息
        """
        print("Generating static data...")
        self.generate_data(articles, stats)
        print(f"Data generated in {self.output_dir}")

    def generate_data(self, articles: List[Dict], stats: Dict = None):
        """
        生成JSON数据文件

        Args:
            articles: 文章列表
            stats: 统计信息
        """
        data = {
            'articles': articles,
            'statistics': stats or {},
            'updated_at': datetime.now().isoformat()
        }

        data_file = self.output_dir / 'data' / 'articles.json'
        data_file.parent.mkdir(parents=True, exist_ok=True)

        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Generated data/articles.json ({len(articles)} articles)")


def generate_static_pages(articles: List[Dict], stats: Dict = None):
    """
    生成静态数据的便捷函数

    Args:
        articles: 文章列表
        stats: 统计信息
    """
    generator = StaticPageGenerator()
    generator.generate_all(articles, stats)