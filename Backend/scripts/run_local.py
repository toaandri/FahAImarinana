"""Local persistent SQLite startup; PostgreSQL deployment remains configured via Compose."""
from pathlib import Path
import argparse
import os
import secrets
import subprocess
import sys
from dotenv import load_dotenv


def main():
    root=Path(__file__).resolve().parents[1]
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8000)
    parser.add_argument('--host',default='127.0.0.1',help='Utiliser 0.0.0.0 pour un téléphone sur le réseau local.')
    parser.add_argument('--create-account',action='store_true')
    args=parser.parse_args()
    load_dotenv(root/'.env',override=False)
    if os.environ.get('ENVIRONMENT')=='production':
        parser.error('Utiliser la procédure PostgreSQL de production, pas le lanceur local.')
    local=root/'.local-data'
    local.mkdir(mode=0o700,exist_ok=True)
    secret=local/'jwt-secret'
    if not os.environ.get('JWT_SECRET'):
        if not secret.exists():
            descriptor=os.open(secret,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(descriptor,'w') as handle:
                handle.write(secrets.token_urlsafe(48))
        os.environ['JWT_SECRET']=secret.read_text().strip()
    os.environ.setdefault('ENVIRONMENT','development')
    os.environ.setdefault('DATABASE_URL','sqlite:///'+str(local/'fanilo.sqlite3'))
    os.environ.setdefault('AUTO_CREATE_TABLES','false')
    subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=root,check=True)
    if args.create_account:
        email=input('Email du compte : ').strip()
        subprocess.run([sys.executable,'-m','app.core.manage_users','--email',email],cwd=root,check=True)
        return
    print(f'Backend local : http://127.0.0.1:{args.port}/docs',flush=True)
    os.chdir(root)
    os.execv(sys.executable,[sys.executable,'-m','uvicorn','app.main:app','--host',args.host,'--port',str(args.port)])


if __name__=='__main__':
    main()
