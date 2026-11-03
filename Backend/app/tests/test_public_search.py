import os
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

os.environ['DATABASE_URL'] = os.environ.get('FANILO_TEST_DATABASE_URL', 'sqlite:///:memory:')
os.environ['ENVIRONMENT'] = 'test'
os.environ['JWT_SECRET'] = 'isolated-test-secret-at-least-thirty-two-bytes'
os.environ['AUTO_CREATE_TABLES'] = 'false'

import httpx
from app.main import create_app
from app.models import Publication
from app.tests.fixtures import make_account, reset_schema, system_session


class PublicSearchTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        reset_schema()
        user = make_account('JOURNALISTE')
        now = datetime.now(timezone.utc)
        with system_session() as db:
            common = dict(newsroom_id=1, dataset='real', id_journaliste_validateur=user.id,
                categorie='Sport', statut_verification='Vrai', horodatage_validation=now,
                contenu_optimise_sms='SMS', published_at=now)
            public = Publication(**common, titre_final='<script>titre</script>', corps_article='Texte public & vérifié',
                                 status='published', confidentiality='public')
            private = Publication(**common, titre_final='DRAFT_SECRET', corps_article='privé',
                                  status='published', confidentiality='private')
            db.add_all([public, private]); db.commit()
            self.public_id, self.private_id = public.id, private.id
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=create_app()), base_url='http://test')

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_public_page_and_sitemap_only_expose_validated_public_articles(self):
        page = await self.client.get('/api/v1/public/article', params={'id': self.public_id})
        self.assertEqual(page.status_code, 200, page.text)
        self.assertIn('&lt;script&gt;titre&lt;/script&gt;', page.text)
        self.assertNotIn('<script>titre</script>', page.text)
        self.assertEqual((await self.client.get('/api/v1/public/article', params={'id': self.private_id})).status_code, 404)
        with patch('app.core.config.get_settings', return_value=SimpleNamespace(public_site_url='https://demo.example')):
            sitemap = await self.client.get('/api/v1/public/sitemap.xml')
        self.assertEqual(sitemap.status_code, 200, sitemap.text)
        self.assertIn(f'https://demo.example/api/v1/public/article?id={self.public_id}', sitemap.text)
        self.assertNotIn(f'id={self.private_id}', sitemap.text)

    async def test_sitemap_requires_public_https_address(self):
        with patch('app.core.config.get_settings', return_value=SimpleNamespace(public_site_url='')):
            self.assertEqual((await self.client.get('/api/v1/public/sitemap.xml')).status_code, 503)
