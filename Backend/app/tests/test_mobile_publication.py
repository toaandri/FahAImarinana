"""Exercise the unchanged mobile publication payload against the API."""
import base64
import os
import unittest

os.environ['DATABASE_URL'] = os.environ.get('FANILO_TEST_DATABASE_URL', 'sqlite:///:memory:')
os.environ['ENVIRONMENT'] = 'test'
os.environ['JWT_SECRET'] = 'isolated-test-secret-at-least-thirty-two-bytes'
os.environ['AUTO_CREATE_TABLES'] = 'false'

import httpx
from app.main import create_app
from app.tests.fixtures import make_account, reset_schema, tokens_for


class MobilePublicationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        reset_schema()
        self.user = make_account('JOURNALISTE')
        self.token = tokens_for(self.user).access_token
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=create_app()), base_url='http://test')
        self.headers = {'Authorization': 'Bearer ' + self.token}

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_text_photo_video_and_media_access(self):
        samples = [(None, None), (b'\x89PNG\r\n\x1a\nphoto', 'image/png'),
                   (b'\x00\x00\x00\x18ftypqt  video', 'video/quicktime')]
        for data, mime in samples:
            payload = {'content': '[Sport] Titre\n\nTexte du reportage'}
            if data is not None:
                payload['media_base64'] = base64.b64encode(data).decode('ascii')
            response = await self.client.post('/api/v1/contributions/signals', headers=self.headers, json=payload)
            self.assertEqual(response.status_code, 201, response.text)
            self.assertEqual(response.json()['status'], 'submitted')
            media_url = f"/api/v1/contributions/{response.json()['id']}/media"
            media = await self.client.get(media_url, headers=self.headers)
            if data is None:
                self.assertEqual(media.status_code, 404)
            else:
                self.assertEqual(media.status_code, 200, media.text)
                self.assertEqual(media.content, data)
                self.assertEqual(media.headers['content-type'], mime)
                self.assertEqual(media.headers['cache-control'], 'private, no-store')
                self.assertEqual((await self.client.get(media_url)).status_code, 401)

        reviewer = make_account('JOURNALISTE', email='reviewer@example.invalid')
        reviewer_headers = {'Authorization': 'Bearer ' + tokens_for(reviewer).access_token}
        queue = await self.client.get('/api/v1/editorial/contributions', headers=reviewer_headers)
        self.assertEqual(queue.status_code, 200, queue.text)
        self.assertEqual(len(queue.json()), 3)
        self.assertEqual(sum(item['has_media'] for item in queue.json()), 2)
        reviewed = await self.client.get(f"/api/v1/editorial/contributions/{response.json()['id']}/media", headers=reviewer_headers)
        self.assertEqual(reviewed.content, samples[-1][0])
        outsider = make_account('JOURNALISTE', email='other@example.invalid', newsroom_id=2, dataset='quarantine')
        outside_headers = {'Authorization': 'Bearer ' + tokens_for(outsider).access_token}
        outside_queue = await self.client.get('/api/v1/editorial/contributions', headers=outside_headers)
        self.assertEqual(outside_queue.json(), [])
        outside_media = await self.client.get(f"/api/v1/editorial/contributions/{response.json()['id']}/media", headers=outside_headers)
        self.assertEqual(outside_media.status_code, 404)

    async def test_rejects_invalid_media(self):
        response = await self.client.post('/api/v1/contributions/signals', headers=self.headers,
                                          json={'content': 'Article', 'media_base64': 'invalid!'})
        self.assertEqual(response.status_code, 422)
