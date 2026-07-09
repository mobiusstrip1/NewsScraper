import logging
import os
from collections import Counter
from datetime import date

from dotenv import load_dotenv

from classify import Classifier
from dedupe import ensure_schema, filter_new_articles, get_articles_for_date, get_conn, upsert_article
from digest import build_digest_text, write_digest_file
from fetch import fetch_recent_articles
from notify import send_daily_digest


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler('logs/run.log', encoding='utf-8'),
        logging.StreamHandler(),
    ],
)


def run() -> None:
    load_dotenv()
    os.makedirs('logs', exist_ok=True)
    os.makedirs('digest', exist_ok=True)

    conn = get_conn()
    ensure_schema(conn)

    fetched = fetch_recent_articles(hours=48)
    new_articles = filter_new_articles(conn, fetched)

    classifier = Classifier()

    for article in new_articles:
        result = classifier.classify(article)
        article.category = result['category']
        article.ai_summary = result['summary']
        article.importance = result['importance']
        article.tags = result['tags']
        upsert_article(conn, article)

    today = date.today().isoformat()
    today_rows = get_articles_for_date(conn, today)
    digest_text = build_digest_text(today_rows)
    out = write_digest_file(digest_text)

    counter = Counter(item['category'] for item in today_rows if (item.get('importance') or 0) >= 2)
    sent = send_daily_digest(
        digest_text,
        counter.get('商业', 0),
        counter.get('科技', 0),
    )

    logging.info(
        'Fetched=%s New=%s Digest=%s BarkSent=%s',
        len(fetched),
        len(new_articles),
        out,
        sent,
    )


if __name__ == '__main__':
    run()

