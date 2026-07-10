import re

from text_utils import clean_text

# 科技类高价值信号
TECH_HIGH_KEYWORDS = (
    'openai', 'anthropic', 'claude', 'gpt-', 'gpt ', 'gemini', 'google deepmind',
    'llama', 'mistral', 'deepseek', 'qwen', 'benchmark', 'sota', 'state-of-the-art',
    'open source', 'open-source', 'opensource', 'weights', 'hugging face', 'huggingface',
    'agent framework', 'multi-agent', 'reasoning model', 'multimodal', 'model release',
    'new model', 'foundation model', 'inference', 'fine-tune', 'fine tune',
    '大模型', '开源模型', 'agent', '具身智能', '机器人', 'benchmark',
)

# 商业类高价值信号
BIZ_HIGH_KEYWORDS = (
    'funding', 'raises', 'raised', 'ipo', 'valuation', 'acquisition', 'merger',
    'series a', 'series b', 'series c', 'investment', 'investors', 'unicorn',
    '融资', '并购', '上市', '估值', '财报', '收购',
)

# 低价值噪声
LOW_VALUE_KEYWORDS = (
    'show hn:', 'ask hn:', 'tell hn:', 'nobel', 'chicken coop', 'linux mint',
    'dino game', 'gorillas', 'career simulator', 'neverdeliver', 'fake online shop',
    'chrome extension', 'assignment helper', 'humanizer', 'plain-english guide',
    'moving a windows', 'pelican riding', 'banana battle',
)

COMPANY_KEYWORDS = (
    'openai', 'anthropic', 'google', 'gemini', 'meta', 'xai', 'microsoft',
    'nvidia', 'deepseek', 'mistral', '长鑫', '中芯', '半导体','AI','芯片'
)


def _text_blob(row: dict) -> str:
    return clean_text(
        f"{row.get('title', '')} {row.get('ai_summary', '')} {row.get('source', '')}",
        500,
    ).lower()


def is_low_value_row(row: dict) -> bool:
    text = _text_blob(row)
    if any(k in text for k in LOW_VALUE_KEYWORDS):
        # 若同时命中高价值 AI 关键词，保留
        if any(k in text for k in TECH_HIGH_KEYWORDS + BIZ_HIGH_KEYWORDS):
            return False
        return True
    if text.startswith('show hn:') or text.startswith('ask hn:'):
        if not any(k in text for k in TECH_HIGH_KEYWORDS):
            return True
    return False


def compute_relevance_score(row: dict) -> int:
    text = _text_blob(row)
    score = int(row.get('importance') or 2) * 10

    if any(k in text for k in TECH_HIGH_KEYWORDS):
        score += 35
    if any(k in text for k in BIZ_HIGH_KEYWORDS):
        score += 30
    if any(k in text for k in COMPANY_KEYWORDS):
        score += 15

    category = row.get('category', '科技')
    if category == '商业' and any(k in text for k in BIZ_HIGH_KEYWORDS):
        score += 20
    if category == '科技' and any(k in text for k in TECH_HIGH_KEYWORDS):
        score += 20

    if is_low_value_row(row):
        score -= 80

    if re.search(r'\b(gpt|claude|gemini|llama|deepseek)[-\s]?\d', text):
        score += 25

    return score


def should_skip_llm_classify(title: str, summary: str) -> bool:
    text = clean_text(f'{title} {summary}', 300).lower()
    if text.startswith('show hn:') or text.startswith('ask hn:'):
        return not any(k in text for k in TECH_HIGH_KEYWORDS + BIZ_HIGH_KEYWORDS)
    return any(k in text for k in LOW_VALUE_KEYWORDS) and not any(
        k in text for k in TECH_HIGH_KEYWORDS + BIZ_HIGH_KEYWORDS
    )


def junk_classification(title: str, summary: str) -> dict:
    return {
        'category': '科技',
        'summary': clean_text(summary or title, 50),
        'importance': 1,
        'tags': ['产品发布'],
    }
