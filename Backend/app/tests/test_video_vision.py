"""Private video contract, vendor failures, idempotence and HTTP authorization."""
import os
os.environ['DATABASE_URL'] = os.environ.get('FANILO_TEST_DATABASE_URL', 'sqlite:///:memory:')
os.environ['ENVIRONMENT'] = 'test'
os.environ['JWT_SECRET'] = 'isolated-test-secret-at-least-thirty-two-bytes'
os.environ['AUTO_CREATE_TABLES'] = 'false'
os.environ['GEMINI_API_KEY'] = ''
import base64
from datetime import datetime, timezone
import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from uuid import uuid4
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import select
from app.main import create_app
from app.core.config import get_settings
from app.tests.fixtures import reset_schema, make_account, tokens_for, system_session
from app.models import MediaAnalysis, Publication
from app.schemas.vision import VideoClipRequest
from app.integrations.ai import gemini

VALID = {'title': 'Observation du clip', 'summary': 'Un rectangle est visible.',
         'observations': [{'time_seconds': 1.0, 'description': 'Une forme rouge sur un fond bleu.'}],
         'limitations': ['La vidéo ne prouve ni le lieu ni la date.'], 'questions_to_verify': ['Quelle est l’origine du clip ?']}


def clip_body():
    return {'capture_id': str(uuid4()), 'sequence': 1,
            'captured_at': datetime.now(timezone.utc).isoformat(), 'duration_seconds': 2,
            # Deliberate container stub; no real provider is invoked in this test suite.
            'video_base64': base64.b64encode(b'\x00\x00\x00\x18ftypisomPRIVATE_CLIP').decode(),
            'mime_type': 'video/mp4', 'language': 'fr'}


