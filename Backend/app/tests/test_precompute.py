import os
os.environ['DATABASE_URL'] = os.environ.get('FANILO_TEST_DATABASE_URL', 'sqlite:///:memory:')
os.environ['ENVIRONMENT'] = 'test'
os.environ['JWT_SECRET'] = 'isolated-test-secret-at-least-thirty-two-bytes'
os.environ['AUTO_CREATE_TABLES'] = 'false'
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from app.services import precompute

ARTICLE = {'url': 'https://original.example/story', 'title': 'Cyclone menace Antananarivo', 'excerpt': 'Cyclone menace Antananarivo demain.'}

class PrecomputeTests(unittest.TestCase):
    def test_candidates_remove_original_outlet_and_mark_reproduced_content(self):
        excerpt = 'Cyclone menace Antananarivo demain. Les habitants sont appelés à rester chez eux et les écoles sont fermées.' * 2
        leads = [{'url': 'https://original.example/another', 'title': ARTICLE['title'], 'excerpt': excerpt},
                 {'url': 'https://other.example/story', 'title': ARTICLE['title'], 'excerpt': excerpt},
                 {'url': 'https://third.example/story', 'title': ARTICLE['title'], 'excerpt': excerpt}]
        candidates = precompute._select_candidates(ARTICLE, leads, [])
        self.assertEqual(len(candidates), 2)
        self.assertFalse(candidates[0]['duplicate'])
        self.assertTrue(candidates[1]['duplicate'])
        self.assertTrue(all(item['assessment'] == 'inconclusive' for item in candidates))

    def test_missing_ai_never_produces_a_score(self):
        with patch.object(precompute, '_public_candidates', return_value=([], [])), patch.object(precompute, '_ai_suggestions', side_effect=precompute.IntegrationUnavailableError('offline')):
            result = precompute._run(ARTICLE, [], 'fr')
        self.assertIsNone(result['claim'])
        self.assertIsNone(result['calculation'])
        self.assertIn('ia_indisponible', result['warnings'])

    def test_ai_cannot_invent_citations_or_use_headlines_as_evidence(self):
        import httpx
        from pydantic import SecretStr
        candidates = [
            {'title': ARTICLE['title'], 'excerpt': 'Cyclone menace Antananarivo demain. Une alerte officielle a été annoncée pour les habitants.', 'duplicate': False, 'assessment': 'inconclusive', 'quote': ''},
            {'title': ARTICLE['title'], 'excerpt': '', 'duplicate': False, 'assessment': 'inconclusive', 'quote': ''},
        ]
        answer = {'choices': [{'message': {'content': '{"claim":"Cyclone menace Antananarivo demain.","assessments":[{"id":0,"assessment":"supports","quote":"Une citation totalement inventée et fausse"},{"id":1,"assessment":"supports","quote":"Cyclone menace Antananarivo demain."}]}'}, 'finish_reason': 'stop'}]}
        real_client = httpx.Client
        settings = SimpleNamespace(openrouter_api_key=SecretStr('test'), openrouter_model='test', openrouter_timeout_seconds=1)
        with patch.object(precompute, 'get_settings', return_value=settings), patch.object(precompute.httpx, 'Client', side_effect=lambda **kw: real_client(transport=httpx.MockTransport(lambda req: httpx.Response(200, json=answer)), **kw)):
            claim = precompute._ai_suggestions(ARTICLE, candidates, 'fr')
        self.assertEqual(claim, 'Cyclone menace Antananarivo demain.')
        self.assertTrue(all(item['assessment'] == 'inconclusive' for item in candidates))

    def test_jobs_are_private_and_reused(self):
        user = SimpleNamespace(id=101, newsroom_id=1, dataset='test')
        other = SimpleNamespace(id=102, newsroom_id=1, dataset='test')
        with patch.object(precompute._pool, 'submit'):
            first = precompute.start(user, ARTICLE, [], 'fr')
            second = precompute.start(user, ARTICLE, [], 'fr')
        try:
            self.assertEqual(first['job_id'], second['job_id'])
            with self.assertRaises(precompute.NotFoundError):
                precompute.get(other, first['job_id'])
        finally:
            with precompute._lock:
                precompute._jobs.pop(first['job_id'], None)

    def test_endpoint_only_accepts_an_article_from_the_feed(self):
        from fastapi import Response
        from app.api.v1.endpoints.copilot import begin_precompute
        from app.schemas.precompute import PrecomputeRequest
        from app.core.errors import NotFoundError
        user = SimpleNamespace(id=101, newsroom_id=1, dataset='test', response_language='fr')
        with patch.object(precompute.gdelt, 'latest_news', return_value={'articles': [ARTICLE]}), \
             patch('app.api.v1.endpoints.copilot.search_knowledge_base', return_value=[]), \
             patch.object(precompute, 'start', return_value={'job_id': 'a' * 32, 'status': 'queued'}) as start:
            with self.assertRaises(NotFoundError):
                begin_precompute(PrecomputeRequest(article_url='https://invalid.example/'), Response(), object(), user)
            response = Response()
            begin_precompute(PrecomputeRequest(article_url=ARTICLE['url']), response, object(), user)
            self.assertEqual(response.headers['cache-control'], 'no-store')
            self.assertEqual(start.call_args.args[1]['url'], ARTICLE['url'])
