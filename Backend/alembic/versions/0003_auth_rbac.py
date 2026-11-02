"""Explicit RBAC, revocable sessions, invitations and version validation.
Revision ID: 0003_auth_rbac
"""
from alembic import op,context
import sqlalchemy as sa
import re

revision='0003_auth_rbac'
down_revision='0002_investigation_storage'
branch_labels=None
depends_on=None


def auth_schema():
    metadata=sa.MetaData()
    sa.Table('newsrooms',metadata,sa.Column('id',sa.Integer,primary_key=True),sa.Column('dataset',sa.String(15)),
             sa.UniqueConstraint('id','dataset'))
    sa.Table('users',metadata,sa.Column('id',sa.Integer,primary_key=True),sa.Column('newsroom_id',sa.Integer),
             sa.Column('dataset',sa.String(15)),sa.UniqueConstraint('id','newsroom_id','dataset'))
    sa.Table('auth_sessions',metadata,
        sa.Column('id',sa.String(length=32),primary_key=True,nullable=False),
        sa.Column('user_id',sa.Integer(),primary_key=False,nullable=False),
        sa.Column('auth_version',sa.Integer(),primary_key=False,nullable=False),
        sa.Column('expires_at',sa.DateTime(timezone=True),primary_key=False,nullable=False),
        sa.Column('revoked_at',sa.DateTime(timezone=True),primary_key=False,nullable=True),
        sa.Column('revocation_reason',sa.String(length=100),primary_key=False,nullable=True),
        sa.Column('user_agent',sa.String(length=250),primary_key=False,nullable=False),
        sa.Column('newsroom_id',sa.Integer(),primary_key=False,nullable=False),
        sa.Column('dataset',sa.String(length=15),primary_key=False,nullable=False),
        sa.Column('confidentiality',sa.String(length=15),primary_key=False,nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),primary_key=False,nullable=False,server_default=sa.func.now()),
        sa.Column('updated_at',sa.DateTime(timezone=True),primary_key=False,nullable=False,server_default=sa.func.now()),
        sa.CheckConstraint("confidentiality IN ('private','confidential')",name='ck_auth_sessions_confidentiality'),
        sa.CheckConstraint("dataset IN ('real','demo','quarantine')",name='ck_auth_sessions_dataset'),
        sa.CheckConstraint('expires_at > created_at',name='ck_auth_sessions_expiry'),
        sa.CheckConstraint('auth_version >= 1',name='ck_auth_sessions_version'),
        sa.ForeignKeyConstraint(['newsroom_id', 'dataset'],['newsrooms.id', 'newsrooms.dataset'],name='fk_auth_sessions_newsroom',ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['user_id', 'newsroom_id', 'dataset'],['users.id', 'users.newsroom_id', 'users.dataset'],name='fk_auth_sessions_user',ondelete='RESTRICT'),
        sa.UniqueConstraint('id', 'newsroom_id', 'dataset',name='uq_auth_sessions_scope'),
    )
    sa.Index('ix_auth_sessions_scope_created',metadata.tables['auth_sessions'].c['newsroom_id'], metadata.tables['auth_sessions'].c['dataset'], metadata.tables['auth_sessions'].c['created_at'],unique=False)
    sa.Index('ix_auth_sessions_user_revoked',metadata.tables['auth_sessions'].c['user_id'], metadata.tables['auth_sessions'].c['revoked_at'],unique=False)
    sa.Table('contributions',metadata,
        sa.Column('id',sa.Integer(),primary_key=True,nullable=False),
        sa.Column('submitted_by_id',sa.Integer(),primary_key=False,nullable=False),
        sa.Column('parent_id',sa.Integer(),primary_key=False,nullable=True),
        sa.Column('kind',sa.String(length=20),primary_key=False,nullable=False),
        sa.Column('content',sa.Text(),primary_key=False,nullable=False),
        sa.Column('reference_url',sa.String(length=500),primary_key=False,nullable=True),
        sa.Column('status',sa.String(length=20),primary_key=False,nullable=False),
        sa.Column('newsroom_id',sa.Integer(),primary_key=False,nullable=False),
        sa.Column('dataset',sa.String(length=15),primary_key=False,nullable=False),
        sa.Column('confidentiality',sa.String(length=15),primary_key=False,nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),primary_key=False,nullable=False,server_default=sa.func.now()),
        sa.Column('updated_at',sa.DateTime(timezone=True),primary_key=False,nullable=False,server_default=sa.func.now()),
        sa.CheckConstraint("kind IN ('signal','information')",name='ck_contribution_kind'),
        sa.CheckConstraint("status IN ('submitted','reviewed','rejected')",name='ck_contribution_status'),
        sa.CheckConstraint("confidentiality IN ('private','confidential')",name='ck_contributions_confidentiality'),
        sa.CheckConstraint("dataset IN ('real','demo','quarantine')",name='ck_contributions_dataset'),
        sa.ForeignKeyConstraint(['submitted_by_id', 'newsroom_id', 'dataset'],['users.id', 'users.newsroom_id', 'users.dataset'],name='fk_contribution_actor',ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['parent_id', 'newsroom_id', 'dataset'],['contributions.id', 'contributions.newsroom_id', 'contributions.dataset'],name='fk_contribution_parent',ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['newsroom_id', 'dataset'],['newsrooms.id', 'newsrooms.dataset'],name='fk_contributions_newsroom',ondelete='RESTRICT'),
        sa.UniqueConstraint('id', 'newsroom_id', 'dataset',name='uq_contributions_scope'),
    )
    sa.Index('ix_contributions_scope_created',metadata.tables['contributions'].c['newsroom_id'], metadata.tables['contributions'].c['dataset'], metadata.tables['contributions'].c['created_at'],unique=False)
    sa.Index('ix_contributions_submitted_by_id',metadata.tables['contributions'].c['submitted_by_id'],unique=False)
    sa.Table('invitations',metadata,
        sa.Column('id',sa.String(length=32),primary_key=True,nullable=False),
        sa.Column('email',sa.String(length=255),primary_key=False,nullable=False),
        sa.Column('role',sa.String(length=30),primary_key=False,nullable=False),
        sa.Column('invited_by_id',sa.Integer(),primary_key=False,nullable=False),
        sa.Column('token_hash',sa.String(length=64),primary_key=False,nullable=False),
        sa.Column('expires_at',sa.DateTime(timezone=True),primary_key=False,nullable=False),
        sa.Column('consumed_at',sa.DateTime(timezone=True),primary_key=False,nullable=True),
        sa.Column('newsroom_id',sa.Integer(),primary_key=False,nullable=False),
        sa.Column('dataset',sa.String(length=15),primary_key=False,nullable=False),
        sa.Column('confidentiality',sa.String(length=15),primary_key=False,nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),primary_key=False,nullable=False,server_default=sa.func.now()),
        sa.Column('updated_at',sa.DateTime(timezone=True),primary_key=False,nullable=False,server_default=sa.func.now()),
        sa.CheckConstraint("role IN ('JOURNALISTE','EDITEUR','ADMINISTRATEUR','CONTRIBUTEUR','LECTEUR')",name='ck_invitation_role'),
        sa.CheckConstraint("confidentiality IN ('private','confidential')",name='ck_invitations_confidentiality'),
        sa.CheckConstraint("dataset IN ('real','demo','quarantine')",name='ck_invitations_dataset'),
        sa.ForeignKeyConstraint(['invited_by_id', 'newsroom_id', 'dataset'],['users.id', 'users.newsroom_id', 'users.dataset'],name='fk_invitation_actor',ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['newsroom_id', 'dataset'],['newsrooms.id', 'newsrooms.dataset'],name='fk_invitations_newsroom',ondelete='RESTRICT'),
        sa.UniqueConstraint('token_hash',name=None),
        sa.UniqueConstraint('id', 'newsroom_id', 'dataset',name='uq_invitations_scope'),
    )
    sa.Index('ix_invitation_email',metadata.tables['invitations'].c['email'],unique=False)
    sa.Index('ix_invitations_scope_created',metadata.tables['invitations'].c['newsroom_id'], metadata.tables['invitations'].c['dataset'], metadata.tables['invitations'].c['created_at'],unique=False)
    sa.Table('technical_settings',metadata,
        sa.Column('id',sa.Integer(),primary_key=True,nullable=False),
        sa.Column('key',sa.String(length=80),primary_key=False,nullable=False),
        sa.Column('value',sa.Integer(),primary_key=False,nullable=False),
        sa.Column('updated_by_id',sa.Integer(),primary_key=False,nullable=False),
        sa.Column('newsroom_id',sa.Integer(),primary_key=False,nullable=False),
        sa.Column('dataset',sa.String(length=15),primary_key=False,nullable=False),
        sa.Column('confidentiality',sa.String(length=15),primary_key=False,nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),primary_key=False,nullable=False,server_default=sa.func.now()),
        sa.Column('updated_at',sa.DateTime(timezone=True),primary_key=False,nullable=False,server_default=sa.func.now()),
        sa.CheckConstraint("key IN ('ingestion_batch_size','research_result_limit')",name='ck_setting_key'),
        sa.CheckConstraint("confidentiality IN ('private','confidential')",name='ck_technical_settings_confidentiality'),
        sa.CheckConstraint("dataset IN ('real','demo','quarantine')",name='ck_technical_settings_dataset'),
        sa.ForeignKeyConstraint(['updated_by_id', 'newsroom_id', 'dataset'],['users.id', 'users.newsroom_id', 'users.dataset'],name='fk_setting_actor',ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['newsroom_id', 'dataset'],['newsrooms.id', 'newsrooms.dataset'],name='fk_technical_settings_newsroom',ondelete='RESTRICT'),
        sa.UniqueConstraint('newsroom_id', 'dataset', 'key',name='uq_setting_key_scope'),
        sa.UniqueConstraint('id', 'newsroom_id', 'dataset',name='uq_technical_settings_scope'),
    )
    sa.Index('ix_technical_settings_scope_created',metadata.tables['technical_settings'].c['newsroom_id'], metadata.tables['technical_settings'].c['dataset'], metadata.tables['technical_settings'].c['created_at'],unique=False)
    sa.Table('refresh_tokens',metadata,
        sa.Column('id',sa.String(length=32),primary_key=True,nullable=False),
        sa.Column('session_id',sa.String(length=32),primary_key=False,nullable=False),
        sa.Column('token_hash',sa.String(length=64),primary_key=False,nullable=False),
        sa.Column('expires_at',sa.DateTime(timezone=True),primary_key=False,nullable=False),
        sa.Column('used_at',sa.DateTime(timezone=True),primary_key=False,nullable=True),
        sa.Column('newsroom_id',sa.Integer(),primary_key=False,nullable=False),
        sa.Column('dataset',sa.String(length=15),primary_key=False,nullable=False),
        sa.Column('confidentiality',sa.String(length=15),primary_key=False,nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),primary_key=False,nullable=False,server_default=sa.func.now()),
        sa.Column('updated_at',sa.DateTime(timezone=True),primary_key=False,nullable=False,server_default=sa.func.now()),
        sa.CheckConstraint("confidentiality IN ('private','confidential')",name='ck_refresh_tokens_confidentiality'),
        sa.CheckConstraint("dataset IN ('real','demo','quarantine')",name='ck_refresh_tokens_dataset'),
        sa.ForeignKeyConstraint(['session_id', 'newsroom_id', 'dataset'],['auth_sessions.id', 'auth_sessions.newsroom_id', 'auth_sessions.dataset'],name='fk_refresh_session',ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['newsroom_id', 'dataset'],['newsrooms.id', 'newsrooms.dataset'],name='fk_refresh_tokens_newsroom',ondelete='RESTRICT'),
        sa.UniqueConstraint('token_hash',name=None),
        sa.UniqueConstraint('id', 'newsroom_id', 'dataset',name='uq_refresh_tokens_scope'),
    )
    sa.Index('ix_refresh_expiry',metadata.tables['refresh_tokens'].c['expires_at'],unique=False)
    sa.Index('ix_refresh_session',metadata.tables['refresh_tokens'].c['session_id'],unique=False)
    sa.Index('ix_refresh_tokens_scope_created',metadata.tables['refresh_tokens'].c['newsroom_id'], metadata.tables['refresh_tokens'].c['dataset'], metadata.tables['refresh_tokens'].c['created_at'],unique=False)
    return metadata


