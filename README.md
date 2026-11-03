# FA AI MARINANA

Projet pour le hackathon FANILO 2026 : assistance à la veille, à la recherche et à la vérification journalistique, avec validation humaine avant publication.

## Où trouver les fichiers

- `Backend/` : serveur Python/FastAPI et schéma de base de données.
- `Frontends/Web/` : nouvelle application Expo avec React Native et support web.
- `Touche/front/` : interface Java et fichiers de démonstration mobile.
- `docker-compose.yml` : configuration locale du serveur et de PostgreSQL.
- [Cahier des charges étendu](docs/specifications/Cahier_des_charges_etendu_FA_AI_MARINANA.md) et [version Word](docs/specifications/Cahier_des_charges_etendu_FA_AI_MARINANA.docx).
- [Analyse de la vidéo et du règlement](docs/analyse/Analyse_video_et_conformite.md) et [version Word](docs/analyse/Analyse_video_et_conformite.docx).
- `docs/references/` : règlement FANILO et standard de livraison de 42.
- `docs/archives/` : trois cahiers initiaux et consignes de l’interface Java ME, conservés comme historique documentaire.

## État du projet

L'intégration [caméra mobile et Gemini Vision](docs/GEMINI_VIDEO.md) enregistre de
courts clips et passe par le backend authentifié. Les résultats restent privés et
soumis à relecture humaine. Le parcours backend avec une vidéo synthétique, Gemini
Flash Lite et un stockage privé a été vérifié. La capture sur téléphone physique
reste à recetter dans Expo Go.

Le parcours documentaire et éditorial local est maintenant connecté : dossiers,
affirmations, preuves, recherche dans les pièces saisies, brouillons et révisions,
validation humaine, publication, consultation SMS par HTTP et synchronisation du
cache public Java ME. La recherche distante Maharavo et la livraison SMS opérateur
restent indisponibles. Voir le [rapport de livraison](docs/RAPPORT_FINAL_INTEGRATION.md)
et le [guide technique et de lancement](docs/INTEGRATION_TECHNIQUE.md).

Pour lancer le backend local avec les dépendances déjà installées :

```sh
.venv/bin/python Backend/scripts/run_local.py --create-account
.venv/bin/python Backend/scripts/run_local.py
```

Créer vos comptes administrateur, journaliste et éditeur avec `--create-account`
avant de tester les différents rôles ; les mots de passe sont demandés au terminal.
Le serveur local expose `http://127.0.0.1:8000/docs`. Le guide décrit aussi
l'installation, PostgreSQL, les migrations, le worker et la compilation mobile.

Le cahier étendu décrit une cible et des priorités, pas une liste de fonctionnalités déjà opérationnelles. Le document Java ME historique décrit une démonstration avec données fictives. Les fonctionnalités réelles doivent être vérifiées avant présentation. La transcription de la vidéo est automatique et peut comporter des erreurs, notamment en malagasy.

## Architecture du backend

Le backend est organisé en modules API v1, configuration/sécurité, modèles et schémas,
repositories, services, workers et intégrations. Les routes historiques `/api/...`
restent disponibles ; `/api/v1/...` expose la version documentée. Les fichiers complets,
leurs responsabilités, les migrations et les commandes de test sont décrits dans
[Backend/ARCHITECTURE.md](Backend/ARCHITECTURE.md).

Une base existante doit être sauvegardée puis adoptée explicitement avec Alembic
avant le premier démarrage de cette version ; voir la procédure dans ce document.
L'inscription exige une invitation nominative à usage unique, dans tous les environnements. Les SMS restent simulés.

La [documentation de persistance](Backend/PERSISTENCE.md) décrit les treize entités,
les relations SQLAlchemy, les migrations, les fixtures et la séparation privé/public.
La migration conserve les données historiques en quarantaine, sans remise en ligne
automatique. La production exige un compte PostgreSQL public distinct en lecture seule.

L’[authentification et les permissions](Backend/AUTHENTICATION.md) reposent sur six rôles explicites,
des invitations nominatives et des sessions révocables avec refresh tokens. Seul un éditeur
valide et publie ; les administrateurs et comptes IA n’héritent d’aucun droit de publication.

## Démarrage local du backend

Lancez uniquement PostgreSQL avec Docker depuis la racine du projet :

```sh
docker compose up -d postgres
```

PostgreSQL est accessible localement sur `localhost:55434`. Pour démarrer le backend
localement, copiez `Backend/.env.example` vers `Backend/.env`, puis lancez Alembic
et Uvicorn depuis `Backend/`. Les frontends se lancent séparément avec leurs scripts
npm habituels.

### Démonstration hackathon

Le seed de démonstration doit être lancé par le backend local avec `DEMO_MODE=true`.
Il charge un jeu de
données entièrement fictif dans une rédaction `demo` isolée, et publie les
articles fictifs via le flux public. Les comptes de test sont :

