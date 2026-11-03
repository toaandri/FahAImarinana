"""Idempotent fictitious dataset, restricted to its own demonstration newsroom."""
import argparse
import os
from datetime import datetime, timezone
from sqlalchemy import select
from ..database import SessionLocal
from ..core.security import password_hash
from ..core.config import get_settings
from ..models import (Newsroom, User, Source, Signal, Case, Claim, Evidence, ClaimEvidence,
                      ResearchJob, MediaAnalysis, Draft, Publication, CorrectionAudit, SmsExchange)


def seed_demo(db):
    if not db.info.get('system'):
        raise ValueError('Le chargement fictif exige une session opérateur explicite.')
    newsroom = db.scalar(select(Newsroom).where(Newsroom.slug == 'fictional-demo'))
    if newsroom:
        return newsroom
    newsroom = Newsroom(id=3, slug='fictional-demo', name='Rédaction fictive — démonstration', dataset='demo')
    db.add(newsroom)
    db.flush()
    scope = {'newsroom_id': newsroom.id, 'dataset': 'demo', 'confidentiality': 'private'}
    now = datetime.now(timezone.utc)
    password = os.environ.get('DEMO_PASSWORD', 'demo12345')
    journalist = User(email=os.environ.get('DEMO_JOURNALIST_EMAIL', 'journaliste.demo@example.invalid'),
                      mot_de_passe_hash=password_hash(password), role='Journaliste', **scope)
    contributor = User(email=os.environ.get('DEMO_CONTRIBUTOR_EMAIL', 'contributeur.demo@example.invalid'),
                      mot_de_passe_hash=password_hash(password), role='JOURNALISTE', **scope)
    source = Source(nom='Bulletin fictif', type='Web', url='https://bulletin.example.invalid', **scope)
    db.add_all([journalist, contributor, source]); db.flush()
    case = Case(title='EXERCICE FICTIF — interruption imaginaire', created_by_id=journalist.id, **scope)
    db.add(case); db.flush()
    signal = Signal(source_id=source.id, case_id=case.id, contenu_brut='Signal entièrement fictif.',
                    contenu_normalise='Signal entièrement fictif.', url_origine='https://bulletin.example.invalid/fiction',
                    horodatage_publication=now, **scope)
    claim = Claim(case_id=case.id, statement='Une interruption imaginaire aurait eu lieu.', **scope)
    evidence = Evidence(case_id=case.id, source_id=source.id, title='Pièce confidentielle fictive', kind='document',
                        content='DEMO_PRIVATE_EVIDENCE_SENTINEL', sha256='a'*64,
                        **{**scope, 'confidentiality':'confidential'})
    db.add_all([signal, claim, evidence]); db.flush()
    link = ClaimEvidence(case_id=case.id, claim_id=claim.id, evidence_id=evidence.id, stance='context', **scope)
    research = ResearchJob(utilisateur_id=journalist.id, case_id=case.id, claim_id=claim.id, sujet='Recherche fictive',
                           modele='simulation', statut='terminee', debut=now, fin=now,
                           synthese='DEMO_PRIVATE_AI_SENTINEL', **scope)
    media = MediaAnalysis(utilisateur_id=journalist.id, case_id=case.id, evidence_id=evidence.id, type_media='document',
                          reference_originale='demo://fiction/document', empreinte_sha256='a'*64, outil='Simulation',
                          version_outil='1', indice_indicatif='non_evalue', cree_le=now, **scope)
    draft = Draft(signal_id=signal.id, case_id=case.id, claim_id=claim.id, titre_suggere='Brouillon fictif privé',
                  synthese_ia='DEMO_PRIVATE_DRAFT_SENTINEL', score_credibilite_indicatif=0,
                  horodatage=now, statut='En_Cours', **scope)
    db.add_all([link, research, media, draft]); db.flush()
    publication = Publication(draft_id=draft.id, titre_final='DÉMONSTRATION — événement imaginaire',
                              corps_article='Exercice fictif : ce texte ne décrit aucun événement réel.',
                              categorie='Démonstration', statut_verification='Faux', id_journaliste_validateur=journalist.id,
                              horodatage_validation=now, contenu_optimise_sms='DEMO : information entièrement fictive.',
                              published_at=now, status='published', **{**scope,'confidentiality':'public'})
    db.add(publication); db.flush()
    db.add_all([
        CorrectionAudit(publication_id=publication.id, actor_id=journalist.id, action='published', reason='Exercice fictif.', **scope),
        SmsExchange(publication_id=publication.id, numero_expediteur='DEMO-NO-PHONE', message_recu='Exercice',
                    message_envoye=publication.contenu_optimise_sms, statut_reponse='Trouve', horodatage=now, **scope),
    ])
    db.flush()
    return newsroom


def main():
    parser = argparse.ArgumentParser(description='Charger uniquement des données fictives dans une rédaction demo séparée.')
    parser.parse_args()
    if get_settings().environment == 'production':
        parser.error('Utiliser une base de démonstration distincte de la production.')
    with SessionLocal(info={'system':True}) as db:
        newsroom = seed_demo(db)
        identifier = newsroom.id
        db.commit()
    print(f'Données fictives créées dans la rédaction {identifier} (dataset=demo). Aucun SMS envoyé.')


if __name__ == '__main__':
    main()
