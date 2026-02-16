"""
翻译模块 - 支持多种翻译模型和内容总结
"""
import requests
from typing import Dict, Optional, List
from abc import ABC, abstractmethod
from backend.config import Config


class Translator(ABC):
    """翻译器基类"""

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key
        self.model = model
        self.default_target_lang = Config.DEFAULT_TRANSLATE_LANGUAGE

    @abstractmethod
    def translate(self, text: str, target_lang: str = None) -> str:
        """
        翻译文本（抽象方法，子类必须实现）

        Args:
            text: 待翻译的文本
            target_lang: 目标语言

        Returns:
            翻译后的文本
        """
        pass

    def summarize_and_translate(self, text: str, target_lang: str = None) -> Dict[str, str]:
        """
        总结并翻译内容（子类可覆盖）

        Args:
            text: 待处理的文本
            target_lang: 目标语言

        Returns:
            {'summary': 总结内容, 'translated': 翻译内容}
        """
        # 默认实现：只翻译不总结
        translated = self.translate(text, target_lang)
        return {'summary': '', 'translated': translated}

    def translate_article_title(self, article: Dict, target_lang: str = None) -> str:
        """
        翻译文章标题

        Args:
            article: 文章字典
            target_lang: 目标语言

        Returns:
            翻译后的标题，失败返回原文
        """
        title = article.get('title', '')
        if not title:
            return ''

        # 检查是否需要翻译（简单判断：包含英文字母）
        if not self._needs_translation(title):
            return title

        translated = self.translate(title, target_lang)
        return translated if translated else title

    def process_article(self, article: Dict, target_lang: str = None) -> Dict:
        """
        处理文章：翻译标题，总结并翻译内容

        Args:
            article: 文章字典
            target_lang: 目标语言

        Returns:
            更新后的文章字典
        """
        # 翻译标题
        title = article.get('title', '')
        if title and self._needs_translation(title):
            translated_title = self.translate(title, target_lang)
            if translated_title:
                article['translated_title'] = translated_title

        # 总结并翻译内容
        content = article.get('content', '')
        if content and len(content) > 50:
            result = self.summarize_and_translate(content, target_lang)
            if result.get('summary'):
                article['summary'] = result['summary']
            if result.get('translated'):
                article['translated_content'] = result['translated']

        return article

    def _needs_translation(self, text: str) -> bool:
        """判断是否需要翻译"""
        import string
        english_chars = sum(1 for c in text if c in string.ascii_letters)
        total_chars = sum(1 for c in text if c.isalnum())
        if total_chars == 0:
            return False
        return english_chars / total_chars > 0.3


class DeepSeekTranslator(Translator):
    """DeepSeek翻译器 - 支持总结和翻译"""

    def __init__(self, api_key: str = None, model: str = None, base_url: str = None):
        super().__init__(api_key, model)
        self.api_key = api_key or Config.DEEPSEEK_API_KEY
        self.model = model or Config.DEEPSEEK_MODEL or 'deepseek-chat'
        self.base_url = base_url or Config.DEEPSEEK_BASE_URL or 'https://api.deepseek.com/v1/chat/completions'

    def _call_api(self, system_prompt: str, user_prompt: str, max_tokens: int = 500) -> str:
        """调用 API"""
        if not self.api_key:
            return ''

        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }

            payload = {
                'model': self.model,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                'temperature': 0.3,
                'max_tokens': max_tokens
            }

            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content'].strip()

        except Exception as e:
            print(f"DeepSeek API error: {e}")
            return ''

    def translate(self, text: str, target_lang: str = None) -> str:
        """翻译文本"""
        target_lang = target_lang or self.default_target_lang
        system_prompt = f"你是一个专业的翻译助手。请将以下内容翻译成{target_lang}，只返回翻译结果，不要添加任何解释。"
        return self._call_api(system_prompt, text)

    def summarize_and_translate(self, text: str, target_lang: str = None) -> Dict[str, str]:
        """
        总结并翻译 Twitter 帖子内容
        
        Args:
            text: 帖子内容
            target_lang: 目标语言
            
        Returns:
            {'summary': 中文总结, 'translated': 中文翻译}
        """
        target_lang = target_lang or self.default_target_lang
        
        # 一步完成总结和翻译
        system_prompt = """你是一个专业的内容编辑。请对以下社交媒体帖子进行处理：
1. 如果内容是英文，请先用1-2句话总结核心内容（中文）
2. 然后提供完整的中文翻译

请严格按照以下JSON格式返回，不要添加其他内容：
{"summary": "一句话总结", "translated": "完整翻译内容"}"""

        result = self._call_api(system_prompt, text, max_tokens=800)
        
        # 解析 JSON 结果
        import json
        try:
            # 尝试提取 JSON
            if '{' in result and '}' in result:
                start = result.index('{')
                end = result.rindex('}') + 1
                json_str = result[start:end]
                data = json.loads(json_str)
                return {
                    'summary': data.get('summary', ''),
                    'translated': data.get('translated', '')
                }
        except Exception as e:
            print(f"JSON parsing error: {e}")
        
        # 如果解析失败，尝试直接作为翻译结果
        if result:
            return {'summary': '', 'translated': result}
        return {'summary': '', 'translated': ''}


