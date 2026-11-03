"""Use JOURNALISTE as the only human role and grant it all human permissions."""
from alembic import op
import sqlalchemy as sa

revision = '0010_unify_human_roles'
down_revision = '0009_all_human_accounts_admin'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(sa.text(
        "UPDATE users SET role='JOURNALISTE', auth_version=auth_version + 1 "
        "WHERE account_type='human' AND role <> 'JOURNALISTE'"
    ))
    op.execute(sa.text("UPDATE invitations SET role='JOURNALISTE' WHERE role <> 'JOURNALISTE'"))

    with op.batch_alter_table('users') as batch:
        batch.drop_constraint('ck_users_role', type_='check')
        batch.create_check_constraint('ck_users_role', "role IN ('JOURNALISTE','SERVICE_IA')")
    with op.batch_alter_table('invitations') as batch:
        batch.drop_constraint('ck_invitation_role', type_='check')
        batch.create_check_constraint('ck_invitation_role', "role = 'JOURNALISTE'")


def downgrade():
    raise RuntimeError('Role unification is irreversible because previous human roles are not retained.')
