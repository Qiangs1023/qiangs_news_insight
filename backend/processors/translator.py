"""
翻译模块 - 支持多种翻译模型
"""
import requests
from typing import Dict, Optional
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

    def _needs_translation(self, text: str) -> bool:
        """判断是否需要翻译"""
        # 简单判断：如果包含较多英文字母，则需要翻译
        import string
        english_chars = sum(1 for c in text if c in string.ascii_letters)
        total_chars = sum(1 for c in text if c.isalnum())
        if total_chars == 0:
            return False
        return english_chars / total_chars > 0.3


class DeepSeekTranslator(Translator):
    """DeepSeek翻译器"""

    def __init__(self, api_key: str = None, model: str = None, base_url: str = None):
        super().__init__(api_key, model)
        self.api_key = api_key or Config.DEEPSEEK_API_KEY
        self.model = model or Config.DEEPSEEK_MODEL or 'deepseek-chat'
        self.base_url = base_url or Config.DEEPSEEK_BASE_URL or 'https://api.deepseek.com/v1/chat/completions'

    def translate(self, text: str, target_lang: str = None) -> str:
        """
        使用DeepSeek API翻译

        Args:
            text: 待翻译的文本
            target_lang: 目标语言

        Returns:
            翻译后的文本
        """
        if not self.api_key:
            print("DeepSeek API key not configured, skipping...")
            return ''

        try:
            target_lang = target_lang or self.default_target_lang

            # 构建请求
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }

            # 翻译提示词
            system_prompt = f"你是一个专业的翻译助手。请将以下内容翻译成{target_lang}，只返回翻译结果，不要添加任何解释。"
            user_prompt = text

            payload = {
                'model': self.model,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                'temperature': 0.3,
                'max_tokens': 500
            }

            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            # 提取翻译结果
            translated_text = result['choices'][0]['message']['content'].strip()

            return translated_text

        except requests.exceptions.RequestException as e:
            print(f"DeepSeek API request error: {e}")
            return ''
        except (KeyError, IndexError) as e:
            print(f"DeepSeek API response parsing error: {e}")
            return ''
        except Exception as e:
            print(f"DeepSeek translation error: {e}")
            return ''


class OpenAITranslator(Translator):
    """OpenAI翻译器（兼容OpenAI API的其他模型）"""

    def __init__(self, api_key: str = None, model: str = None, base_url: str = None):
        super().__init__(api_key, model)
        self.api_key = api_key or Config.OPENAI_API_KEY
        self.model = model or Config.OPENAI_MODEL or 'gpt-3.5-turbo'
        self.base_url = base_url or Config.OPENAI_BASE_URL or 'https://api.openai.com/v1/chat/completions'

    def translate(self, text: str, target_lang: str = None) -> str:
        """
        使用OpenAI API翻译

        Args:
            text: 待翻译的文本
            target_lang: 目标语言

        Returns:
            翻译后的文本
        """
        if not self.api_key:
            print("OpenAI API key not configured, skipping...")
            return ''

        try:
            target_lang = target_lang or self.default_target_lang

            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }

            system_prompt = f"你是一个专业的翻译助手。请将以下内容翻译成{target_lang}，只返回翻译结果，不要添加任何解释。"

            payload = {
                'model': self.model,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': text}
                ],
                'temperature': 0.3,
                'max_tokens': 500
            }

            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            translated_text = result['choices'][0]['message']['content'].strip()

            return translated_text

        except requests.exceptions.RequestException as e:
            print(f"OpenAI API request error: {e}")
            return ''
        except (KeyError, IndexError) as e:
            print(f"OpenAI API response parsing error: {e}")
            return ''
        except Exception as e:
            print(f"OpenAI translation error: {e}")
            return ''


class GoogleTranslator(Translator):
    """Google翻译器（免费）"""

    def __init__(self, api_key: str = None, model: str = None):
        super().__init__(api_key, model)

    def translate(self, text: str, target_lang: str = None) -> str:
        """
        使用Google Translate API翻译

        Args:
            text: 待翻译的文本
            target_lang: 目标语言

        Returns:
            翻译后的文本
        """
        try:
            # 使用deep-translator库（免费）
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
        """
        使用DeepL API翻译

        Args:
            text: 待翻译的文本
            target_lang: 目标语言

        Returns:
            翻译后的文本
        """
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
        translated_title = translator.translate_article_title(article)
        if translated_title:
            article['translated_title'] = translated_title

    return articles