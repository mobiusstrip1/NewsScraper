import os
from urllib.parse import quote

import requests


def send_bark(key: str, title: str, body: str) -> bool:
    if not key:
        return False
    url = f"https://api.day.app/{key}/{quote(title)}/{quote(body)}"
    try:
        requests.get(url, timeout=10)
        return True
    except Exception:
        return False


def send_daily_notice(biz_count: int, tech_count: int) -> bool:
    key = os.getenv('BARK_KEY', '')
    title = '今日AI资讯摘要已生成'
    body = f'商业{biz_count}条，科技{tech_count}条。完整内容已归档。'
    return send_bark(key, title, body)

