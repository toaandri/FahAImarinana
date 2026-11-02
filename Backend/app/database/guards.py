"""DDL guards for disposable create_all databases; Alembic freezes its own DDL."""
from sqlalchemy import text, inspect


def install_guards(connection, tables):
    if connection.dialect.name == 'postgresql':
        connection.execute(text('''CREATE OR REPLACE FUNCTION fanilo_touch_updated_at() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN NEW.updated_at = clock_timestamp(); RETURN NEW; END $$'''))
        for table in tables:
            if table not in {'corrections_audit', 'draft_revisions'}:
                connection.execute(text(f'DROP TRIGGER IF EXISTS tr_{table}_updated_at ON {table}'))
                connection.execute(text(f'CREATE TRIGGER tr_{table}_updated_at BEFORE UPDATE ON {table} FOR EACH ROW EXECUTE FUNCTION fanilo_touch_updated_at()'))
        connection.execute(text('''CREATE OR REPLACE FUNCTION fanilo_immutable_audit() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN RAISE EXCEPTION 'corrections_audit is append-only'; END $$'''))
        connection.execute(text('DROP TRIGGER IF EXISTS tr_audit_immutable ON corrections_audit'))
        connection.execute(text('CREATE TRIGGER tr_audit_immutable BEFORE UPDATE OR DELETE ON corrections_audit FOR EACH ROW EXECUTE FUNCTION fanilo_immutable_audit()'))
        connection.execute(text('DROP TRIGGER IF EXISTS tr_audit_no_truncate ON corrections_audit'))
        connection.execute(text('CREATE TRIGGER tr_audit_no_truncate BEFORE TRUNCATE ON corrections_audit FOR EACH STATEMENT EXECUTE FUNCTION fanilo_immutable_audit()'))
        if 'draft_revisions' in tables:
            connection.execute(text('DROP TRIGGER IF EXISTS tr_revision_immutable ON draft_revisions'))
            connection.execute(text('CREATE TRIGGER tr_revision_immutable BEFORE UPDATE OR DELETE ON draft_revisions FOR EACH ROW EXECUTE FUNCTION fanilo_immutable_audit()'))
            connection.execute(text('DROP TRIGGER IF EXISTS tr_revision_no_truncate ON draft_revisions'))
            connection.execute(text('CREATE TRIGGER tr_revision_no_truncate BEFORE TRUNCATE ON draft_revisions FOR EACH STATEMENT EXECUTE FUNCTION fanilo_immutable_audit()'))
        if 'account_type' in {column['name'] for column in inspect(connection).get_columns('users')}:
            connection.execute(text("""CREATE OR REPLACE FUNCTION fanilo_immutable_identity() RETURNS trigger LANGUAGE plpgsql AS $$
                BEGIN IF OLD.account_type <> NEW.account_type THEN RAISE EXCEPTION 'identity type is immutable'; END IF; RETURN NEW; END $$"""))
            connection.execute(text('DROP TRIGGER IF EXISTS tr_users_identity ON users'))
            connection.execute(text('CREATE TRIGGER tr_users_identity BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION fanilo_immutable_identity()'))
        for table, name, expression in (
            ('evidence', 'ck_evidence_sha256_format', "sha256 IS NULL OR sha256 ~ '^[0-9a-f]{64}$'"),
            ('media_analyses', 'ck_media_sha256_format', "empreinte_sha256 ~ '^[0-9a-f]{64}$'"),
        ):
            existing = {constraint['name'] for constraint in inspect(connection).get_check_constraints(table)}
            if name not in existing:
                connection.execute(text(f'ALTER TABLE {table} ADD CONSTRAINT {name} CHECK ({expression})'))
    else:
        if 'account_type' in {column['name'] for column in inspect(connection).get_columns('users')}:
            connection.execute(text("CREATE TRIGGER IF NOT EXISTS tr_users_identity BEFORE UPDATE OF account_type ON users WHEN OLD.account_type != NEW.account_type BEGIN SELECT RAISE(ABORT,'identity type is immutable'); END"))
        for action in ('UPDATE', 'DELETE'):
            connection.execute(text(f"CREATE TRIGGER IF NOT EXISTS tr_audit_no_{action.lower()} BEFORE {action} ON corrections_audit BEGIN SELECT RAISE(ABORT, 'corrections_audit is append-only'); END"))
            if 'draft_revisions' in tables:
                connection.execute(text(f"CREATE TRIGGER IF NOT EXISTS tr_revision_no_{action.lower()} BEFORE {action} ON draft_revisions BEGIN SELECT RAISE(ABORT, 'draft_revisions is append-only'); END"))
