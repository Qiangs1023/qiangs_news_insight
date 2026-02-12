"""
日志工具模块
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from backend.config import Config


class Logger:
    """日志管理器"""

    def __init__(self, name: str = 'NewsAggregator'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, Config.LOG_LEVEL))

        # 清除现有处理器
        self.logger.handlers.clear()

        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # 文件处理器
        log_file = Path(Config.LOG_FILE)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def debug(self, message):
        """记录调试信息"""
        self.logger.debug(message)

    def info(self, message):
        """记录信息"""
        self.logger.info(message)

    def warning(self, message):
        """记录警告"""
        self.logger.warning(message)

    def error(self, message):
        """记录错误"""
        self.logger.error(message)

    def critical(self, message):
        """记录严重错误"""
        self.logger.critical(message)


# 全局日志实例
logger = Logger()


def get_logger(name: str = 'NewsAggregator') -> Logger:
    """获取日志实例"""
    return Logger(name)