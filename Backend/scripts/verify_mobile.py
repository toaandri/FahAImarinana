"""Compile and exercise the actual Java ME HTTP/RMS client on a disposable backend."""
from pathlib import Path
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request


def main():
    root=Path(__file__).resolve().parents[2]
    emulator=Path(os.environ.get('MICROEMU_HOME','/tmp/opencode/microemulator-2.0.4'))
    if not (emulator/'microemulator.jar').is_file():
        raise SystemExit('Définir MICROEMU_HOME vers une installation MicroEmulator 2.0.4 existante.')
    with tempfile.TemporaryDirectory(prefix='fa-mobile-test-') as directory:
        scratch=Path(directory); classes=scratch/'classes'; classes.mkdir()
        env={**os.environ,'DATABASE_URL':'sqlite:///'+str(scratch/'backend.sqlite3'),
             'ENVIRONMENT':'test','JWT_SECRET':secrets.token_urlsafe(48),'GEMINI_API_KEY':'',
             'PUBLIC_DATABASE_URL':'','AUTO_CREATE_TABLES':'false'}
        backend=root/'Backend'
        subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=backend,env=env,check=True)
        seed="""
from app.database import SessionLocal
from app.database.scope import set_scope
from app.models import User,Source
from app.core.security import password_hash
with SessionLocal() as db:
    set_scope(db,1,'real')
    hashed=password_hash('mobile-test-password-only')
    db.add(User(email='mobile-journalist@example.invalid',mot_de_passe_hash=hashed,role='JOURNALISTE'))
    db.add(User(email='mobile-editor@example.invalid',mot_de_passe_hash=hashed,role='JOURNALISTE'))
    db.add(Source(nom='Explicit mobile test fixture',type='Web',url='https://mobile-source.example.invalid'))
    db.commit()
"""
        subprocess.run([sys.executable,'-c',seed],cwd=backend,env=env,check=True)
        # Reserve a free loopback port; never point this test at an existing backend.
        with socket.socket() as listener:
            listener.bind(('127.0.0.1',0)); port=listener.getsockname()[1]
        log=(scratch/'backend.log').open('w+')
        server=subprocess.Popen([sys.executable,'scripts/run_local.py','--port',str(port)],
                                cwd=backend,env=env,stdout=log,stderr=log)
        try:
            url=f'http://127.0.0.1:{port}'
            for _ in range(100):
                if server.poll() is not None:
                    raise RuntimeError('Backend de test arrêté au démarrage.')
                try:
                    urllib.request.urlopen(url+'/api/v1/health',timeout=1).close(); break
                except OSError:
                    time.sleep(.1)
            else:
                raise RuntimeError('Backend de test indisponible.')
            api_classpath=os.pathsep.join(str(emulator/'lib'/name) for name in ('midpapi20.jar','cldcapi11.jar'))
            sources=[str(p) for folder in ('src','tests') for p in (root/'Touche/front'/folder).rglob('*.java')]
            subprocess.run(['javac','--release','8','-cp',api_classpath,'-d',str(classes),*sources],check=True)
            subprocess.run(['java','-cp',str(classes),'CodecTest'],check=True,timeout=10)
            classpath=os.pathsep.join([str(emulator/'microemulator.jar'),str(classes)])
            result=subprocess.run(['java','-Djava.awt.headless=true','-Duser.home='+str(scratch),
                '-Dfa.test.url='+url,'-cp',classpath,'org.microemu.app.Headless','MobileSmoke'],
                capture_output=True,text=True,timeout=60)
            print(result.stdout); print(result.stderr,file=sys.stderr)
            if result.returncode!=0 or 'MOBILE_SMOKE_OK' not in result.stdout:
                raise RuntimeError('Échec du test mobile réel.')
        finally:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill(); server.wait(timeout=5)
            log.close()
    return 0


if __name__=='__main__':
    sys.exit(main())
