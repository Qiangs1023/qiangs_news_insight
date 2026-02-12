"""
配置管理模块
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量（指定项目根目录的 .env 文件，override=True 确保 .env 优先）
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / '.env', override=True)

class Config:
    """配置类"""

    # Notion配置
    NOTION_API_KEY = os.getenv('NOTION_API_KEY', 'virtual_notion_api_key')
    NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID', 'virtual_database_id')

    # Twitter API配置
    # Twitter API v2 使用 Bearer Token
    TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN', '')
    TWITTER_API_KEY = os.getenv('TWITTER_API_KEY', '')  # 兼容旧配置
    TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET', '')
    TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN', '')
    TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET', '')

    # YouTube API配置
    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')

    # 翻译API配置
    # 翻译器类型: deepseek, openai, google, deepl
    TRANSLATOR_TYPE = os.getenv('TRANSLATOR_TYPE', 'deepseek')

    # DeepSeek配置
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
    DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
    DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1/chat/completions')

    # OpenAI配置
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1/chat/completions')

    # DeepL配置
    DEEPL_API_KEY = os.getenv('DEEPL_API_KEY', '')
    GOOGLE_TRANSLATE_API_KEY = os.getenv('GOOGLE_TRANSLATE_API_KEY', '')

    # 数据库配置
    DATABASE_PATH = os.getenv('DATABASE_PATH', './data/news.db')

    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', './logs/app.log')

    # 项目路径
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / 'data'
    LOGS_DIR = BASE_DIR / 'logs'
    FRONTEND_DIR = BASE_DIR / 'frontend'
    FRONTEND_DIST_DIR = FRONTEND_DIR / 'dist'

    # 订阅源类型
    SOURCE_TYPES = {
        'rss': 'RSS',
        'twitter': 'Twitter',
        'youtube': 'YouTube',
        'blog': 'Blog'
    }

    # 抓取配置
    REQUEST_TIMEOUT = 30  # 请求超时时间（秒）
    MAX_RETRIES = 3  # 最大重试次数
    RETRY_DELAY = 2  # 重试延迟（秒）

    # 翻译配置
    DEFAULT_TRANSLATE_LANGUAGE = 'zh'  # 默认翻译语言（中文）

    @classmethod
    def init_directories(cls):
        """初始化必要的目录"""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        cls.FRONTEND_DIST_DIR.mkdir(parents=True, exist_ok=True)


# 初始化目录
Config.init_directories()