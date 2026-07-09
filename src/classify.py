import json
import os
import re

from anthropic import Anthropic
import requests

from models import Article

VALID_TAGS = [
    '融资', '并购', '政策', '大模型', '具身智能', '机器人', '可穿戴设备', '芯片', '产品发布', '论文/研究'
]


PROMPT_TEMPLATE = '''你是一名AI/科技行业分析师。请阅读以下资讯标题和摘要，输出严格的JSON（不要任何多余文字）：
{
  "category": "商业" 或 "科技",
  "summary": "不超过50字的中文摘要",
  "importance": 1-5的整数（5=非常重要，如重大融资/技术突破；1=一般资讯）, 
  "tags": ["标签1", "标签2"]
}

分类标准：
- 商业：融资、并购、财报、上市、政策监管、市场份额变化——可用于投资判断
- 科技：技术突破、新模型/新产品发布、论文成果、demo展示——侧重新技术进展
- 如果两者都相关，请按“更主要的信息价值”二选一

标签请仅从以下列表中选择1-3个：[{tags}]

标题：{title}
摘要：{summary}
来源：{source}
'''


class Classifier:
    def __init__(self) -> None:
        provider = os.getenv('LLM_PROVIDER', 'auto').strip().lower()
        self.provider = self._resolve_provider(provider)

        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY', '').strip()
        self.anthropic_model = os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-5').strip()

        self.openai_key = os.getenv('OPENAI_API_KEY', '').strip()
        self.openai_model = os.getenv('OPENAI_MODEL', 'qwen-plus').strip()
        self.openai_base_url = os.getenv(
            'OPENAI_BASE_URL',
            'https://dashscope.aliyuncs.com/compatible-mode/v1',
        ).strip().rstrip('/')

        self.client = Anthropic(api_key=self.anthropic_key) if self.provider == 'anthropic' and self.anthropic_key else None

    def _resolve_provider(self, provider: str) -> str:
        if provider in ('anthropic', 'openai_compatible'):
            return provider
        if os.getenv('OPENAI_API_KEY', '').strip():
            return 'openai_compatible'
        if os.getenv('ANTHROPIC_API_KEY', '').strip():
            return 'anthropic'
        return 'fallback'

    def _fallback(self, article: Article) -> dict:
        summary = article.summary.replace('\n', ' ').strip()[:50] or article.title[:50]
        return {
            'category': '科技',
            'summary': summary,
            'importance': 2,
            'tags': ['产品发布'],
        }

    def classify(self, article: Article) -> dict:
        if self.provider == 'anthropic':
            return self._classify_with_anthropic(article)
        if self.provider == 'openai_compatible':
            return self._classify_with_openai_compatible(article)
        return self._fallback(article)

    def _classify_with_anthropic(self, article: Article) -> dict:
        if not self.client:
            return self._fallback(article)
        prompt = PROMPT_TEMPLATE.format(
            tags='，'.join(VALID_TAGS),
            title=article.title,
            summary=article.summary[:1000],
            source=article.source,
        )
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                temperature=0,
                messages=[{'role': 'user', 'content': prompt}],
            )
            text = ''.join(block.text for block in response.content if getattr(block, 'text', None)).strip()
            match = re.search(r'\{[\s\S]*\}', text)
            parsed = json.loads(match.group(0) if match else text)
            category = parsed.get('category', '科技')
            if category not in ('商业', '科技'):
                category = '科技'
            importance = int(parsed.get('importance', 2))
            importance = max(1, min(5, importance))
            tags = [t for t in parsed.get('tags', []) if t in VALID_TAGS][:3]
            if not tags:
                tags = ['产品发布']
            summary = str(parsed.get('summary', '')).strip()[:50] or article.title[:50]
            return {
                'category': category,
                'summary': summary,
                'importance': importance,
                'tags': tags,
            }
        except Exception:
            return self._fallback(article)

    def _classify_with_openai_compatible(self, article: Article) -> dict:
        if not self.openai_key:
            return self._fallback(article)
        prompt = PROMPT_TEMPLATE.format(
            tags='，'.join(VALID_TAGS),
            title=article.title,
            summary=article.summary[:1000],
            source=article.source,
        )
        try:
            resp = requests.post(
                f'{self.openai_base_url}/chat/completions',
                headers={
                    'Authorization': f'Bearer {self.openai_key}',
                    'Content-Type': 'application/json',
                },
                json={
                    'model': self.openai_model,
                    'temperature': 0,
                    'messages': [{'role': 'user', 'content': prompt}],
                },
                timeout=45,
            )
            resp.raise_for_status()
            payload = resp.json()
            text = payload['choices'][0]['message']['content'].strip()
            match = re.search(r'\{[\s\S]*\}', text)
            parsed = json.loads(match.group(0) if match else text)
            category = parsed.get('category', '科技')
            if category not in ('商业', '科技'):
                category = '科技'
            importance = int(parsed.get('importance', 2))
            importance = max(1, min(5, importance))
            tags = [t for t in parsed.get('tags', []) if t in VALID_TAGS][:3]
            if not tags:
                tags = ['产品发布']
            summary = str(parsed.get('summary', '')).strip()[:50] or article.title[:50]
            return {
                'category': category,
                'summary': summary,
                'importance': importance,
                'tags': tags,
            }
        except Exception:
            return self._fallback(article)

