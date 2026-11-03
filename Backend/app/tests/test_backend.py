"""HTTP regression tests on an isolated database; no network calls or provider keys."""
import os
# Use an explicitly disposable test URL. Never reuse DATABASE_URL from a developer's shell.
os.environ['DATABASE_URL'] = os.environ.get('FANILO_TEST_DATABASE_URL', 'sqlite:///:memory:')
os.environ['ENVIRONMENT'] = 'test'
os.environ['JWT_SECRET'] = 'isolated-test-secret-at-least-thirty-two-bytes'
os.environ['GEMINI_API_KEY'] = ''
os.environ['OPENROUTER_API_KEY'] = ''
os.environ['AUTO_CREATE_TABLES'] = 'false'
os.environ['ALLOW_PUBLIC_REGISTRATION'] = 'true'

import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from app.main import create_app
from app.database import Base, engine
from app.tests.fixtures import reset_schema, system_session as SessionLocal, make_account, tokens_for
from app.core.config import Settings, get_settings
from app.models import ArticleCertifie, DocumentRecherche, DraftIA, Utilisateur
from app.core.security import create_access_token
from app.integrations.ai.gemini import GeminiUnavailableError, generate_draft
from app.integrations.maharavo.research import get_research_provider
from app.integrations.sms.gateway import get_sms_gateway


