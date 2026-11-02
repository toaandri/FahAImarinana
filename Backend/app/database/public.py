"""Sanitized SQL projections. No source, draft, evidence or AI analysis is selected."""
from sqlalchemy import text

FIELDS = ('id', 'titre_final', 'corps_article', 'categorie', 'statut_verification',
          'horodatage_validation', 'contenu_optimise_sms', 'newsroom_id')
VIEW_DATASETS = {'public_publications': 'real', 'demo_publications': 'demo'}


def create_public_views(connection):
    for view, dataset in VIEW_DATASETS.items():
        barrier = ' WITH (security_barrier=true)' if connection.dialect.name == 'postgresql' else ''
        clock = "julianday(published_at) <= julianday('now')" if connection.dialect.name == 'sqlite' else "published_at <= CURRENT_TIMESTAMP"
        connection.execute(text(f'''CREATE VIEW {view}{barrier} AS
            SELECT {', '.join(FIELDS)} FROM publications
            WHERE confidentiality = 'public' AND status = 'published'
              AND published_at IS NOT NULL AND {clock}
              AND dataset = '{dataset}'
              AND statut_verification IN ('Vrai','Faux','Trompeur')'''))
    connection.execute(text('CREATE VIEW articles_certifies_publics AS SELECT * FROM public_publications'))


def drop_public_views(connection):
    for view in ('articles_certifies_publics', 'public_publications', 'demo_publications'):
        connection.execute(text(f'DROP VIEW IF EXISTS {view}'))


def verify_public_role(connection):
    """Production refuses any public DB identity that can read a private base table."""
    from ..database.base import Base
    role = connection.execute(text('SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user')).one()
    if role.rolsuper or role.rolbypassrls:
        raise RuntimeError('Le compte PostgreSQL public doit être non privilégié.')
    for table in Base.metadata.tables:
        if connection.scalar(text("SELECT has_table_privilege(current_user, :table, 'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')"), {'table': table}):
            raise RuntimeError('Le compte PostgreSQL public possède des droits sur une table applicative.')
    if not connection.scalar(text("SELECT has_table_privilege(current_user, 'public_publications', 'SELECT')")):
        raise RuntimeError('La vue des publications publiques doit être accessible au compte public.')
    if connection.scalar(text("SELECT has_table_privilege(current_user, 'demo_publications', 'SELECT,INSERT,UPDATE,DELETE')")):
        raise RuntimeError('Le compte PostgreSQL public réel ne doit pas accéder aux démonstrations.')
