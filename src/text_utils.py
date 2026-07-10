import html
import re


def clean_text(text: str, max_len: int = 1000) -> str:
    if not text:
        return ''
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:max_len]
