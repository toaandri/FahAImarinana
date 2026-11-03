"""Store the display name used by client profiles."""
from alembic import op
import sqlalchemy as sa

revision = '0008_profile_name'
down_revision = '0007_response_language'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('users', sa.Column('name', sa.String(120), nullable=False, server_default=''))

def downgrade():
    raise RuntimeError('Profile names must be preserved.')
