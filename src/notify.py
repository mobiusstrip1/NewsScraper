import logging
import os
import sys
from urllib.parse import quote

import requests

BARK_CHUNK_SIZE = 3500
DEFAULT_BARK_SERVER = 'https://api.day.app'


def _parse_bark_response(resp: requests.Response) -> tuple[bool, str]:
    try:
        data = resp.json()
    except Exception:
        return False, f'invalid JSON response: {resp.text[:200]}'

    code = data.get('code')
    message = str(data.get('message', ''))
    if code == 200:
        return True, message or 'success'
    return False, f'Bark API code={code}, message={message}'


def send_bark(
    key: str,
    title: str,
    body: str,
    *,
    group: str = 'AI资讯',
    server: str = DEFAULT_BARK_SERVER,
    verbose: bool = False,
) -> tuple[bool, str]:
    key = (key or '').strip()
    if not key:
        return False, 'BARK_KEY is empty'

    if key.lower().startswith('device'):
        return False, 'looks like device token, please use Bark push Key instead'

    server = server.rstrip('/')
    endpoint = f'{server}/{key}/'

    try:
        resp = requests.post(
            endpoint,
            json={
                'title': title,
                'body': body,
                'group': group,
                'isArchive': '1',
            },
            timeout=15,
        )
        ok, detail = _parse_bark_response(resp)
        if verbose:
            print(f'POST {endpoint}')
            print(f'HTTP {resp.status_code}: {resp.text[:300]}')
        if ok:
            return True, detail
    except Exception as exc:
        if verbose:
            print(f'POST failed: {exc}')

    # Fallback for older/simple Bark setups.
    try:
        url = f'{server}/{key}/{quote(title)}/{quote(body[:500])}'
        resp = requests.get(url, timeout=10)
        ok, detail = _parse_bark_response(resp)
        if verbose:
            print(f'GET {url}')
            print(f'HTTP {resp.status_code}: {resp.text[:300]}')
        return ok, detail
    except Exception as exc:
        return False, str(exc)


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
    server = os.getenv('BARK_SERVER', DEFAULT_BARK_SERVER)
    if not key.strip():
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
        ok, detail = send_bark(key, title, chunk, server=server)
        if ok:
            sent += 1
        else:
            logging.warning('Bark push failed: %s', detail)

    return sent


def send_test_notice(verbose: bool = False) -> tuple[bool, str]:
    key = os.getenv('BARK_KEY', '')
    server = os.getenv('BARK_SERVER', DEFAULT_BARK_SERVER)
    return send_bark(
        key,
        'Bark测试',
        '如果你看到这条消息，说明推送配置成功。',
        server=server,
        verbose=verbose,
    )


if __name__ == '__main__':
    from dotenv import load_dotenv

    load_dotenv()
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    key = os.getenv('BARK_KEY', '').strip()
    if key:
        masked = f'{key[:4]}...{key[-4:]}' if len(key) > 8 else '(too short)'
        print(f'BARK_KEY loaded: {masked} (len={len(key)})')
    else:
        print('BARK_KEY is empty')

    ok, detail = send_test_notice(verbose=verbose)
    print('sent' if ok else 'failed')
    print(detail)
