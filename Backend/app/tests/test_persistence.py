"""Persistence, relationships, tenant isolation and public-data non-disclosure."""
import os
os.environ.setdefault('DATABASE_URL', os.environ.get('FANILO_TEST_DATABASE_URL', 'sqlite:///:memory:'))
os.environ.setdefault('ENVIRONMENT', 'test')
os.environ.setdefault('JWT_SECRET', 'isolated-test-secret-at-least-thirty-two-bytes')
from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import patch
from sqlalchemy import select, text, insert, inspect
from sqlalchemy.exc import IntegrityError, DBAPIError
from fastapi.testclient import TestClient
from app.database import SessionLocal, engine
from app.database.scope import set_scope
from app.database.seed_demo import seed_demo
from app.tests.fixtures import reset_schema, system_session, tokens_for
from app.models import (Newsroom, User, Source, Signal, Case, Claim, Evidence, ClaimEvidence,
                        ResearchJob, MediaAnalysis, Draft, Publication, CorrectionAudit, SmsExchange)
from app.repositories.base import Repository
from app.core.errors import ForbiddenError, ConflictError
from app.core.config import get_settings
from app.core.security import create_access_token
from app.main import create_app

MODELS = [User, Source, Signal, Case, Claim, Evidence, ClaimEvidence, ResearchJob, MediaAnalysis,
          Draft, Publication, CorrectionAudit, SmsExchange]


def repository(db, model):
    instance = Repository(db)
    instance.model = model
    return instance


