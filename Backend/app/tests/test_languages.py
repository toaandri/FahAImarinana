"""Language preferences, routing, detection and source-preserving translations."""
import os
os.environ['DATABASE_URL'] = os.environ.get('FANILO_TEST_DATABASE_URL', 'sqlite:///:memory:')
os.environ['ENVIRONMENT'] = 'test'
os.environ['JWT_SECRET'] = 'isolated-test-secret-at-least-thirty-two-bytes'
os.environ['GEMINI_API_KEY'] = ''
os.environ['OPENROUTER_API_KEY'] = ''
os.environ['GOOGLE_TRANSLATION_API_KEY'] = ''
os.environ['AUTO_CREATE_TABLES'] = 'false'

import unittest
from unittest.mock import patch
import httpx
from fastapi.testclient import TestClient
from app.core.config import Settings
from app.core.errors import IntegrationUnavailableError
from app.main import create_app
from app.tests.fixtures import reset_schema, make_account, tokens_for, system_session
from app.models import User
from app.services.translation import translate_answer
from app.integrations.ai.openrouter import OpenRouterUnavailableError, answer_question
from app.integrations.ai.gemini import research_web
from app.utils.languages import resolve_language, language_instruction, expand_research_question


class LanguagePolicyTests(unittest.TestCase):
    def test_auto_detection_and_explicit_override(self):
        for question, language in [('Inona no atao hoe fanamarinana ny vaovao?', 'mg'),
                                   ('Salama, afaka manampy ahy ve ianao?', 'mg'),
                                   ('Comment vérifier une information ?', 'fr'),
                                   ('Explique la méthode en malagasy', 'mg'),
                                   ('Antananarivo', 'fr'), ('Hello', 'en'), ('Is this news true?', 'en'),
                                   ('How can I verify this claim?', 'en'), ('Bonjour', 'fr'), ('Salama', 'mg')]:
            self.assertEqual(resolve_language('auto', question), language)
        self.assertEqual(resolve_language('mg', 'Bonjour'), 'mg')
        self.assertEqual(resolve_language('fr', 'Salama'), 'fr')
        self.assertIn('preuve', expand_research_question('Inona ny porofo?'))

    def test_english_reaches_both_providers(self):
        settings = Settings(openrouter_api_key='test', jwt_secret='test')
        response = httpx.Response(200, json={'choices': [{'message': {'content': 'Hello'}}]},
                                  request=httpx.Request('POST', 'https://openrouter.ai'))
        with patch('app.integrations.ai.openrouter.get_settings', return_value=settings), \
             patch('app.integrations.ai.openrouter.httpx.Client') as client:
            post = client.return_value.__enter__.return_value.post
            post.return_value = response
            answer_question('Hello', [], language=resolve_language('auto', 'Hello'))
            self.assertIn('English', post.call_args.kwargs['json']['messages'][0]['content'])
        with patch('app.integrations.ai.gemini._request', return_value={'output_text': 'Hello'}) as request:
            research_web('Hello', language=resolve_language('auto', 'Hello'))
            self.assertIn('English', request.call_args.args[0]['input'])

    def test_both_providers_receive_malagasy_and_glossary(self):
        settings = Settings(openrouter_api_key='test', jwt_secret='test')
        response = httpx.Response(200, json={'choices': [{'message': {'content': 'Salama'}}]},
                                  request=httpx.Request('POST', 'https://openrouter.ai'))
        with patch('app.integrations.ai.openrouter.get_settings', return_value=settings), \
             patch('app.integrations.ai.openrouter.httpx.Client') as client:
            post = client.return_value.__enter__.return_value.post
            post.return_value = response
            self.assertEqual(answer_question('Bonjour', [], language='mg'), 'Salama')
            instruction = post.call_args.kwargs['json']['messages'][0]['content']
            self.assertIn(language_instruction('mg'), instruction)
            self.assertIn('loharano', instruction)
        with patch('app.integrations.ai.gemini._request', return_value={'output_text': 'Valiny'}) as request:
            self.assertEqual(research_web('Bonjour', language='mg'), ('Valiny', []))
            self.assertIn(language_instruction('mg'), request.call_args.args[0]['input'])


