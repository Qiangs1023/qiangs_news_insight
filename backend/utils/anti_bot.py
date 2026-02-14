"""
反反爬虫工具模块
"""
import random
import time
import requests
from urllib.robotparser import RobotFileParser
from typing import Optional
from datetime import datetime


# 伪装请求头列表
DEFAULT_HEADERS_LIST = [
    {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    },
    {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive',
    },
    {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
    },
]


class AntiBotMixin:
    """反反爬虫混入类"""

    # 默认设置（可在子类中覆盖）
    MIN_DELAY = 1.0  # 最小延迟（秒）
    MAX_DELAY = 3.0  # 最大延迟（秒）
    ENABLE_ROBOTS_CHECK = True  # 是否检查 robots.txt

    def __init__(self):
        self._last_request_time: Optional[float] = None
        self._robots_cache: dict = {}  # robots.txt 缓存

    def get_random_headers(self) -> dict:
        """获取随机请求头"""
        return DEFAULT_HEADERS_LIST[random.randint(0, len(DEFAULT_HEADERS_LIST) - 1)].copy()

    def get_random_delay(self) -> float:
        """获取随机延迟时间"""
        return random.uniform(self.MIN_DELAY, self.MAX_DELAY)

    def wait_before_request(self):
        """请求前等待（控制频率）"""
        if self._last_request_time is not None:
            elapsed = time.time() - self._last_request_time
            delay = self.get_random_delay()
            if elapsed < delay:
                time.sleep(delay - elapsed)
        self._last_request_time = time.time()

    def can_fetch(self, url: str) -> bool:
        """
        检查是否允许抓取（检查 robots.txt）

        Args:
            url: 要检查的URL

        Returns:
            是否允许抓取
        """
        if not self.ENABLE_ROBOTS_CHECK:
            return True

        try:
            from urllib.parse import urlparse
            base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"

            # 检查缓存
            if base_url in self._robots_cache:
                rp = self._robots_cache[base_url]
            else:
                rp = RobotFileParser()
                robots_url = f"{base_url}/robots.txt"
                rp.set_url(robots_url)
                try:
                    rp.read()
                    self._robots_cache[base_url] = rp
                except:
                    # 无法读取 robots.txt，默认为允许
                    return True

            return rp.can_fetch("*", url)

        except Exception:
            return True  # 出错时默认为允许

    def safe_request(self, url: str, session: requests.Session = None,
                     timeout: int = 10, max_retries: int = 3) -> Optional[requests.Response]:
        """
        安全的 HTTP 请求（带重试和延迟）

        Args:
            url: 请求 URL
            session: requests Session（可选）
            timeout: 超时时间
            max_retries: 最大重试次数

        Returns:
            Response 对象，失败返回 None
        """
        if not self.can_fetch(url):
            print(f"Robots.txt disallows fetching: {url}")
            return None

        # 使用传入的 session 或创建新 session
        if session is None:
            session = requests.Session()

        for attempt in range(max_retries):
            try:
                self.wait_before_request()

                headers = self.get_random_headers()
                response = session.get(url, headers=headers, timeout=timeout)

                # 检查状态码
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Rate limited
                    wait_time = (attempt + 1) * 5  # 递增等待
                    print(f"Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"HTTP {response.status_code}: {url}")

            except requests.exceptions.Timeout:
                print(f"Timeout (attempt {attempt + 1}/{max_retries}): {url}")
            except requests.exceptions.RequestException as e:
                print(f"Request error (attempt {attempt + 1}/{max_retries}): {e}")

            if attempt < max_retries - 1:
                time.sleep(random.uniform(2, 5))

        print(f"Failed after {max_retries} attempts: {url}")
        return None
