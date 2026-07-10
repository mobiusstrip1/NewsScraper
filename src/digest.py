from collections import defaultdict
from datetime import datetime
from pathlib import Path

from text_utils import clean_text


def _stars(importance: int) -> str:
    return '★' * max(1, min(5, importance))


def build_raw_digest_text(rows: list[dict]) -> str:
    """Full list for local archive/debug only (not pushed)."""
    groups = defaultdict(list)
    for row in rows:
        if row.get('importance', 0) >= 2:
            groups[row.get('category', '科技')].append(row)

    for key in groups:
        groups[key].sort(key=lambda x: x.get('importance', 0), reverse=True)

    lines = []
    biz = groups.get('商业', [])
    tech = groups.get('科技', [])

    lines.append(f'【商业】共{len(biz)}条')
    for item in biz:
        summary = clean_text(item.get('ai_summary') or item.get('title', ''), 80)
        title = clean_text(item.get('title', ''), 160)
        lines.append(f"{_stars(item['importance'])} {title}")
        lines.append(f"   {summary} | {item['source']}")
    lines.append('')

    lines.append(f'【科技】共{len(tech)}条')
    for item in tech:
        summary = clean_text(item.get('ai_summary') or item.get('title', ''), 80)
        title = clean_text(item.get('title', ''), 160)
        lines.append(f"{_stars(item['importance'])} {title}")
        lines.append(f"   {summary} | {item['source']}")

    text = '\n'.join(lines).strip()
    if not text:
        return '今日暂无 importance>=2 的资讯。'
    return text


def write_digest_file(text: str, date: datetime | None = None, *, suffix: str = '') -> Path:
    date = date or datetime.now()
    name = f'{date:%Y-%m-%d}{suffix}.md'
    out = Path('digest') / name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding='utf-8')
    return out
