# Intégration technique — livraison du 2 novembre 2026

Ce document complète [l'audit préalable](AUDIT_INTEGRATION.md). Le parcours documentaire et éditorial local est implémenté ; la connexion au moteur Maharavo externe et la livraison SMS opérateur restent indisponibles. Aucun succès fournisseur distant n'est annoncé.

## Architecture et décisions

Architecture conservée : `Backend/app` FastAPI → dépendances/RBAC → services → repositories/SQLAlchemy → PostgreSQL. Les migrations restent dans `Backend/alembic`. Les routes `/api` et `/api/v1` partagent la même implémentation. Le client existant reste en Java ME, avec formulaires MIDP et transport HTTP réel ; aucune application web ou framework supplémentaire n'est ajouté.

Le stockage existant des dossiers, affirmations, preuves, associations, recherches, brouillons et publications est réutilisé. Seule la table privée `draft_revisions` est ajoutée, par `0004_draft_history`. Ses clés étrangères composites imposent le même périmètre de rédaction/dataset pour le brouillon et son acteur. Les snapshots sont immuables en ORM et SQL, y compris face à une suppression ou à TRUNCATE PostgreSQL. La migration ne réécrit ni ne supprime les données historiques ; les versions antérieures à l'installation ne peuvent pas être reconstituées.

Les versions de contenu public utilisent une empreinte SHA-256 des champs publiés. Il n'est pas nécessaire de dupliquer les publications dans une seconde implémentation ou de créer une table de sessions pour les lecteurs anonymes : la date de synchronisation et l'instantané complet sont enregistrés dans le cache RMS public du téléphone. Les révisions éditoriales existantes et le journal `corrections_audit` sont conservés ; les snapshots de brouillons complètent cet historique privé.

## Résultats par phase

| Phase | Travail et vérification |
|---|---|
| 1 Audit | Inventaire, analyse du backend, modèles/migrations/RBAC, moteur/connecteur Maharavo et Java ME ; plan dans `AUDIT_INTEGRATION.md`, produit avant modification. |
| 2 Fondations | Migration additive d'historique ; tests de migration neuve, adoption et comparaison ORM. |
| 3 Sécurité | Permissions explicites `cases.edit`, `claims.add`, politiques de toutes les routes, limites locales par IP et absence de cache HTTP privé. Les contrôles humains et l'isolation restent actifs. |
| 4 Investigations | Modification avec conflit de version, archivage, pagination/filtres, affirmations, preuves documentées, liens entre preuves et affirmations, catalogue de sources disponibles. Tests positifs et refus inter-dossiers/inter-rédactions. |
| 5 IA | Le connecteur Maharavo préexistant est préservé ; aucun adaptateur distant inventé. Nouvelle recherche lexicale locale identifiée et persistée, sans jugement de vérité ni appel web. Connexion externe encore indisponible. |
| 6 Traitements | File durable réutilisant `research_jobs`, worker par lots, prise de tâche atomique, verrou `SKIP LOCKED` PostgreSQL, échecs, annulation et récupération explicite des tâches interrompues. Pas de broker ajouté. |
| 7 Publication | Création humaine du brouillon lié au dossier/signal/affirmation ; nouvelle révision accessible en POST pour MIDP ; historique initial/modifications/relecture/validation/publication ; validation exacte de version et contenu conservée. |
| 8 Services | Réponse SMS sans résultat conforme ; recherche exclusivement publique. Synchronisation complète avec empreintes et ETag, remplacement atomique du cache et suppression au retrait. Aucun SMS livré. |
| 9 Frontend | Suppression de l'accès par `1234` et des réponses/lists fictives ; HTTP, sessions mémoire/refresh, formulaires réels, pagination, erreurs/chargement, permissions, confirmation éditoriale et cache exclusivement public. Compilation et test Java ME headless sur vrai serveur temporaire. |
| 10 Qualité | Tests SQLite/PostgreSQL, tests réseau/RMS Java ME, vérification des dépendances et des différences ; détails des résultats ci-dessous. Les fournisseurs distants restent hors recette. |

## API ajoutée ou complétée

Documentation OpenAPI : `http://127.0.0.1:8000/docs`, schéma : `/openapi.json`. Préfixe des routes suivantes : `/api/v1`, avec alias `/api`.

| Méthode et route | Fonction et accès |
|---|---|
| POST `/cases` | Créer un dossier — journaliste. |
| GET `/cases` | Liste avec `limit` (1–200, défaut 50), `offset`, `q`, `status` — journaliste/éditeur. |
| GET/PATCH `/cases/{id}` | Lire / modifier titre et description ; PATCH exige `expected_updated_at` reçu à la lecture. Les conflits renvoient 409. |
| POST `/cases/{id}/archive` | Archiver ; les nouvelles écritures documentaires sur ce dossier sont refusées. |
| GET/POST `/cases/{id}/claims` | Lire / créer les affirmations ; aucun verdict ne peut être fourni à la création. |
| GET/POST `/cases/{id}/evidence` | Lire / ajouter une preuve privée ; référence originale, source et date de consultation sont conservées. |
| GET/POST `/cases/{id}/claims/{claim_id}/evidence` | Consulter / proposer un lien supports/refutes/context ; preuve et affirmation doivent appartenir au même dossier. Doublon : 409. |
| GET `/cases/{id}/sources` | Catalogue de sources de veille de la rédaction disponibles pour référencer une pièce. Il ne s'agit pas d'une liste de confirmations indépendantes. |
| POST `/signals/ingest` | Désormais accepte `case_id` ; refuse un dossier absent ou archivé. |
| GET/POST `/cases/{id}/drafts` | Liste / création humaine d'un brouillon ; le signal et l'affirmation éventuelle doivent appartenir au dossier. Un brouillon par signal, convention existante conservée. |
| GET/POST `/cases/{id}/research` | Historique / recherche locale dans les pièces saisies. Fournisseur `local-document-search-v1` ; pas une recherche approfondie web ou Maharavo. |
| POST `/cases/{id}/research/tasks` | Enregistrer une recherche locale asynchrone — 202, statut `queued`, identifiant durable. |
| GET `/research-jobs/{id}` | Consulter l'état/résultat/erreur d'une recherche autorisée de la rédaction. |
| POST `/research-jobs/{id}/cancel` | Annuler une tâche encore en attente ; demandeur ou worker autorisé seulement. |
| GET `/drafts/{id}/history` | Historique privé paginé et acteur identifié — journaliste/éditeur. |
| POST `/drafts/{id}/revisions` | Même opération métier que PATCH `/drafts/{id}`, accessible aux clients MIDP sans PATCH ; `expected_version` obligatoire, 201. |
| GET `/drafts/{id}/version` | Inclut désormais le contenu éditorial approuvé, privé, pour retrouver exactement la version validée dans l'interface éditeur. |
| GET `/public/articles` | Publications approuvées actives ; pagination bornée ajoutée. |
| GET `/public/sync` | Instantané public complet avec versions, date et ETag, ou 304 si identique. |
| POST `/sms/citizen` | Consultation HTTP du service SMS ; réponse exacte si aucun résultat, aucun envoi opérateur. |

Les listes de ressources par dossier, l'historique et le catalogue de sources acceptent `limit` et `offset`. Les routes privées exigent `Authorization: Bearer <access_token>`. Les nouveaux contrats de création refusent les champs supplémentaires tels que verdict, rôle, périmètre ou validation. Les routes éditoriales existantes sont conservées : `review`, `validate`, `publish`, `correct`, `withdraw` sous `/workflow`.

## Recherches et worker

La recherche locale parcourt au maximum 1 000 pièces du dossier et conserve les vingt correspondances les mieux classées. Au-delà de 1 000 pièces, elle enregistre un état partiel et une limite explicite. Une citation conserve l'identifiant de preuve, la source, l'URL originale et un extrait exact. Aucun score lexical n'est transformé en verdict.

La file utilise les statuts historiques du modèle, sans seconde table de tâches :

| Valeur SQL/API | Sens |
|---|---|
| `queued` | pending |
| `en_cours` | running |
| `terminee` | completed |
| `partielle` | partially_completed |
| `echouee` | failed |
| `cancelled` | cancelled |

Le worker est un lot explicite, pas un ordonnanceur démarré silencieusement. La soumission HTTP ne traite pas la tâche. Un opérateur doit lancer le worker ou le planifier. Créer un compte de service depuis un administrateur via POST `/admin/service-accounts`, avec les permissions **`tasks.run` et `research.run`** ; conserver son identifiant numérique. Le traitement revérifie l'activation, le rôle, le type de compte et les scopes côté serveur. Le compte est limité à sa rédaction et son dataset.

Depuis `Backend/`, avec l'environnement virtuel activé :

```sh
python -m app.workers.research_queue --service-user-id 4 --limit 20
python -m app.workers.research_queue --service-user-id 4 --limit 20 --recover-stale
```

Remplacer `4` par l'identifiant réel. `--recover-stale` marque en échec les recherches locales en cours depuis plus de quinze minutes. Il ne relance pas arbitrairement les opérations et n'invente pas de résultat. Chaque traitement dispose de sa transaction ; la prise est persistée avant calcul. Une panne du processus reste identifiable puis récupérable. L'ingestion supervisée historique reste disponible avec `python -m app.workers.ingestion`.

## Synchronisation et confidentialité

`/public/sync` lit exclusivement la vue SQL publique au moyen de la dépendance publique. Aucun brouillon, numéro de téléphone, preuve, source privée, analyse ou identifiant de validateur n'y est sélectionné. La réponse contient `complete=true`, `strategy=replace`, `snapshot_version`, `synchronized_at`, et `items`. Chaque article expose `content_version`, calculé sur les champs publiés.

Le client remplace **l'ensemble** de son cache seulement après réponse complète, validation du format et écriture RMS réussie. Les doublons disparaissent et les publications absentes du nouvel instantané sont supprimées. Une erreur réseau, de taille ou de stockage conserve l'ancien cache et affiche une erreur. Le cache est rattaché au serveur configuré. Aucune donnée de rédaction ni jeton n'est écrit en RMS.

Le serveur refuse explicitement une synchronisation dépassant 2 000 publications au lieu d'envoyer un instantané tronqué. Le mobile limite les réponses à 256 Kio. Pour un déploiement plus important, prévoir des instantanés paginés immuables. Les listes ordinaires restent paginées.

Une correction change l'empreinte ; un retrait fait disparaître l'article à la prochaine synchronisation. **Hors réseau, un appareil peut encore posséder une ancienne publication retirée depuis sa dernière synchronisation.** L'interface affiche toujours la date et le caractère potentiellement périmé du cache. L'ETag permet également à un autre client d'envoyer `If-None-Match` ; le client Java actuel retélécharge le petit instantané complet.

Le service SMS ne génère jamais de faits absents des publications. Le texte sans résultat est exactement :

> Aucune vérification publiée trouvée pour cette demande.

Le numéro et la demande restent dans l'historique privé existant. Le service HTTP calcule une réponse ; aucun webhook ni fournisseur SMS réel n'est connecté. La passerelle préexistante est un simulateur explicite.

## Installation et lancement

Depuis la racine du dépôt, pour un environnement neuf :

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r Backend/requirements-dev.txt
```

Pour démarrer immédiatement en local sans installer un serveur PostgreSQL :

```sh
.venv/bin/python Backend/scripts/run_local.py --create-account
.venv/bin/python Backend/scripts/run_local.py --create-account
.venv/bin/python Backend/scripts/run_local.py --create-account
.venv/bin/python Backend/scripts/run_local.py
```

Créer respectivement un administrateur, un journaliste et un éditeur avec vos propres emails et mots de passe, demandés au terminal. Aucune identité ni mot de passe universel n'est ajouté. Le lanceur applique les migrations, utilise SQLite dans `Backend/.local-data/` si `DATABASE_URL` n'est pas défini, et garde un secret JWT aléatoire persistant en fichier local protégé. Ce dossier est exclu de Git. `Backend/.env` est chargé s'il existe ; les variables déjà définies ont priorité. Le lanceur local n'est pas le déploiement de production.

Pour PostgreSQL, la procédure existante reste valable :

```sh
cp Backend/.env.example Backend/.env
# Renseigner les variables de développement, puis :
cd Backend
../.venv/bin/python -m alembic upgrade head
../.venv/bin/python -m app.core.manage_users --email administrateur@example.org --role ADMINISTRATEUR
../.venv/bin/python -m app.core.manage_users --email journaliste@example.org --role JOURNALISTE
../.venv/bin/python -m app.core.manage_users --email editeur@example.org --role EDITEUR
../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Pour une base historique, sauvegarder avant l'adoption explicite `alembic -x adopt_legacy=true upgrade head` ; consulter `Backend/PERSISTENCE.md`. Aucune base applicative existante n'a été migrée pendant cette intervention.

Avec Docker, depuis la racine : `docker compose up --build`. Compose charge les variables du shell ou du `.env` de la racine, pas `Backend/.env`. La construction et le démarrage complets Docker ne constituent pas la recette utilisée ici ; la validation porte sur les processus Python/PostgreSQL/Java locaux.

Pour le mobile, utiliser une installation **existante** de MicroEmulator 2.0.4 :

```sh
MICROEMU_HOME=/chemin/vers/microemulator-2.0.4 bash Touche/lancement.sh --build
MICROEMU_HOME=/chemin/vers/microemulator-2.0.4 bash Touche/lancement.sh
```

Le script compile et produit `Touche/front/build/FAAIMARINANA.jar` et `.jad`. Le dossier `build` est ignoré par Git. Les fichiers `deploy` préexistants restent les anciennes distributions de démonstration ; utiliser la distribution nouvellement construite. Le build Java 8 vise MicroEmulator, **pas une certification/prévérification sur téléphone CLDC physique**. Les bibliothèques et l'émulateur ne sont pas téléchargés silencieusement.

Sur l'écran de connexion, configurer `http://127.0.0.1:8000` dans l'émulateur local, puis les vrais identifiants. Un serveur non local exige HTTPS. `10.0.2.2` est autorisé pour un émulateur utilisant cette passerelle. Les tokens et mots de passe restent en mémoire ; aucune clé API n'est requise sur le téléphone. Le client renouvelle les tokens d'accès via refresh token et révoque la session lors de la déconnexion réseau.

## Parcours de démonstration manuel

1. Administrateur : créer une source de veille avec sa vraie URL. Journaliste : se connecter et créer un dossier.
2. Ajouter une affirmation puis une preuve avec son extrait original, sa source et son URL. Relier la preuve à l'affirmation avec une justification de contexte.
3. Ajouter un signal documenté au dossier ; noter son identifiant présenté par le mobile.
4. Rechercher dans les pièces locales et consulter les citations enregistrées. Cette étape ne prétend pas être une analyse Maharavo distante.
5. Préparer un brouillon humain avec les identifiants du signal et de l'affirmation. Le modifier si nécessaire ; la nouvelle révision invalide une éventuelle validation précédente.
6. Éditeur : se connecter, ouvrir le même dossier et consulter ses affirmations, preuves et brouillons. Examiner puis valider le contenu final avec son résumé SMS et son verdict humain.
7. Confirmer la publication de cette même version. Toute différence avec le contenu validé est refusée par le serveur.
8. Lecteur public : synchroniser les publications et consulter le cache. Le service de consultation SMS doit retrouver uniquement le résumé approuvé ; sans résultat, il retourne le texte imposé.

## Variables d'environnement

Le catalogue exhaustif reste `Backend/.env.example`.

- Stockage : `DATABASE_URL` ou `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD` ; `PUBLIC_DATABASE_URL` distinct obligatoire en production.
- Périmètres : `DEFAULT_NEWSROOM_ID`, `DEFAULT_DATASET`, `PUBLIC_NEWSROOM_ID`, `PUBLIC_DATASET`.
- Sécurité : `ENVIRONMENT`, `JWT_SECRET`, `JWT_ISSUER`, `JWT_AUDIENCE`, `JWT_EXPIRE_MINUTES`, `REFRESH_EXPIRE_DAYS`, `INVITATION_EXPIRE_HOURS`, `FRONTEND_ORIGINS`, `AUTO_CREATE_TABLES=false`, `ALLOW_PUBLIC_REGISTRATION=false`.
- Nouveaux quotas : `AUTH_REQUESTS_PER_MINUTE=60`, `PUBLIC_REQUESTS_PER_MINUTE=60`. Compteurs bornés par processus et IP de connexion, partagés entre alias historiques/v1. Ne pas déduire l'IP de n'importe quel `X-Forwarded-For`. Un reverse proxy doit fournir les quotas globaux si plusieurs workers sont déployés.
- Services facultatifs : `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_TIMEOUT_SECONDS`, `SMS_BACKEND=simulation` ; paramètres `MAHARAVO_*` décrits dans `Backend/MAHARAVO_INTEGRATION.md`, toujours fermés sans adaptateur documenté.
- Outils de test : `MICROEMU_HOME` ; `FANILO_TEST_DATABASE_URL` uniquement pour une base PostgreSQL **jetable**. Les scripts `verify_postgresql.py` et `verify_mobile.py` créent leurs propres environnements temporaires.

## Tests et résultats

Commandes depuis `Backend/`, avec Python de l'environnement virtuel :

```sh
../.venv/bin/python -B -m unittest discover -s app/tests -v
../.venv/bin/python -B scripts/verify_postgresql.py
MICROEMU_HOME=/chemin/vers/microemulator-2.0.4 ../.venv/bin/python -B scripts/verify_mobile.py
../.venv/bin/python -m pip check
```

`verify_postgresql.py` exige les binaires PostgreSQL `initdb` et `pg_ctl` : cluster neuf dans un dossier privé 0700, socket Unix uniquement, arrêt et suppression à la fin. Il ne se connecte à aucun cluster existant. Le test mobile utilise Alembic, une base SQLite temporaire, Uvicorn sur une adresse loopback éphémère et le vrai `Connector` HTTP/RMS de MicroEmulator, avec comptes explicitement réservés aux tests.

Les résultats finaux sont consignés dans la section de recette du [rapport final](RAPPORT_FINAL_INTEGRATION.md). La suite vérifie authentification, tokens expirés/révocation, permissions des six rôles, refus des décisions éditoriales IA, transactions, isolations, preuves, historique, migrations, erreurs/timeouts/résultats partiels des contrats du connecteur, SMS public, synchronisation et file de tâches. Les tests du connecteur IA utilisent des transports unitaires contrôlés ; ils ne constituent pas une connexion Maharavo réelle.

## Limites restantes et suites recommandées

- Maharavo externe : pas de serveur/SDK/API réel dans le dépôt, donc route de recherche distante toujours 503 ; recherche web approfondie et analyses distantes non certifiées. Le protocole et un environnement autorisé sont nécessaires pour terminer cette phase.
- SMS : pas d'opérateur, webhook authentifié, signature fournisseur, accusé de livraison ni envoi réel. La consultation HTTP est fonctionnelle et séparée.
- Multilingue : UTF-8, contenus originaux et textes français/malagasy/anglais supportés techniquement ; workflow explicite de traduction et validation linguistique humaine pas encore implémenté. Ne pas présenter une traduction automatique comme approuvée.
- Éditorial : le modèle historique des états est conservé ; l'ensemble des états indicatifs de la mission n'est pas ajouté. Les dossiers sont partagés au sein de la rédaction autorisée, sans ACL nominative par dossier. Le compte administrateur n'hérite pas du droit de publier.
- UI : parcours documentaire central connecté, mais interface complète de gestion des invitations/comptes/paramètres, notifications de soumission et tableau de bord statistique restent à compléter. Les IDs documentaires sont visibles pour relier les pièces ; des sélecteurs amélioreront l'ergonomie.
- Extractions de fichiers et médias : pas de téléchargement/upload documentaire ni analyse forensique automatisée ajouté. L'extrait et la référence de la pièce sont saisis explicitement.
- Traitements : file durable pour recherches locales, pas de collecte web planifiée ni ordonnanceur distribué, SMS asynchrone ou exécution Maharavo autonome. Les quotas sont locaux ; les WebSockets existants restent limités au processus.
- Production : déploiement Docker complet, terminaison TLS, sauvegardes/restauration, supervision, politique de rétention SMS, test sur téléphone physique et montée en charge restent des recettes séparées.

Ces limites sont exposées pour éviter de déclarer les vingt exigences globales entièrement terminées alors que certaines dépendent d'interfaces externes absentes.
