"""
Notion集成模块
"""
from typing import List, Dict, Optional
from datetime import datetime
from notion_client import Client
from backend.config import Config


class NotionIntegration:
    """Notion集成类"""

    def __init__(self):
        self.client = Client(auth=Config.NOTION_API_KEY)
        self.database_id = Config.NOTION_DATABASE_ID

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
            response = self.client.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "Status",
                    "checkbox": {
                        "equals": True
                    }
                }
            )

            sources = []
            for result in response.get('results', []):
                props = result['properties']

                # 提取订阅源信息
                notion_id = result['id']

                # Name (Title)
                name = ''
                if props.get('Name', {}).get('title'):
                    name = props['Name']['title'][0]['text']['content']

                # Feed URL
                feed_url = props.get('Feed URL', {}).get('url', '')

                # URL (目标网站)
                url = props.get('URL', {}).get('url', '')

                # # Limit (Number)
                limit = 0
                if props.get('# Limit', {}).get('number') is not None:
                    limit = int(props['# Limit']['number'])

                # Deep Read (Checkbox)
                deep_read = props.get('Deep Read', {}).get('checkbox', False)

                # Translate (Checkbox)
                translate = props.get('Translate', {}).get('checkbox', False)

                # Category (Multi-select)
                categories = []
                for tag in props.get('Category', {}).get('multi_select', []):
                    categories.append(tag['name'])

                # Description (Text)
                description = ''
                if props.get('Description', {}).get('rich_text'):
                    description = props['Description']['rich_text'][0]['text']['content']

                # Date
                date = None
                if props.get('Date', {}).get('date'):
                    date_str = props['Date']['date'].get('start')
                    if date_str:
                        from datetime import datetime
                        try:
                            date = datetime.fromisoformat(date_str)
                        except:
                            pass

                # 根据Feed URL或URL判断类型
                source_type = 'rss'
                if 'youtube.com' in feed_url or 'youtube.com' in url:
                    source_type = 'youtube'
                elif feed_url and ('feed' in feed_url.lower() or 'rss' in feed_url.lower()):
                    source_type = 'rss'
                elif url and ('youtube.com' in url):
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

            self.client.pages.update(
                page_id=notion_id,
                properties={
                    "Date": {
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