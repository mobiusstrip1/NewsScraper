import logging
import os
from urllib.parse import quote

import requests

BARK_CHUNK_SIZE = 3500


def send_bark(key: str, title: str, body: str, *, group: str = 'AI资讯') -> bool:
    if not key:
        return False
    try:
        resp = requests.post(
            f'https://api.day.app/{key}/',
            json={
                'title': title,
                'body': body,
                'group': group,
                'isArchive': '1',
            },
            timeout=15,
        )
        resp.raise_for_status()
        return True
    except Exception:
        # Fallback for older/simple Bark setups.
        try:
            url = f'https://api.day.app/{key}/{quote(title)}/{quote(body[:500])}'
            requests.get(url, timeout=10)
            return True
        except Exception:
            return False


def _split_text(text: str, chunk_size: int = BARK_CHUNK_SIZE) -> list[str]:
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for line in text.splitlines():
        line_len = len(line) + 1
        if current_len + line_len > chunk_size and current:
            chunks.append('\n'.join(current))
            current = [line]
            current_len = line_len
        else:
            current.append(line)
            current_len += line_len

    if current:
        chunks.append('\n'.join(current))
    return chunks


def send_daily_digest(digest_text: str, biz_count: int, tech_count: int) -> int:
    key = os.getenv('BARK_KEY', '')
    if not key:
        logging.warning('BARK_KEY is empty, skip notification')
        return 0

    chunks = _split_text(digest_text)
    total = len(chunks)
    sent = 0

    for index, chunk in enumerate(chunks, start=1):
        if total == 1:
            title = f'今日AI资讯（商业{biz_count}·科技{tech_count}）'
        else:
            title = f'今日AI资讯 {index}/{total}（商业{biz_count}·科技{tech_count}）'
        if send_bark(key, title, chunk):
            sent += 1

    return sent


def send_test_notice() -> bool:
    key = os.getenv('BARK_KEY', '')
    return send_bark(key, 'Bark测试', '如果你看到这条消息，说明推送配置成功。')


if __name__ == '__main__':
    from dotenv import load_dotenv

    load_dotenv()
    ok = send_test_notice()
    print('sent' if ok else 'failed')
