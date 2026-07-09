import hashlib
import json
import sqlite3
from datetime import datetime, timezone

from models import Article

DB_PATH = 'data/news.db'


def get_conn(db_path: str = DB_PATH) -> sqlite3.Connection:
    return sqlite3.connect(db_path)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url_hash TEXT UNIQUE,
            title TEXT NOT NULL,
            link TEXT NOT NULL,
            source TEXT NOT NULL,
            published_time TEXT NOT NULL,
            category TEXT,
            ai_summary TEXT,
            importance INTEGER,
            tags TEXT,
            created_at TEXT NOT NULL
        )
        '''
    )
    conn.commit()


def hash_link(link: str) -> str:
    return hashlib.sha256(link.encode('utf-8')).hexdigest()


def filter_new_articles(conn: sqlite3.Connection, articles: list[Article]) -> list[Article]:
    new_items = []
    for article in articles:
        h = hash_link(article.link)
        cur = conn.execute('SELECT 1 FROM articles WHERE url_hash = ?', (h,))
        if cur.fetchone() is None:
            new_items.append(article)
    return new_items


def upsert_article(conn: sqlite3.Connection, article: Article) -> None:
    h = hash_link(article.link)
    conn.execute(
        '''
        INSERT OR IGNORE INTO articles (
            url_hash, title, link, source, published_time, category, ai_summary, importance, tags, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            h,
            article.title,
            article.link,
            article.source,
            article.published_time.astimezone(timezone.utc).isoformat(),
            article.category,
            article.ai_summary,
            article.importance,
            json.dumps(article.tags or [], ensure_ascii=False),
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()

