import json
import os
import re

from llm_client import LLMClient
from models import Article
from relevance import junk_classification, should_skip_llm_classify
from text_utils import clean_text

VALID_TAGS = [
    '融资', '并购', '政策', '大模型', '具身智能', '机器人', '可穿戴设备', '芯片', '产品发布', '论文/研究', 'IPO/上市'
]


PROMPT_TEMPLATE = '''你是一名AI/科技行业分析师。请阅读以下资讯标题和摘要，输出严格的JSON（不要任何多余文字）：
{{
  "category": "商业" 或 "科技",
  "summary": "不超过50字的中文摘要",
  "importance": 1-5的整数（5=非常重要；1=一般资讯）,
  "tags": ["标签1", "标签2"]
}}

分类标准：
- 商业：融资、并购、IPO/上市筹备、估值变动、财报、政策监管
- 科技（高优先级，importance 4-5）：
  - OpenAI/Anthropic/Google Gemini 新模型发布、版本更新
  - benchmark/SOTA 跑分、评测结果
  - Agent 新框架、多智能体系统、推理能力升级
  - 重要开源模型/权重发布（HuggingFace 等）
  - 具身智能/机器人关键技术进展
- 低价值（importance 1-2）：Show HN 小工具、无关社会新闻、游戏/生活类、营销稿

标签请仅从以下列表中选择1-3个：[{tags}]

标题：{title}
摘要：{summary}
来源：{source}
'''


def _build_prompt(article: Article) -> str:
    return PROMPT_TEMPLATE.format(
        tags='，'.join(VALID_TAGS),
        title=clean_text(article.title, 200),
        summary=clean_text(article.summary, 1000),
        source=article.source,
    )


def _parse_classification(text: str, article: Article) -> dict:
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
    summary = clean_text(str(parsed.get('summary', '')).strip(), 50) or clean_text(article.title, 50)
    return {
        'category': category,
        'summary': summary,
        'importance': importance,
        'tags': tags,
    }


class Classifier:
    def __init__(self) -> None:
        self.llm = LLMClient()

    def _fallback(self, article: Article) -> dict:
        title = clean_text(article.title, 200)
        summary = clean_text(article.summary, 50) or title[:50]
        text = f'{title} {summary}'.lower()
        business_keywords = (
            'funding', 'ipo', 'acquisition', 'merger', 'valuation', 'raises', 'series ',
            '融资', '并购', '上市', '估值', '财报',
        )
        tech_high = (
            'openai', 'anthropic', 'claude', 'gpt', 'gemini', 'benchmark', 'agent',
            'open source', 'model', 'llama', 'deepseek',
        )
        if any(k in text for k in business_keywords):
            category, importance, tags = '商业', 4, ['融资']
        elif any(k in text for k in tech_high):
            category, importance, tags = '科技', 4, ['大模型']
        else:
            category, importance, tags = '科技', 2, ['产品发布']
        return {
            'category': category,
            'summary': summary,
            'importance': importance,
            'tags': tags,
        }

    def classify(self, article: Article) -> dict:
        if should_skip_llm_classify(article.title, article.summary):
            return junk_classification(article.title, article.summary)

        if not self.llm.available:
            return self._fallback(article)

        prompt = _build_prompt(article)
        try:
            text = self.llm.chat(prompt, max_tokens=300)
            if not text:
                return self._fallback(article)
            return _parse_classification(text, article)
        except Exception:
            return self._fallback(article)
