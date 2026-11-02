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

    def test_public_database_role_cannot_read_private_tables_or_demo_view(self):
        from sqlalchemy.exc import DBAPIError
        from app.database.public import verify_public_role
        command.upgrade(self.config(), 'head')
        self.connection.commit()
        role = 'fanilo_reader_' + uuid4().hex
        try:
            self.connection.exec_driver_sql(f'CREATE ROLE "{role}" NOLOGIN NOSUPERUSER NOBYPASSRLS')
            self.connection.exec_driver_sql(f'GRANT USAGE ON SCHEMA "{self.schema}" TO "{role}"')
            self.connection.exec_driver_sql(f'GRANT SELECT ON "{self.schema}".public_publications TO "{role}"')
            self.connection.exec_driver_sql(f'SET LOCAL ROLE "{role}"')
            verify_public_role(self.connection)
            self.assertEqual(self.connection.scalar(text('SELECT count(*) FROM public_publications')), 0)
            for table in ['publications','drafts','evidence','research_jobs','media_analyses','users','sms_exchanges','demo_publications']:
                with self.assertRaises(DBAPIError):
                    with self.connection.begin_nested():
                        self.connection.exec_driver_sql(f'SELECT * FROM {table}')
            self.connection.exec_driver_sql('RESET ROLE')
            self.connection.exec_driver_sql(f'GRANT SELECT ON "{self.schema}".demo_publications TO "{role}"')
            self.connection.exec_driver_sql(f'SET LOCAL ROLE "{role}"')
            with self.assertRaisesRegex(RuntimeError,'démonstrations'):
                verify_public_role(self.connection)
        finally:
            # Role creation/grants are transactional: rollback removes the test role.
            self.connection.rollback()

    def test_legacy_publications_are_quarantined_and_not_automatically_released(self):
        command.upgrade(self.config(), '0001_modular_baseline')
        self.connection.exec_driver_sql("INSERT INTO utilisateurs (id,email,mot_de_passe_hash,role,actif) VALUES (1,'legacy@example.invalid','hash','Journaliste',true)")
        self.connection.exec_driver_sql("INSERT INTO articles_certifies (titre_final,corps_article,categorie,statut_verification,id_journaliste_validateur,horodatage_validation,contenu_optimise_sms) VALUES ('Legacy title','Legacy content','Legacy','Vrai',1,CURRENT_TIMESTAMP,'Legacy SMS')")
        self.connection.commit()
        command.upgrade(self.config(), 'head')
        row=self.connection.execute(text('SELECT dataset,confidentiality,newsroom_id FROM publications')).one()
        self.assertEqual(tuple(row),('quarantine','private',2))
        self.assertEqual(self.connection.scalar(text('SELECT count(*) FROM public_publications')),0)
        self.assertEqual(self.connection.scalar(text('SELECT count(*) FROM demo_publications')),0)

    def test_invalid_legacy_validator_aborts_without_renaming_or_deleting(self):
        command.upgrade(self.config(), '0001_modular_baseline')
        self.connection.exec_driver_sql("INSERT INTO articles_certifies (titre_final,corps_article,categorie,statut_verification,id_journaliste_validateur,horodatage_validation,contenu_optimise_sms) VALUES ('Orphan','Content','Legacy','Vrai',999,CURRENT_TIMESTAMP,'SMS')")
        self.connection.commit()
        with self.assertRaisesRegex(RuntimeError,'validateur absent'):
            command.upgrade(self.config(), 'head')
        self.assertIn('articles_certifies',inspect(self.connection).get_table_names())
        self.assertNotIn('publications',inspect(self.connection).get_table_names())
        self.assertEqual(self.connection.scalar(text('SELECT count(*) FROM articles_certifies')),1)

    def test_adoption_of_actual_legacy_sql_preserves_data_and_view(self):
        sql = (ROOT / 'database/fanilo_postgresql.sql').read_text()
        # Keep transaction ownership with this test connection.
        sql = '\n'.join(line for line in sql.splitlines() if line.strip() not in {'BEGIN;', 'COMMIT;'})
        self.connection.exec_driver_sql(sql)
        self.connection.exec_driver_sql("INSERT INTO utilisateurs (email, mot_de_passe_hash) VALUES ('legacy@example.invalid', 'hash')")
        self.connection.commit()
        command.upgrade(self.config(adopt=True), 'head')
        self.assertEqual(self.connection.scalar(text('SELECT count(*) FROM users')), 1)
        self.assertIn('messages_chat', inspect(self.connection).get_table_names())
        self.assertIn('articles_certifies_publics', inspect(self.connection).get_view_names())
