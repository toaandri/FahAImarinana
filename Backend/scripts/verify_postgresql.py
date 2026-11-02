"""Run the suite on an owned temporary PostgreSQL cluster, never an existing DB."""
from pathlib import Path
import getpass
import glob
import os
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import quote


def main():
    candidates=sorted(glob.glob('/usr/lib/postgresql/*/bin/initdb'),reverse=True)
    initdb=shutil.which('initdb') or (candidates[0] if candidates else None)
    if initdb is None:
        raise SystemExit('Installer PostgreSQL et ses outils initdb/pg_ctl avant ce test.')
    binary=Path(initdb).parent
    root=Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='fa-pg-test-') as directory:
        data=Path(directory)/'data'; log=Path(directory)/'postgres.log'
        subprocess.run([str(binary/'initdb'),'-D',str(data),'-A','trust','--no-locale','--encoding=UTF8'],
                       check=True,stdout=subprocess.DEVNULL)
        started=False
        try:
            # Private 0700 directory, Unix socket only. No TCP listener or existing cluster.
            subprocess.run([str(binary/'pg_ctl'),'-D',str(data),'-l',str(log),'-w','start',
                '-o',f"-F -h '' -k {directory}"],check=True,stdout=subprocess.DEVNULL)
            started=True
            env={**os.environ,'FANILO_TEST_DATABASE_URL':
                 f'postgresql+psycopg://{quote(getpass.getuser())}@/postgres?host={quote(directory,safe="")}',
                 'PUBLIC_DATABASE_URL':''}
            result=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','app/tests','-v'],cwd=root,env=env)
            return result.returncode
        finally:
            if started:
                subprocess.run([str(binary/'pg_ctl'),'-D',str(data),'-w','stop','-m','fast'],
                               check=True,stdout=subprocess.DEVNULL)


if __name__=='__main__':
    sys.exit(main())
