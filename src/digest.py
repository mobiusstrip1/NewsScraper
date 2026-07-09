from collections import defaultdict
from datetime import datetime
from pathlib import Path


def _stars(importance: int) -> str:
    return '?' * max(1, min(5, importance))


def build_digest_text(rows: list[dict]) -> str:
    groups = defaultdict(list)
    for row in rows:
        if row.get('importance', 0) >= 2:
            groups[row.get('category', '科技')].append(row)

    for key in groups:
        groups[key].sort(key=lambda x: x.get('importance', 0), reverse=True)

    lines = []
    biz = groups.get('商业', [])
    tech = groups.get('科技', [])

    lines.append(f'?? 商业类 (共{len(biz)}条)')
    for item in biz:
        lines.append(f"{_stars(item['importance'])} [{item['title']}] - {item['ai_summary']} - {item['source']}")
    lines.append('')

    lines.append(f'?? 科技类 (共{len(tech)}条)')
    for item in tech:
        lines.append(f"{_stars(item['importance'])} [{item['title']}] - {item['ai_summary']} - {item['source']}")

    return '\n'.join(lines).strip()


def write_digest_file(text: str, date: datetime | None = None) -> Path:
    date = date or datetime.now()
    out = Path('digest') / f'{date:%Y-%m-%d}.md'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding='utf-8')
    return out

