"""Profile photo persistence, replacement, validation and account isolation."""
import os
os.environ['DATABASE_URL'] = os.environ.get('FANILO_TEST_DATABASE_URL', 'sqlite:///:memory:')
os.environ['ENVIRONMENT'] = 'test'
os.environ['JWT_SECRET'] = 'isolated-test-secret-at-least-thirty-two-bytes'
os.environ['AUTO_CREATE_TABLES'] = 'false'
os.environ['GEMINI_API_KEY'] = ''
os.environ['OPENROUTER_API_KEY'] = ''

import base64
import struct
import unittest
import zlib

from fastapi.testclient import TestClient

from app.main import create_app
from app.models import User
from app.schemas.profile import MAX_PHOTO_BYTES
from app.tests.fixtures import make_account, reset_schema, system_session, tokens_for


def png(red):
    def chunk(kind, data):
        return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!2I5B', 1, 1, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(bytes([0, red, 0, 0]))) + chunk(b'IEND', b''))


class ProfilePhotoTests(unittest.TestCase):
    def setUp(self):
        reset_schema()
        self.user = make_account('JOURNALISTE', email='photo@example.invalid')
        self.other = make_account('JOURNALISTE', email='other-photo@example.invalid')
        self.foreign = make_account('JOURNALISTE', email='foreign-photo@example.invalid', newsroom_id=2, dataset='quarantine')
        self.headers = {'Authorization': 'Bearer ' + tokens_for(self.user).access_token}
        self.client = TestClient(create_app())
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)

    def upload(self, raw):
        return self.client.put('/api/v1/auth/me/photo', headers=self.headers,
                               json={'image_base64': base64.b64encode(raw).decode()})

    def test_photo_is_saved_replaced_and_reloaded_with_a_new_session(self):
        self.assertEqual(self.client.get('/api/v1/auth/me/photo', headers=self.headers).json(), {'photo': None})
        for raw in [png(0), png(255)]:
            response = self.upload(raw)
            self.assertEqual(response.status_code, 200, response.text)
            expected = {'photo': 'data:image/png;base64,' + base64.b64encode(raw).decode()}
            self.assertEqual(response.json(), expected)
            self.assertEqual(response.headers['cache-control'], 'no-store')
            # Fresh database session proves the image is not held in request/UI memory.
            with system_session() as db:
                self.assertEqual(db.get(User, self.user.id).profile_photo, raw)
            new_headers = {'Authorization': 'Bearer ' + tokens_for(self.user).access_token}
            reloaded = self.client.get('/api/auth/me/photo', headers=new_headers)
            self.assertEqual(reloaded.json(), expected)
            self.assertEqual(reloaded.headers['cache-control'], 'no-store')

    def test_photos_are_private_to_the_authenticated_account(self):
        self.assertEqual(self.upload(png(10)).status_code, 200)
        for account in [self.other, self.foreign]:
            headers = {'Authorization': 'Bearer ' + tokens_for(account).access_token}
            self.assertEqual(self.client.get('/api/v1/auth/me/photo', headers=headers).json(), {'photo': None})
            changed = self.client.put('/api/v1/auth/me/photo', headers=headers,
                                      json={'image_base64': base64.b64encode(png(20)).decode(), 'user_id': self.user.id})
            self.assertEqual(changed.status_code, 422)
        for method in ['get', 'put']:
            response = getattr(self.client, method)('/api/v1/auth/me/photo')
            self.assertEqual(response.status_code, 401)

    def test_invalid_and_oversized_uploads_preserve_the_existing_photo(self):
        raw = png(30)
        self.assertEqual(self.upload(raw).status_code, 200)
        for encoded in ['invalid!!!', base64.b64encode(b'<svg></svg>').decode(),
                        base64.b64encode(raw + b'0' * (MAX_PHOTO_BYTES + 1 - len(raw))).decode()]:
            response = self.client.put('/api/v1/auth/me/photo', headers=self.headers, json={'image_base64': encoded})
            self.assertEqual(response.status_code, 422, response.text)
        response = self.client.put('/api/v1/auth/me/photo', headers=self.headers,
                                   content=b'x' * (3 * 1024 * 1024 + 1))
        self.assertEqual(response.status_code, 413)
        with system_session() as db:
            self.assertEqual(db.get(User, self.user.id).profile_photo, raw)


if __name__ == '__main__':
    unittest.main()
