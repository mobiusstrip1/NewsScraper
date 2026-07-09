import logging
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import feedparser
import yaml

from models import Article


def _parse_published(entry) -> datetime | None:
    if getattr(entry, 'published_parsed', None):
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    if getattr(entry, 'updated_parsed', None):
        return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
    if getattr(entry, 'published', None):
        try:
            dt = parsedate_to_datetime(entry.published)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            return None
    return None


def load_sources(config_path: str = 'config/sources.yaml') -> list[dict]:
    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    return data.get('sources', [])


def fetch_recent_articles(hours: int = 48) -> list[Article]:
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(hours=hours)
    results: list[Article] = []

    for source in load_sources():
        source_name = source['name']
        source_url = source['url']
        try:
            feed = feedparser.parse(source_url)
            for entry in feed.entries:
                published_time = _parse_published(entry)
                if not published_time or published_time < threshold:
                    continue
                title = (getattr(entry, 'title', '') or '').strip()
                link = (getattr(entry, 'link', '') or '').strip()
                if not title or not link:
                    continue
                summary = (getattr(entry, 'summary', '') or '').strip()
                results.append(
                    Article(
                        title=title,
                        link=link,
                        summary=summary,
                        source=source_name,
                        published_time=published_time,
                    )
                )
        except Exception as exc:
            logging.exception('Failed to fetch source %s (%s): %s', source_name, source_url, exc)

    return results