def upgrade():
    if context.is_offline_mode():
        raise RuntimeError("Exécuter cette migration en ligne.")
    connection=op.get_bind()
    checks=sa.inspect(connection).get_check_constraints("users")
    with op.batch_alter_table("users") as batch:
        for check in checks:
            if re.search(r"\brole\b",check["sqltext"],re.I):
                batch.drop_constraint(check["name"],type_="check")
        batch.add_column(sa.Column('account_type',sa.String(length=10),nullable=False,server_default=sa.text("'human'")))
        batch.add_column(sa.Column('auth_version',sa.Integer(),nullable=False,server_default=sa.text("1")))
        batch.add_column(sa.Column('service_permissions',sa.JSON(),nullable=False,server_default=sa.text("'[]'")))
    op.execute(sa.text("UPDATE users SET role=CASE role WHEN 'Journaliste' THEN 'JOURNALISTE' WHEN 'Editeur' THEN 'EDITEUR' ELSE role END"))
    with op.batch_alter_table('users') as batch:
        batch.create_check_constraint('ck_users_auth_version','auth_version >= 1')
        batch.create_check_constraint('ck_users_identity_role',"(account_type='service' AND role='SERVICE_IA') OR (account_type='human' AND role!='SERVICE_IA')")
        batch.create_check_constraint('ck_users_role',"role IN ('JOURNALISTE','EDITEUR','ADMINISTRATEUR','CONTRIBUTEUR','LECTEUR','SERVICE_IA')")
        batch.alter_column('account_type',existing_type=sa.String(length=10),server_default=None)
        batch.alter_column('auth_version',existing_type=sa.Integer(),server_default=None)
        batch.alter_column('service_permissions',existing_type=sa.JSON(),server_default=None)
    with op.batch_alter_table("drafts") as batch:
        batch.add_column(sa.Column('version',sa.Integer(),nullable=False,server_default=sa.text("1")))
        batch.add_column(sa.Column('validated_version',sa.Integer(),nullable=True))
        batch.add_column(sa.Column('validated_by_id',sa.Integer(),nullable=True))
        batch.add_column(sa.Column('validated_at',sa.DateTime(timezone=True),nullable=True))
        batch.add_column(sa.Column('approved_payload',sa.JSON(),nullable=True))
        batch.add_column(sa.Column('approved_payload_hash',sa.String(length=64),nullable=True))
        batch.add_column(sa.Column('review_notes',sa.Text(),nullable=False,server_default=sa.text("''")))
        batch.create_check_constraint('ck_drafts_validation','validated_version IS NULL OR (validated_version=version AND validated_by_id IS NOT NULL AND validated_at IS NOT NULL AND approved_payload_hash IS NOT NULL)')
        batch.create_check_constraint('ck_drafts_version','version >= 1')
        batch.create_foreign_key('fk_drafts_validator','users',['validated_by_id','newsroom_id','dataset'],['id','newsroom_id','dataset'],ondelete='RESTRICT')
    with op.batch_alter_table('drafts') as batch:
        batch.alter_column('version',existing_type=sa.Integer(),server_default=None)
        batch.alter_column('review_notes',existing_type=sa.Text(),server_default=None)
    metadata=auth_schema()
    metadata.create_all(connection,tables=[table for table in metadata.sorted_tables if table.name not in {'users','newsrooms'}])
    if connection.dialect.name=='postgresql':
        for table in metadata.tables:
            if table not in {'users','newsrooms'}:
                op.execute(sa.text(f'CREATE TRIGGER tr_{table}_updated_at BEFORE UPDATE ON {table} FOR EACH ROW EXECUTE FUNCTION fanilo_touch_updated_at()'))
        op.execute(sa.text("""CREATE FUNCTION fanilo_immutable_identity() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN IF OLD.account_type <> NEW.account_type THEN RAISE EXCEPTION 'identity type is immutable'; END IF; RETURN NEW; END $$"""))
        op.execute(sa.text('CREATE TRIGGER tr_users_identity BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION fanilo_immutable_identity()'))
    else:
        op.execute(sa.text("CREATE TRIGGER tr_users_identity BEFORE UPDATE OF account_type ON users WHEN OLD.account_type != NEW.account_type BEGIN SELECT RAISE(ABORT,'identity type is immutable'); END"))


def downgrade():
    raise RuntimeError('Cette migration révoque le modèle de jetons historique ; restaurer une sauvegarde revue plutôt que réactiver des accès non révocables.')
