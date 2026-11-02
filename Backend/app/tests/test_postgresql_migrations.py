"""Optional PostgreSQL migration checks in isolated schemas of a disposable test DB."""
import os
import unittest
from pathlib import Path
from uuid import uuid4
from types import SimpleNamespace
from sqlalchemy import create_engine, inspect, text
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.autogenerate import compare_metadata
from app.database.base import Base
from app import models

ROOT = Path(__file__).resolve().parents[2]
URL = os.environ.get('FANILO_TEST_DATABASE_URL', '')


@unittest.skipUnless(URL.startswith('postgresql'), 'Disposable PostgreSQL URL not configured')
class PostgreSQLMigrationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(URL)
        self.schema = 'fanilo_test_' + uuid4().hex
        self.connection = self.engine.connect()
        self.connection.exec_driver_sql(f'CREATE SCHEMA "{self.schema}"')
        self.connection.exec_driver_sql(f'SET search_path TO "{self.schema}"')
        self.connection.commit()

    def tearDown(self):
        self.connection.rollback()
        self.connection.exec_driver_sql(f'DROP SCHEMA "{self.schema}" CASCADE')
        self.connection.commit()
        self.connection.close()
        self.engine.dispose()

    def config(self, adopt=False):
        cfg = Config(str(ROOT / 'alembic.ini'))
        cfg.attributes['connection'] = self.connection
        cfg.cmd_opts = SimpleNamespace(x=['adopt_legacy=true'] if adopt else [])
        return cfg

    def test_fresh_migration_matches_orm_on_postgresql(self):
        command.upgrade(self.config(), 'head')
        self.assertEqual(compare_metadata(MigrationContext.configure(self.connection), Base.metadata), [])
        self.assertEqual(set(inspect(self.connection).get_table_names()) - {'alembic_version'}, set(Base.metadata.tables))

    def test_adoption_of_actual_legacy_sql_preserves_data_and_view(self):
        sql = (ROOT / 'database/fanilo_postgresql.sql').read_text()
        # Keep transaction ownership with this test connection.
        sql = '\n'.join(line for line in sql.splitlines() if line.strip() not in {'BEGIN;', 'COMMIT;'})
        self.connection.exec_driver_sql(sql)
        self.connection.exec_driver_sql("INSERT INTO utilisateurs (email, mot_de_passe_hash) VALUES ('legacy@example.invalid', 'hash')")
        self.connection.commit()
        command.upgrade(self.config(adopt=True), 'head')
        self.assertEqual(self.connection.scalar(text('SELECT count(*) FROM utilisateurs')), 1)
        self.assertIn('messages_chat', inspect(self.connection).get_table_names())
        self.assertIn('articles_certifies_publics', inspect(self.connection).get_view_names())
