"""Role matrix, invitations, sessions, token rotation and editorial invariants."""
import os
os.environ['DATABASE_URL']=os.environ.get('FANILO_TEST_DATABASE_URL','sqlite:///:memory:')
os.environ['ENVIRONMENT']='test'
os.environ['JWT_SECRET']='isolated-test-secret-at-least-thirty-two-bytes'
os.environ['GEMINI_API_KEY']=''
os.environ['AUTO_CREATE_TABLES']='false'
os.environ['ALLOW_PUBLIC_REGISTRATION']='false'
import unittest
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from fastapi.testclient import TestClient
from sqlalchemy import select
from jose import jwt
from app.main import create_app
from app.database import engine,SessionLocal
from app.tests.fixtures import reset_schema,make_account,tokens_for,system_session
from app.models import User,Source,Signal,Draft,Case,RefreshToken,Invitation
from app.core.rbac import Role,Permission as P,ROLE_PERMISSIONS
from app.core.config import get_settings
from app.core.errors import ForbiddenError,AuthenticationError
from app.core.security import password_matches,now
from app.services.auth import secret_hash,refresh_tokens

FINAL={'titre_final':'Approved title','corps_article':'Approved body','categorie':'Test',
       'statut_verification':'Vrai','contenu_optimise_sms':'Approved SMS'}


