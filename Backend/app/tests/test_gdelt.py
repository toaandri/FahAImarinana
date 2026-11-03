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
        self.assertEqual(gdelt.classify_topics('Un cyclone frappe la côte'), ['Société'])
        self.assertEqual(gdelt.classify_topics('Investissement et économie'), ['Économie'])
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
        self.assertEqual(len(requests), 1)
        self.assertEqual(len(result['articles']), 1)
        self.assertEqual(result['articles'][0]['source'], 'news.example')
        self.assertEqual(result['articles'][0]['seen_at'], '2026-11-03T12:00:00+00:00')
        self.assertIsNone(result['articles'][0]['image'])
        self.assertNotIn('credibility', result['articles'][0])

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
            return httpx.Response(429) if request.url.host == 'api.gdeltproject.org' else httpx.Response(200, content=rss)
        with patch('app.services.gdelt.httpx.Client', side_effect=lambda **kw: real_client(transport=httpx.MockTransport(respond), **kw)):
            result = gdelt.latest_news()
        self.assertEqual(result['provider'], 'rss')
        self.assertEqual(result['articles'][0]['title'], 'Actualite malgache')
        self.assertEqual(result['articles'][0]['seen_at'], '2026-11-03T12:00:00+00:00')
        self.assertEqual(result['articles'][0]['image'], 'https://news.example/photo.jpg')
        self.assertEqual(result['articles'][0]['excerpt'], 'Extrait & faits.')
