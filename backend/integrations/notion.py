"""
Notion集成模块
"""
from typing import List, Dict, Optional
from datetime import datetime
from notion_client import Client
from backend.config import Config


def normalize_id(id_str: str) -> str:
    """规范化 UUID ID（移除所有短横线）"""
    return id_str.replace('-', '')


def get_prop_value(props: Dict, prop_name: str, prop_type: str, default=None):
    """安全获取属性值"""
    try:
        prop_data = props.get(prop_name, {})
        if not prop_data:
            return default

        if prop_type == 'title':
            title_list = prop_data.get('title', [])
            if title_list:
                return title_list[0].get('text', {}).get('content', default)
        elif prop_type == 'url':
            return prop_data.get('url', default) or default
        elif prop_type == 'number':
            val = prop_data.get('number')
            return int(val) if val is not None else default
        elif prop_type == 'checkbox':
            return prop_data.get('checkbox', False)
        elif prop_type == 'multi_select':
            return [tag['name'] for tag in prop_data.get('multi_select', [])]
        elif prop_type == 'rich_text':
            rich_list = prop_data.get('rich_text', [])
            if rich_list:
                return rich_list[0].get('text', {}).get('content', default)
            return default
        elif prop_type == 'date':
            date_obj = prop_data.get('date')
            if date_obj:
                date_str = date_obj.get('start')
                if date_str:
                    try:
                        return datetime.fromisoformat(date_str)
                    except:
                        pass
            return default
    except Exception:
        pass
    return default


class NotionIntegration:
    """Notion集成类"""

    def __init__(self):
        self.client = Client(auth=Config.NOTION_API_KEY)
        self.database_id = normalize_id(Config.NOTION_DATABASE_ID)

    def get_active_sources(self) -> List[Dict]:
        """
        从Notion数据库获取所有启用的订阅源

        Returns:
            订阅源列表，每个元素包含：
            - notion_id: Notion页面ID
            - name: 订阅源名称
            - feed_url: Feed URL
            - url: 目标网站URL
            - limit: 抓取条数限制
            - deep_read: 是否深度阅读
            - translate: 是否翻译
            - category: 分类标签
            - description: 描述
        """
        try:
            # 使用 search API 查询数据库中的项目
            response = self.client.search(
                query="",
                filter={
                    "value": "page",
                    "property": "object"
                },
                page_size=100
            )

            # 过滤出属于指定数据库的页面
            results = []
            for item in response.get('results', []):
                parent_db_id = item.get('parent', {}).get('database_id', '')
                if normalize_id(parent_db_id) == self.database_id:
                    # 检查 Status 是否为 True
                    props = item.get('properties', {})
                    status = props.get('Status', {}).get('checkbox', False)
                    if status:
                        results.append(item)

            sources = []
            for result in results:
                props = result.get('properties', {})

                # 提取订阅源信息
                notion_id = result['id']

                # 使用安全的属性获取方法
                name = get_prop_value(props, 'Name', 'title', '')
                feed_url = get_prop_value(props, 'Feed URL', 'url', '')
                url = get_prop_value(props, 'URL', 'url', '')
                limit = get_prop_value(props, 'Limit', 'number', 0)
                deep_read = get_prop_value(props, 'Deep Read', 'checkbox', False)
                translate = get_prop_value(props, 'Translate', 'checkbox', False)
                categories = get_prop_value(props, 'Category', 'multi_select', [])
                description = get_prop_value(props, 'Description', 'rich_text', '')
                date = get_prop_value(props, '日期', 'date', None)

                # 根据Feed URL或URL判断类型
                source_type = 'rss'
                if 'youtube.com' in (feed_url or '') or 'youtube.com' in (url or ''):
                    source_type = 'youtube'
                elif (feed_url or '') and ('feed' in feed_url.lower() or 'rss' in feed_url.lower()):
                    source_type = 'rss'
                elif (url or '') and ('youtube.com' in url):
                    source_type = 'youtube'
                else:
                    source_type = 'blog'

                sources.append({
                    'notion_id': notion_id,
                    'name': name,
                    'feed_url': feed_url,
                    'url': url,
                    'limit': limit,
                    'deep_read': deep_read,
                    'translate': translate,
                    'category': categories,
                    'description': description,
                    'date': date,
                    'type': source_type
                })

            print(f"Found {len(sources)} active sources from Notion")
            return sources

        except Exception as e:
            print(f"Error fetching sources from Notion: {e}")
            return []

    def update_last_fetched(self, notion_id: str, fetched_at: datetime = None):
        """
        更新订阅源的最后抓取时间

        Args:
            notion_id: Notion页面ID
            fetched_at: 抓取时间（默认为当前时间）
        """
        try:
            if fetched_at is None:
                fetched_at = datetime.now()

            # 尝试使用 "日期" 字段（中文），如果不存在则跳过
            self.client.pages.update(
                page_id=notion_id,
                properties={
                    "日期": {
                        "date": {
                            "start": fetched_at.isoformat()
                        }
                    }
                }
            )
            print(f"Updated last fetched time for {notion_id}")
        except Exception as e:
            print(f"Error updating last fetched time: {e}")

    def test_connection(self) -> bool:
        """测试Notion连接"""
        try:
            self.client.users.me()
            return True
        except Exception as e:
            print(f"Notion connection test failed: {e}")
            return False


# 便捷函数
def get_notion_sources() -> List[Dict]:
    """获取Notion中的订阅源列表"""
    integration = NotionIntegration()
    return integration.get_active_sources()


def update_source_fetch_time(notion_id: str):
    """更新订阅源抓取时间"""
    integration = NotionIntegration()
    integration.update_last_fetched(notion_id)