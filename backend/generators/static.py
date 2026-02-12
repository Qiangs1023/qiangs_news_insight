"""
静态页面生成模块
"""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from config import Config


class StaticPageGenerator:
    """静态页面生成器"""

    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir or Config.FRONTEND_DIST_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_all(self, articles: List[Dict], stats: Dict = None):
        """
        生成所有静态页面

        Args:
            articles: 文章列表
            stats: 统计信息
        """
        print("Generating static pages...")

        # 生成主页面
        self.generate_index(articles, stats)

        # 生成数据文件
        self.generate_data(articles, stats)

        # 复制CSS和JS文件
        self.copy_assets()

        print(f"Static pages generated in {self.output_dir}")

    def generate_index(self, articles: List[Dict], stats: Dict = None):
        """
        生成主页面HTML

        Args:
            articles: 文章列表
            stats: 统计信息
        """
        articles_html = self._render_articles(articles)

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>News Aggregator</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <header class="bg-dark text-white py-3 mb-4">
        <div class="container">
            <div class="d-flex justify-content-between align-items-center">
                <h1 class="h4 mb-0">News Aggregator</h1>
                <div class="d-flex align-items-center gap-3">
                    <span class="badge bg-info">Total: {stats.get('articles', {}).get('total_articles', 0) if stats else len(articles)}</span>
                    <span class="badge bg-success">Sources: {stats.get('sources', {}).get('active_sources', 0) if stats else 0}</span>
                </div>
            </div>
        </div>
    </header>

    <main class="container">
        <div class="filters mb-4">
            <div class="row g-2">
                <div class="col-md-6">
                    <input type="text" class="form-control" id="searchInput" placeholder="Search articles...">
                </div>
                <div class="col-md-3">
                    <select class="form-select" id="sourceFilter">
                        <option value="">All Sources</option>
                        <!-- Sources will be added dynamically -->
                    </select>
                </div>
                <div class="col-md-3">
                    <select class="form-select" id="dateFilter">
                        <option value="">All Time</option>
                        <option value="today">Today</option>
                        <option value="week">This Week</option>
                        <option value="month">This Month</option>
                    </select>
                </div>
            </div>
        </div>

        <div id="articlesContainer" class="row g-4">
            {articles_html}
        </div>
    </main>

    <footer class="bg-light text-center py-3 mt-5">
        <div class="container">
            <p class="mb-0 text-muted">Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/vue@3/dist/vue.global.prod.js"></script>
    <script src="js/app.js"></script>
</body>
</html>"""

        # 写入文件
        index_file = self.output_dir / 'index.html'
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"Generated index.html")

    def _render_articles(self, articles: List[Dict]) -> str:
        """
        渲染文章卡片HTML

        Args:
            articles: 文章列表

        Returns:
            HTML字符串
        """
        html_parts = []

        for article in articles[:50]:  # 限制显示数量
            title = article.get('translated_title') or article.get('title', 'No Title')
            content = article.get('content', '')[:200]
            url = article.get('url', '#')
            source_name = article.get('source_name', 'Unknown')
            source_type = article.get('source_type', 'unknown')
            published_at = article.get('published_at', '')

            if published_at:
                try:
                    if isinstance(published_at, str):
                        published_at = datetime.fromisoformat(published_at)
                    published_str = published_at.strftime('%Y-%m-%d %H:%M')
                except:
                    published_str = ''
            else:
                published_str = ''

            html_part = f"""
            <div class="col-md-6 col-lg-4">
                <div class="card h-100 article-card">
                    <div class="card-body">
                        <span class="badge bg-secondary source-badge mb-2">{source_name}</span>
                        <h5 class="card-title">
                            <a href="{url}" target="_blank" rel="noopener noreferrer" class="text-decoration-none">
                                {title}
                            </a>
                        </h5>
                        <p class="card-text text-muted">{content}...</p>
                        <div class="d-flex justify-content-between align-items-center">
                            <small class="text-muted">
                                <i class="bi bi-clock"></i> {published_str}
                            </small>
                            <a href="{url}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-primary">
                                Read More
                            </a>
                        </div>
                    </div>
                </div>
            </div>"""

            html_parts.append(html_part)

        return ''.join(html_parts)

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

        print(f"Generated data/articles.json")

    def copy_assets(self):
        """复制CSS和JS文件"""
        # 创建CSS目录
        css_dir = self.output_dir / 'css'
        css_dir.mkdir(parents=True, exist_ok=True)

        # 创建简单的CSS文件
        css_content = """
.article-card {
    transition: transform 0.2s;
}

.article-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.source-badge {
    font-size: 0.75rem;
}

.card-title a {
    color: #212529;
}

.card-title a:hover {
    color: #0d6efd;
}
"""

        css_file = css_dir / 'style.css'
        with open(css_file, 'w', encoding='utf-8') as f:
            f.write(css_content)

        # 创建JS目录
        js_dir = self.output_dir / 'js'
        js_dir.mkdir(parents=True, exist_ok=True)

        # 创建简单的JS文件
        js_content = """
// Vue应用
const { createApp } = Vue;

createApp({
    data() {
        return {
            articles: [],
            filteredArticles: [],
            searchQuery: '',
            selectedSource: '',
            selectedDate: ''
        }
    },
    mounted() {
        this.loadArticles();
    },
    methods: {
        async loadArticles() {
            try {
                const response = await fetch('data/articles.json');
                const data = await response.json();
                this.articles = data.articles;
                this.filteredArticles = this.articles;
                this.populateSourceFilter();
            } catch (error) {
                console.error('Error loading articles:', error);
            }
        },
        populateSourceFilter() {
            const sources = [...new Set(this.articles.map(a => a.source_name))];
            const select = document.getElementById('sourceFilter');
            sources.forEach(source => {
                const option = document.createElement('option');
                option.value = source;
                option.textContent = source;
                select.appendChild(option);
            });
        },
        filterArticles() {
            let filtered = this.articles;

            // 搜索过滤
            if (this.searchQuery) {
                const query = this.searchQuery.toLowerCase();
                filtered = filtered.filter(a =>
                    (a.title && a.title.toLowerCase().includes(query)) ||
                    (a.content && a.content.toLowerCase().includes(query))
                );
            }

            // 源过滤
            if (this.selectedSource) {
                filtered = filtered.filter(a => a.source_name === this.selectedSource);
            }

            // 日期过滤
            if (this.selectedDate) {
                const now = new Date();
                const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

                filtered = filtered.filter(a => {
                    const articleDate = new Date(a.published_at);
                    if (this.selectedDate === 'today') {
                        return articleDate >= today;
                    } else if (this.selectedDate === 'week') {
                        const weekAgo = new Date(today);
                        weekAgo.setDate(weekAgo.getDate() - 7);
                        return articleDate >= weekAgo;
                    } else if (this.selectedDate === 'month') {
                        const monthAgo = new Date(today);
                        monthAgo.setMonth(monthAgo.getMonth() - 1);
                        return articleDate >= monthAgo;
                    }
                    return true;
                });
            }

            this.filteredArticles = filtered;
        }
    }
}).mount('#app');
"""

        js_file = js_dir / 'app.js'
        with open(js_file, 'w', encoding='utf-8') as f:
            f.write(js_content)

        print("Generated CSS and JS files")


def generate_static_pages(articles: List[Dict], stats: Dict = None):
    """
    生成静态页面的便捷函数

    Args:
        articles: 文章列表
        stats: 统计信息
    """
    generator = StaticPageGenerator()
    generator.generate_all(articles, stats)