class AuthRBACTests(unittest.TestCase):
    def setUp(self):
        reset_schema()
        self.users={role:make_account(role.value) for role in Role}
        self.tokens={role:tokens_for(user) for role,user in self.users.items()}
        with system_session() as db:
            source=Source(nom='Test source',type='Web',url='https://source.example.invalid')
            db.add(source); db.flush()
            case=Case(title='Private case',created_by_id=self.users[Role.JOURNALISTE].id)
            db.add(case); db.flush()
            signal=Signal(source_id=source.id,case_id=case.id,contenu_brut='A signal',contenu_normalise='A signal',
                url_origine='https://source.example.invalid/item',horodatage_publication=now())
            db.add(signal); db.flush()
            draft=Draft(signal_id=signal.id,case_id=case.id,titre_suggere='Private draft',synthese_ia='Private analysis',
                score_credibilite_indicatif=0,horodatage=now())
            db.add(draft); db.commit()
            self.case_id=case.id; self.signal_id=signal.id; self.draft_id=draft.id
        self.app=create_app(); self.client=TestClient(self.app); self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None,None,None)

    def req(self,role,method,path,body=None):
        return self.client.request(method,'/api'+path,headers={
            'Authorization':'Bearer '+self.tokens[Role(role)].access_token},json=body)

    def invite(self,email):
        result=self.req('ADMINISTRATEUR','POST','/admin/invitations',{'email':email,'role':'JOURNALISTE'})
        self.assertEqual(result.status_code,201,result.text)
        return result.json()['invitation_token']

    def test_all_six_roles_have_only_explicit_grants(self):
        operations=[
            ('POST','/cases',{'title':'New case'},{'JOURNALISTE'},201),
            ('GET','/cases',None,{'JOURNALISTE','EDITEUR'},200),
            ('POST',f'/cases/{self.case_id}/evidence',{'title':'Proof','kind':'document','content':'Private'},{'JOURNALISTE'},201),
            ('POST','/copilot/research',{'question':'Test question'},{'JOURNALISTE','SERVICE_IA'},200),
            ('POST',f'/signals/{self.signal_id}/analyze',{}, {'JOURNALISTE','SERVICE_IA'},409),
            ('GET',f'/drafts/{self.draft_id}',None,{'JOURNALISTE','EDITEUR'},200),
            ('GET','/admin/users',None,{'ADMINISTRATEUR'},200),
            ('GET','/sources',None,{'ADMINISTRATEUR'},200),
            ('POST','/sources',{'nom':'Managed source','type':'Web','url':'https://managed.example.invalid'},{'ADMINISTRATEUR'},201),
            ('PUT','/admin/settings/research_result_limit',{'value':3},{'ADMINISTRATEUR'},200),
            ('POST','/contributions/signals',{'content':'A report'},{'CONTRIBUTEUR'},201),
            ('POST','/workflow/process-pending',None,{'SERVICE_IA'},200),
            ('POST',f'/workflow/drafts/{self.draft_id}/review',{'expected_version':1,'decision':'reviewed','notes':'Reviewed'},{'EDITEUR'},200),
            ('POST',f'/workflow/drafts/{self.draft_id}/validate',{**FINAL,'expected_version':1},{'EDITEUR'},200),
            ('POST',f'/workflow/drafts/{self.draft_id}/publish',FINAL,{'EDITEUR'},200),
        ]
        for method,path,body,allowed,status in operations:
            order=[r for r in Role if r not in allowed]+[r for r in Role if r in allowed]
            for role in order:
                with self.subTest(role=role,method=method,path=path):
                    result=self.req(role,method,path,body)
                    self.assertEqual(result.status_code,status if role in allowed else 403,result.text)
        for role in Role:
            self.assertEqual(self.req(role,'GET','/public/articles').status_code,200)
        self.assertNotIn(P.PUBLISH,ROLE_PERMISSIONS[Role.ADMINISTRATEUR])

    def test_editorial_functions_reject_every_role_except_editor_without_http(self):
        from app.services.editorial import publish_draft
        from app.services.draft_workflow import validate_draft
        from app.services.publications import correct_publication,withdraw_publication
        from app.schemas import PublishRequest
        from app.schemas.editorial import ValidateDraftRequest
        for role in Role:
            if role==Role.EDITEUR: continue
            with system_session() as db:
                user=db.get(User,self.users[role].id); draft=db.get(Draft,self.draft_id)
                calls=[lambda:validate_draft(db,user,draft.id,ValidateDraftRequest(**FINAL,expected_version=1)),
                    lambda:publish_draft(db,draft,user,PublishRequest(**FINAL)),
                    lambda:correct_publication(db,user,999,PublishRequest(**FINAL),reason='Test'),
                    lambda:withdraw_publication(db,user,999,reason='Test')]
                for call in calls:
                    with self.subTest(role=role):
                        with self.assertRaises(ForbiddenError): call()

    def test_controlled_single_use_invitation_and_password_hash(self):
        body={'email':'invited@example.invalid','mot_de_passe':'password123'}
        self.assertEqual(self.client.post('/api/auth/register',json=body).status_code,403)
        self.assertEqual(self.client.post('/api/auth/register',json={**body,'role':'EDITEUR'}).status_code,422)
        secret=self.invite(body['email'])
        self.assertEqual(self.client.post('/api/auth/register',json={**body,'email':'wrong@example.invalid','invitation_token':secret}).status_code,403)
        result=self.client.post('/api/auth/register',json={**body,'invitation_token':secret})
        self.assertEqual(result.status_code,201,result.text)
        self.assertEqual(result.headers['cache-control'],'no-store')
        self.assertEqual(self.client.post('/api/auth/register',json={**body,'invitation_token':secret}).status_code,403)
        with system_session() as db:
            user=db.scalar(select(User).where(User.email==body['email']))
            self.assertEqual(user.role,'JOURNALISTE')
            self.assertTrue(user.mot_de_passe_hash.startswith('scrypt$'))
            self.assertTrue(password_matches(body['mot_de_passe'],user.mot_de_passe_hash))
            self.assertIsNotNone(db.get(Invitation,secret.split('.')[0]).consumed_at)

    def test_expired_invitation_and_non_admin_invitation_are_denied(self):
        for role in Role:
            if role!=Role.ADMINISTRATEUR:
                self.assertEqual(self.req(role,'POST','/admin/invitations',{'email':'new@example.invalid','role':'LECTEUR'}).status_code,403)
        secret=self.invite('expired@example.invalid')
        with system_session() as db:
            db.get(Invitation,secret.split('.')[0]).expires_at=now()-timedelta(seconds=1); db.commit()
        self.assertEqual(self.client.post('/api/auth/register',json={'email':'expired@example.invalid','mot_de_passe':'password123','invitation_token':secret}).status_code,403)

    def test_refresh_rotation_and_reuse_revokes_the_family(self):
        result=self.client.post('/api/auth/login',json={'email':'journaliste@example.invalid','mot_de_passe':'password123'})
        self.assertEqual(result.status_code,200,result.text); first=result.json()
        result=self.client.post('/api/auth/refresh',json={'refresh_token':first['refresh_token']})
        self.assertEqual(result.status_code,200,result.text); second=result.json()
        self.assertNotEqual(first['refresh_token'],second['refresh_token'])
        with system_session() as db:
            token=db.get(RefreshToken,first['refresh_token'].split('.')[0])
            self.assertEqual(token.token_hash,secret_hash(first['refresh_token'])); self.assertIsNotNone(token.used_at)
        self.assertEqual(self.client.post('/api/auth/refresh',json={'refresh_token':first['refresh_token']}).status_code,401)
        self.assertEqual(self.client.get('/api/auth/me',headers={'Authorization':'Bearer '+second['access_token']}).status_code,401)
        self.assertEqual(self.client.post('/api/auth/refresh',json={'refresh_token':second['refresh_token']}).status_code,401)

    def test_wrong_refresh_secret_cannot_revoke_a_session(self):
        secret=self.tokens[Role.JOURNALISTE].refresh_token
        wrong=secret[:-1]+('a' if secret[-1]!='a' else 'b')
        self.assertEqual(self.client.post('/api/auth/refresh',json={'refresh_token':wrong}).status_code,401)
        self.assertEqual(self.req('JOURNALISTE','GET','/auth/me').status_code,200)

    def test_logout_ownership_and_logout_all(self):
        mine=self.tokens[Role.JOURNALISTE]; other=self.tokens[Role.EDITEUR]
        self.assertEqual(self.req('JOURNALISTE','DELETE','/auth/sessions/'+other.session_id).status_code,404)
        self.assertEqual([r['id'] for r in self.req('JOURNALISTE','GET','/auth/sessions').json()],[mine.session_id])
        self.assertEqual(self.req('JOURNALISTE','POST','/auth/logout').status_code,204)
        self.assertEqual(self.req('JOURNALISTE','GET','/auth/me').status_code,401)
        self.assertEqual(self.client.post('/api/auth/refresh',json={'refresh_token':mine.refresh_token}).status_code,401)
        self.assertEqual(self.req('EDITEUR','POST','/auth/logout-all').status_code,204)
        self.assertEqual(self.req('EDITEUR','GET','/auth/me').status_code,401)

    def test_jwt_validation_and_database_role_authority(self):
        settings=get_settings(); pair=self.tokens[Role.JOURNALISTE]; claims=jwt.get_unverified_claims(pair.access_token)
        key=settings.jwt_secret.get_secret_value()
        variants=[({**claims,'exp':1},key,'HS256'),({**claims,'iss':'wrong'},key,'HS256'),
            ({**claims,'aud':'wrong'},key,'HS256'),({**claims,'type':'refresh'},key,'HS256'),
            ({**claims,'sid':'0'*32},key,'HS256'),(claims,'wrong-key','HS256'),(claims,key,'HS512')]
        for payload,secret,alg in variants:
            token=jwt.encode(payload,secret,algorithm=alg)
            self.assertEqual(self.client.get('/api/auth/me',headers={'Authorization':'Bearer '+token}).status_code,401)
        token=jwt.encode({**claims,'role':'EDITEUR'},key,algorithm='HS256')
        result=self.client.post(f'/api/workflow/drafts/{self.draft_id}/publish',headers={'Authorization':'Bearer '+token},json=FINAL)
        self.assertEqual(result.status_code,403)
        self.assertEqual(self.client.get('/api/auth/me',headers={'Authorization':'Bearer '+pair.refresh_token}).status_code,401)

    def test_password_change_and_bcrypt_migration(self):
        import bcrypt
        with system_session() as db:
            db.get(User,self.users[Role.JOURNALISTE].id).mot_de_passe_hash=bcrypt.hashpw(b'password123',bcrypt.gensalt(rounds=4)).decode(); db.commit()
        self.assertEqual(self.client.post('/api/auth/login',json={'email':'journaliste@example.invalid','mot_de_passe':'password123'}).status_code,200)
        with system_session() as db:
            self.assertTrue(db.get(User,self.users[Role.JOURNALISTE].id).mot_de_passe_hash.startswith('scrypt$'))
        result=self.req('JOURNALISTE','POST','/auth/password',{'current_password':'password123','new_password':'new-secure-password-123'})
        self.assertEqual(result.status_code,204,result.text)
        self.assertEqual(self.req('JOURNALISTE','GET','/auth/me').status_code,401)
        self.assertEqual(self.client.post('/api/auth/login',json={'email':'journaliste@example.invalid','mot_de_passe':'password123'}).status_code,401)
        self.assertEqual(self.client.post('/api/auth/login',json={'email':'journaliste@example.invalid','mot_de_passe':'new-secure-password-123'}).status_code,200)

    def test_ai_identity_scopes_and_conversion_are_restricted(self):
        result=self.req('ADMINISTRATEUR','POST','/admin/service-accounts',{'email':'worker@example.invalid','permissions':['drafts.create']})
        self.assertEqual(result.status_code,201,result.text); credentials=result.json()
        self.assertEqual(self.client.post('/api/auth/login',json={'email':credentials['client_id'],'mot_de_passe':credentials['client_secret']}).status_code,401)
        result=self.client.post('/api/auth/service-token',json={'client_id':credentials['client_id'],'client_secret':credentials['client_secret']})
        self.assertEqual(result.status_code,200,result.text); headers={'Authorization':'Bearer '+result.json()['access_token']}
        self.assertEqual(self.client.post('/api/copilot/research',headers=headers,json={'question':'Test question'}).status_code,403)
        self.assertEqual(self.client.post(f'/api/workflow/drafts/{self.draft_id}/validate',headers=headers,json={**FINAL,'expected_version':1}).status_code,403)
        self.assertEqual(self.req('ADMINISTRATEUR','PATCH',f"/admin/users/{credentials['id']}",{'role':'EDITEUR'}).status_code,403)
        self.assertEqual(self.req('ADMINISTRATEUR','POST','/admin/service-accounts',{'email':'bad@example.invalid','permissions':['publications.publish']}).status_code,422)

    def test_account_changes_revoke_tokens_and_admin_cannot_promote_itself(self):
        admin=self.users[Role.ADMINISTRATEUR]; journalist=self.users[Role.JOURNALISTE]
        self.assertEqual(self.req('ADMINISTRATEUR','PATCH',f'/admin/users/{admin.id}',{'role':'EDITEUR'}).status_code,403)
        result=self.req('ADMINISTRATEUR','PATCH',f'/admin/users/{journalist.id}',{'status':'suspended'})
        self.assertEqual(result.status_code,200,result.text)
        self.assertEqual(self.req('JOURNALISTE','GET','/auth/me').status_code,401)
        self.assertEqual(self.client.post('/api/auth/login',json={'email':'journaliste@example.invalid','mot_de_passe':'password123'}).status_code,401)

    def test_version_validation_and_exact_publication_payload(self):
        path=f'/workflow/drafts/{self.draft_id}'
        self.assertEqual(self.req('EDITEUR','POST',path+'/publish',FINAL).status_code,409)
        self.assertEqual(self.req('EDITEUR','POST',path+'/validate',{**FINAL,'expected_version':1}).status_code,200)
        self.assertEqual(self.req('EDITEUR','POST',path+'/publish',{**FINAL,'corps_article':'Unreviewed'}).status_code,409)
        result=self.req('JOURNALISTE','PATCH',f'/drafts/{self.draft_id}',{'expected_version':1,'synthese_ia':'New private draft'})
        self.assertEqual(result.status_code,200,result.text); self.assertIsNone(result.json()['validated_version'])
        self.assertEqual(self.req('EDITEUR','POST',path+'/publish',FINAL).status_code,409)
        self.assertEqual(self.req('EDITEUR','POST',path+'/validate',{**FINAL,'expected_version':1}).status_code,409)
        self.assertEqual(self.req('EDITEUR','POST',path+'/validate',{**FINAL,'expected_version':2}).status_code,200)
        self.assertEqual(self.req('EDITEUR','POST',path+'/publish',FINAL).status_code,200)

    def test_contributors_only_access_their_own_submissions(self):
        result=self.req('CONTRIBUTEUR','POST','/contributions/signals',{'content':'My report'})
        self.assertEqual(result.status_code,201,result.text); identifier=result.json()['id']
        self.assertEqual(self.req('CONTRIBUTEUR','POST',f'/contributions/{identifier}/information',{'content':'Additional information'}).status_code,201)
        other=make_account('CONTRIBUTEUR',email='other-contributor@example.invalid'); token=tokens_for(other)
        self.assertEqual(self.client.get(f'/api/contributions/{identifier}',headers={'Authorization':'Bearer '+token.access_token}).status_code,404)
        self.assertEqual(self.req('CONTRIBUTEUR','POST',f'/contributions/{identifier}/information',{'content':'Invalid','case_id':self.case_id}).status_code,422)

    def test_every_private_http_operation_has_a_middleware_policy(self):
        import re
        from app.core.route_policies import PUBLIC_ROUTES,policy_for
        for path,methods in self.app.openapi()['paths'].items():
            relative=path.removeprefix('/api/v1')
            relative=re.sub(r'\{session_id\}','a'*32 if relative.startswith('/auth/') else '1',relative)
            relative=re.sub(r'\{key\}','research_result_limit',relative)
            relative=re.sub(r'\{[^}]+\}','1',relative)
            for method in methods:
                if (method.upper(),relative) not in PUBLIC_ROUTES:
                    self.assertTrue(policy_for(method.upper(),relative)[0],(method,relative))

    def test_orm_guard_rejects_ai_admin_and_journalist_validation(self):
        from app.database.scope import scope_for_user
        from app.core.security import now
        for role in ('SERVICE_IA','ADMINISTRATEUR','JOURNALISTE'):
            with SessionLocal() as db:
                from app.repositories.identity import UserRepository
                user=UserRepository(db).get_for_auth(self.users[Role(role)].id)
                scope_for_user(db,user)
                draft=db.get(Draft,self.draft_id)
                draft.validated_version=1; draft.validated_by_id=user.id; draft.validated_at=now()
                draft.approved_payload=FINAL; draft.approved_payload_hash='a'*64
                with self.assertRaises(ForbiddenError): db.flush()
                db.rollback()

    def test_service_identity_type_is_immutable_even_in_sql(self):
        from sqlalchemy import update
        from sqlalchemy.exc import DBAPIError
        with system_session() as db:
            with self.assertRaises(DBAPIError):
                with db.begin_nested():
                    db.execute(update(User).where(User.id==self.users[Role.SERVICE_IA].id)
                               .values(role='EDITEUR',account_type='human'))

    def test_revoked_websocket_cannot_receive_the_next_alert(self):
        from starlette.websockets import WebSocketDisconnect
        token=self.tokens[Role.JOURNALISTE].access_token
        with self.client.websocket_connect('/api/alerts/ws',subprotocols=['bearer',token]) as websocket:
            self.assertEqual(self.req('JOURNALISTE','POST','/auth/logout').status_code,204)
            self.assertEqual(self.req('EDITEUR','POST',f'/copilot/alerts/signal/{self.signal_id}').status_code,200)
            with self.assertRaises(WebSocketDisconnect) as closed:
                websocket.receive_json()
            self.assertEqual(closed.exception.code,1008)

    def test_ai_can_create_only_a_private_unvalidated_draft(self):
        with system_session() as db:
            original=db.get(Signal,self.signal_id)
            signal=Signal(source_id=original.source_id,case_id=self.case_id,contenu_brut='Another signal',
                contenu_normalise='Another signal',url_origine='https://source.example.invalid/other',horodatage_publication=now())
            db.add(signal); db.commit(); identifier=signal.id
        result=self.req('SERVICE_IA','POST',f'/signals/{identifier}/analyze',{})
        self.assertEqual(result.status_code,201,result.text)
        with system_session() as db:
            draft=db.get(Draft,result.json()['id'])
            self.assertEqual(draft.confidentiality,'private')
            self.assertIsNone(draft.validated_version)
        payload={'objet_type':'draft','objet_id':result.json()['id'],'identite_source':'faible',
            'solidite_preuves':'faible','validation_editoriale':'eleve','conclusion':'confirme','justification':'Test'}
        self.assertEqual(self.req('SERVICE_IA','POST','/maharavo/confidence',payload).status_code,403)

    def test_expired_refresh_is_rejected_without_rotation(self):
        secret=self.tokens[Role.JOURNALISTE].refresh_token
        with system_session() as db:
            db.get(RefreshToken,secret.split('.')[0]).expires_at=now()-timedelta(seconds=1); db.commit()
        self.assertEqual(self.client.post('/api/auth/refresh',json={'refresh_token':secret}).status_code,401)

    @unittest.skipUnless(engine.dialect.name=='postgresql','PostgreSQL row locks required')
    def test_concurrent_refresh_detects_reuse(self):
        secret=self.tokens[Role.JOURNALISTE].refresh_token; barrier=Barrier(2)
        def rotate():
            with SessionLocal() as db:
                barrier.wait(timeout=10)
                try: refresh_tokens(db,secret); return 200
                except AuthenticationError: db.rollback(); return 401
        with ThreadPoolExecutor(max_workers=2) as executor:
            results=list(executor.map(lambda _:rotate(),range(2)))
        self.assertCountEqual(results,[200,401])
        self.assertEqual(self.req('JOURNALISTE','GET','/auth/me').status_code,401)


if __name__=='__main__':
    unittest.main()