- `journaliste.demo@example.invalid` / `demo12345`
- `contributeur.demo@example.invalid` / `demo12345`

Pour désactiver le seed fictif, lancer Compose avec
`DEMO_MODE=false`, `DEFAULT_DATASET=real`, `PUBLIC_DATASET=real`,
`DEFAULT_NEWSROOM_ID=1` et `PUBLIC_NEWSROOM_ID=1`. Ne jamais activer le mode
demo sur une base de production. Le backend expose notamment l’authentification, les sources et signaux de veille,
la génération de brouillons IA, la validation humaine, le flux public/SMS et le
Copilot local sur les articles certifiés, ou web lorsque Gemini est activé. Les écritures et consultations privées appliquent des permissions par rôle et rédaction ;
l’inscription exige une invitation attribuant un rôle explicite. Seuls les éditeurs
peuvent valider et publier les versions. Le worker supervisé peut être déclenché avec
`POST /api/workflow/process-pending` avec un compte SERVICE_IA disposant des scopes
`tasks.run` et `drafts.create`.

Pour activer Google AI Studio, créer une clé dans [Google AI Studio](https://aistudio.google.com/apikey)
et renseigner `GEMINI_API_KEY`. Le backend utilise alors Gemini pour les brouillons
structurés et le Copilot web avec Google Search. Sans clé, il conserve le moteur local
et indique que les sorties restent des pré-analyses. L’IA ne peut jamais publier
directement un article certifié.

Pour utiliser OpenRouter dans le chatbot, renseigner `OPENROUTER_API_KEY` dans
`Backend/.env` et redémarrer le backend. `OPENROUTER_MODEL` vaut par défaut
[`openrouter/free`](https://openrouter.ai/openrouter/free) ; le délai est configurable
avec `OPENROUTER_TIMEOUT_SECONDS` (45 secondes). La clé reste côté serveur.
Le chatbot transmet la question et les extraits pertinents des documents certifiés
à OpenRouter, sans recherche web en direct. En cas d’échec, il utilise Gemini si
configuré, puis le moteur local. Les autres fonctions IA conservent leur fournisseur.

Le [rapport d’inspection et le socle du connecteur Maharavo](Backend/MAHARAVO_INTEGRATION.md)
distinguent le contrat backend proposé de l’interface externe, qui n’est pas documentée
dans ce dépôt. Aucune connexion réelle à un moteur HTTP Maharavo n’est annoncée.

Le périmètre Maharavo est exposé sous `/api/maharavo` :

- `POST /research` renvoie explicitement `503` tant que l’interface réelle et
  l’adaptateur documenté manquent ; aucun appel Gemini n’est présenté comme Maharavo.
- `POST /media-analysis` enregistre l’empreinte, l’outil, les observations et
  les limites d’une analyse guidée ; il ne conclut jamais seul à une manipulation.
- `POST /confidence` conserve séparément l’identité de la source, la solidité
  des preuves et l’état de validation éditoriale.

## Démarrage de l’application React Native

Depuis la racine du projet :

```sh
cd Frontends/Web
npm run web
```

Pour démarrer l’application sur Android, utilisez `npm run android`. Le lancement iOS nécessite macOS (`npm run ios`).

Pour l’interface Java ME connectée, les sources se trouvent dans `Touche/front/src/`.
Le script `MICROEMU_HOME=/chemin/vers/microemulator-2.0.4 bash Touche/lancement.sh`
compile et lance le client ; `--build` produit seulement le nouveau JAR/JAD dans
`Touche/front/build/`. Les distributions de `deploy/` sont les anciennes versions.
Le client utilise les vrais comptes et endpoints, sans code d'accès fixe. Son cache
hors ligne contient uniquement les publications publiques synchronisées et leur date.

## Organisation locale

Le dossier principal `C:\FahAImarinana` est le seul dossier de travail actif. `.docs-push` était une copie Git temporaire utilisée pour publier les documents et a été retirée. Les outils téléchargés dans `.analyse_deps/`, les fichiers intermédiaires conservés dans `.local-analysis/` et la vidéo originale restent locaux et sont exclus de Git. Les fichiers compilés et caches sont également exclus ; les distributions JAR/JAD existantes sont conservées.

Une branche locale `backup/avant-rangement-20261102` conserve l’historique précédant le rangement. Elle contient des outils volumineux : ne pas la pousser sur GitHub. Le code source existant n’a pas été modifié par ce rangement.

## Documents et outils IA

Les documents étendus ont été préparés avec Codex. L’analyse audio utilise une transcription locale Vosk ; les réserves et sources sont détaillées dans l’annexe. Les originaux et les références sont conservés pour permettre la relecture humaine.
