"""Persist uploaded photos and videos with their media type."""
from alembic import op
import sqlalchemy as sa

revision = '0011_contribution_media'
down_revision = '0010_unify_human_roles'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('contributions', sa.Column('media', sa.LargeBinary(), nullable=True))
    op.add_column('contributions', sa.Column('media_content_type', sa.String(length=150), nullable=True))


def downgrade():
    raise RuntimeError('Les médias envoyés doivent être conservés ; pas de suppression automatique.')