class VideoVisionTests(unittest.TestCase):
    def setUp(self):
        reset_schema()
        self.journalist = make_account('JOURNALISTE')
        self.reader = make_account('LECTEUR')
        self.ai = make_account('SERVICE_IA')
        self.headers = {'Authorization': 'Bearer ' + tokens_for(self.journalist).access_token}
        self.app = create_app(); self.client = TestClient(self.app); self.client.__enter__()
        self.settings = get_settings().model_copy(update={'gemini_api_key': SecretStr('unit-test-key-only')})
        self.provider_settings = patch('app.integrations.ai.gemini.get_settings', return_value=self.settings)
        self.service_settings = patch('app.services.vision.get_settings', return_value=self.settings)
        self.provider_settings.start(); self.service_settings.start()
        self.addCleanup(self.provider_settings.stop); self.addCleanup(self.service_settings.stop)

    def tearDown(self):
        self.client.__exit__(None, None, None)

    def submit(self, body, **kwargs):
        return self.client.post('/api/v1/vision/video', headers=self.headers, json=body, **kwargs)

    def test_valid_result_is_private_persisted_idempotent_and_not_published(self):
        body = clip_body()
        with patch('app.integrations.ai.gemini._request', return_value={'status': 'completed', 'output_text': json.dumps(VALID)}) as provider:
            response = self.submit(body)
            self.assertEqual(response.status_code, 201, response.text)
            first = response.json()
            second = self.submit(body)
            self.assertEqual(second.json()['id'], first['id']); self.assertEqual(provider.call_count, 1)
            wire = provider.call_args.args[0]
            self.assertEqual(wire['model'], self.settings.gemini_vision_model)
            self.assertEqual(wire['input'][0]['type'], 'video')
            self.assertFalse(wire['store']); self.assertNotIn('key', wire)
        self.assertTrue(first['requires_human_review']); self.assertEqual(first['status'], 'completed')
        self.assertEqual(first['result']['analysis']['title'], VALID['title'])
        self.assertNotIn(body['video_base64'], response.text)
        self.assertEqual(self.client.get('/api/public/sync').json()['items'], [])
        self.assertEqual(self.client.get(f"/api/v1/vision/analyses/{first['id']}", headers=self.headers).status_code, 200)
        with system_session() as db:
            stored = db.get(MediaAnalysis, first['id'])
            self.assertEqual(stored.confidentiality, 'private'); self.assertEqual(stored.indice_indicatif, 'non_evalue')
            self.assertIsNone(db.scalar(select(Publication)))

    def test_authentication_roles_and_ownership(self):
        self.assertEqual(self.client.post('/api/v1/vision/video', json={}).status_code, 401)
        headers = {'Authorization': 'Bearer ' + tokens_for(self.reader).access_token}
        self.assertEqual(self.client.post('/api/v1/vision/video', json={}, headers=headers).status_code, 403)
        body = clip_body()
        with patch('app.integrations.ai.gemini._request', return_value={'status': 'completed', 'output_text': json.dumps(VALID)}):
            response = self.submit(body)
        identifier = response.json()['id']
        other = make_account('JOURNALISTE', email='other-video@example.invalid')
        headers = {'Authorization': 'Bearer ' + tokens_for(other).access_token}
        self.assertEqual(self.client.get(f'/api/v1/vision/analyses/{identifier}', headers=headers).status_code, 404)
        self.assertEqual(self.client.get('/api/v1/vision/analyses?capture_id=' + body['capture_id'], headers=headers).json(), [])

    def test_failures_and_timeouts_remain_failed_without_fallback(self):
        for failure in (gemini.GeminiUnavailableError('Moteur indisponible.'),
                        gemini.GeminiUnavailableError('Délai dépassé.', code='provider_timeout', http_status=504)):
            with self.subTest(code=failure.code):
                body = clip_body()
                with patch('app.integrations.ai.gemini._request', side_effect=failure):
                    response = self.submit(body)
                self.assertEqual(response.status_code, failure.http_status, response.text)
                with system_session() as db:
                    job = db.scalar(select(MediaAnalysis).where(MediaAnalysis.capture_key == body['capture_id'] + ':1'))
                    self.assertEqual(job.status, 'failed'); self.assertNotIn('analysis', job.result)
                    self.assertEqual(job.result['error']['code'], failure.code)
                self.assertEqual(self.submit(body).status_code, 409)

    def test_invalid_video_oversize_and_unknown_fields_are_rejected_without_echo(self):
        body = clip_body()
        for changes in ({'video_base64': 'PRIVATE_INVALID_DATA'}, {'duration_seconds': 20}, {'published': True}):
            response = self.submit({**body, **changes})
            self.assertEqual(response.status_code, 422, response.text)
            self.assertNotIn('PRIVATE_INVALID_DATA', response.text)
            self.assertNotIn('"input"', response.text)
        response = self.client.post('/api/v1/vision/video', headers={**self.headers, 'Content-Type': 'application/json'},
                                    content=b'x' * (6 * 1024 * 1024 + 1))
        self.assertEqual(response.status_code, 413)

    def test_changed_content_for_same_capture_is_rejected(self):
        body = clip_body()
        with patch('app.integrations.ai.gemini._request', return_value={'status': 'completed', 'output_text': json.dumps(VALID)}):
            self.assertEqual(self.submit(body).status_code, 201)
        body['video_base64'] = base64.b64encode(b'\x00\x00\x00\x18ftypisomOTHER_CLIP').decode()
        self.assertEqual(self.submit(body).status_code, 409)

    def test_bad_partial_and_editorial_results_are_not_accepted(self):
        results = [{'status': 'completed', 'output_text': '{invalid'}, {'status': 'incomplete', 'output_text': json.dumps(VALID)},
                   {'status': 'completed', 'output_text': json.dumps({**VALID, 'published': True})},
                   {'status': 'completed', 'output_text': json.dumps({**VALID, 'observations': [{'time_seconds': 9, 'description': 'Out of clip'}]})}]
        for result in results:
            with patch('app.integrations.ai.gemini._request', return_value=result):
                self.assertEqual(self.submit(clip_body()).status_code, 503)

    def test_real_http_transport_error_messages_do_not_echo_secret(self):
        for failure, code in ((HTTPError('https://example.invalid', 403, 'unit-test-key-only', {}, io.BytesIO()), 'gemini_http_403'),
                              (TimeoutError('unit-test-key-only'), 'provider_timeout'),
                              (URLError('unit-test-key-only'), 'provider_unavailable')):
            with patch('app.integrations.ai.gemini.urlopen', side_effect=failure):
                with self.assertRaises(gemini.GeminiUnavailableError) as caught:
                    gemini.analyze_video_clip(VideoClipRequest(**clip_body()))
            self.assertEqual(caught.exception.code, code); self.assertNotIn('unit-test-key-only', str(caught.exception))

    def test_missing_key_is_explicit_and_does_not_create_a_fake_analysis(self):
        settings = self.settings.model_copy(update={'gemini_api_key': SecretStr('')})
        with patch('app.services.vision.get_settings', return_value=settings):
            self.assertEqual(self.submit(clip_body()).status_code, 503)
        with system_session() as db:
            self.assertIsNone(db.scalar(select(MediaAnalysis)))


if __name__ == '__main__':
    unittest.main()
