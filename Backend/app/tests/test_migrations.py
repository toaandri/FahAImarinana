"""Exercise migrations on a disposable engine, including explicit legacy adoption."""
import os
os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')
os.environ.setdefault('ENVIRONMENT', 'test')
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.autogenerate import compare_metadata
from sqlalchemy import create_engine, inspect, text
from app.database.base import Base
from app import models

ROOT = Path(__file__).resolve().parents[2]


def config(connection, **options):
    cfg = Config(str(ROOT / 'alembic.ini'))
    cfg.attributes['connection'] = connection
    cfg.cmd_opts = SimpleNamespace(x=[f'{name}={value}' for name, value in options.items()])
    return cfg


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')

    def tearDown(self):
        self.engine.dispose()

    def test_upgrade_matches_models_and_downgrade_is_guarded(self):
        with self.engine.begin() as connection:
            cfg = config(connection)
            command.upgrade(cfg, 'head')
            self.assertEqual(set(inspect(connection).get_table_names()) - {'alembic_version'}, set(Base.metadata.tables))
            self.assertEqual(compare_metadata(MigrationContext.configure(connection), Base.metadata), [])
            with self.assertRaises(RuntimeError):
                command.downgrade(cfg, 'base')
            command.downgrade(config(connection, allow_drop_baseline='true'), 'base')
            self.assertEqual(set(inspect(connection).get_table_names()), {'alembic_version'})

    def test_legacy_adoption_keeps_data_and_adds_missing_chat_tables(self):
        with self.engine.begin() as connection:
            legacy_tables = [table for table in Base.metadata.sorted_tables if table.name not in {'sessions_chat', 'messages_chat'}]
            Base.metadata.create_all(connection, tables=legacy_tables)
            connection.execute(text("INSERT INTO utilisateurs (id,email,mot_de_passe_hash,role,actif) VALUES (1,'legacy@example.invalid','hash','Journaliste',true)"))
            with self.assertRaises(RuntimeError):
                command.upgrade(config(connection), 'head')
            command.upgrade(config(connection, adopt_legacy='true'), 'head')
            self.assertEqual(connection.scalar(text('SELECT count(*) FROM utilisateurs')), 1)
            self.assertIn('messages_chat', inspect(connection).get_table_names())

    def test_incompatible_legacy_schema_is_rejected_before_changes(self):
        with self.engine.begin() as connection:
            connection.execute(text('CREATE TABLE utilisateurs (id INTEGER PRIMARY KEY)'))
            with self.assertRaisesRegex(RuntimeError, 'incompatible'):
                command.upgrade(config(connection, adopt_legacy='true'), 'head')
            self.assertNotIn('sources_surveillees', inspect(connection).get_table_names())

    def test_offline_sql_generation(self):
        cfg = Config(str(ROOT / 'alembic.ini'), output_buffer=io.StringIO())
        command.upgrade(cfg, 'head', sql=True)
        self.assertIn('CREATE TABLE messages_chat', cfg.output_buffer.getvalue())


if __name__ == '__main__':
    unittest.main()
