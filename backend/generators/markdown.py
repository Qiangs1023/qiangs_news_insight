"""
Markdown 生成器模块
"""
from datetime import datetime, timedelta
from typing import List, Dict
from pathlib import Path
import glob
import os
from backend.config import Config


def generate_markdown(articles: List[Dict], output_path: str = None) -> str:
    """
    生成 Markdown 格式的文章列表

    Args:
        articles: 文章列表
        output_path: 输出文件路径（可选）

    Returns:
        Markdown 内容字符串
    """
    if not articles:
        return "# 今日新闻\n\n暂无文章\n"

    # 按发布时间倒序
    sorted_articles = sorted(articles, key=lambda x: x.get('published_at', ''), reverse=True)

    # 按来源分组
    sources = {}
    for article in sorted_articles:
        source_name = article.get('source_name', 'Unknown')
        if source_name not in sources:
            sources[source_name] = []
        sources[source_name].append(article)

    # 生成 Markdown
    date_str = datetime.now().strftime('%Y年%m月%d日')
    lines = [
        f"# 今日新闻 - {date_str}",
        "",
        f"总计: {len(articles)} 篇",
        "",
        "---",
        ""
    ]

    for source_name, source_articles in sources.items():
        lines.append(f"## {source_name}")
        lines.append("")
        for article in source_articles:
            title = article.get('title', '无标题')
            url = article.get('url', '')
            published_at = article.get('published_at', '')
            translated_title = article.get('translated_title')
            description = article.get('description', '') or article.get('content', '')[:200]

            # 格式化日期
            if published_at:
                try:
                    dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    date_str = dt.strftime('%m月%d日 %H:%M')
                except:
                    date_str = published_at[:10] if len(published_at) >= 10 else ''
            else:
                date_str = ''

            # 标题行
            if translated_title:
                lines.append(f"### {title}")
                lines.append(f"*{translated_title}*")
            else:
                lines.append(f"### {title}")

            if date_str:
                lines.append(f"> 📅 {date_str}")

            if url:
                lines.append(f"> [阅读原文]({url})")

            if description:
                lines.append(f"> {description}...")

            lines.append("")

        lines.append("---")
        lines.append("")

    lines.append(f"*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

    markdown_content = '\n'.join(lines)

    # 如果指定了输出路径，写入文件
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

    return markdown_content


def generate_daily_markdown(articles: List[Dict], date: datetime = None) -> str:
    """
    生成每日新闻 Markdown 文件（带时间戳，保留每次抓取记录）

    Args:
        articles: 文章列表
        date: 日期时间（默认为当前时间）

    Returns:
        输出文件路径
    """
    if date is None:
        date = datetime.now()

    # 生成文件名：news_YYYY-MM-DD_HH-MM.md
    date_str = date.strftime('%Y-%m-%d')
    time_str = date.strftime('%H-%M')
    filename = f"news_{date_str}_{time_str}.md"
    output_path = Config.DATA_DIR / filename

    # 生成内容
    content = generate_markdown(articles, str(output_path))

    return str(output_path)


def generate_latest_markdown(articles: List[Dict]) -> str:
    """
    生成最新新闻 Markdown 文件（latest.md）

    Args:
        articles: 文章列表

    Returns:
        输出文件路径
    """
    output_path = Config.DATA_DIR / "latest.md"
    content = generate_markdown(articles, str(output_path))
    return str(output_path)


def cleanup_old_markdown_files(days: int = 30) -> int:
    """
    清理旧的 Markdown 文件，保留最近 N 天

    Args:
        days: 保留天数，默认为 30 天

    Returns:
        删除的文件数量
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    deleted_count = 0

    # 匹配所有 news_YYYY-MM-DD_HH-MM.md 文件
    pattern = str(Config.DATA_DIR / "news_*.md")
    files = glob.glob(pattern)

    for file_path in files:
        try:
            # 从文件名提取日期时间
            filename = os.path.basename(file_path)
            # 格式: news_YYYY-MM-DD_HH-MM.md
            date_str = filename[5:-3]  # 去掉 "news_" 和 ".md"

            if len(date_str) == 15:  # YYYY-MM-DD_HH-MM
                file_date = datetime.strptime(date_str, '%Y-%m-%d_%H-%M')

                if file_date < cutoff_date:
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"Deleted old file: {filename}")
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")

    if deleted_count > 0:
        print(f"Cleaned up {deleted_count} old markdown files")
    else:
        print("No old markdown files to clean up")

    return deleted_count
