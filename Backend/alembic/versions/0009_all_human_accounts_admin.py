"""Promote existing human accounts to the administrator role."""
from alembic import op
import sqlalchemy as sa

revision = '0009_all_human_accounts_admin'
down_revision = '0008_profile_name'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(sa.text("UPDATE users SET role='ADMINISTRATEUR' WHERE account_type='human'"))

def downgrade():
    raise RuntimeError('Human account role promotion is irreversible because previous roles are not retained.')