class BackendTests(unittest.TestCase):
    def setUp(self):
        reset_schema()
        self.app = create_app()
        self.client = TestClient(self.app)
        self.client.__enter__()
        self.journalist=make_account('JOURNALISTE',email='editor@example.invalid')
        self.editor=make_account('EDITEUR')
        self.admin=make_account('ADMINISTRATEUR')
        self.ia=make_account('SERVICE_IA')
        def headers(user): return {'Authorization':'Bearer '+tokens_for(user).access_token}
        self.headers=headers(self.journalist)
        self.editor_headers=headers(self.editor)
        self.admin_headers=headers(self.admin)
        self.ia_headers=headers(self.ia)

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.app.dependency_overrides.clear()

    def signal(self):
        response = self.client.post('/api/sources', headers=self.admin_headers, json={
            'nom': 'Source', 'type': 'Web', 'url': 'https://example.invalid/'})
        self.assertEqual(response.status_code, 201, response.text)
        response = self.client.post('/api/signals/ingest', headers=self.headers, json={
            'source_id': response.json()['id'], 'contenu': 'Manifestation annoncée dans la capitale',
            'url_origine': 'https://example.invalid/item',
            'horodatage_publication': datetime.now(timezone.utc).isoformat(),
            'nombre_interactions': 600})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()['id']

    def draft(self):
        signal_id = self.signal()
        response = self.client.post(f'/api/signals/{signal_id}/analyze', json={}, headers=self.headers)
        self.assertEqual(response.status_code, 201, response.text)
        return signal_id, response.json()['id']

    def publish(self, draft_id):
        payload={'titre_final':'Manifestation démentie','corps_article':'La manifestation annoncée est fausse.',
            'categorie':'Société','statut_verification':'Faux','contenu_optimise_sms':'Information démentie.'}
        self.client.post(f'/api/workflow/drafts/{draft_id}/validate',headers=self.editor_headers,json={**payload,'expected_version':1})
        return self.client.post(f'/api/workflow/drafts/{draft_id}/publish',headers=self.editor_headers,json=payload)

    def test_legacy_and_v1_routes_have_identical_contracts(self):
        schema = self.app.openapi()
        # The frozen manifest contains all HTTP operations before the refactor.
        manifest = json.loads(Path(__file__).with_name('legacy_contract.json').read_text())
        for path, methods in manifest.items():
            target = schema['paths'][path.replace('/api/', '/api/v1/', 1)]
            for method, expected in methods.items():
                self.assertIn(method, target)
                responses=set(expected['responses'])
                if path=='/api/public/articles' and method=='get':
                    responses.add('422')  # added bounded pagination query validation
                self.assertEqual(set(target[method]['responses']), responses)
                self.assertEqual(bool(target[method].get('security')), expected['auth'])
        self.assertEqual(self.client.get('/api/health').json(), self.client.get('/api/v1/health').json())
        self.assertEqual(self.client.get('/api/public/articles').json(), self.client.get('/api/v1/public/articles').json())
        for model, fields in json.loads(Path(__file__).with_name('legacy_response_fields.json').read_text()).items():
            self.assertTrue(set(fields)<=set(schema['components']['schemas'][model]['properties']))

    def test_publication_sms_search_and_duplicate_conflicts(self):
        signal_id, draft_id = self.draft()
        self.assertEqual(self.client.get('/api/public/articles').json(), [])
        self.assertEqual(self.publish(draft_id).status_code, 200)
        self.assertEqual(self.publish(draft_id).status_code, 409)
        self.assertEqual(self.client.post(f'/api/signals/{signal_id}/analyze', json={}, headers=self.headers).status_code, 409)
        self.assertEqual(len(self.client.get('/api/public/articles').json()), 1)
        result = self.client.post('/api/sms/citizen', json={'numero_expediteur': '+261000000', 'message': 'manifestation'})
        self.assertEqual(result.json(), {'message': 'Information démentie.', 'statut': 'Trouve'})
        result = self.client.post('/api/copilot/research', headers=self.headers, json={'question': 'manifestation'})
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(len(result.json()['citations']), 1)
        cross = self.client.post(f'/api/workflow/signals/{signal_id}/cross-check', headers=self.headers).json()
        self.assertEqual(cross['score_concordance'], 0)
        self.assertFalse(cross['sources'][0]['concorde'])
        self.assertFalse(cross['sources'][0]['officielle'])

    def test_publication_rolls_back_if_indexing_fails(self):
        _, draft_id = self.draft()
        with patch('app.services.editorial.index_certified_article', side_effect=RuntimeError('test')):
            with self.assertRaises(RuntimeError):
                self.publish(draft_id)
        with SessionLocal() as db:
            self.assertEqual(db.scalar(select(func.count(ArticleCertifie.id))), 0)
            self.assertEqual(db.get(DraftIA, draft_id).statut, 'En_Attente')
        self.assertEqual(self.publish(draft_id).status_code, 200)

    def test_authentication_validation_and_normalized_duplicates(self):
        self.assertEqual(self.client.post('/api/sources', json={}).status_code, 401)
        self.assertEqual(self.client.get('/api/drafts/1').status_code, 401)
        bad = self.client.post('/api/auth/register', json={'email': 'bad', 'mot_de_passe': 'é' * 40})
        self.assertEqual(bad.status_code, 422)
        duplicate = self.client.post('/api/auth/register', json={
            'email': ' EDITOR@EXAMPLE.INVALID ', 'mot_de_passe': 'password123'})
        self.assertEqual(duplicate.status_code, 403)
        invalid = self.client.get('/api/drafts/1', headers={'Authorization': 'Bearer invalid'})
        self.assertEqual(invalid.status_code, 401)
        with patch('app.services.auth.get_settings', return_value=Settings(allow_public_registration=False)):
            result = self.client.post('/api/auth/register', json={
                'email': 'new@example.invalid', 'mot_de_passe': 'password123'})
            self.assertEqual(result.status_code, 403)

    def test_chat_sessions_are_private_and_messages_persist(self):
        session = self.client.post('/api/copilot/sessions', headers=self.headers, json={'titre': 'Enquête'}).json()
        other=make_account('JOURNALISTE',email='other@example.invalid')
        other_headers={'Authorization':'Bearer '+tokens_for(other).access_token}
        path = f"/api/copilot/sessions/{session['id']}"
        self.assertEqual(self.client.get(path + '/messages', headers=other_headers).status_code, 404)
        self.assertEqual(self.client.post(path + '/ask', headers=other_headers, json={'question': 'Question inconnue'}).status_code, 404)
        self.assertEqual(self.client.post(path + '/ask', headers=self.headers, json={'question': 'Question inconnue'}).status_code, 200)
        self.assertEqual(len(self.client.get(path + '/messages', headers=self.headers).json()), 2)

    def test_worker_processes_only_pending_urgent_signals(self):
        self.signal()
        first = self.client.post('/api/workflow/process-pending', headers=self.ia_headers)
        self.assertEqual(first.json(), {'processed': 1})
        self.assertEqual(self.client.post('/api/workflow/process-pending', headers=self.ia_headers).json(), {'processed': 0})

    def test_websocket_requires_auth_and_alert_gateway_is_injectable(self):
        from starlette.websockets import WebSocketDisconnect
        with self.assertRaises(WebSocketDisconnect):
            with self.client.websocket_connect('/api/alerts/ws'):
                pass
        signal_id = self.signal()
        class Gateway:
            def send(self, phone, message):
                raise AssertionError('No contact configured')
        self.app.dependency_overrides[get_sms_gateway] = Gateway
        token = self.headers['Authorization'][7:]
        with self.client.websocket_connect('/api/alerts/ws', subprotocols=['bearer', token]) as ws:
            response = self.client.post(f'/api/copilot/alerts/signal/{signal_id}', headers=self.editor_headers)
            self.assertEqual(response.status_code, 200, response.text)
            payload = ws.receive_json()
            self.assertEqual(payload, {'type': 'alert', 'signal_id': signal_id, 'sent_count': 0})

    def test_maharavo_capabilities_are_preserved(self):
        research = self.client.post('/api/maharavo/research', headers=self.headers, json={'sujet': 'Sujet de recherche'})
        self.assertEqual(research.status_code, 503, research.text)
        from app.models import ResearchJob
        with SessionLocal() as db:
            self.assertEqual(db.scalar(select(func.count(ResearchJob.id))), 0)
        media = self.client.post('/api/maharavo/media-analysis', headers=self.headers, json={
            'type_media': 'image', 'reference_originale': 'preuve.jpg', 'empreinte_sha256': 'a' * 64,
            'outil': 'Inspection humaine', 'version_outil': '1'})
        self.assertEqual(media.status_code, 201, media.text)
        confidence = self.client.post('/api/maharavo/confidence', headers=self.headers, json={
            'objet_type': 'media', 'objet_id': media.json()['id'], 'identite_source': 'faible',
            'solidite_preuves': 'faible', 'validation_editoriale': 'non_evalue',
            'conclusion': 'non_verifiable', 'justification': 'Preuves insuffisantes'})
        self.assertEqual(confidence.status_code, 201, confidence.text)

    def test_unknown_sms_and_generated_json_validation(self):
        result = self.client.post('/api/sms/citizen', json={'numero_expediteur': '+261000000', 'message': 'inconnu'})
        self.assertEqual(result.json()['statut'], 'Non_Trouve')
        with patch('app.integrations.ai.gemini._request', return_value={'output_text': '{"titre":"incomplet"}'}):
            with self.assertRaises(GeminiUnavailableError):
                generate_draft('texte', 'date', [])

    @unittest.skipUnless(engine.dialect.name == 'postgresql', 'PostgreSQL row locks required')
    def test_concurrent_publications_create_one_article(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from app.schemas import PublishRequest
        from app.services.editorial import publish_draft
        from app.core.errors import ConflictError
        _, draft_id = self.draft()
        self.client.post(f'/api/workflow/drafts/{draft_id}/validate',headers=self.editor_headers,json={
            'titre_final':'Titre','corps_article':'Contenu','categorie':'Audit','statut_verification':'Vrai',
            'contenu_optimise_sms':'Résumé','expected_version':1})
        barrier = Barrier(2)
        def publish_in_session():
            with SessionLocal() as db:
                draft = db.get(DraftIA, draft_id)
                user = db.scalar(select(Utilisateur).where(Utilisateur.role=='EDITEUR'))
                barrier.wait(timeout=10)
                try:
                    publish_draft(db, draft, user, PublishRequest(
                        titre_final='Titre', corps_article='Contenu', categorie='Audit',
                        statut_verification='Vrai', contenu_optimise_sms='Résumé'))
                    return 'published'
                except ConflictError:
                    db.rollback()
                    return 'conflict'
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: publish_in_session(), range(2)))
        self.assertCountEqual(results, ['published', 'conflict'])
        with SessionLocal() as db:
            self.assertEqual(db.scalar(select(func.count(ArticleCertifie.id))), 1)
            self.assertEqual(db.scalar(select(func.count(DocumentRecherche.id))), 1)

    def test_production_configuration_rejects_unsafe_settings(self):
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            Settings(environment='production', allow_public_registration=False)
        with self.assertRaises(ValidationError):
            Settings(environment='production', jwt_secret='a' * 48, allow_public_registration=True)
        settings = Settings(environment='production', jwt_secret='a' * 48, allow_public_registration=False, public_database_url='postgresql+psycopg://public_reader@localhost/fanilo')
        self.assertFalse(settings.auto_create_tables)


if __name__ == '__main__':
    unittest.main()