def graph(db, label, *, audit=True):
    now = datetime.now(timezone.utc)
    user = User(email=f'{label}@example.invalid', mot_de_passe_hash='fixture-not-a-usable-password', role='EDITEUR')
    source = Source(nom=label, type='Web', url='https://source.example.invalid')
    db.add_all([user, source]); db.flush()
    from app.database.scope import scope_for_user
    scope_for_user(db,user)
    case = Case(title=f'Case {label}', created_by_id=user.id)
    db.add(case); db.flush()
    signal = Signal(source_id=source.id, case_id=case.id, contenu_brut='PRIVATE_SIGNAL_SENTINEL',
                    contenu_normalise='PRIVATE_SIGNAL_SENTINEL', url_origine='https://source.example.invalid/item',
                    horodatage_publication=now)
    claim = Claim(case_id=case.id, statement='PRIVATE_CLAIM_SENTINEL')
    evidence = Evidence(case_id=case.id, source_id=source.id, title='Private evidence', kind='document',
                        content='PRIVATE_EVIDENCE_SENTINEL', confidentiality='confidential', sha256='b'*64)
    db.add_all([signal, claim, evidence]); db.flush()
    link = ClaimEvidence(case_id=case.id, claim_id=claim.id, evidence_id=evidence.id)
    research = ResearchJob(utilisateur_id=user.id, case_id=case.id, claim_id=claim.id, sujet='PRIVATE_RESEARCH_SENTINEL',
                           modele='fixture', debut=now, synthese='PRIVATE_AI_SENTINEL')
    media = MediaAnalysis(utilisateur_id=user.id, case_id=case.id, evidence_id=evidence.id, type_media='image',
                          reference_originale='PRIVATE_MEDIA_SENTINEL', empreinte_sha256='b'*64,
                          outil='fixture', version_outil='1', indice_indicatif='non_evalue', cree_le=now)
    draft = Draft(signal_id=signal.id, case_id=case.id, claim_id=claim.id, titre_suggere='Private draft',
                  synthese_ia='PRIVATE_DRAFT_SENTINEL', score_credibilite_indicatif=0, horodatage=now)
    db.add_all([link, research, media, draft]); db.flush()
    publication = Publication(draft_id=draft.id, titre_final='Approved public title', corps_article='Approved public body.',
                              categorie='Fixture', statut_verification='Vrai', id_journaliste_validateur=user.id,
                              horodatage_validation=now, contenu_optimise_sms='Approved SMS.',
                              confidentiality='public', status='published', published_at=now)
    db.add(publication); db.flush()
    sms = SmsExchange(publication_id=publication.id, numero_expediteur='TEST-NO-PHONE', message_recu='Fixture',
                      message_envoye='Approved SMS.', horodatage=now, statut_reponse='Trouve')
    db.add(sms)
    result = {type(record): record for record in [user,source,signal,case,claim,evidence,link,research,media,draft,publication,sms]}
    if audit:
        correction = CorrectionAudit(publication_id=publication.id, actor_id=user.id, action='published', reason='Fixture')
        db.add(correction); result[CorrectionAudit] = correction
    db.flush()
    return result


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        reset_schema()
        self.addCleanup(engine.dispose)

    def session(self, newsroom_id=1, dataset='real'):
        db = SessionLocal()
        set_scope(db, newsroom_id, dataset)
        actor=db.scalar(select(User.id).where(User.role=='EDITEUR').limit(1))
        if actor is not None: db.info['actor_id']=actor
        self.addCleanup(db.close)
        return db

    def test_all_models_have_lifecycle_scope_and_business_status(self):
        with self.session() as db:
            records = graph(db, 'all-models'); db.commit()
            for model in MODELS:
                with self.subTest(model=model.__tablename__):
                    entity = repository(db,model).get(records[model].id)
                    self.assertIsNotNone(entity.created_at)
                    self.assertIsNotNone(entity.updated_at)
                    self.assertEqual((entity.newsroom_id,entity.dataset),(1,'real'))
                    self.assertIsNotNone(entity.status)
                    self.assertEqual(len(repository(db,model).list()),1)
                    self.assertTrue(inspect(model).relationships or model is User)

    def test_relationship_graph_and_association_object(self):
        with self.session() as db:
            records=graph(db,'relations'); db.commit(); db.expire_all()
            case=repository(db,Case).get(records[Case].id)
            self.assertEqual(case.creator.email,'relations@example.invalid')
            self.assertEqual(case.claims[0].evidence_links[0].evidence.content,'PRIVATE_EVIDENCE_SENTINEL')
            self.assertEqual(case.evidence[0].claim_links[0].claim.id,case.claims[0].id)
            self.assertEqual(case.signals[0].source.signals[0].id,case.signals[0].id)
            self.assertEqual(case.drafts[0].signal.id,case.signals[0].id)
            self.assertEqual(case.drafts[0].publication.validator.id,case.creator.id)
            self.assertEqual(case.research_jobs[0].claim.id,case.claims[0].id)
            self.assertEqual(case.evidence[0].media_analyses[0].evidence.id,case.evidence[0].id)
            self.assertEqual(case.drafts[0].publication.corrections[0].actor.id,case.creator.id)
            self.assertEqual(case.drafts[0].publication.sms_exchanges[0].publication.id,case.drafts[0].publication.id)

    def test_crud_for_every_mutable_entity(self):
        with self.session() as db:
            records=graph(db,'crud',audit=False); db.commit()
            changes={User:('email','crud-updated@example.invalid'),Source:('nom','Updated source'),
                Signal:('contenu_normalise','Updated signal'),Case:('description','Updated case'),
                Claim:('statement','Updated claim'),Evidence:('title','Updated evidence'),
                ClaimEvidence:('rationale','Updated rationale'),ResearchJob:('sujet','Updated research'),
                MediaAnalysis:('observations',['Updated observation']),Draft:('synthese_ia','Updated draft'),
                Publication:('corps_article','Updated approved body'),SmsExchange:('message_recu','Updated SMS')}
            for model,(field,value) in changes.items():
                entity=repository(db,model).update(records[model].id,**{field:value})
                self.assertEqual(getattr(entity,field),value)
                self.assertGreaterEqual(entity.updated_at,entity.created_at)
            db.commit()
            order=[SmsExchange,Publication,Draft,MediaAnalysis,ResearchJob,ClaimEvidence,Evidence,Claim,Signal,Case,Source,User]
            for model in order:
                identifier=records[model].id
                repository(db,model).delete(identifier)
                self.assertIsNone(repository(db,model).get(identifier))
            db.commit()

    def test_missing_scope_and_cross_newsroom_reads_and_writes_are_denied(self):
        with self.session() as db:
            real=graph(db,'real'); db.commit()
            real_id=real[Draft].id
        with system_session() as admin:
            demo=seed_demo(admin); admin.commit(); demo_id=demo.id
            private_draft=admin.scalar(select(Draft).where(Draft.dataset=='demo')).id
        with SessionLocal() as unscoped:
            with self.assertRaises(ForbiddenError): repository(unscoped,Draft).list()
        with self.session() as db:
            self.assertIsNone(repository(db,Draft).get(private_draft))
            self.assertEqual(repository(db,Draft).get(real_id).id,real_id)
            entity=repository(db,Draft).get(real_id)
            entity.dataset='demo'
            with self.assertRaises(ForbiddenError): db.flush()
            db.rollback()
        with self.session(demo_id,'demo') as db:
            self.assertIsNone(repository(db,Draft).get(real_id))

    def test_database_rejects_cross_dataset_and_cross_case_foreign_keys(self):
        with self.session() as db:
            records=graph(db,'integrity'); db.commit()
            other_case=Case(title='Other case',created_by_id=records[User].id)
            db.add(other_case); db.flush()
            other=Evidence(case_id=other_case.id,title='Other',kind='document',content='Private')
            db.add(other); db.flush()
            with self.assertRaises(IntegrityError):
                with db.begin_nested():
                    db.add(ClaimEvidence(case_id=records[Case].id,claim_id=records[Claim].id,evidence_id=other.id)); db.flush()
            # Core INSERT bypasses ORM guards; the database still enforces newsroom/dataset integrity.
            with self.assertRaises(IntegrityError):
                with db.begin_nested():
                    db.execute(insert(Source).values(nom='Invalid',type='Web',url='https://invalid.example.invalid',
                        statut='Actif',frequence_scan_secondes=900,newsroom_id=1,dataset='demo',confidentiality='private'))

    def test_checks_uniqueness_and_restrict_deletion(self):
        with self.session() as db:
            records=graph(db,'constraints'); db.commit()
            for entity in [
                ClaimEvidence(case_id=records[Case].id,claim_id=records[Claim].id,evidence_id=records[Evidence].id),
                Source(nom='Invalid',type='Web',url='https://invalid.example.invalid',frequence_scan_secondes=1),
                Evidence(case_id=records[Case].id,title='Invalid',kind='document',content='Private',confidentiality='public'),
                Claim(case_id=records[Case].id,statement='Invalid',status='invented'),
            ]:
                with self.assertRaises(IntegrityError):
                    with db.begin_nested(): db.add(entity); db.flush()
            with self.assertRaises(IntegrityError):
                with db.begin_nested(): repository(db,Case).delete(records[Case].id)

    def test_audit_create_read_but_update_delete_are_rejected_in_orm_and_sql(self):
        with self.session() as db:
            records=graph(db,'audit'); db.commit()
            identifier=records[CorrectionAudit].id
            for action in ('update','delete'):
                with self.assertRaises(ConflictError):
                    with db.begin_nested():
                        repo=repository(db,CorrectionAudit)
                        repo.update(identifier,reason='Tampered') if action=='update' else repo.delete(identifier)
                sql='UPDATE corrections_audit SET reason=\'Tampered\' WHERE id=:id' if action=='update' else 'DELETE FROM corrections_audit WHERE id=:id'
                with self.assertRaises(DBAPIError):
                    with db.begin_nested(): db.execute(text(sql),{'id':identifier})
            if engine.dialect.name=='postgresql':
                with self.assertRaises(DBAPIError):
                    with db.begin_nested(): db.execute(text('TRUNCATE corrections_audit'))
            self.assertEqual(repository(db,CorrectionAudit).get(identifier).reason,'Fixture')

    def test_demo_seed_is_idempotent_and_never_creates_real_records(self):
        with system_session() as db:
            first=seed_demo(db); db.commit(); identifier=first.id
            second=seed_demo(db); db.commit(); self.assertEqual(second.id,identifier)
            for model in MODELS:
                rows=list(db.scalars(select(model)))
                self.assertEqual(len(rows),1)
                self.assertTrue(all(row.dataset=='demo' and row.newsroom_id==identifier for row in rows))

    def test_public_endpoints_expose_only_approved_real_publications(self):
        with self.session() as db:
            records=graph(db,'public'); db.commit()
            token=tokens_for(records[User]).access_token; public_id=records[Publication].id
            # A known private publication must never be discoverable through public text search.
            records[Publication].confidentiality='private'; records[Publication].corps_article='PRIVATE_PUBLICATION_SENTINEL'
            db.commit()
        with system_session() as admin:
            demo=seed_demo(admin); admin.commit(); demo_id=demo.id
            demo_draft_id=admin.scalar(select(Draft).where(Draft.dataset=='demo')).id
        with TestClient(create_app()) as client:
            self.assertEqual(client.get('/api/public/articles?dataset=demo&newsroom_id='+str(demo_id)).json(),[])
            result=client.post('/api/sms/citizen',json={'numero_expediteur':'TEST-NO-PHONE','message':'PRIVATE_PUBLICATION_SENTINEL'})
            self.assertEqual(result.json()['statut'],'Non_Trouve')
            for resource in ('drafts','evidence','claims','research_jobs','media_analyses','corrections_audit'):
                self.assertEqual(client.get('/api/public/'+resource+'/1').status_code,404)
            self.assertEqual(client.get(f'/api/drafts/{demo_draft_id}',headers={'Authorization':'Bearer '+token}).status_code,404)
            with self.session() as db:
                publication=repository(db,Publication).get(public_id)
                publication.confidentiality='public'; publication.corps_article='Approved real body'; db.commit()
            response=client.get('/api/public/articles')
            self.assertEqual(len(response.json()),1)
            self.assertEqual(response.json()[0]['id'],public_id)
            for word in ('PRIVATE_','DEMO_PRIVATE_','draft_id','newsroom_id','password','citations','source_id'):
                self.assertNotIn(word,response.text)
            with self.session() as db:
                publication=repository(db,Publication).get(public_id)
                publication.published_at=datetime.now(timezone.utc)+timedelta(days=1); db.commit()
            self.assertEqual(client.get('/api/public/articles').json(),[])
            with self.session() as db:
                publication=repository(db,Publication).get(public_id)
                publication.status='withdrawn'; publication.confidentiality='private'; db.commit()
            self.assertEqual(client.get('/api/public/articles').json(),[])

    def test_correction_and_withdrawal_are_transactional_and_audited(self):
        from app.services.publications import correct_publication,withdraw_publication
        from app.schemas import PublishRequest
        from app.repositories.publications import PublicPublicationRepository
        with self.session() as db:
            records=graph(db,'correction'); records[User].role='EDITEUR'; db.commit()
            publication=records[Publication]
            payload=PublishRequest(titre_final='Corrected title',corps_article='Corrected approved body',
                categorie='Fixture',statut_verification='Faux',contenu_optimise_sms='Corrected SMS')
            correct_publication(db,records[User],publication.id,payload,reason='Human correction')
            self.assertEqual(publication.revision,2)
            audits=repository(db,CorrectionAudit).list()
            self.assertEqual(len(audits),2)
            self.assertEqual(audits[1].before['corps_article'],'Approved public body.')
            self.assertEqual(PublicPublicationRepository(db).published()[0]['corps_article'],'Corrected approved body')
            withdraw_publication(db,records[User],publication.id,reason='Editorial withdrawal')
            self.assertEqual(PublicPublicationRepository(db).published(),[])
            self.assertEqual(len(repository(db,CorrectionAudit).list()),3)

    def test_every_private_model_rejects_public_confidentiality(self):
        with self.session() as db:
            records=graph(db,'visibility'); db.commit()
            for model in MODELS:
                if model is Publication:
                    continue
                with self.subTest(model=model.__tablename__):
                    with self.assertRaises(DBAPIError):
                        with db.begin_nested():
                            db.execute(text(f"UPDATE {model.__tablename__} SET confidentiality='public' WHERE id=:id"),{'id':records[model].id})

    def test_same_dataset_newsrooms_and_bulk_operations_are_isolated(self):
        from sqlalchemy import update,delete
        with self.session() as db:
            first=graph(db,'newsroom-a'); db.commit(); first_id=first[Draft].id
        with system_session() as admin:
            other=Newsroom(slug='other-real',name='Other real newsroom',dataset='real')
            admin.add(other); admin.commit(); other_id=other.id
        with self.session(other_id,'real') as db:
            second=graph(db,'newsroom-b'); db.commit()
            self.assertIsNone(repository(db,Draft).get(first_id))
            result=db.execute(update(Draft).where(Draft.id==first_id).values(synthese_ia='tampered'))
            self.assertEqual(result.rowcount,0)
            result=db.execute(delete(Draft).where(Draft.id==first_id))
            self.assertEqual(result.rowcount,0)
            with self.assertRaises(IntegrityError):
                with db.begin_nested():
                    second[Draft].signal_id=first[Signal].id
                    db.flush()
        with self.session() as db:
            self.assertEqual(repository(db,Draft).get(first_id).synthese_ia,'PRIVATE_DRAFT_SENTINEL')

    def test_websocket_broadcasts_are_partitioned_by_scope(self):
        import asyncio
        from app.integrations.notifications.websocket import AlertManager
        class Socket:
            def __init__(self): self.messages=[]
            async def accept(self,subprotocol=None): pass
            async def send_json(self,payload): self.messages.append(payload)
        async def scenario():
            manager=AlertManager(validator=lambda token,scope:True); real=Socket(); demo=Socket(); other=Socket()
            await manager.connect(real,scope=(1,'real'),token='fixture')
            await manager.connect(demo,scope=(3,'demo'),token='fixture')
            await manager.connect(other,scope=(4,'real'),token='fixture')
            await manager.broadcast({'signal_id':1},scope=(1,'real'))
            self.assertEqual(real.messages,[{'signal_id':1}])
            self.assertEqual(demo.messages,[])
            self.assertEqual(other.messages,[])
        asyncio.run(scenario())

    def test_demo_public_view_requires_explicit_server_configuration(self):
        with system_session() as db:
            demo=seed_demo(db); db.commit(); demo_id=demo.id
        settings=get_settings().model_copy(update={'public_dataset':'demo','public_newsroom_id':demo_id})
        with TestClient(create_app()) as client:
            self.assertEqual(client.get('/api/public/articles').json(),[])
            with patch('app.repositories.publications.get_settings',return_value=settings):
                result=client.get('/api/public/articles')
                self.assertEqual(len(result.json()),1)
                self.assertIn('DÉMONSTRATION',result.json()[0]['titre_final'])
                self.assertNotIn('DEMO_PRIVATE_',result.text)


if __name__=='__main__':
    unittest.main()
