"""Database-backed local research tasks; no vendor execution is fabricated."""
from datetime import timedelta
from sqlalchemy import select,update
from ..models import ResearchJob
from ..core.rbac import Permission as P,authorize,permissions_for
from ..core.errors import NotFoundError,ConflictError,ForbiddenError
from ..core.security import now
from ..database.scope import scope_for_user
from .investigations import get_case,search_case_pieces


def enqueue(db,user,case_id,payload):
    authorize(user,P.RESEARCH_RUN); scope_for_user(db,user)
    get_case(db,case_id,writable=True)
    job=ResearchJob(utilisateur_id=user.id,case_id=case_id,sujet=payload.question,
        questions=[payload.question],modele='local-document-search-v1',statut='queued',debut=now())
    db.add(job); db.commit()
    return job


def get_job(db,user,identifier):
    authorize(user,P.RESEARCH_RUN); scope_for_user(db,user)
    job=db.scalar(select(ResearchJob).where(ResearchJob.id==identifier))
    if job is None:
        raise NotFoundError('Tâche introuvable.')
    return job


def cancel(db,user,identifier):
    job=get_job(db,user,identifier)
    if job.utilisateur_id!=user.id and P.TASKS_RUN not in permissions_for(user):
        raise ForbiddenError('Seul le demandeur ou le worker autorisé peut annuler cette tâche.')
    changed=db.execute(update(ResearchJob).where(ResearchJob.id==identifier,ResearchJob.statut=='queued')
        .values(statut='cancelled',fin=now()))
    if changed.rowcount!=1:
        raise ConflictError('Seule une tâche encore en attente peut être annulée.')
    db.commit(); db.refresh(job)
    return job


def run_one(db,user):
    authorize(user,P.TASKS_RUN); authorize(user,P.RESEARCH_RUN); scope_for_user(db,user)
    statement=select(ResearchJob).where(ResearchJob.statut=='queued',
        ResearchJob.modele=='local-document-search-v1').order_by(ResearchJob.id).limit(1)
    if db.bind.dialect.name=='postgresql':
        statement=statement.with_for_update(skip_locked=True)
    job=db.scalar(statement)
    if job is None:
        return None
    identifier=job.id
    claimed=db.execute(update(ResearchJob).where(ResearchJob.id==identifier,ResearchJob.statut=='queued')
        .values(statut='en_cours',debut=now()))
    if claimed.rowcount!=1:
        db.rollback(); return None
    db.commit()
    try:
        get_case(db,job.case_id,writable=True)
        result=search_case_pieces(db,job.case_id,job.sujet)
        for key,value in result.items():
            setattr(job,key,value)
        job.fin=now(); db.commit()
    except Exception:
        db.rollback()
        # Do not leak raw exceptions or private document contents into task errors.
        job=db.scalar(select(ResearchJob).where(ResearchJob.id==identifier))
        job.statut='echouee'; job.fin=now()
        job.erreurs=['local_research_failed : recherche locale interrompue.']
        job.synthese=None; job.citations=[]
        db.commit()
    return job


def fail_stale(db,user,minutes=15):
    """Explicit recovery after a killed worker. Never declare an interrupted job successful."""
    authorize(user,P.TASKS_RUN); authorize(user,P.RESEARCH_RUN); scope_for_user(db,user)
    result=db.execute(update(ResearchJob).where(ResearchJob.statut=='en_cours',
        ResearchJob.modele=='local-document-search-v1',ResearchJob.debut<now()-timedelta(minutes=minutes))
        .values(statut='echouee',fin=now(),synthese=None,citations=[],
                erreurs=['worker_interrupted : traitement interrompu ; soumettre une nouvelle demande.']))
    db.commit()
    return result.rowcount
