"""Bounded, cached GDELT discovery feed; results are not fact checks."""
import threading
import time
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from xml.etree import ElementTree

import httpx

from ..core.errors import IntegrationUnavailableError

URL = 'https://api.gdeltproject.org/api/v2/doc/doc'
_lock = threading.Lock()
_cached = None
_expires = 0.0
GOOGLE_NEWS_URLS = (
    'https://news.google.com/rss/search?q=Madagascar&hl=fr&gl=MG&ceid=MG:fr',
    'https://news.google.com/rss/search?q=Madagascar+sport&hl=fr&gl=MG&ceid=MG:fr',
    'https://news.google.com/rss/search?q=Madagascar+%C3%A9conomie&hl=fr&gl=MG&ceid=MG:fr',
    'https://news.google.com/rss/search?q=Madagascar+soci%C3%A9t%C3%A9&hl=fr&gl=MG&ceid=MG:fr',
)
RSS_URLS = ('https://www.madagascar-tribune.com/spip.php?page=backend',
            'https://www.france24.com/fr/tag/madagascar/rss')

TOPIC_TERMS = {
    'Politique': ('politique', 'gouvernement', 'president', 'presidentiel', 'election', 'electoral',
                  'parlement', 'depute', 'senat', 'ministre', 'maire', 'diplomatie', 'opposition',
                  'government', 'president', 'election', 'minister', 'politics', 'parliament',
                  'fitondrana', 'filoha', 'fifidianana', 'governemanta'),
    'Sport': ('sport', 'sportif', 'football', 'foot', 'basket', 'basketball', 'rugby', 'tennis',
              'athletisme', 'athlete', 'championnat', 'champion', 'olympique', 'match',
              'footballer', 'soccer', 'athletics', 'olympics', 'tournament', 'barea', 'kitra', 'volleyball', 'cyclisme', 'judo'),
    'Économie': ('economie', 'economique', 'entreprise', 'investissement', 'commerce', 'industrie',
                 'finance', 'banque', 'inflation', 'emploi', 'budget', 'agriculture', 'tourisme',
                 'economy', 'business', 'investment', 'trade', 'tourism', 'toekarena', 'varotra', 'peche', 'paysans', 'agricole', 'exportation'),
    'Société': ('societe', 'education', 'sante', 'ecole', 'hopital', 'population', 'justice',
                'environnement', 'climat', 'inondation', 'cyclone', 'police', 'culture',
                'community', 'health', 'school', 'education', 'climate', 'fahasalamana', 'sekoly', 'universite', 'etudiants', 'maladie', 'medecin'),
}


def classify_topics(title: str, excerpt: str = '', metadata=()) -> list[str]:
    """Best-effort keywords on supplied metadata, title and excerpt; not editorial labels."""
    text = ' '.join([title, excerpt, *metadata]).casefold()
    text = ''.join(char for char in unicodedata.normalize('NFKD', text) if not unicodedata.combining(char))
    words = set(re.findall(r'[^\W_]+', text))
    words.update(word[:-1] for word in tuple(words) if len(word) > 4 and word.endswith('s'))
    return [category for category, terms in TOPIC_TERMS.items() if words.intersection(terms)]


def _valid_url(value):
    if not isinstance(value, str) or len(value) > 2000:
        return None
    try:
        parsed = urlsplit(value)
        return value if parsed.scheme in ('http', 'https') and parsed.hostname and not parsed.username and not parsed.password else None
    except ValueError:
        return None


