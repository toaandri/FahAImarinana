"""Explicit real-provider smoke test using only a tiny generated, non-private video."""
from pathlib import Path
import argparse
import base64
from datetime import datetime, timezone
import subprocess
import sys
import tempfile
import time
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.schemas.vision import VideoClipRequest
from app.integrations.ai.gemini import analyze_video_clip, GeminiUnavailableError


def verify_http(clip, directory):
    import os
    import secrets
    os.environ['DATABASE_URL'] = 'sqlite:///' + str(Path(directory) / 'vision-http.sqlite3')
    os.environ['PUBLIC_DATABASE_URL'] = ''
    os.environ['ENVIRONMENT'] = 'test'
    os.environ['JWT_SECRET'] = secrets.token_urlsafe(48)
    os.environ['AUTO_CREATE_TABLES'] = 'false'
    from alembic import command
    from alembic.config import Config
    from fastapi.testclient import TestClient
    from app.main import create_app
    from app.tests.fixtures import make_account, system_session
    from app.models import MediaAnalysis
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / 'alembic.ini'))
    config.set_main_option('script_location', str(root / 'alembic'))
    command.upgrade(config, 'head')
    make_account('JOURNALISTE', email='vision-http-test@example.invalid')
    with TestClient(create_app()) as client:
        login = client.post('/api/v1/auth/login', json={
            'email': 'vision-http-test@example.invalid', 'mot_de_passe': 'password123'})
        if login.status_code != 200:
            print('GEMINI_VISION_HTTP_FAILED authentication', login.status_code)
            return 1
        headers = {'Authorization': 'Bearer ' + login.json()['access_token']}
        started = time.monotonic()
        response = client.post('/api/v1/vision/video', headers=headers, json=clip.model_dump(mode='json'))
        if response.status_code != 201:
            print('GEMINI_VISION_HTTP_FAILED', response.status_code, response.json().get('detail', 'Erreur'))
            return 1
        result = response.json()
        assert result['status'] == 'completed' and result['requires_human_review']
        assert client.get('/api/v1/public/sync').json()['items'] == []
        assert client.get('/api/v1/vision/analyses/' + str(result['id']), headers=headers).status_code == 200
        with system_session() as db:
            stored = db.get(MediaAnalysis, result['id'])
            assert stored.status == 'completed' and stored.confidentiality == 'private'
        print('GEMINI_VISION_HTTP_OK — authentification, appel réel Gemini, persistance privée et absence de fuite publique.')
        print('Modèle :', result['result']['model'])
        print('Titre :', result['result']['analysis']['title'])
        print('Durée requête :', round(time.monotonic() - started, 2), 'secondes')
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--http', action='store_true', help='Vérifier aussi authentification, API et stockage sur une base jetable.')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='fa-vision-test-') as directory:
        video = Path(directory) / 'synthetic.mp4'
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'lavfi',
            '-i', 'color=c=blue:s=160x120:r=4:d=2', '-vf',
            'drawbox=x=40:y=30:w=50:h=40:color=red:t=fill', '-an', '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(video)], check=True)
        clip = VideoClipRequest(capture_id=uuid4(), sequence=1, captured_at=datetime.now(timezone.utc),
            duration_seconds=2, video_base64=base64.b64encode(video.read_bytes()).decode())
        if args.http:
            return verify_http(clip, directory)
        try:
            result = analyze_video_clip(clip)
        except GeminiUnavailableError as exc:
            print('GEMINI_VISION_FAILED', exc.code, str(exc))
            return 1
        print('GEMINI_VISION_OK — vidéo synthétique uniquement, aucune vidéo privée envoyée.')
        print('Titre :', result.title)
        print('Observations :', len(result.observations))
        return 0


if __name__ == '__main__':
    sys.exit(main())
