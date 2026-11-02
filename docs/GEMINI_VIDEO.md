# Capture mobile et analyse Gemini Vision — 3 novembre 2026

## État vérifié

L'écran mobile Direct utilise maintenant une vraie `CameraView` Expo pour enregistrer des clips, avec microphone facultatif, arrêt et rapport privé. Les analyses passent par le backend authentifié, jamais directement par une clé embarquée dans le téléphone.

**La recette de génération distante a réussi avec `gemini-3.5-flash-lite`.** Une vidéo synthétique de deux secondes (carré rouge sur fond bleu) a été analysée par Gemini. Le parcours HTTP complet a également réussi : authentification d'un journaliste, POST vidéo, appel réel à Gemini, résultat privé enregistré et absence de fuite dans le flux public. La requête d'analyse de ce test a pris **6,47 secondes**, hors capture ; cette mesure isolée ne garantit pas la latence sur un téléphone ou un autre réseau.

Les premiers essais avec `gemini-3.8-flash` avaient expiré à 45 puis 90 secondes. Le modèle vidéo est donc configurable séparément avec `GEMINI_VISION_MODEL=gemini-3.5-flash-lite`, vérifié dans cette recette. `GEMINI_MODEL` conserve le choix existant pour les autres fonctions. Il n'y a pas de changement automatique de modèle ni de simulation en cas d'échec.

La clé fournie a été enregistrée dans `Backend/.env`, protégé en lecture/écriture pour son propriétaire et ignoré par Git. Aucune valeur réelle n'est dans ce guide ou le frontend. La clé ayant été partagée dans la conversation, sa rotation reste recommandée avant un déploiement réel.

## Parcours mobile

1. Démarrer le backend et Expo, puis se connecter avec un compte journaliste autorisé à `analyses.write`.
2. Ouvrir Reportage depuis l'accueil, ou « Filmer une vidéo » depuis la préparation d'article.
3. Autoriser la caméra. Le microphone reste coupé tant que vous ne l'activez pas explicitement.
4. Démarrer : l'application vérifie la configuration du backend, enregistre un clip de six secondes, l'envoie au backend puis attend son analyse. Elle répète au maximum dix fois. Les phases « enregistrement », « analyse » et « finalisation » sont distinctes.
5. Le bouton d'arrêt termine le clip en cours et attend le résultat déjà demandé. Le passage en arrière-plan ou la sortie de l'écran interrompt la capture et annule la requête mobile ; le serveur peut encore terminer un appel déjà parti.
6. Consulter le rapport : observations horodatées relativement à chaque clip, limites, questions à vérifier et ouverture du clip local dans le lecteur du téléphone. « Actualiser les analyses enregistrées » récupère les résultats côté serveur après une coupure réseau.

**Ce mode n'est pas une vidéo continue ni un flux Live API sans interruption.** Il alterne capture et analyse de courts clips. Sa latence dépend du réseau et de Gemini. Il ne vérifie pas automatiquement l'origine, la date, le lieu ou la véracité d'une affirmation. Aucun score de crédibilité, verdict final ou publication automatique n'est produit.

Les fichiers enregistrés restent dans le cache privé du téléphone, pas dans un stockage vidéo durable sur le serveur. Le système peut nettoyer ce cache. Le rapport mobile est en mémoire et disparaît à la déconnexion ou au redémarrage ; les analyses et empreintes restent privées en base. Prévoir une collecte de preuve durable séparée si le fichier doit être archivé à long terme.

## Backend et contrat

- `GET /api/v1/vision/status` : présence de la configuration (sans valider la clé auprès de Google), modèle demandé, identifiant de capture, durée et taille maximales.
- `POST /api/v1/vision/video` : vidéo MP4/MOV en base64, UUID de capture, numéro de clip, date déclarée par l'appareil, durée déclarée, langue de réponse et éventuel `case_id`. Retourne l'analyse privée terminée ou une erreur explicite.
- `GET /api/v1/vision/analyses?capture_id=UUID` : historique de la capture pour son propriétaire, pagination `limit`/`offset`.
- `GET /api/v1/vision/analyses/{id}` : analyse du propriétaire uniquement.

Toutes ces routes exigent une session et la permission `analyses.write`. Les comptes lecteur et contributeur sont refusés. Un compte IA ne peut accéder qu'aux scopes qui lui sont explicitement attribués et ne peut toujours ni valider ni publier.