class _FeedContent(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text = []
        self.images = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.hidden += 1
        if tag == 'img':
            self.images.append(dict(attrs).get('src', ''))

    def handle_endtag(self, tag):
        if tag in ('script', 'style') and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.text.append(data)


def _rss_content(item, article_url):
    description = item.findtext('description') or ''
    encoded = item.findtext('{http://purl.org/rss/1.0/modules/content/}encoded') or ''
    parser = _FeedContent()
    parser.feed(description or encoded)
    excerpt = ' '.join(' '.join(parser.text).split())[:1200]
    images = []
    for tag in ('{http://search.yahoo.com/mrss/}content', '{http://search.yahoo.com/mrss/}thumbnail', 'enclosure'):
        for element in item.findall(tag):
            if tag != 'enclosure' or element.get('type', '').startswith('image/'):
                images.append(element.get('url', ''))
    if not images:
        images.extend(parser.images)
        if encoded and encoded != description:
            image_parser = _FeedContent()
            image_parser.feed(encoded)
            images.extend(image_parser.images)
    image = next((valid for candidate in images if candidate and (valid := _valid_url(urljoin(article_url, candidate)))), None)
    return excerpt, image


def _rss_fallback(urls=RSS_URLS):
    """Return recent real headlines when GDELT is unavailable."""
    with httpx.Client(timeout=5, follow_redirects=False) as client:
        for url in urls:
            try:
                with client.stream('GET', url, headers={'User-Agent': 'FahAImarinana/1.0'}) as response:
                    response.raise_for_status()
                    parts, size = [], 0
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > 1024 * 1024:
                            raise ValueError('RSS response too large')
                        parts.append(chunk)
                root = ElementTree.fromstring(b''.join(parts))
                results, seen = [], set()
                for item in root.findall('./channel/item'):
                    link = _valid_url(item.findtext('link'))
                    title = item.findtext('title')
                    if not link or link in seen or not title or not title.strip():
                        continue
                    seen.add(link)
                    try:
                        date = parsedate_to_datetime(item.findtext('pubDate') or '').astimezone(timezone.utc).isoformat()
                    except (TypeError, ValueError, OverflowError):
                        date = None
                    excerpt, image = _rss_content(item, link)
                    # Google News descriptions commonly repeat the headline and outlet only.
                    if urlsplit(link).hostname == 'news.google.com':
                        excerpt = ''
                    categories = classify_topics(title, excerpt, [category.text or '' for category in item.findall('category')])
                    results.append({'title': title.strip()[:500], 'url': link,
                                    'source': (item.findtext('source') or urlsplit(link).hostname or '')[:250], 'seen_at': date, 'image': image,
                                    'excerpt': excerpt, 'categories': categories})
                    if len(results) >= 30:
                        break
                if results:
                    return {'articles': results, 'fetched_at': datetime.now(timezone.utc).isoformat(), 'provider': 'rss'}
            except (httpx.HTTPError, ValueError, ElementTree.ParseError):
                continue
    raise IntegrationUnavailableError('Actualités momentanément indisponibles.')


def _gdelt_news():
    with httpx.Client(timeout=5, follow_redirects=False) as client:
        with client.stream('GET', URL, params={'query': 'Madagascar', 'mode': 'ArtList',
             'format': 'json', 'sort': 'DateDesc', 'maxrecords': 30}) as response:
            response.raise_for_status()
            chunks, size = [], 0
            for chunk in response.iter_bytes():
                size += len(chunk)
                if size > 1024 * 1024:
                    raise ValueError('Response too large')
                chunks.append(chunk)
    import json
    data = json.loads(b''.join(chunks))
    articles = data.get('articles', [])
    if not isinstance(articles, list):
        raise ValueError('Invalid articles')
    results = []
    for item in articles[:30]:
        if not isinstance(item, dict):
            continue
        url = _valid_url(item.get('url'))
        title = item.get('title')
        if not url or not isinstance(title, str) or not title.strip():
            continue
        raw_date = item.get('seendate', '')
        try:
            date = datetime.strptime(raw_date, '%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc).isoformat()
        except (ValueError, TypeError):
            date = None
        results.append({'title': title.strip()[:500], 'url': url,
            'source': urlsplit(url).hostname or '', 'seen_at': date,
            'image': _valid_url(item.get('socialimage')), 'excerpt': '',
            'categories': classify_topics(title)})
    if not results:
        raise ValueError('No articles')
    return results


def _google_news():
    # Fixed URLs and short timeouts keep discovery bounded; no article URL is fetched.
    def load(url):
        try:
            return _rss_fallback((url,))['articles']
        except (IntegrationUnavailableError, httpx.HTTPError, ValueError):
            return []

    with ThreadPoolExecutor(max_workers=len(GOOGLE_NEWS_URLS)) as pool:
        return list(pool.map(load, GOOGLE_NEWS_URLS))


def _merge_feeds(feeds):
    # Interleave providers and topic searches so a large political feed cannot hide
    # the other searches. Deduplicate links without guessing publisher identity.
    output, seen = [], set()
    for index in range(max((len(feed) for feed in feeds), default=0)):
        for feed in feeds:
            if index >= len(feed):
                continue
            item = feed[index]
            if item['url'] not in seen:
                seen.add(item['url'])
                output.append(item)
            if len(output) >= 120:
                return output
    return output


def latest_news():
    global _cached, _expires
    with _lock:
        if _cached is not None and time.monotonic() < _expires:
            return _cached
        try:
            gdelt_items = _gdelt_news()
        except (httpx.HTTPError, ValueError, TypeError, AttributeError):
            gdelt_items = []
        google_feeds = _google_news()
        google_available = any(google_feeds)
        feeds = ([gdelt_items] if gdelt_items else []) + google_feeds
        items = _merge_feeds(feeds)
        if items:
            provider = 'mixed' if gdelt_items and google_available else ('gdelt' if gdelt_items else 'google_news')
            _cached = {'articles': items, 'fetched_at': datetime.now(timezone.utc).isoformat(), 'provider': provider}
            _expires = time.monotonic() + 300
            return _cached
        try:
            _cached = _rss_fallback()
            _expires = time.monotonic() + 300
            return _cached
        except (IntegrationUnavailableError, httpx.HTTPError):
            if _cached is not None:
                return {**_cached, 'stale': True}
            raise IntegrationUnavailableError('Actualités momentanément indisponibles.') from None
