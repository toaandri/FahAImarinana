-- Run after Alembic as the database/schema owner, in the intended database.
-- No password is stored here. Provision a separate LOGIN identity in your secret manager
-- and grant it membership in fanilo_public_reader, then set PUBLIC_DATABASE_URL.
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'fanilo_public_reader') THEN
        CREATE ROLE fanilo_public_reader NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
    END IF;
END $$;
GRANT USAGE ON SCHEMA public TO fanilo_public_reader;
REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM fanilo_public_reader;
REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM fanilo_public_reader;
GRANT SELECT ON public.public_publications TO fanilo_public_reader;
-- Deliberately no grant on demo_publications, publications, users, drafts, evidence,
-- research_jobs, media_analyses, sms_exchanges or corrections_audit.
-- Production startup checks effective rights, including inherited grants.
