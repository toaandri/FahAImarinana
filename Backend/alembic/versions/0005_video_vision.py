"""Private, idempotent video observations; preserve guided legacy media analyses."""
from alembic import op
import sqlalchemy as sa

revision = '0005_video_vision'
down_revision = '0004_draft_history'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('media_analyses', sa.Column('capture_key', sa.String(80), nullable=True))
    op.add_column('media_analyses', sa.Column('result', sa.JSON, nullable=True))
    op.create_index('uq_media_capture', 'media_analyses',
                    ['newsroom_id', 'dataset', 'utilisateur_id', 'capture_key'], unique=True)


def downgrade():
    raise RuntimeError('Les observations vidéo privées doivent être conservées ; pas de suppression automatique.')