Le backend limite le clip à 4 Mio et la requête JSON à 6 Mio avant validation. Il vérifie l'encodage et la signature de conteneur MP4/MOV ; **il ne réalise pas un décodage forensique complet du fichier ni une mesure indépendante de sa durée**. Les durées acceptées vont jusqu'à dix secondes et proviennent du client ; Gemini valide le média. La caméra mobile impose aussi une durée et une taille d'enregistrement. La requête et la réponse fournisseur sont bornées ; deux appels simultanés maximum et douze soumissions par minute/IP/processus. Les déploiements multiples nécessitent des quotas partagés.

Un clip est identifié par rédaction, dataset, propriétaire et `capture_id:sequence`. Une répétition du même clip terminé retourne son résultat existant sans nouvel appel. Un contenu différent sous le même identifiant est refusé. Un clip échoué ou encore en cours n'est pas rejoué silencieusement. Une requête expirée peut avoir été traitée chez le fournisseur : vérifier l'état existant avant de filmer un nouveau clip.

Les modèles `VideoAnalysisResult` et `VideoObservation` valident le JSON généré. Une réponse incomplète, un champ éditorial inattendu ou un horodatage hors clip entraîne un échec. Le modèle est demandé avec un raisonnement réduit et un budget de sortie borné. La requête utilise le transport Gemini existant, l'API Interactions documentée, `store=false` et la révision API `2026-05-20`. MP4 est envoyé comme `video/mp4` et le MIME caméra MOV `video/quicktime` est normalisé vers `video/mov`, documenté par Google.

La migration additive `0005_video_vision` ajoute `capture_key`, `result` JSON et un index unique à `media_analyses`. Les analyses guidées historiques sont conservées avec ces champs nuls. Les statuts sont `running`, `completed`, `failed` ; l'erreur et la date de fin sont conservées dans le résultat privé. L'empreinte SHA-256 relie le résultat au clip. Aucune vidéo base64 brute n'est stockée en base ni recopiée dans les erreurs de validation.

`store=false` désactive la conservation des interactions pour leur réutilisation par cette API ; les conditions de traitement/rétention du fournisseur restent celles de votre compte Google.

Les observations restent distinctes de la validation éditoriale. `indice_indicatif` reste `non_evalue` et `requires_human_review` vaut toujours `true`. Les vues publiques/SMS/synchronisation ne sélectionnent aucune analyse vidéo.

## Lancement

Les dépendances Python existantes suffisent. Le mobile déclare désormais `expo-file-system` avec la version compatible SDK 58, installée par `expo install`. Le plugin `expo-camera` déclare les messages caméra/microphone pour les builds natifs. La capture nécessite un téléphone Android/iOS ; le bouton vidéo est désactivé sur le web. Aucune validation caméra physique n'a été effectuée dans cet environnement.

Depuis la racine, pour le lanceur de développement accessible sur le réseau local :

```sh
.venv/bin/python Backend/scripts/run_local.py --port 18000 --host 0.0.0.0
```

Le lanceur charge `Backend/.env`, utilise `DATABASE_URL` si défini et applique Alembic avant Uvicorn. Sans `DATABASE_URL`, il utilise la base SQLite locale. Les comptes ne sont pas inventés : en créer un au besoin avec `run_local.py --create-account`, rôle `JOURNALISTE`, avant le lancement du serveur.

Dans l'environnement préparé pendant cette intégration, PostgreSQL est lancé sur `127.0.0.1:55434`, la base est migrée jusqu'à `0005_video_vision` et le backend utilise ce PostgreSQL via son `.env` privé. Un secret de session stable a aussi été généré dans ce fichier ignoré. La base était neuve et ne contenait aucun compte : créer son propre compte avec la commande ci-dessous, en choisissant le rôle `JOURNALISTE` et un mot de passe personnel demandé au terminal. Aucun compte ni mot de passe par défaut n'a été ajouté.

```sh
.venv/bin/python Backend/scripts/run_local.py --create-account
```

Pour un backend PostgreSQL déjà configuré, depuis `Backend/` :

```sh
../.venv/bin/python -m alembic upgrade head
../.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 18000
```

