import unittest
from unittest.mock import patch

import httpx

from app.services import gdelt
from app.core.errors import IntegrationUnavailableError


class GdeltTests(unittest.TestCase):
    def setUp(self):
        gdelt._cached = None
        gdelt._expires = 0

    def test_topic_classification_is_accent_insensitive_and_can_be_empty(self):
        self.assertEqual(gdelt.classify_topics('Élections : le président prend la parole'), ['Politique'])
        self.assertEqual(gdelt.classify_topics('Football : victoire des Barea'), ['Sport'])
        self.assertEqual(gdelt.classify_topics('Un cyclone frappe la côte'), ['Société', 'Environnement'])
        self.assertEqual(gdelt.classify_topics('Investissement et économie'), ['Économie'])
        self.assertEqual(gdelt.classify_topics('Les services financiers et bancaires'), ['Économie', 'Finance'])
        self.assertIn('Culture', gdelt.classify_topics('Festival de musique à Madagascar'))
        self.assertIn('Technologie', gdelt.classify_topics('Innovation numérique à Madagascar'))
        self.assertEqual(gdelt.classify_topics('Protection sociale à Madagascar'), ['Société'])
        self.assertEqual(gdelt.classify_topics('Actualités diverses'), [])
        self.assertIn('Sport', gdelt.classify_topics('Résultat du jour', metadata=['SPORT']))

    def test_normalizes_unverified_metadata_and_caches(self):
        requests = []
        def respond(request):
            requests.append(request)
            return httpx.Response(200, json={'articles': [
                {'title': 'Test Madagascar', 'url': 'https://news.example/article',
                 'seendate': '20261103T120000Z', 'socialimage': 'javascript:alert(1)'},
                {'title': 'Invalid', 'url': 'javascript:alert(1)'},
            ]})
        real_client = httpx.Client
        with patch('app.services.gdelt.httpx.Client', side_effect=lambda **kw: real_client(transport=httpx.MockTransport(respond), **kw)):
            result = gdelt.latest_news()
            self.assertEqual(gdelt.latest_news(), result)
        self.assertEqual(len(requests), 1 + len(gdelt.GOOGLE_NEWS_URLS) + len(gdelt.RSS_URLS))
        self.assertEqual(len(result['articles']), 1)
        self.assertEqual(result['articles'][0]['source'], 'news.example')
        self.assertEqual(result['articles'][0]['seen_at'], '2026-11-03T12:00:00+00:00')
        self.assertIsNone(result['articles'][0]['image'])
        self.assertNotIn('credibility', result['articles'][0])

    def test_google_news_is_combined_and_topic_feeds_are_interleaved(self):
        real_client = httpx.Client
        def respond(request):
            if request.url.host == 'api.gdeltproject.org':
                return httpx.Response(200, json={'articles': [{'title': 'Madagascar : actualité politique', 'url': 'https://example.org/politique'}]})
            term = request.url.params.get('q', '')
            if 'sport' in term:
                title, identifier = 'Football : victoire des Barea', 'sport'
            elif 'économie' in term:
                title, identifier = 'Économie et entreprises à Madagascar', 'economie'
            elif 'société' in term:
                title, identifier = 'Santé et écoles à Madagascar', 'societe'
            else:
                title, identifier = 'Madagascar actualités diverses', 'general'
            xml = f'<rss><channel><item><title>{title}</title><link>https://news.google.com/rss/articles/{identifier}</link><source>Journal local</source><description>{title}</description></item></channel></rss>'
            return httpx.Response(200, text=xml)
        with patch('app.services.gdelt.httpx.Client', side_effect=lambda **kw: real_client(transport=httpx.MockTransport(respond), **kw)):
            result = gdelt.latest_news()
        self.assertEqual(result['provider'], 'mixed')
        self.assertEqual(len(result['articles']), 5)
        for category in ('Politique', 'Sport', 'Économie', 'Société'):
            self.assertTrue(any(category in item['categories'] for item in result['articles']), category)
        google_item = result['articles'][1]
        self.assertEqual(google_item['source'], 'Journal local')
        self.assertEqual(google_item['excerpt'], '')

    def test_google_news_works_without_gdelt_and_deduplicates_links(self):
        article = {'url': 'https://news.google.com/rss/articles/one', 'title': 'Football', 'categories': ['Sport']}
        with patch.object(gdelt, '_gdelt_news', side_effect=ValueError()), patch.object(gdelt, '_google_news', return_value=[[article], [article], [], []]):
            result = gdelt.latest_news()
        self.assertEqual(result['provider'], 'google_news')
        self.assertEqual(result['articles'], [article])

    def test_press_images_are_included_with_google_news(self):
        google = {'url': 'https://news.google.com/articles/one', 'title': 'Actualité', 'image': None}
        press = {'url': 'https://press.example/two', 'title': 'Sport', 'image': 'https://press.example/image.jpg'}
        with patch.object(gdelt, '_gdelt_news', side_effect=ValueError()), \
             patch.object(gdelt, '_google_news', return_value=[[google]]), \
             patch.object(gdelt, '_rss_fallback', return_value={'articles': [press]}):
            result = gdelt.latest_news()
        self.assertEqual(result['provider'], 'mixed')
        self.assertIn(press, result['articles'])

    def test_image_proxy_only_serves_an_image_from_the_feed(self):
        from app.api.v1.endpoints.public import news_image
        from app.core.errors import NotFoundError
        url = 'https://www.madagascar-tribune.com/IMG/photo.jpg'
        transport = httpx.MockTransport(lambda request: httpx.Response(200, content=b'image', headers={'content-type': 'image/jpeg'}))
        with patch.object(gdelt, 'latest_news', return_value={'articles': [{'image': url}]}), \
             patch('httpx.stream', side_effect=lambda method, target, **kw: httpx.stream(method, target, **kw)) as stream:
            with self.assertRaises(NotFoundError):
                news_image('https://127.0.0.1/IMG/private.jpg')
            stream.assert_not_called()
        with patch.object(gdelt, 'latest_news', return_value={'articles': [{'image': url}]}), \
             patch('httpx.stream', side_effect=lambda method, target, **kw: httpx.Client(transport=transport).stream(method, target)):
            result = news_image(url)
        self.assertEqual(result.body, b'image')

    def test_google_news_searches_finance_and_social(self):
        terms = [httpx.URL(url).params['q'] for url in gdelt.GOOGLE_NEWS_URLS]
        self.assertIn('Madagascar finance', terms)
        self.assertIn('Madagascar social', terms)
        self.assertIn('Madagascar culture', terms)
        self.assertIn('Madagascar environnement', terms)
        self.assertIn('Madagascar technologie', terms)

    def test_rss_follows_only_same_host_redirects(self):
        real_client = httpx.Client
        requests = []
        def respond(request):
            requests.append(str(request.url))
            if request.url.path == '/start':
                return httpx.Response(302, headers={'location': '/feed'})
            return httpx.Response(200, text='<rss><channel><item><title>Sport</title><link>https://example.org/article</link></item></channel></rss>')
        with patch('app.services.gdelt.httpx.Client', side_effect=lambda **kw: real_client(transport=httpx.MockTransport(respond), **kw)):
            self.assertEqual(len(gdelt._rss_fallback(('https://news.google.com/start',))['articles']), 1)
        self.assertEqual(len(requests), 2)
        requests.clear()
        def unsafe(request):
            requests.append(str(request.url))
            return httpx.Response(302, headers={'location': 'http://127.0.0.1/private'})
        with patch('app.services.gdelt.httpx.Client', side_effect=lambda **kw: real_client(transport=httpx.MockTransport(unsafe), **kw)):
            with self.assertRaises(IntegrationUnavailableError):
                gdelt._rss_fallback(('https://news.google.com/start',))
        self.assertEqual(len(requests), 1)

    def test_invalid_provider_response_is_explicit(self):
        real_client = httpx.Client
        transport = httpx.MockTransport(lambda request: httpx.Response(429))
        with patch('app.services.gdelt.time.sleep'), patch('app.services.gdelt.httpx.Client', side_effect=lambda **kw: real_client(transport=transport, **kw)):
            with self.assertRaises(IntegrationUnavailableError):
                gdelt.latest_news()

    def test_gdelt_limit_uses_rss_and_identifies_source(self):
        real_client = httpx.Client
        rss = b'''<?xml version="1.0"?><rss xmlns:media="http://search.yahoo.com/mrss/"><channel>
        <item><title>Actualite malgache</title><link>https://news.example/a</link>
        <pubDate>Tue, 03 Nov 2026 12:00:00 GMT</pubDate>
        <description>&lt;p&gt;Extrait &amp;amp; faits.&lt;/p&gt;</description>
        <media:content url="https://news.example/photo.jpg" type="image/jpeg" /></item>
        </channel></rss>'''
        def respond(request):
            return httpx.Response(429) if request.url.host in ('api.gdeltproject.org', 'news.google.com') else httpx.Response(200, content=rss)
        with patch('app.services.gdelt.httpx.Client', side_effect=lambda **kw: real_client(transport=httpx.MockTransport(respond), **kw)):
            result = gdelt.latest_news()
        self.assertEqual(result['provider'], 'rss')
        self.assertEqual(result['articles'][0]['title'], 'Actualite malgache')
        self.assertEqual(result['articles'][0]['seen_at'], '2026-11-03T12:00:00+00:00')
        self.assertEqual(result['articles'][0]['image'], 'https://news.example/photo.jpg')
        self.assertEqual(result['articles'][0]['excerpt'], 'Extrait & faits.')
