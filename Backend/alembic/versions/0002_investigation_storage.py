"""Canonical persistence, tenant/dataset integrity and sanitized public projections.

Historical records are quarantined; publication is never inferred from a legacy row.
Revision ID: 0002_investigation_storage
"""
from alembic import op, context
import sqlalchemy as sa

revision = "0002_investigation_storage"
down_revision = "0001_modular_baseline"
branch_labels = None
depends_on = None

RENAMES = {
    "utilisateurs": "users", "sources_surveillees": "sources", "signaux_bruts": "signals",
    "drafts_ia": "drafts", "articles_certifies": "publications", "historique_sms": "sms_exchanges",
    "recherches_maharavo": "research_jobs", "analyses_media_maharavo": "media_analyses",
}
LEGACY_TABLES = ["utilisateurs", "sources_surveillees", "signaux_bruts", "drafts_ia", "articles_certifies",
                 "historique_sms", "recherches_maharavo", "analyses_media_maharavo", "contacts_journalistes",
                 "documents_recherche", "sessions_chat", "messages_chat", "evaluations_confiance_maharavo"]
NAMING = {"fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
          "uq": "uq_%(table_name)s_%(column_0_name)s"}


def target_schema():
    """Frozen metadata: later model changes cannot alter this revision."""
    metadata = sa.MetaData()
    sa.Table('newsrooms', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('slug', sa.String(length=100), primary_key=False, nullable=False),
        sa.Column('name', sa.String(length=150), primary_key=False, nullable=False),
        sa.Column('dataset', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('status', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("dataset IN ('real','demo','quarantine')", name='ck_newsrooms_dataset'),
        sa.CheckConstraint("status IN ('active','archived')", name='ck_newsrooms_status'),
        sa.UniqueConstraint('slug', name=None),
        sa.UniqueConstraint('id', 'dataset', name='uq_newsrooms_dataset'),
    )
    sa.Table('documents_recherche', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('titre', sa.String(length=250), primary_key=False, nullable=False),
        sa.Column('contenu', sa.Text(), primary_key=False, nullable=False),
        sa.Column('url', sa.String(length=500), primary_key=False, nullable=True),
        sa.Column('est_certifie', sa.Boolean(), primary_key=False, nullable=False),
        sa.Column('cree_le', sa.DateTime(timezone=True), primary_key=False, nullable=False),
        sa.Column('newsroom_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('dataset', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('confidentiality', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("confidentiality IN ('private','confidential')", name='ck_documents_recherche_confidentiality'),
        sa.CheckConstraint("dataset IN ('real','demo','quarantine')", name='ck_documents_recherche_dataset'),
        sa.ForeignKeyConstraint(['newsroom_id', 'dataset'], ['newsrooms.id', 'newsrooms.dataset'], name='fk_documents_recherche_newsroom', ondelete='RESTRICT'),
        sa.UniqueConstraint('id', 'newsroom_id', 'dataset', name='uq_documents_recherche_scope'),
    )
    sa.Index('ix_documents_recherche_scope_created', metadata.tables['documents_recherche'].c['newsroom_id'], metadata.tables['documents_recherche'].c['dataset'], metadata.tables['documents_recherche'].c['created_at'], unique=False)
    sa.Table('sources', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('nom', sa.String(length=150), primary_key=False, nullable=False),
        sa.Column('type', sa.String(length=30), primary_key=False, nullable=False),
        sa.Column('url', sa.String(length=500), primary_key=False, nullable=False),
        sa.Column('statut', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('frequence_scan_secondes', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('derniere_verification', sa.DateTime(timezone=True), primary_key=False, nullable=True),
        sa.Column('newsroom_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('dataset', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('confidentiality', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("confidentiality IN ('private','confidential')", name='ck_sources_confidentiality'),
        sa.CheckConstraint("dataset IN ('real','demo','quarantine')", name='ck_sources_dataset'),
        sa.CheckConstraint('frequence_scan_secondes >= 60', name='ck_sources_frequency'),
        sa.CheckConstraint("statut IN ('Actif','Inactif')", name='ck_sources_status'),
        sa.CheckConstraint("type IN ('Facebook','X','Web','RSS')", name='ck_sources_type'),
        sa.ForeignKeyConstraint(['newsroom_id', 'dataset'], ['newsrooms.id', 'newsrooms.dataset'], name='fk_sources_newsroom', ondelete='RESTRICT'),
        sa.UniqueConstraint('id', 'newsroom_id', 'dataset', name='uq_sources_scope'),
    )
    sa.Index('ix_sources_scope_created', metadata.tables['sources'].c['newsroom_id'], metadata.tables['sources'].c['dataset'], metadata.tables['sources'].c['created_at'], unique=False)
    sa.Table('users', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('email', sa.String(length=255), primary_key=False, nullable=False),
        sa.Column('mot_de_passe_hash', sa.String(length=255), primary_key=False, nullable=False),
        sa.Column('role', sa.String(length=30), primary_key=False, nullable=False),
        sa.Column('actif', sa.Boolean(), primary_key=False, nullable=False),
        sa.Column('status', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('newsroom_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('dataset', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('confidentiality', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("confidentiality IN ('private','confidential')", name='ck_users_confidentiality'),
        sa.CheckConstraint("dataset IN ('real','demo','quarantine')", name='ck_users_dataset'),
        sa.CheckConstraint("role IN ('Journaliste','Editeur')", name='ck_users_role'),
        sa.CheckConstraint("status IN ('active','suspended','archived')", name='ck_users_status'),
        sa.ForeignKeyConstraint(['newsroom_id', 'dataset'], ['newsrooms.id', 'newsrooms.dataset'], name='fk_users_newsroom', ondelete='RESTRICT'),
        sa.UniqueConstraint('id', 'newsroom_id', 'dataset', name='uq_users_scope'),
    )
    sa.Index('ix_users_email', metadata.tables['users'].c['email'], unique=True)
    sa.Index('ix_users_scope_created', metadata.tables['users'].c['newsroom_id'], metadata.tables['users'].c['dataset'], metadata.tables['users'].c['created_at'], unique=False)
    sa.Table('cases', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('title', sa.String(length=250), primary_key=False, nullable=False),
        sa.Column('description', sa.Text(), primary_key=False, nullable=False),
        sa.Column('status', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('created_by_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('newsroom_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('dataset', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('confidentiality', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("confidentiality IN ('private','confidential')", name='ck_cases_confidentiality'),
        sa.CheckConstraint("dataset IN ('real','demo','quarantine')", name='ck_cases_dataset'),
        sa.CheckConstraint("status IN ('open','investigating','review','closed','archived')", name='ck_cases_status'),
        sa.ForeignKeyConstraint(['created_by_id', 'newsroom_id', 'dataset'], ['users.id', 'users.newsroom_id', 'users.dataset'], name='fk_cases_creator_scope', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['newsroom_id', 'dataset'], ['newsrooms.id', 'newsrooms.dataset'], name='fk_cases_newsroom', ondelete='RESTRICT'),
        sa.UniqueConstraint('id', 'newsroom_id', 'dataset', name='uq_cases_scope'),
    )
    sa.Index('ix_cases_creator', metadata.tables['cases'].c['created_by_id'], unique=False)
    sa.Index('ix_cases_scope_created', metadata.tables['cases'].c['newsroom_id'], metadata.tables['cases'].c['dataset'], metadata.tables['cases'].c['created_at'], unique=False)
    sa.Index('ix_cases_status', metadata.tables['cases'].c['newsroom_id'], metadata.tables['cases'].c['dataset'], metadata.tables['cases'].c['status'], unique=False)
    sa.Table('contacts_journalistes', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('utilisateur_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('numero_telephone', sa.String(length=30), primary_key=False, nullable=False),
        sa.Column('alertes_actives', sa.Boolean(), primary_key=False, nullable=False),
        sa.Column('newsroom_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('dataset', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('confidentiality', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("confidentiality IN ('private','confidential')", name='ck_contacts_journalistes_confidentiality'),
        sa.CheckConstraint("dataset IN ('real','demo','quarantine')", name='ck_contacts_journalistes_dataset'),
        sa.ForeignKeyConstraint(['newsroom_id', 'dataset'], ['newsrooms.id', 'newsrooms.dataset'], name='fk_contacts_journalistes_newsroom', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['utilisateur_id', 'newsroom_id', 'dataset'], ['users.id', 'users.newsroom_id', 'users.dataset'], name='fk_contacts_user_scope', ondelete='RESTRICT'),
        sa.UniqueConstraint('numero_telephone', name=None),
        sa.UniqueConstraint('id', 'newsroom_id', 'dataset', name='uq_contacts_journalistes_scope'),
    )
    sa.Index('ix_contacts_journalistes_scope_created', metadata.tables['contacts_journalistes'].c['newsroom_id'], metadata.tables['contacts_journalistes'].c['dataset'], metadata.tables['contacts_journalistes'].c['created_at'], unique=False)
    sa.Table('evaluations_confiance_maharavo', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('utilisateur_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('objet_type', sa.String(length=30), primary_key=False, nullable=False),
        sa.Column('objet_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('identite_source', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('solidite_preuves', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('validation_editoriale', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('conclusion', sa.String(length=40), primary_key=False, nullable=False),
        sa.Column('justification', sa.Text(), primary_key=False, nullable=False),
        sa.Column('cree_le', sa.DateTime(timezone=True), primary_key=False, nullable=False),
        sa.Column('newsroom_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('dataset', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('confidentiality', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("confidentiality IN ('private','confidential')", name='ck_evaluations_confiance_maharavo_confidentiality'),
        sa.CheckConstraint("dataset IN ('real','demo','quarantine')", name='ck_evaluations_confiance_maharavo_dataset'),
        sa.ForeignKeyConstraint(['utilisateur_id', 'newsroom_id', 'dataset'], ['users.id', 'users.newsroom_id', 'users.dataset'], name='fk_confidence_user_scope', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['newsroom_id', 'dataset'], ['newsrooms.id', 'newsrooms.dataset'], name='fk_evaluations_confiance_maharavo_newsroom', ondelete='RESTRICT'),
        sa.UniqueConstraint('id', 'newsroom_id', 'dataset', name='uq_evaluations_confiance_maharavo_scope'),
    )
    sa.Index('ix_evaluations_confiance_maharavo_scope_created', metadata.tables['evaluations_confiance_maharavo'].c['newsroom_id'], metadata.tables['evaluations_confiance_maharavo'].c['dataset'], metadata.tables['evaluations_confiance_maharavo'].c['created_at'], unique=False)
    sa.Table('sessions_chat', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('utilisateur_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('titre', sa.String(length=250), primary_key=False, nullable=False),
        sa.Column('cree_le', sa.DateTime(timezone=True), primary_key=False, nullable=False),
        sa.Column('mise_a_jour_le', sa.DateTime(timezone=True), primary_key=False, nullable=False),
        sa.Column('newsroom_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('dataset', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('confidentiality', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("confidentiality IN ('private','confidential')", name='ck_sessions_chat_confidentiality'),
        sa.CheckConstraint("dataset IN ('real','demo','quarantine')", name='ck_sessions_chat_dataset'),
        sa.ForeignKeyConstraint(['utilisateur_id', 'newsroom_id', 'dataset'], ['users.id', 'users.newsroom_id', 'users.dataset'], name='fk_chat_user_scope', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['newsroom_id', 'dataset'], ['newsrooms.id', 'newsrooms.dataset'], name='fk_sessions_chat_newsroom', ondelete='RESTRICT'),
        sa.UniqueConstraint('id', 'newsroom_id', 'dataset', name='uq_sessions_chat_scope'),
    )
    sa.Index('ix_sessions_chat_scope_created', metadata.tables['sessions_chat'].c['newsroom_id'], metadata.tables['sessions_chat'].c['dataset'], metadata.tables['sessions_chat'].c['created_at'], unique=False)
    sa.Table('claims', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('case_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('statement', sa.Text(), primary_key=False, nullable=False),
        sa.Column('status', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('verdict', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('newsroom_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('dataset', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('confidentiality', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("confidentiality IN ('private','confidential')", name='ck_claims_confidentiality'),
        sa.CheckConstraint("dataset IN ('real','demo','quarantine')", name='ck_claims_dataset'),
        sa.CheckConstraint("status IN ('unverified','investigating','verified','disputed','insufficient')", name='ck_claims_status'),
        sa.CheckConstraint("verdict IN ('unknown','confirmed','refuted','misleading','partial','unverifiable')", name='ck_claims_verdict'),
        sa.ForeignKeyConstraint(['case_id', 'newsroom_id', 'dataset'], ['cases.id', 'cases.newsroom_id', 'cases.dataset'], name='fk_claims_case_scope', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['newsroom_id', 'dataset'], ['newsrooms.id', 'newsrooms.dataset'], name='fk_claims_newsroom', ondelete='RESTRICT'),
        sa.UniqueConstraint('id', 'case_id', 'newsroom_id', 'dataset', name='uq_claims_case_scope'),
        sa.UniqueConstraint('id', 'newsroom_id', 'dataset', name='uq_claims_scope'),
    )
    sa.Index('ix_claims_case_status', metadata.tables['claims'].c['case_id'], metadata.tables['claims'].c['status'], unique=False)
    sa.Index('ix_claims_scope_created', metadata.tables['claims'].c['newsroom_id'], metadata.tables['claims'].c['dataset'], metadata.tables['claims'].c['created_at'], unique=False)
    sa.Table('evidence', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('case_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('source_id', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('title', sa.String(length=250), primary_key=False, nullable=False),
        sa.Column('kind', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('content', sa.Text(), primary_key=False, nullable=False),
        sa.Column('storage_key', sa.String(length=500), primary_key=False, nullable=True),
        sa.Column('original_url', sa.String(length=500), primary_key=False, nullable=True),
        sa.Column('sha256', sa.String(length=64), primary_key=False, nullable=True),
        sa.Column('status', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('collected_at', sa.DateTime(timezone=True), primary_key=False, nullable=True),
        sa.Column('newsroom_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('dataset', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('confidentiality', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("confidentiality IN ('private','confidential')", name='ck_evidence_confidentiality'),
        sa.CheckConstraint("dataset IN ('real','demo','quarantine')", name='ck_evidence_dataset'),
        sa.CheckConstraint('sha256 IS NULL OR length(sha256) = 64', name='ck_evidence_hash'),
        sa.CheckConstraint("kind IN ('document','image','video','audio','url','testimony')", name='ck_evidence_kind'),
        sa.CheckConstraint("status IN ('collected','reviewing','verified','rejected')", name='ck_evidence_status'),
        sa.ForeignKeyConstraint(['case_id', 'newsroom_id', 'dataset'], ['cases.id', 'cases.newsroom_id', 'cases.dataset'], name='fk_evidence_case_scope', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['newsroom_id', 'dataset'], ['newsrooms.id', 'newsrooms.dataset'], name='fk_evidence_newsroom', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['source_id', 'newsroom_id', 'dataset'], ['sources.id', 'sources.newsroom_id', 'sources.dataset'], name='fk_evidence_source_scope', ondelete='RESTRICT'),
        sa.UniqueConstraint('id', 'case_id', 'newsroom_id', 'dataset', name='uq_evidence_case_scope'),
        sa.UniqueConstraint('newsroom_id', 'dataset', 'sha256', name='uq_evidence_hash_scope'),
        sa.UniqueConstraint('id', 'newsroom_id', 'dataset', name='uq_evidence_scope'),
    )
    sa.Index('ix_evidence_case_status', metadata.tables['evidence'].c['case_id'], metadata.tables['evidence'].c['status'], unique=False)
    sa.Index('ix_evidence_scope_created', metadata.tables['evidence'].c['newsroom_id'], metadata.tables['evidence'].c['dataset'], metadata.tables['evidence'].c['created_at'], unique=False)
    sa.Index('ix_evidence_source', metadata.tables['evidence'].c['source_id'], unique=False)
    sa.Table('messages_chat', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('session_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('role', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('contenu', sa.Text(), primary_key=False, nullable=False),
        sa.Column('citations', sa.JSON(), primary_key=False, nullable=False),
        sa.Column('horodatage', sa.DateTime(timezone=True), primary_key=False, nullable=False),
        sa.Column('newsroom_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('dataset', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('confidentiality', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("confidentiality IN ('private','confidential')", name='ck_messages_chat_confidentiality'),
        sa.CheckConstraint("dataset IN ('real','demo','quarantine')", name='ck_messages_chat_dataset'),
        sa.ForeignKeyConstraint(['newsroom_id', 'dataset'], ['newsrooms.id', 'newsrooms.dataset'], name='fk_messages_chat_newsroom', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['session_id', 'newsroom_id', 'dataset'], ['sessions_chat.id', 'sessions_chat.newsroom_id', 'sessions_chat.dataset'], name='fk_messages_session_scope', ondelete='RESTRICT'),
        sa.UniqueConstraint('id', 'newsroom_id', 'dataset', name='uq_messages_chat_scope'),
    )
    sa.Index('ix_messages_chat_scope_created', metadata.tables['messages_chat'].c['newsroom_id'], metadata.tables['messages_chat'].c['dataset'], metadata.tables['messages_chat'].c['created_at'], unique=False)
    sa.Table('signals', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('source_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('contenu_brut', sa.Text(), primary_key=False, nullable=False),
        sa.Column('contenu_normalise', sa.Text(), primary_key=False, nullable=False),
        sa.Column('url_origine', sa.String(length=500), primary_key=False, nullable=False),
        sa.Column('horodatage_publication', sa.DateTime(timezone=True), primary_key=False, nullable=False),
        sa.Column('auteur', sa.String(length=150), primary_key=False, nullable=True),
        sa.Column('nombre_interactions', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('niveau_viralite', sa.Float(), primary_key=False, nullable=False),
        sa.Column('mots_cles_detectes', sa.JSON(), primary_key=False, nullable=False),
        sa.Column('est_urgent', sa.Boolean(), primary_key=False, nullable=False),
        sa.Column('case_id', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('status', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('newsroom_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('dataset', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('confidentiality', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("confidentiality IN ('private','confidential')", name='ck_signals_confidentiality'),
        sa.CheckConstraint("dataset IN ('real','demo','quarantine')", name='ck_signals_dataset'),
        sa.CheckConstraint('nombre_interactions >= 0', name='ck_signals_interactions'),
        sa.CheckConstraint("status IN ('new','triaged','investigating','archived')", name='ck_signals_status'),
        sa.CheckConstraint('niveau_viralite >= 0 AND niveau_viralite <= 100', name='ck_signals_virality'),
        sa.ForeignKeyConstraint(['case_id', 'newsroom_id', 'dataset'], ['cases.id', 'cases.newsroom_id', 'cases.dataset'], name='fk_signals_case_scope', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['newsroom_id', 'dataset'], ['newsrooms.id', 'newsrooms.dataset'], name='fk_signals_newsroom', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['source_id', 'newsroom_id', 'dataset'], ['sources.id', 'sources.newsroom_id', 'sources.dataset'], name='fk_signals_source_scope', ondelete='RESTRICT'),
        sa.UniqueConstraint('id', 'newsroom_id', 'dataset', name='uq_signals_scope'),
    )
    sa.Index('ix_signals_case', metadata.tables['signals'].c['case_id'], unique=False)
    sa.Index('ix_signals_scope_created', metadata.tables['signals'].c['newsroom_id'], metadata.tables['signals'].c['dataset'], metadata.tables['signals'].c['created_at'], unique=False)
    sa.Index('ix_signals_source_date', metadata.tables['signals'].c['source_id'], metadata.tables['signals'].c['horodatage_publication'], unique=False)
    sa.Index('ix_signals_urgent', metadata.tables['signals'].c['newsroom_id'], metadata.tables['signals'].c['dataset'], metadata.tables['signals'].c['est_urgent'], metadata.tables['signals'].c['horodatage_publication'], unique=False)
    sa.Table('claim_evidence', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('case_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('claim_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('evidence_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('stance', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('status', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('rationale', sa.Text(), primary_key=False, nullable=False),
        sa.Column('newsroom_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('dataset', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('confidentiality', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("confidentiality IN ('private','confidential')", name='ck_claim_evidence_confidentiality'),
        sa.CheckConstraint("dataset IN ('real','demo','quarantine')", name='ck_claim_evidence_dataset'),
        sa.CheckConstraint("stance IN ('supports','refutes','context')", name='ck_claim_evidence_stance'),
        sa.CheckConstraint("status IN ('proposed','reviewed','rejected')", name='ck_claim_evidence_status'),
        sa.ForeignKeyConstraint(['claim_id', 'case_id', 'newsroom_id', 'dataset'], ['claims.id', 'claims.case_id', 'claims.newsroom_id', 'claims.dataset'], name='fk_claim_evidence_claim', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['evidence_id', 'case_id', 'newsroom_id', 'dataset'], ['evidence.id', 'evidence.case_id', 'evidence.newsroom_id', 'evidence.dataset'], name='fk_claim_evidence_evidence', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['newsroom_id', 'dataset'], ['newsrooms.id', 'newsrooms.dataset'], name='fk_claim_evidence_newsroom', ondelete='RESTRICT'),
        sa.UniqueConstraint('claim_id', 'evidence_id', name='uq_claim_evidence_pair'),
        sa.UniqueConstraint('id', 'newsroom_id', 'dataset', name='uq_claim_evidence_scope'),
    )
    sa.Index('ix_claim_evidence_reverse', metadata.tables['claim_evidence'].c['evidence_id'], metadata.tables['claim_evidence'].c['claim_id'], unique=False)
    sa.Index('ix_claim_evidence_scope_created', metadata.tables['claim_evidence'].c['newsroom_id'], metadata.tables['claim_evidence'].c['dataset'], metadata.tables['claim_evidence'].c['created_at'], unique=False)
    sa.Table('drafts', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('signal_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('titre_suggere', sa.String(length=250), primary_key=False, nullable=False),
        sa.Column('synthese_ia', sa.Text(), primary_key=False, nullable=False),
        sa.Column('score_credibilite_indicatif', sa.Float(), primary_key=False, nullable=False),
        sa.Column('sources_croisees', sa.JSON(), primary_key=False, nullable=False),
        sa.Column('statut', sa.String(length=25), primary_key=False, nullable=False),
        sa.Column('horodatage', sa.DateTime(timezone=True), primary_key=False, nullable=False),
        sa.Column('case_id', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('claim_id', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('newsroom_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('dataset', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('confidentiality', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('claim_id IS NULL OR case_id IS NOT NULL', name='ck_drafts_claim_case'),
        sa.CheckConstraint("confidentiality IN ('private','confidential')", name='ck_drafts_confidentiality'),
        sa.CheckConstraint("dataset IN ('real','demo','quarantine')", name='ck_drafts_dataset'),
        sa.CheckConstraint('score_credibilite_indicatif >= 0 AND score_credibilite_indicatif <= 100', name='ck_drafts_score'),
        sa.CheckConstraint("statut IN ('En_Attente','En_Cours','Rejete')", name='ck_drafts_status'),
        sa.ForeignKeyConstraint(['case_id', 'newsroom_id', 'dataset'], ['cases.id', 'cases.newsroom_id', 'cases.dataset'], name='fk_drafts_case_scope', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['claim_id', 'case_id', 'newsroom_id', 'dataset'], ['claims.id', 'claims.case_id', 'claims.newsroom_id', 'claims.dataset'], name='fk_drafts_claim_case', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['newsroom_id', 'dataset'], ['newsrooms.id', 'newsrooms.dataset'], name='fk_drafts_newsroom', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['signal_id', 'newsroom_id', 'dataset'], ['signals.id', 'signals.newsroom_id', 'signals.dataset'], name='fk_drafts_signal_scope', ondelete='RESTRICT'),
        sa.UniqueConstraint('signal_id', name='uq_drafts_ia_signal_id'),
        sa.UniqueConstraint('id', 'newsroom_id', 'dataset', name='uq_drafts_scope'),
    )
    sa.Index('ix_drafts_case', metadata.tables['drafts'].c['case_id'], unique=False)
    sa.Index('ix_drafts_claim', metadata.tables['drafts'].c['claim_id'], unique=False)
    sa.Index('ix_drafts_scope_created', metadata.tables['drafts'].c['newsroom_id'], metadata.tables['drafts'].c['dataset'], metadata.tables['drafts'].c['created_at'], unique=False)
    sa.Index('ix_drafts_status', metadata.tables['drafts'].c['newsroom_id'], metadata.tables['drafts'].c['dataset'], metadata.tables['drafts'].c['statut'], metadata.tables['drafts'].c['horodatage'], unique=False)
    sa.Table('media_analyses', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('utilisateur_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('type_media', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('reference_originale', sa.String(length=500), primary_key=False, nullable=False),
        sa.Column('empreinte_sha256', sa.String(length=64), primary_key=False, nullable=False),
        sa.Column('outil', sa.String(length=150), primary_key=False, nullable=False),
        sa.Column('version_outil', sa.String(length=80), primary_key=False, nullable=False),
        sa.Column('observations', sa.JSON(), primary_key=False, nullable=False),
        sa.Column('indice_indicatif', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('limites', sa.JSON(), primary_key=False, nullable=False),
        sa.Column('cree_le', sa.DateTime(timezone=True), primary_key=False, nullable=False),
        sa.Column('case_id', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('evidence_id', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('status', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('newsroom_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('dataset', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('confidentiality', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("confidentiality IN ('private','confidential')", name='ck_media_analyses_confidentiality'),
        sa.CheckConstraint("dataset IN ('real','demo','quarantine')", name='ck_media_analyses_dataset'),
        sa.CheckConstraint('evidence_id IS NULL OR case_id IS NOT NULL', name='ck_media_evidence_case'),
        sa.CheckConstraint('length(empreinte_sha256) = 64', name='ck_media_hash'),
        sa.CheckConstraint("status IN ('pending','running','completed','failed','reviewed')", name='ck_media_status'),
        sa.CheckConstraint("type_media IN ('image','video','audio','document')", name='ck_media_type'),
        sa.ForeignKeyConstraint(['newsroom_id', 'dataset'], ['newsrooms.id', 'newsrooms.dataset'], name='fk_media_analyses_newsroom', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['case_id', 'newsroom_id', 'dataset'], ['cases.id', 'cases.newsroom_id', 'cases.dataset'], name='fk_media_case_scope', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['evidence_id', 'case_id', 'newsroom_id', 'dataset'], ['evidence.id', 'evidence.case_id', 'evidence.newsroom_id', 'evidence.dataset'], name='fk_media_evidence_case', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['utilisateur_id', 'newsroom_id', 'dataset'], ['users.id', 'users.newsroom_id', 'users.dataset'], name='fk_media_user_scope', ondelete='RESTRICT'),
        sa.UniqueConstraint('id', 'newsroom_id', 'dataset', name='uq_media_analyses_scope'),
    )
    sa.Index('ix_media_analyses_scope_created', metadata.tables['media_analyses'].c['newsroom_id'], metadata.tables['media_analyses'].c['dataset'], metadata.tables['media_analyses'].c['created_at'], unique=False)
    sa.Index('ix_media_case', metadata.tables['media_analyses'].c['case_id'], unique=False)
    sa.Index('ix_media_evidence', metadata.tables['media_analyses'].c['evidence_id'], unique=False)
    sa.Index('ix_media_user', metadata.tables['media_analyses'].c['utilisateur_id'], unique=False)
    sa.Table('research_jobs', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('utilisateur_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('sujet', sa.String(length=500), primary_key=False, nullable=False),
        sa.Column('questions', sa.JSON(), primary_key=False, nullable=False),
        sa.Column('periode', sa.String(length=100), primary_key=False, nullable=True),
        sa.Column('langues', sa.JSON(), primary_key=False, nullable=False),
        sa.Column('territoire', sa.String(length=150), primary_key=False, nullable=True),
        sa.Column('requetes', sa.JSON(), primary_key=False, nullable=False),
        sa.Column('documents_ouverts', sa.JSON(), primary_key=False, nullable=False),
        sa.Column('citations', sa.JSON(), primary_key=False, nullable=False),
        sa.Column('synthese', sa.Text(), primary_key=False, nullable=True),
        sa.Column('erreurs', sa.JSON(), primary_key=False, nullable=False),
        sa.Column('statut', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('modele', sa.String(length=100), primary_key=False, nullable=False),
        sa.Column('debut', sa.DateTime(timezone=True), primary_key=False, nullable=False),
        sa.Column('fin', sa.DateTime(timezone=True), primary_key=False, nullable=True),
        sa.Column('case_id', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('claim_id', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('newsroom_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('dataset', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('confidentiality', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('claim_id IS NULL OR case_id IS NOT NULL', name='ck_research_claim_case'),
        sa.CheckConstraint('fin IS NULL OR fin >= debut', name='ck_research_dates'),
        sa.CheckConstraint("confidentiality IN ('private','confidential')", name='ck_research_jobs_confidentiality'),
        sa.CheckConstraint("dataset IN ('real','demo','quarantine')", name='ck_research_jobs_dataset'),
        sa.CheckConstraint("statut IN ('queued','en_cours','terminee','partielle','echouee','cancelled')", name='ck_research_status'),
        sa.ForeignKeyConstraint(['case_id', 'newsroom_id', 'dataset'], ['cases.id', 'cases.newsroom_id', 'cases.dataset'], name='fk_research_case_scope', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['claim_id', 'case_id', 'newsroom_id', 'dataset'], ['claims.id', 'claims.case_id', 'claims.newsroom_id', 'claims.dataset'], name='fk_research_claim_case', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['newsroom_id', 'dataset'], ['newsrooms.id', 'newsrooms.dataset'], name='fk_research_jobs_newsroom', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['utilisateur_id', 'newsroom_id', 'dataset'], ['users.id', 'users.newsroom_id', 'users.dataset'], name='fk_research_user_scope', ondelete='RESTRICT'),
        sa.UniqueConstraint('id', 'newsroom_id', 'dataset', name='uq_research_jobs_scope'),
    )
    sa.Index('ix_research_case', metadata.tables['research_jobs'].c['case_id'], unique=False)
    sa.Index('ix_research_claim', metadata.tables['research_jobs'].c['claim_id'], unique=False)
    sa.Index('ix_research_jobs_scope_created', metadata.tables['research_jobs'].c['newsroom_id'], metadata.tables['research_jobs'].c['dataset'], metadata.tables['research_jobs'].c['created_at'], unique=False)
    sa.Index('ix_research_status', metadata.tables['research_jobs'].c['newsroom_id'], metadata.tables['research_jobs'].c['dataset'], metadata.tables['research_jobs'].c['statut'], unique=False)
    sa.Index('ix_research_user', metadata.tables['research_jobs'].c['utilisateur_id'], unique=False)
    sa.Table('publications', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('draft_id', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('titre_final', sa.String(length=250), primary_key=False, nullable=False),
        sa.Column('corps_article', sa.Text(), primary_key=False, nullable=False),
        sa.Column('categorie', sa.String(length=50), primary_key=False, nullable=False),
        sa.Column('statut_verification', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('id_journaliste_validateur', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('horodatage_validation', sa.DateTime(timezone=True), primary_key=False, nullable=False),
        sa.Column('contenu_optimise_sms', sa.String(length=480), primary_key=False, nullable=False),
        sa.Column('status', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('revision', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), primary_key=False, nullable=True),
        sa.Column('newsroom_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('dataset', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('confidentiality', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("confidentiality IN ('private','confidential','public')", name='ck_publications_confidentiality'),
        sa.CheckConstraint("dataset IN ('real','demo','quarantine')", name='ck_publications_dataset'),
        sa.CheckConstraint("confidentiality != 'public' OR (status = 'published' AND published_at IS NOT NULL)", name='ck_publications_release'),
        sa.CheckConstraint('revision >= 1', name='ck_publications_revision'),
        sa.CheckConstraint("status IN ('scheduled','published','withdrawn','archived')", name='ck_publications_status'),
        sa.CheckConstraint("statut_verification IN ('Vrai','Faux','Trompeur')", name='ck_publications_verdict'),
        sa.ForeignKeyConstraint(['draft_id', 'newsroom_id', 'dataset'], ['drafts.id', 'drafts.newsroom_id', 'drafts.dataset'], name='fk_publications_draft_scope', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['newsroom_id', 'dataset'], ['newsrooms.id', 'newsrooms.dataset'], name='fk_publications_newsroom', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['id_journaliste_validateur', 'newsroom_id', 'dataset'], ['users.id', 'users.newsroom_id', 'users.dataset'], name='fk_publications_validator_scope', ondelete='RESTRICT'),
        sa.UniqueConstraint('draft_id', name='uq_publications_draft'),
        sa.UniqueConstraint('id', 'newsroom_id', 'dataset', name='uq_publications_scope'),
    )
    sa.Index('ix_publications_public', metadata.tables['publications'].c['newsroom_id'], metadata.tables['publications'].c['dataset'], metadata.tables['publications'].c['confidentiality'], metadata.tables['publications'].c['status'], metadata.tables['publications'].c['published_at'], unique=False)
    sa.Index('ix_publications_scope_created', metadata.tables['publications'].c['newsroom_id'], metadata.tables['publications'].c['dataset'], metadata.tables['publications'].c['created_at'], unique=False)
    sa.Index('ix_publications_validator', metadata.tables['publications'].c['id_journaliste_validateur'], unique=False)
    sa.Table('corrections_audit', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('publication_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('actor_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('action', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('status', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('reason', sa.Text(), primary_key=False, nullable=False),
        sa.Column('before', sa.JSON(), primary_key=False, nullable=False),
        sa.Column('after', sa.JSON(), primary_key=False, nullable=False),
        sa.Column('newsroom_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('dataset', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('confidentiality', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("action IN ('published','corrected','withdrawn','restored')", name='ck_audit_action'),
        sa.CheckConstraint("status = 'recorded'", name='ck_audit_status'),
        sa.CheckConstraint("confidentiality IN ('private','confidential')", name='ck_corrections_audit_confidentiality'),
        sa.CheckConstraint("dataset IN ('real','demo','quarantine')", name='ck_corrections_audit_dataset'),
        sa.ForeignKeyConstraint(['actor_id', 'newsroom_id', 'dataset'], ['users.id', 'users.newsroom_id', 'users.dataset'], name='fk_audit_actor_scope', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['publication_id', 'newsroom_id', 'dataset'], ['publications.id', 'publications.newsroom_id', 'publications.dataset'], name='fk_audit_publication_scope', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['newsroom_id', 'dataset'], ['newsrooms.id', 'newsrooms.dataset'], name='fk_corrections_audit_newsroom', ondelete='RESTRICT'),
        sa.UniqueConstraint('id', 'newsroom_id', 'dataset', name='uq_corrections_audit_scope'),
    )
    sa.Index('ix_audit_actor', metadata.tables['corrections_audit'].c['actor_id'], unique=False)
    sa.Index('ix_audit_publication_date', metadata.tables['corrections_audit'].c['publication_id'], metadata.tables['corrections_audit'].c['created_at'], unique=False)
    sa.Index('ix_corrections_audit_scope_created', metadata.tables['corrections_audit'].c['newsroom_id'], metadata.tables['corrections_audit'].c['dataset'], metadata.tables['corrections_audit'].c['created_at'], unique=False)
    sa.Table('sms_exchanges', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('numero_expediteur', sa.String(length=30), primary_key=False, nullable=False),
        sa.Column('message_recu', sa.Text(), primary_key=False, nullable=False),
        sa.Column('message_envoye', sa.Text(), primary_key=False, nullable=False),
        sa.Column('horodatage', sa.DateTime(timezone=True), primary_key=False, nullable=False),
        sa.Column('statut_reponse', sa.String(length=30), primary_key=False, nullable=False),
        sa.Column('publication_id', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('delivery_status', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('provider_message_id', sa.String(length=150), primary_key=False, nullable=True),
        sa.Column('newsroom_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('dataset', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('confidentiality', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), primary_key=False, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("delivery_status IN ('received','simulated','queued','sent','delivered','failed')", name='ck_sms_delivery'),
        sa.CheckConstraint("confidentiality IN ('private','confidential')", name='ck_sms_exchanges_confidentiality'),
        sa.CheckConstraint("dataset IN ('real','demo','quarantine')", name='ck_sms_exchanges_dataset'),
        sa.CheckConstraint("statut_reponse IN ('Trouve','Non_Trouve','Pending','Failed')", name='ck_sms_response'),
        sa.ForeignKeyConstraint(['newsroom_id', 'dataset'], ['newsrooms.id', 'newsrooms.dataset'], name='fk_sms_exchanges_newsroom', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['publication_id', 'newsroom_id', 'dataset'], ['publications.id', 'publications.newsroom_id', 'publications.dataset'], name='fk_sms_publication_scope', ondelete='RESTRICT'),
        sa.UniqueConstraint('provider_message_id', name=None),
        sa.UniqueConstraint('id', 'newsroom_id', 'dataset', name='uq_sms_exchanges_scope'),
    )
    sa.Index('ix_sms_exchanges_scope_created', metadata.tables['sms_exchanges'].c['newsroom_id'], metadata.tables['sms_exchanges'].c['dataset'], metadata.tables['sms_exchanges'].c['created_at'], unique=False)
    sa.Index('ix_sms_phone_date', metadata.tables['sms_exchanges'].c['numero_expediteur'], metadata.tables['sms_exchanges'].c['horodatage'], unique=False)
    sa.Index('ix_sms_publication', metadata.tables['sms_exchanges'].c['publication_id'], unique=False)
    return metadata

DEFAULTS = {'newsrooms': {'dataset': 'real', 'status': 'active'}, 'users': {'role': 'Journaliste', 'actif': True, 'status': 'active', 'newsroom_id': 1, 'dataset': 'real', 'confidentiality': 'private'}, 'contacts_journalistes': {'alertes_actives': True, 'newsroom_id': 1, 'dataset': 'real', 'confidentiality': 'private'}, 'sources': {'statut': 'Actif', 'frequence_scan_secondes': 900, 'newsroom_id': 1, 'dataset': 'real', 'confidentiality': 'private'}, 'signals': {'nombre_interactions': 0, 'niveau_viralite': 0, 'est_urgent': False, 'status': 'new', 'newsroom_id': 1, 'dataset': 'real', 'confidentiality': 'private'}, 'cases': {'description': '', 'status': 'open', 'newsroom_id': 1, 'dataset': 'real', 'confidentiality': 'private'}, 'claims': {'status': 'unverified', 'verdict': 'unknown', 'newsroom_id': 1, 'dataset': 'real', 'confidentiality': 'private'}, 'evidence': {'status': 'collected', 'newsroom_id': 1, 'dataset': 'real', 'confidentiality': 'private'}, 'claim_evidence': {'stance': 'context', 'status': 'proposed', 'rationale': '', 'newsroom_id': 1, 'dataset': 'real', 'confidentiality': 'private'}, 'drafts': {'statut': 'En_Attente', 'newsroom_id': 1, 'dataset': 'real', 'confidentiality': 'private'}, 'publications': {'status': 'published', 'revision': 1, 'newsroom_id': 1, 'dataset': 'real', 'confidentiality': 'private'}, 'research_jobs': {'statut': 'en_cours', 'newsroom_id': 1, 'dataset': 'real', 'confidentiality': 'private'}, 'media_analyses': {'status': 'completed', 'newsroom_id': 1, 'dataset': 'real', 'confidentiality': 'private'}, 'evaluations_confiance_maharavo': {'newsroom_id': 1, 'dataset': 'real', 'confidentiality': 'private'}, 'sms_exchanges': {'delivery_status': 'simulated', 'newsroom_id': 1, 'dataset': 'real', 'confidentiality': 'private'}, 'corrections_audit': {'status': 'recorded', 'newsroom_id': 1, 'dataset': 'real', 'confidentiality': 'private'}, 'documents_recherche': {'est_certifie': False, 'newsroom_id': 1, 'dataset': 'real', 'confidentiality': 'private'}, 'sessions_chat': {'titre': 'Investigation', 'newsroom_id': 1, 'dataset': 'real', 'confidentiality': 'private'}, 'messages_chat': {'newsroom_id': 1, 'dataset': 'real', 'confidentiality': 'private'}}


def preflight(connection):
    duplicate = connection.execute(sa.text(
        "SELECT draft_id FROM articles_certifies WHERE draft_id IS NOT NULL GROUP BY draft_id HAVING count(*) > 1 LIMIT 1"
    )).first()
    orphan = connection.execute(sa.text(
        "SELECT a.id FROM articles_certifies a LEFT JOIN utilisateurs u ON u.id = a.id_journaliste_validateur WHERE u.id IS NULL LIMIT 1"
    )).first()
    if duplicate or orphan:
        raise RuntimeError("Migration interrompue : publications dupliquées ou validateur absent. Réconcilier les données avant de relancer ; aucune suppression automatique.")


def add_public_views(connection):
    fields = "id,titre_final,corps_article,categorie,statut_verification,horodatage_validation,contenu_optimise_sms,newsroom_id"
    for name, dataset in (("public_publications", "real"), ("demo_publications", "demo")):
        barrier = " WITH (security_barrier=true)" if connection.dialect.name == "postgresql" else ""
        clock = "julianday(published_at) <= julianday('now')" if connection.dialect.name == "sqlite" else "published_at <= CURRENT_TIMESTAMP"
        op.execute(sa.text(f"CREATE VIEW {name}{barrier} AS SELECT {fields} FROM publications WHERE confidentiality='public' AND status='published' AND published_at IS NOT NULL AND {clock} AND dataset='{dataset}' AND statut_verification IN ('Vrai','Faux','Trompeur')"))
    op.execute(sa.text("CREATE VIEW articles_certifies_publics AS SELECT * FROM public_publications"))


def add_triggers(connection, tables):
    if connection.dialect.name == "postgresql":
        op.execute(sa.text("""CREATE FUNCTION fanilo_touch_updated_at() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN NEW.updated_at = clock_timestamp(); RETURN NEW; END $$"""))
        for table in tables:
            if table != "corrections_audit":
                op.execute(sa.text(f"CREATE TRIGGER tr_{table}_updated_at BEFORE UPDATE ON {table} FOR EACH ROW EXECUTE FUNCTION fanilo_touch_updated_at()"))
        op.execute(sa.text("""CREATE FUNCTION fanilo_immutable_audit() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN RAISE EXCEPTION 'corrections_audit is append-only'; END $$"""))
        op.execute(sa.text("CREATE TRIGGER tr_audit_immutable BEFORE UPDATE OR DELETE ON corrections_audit FOR EACH ROW EXECUTE FUNCTION fanilo_immutable_audit()"))
        op.execute(sa.text("CREATE TRIGGER tr_audit_no_truncate BEFORE TRUNCATE ON corrections_audit FOR EACH STATEMENT EXECUTE FUNCTION fanilo_immutable_audit()"))
        op.execute(sa.text("ALTER TABLE evidence ADD CONSTRAINT ck_evidence_sha256_format CHECK (sha256 IS NULL OR sha256 ~ '^[0-9a-f]{64}$')"))
        op.execute(sa.text("ALTER TABLE media_analyses ADD CONSTRAINT ck_media_sha256_format CHECK (empreinte_sha256 ~ '^[0-9a-f]{64}$')"))
    else:
        for action in ("UPDATE", "DELETE"):
            op.execute(sa.text(f"CREATE TRIGGER tr_audit_no_{action.lower()} BEFORE {action} ON corrections_audit BEGIN SELECT RAISE(ABORT, 'corrections_audit is append-only'); END"))


def upgrade():
    if context.is_offline_mode():
        raise RuntimeError("Cette migration inspecte et préserve les données existantes : exécuter en ligne sur une copie sauvegardée.")
    connection = op.get_bind()
    preflight(connection)
    op.execute(sa.text("DROP VIEW IF EXISTS articles_certifies_publics"))
    # Remove old simple foreign keys before renaming; rebuilt below as scoped composites.
    for table in LEGACY_TABLES:
        foreign = sa.inspect(connection).get_foreign_keys(table)
        if foreign:
            with op.batch_alter_table(table, naming_convention=NAMING) as batch:
                for fk in foreign:
                    name = fk["name"] or f"fk_{table}_{fk['constrained_columns'][0]}_{fk['referred_table']}"
                    batch.drop_constraint(name, type_="foreignkey")
    for old, new in RENAMES.items():
        op.rename_table(old, new)
    metadata = target_schema()
    newsroom = metadata.tables["newsrooms"]
    newsroom.create(connection)
    op.bulk_insert(newsroom, [
        {"id": 1, "slug": "default-real", "name": "Rédaction principale", "dataset": "real", "status": "active"},
        {"id": 2, "slug": "legacy-quarantine", "name": "Archives non classifiées", "dataset": "quarantine", "status": "active"},
    ])
    if connection.dialect.name == "postgresql":
        op.execute(sa.text("SELECT setval(pg_get_serial_sequence('newsrooms','id'), 2, true)"))
    existing = [RENAMES.get(name, name) for name in LEGACY_TABLES]
    added_columns = {}
    for name in existing:
        table = metadata.tables[name]
        stored = {column["name"] for column in sa.inspect(connection).get_columns(name)}
        added_columns[name] = []
        for column in table.columns:
            if column.name in stored:
                continue
            default = column.server_default
            if default is None and not column.nullable:
                value = DEFAULTS.get(name, {}).get(column.name)
                if column.name == "newsroom_id": value = 2
                elif column.name == "dataset": value = "quarantine"
                if value is None:
                    raise RuntimeError(f"Backfill explicite requis pour {name}.{column.name}")
                default = sa.text("true" if value is True else "false" if value is False else str(value)) if isinstance(value, (int, float, bool)) else sa.text("'" + str(value).replace("'", "''") + "'")
            with op.batch_alter_table(name, recreate="always" if connection.dialect.name == "sqlite" else "auto") as addition:
                addition.add_column(sa.Column(column.name, column.type, nullable=column.nullable, server_default=default))
            added_columns[name].append(column.name)
        # Retain historic domain CHECKs/indexes; replace unique keys with canonical equivalents.
        inspector = sa.inspect(connection)
        uniques = inspector.get_unique_constraints(name)
        if uniques:
            with op.batch_alter_table(name, naming_convention=NAMING) as batch:
                for unique in uniques:
                    constraint_name = unique["name"] or f"uq_{name}_{unique['column_names'][0]}"
                    batch.drop_constraint(constraint_name, type_="unique")
        for index in inspector.get_indexes(name):
            if index.get("unique"):
                op.drop_index(index["name"], table_name=name)
        with op.batch_alter_table(name, naming_convention=NAMING) as batch:
            for constraint in sorted(table.constraints, key=lambda item: item.name or ""):
                if isinstance(constraint, sa.UniqueConstraint):
                    cname = constraint.name or f"uq_{name}_{next(iter(constraint.columns)).name}"
                    batch.create_unique_constraint(cname, [column.name for column in constraint.columns])
                elif isinstance(constraint, sa.CheckConstraint):
                    batch.create_check_constraint(constraint.name, str(constraint.sqltext))
            for added in added_columns[name]:
                if table.c[added].server_default is None:
                    batch.alter_column(added, existing_type=table.c[added].type, server_default=None)
    new_tables = [table for table in metadata.sorted_tables if table.name not in existing and table.name != "newsrooms"]
    metadata.create_all(connection, tables=new_tables)
    for name in existing:
        table = metadata.tables[name]
        with op.batch_alter_table(name, naming_convention=NAMING) as batch:
            for constraint in sorted(table.foreign_key_constraints, key=lambda item: item.name):
                elements = list(constraint.elements)
                batch.create_foreign_key(constraint.name, constraint.referred_table.name,
                    [item.parent.name for item in elements], [item.column.name for item in elements], ondelete=constraint.ondelete)
        stored_indexes = {index["name"] for index in sa.inspect(connection).get_indexes(name)}
        for index in table.indexes:
            if index.name not in stored_indexes:
                index.create(connection)
    add_public_views(connection)
    add_triggers(connection, metadata.tables)


def downgrade():
    raise RuntimeError("Migration de confidentialité non réversible automatiquement : restaurer une sauvegarde revue, afin de ne pas réexposer les archives ni supprimer les preuves et l’audit.")