Sur le téléphone, `localhost` désigne le téléphone. Le client sait remplacer un backend localhost par l'adresse privée de Metro en développement, en conservant son port. Pour choisir explicitement l'adresse, créer `Frontend/Mobile/.env` avec **uniquement l'URL publique du backend** :

```dotenv
EXPO_PUBLIC_API_URL=http://ADRESSE_LAN_DU_PC:18000/api/v1
```

Le téléphone et le PC doivent être sur le même réseau et le port accessible. Ne jamais utiliser `EXPO_PUBLIC_GEMINI_API_KEY`. L'exemple `.env.example` mobile ne contient qu'une URL. Pour un déploiement distant, utiliser HTTPS et configurer l'origine web autorisée si nécessaire.

Depuis `Frontend/Mobile/` :

```sh
nvm use
npm install
npm start -- --clear
```

Variables serveur : `GEMINI_API_KEY`, **`GEMINI_VISION_MODEL=gemini-3.5-flash-lite`**, `GEMINI_MODEL=gemini-3.8-flash` pour les fonctions existantes, `GEMINI_TIMEOUT_SECONDS=45` (configurable), plus les paramètres habituels de base/session. Redémarrer le backend après modification. La configuration Compose actuelle ne lance que PostgreSQL (`docker compose up -d postgres`, port hôte 55434) ; le backend Python est démarré séparément. Renseigner son `DATABASE_URL` ou ses variables `DATABASE_*` pour utiliser ce PostgreSQL, notamment `DATABASE_PORT=55434`, au lieu de la base SQLite locale.

## Vérifications

Depuis `Backend/` :

```sh
../.venv/bin/python -B -m unittest discover -s app/tests -v
../.venv/bin/python -B scripts/verify_postgresql.py
# Test distant explicite : exige ffmpeg pour générer un clip synthétique de 2 s.
# Cette commande effectue un appel réel et peut consommer le quota Gemini.
../.venv/bin/python -B scripts/check_gemini_vision.py
# Parcours réel complet sur une base neuve temporaire, sans toucher la base applicative :
../.venv/bin/python -B scripts/check_gemini_vision.py --http
```

Depuis `Frontend/Mobile/`, avec Node 24 :

```sh
npm run lint
node node_modules/typescript/bin/tsc --noEmit
node tests/vision-client.test.cjs
EXPO_OFFLINE=1 npx expo export --platform android --output-dir /tmp/fa-gemini-vision-android
```

Les tests backend spécifiques vérifient les permissions, la propriété, l'absence de fuite publique/base64/secrets, les erreurs/délais, le refus des résultats partiels et des champs de publication, la persistance et l'idempotence. Les tests client vérifient l'adresse LAN, le token de session, l'annulation de requête, les métadonnées et le rejet de fichiers trop volumineux. Leurs fournisseurs et fichiers sont explicitement des fixtures ; ils ne constituent pas une recette Gemini distante.

Les conflits Git présents dans la connexion, le profil et la discussion ont été résolus en conservant les appels backend et les corrections de rendu Text.

Résultats de recette : 95 tests PostgreSQL réussis sans test ignoré ; 95 tests SQLite exécutés, dont 88 réussis et 7 spécifiques PostgreSQL ignorés ; 5 tests client réussis ; TypeScript valide ; lint sans erreur (2 avertissements de style préexistants dans `mockData.ts`) ; export Android réussi, 1 797 modules. Les tests ciblés sont aussi relancés après séparation des modèles vidéo/texte. Le test de persistance de démonstration a été ajusté aux deux comptes déjà créés par son seed (journaliste et contributeur), sans retirer ce comportement existant. La génération vidéo distante et le parcours backend HTTP réel ont réussi ; **l'usage de la caméra sur téléphone physique n'est pas encore déclaré validé**.

## Sources techniques inspectées

- [Expo Camera, SDK 58](https://docs.expo.dev/versions/v58.0.0/sdk/camera/).
- [Expo FileSystem, SDK 58](https://docs.expo.dev/versions/v58.0.0/sdk/filesystem/).
- [Gemini : compréhension vidéo et formats pris en charge](https://ai.google.dev/gemini-api/docs/video-understanding).
- [Gemini : sorties structurées avec Interactions](https://ai.google.dev/gemini-api/docs/migrate-to-interactions).
- [Gemini : contrôle du raisonnement et latence](https://ai.google.dev/gemini-api/docs/thinking).
