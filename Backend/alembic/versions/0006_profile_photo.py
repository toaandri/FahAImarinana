"""Persist each account's profile image in the private database."""
from alembic import op
import sqlalchemy as sa

revision = '0006_profile_photo'
down_revision = '0005_video_vision'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('profile_photo', sa.LargeBinary(), nullable=True))


def downgrade():
    raise RuntimeError('Les photos de profil doivent être conservées ; pas de suppression automatique.')
