# FA AI MARINANA

Projet pour le hackathon FANILO 2026 : assistance à la veille, à la recherche et à la vérification journalistique, avec validation humaine avant publication.

## Où trouver les fichiers

- `Backend/` : serveur Python/FastAPI et schéma de base de données.
- `Touche/front/` : interface Java et fichiers de démonstration mobile.
- `docker-compose.yml` : configuration locale du serveur et de PostgreSQL.
- [Cahier des charges étendu](docs/specifications/Cahier_des_charges_etendu_FA_AI_MARINANA.md) et [version Word](docs/specifications/Cahier_des_charges_etendu_FA_AI_MARINANA.docx).
- [Analyse de la vidéo et du règlement](docs/analyse/Analyse_video_et_conformite.md) et [version Word](docs/analyse/Analyse_video_et_conformite.docx).
- `docs/references/` : règlement FANILO et standard de livraison de 42.
- `docs/archives/` : trois cahiers initiaux et consignes de l’interface Java ME, conservés comme historique documentaire.

## État du projet

Le cahier étendu décrit une cible et des priorités, pas une liste de fonctionnalités déjà opérationnelles. Le document Java ME historique décrit une démonstration avec données fictives. Les fonctionnalités réelles doivent être vérifiées avant présentation. La transcription de la vidéo est automatique et peut comporter des erreurs, notamment en malagasy.

## Architecture du backend

Le backend est organisé en modules API v1, configuration/sécurité, modèles et schémas,
repositories, services, workers et intégrations. Les routes historiques `/api/...`
restent disponibles ; `/api/v1/...` expose la version documentée. Les fichiers complets,
leurs responsabilités, les migrations et les commandes de test sont décrits dans
[Backend/ARCHITECTURE.md](Backend/ARCHITECTURE.md).

Une base existante doit être sauvegardée puis adoptée explicitement avec Alembic
avant le premier démarrage de cette version ; voir la procédure dans ce document.
L'inscription publique sert uniquement au développement et doit être désactivée
en production. Les SMS restent simulés.

La [documentation de persistance](Backend/PERSISTENCE.md) décrit les treize entités,
les relations SQLAlchemy, les migrations, les fixtures et la séparation privé/public.
La migration conserve les données historiques en quarantaine, sans remise en ligne
automatique. La production exige un compte PostgreSQL public distinct en lecture seule.

## Démarrage local du backend

Avec Docker et Docker Compose installés, depuis la racine du projet :

```sh
docker compose up --build
```

La configuration expose le backend sur le port 8000 et PostgreSQL sur le port 5432. Les identifiants fournis par cette configuration servent uniquement au développement local. Le backend expose notamment l’authentification, les sources et signaux de veille,
la génération de brouillons IA, la validation humaine, le flux public/SMS et le
Copilot local sur les articles certifiés, ou web lorsque Gemini est activé. Les écritures de veille et la consultation
des brouillons exigent un jeton de journaliste ou d’éditeur ; l’inscription crée
toujours un compte journaliste. Le worker supervisé peut être déclenché avec
`POST /api/workflow/process-pending` après authentification.

Pour activer Google AI Studio, créer une clé dans [Google AI Studio](https://aistudio.google.com/apikey)
et renseigner `GEMINI_API_KEY`. Le backend utilise alors Gemini pour les brouillons
structurés et le Copilot web avec Google Search. Sans clé, il conserve le moteur local
et indique que les sorties restent des pré-analyses. L’IA ne peut jamais publier
directement un article certifié.

Le périmètre Maharavo est exposé sous `/api/maharavo` :

- `POST /research` conserve le sujet, les questions, la période, les langues,
  le territoire, les citations et l’état `terminee`, `partielle` ou `echouee`.
- `POST /media-analysis` enregistre l’empreinte, l’outil, les observations et
  les limites d’une analyse guidée ; il ne conclut jamais seul à une manipulation.
- `POST /confidence` conserve séparément l’identité de la source, la solidité
  des preuves et l’état de validation éditoriale.

Pour l’interface Java ME, les sources se trouvent dans `Touche/front/src/` et les distributions dans `Touche/front/deploy/`. Le script historique `Touche/lancement.sh` utilise des chemins propres à la machine de son auteur ; il doit être adapté à votre environnement.

## Organisation locale

Le dossier principal `C:\FahAImarinana` est le seul dossier de travail actif. `.docs-push` était une copie Git temporaire utilisée pour publier les documents et a été retirée. Les outils téléchargés dans `.analyse_deps/`, les fichiers intermédiaires conservés dans `.local-analysis/` et la vidéo originale restent locaux et sont exclus de Git. Les fichiers compilés et caches sont également exclus ; les distributions JAR/JAD existantes sont conservées.

Une branche locale `backup/avant-rangement-20261102` conserve l’historique précédant le rangement. Elle contient des outils volumineux : ne pas la pousser sur GitHub. Le code source existant n’a pas été modifié par ce rangement.

## Documents et outils IA

Les documents étendus ont été préparés avec Codex. L’analyse audio utilise une transcription locale Vosk ; les réserves et sources sont détaillées dans l’annexe. Les originaux et les références sont conservés pour permettre la relecture humaine.
