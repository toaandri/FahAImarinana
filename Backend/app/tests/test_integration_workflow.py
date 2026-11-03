"""Real HTTP local workflow; no simulated external Maharavo/SMS delivery."""
import os
os.environ['DATABASE_URL'] = os.environ.get('FANILO_TEST_DATABASE_URL','sqlite:///:memory:')
os.environ['ENVIRONMENT'] = 'test'
os.environ['JWT_SECRET'] = 'isolated-test-secret-at-least-thirty-two-bytes'
os.environ['AUTO_CREATE_TABLES'] = 'false'
from datetime import datetime, timezone
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError
from app.main import create_app
from app.tests.fixtures import reset_schema, make_account, tokens_for, system_session
from app.models import DraftRevision, Newsroom
from app.core.constants import SECURITY_RESPONSE

FINAL = {'titre_final':'Vérification eau', 'corps_article':'Résultat validé concernant eau.',
         'categorie':'Société', 'statut_verification':'Vrai','contenu_optimise_sms':'Résumé approuvé eau.'}


class IntegrationWorkflowTests(unittest.TestCase):
    def setUp(self):
        reset_schema()
        self.users={
            'JOURNALISTE':make_account('JOURNALISTE',email='workflow-journalist@example.invalid'),
            'SERVICE_IA':make_account('SERVICE_IA'),
        }
        self.headers={role:{'Authorization':'Bearer '+tokens_for(user).access_token} for role,user in self.users.items()}
        self.app=create_app(); self.client=TestClient(self.app); self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None,None,None)

    def req(self,method,path,body=None,role='JOURNALISTE',status=200):
        result=self.client.request(method,'/api/v1'+path,headers=self.headers[role],json=body)
        self.assertEqual(result.status_code,status,result.text)
        return result.json()

    def case(self):
        return self.req('POST','/cases',{'title':'Dossier eau'},status=201)

    def prepare(self):
        case=self.case(); cid=case['id']
        claim=self.req('POST',f'/cases/{cid}/claims',{'statement':'Une affirmation eau'},status=201)
        source=self.req('POST','/sources',{'nom':'Document original','type':'Web','url':'https://source.example.invalid'},status=201)
        evidence=self.req('POST',f'/cases/{cid}/evidence',{'title':'Document eau','kind':'document','content':'PRIVATE_PIECE eau',
            'source_id':source['id'],'original_url':'https://source.example.invalid/document'},status=201)
        self.req('POST',f"/cases/{cid}/claims/{claim['id']}/evidence",{'evidence_id':evidence['id'],'stance':'context'},status=201)
        signal=self.req('POST','/signals/ingest',{'case_id':cid,'source_id':source['id'],'contenu':'Signal eau',
            'url_origine':'https://source.example.invalid/item','horodatage_publication':datetime.now(timezone.utc).isoformat()},status=201)
        draft=self.req('POST',f'/cases/{cid}/drafts',{'signal_id':signal['id'],'claim_id':claim['id'],
            'titre_suggere':'Projet humain','synthese_ia':'PRIVATE_DRAFT'},status=201)
        return cid,claim,evidence,draft

    def test_complete_local_editorial_path(self):
        cid,claim,evidence,draft=self.prepare(); did=draft['id']
        self.assertEqual(self.req('GET',f'/cases/{cid}/claims')[0]['verdict'],'unknown')
        self.assertEqual(len(self.req('GET',f'/cases/{cid}/evidence')),1)
        job=self.req('POST',f'/cases/{cid}/research',{'question':'eau'},status=201)
        self.assertEqual(job['modele'],'local-document-search-v1')
        self.assertEqual(job['citations'][0]['evidence_id'],evidence['id'])
        self.assertEqual(len(self.req('GET',f'/cases/{cid}/research')),1)
        self.assertEqual(self.client.get('/api/public/articles').json(),[])
        self.req('POST',f'/workflow/drafts/{did}/review',{'expected_version':1,'decision':'reviewed','notes':'Pièces relues'})
        self.req('POST',f'/workflow/drafts/{did}/validate',{**FINAL,'expected_version':1})
        article=self.req('POST',f'/workflow/drafts/{did}/publish',FINAL)
        self.assertEqual(self.client.get('/api/public/articles').json()[0]['id'],article['id'])
        sms=self.client.post('/api/sms/citizen',json={'numero_expediteur':'+261000000','message':'eau'}).json()
        self.assertEqual(sms['message'],FINAL['contenu_optimise_sms'])
        history=self.req('GET',f'/drafts/{did}/history')
        self.assertEqual([row['event'] for row in history],['created','reviewed','validated','published'])
        self.assertTrue(all(row['actor_id'] for row in history))

    def test_conflicts_permissions_and_cross_case_evidence(self):
        cid,claim,evidence,draft=self.prepare(); other=self.case()['id']
        other_claim=self.req('POST',f'/cases/{other}/claims',{'statement':'Autre'},status=201)
        self.req('POST',f"/cases/{other}/claims/{other_claim['id']}/evidence",{'evidence_id':evidence['id']},status=404)
        self.req('POST',f"/cases/{cid}/claims/{claim['id']}/evidence",{'evidence_id':evidence['id']},status=409)
        for role in ('SERVICE_IA',):
            self.req('GET',f'/cases/{cid}/evidence',role=role,status=403)
        self.req('POST',f'/cases/{cid}/claims',{'statement':'Non','verdict':'confirmed'},status=422)
        self.req('POST',f'/workflow/drafts/{draft["id"]}/validate',{**FINAL,'expected_version':1},role='SERVICE_IA',status=403)
        self.req('POST',f'/workflow/drafts/{draft["id"]}/publish',FINAL,role='SERVICE_IA',status=403)

    def test_update_pagination_archive_and_explicit_no_result(self):
        case=self.case(); cid=case['id']
        updated=self.req('PATCH',f'/cases/{cid}',{'title':'Nouveau titre','expected_updated_at':case['updated_at']})
        self.assertEqual(updated['title'],'Nouveau titre')
        self.req('PATCH',f'/cases/{cid}',{'description':'Deuxième modification',
            'expected_updated_at':updated['updated_at']})
        self.req('PATCH',f'/cases/{cid}',{'title':'Version périmée','expected_updated_at':case['updated_at']},status=409)
        self.case()
        self.assertEqual(len(self.req('GET','/cases?limit=1&offset=1')),1)
        self.assertEqual(len(self.req('GET','/cases?q=Nouveau')),1)
        self.assertEqual(self.req('GET','/cases?q=%25'),[])
        self.req('POST',f'/cases/{cid}/archive')
        self.req('POST',f'/cases/{cid}/claims',{'statement':'Interdit'},status=409)
        result=self.client.post('/api/sms/citizen',json={'numero_expediteur':'+261000000','message':'PRIVATE_PIECE'}).json()
        self.assertEqual(result['message'],SECURITY_RESPONSE)

    def test_history_is_immutable_and_edit_requires_revalidation(self):
        cid,claim,evidence,draft=self.prepare(); did=draft['id']
        self.req('POST',f'/workflow/drafts/{did}/validate',{**FINAL,'expected_version':1})
        changed=self.req('PATCH',f'/drafts/{did}',{'expected_version':1,'synthese_ia':'New text'})
        self.assertIsNone(changed['validated_version'])
        self.req('POST',f'/workflow/drafts/{did}/publish',FINAL,status=409)
        history=self.req('GET',f'/drafts/{did}/history')
        self.assertEqual(history[-2]['snapshot']['synthese_ia'],'PRIVATE_DRAFT')
        self.assertEqual(history[-1]['snapshot']['synthese_ia'],'New text')
        with system_session() as db:
            with self.assertRaises(DBAPIError):
                db.execute(text('UPDATE draft_revisions SET version=99'))
            db.rollback()

    def test_other_newsroom_cannot_access_cases(self):
        cid=self.case()['id']
        with system_session() as db:
            db.add(Newsroom(id=3,slug='other-real',name='Other newsroom',dataset='real')); db.commit()
        user=make_account('JOURNALISTE',email='other@example.invalid',newsroom_id=3)
        headers={'Authorization':'Bearer '+tokens_for(user).access_token}
        for suffix in ('','/claims','/evidence','/drafts','/research','/sources'):
            result=self.client.get('/api/v1/cases/'+str(cid)+suffix,headers=headers)
            self.assertEqual(result.status_code,404,result.text)

    def test_public_sync_versions_corrections_withdrawals_and_privacy(self):
        empty=self.client.get('/api/v1/public/sync').json()
        self.assertTrue(empty['complete']); self.assertEqual(empty['items'],[])
        cid,claim,evidence,draft=self.prepare(); did=draft['id']
        self.assertEqual(self.client.get('/api/v1/public/sync').json()['items'],[])
        self.req('POST',f'/workflow/drafts/{did}/validate',{**FINAL,'expected_version':1})
        article=self.req('POST',f'/workflow/drafts/{did}/publish',FINAL); aid=article['id']
        response=self.client.get('/api/v1/public/sync'); first=response.json()
        self.assertEqual(first['strategy'],'replace'); self.assertEqual(first['items'][0]['id'],aid)
        self.assertNotIn('PRIVATE_',response.text)
        self.assertNotIn('draft_id',response.text)
        unchanged=self.client.get('/api/v1/public/sync',headers={'If-None-Match':response.headers['etag']})
        self.assertEqual(unchanged.status_code,304)
        self.req('POST',f'/workflow/publications/{aid}/correct',{**FINAL,'corps_article':'Texte corrigé eau','reason':'Nouvelle pièce examinée'})
        corrected=self.client.get('/api/v1/public/sync').json()
        self.assertNotEqual(first['items'][0]['content_version'],corrected['items'][0]['content_version'])
        self.req('POST',f'/workflow/publications/{aid}/withdraw',{'reason':'Réexamen nécessaire'})
        self.assertEqual(self.client.get('/api/v1/public/sync').json()['items'],[])
        sms=self.client.post('/api/sms/citizen',json={'numero_expediteur':'+261000000','message':'eau'}).json()
        self.assertEqual(sms['message'],'Aucune vérification publiée trouvée pour cette demande.')

    def test_request_limits_share_legacy_and_v1_and_private_cache_is_disabled(self):
        from app.middleware.rate_limit import RateLimitMiddleware
        limited=RateLimitMiddleware(self.app,auth_limit=2,public_limit=2)
        with TestClient(limited) as client:
            self.assertEqual(client.get('/api/public/sync').status_code,200)
            self.assertEqual(client.get('/api/v1/public/sync').status_code,200)
            response=client.get('/api/public/sync')
            self.assertEqual(response.status_code,429)
            self.assertIn('retry-after',response.headers)
        response=self.client.get('/api/v1/cases',headers=self.headers['JOURNALISTE'])
        self.assertEqual(response.headers['cache-control'],'no-store')

    def test_durable_queue_success_failure_cancellation_and_recovery(self):
        from unittest.mock import patch
        from app.database import SessionLocal
        from app.repositories.identity import UserRepository
        from app.services.tasks import run_one,fail_stale
        from app.core.security import now
        from app.models import ResearchJob
        from datetime import timedelta
        cid,claim,evidence,draft=self.prepare()
        def queued():
            return self.req('POST',f'/cases/{cid}/research/tasks',{'question':'eau'},status=202)['id']
        first=queued()
        self.assertEqual(self.req('GET',f'/research-jobs/{first}')['statut'],'queued')
        def work():
            with SessionLocal() as db:
                worker=UserRepository(db).get_for_auth(self.users['SERVICE_IA'].id)
                result=run_one(db,worker)
                return result.statut if result else None
        self.assertEqual(work(),'terminee')
        self.assertEqual(self.req('GET',f'/research-jobs/{first}')['citations'][0]['evidence_id'],evidence['id'])
        second=queued()
        with patch('app.services.tasks.search_case_pieces',side_effect=RuntimeError('PRIVATE_FAILURE')):
            self.assertEqual(work(),'echouee')
        failed=self.req('GET',f'/research-jobs/{second}')
        self.assertNotIn('PRIVATE_FAILURE',str(failed)); self.assertIsNotNone(failed['fin'])
        third=queued()
        self.assertEqual(self.req('POST',f'/research-jobs/{third}/cancel')['statut'],'cancelled')
        self.req('POST',f'/research-jobs/{first}/cancel',status=409)
        self.assertIsNone(work())
        fourth=queued()
        with system_session() as db:
            job=db.get(ResearchJob,fourth); job.statut='en_cours'; job.debut=now()-timedelta(hours=1); db.commit()
        with SessionLocal() as db:
            worker=UserRepository(db).get_for_auth(self.users['SERVICE_IA'].id)
            self.assertEqual(fail_stale(db,worker),1)
        self.assertEqual(self.req('GET',f'/research-jobs/{fourth}')['statut'],'echouee')


if __name__=='__main__':
    unittest.main()
