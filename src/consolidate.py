import json
import logging
import os
import re

from llm_client import LLMClient
from relevance import compute_relevance_score, is_low_value_row
from text_utils import clean_text

POLISH_PROMPT = '''你是AI行业日报编辑。下面条目已经人工筛选完成，请只做中文润色，不要删除、不要合并、不要新增条目。

要求：
1. 保持条目数量不变，顺序不变
2. 标题和摘要都改为自然中文
3. 每条格式：★★★ 中文标题 - 50字内中文摘要 - 来源
4. 严格输出以下结构：

【商业】共{N_BIZ}条
（商业条目，每行一条）

【科技】共{N_TECH}条
（科技条目，每行一条）

输入条目（JSON）：
{items_json}
'''


def _stars(importance: int) -> str:
    return '★' * max(1, min(5, importance))


def _format_item(item: dict) -> str:
    summary = clean_text(item.get('ai_summary') or item.get('title', ''), 50)
    title = clean_text(item.get('title', ''), 120)
    return f"{_stars(item.get('importance') or 3)} {title} - {summary} - {item.get('source', '')}"


def _select_by_relevance(rows: list[dict], max_biz: int, max_tech: int) -> tuple[list[dict], list[dict]]:
    candidates = [r for r in rows if not is_low_value_row(r)]
    if not candidates:
        candidates = rows

    scored = [(compute_relevance_score(r), r) for r in candidates]
    scored.sort(key=lambda x: x[0], reverse=True)

    biz: list[dict] = []
    tech: list[dict] = []
    for _, row in scored:
        if row.get('category') == '商业' and len(biz) < max_biz:
            biz.append(row)
        elif row.get('category') == '科技' and len(tech) < max_tech:
            tech.append(row)
        if len(biz) >= max_biz and len(tech) >= max_tech:
            break

    # 商业不足时，从高分条目中补充含资本信号的内容
    if len(biz) < max_biz:
        for _, row in scored:
            if row in biz or row in tech:
                continue
            text = f"{row.get('title', '')} {row.get('ai_summary', '')}".lower()
            if any(k in text for k in ('funding', 'ipo', 'valuation', '融资', '上市', '并购', 'raises')):
                row = dict(row)
                row['category'] = '商业'
                biz.append(row)
            if len(biz) >= max_biz:
                break

    # 科技不足时，从高分非商业条目补充
    if len(tech) < max_tech:
        for _, row in scored:
            if row in biz or row in tech:
                continue
            tech.append(row)
            if len(tech) >= max_tech:
                break

    return biz, tech


def _build_digest_text(biz: list[dict], tech: list[dict]) -> str:
    lines = [f'【商业】共{len(biz)}条']
    if biz:
        lines.extend(_format_item(item) for item in biz)
    else:
        lines.append('今日暂无重要商业资讯。')

    lines.append('')
    lines.append(f'【科技】共{len(tech)}条')
    if tech:
        lines.extend(_format_item(item) for item in tech)
    else:
        lines.append('今日暂无重要科技资讯。')

    return '\n'.join(lines).strip()


def _count_section_items(text: str, section: str) -> int:
    match = re.search(rf'【{section}】共(\d+)条', text)
    return int(match.group(1)) if match else 0


def consolidate_digest(rows: list[dict]) -> tuple[str, int, int]:
    max_biz = int(os.getenv('DIGEST_MAX_BUSINESS', '5'))
    max_tech = int(os.getenv('DIGEST_MAX_TECH', '8'))

    biz, tech = _select_by_relevance(rows, max_biz, max_tech)
    base_text = _build_digest_text(biz, tech)

    client = LLMClient()
    selected = [{'category': '商业', **item} for item in biz] + [{'category': '科技', **item} for item in tech]
    if not client.available or not selected:
        return base_text, len(biz), len(tech)

    enable_polish = os.getenv('LLM_ENABLE_POLISH', 'true').strip().lower() in ('1', 'true', 'yes')
    if not enable_polish:
        logging.info('LLM polish disabled (LLM_ENABLE_POLISH=false), using rule-based digest')
        return base_text, len(biz), len(tech)

    prompt = POLISH_PROMPT.format(
        N_BIZ=len(biz),
        N_TECH=len(tech),
        items_json=json.dumps(
            [
                {
                    'category': item.get('category'),
                    'title': clean_text(item.get('title', ''), 160),
                    'summary': clean_text(item.get('ai_summary') or item.get('title', ''), 120),
                    'importance': item.get('importance', 3),
                    'source': item.get('source', ''),
                }
                for item in selected
            ],
            ensure_ascii=False,
            indent=2,
        ),
    )
    try:
        logging.info('Polishing digest in Chinese (%s biz + %s tech)...', len(biz), len(tech))
        text = client.chat(prompt, max_tokens=5000, purpose='polish')
        if text and '【商业】' in text and '【科技】' in text:
            return (
                text.strip(),
                _count_section_items(text, '商业'),
                _count_section_items(text, '科技'),
            )
    except Exception as exc:
        logging.warning('LLM polish failed, using rule-based digest: %s', exc)

    return base_text, len(biz), len(tech)
