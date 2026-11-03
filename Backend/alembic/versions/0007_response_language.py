"""Persist the account's preferred AI response language."""
from alembic import op
import sqlalchemy as sa

revision = '0007_response_language'
down_revision = '0006_profile_photo'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('response_language', sa.String(4), nullable=False, server_default='auto'))


def downgrade():
    raise RuntimeError('Les préférences de langue doivent être conservées.')
