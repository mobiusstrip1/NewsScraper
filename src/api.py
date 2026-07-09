from datetime import date, datetime, timedelta
import json
import sqlite3

from fastapi import FastAPI, Query

app = FastAPI(title='AI News Digest API')


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect('data/news.db')
    conn.row_factory = sqlite3.Row
    return conn


def _query_by_date(target: str):
    conn = _connect()
    rows = conn.execute(
        '''
        SELECT title, link, source, published_time, category, ai_summary, importance, tags, created_at
        FROM articles
        WHERE substr(created_at,1,10)=?
        ORDER BY importance DESC, published_time DESC
        ''',
        (target,),
    ).fetchall()
    conn.close()
    result = []
    for row in rows:
        item = dict(row)
        item['tags'] = json.loads(item['tags'] or '[]')
        result.append(item)
    return result


@app.get('/digest/today')
def digest_today():
    today = date.today().isoformat()
    return {'date': today, 'items': _query_by_date(today)}


@app.get('/digest/{target_date}')
def digest_by_date(target_date: str):
    datetime.strptime(target_date, '%Y-%m-%d')
    return {'date': target_date, 'items': _query_by_date(target_date)}


@app.get('/digest')
def digest_filter(category: str | None = Query(default=None), days: int = Query(default=7, ge=1, le=30)):
    conn = _connect()
    start = (date.today() - timedelta(days=days - 1)).isoformat()
    sql = '''
        SELECT title, link, source, published_time, category, ai_summary, importance, tags, created_at
        FROM articles
        WHERE substr(created_at,1,10) >= ?
    '''
    params: list = [start]
    if category:
        sql += ' AND category = ?'
        params.append(category)
    sql += ' ORDER BY created_at DESC, importance DESC'
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    result = []
    for row in rows:
        item = dict(row)
        item['tags'] = json.loads(item['tags'] or '[]')
        result.append(item)
    return {'days': days, 'category': category, 'items': result}