class OpenAITranslator(Translator):
    """OpenAI翻译器 - 支持总结和翻译"""

    def __init__(self, api_key: str = None, model: str = None, base_url: str = None):
        super().__init__(api_key, model)
        self.api_key = api_key or Config.OPENAI_API_KEY
        self.model = model or Config.OPENAI_MODEL or 'gpt-3.5-turbo'
        self.base_url = base_url or Config.OPENAI_BASE_URL or 'https://api.openai.com/v1/chat/completions'

    def _call_api(self, system_prompt: str, user_prompt: str, max_tokens: int = 500) -> str:
        """调用 API"""
        if not self.api_key:
            return ''

        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }

            payload = {
                'model': self.model,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                'temperature': 0.3,
                'max_tokens': max_tokens
            }

            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content'].strip()

        except Exception as e:
            print(f"OpenAI API error: {e}")
            return ''

    def translate(self, text: str, target_lang: str = None) -> str:
        """翻译文本"""
        target_lang = target_lang or self.default_target_lang
        system_prompt = f"你是一个专业的翻译助手。请将以下内容翻译成{target_lang}，只返回翻译结果，不要添加任何解释。"
        return self._call_api(system_prompt, text)

    def summarize_and_translate(self, text: str, target_lang: str = None) -> Dict[str, str]:
        """总结并翻译"""
        target_lang = target_lang or self.default_target_lang
        
        system_prompt = f"""你是一个专业的内容编辑。请对以下社交媒体帖子进行处理：
1. 用1-2句话总结核心内容（{target_lang}）
2. 提供完整的{target_lang}翻译

请严格按照以下JSON格式返回：
{{"summary": "一句话总结", "translated": "完整翻译内容"}}"""

        result = self._call_api(system_prompt, text, max_tokens=800)
        
        import json
        try:
            if '{' in result and '}' in result:
                start = result.index('{')
                end = result.rindex('}') + 1
                json_str = result[start:end]
                data = json.loads(json_str)
                return {
                    'summary': data.get('summary', ''),
                    'translated': data.get('translated', '')
                }
        except Exception as e:
            print(f"JSON parsing error: {e}")
        
        return {'summary': '', 'translated': result if result else ''}


class GoogleTranslator(Translator):
    """Google翻译器（免费）"""

    def __init__(self, api_key: str = None, model: str = None):
        super().__init__(api_key, model)

    def translate(self, text: str, target_lang: str = None) -> str:
        """使用Google Translate API翻译"""
        try:
            from deep_translator import GoogleTranslator as GT

            translator = GT(source='auto', target=target_lang or self.default_target_lang)
            result = translator.translate(text)

            return result

        except ImportError:
            print("deep-translator not installed, skipping translation...")
            return ''
        except Exception as e:
            print(f"Google translation error: {e}")
            return ''


class DeepLTranslator(Translator):
    """DeepL翻译器（需要API密钥）"""

    def __init__(self, api_key: str = None, model: str = None):
        super().__init__(api_key, model)
        self.api_key = api_key or Config.DEEPL_API_KEY

    def translate(self, text: str, target_lang: str = None) -> str:
        """使用DeepL API翻译"""
        if not self.api_key:
            print("DeepL API key not configured, skipping...")
            return ''

        try:
            import deepl

            translator = deepl.Translator(self.api_key)
            result = translator.translate_text(
                text,
                target_lang=target_lang or self.default_target_lang.upper()
            )

            return result.text

        except ImportError:
            print("deepl not installed, skipping translation...")
            return ''
        except Exception as e:
            print(f"DeepL translation error: {e}")
            return ''


class TranslatorFactory:
    """翻译器工厂类"""

    # 支持的翻译器类型
    TRANSLATORS = {
        'deepseek': DeepSeekTranslator,
        'openai': OpenAITranslator,
        'google': GoogleTranslator,
        'deepl': DeepLTranslator,
    }

    @classmethod
    def create(cls, translator_type: str = None, **kwargs) -> Optional[Translator]:
        """
        创建翻译器实例

        Args:
            translator_type: 翻译器类型（deepseek/openai/google/deepl）
            **kwargs: 传递给翻译器的参数（api_key, model, base_url等）

        Returns:
            翻译器实例，失败返回None
        """
        # 如果未指定类型，使用配置中的类型
        if translator_type is None:
            translator_type = Config.TRANSLATOR_TYPE

        # 获取翻译器类
        translator_class = cls.TRANSLATORS.get(translator_type.lower())

        if translator_class is None:
            print(f"Unknown translator type: {translator_type}")
            return None

        # 创建实例
        try:
            return translator_class(**kwargs)
        except Exception as e:
            print(f"Error creating translator: {e}")
            return None

    @classmethod
    def get_supported_translators(cls) -> list[str]:
        """获取支持的翻译器类型列表"""
        return list(cls.TRANSLATORS.keys())


def create_translator() -> Optional[Translator]:
    """
    创建翻译器（便捷函数）

    根据配置自动选择翻译器

    Returns:
        翻译器实例
    """
    return TranslatorFactory.create()


def translate_articles(articles: list[Dict], translator: Translator = None) -> list[Dict]:
    """
    翻译文章列表

    Args:
        articles: 文章列表
        translator: 翻译器实例

    Returns:
        更新后的文章列表
    """
    if translator is None:
        translator = create_translator()

    if translator is None:
        print("No translator available, skipping translation...")
        return articles

    for article in articles:
        translator.process_article(article)

    return articles