class TranslationTests(unittest.TestCase):
    def test_openrouter_translation_preserves_links(self):
        settings = Settings(openrouter_api_key='test', jwt_secret='test')
        with patch('app.services.translation.get_settings', return_value=settings), \
             patch('app.services.translation.answer_question', return_value='Loharano : FAHAIURL0TOKEN') as answer:
            result = translate_answer('Source : https://example.invalid/article?id=5', 'mg')
            self.assertEqual(result, {'text': 'Loharano : https://example.invalid/article?id=5', 'language': 'mg', 'provider': 'openrouter'})
            self.assertEqual(answer.call_args.kwargs, {'language': 'mg', 'translate': True})

    def test_google_is_used_when_configured(self):
        settings = Settings(google_translation_api_key='test-google-secret', jwt_secret='test')
        response = httpx.Response(200, json={'data': {'translations': [{'translatedText': 'Salama'}]}},
                                  request=httpx.Request('POST', 'https://translation.googleapis.com'))
        with patch('app.services.translation.get_settings', return_value=settings), \
             patch('app.services.translation.httpx.Client') as client:
            post = client.return_value.__enter__.return_value.post
            post.return_value = response
            self.assertEqual(translate_answer('Bonjour', 'mg')['provider'], 'google_translation')
            self.assertEqual(post.call_args.kwargs['json']['target'], 'mg')
            self.assertNotIn('test-google-secret', post.call_args.args[0])

    def test_google_failure_falls_back_to_existing_provider(self):
        settings = Settings(google_translation_api_key='test-google', openrouter_api_key='test', jwt_secret='test')
        response = httpx.Response(403, request=httpx.Request('POST', 'https://translation.googleapis.com'))
        with patch('app.services.translation.get_settings', return_value=settings), \
             patch('app.services.translation.httpx.Client') as client, \
             patch('app.services.translation.answer_question', return_value='Salama'):
            client.return_value.__enter__.return_value.post.return_value = response
            self.assertEqual(translate_answer('Bonjour', 'mg')['provider'], 'openrouter')

    def test_missing_or_invented_links_are_rejected_and_fallback_is_used(self):
        settings = Settings(openrouter_api_key='test', gemini_api_key='test', jwt_secret='test')
        with patch('app.services.translation.get_settings', return_value=settings), \
             patch('app.services.translation.answer_question', return_value='Loharano https://invented.invalid'), \
             patch('app.services.translation.translate_text', return_value='Loharano FAHAIURL0TOKEN'):
            translated = translate_answer('Source https://example.invalid', 'mg')
            self.assertEqual(translated['provider'], 'gemini')
            self.assertEqual(translated['text'], 'Loharano https://example.invalid')

    def test_unavailable_is_explicit_in_requested_language(self):
        settings = Settings(jwt_secret='test')
        with patch('app.services.translation.get_settings', return_value=settings):
            with self.assertRaisesRegex(IntegrationUnavailableError, 'Tsy afaka'):
                translate_answer('Bonjour', 'mg')


class LanguageEndpointTests(unittest.TestCase):
    def setUp(self):
        reset_schema()
        self.user = make_account('JOURNALISTE', email='languages@example.invalid')
        self.other = make_account('JOURNALISTE', email='languages-other@example.invalid')
        self.headers = {'Authorization': 'Bearer ' + tokens_for(self.user).access_token}
        self.client = TestClient(create_app())
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)

    def test_preference_persists_and_is_private(self):
        response = self.client.patch('/api/v1/auth/me/language', headers=self.headers, json={'language': 'mg'})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.client.get('/api/v1/auth/me', headers=self.headers).json()['response_language'], 'mg')
        with system_session() as db:
            self.assertEqual(db.get(User, self.user.id).response_language, 'mg')
            self.assertEqual(db.get(User, self.other.id).response_language, 'auto')
        self.assertEqual(self.client.patch('/api/auth/me/language', headers=self.headers, json={'language': 'xx'}).status_code, 422)
        self.assertEqual(self.client.patch('/api/auth/me/language', json={'language': 'mg'}).status_code, 401)

    def test_research_and_persistent_chat_use_preference_and_explicit_language(self):
        self.client.patch('/api/auth/me/language', headers=self.headers, json={'language': 'mg'})
        with patch('app.api.v1.endpoints.copilot.build_research_answer', return_value=('Valiny', [], [])) as answer:
            response = self.client.post('/api/v1/copilot/research', headers=self.headers, json={'question': 'Bonjour'})
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(answer.call_args.kwargs, {'use_openrouter': True, 'language': 'mg'})
            self.client.post('/api/copilot/research', headers=self.headers, json={'question': 'Bonjour', 'language': 'fr'})
            self.assertEqual(answer.call_args.kwargs['language'], 'fr')
            for question, expected in [('Hello, is this true?', 'en'), ('Bonjour, est-ce vrai?', 'fr'), ('Salama, marina ve izany?', 'mg')]:
                response = self.client.post('/api/copilot/research', headers=self.headers, json={'question': question, 'language': 'auto'})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(answer.call_args.kwargs['language'], expected)
            self.client.post('/api/copilot/research', headers=self.headers, json={'question': 'Inona ny vaovao?', 'language': 'auto'})
            self.assertEqual(answer.call_args.kwargs['language'], 'mg')
        session = self.client.post('/api/copilot/sessions', headers=self.headers, json={'titre': 'Malagasy'}).json()
        with patch('app.services.chat.build_research_answer', return_value=('Valiny', [], [])) as answer:
            response = self.client.post(f"/api/copilot/sessions/{session['id']}/ask", headers=self.headers, json={'question': 'Bonjour'})
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(answer.call_args.kwargs['language'], 'mg')

    def test_local_fallback_and_translation_validation(self):
        response = self.client.post('/api/copilot/research', headers=self.headers, json={'question': 'Inona ny vaovao?', 'language': 'auto'})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn('Tsy misy', response.json()['reponse'])
        self.assertEqual(self.client.post('/api/copilot/translate', headers=self.headers, json={'text': 'Bonjour', 'target_language': 'auto'}).status_code, 422)
        with patch('app.api.v1.endpoints.copilot.translate_answer', return_value={'text': 'Salama', 'language': 'mg', 'provider': 'openrouter'}):
            response = self.client.post('/api/copilot/translate', headers=self.headers, json={'text': 'Bonjour', 'target_language': 'mg'})
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertEqual(self.client.post('/api/copilot/translate', json={'text': 'Bonjour', 'target_language': 'mg'}).status_code, 401)


if __name__ == '__main__':
    unittest.main()
