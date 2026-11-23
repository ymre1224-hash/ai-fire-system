#!/usr/bin/env python3
"""Collect link-only candidate articles from publisher RSS feeds.
No generated reviews, endorsements, affiliate links, or unsupported claims.
"""
import datetime as dt
import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'data' / 'candidates.json'
SOURCES = [
    ('GitHub Blog', 'https://github.blog/feed/'),
    ('Cloudflare Blog', 'https://blog.cloudflare.com/rss/'),
]
KEYWORDS = re.compile(r'\b(ai|agents?|artificial intelligence|automation|android|machine learning|llm|generative)\b', re.I)

def parse_feed(payload, publisher):
    root = ET.fromstring(payload)
    out = []
    for item in root.findall('.//item'):
        title = ' '.join((item.findtext('title') or '').split())[:160]
        url = (item.findtext('link') or '').strip()
        if not KEYWORDS.search(title):
            continue
        if not url.startswith('https://'):
            continue
        out.append({'publisher': publisher, 'title': title, 'url': url})
    return out

def collect():
    results = []
    errors = []
    for name, url in SOURCES:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'AI-FIRE-LAB/0.3 (RSS candidate feed)'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read(1_500_000)
            results.extend(parse_feed(data, name))
        except Exception as exc:
            errors.append(f'{name}: {exc.__class__.__name__}')
    return results, errors

def main():
    candidates, errors = collect()
    seen, unique = set(), []
    for c in candidates:
        if c['url'] in seen:
            continue
        seen.add(c['url']); unique.append(c)
    if not unique:
        print('No articles fetched; keeping existing data unchanged.', errors)
        return
    doc = {
        'generated_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
        'status': 'unverified_candidates',
        'note': '公式ブログの見出しとリンクを自動取得した候補一覧です。比較・推薦・価格情報ではありません。',
        'items': unique[:12],
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Wrote', len(doc['items']), 'candidates to', DEST, 'source_errors=', errors)

if __name__ == '__main__':
    main()
