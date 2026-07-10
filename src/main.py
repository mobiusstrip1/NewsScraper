import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

from classify import Classifier
from consolidate import consolidate_digest
from dedupe import ensure_schema, filter_new_articles, get_articles_for_date, get_conn, upsert_article
from digest import build_raw_digest_text, write_digest_file
from env_config import load_project_env, validate_env
from fetch import fetch_recent_articles
from notify import send_daily_digest


def _setup_logging() -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    try:
        handlers.append(logging.FileHandler('logs/run.log', encoding='utf-8'))
    except OSError:
        pass
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        handlers=handlers,
        force=True,
    )


def _classify_article(classifier: Classifier, article):
    result = classifier.classify(article)
    article.category = result['category']
    article.ai_summary = result['summary']
    article.importance = result['importance']
    article.tags = result['tags']
    return article


def run() -> None:
    load_project_env()
    _setup_logging()
    validate_env()
    os.makedirs('logs', exist_ok=True)
    os.makedirs('digest', exist_ok=True)

    t0 = time.time()
    conn = get_conn()
    ensure_schema(conn)

    logging.info('[1/4] Fetching RSS feeds...')
    fetched = fetch_recent_articles(hours=48)
    new_articles = filter_new_articles(conn, fetched)
    logging.info('Fetched %s articles, %s new (%.1fs)', len(fetched), len(new_articles), time.time() - t0)

    classifier = Classifier()
    total = len(new_articles)
    workers = max(1, int(os.getenv('LLM_CLASSIFY_WORKERS', '3')))

    if total:
        logging.info('[2/4] Classifying %s new articles (workers=%s)...', total, workers)
        t_classify = time.time()
        if workers > 1 and total > 1:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {
                    pool.submit(_classify_article, classifier, article): article
                    for article in new_articles
                }
                done = 0
                for future in as_completed(futures):
                    done += 1
                    article = future.result()
                    upsert_article(conn, article)
                    if done == 1 or done % 5 == 0 or done == total:
                        logging.info('  classify %s/%s: %s', done, total, article.title[:70])
        else:
            for idx, article in enumerate(new_articles, start=1):
                if idx == 1 or idx % 5 == 0 or idx == total:
                    logging.info('  classify %s/%s: %s', idx, total, article.title[:70])
                article = _classify_article(classifier, article)
                upsert_article(conn, article)
        logging.info('Classification done in %.1fs', time.time() - t_classify)
    else:
        logging.info('[2/4] No new articles to classify')

    today = date.today().isoformat()
    today_rows = get_articles_for_date(conn, today)
    logging.info('[3/4] Building digest from %s today rows...', len(today_rows))

    raw_text = build_raw_digest_text(today_rows)
    write_digest_file(raw_text, suffix='-raw')

    t_digest = time.time()
    digest_text, biz_count, tech_count = consolidate_digest(today_rows)
    logging.info('Digest built in %.1fs', time.time() - t_digest)
    out = write_digest_file(digest_text)

    logging.info('[4/4] Sending Bark notification...')
    sent = send_daily_digest(digest_text, biz_count, tech_count)

    logging.info(
        'Done in %.1fs | Fetched=%s New=%s Digest=%s Biz=%s Tech=%s BarkSent=%s',
        time.time() - t0,
        len(fetched),
        len(new_articles),
        out,
        biz_count,
        tech_count,
        sent,
    )


if __name__ == '__main__':
    run()
