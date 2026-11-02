"""Add private draft history without rewriting existing records."""
from alembic import op
import sqlalchemy as sa

revision = '0004_draft_history'
down_revision = '0003_auth_rbac'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('draft_revisions',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('draft_id', sa.Integer, nullable=False),
        sa.Column('actor_id', sa.Integer, nullable=False),
        sa.Column('version', sa.Integer, nullable=False),
        sa.Column('event', sa.String(20), nullable=False),
        sa.Column('snapshot', sa.JSON, nullable=False),
        sa.Column('newsroom_id', sa.Integer, nullable=False),
        sa.Column('dataset', sa.String(15), nullable=False),
        sa.Column('confidentiality', sa.String(15), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('id', 'newsroom_id', 'dataset', name='uq_draft_revisions_scope'),
        sa.ForeignKeyConstraint(['newsroom_id','dataset'], ['newsrooms.id','newsrooms.dataset'], name='fk_draft_revisions_newsroom', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['draft_id','newsroom_id','dataset'], ['drafts.id','drafts.newsroom_id','drafts.dataset'], name='fk_revision_draft', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['actor_id','newsroom_id','dataset'], ['users.id','users.newsroom_id','users.dataset'], name='fk_revision_actor', ondelete='RESTRICT'),
        sa.CheckConstraint("dataset IN ('real','demo','quarantine')", name='ck_draft_revisions_dataset'),
        sa.CheckConstraint("confidentiality IN ('private','confidential')", name='ck_draft_revisions_confidentiality'),
        sa.CheckConstraint('version >= 1', name='ck_revision_version'),
        sa.CheckConstraint("event IN ('created','before_edit','edited','reviewed','validated','published')", name='ck_revision_event'),
    )
    op.create_index('ix_revision_draft', 'draft_revisions', ['draft_id','id'])
    op.create_index('ix_draft_revisions_scope_created', 'draft_revisions', ['newsroom_id','dataset','created_at'])
    if op.get_bind().dialect.name == 'postgresql':
        op.execute("CREATE TRIGGER tr_revision_immutable BEFORE UPDATE OR DELETE ON draft_revisions FOR EACH ROW EXECUTE FUNCTION fanilo_immutable_audit()")
        op.execute("CREATE TRIGGER tr_revision_no_truncate BEFORE TRUNCATE ON draft_revisions FOR EACH STATEMENT EXECUTE FUNCTION fanilo_immutable_audit()")
    else:
        for action in ('UPDATE', 'DELETE'):
            op.execute(f"CREATE TRIGGER tr_revision_no_{action.lower()} BEFORE {action} ON draft_revisions BEGIN SELECT RAISE(ABORT, 'draft_revisions is append-only'); END")


def downgrade():
    raise RuntimeError('Historique conservé : aucune suppression automatique autorisée.')
