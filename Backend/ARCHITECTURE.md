# Backend FA AI MARINANA — architecture modulaire

Mise à jour du 2 novembre 2026 : les paragraphes de limites et résultats historiques
ci-dessous décrivent la restructuration initiale. Les ajouts ultérieurs (API dossiers,
preuves/affirmations, historique immuable, file durable locale, synchronisation et
mobile HTTP/RMS) sont détaillés dans le [guide d'intégration](../docs/INTEGRATION_TECHNIQUE.md)
et son [rapport de recette](../docs/RAPPORT_FINAL_INTEGRATION.md).

Les règles actuelles d’inscription, de session et de publication sont décrites dans [AUTHENTICATION.md](AUTHENTICATION.md).

Le schéma actuel, les treize entités principales et la migration de confidentialité sont détaillés dans [PERSISTENCE.md](PERSISTENCE.md).

La restructuration conserve les fonctionnalités existantes et leur stockage. Elle sépare les adaptateurs HTTP, les règles métier, les requêtes SQL et les fournisseurs externes. Les ajouts Maharavo présents dans la fusion concurrente sont intégrés : recherche, enregistrement d'analyse média guidée et évaluation de confiance.

## Organisation et dépendances

```text
app/
  main.py
  api/v1/router.py
  api/v1/endpoints/
  core/{config,constants,security,permissions,errors,manage_users}.py
  database/{base,connection}.py
  models/
  schemas/
  repositories/
  services/
  workers/{ingestion,research,media,notifications}.py
  integrations/{ai,maharavo,sms,notifications}/
  middleware/errors.py
  utils/text.py
  tests/
alembic/
  env.py
  script.py.mako
  versions/0001_modular_baseline.py
```

Flux principal : HTTP → dépendances d'authentification → service métier → repository → SQLAlchemy/PostgreSQL. Les services contrôlent les commits ; les repositories ne valident jamais une transaction. Les adaptateurs IA/SMS sont distincts du stockage et des règles éditoriales. Le fournisseur de recherche Maharavo et la passerelle SMS sont remplaçables avec `app.dependency_overrides`.

Le moteur SQLAlchemy reste synchrone. FastAPI exécute les endpoints synchrones dans ses threads ; les accès synchrones de la route d'alerte asynchrone passent explicitement dans un thread. Chaque requête ou job possède sa session, fermée même en cas d'erreur. Le pool est libéré à l'arrêt de l'application.

## Compatibilité et changements justifiés

- Les routes historiques `/api/...` existent toujours, avec les mêmes champs de réponse et codes de succès. Elles partagent leurs fonctions avec `/api/v1/...` ; seule la version v1 apparaît dans OpenAPI.
- Les noms de modèles, champs, tables et valeurs éditoriales sont conservés. `En_Cours` reste la valeur historique indiquant un brouillon publié.
- Les anciens imports `app.models`, `app.schemas`, `app.services`, `app.database`, `app.workers`, `app.dependencies`, `app.controllers.*`, `app.gemini_service`, `app.maharavo_service` et `app.notifications` restent disponibles. Les fichiers plats remplacés par des packages ne contiennent pas une seconde implémentation.
- Une seconde analyse retourne un conflit 409. Publication et indexation partagent une transaction ; un verrou PostgreSQL empêche deux publications concurrentes par ce service.
- Une ressemblance lexicale produit une piste non confirmée (`concorde=false`, `officielle=false`). Ce changement corrige une fausse affirmation de vérification.
- Les mots de passe dépassant 72 octets UTF-8 sont rejetés avec 422. L'email est normalisé avant la recherche de doublon. Les emails restent des chaînes pour préserver les clients existants.
- Les alertes WebSocket exigent désormais un JWT : correction nécessaire de l'accès public aux alertes privées. Les clients utilisent `Authorization: Bearer <jeton>` ou les sous-protocoles `['bearer', jeton]` ; le serveur sélectionne `bearer`. Aucun jeton dans l'URL. Les diffusions donnent `sent_count`, sans numéro de téléphone. La réponse HTTP autorisée conserve son champ historique `sent`.
- L’inscription exige une invitation nominative à usage unique. La CLI opérateur permet de créer le premier administrateur.

## Configuration

Copier `Backend/.env.example` vers `Backend/.env` pour une exécution Python locale. Le chargeur lit ce fichier une seule fois ; les variables du processus ont priorité. La configuration Pydantic est validée au démarrage. `DATABASE_URL` prime sur les variables `DATABASE_*`.

Docker Compose ne gère ici que PostgreSQL, publié sur `localhost:55434`. Le backend
local utilise `Backend/.env`, qui est exclu de l'image par `.dockerignore`.

Développement : renseigner un secret JWT stable pour conserver les sessions entre redémarrages et partager les jetons entre processus. Sans secret, un secret aléatoire temporaire est généré et un avertissement est émis. Aucun secret fixe connu n'est utilisé.

Production : `ENVIRONMENT=production`, `JWT_SECRET` aléatoire d'au moins 32 octets, `ALLOW_PUBLIC_REGISTRATION=false`, `AUTO_CREATE_TABLES=false`. La configuration refuse un secret insuffisant, les inscriptions publiques ou la création implicite de tables. Les identifiants PostgreSQL, origines CORS, HTTPS et sauvegardes doivent être configurés dans l'environnement de déploiement.

## Installation et migrations

Depuis `Backend/`, avec l'environnement Python activé :

```sh
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 18000
```

Pour démarrer PostgreSQL avec Docker, depuis la racine :

```sh
docker compose up -d postgres
```

Le backend local doit ensuite exécuter Alembic avant Uvicorn. PostgreSQL est publié
sur `localhost:55434`.

### Base historique

Sauvegarder la base et relire le schéma avant son adoption. La migration initiale refuse par défaut les tables préexistantes. L'adoption explicite vérifie colonnes, familles de types, tailles minimales, nullabilité, clés primaires, clés étrangères et unicités attendues avant de créer les tables manquantes. Une incompatibilité interrompt l'opération ; aucune donnée n'est supprimée automatiquement.

```sh
alembic -x adopt_legacy=true upgrade head
```

Pour le volume existant de Compose :

```sh
docker compose run --rm backend alembic -x adopt_legacy=true upgrade head
docker compose up --build
```

Le schéma de référence initial est figé dans la révision Alembic, sans import des futurs modèles. Les contraintes, index, valeurs par défaut, JSONB et vue supplémentaires des bases SQL historiques sont conservés. Le fichier SQL historique est conservé sans modification par cette restructuration. Les nouvelles évolutions doivent être réalisées par migrations ; relire les différences générées, notamment les objets historiques supplémentaires.

Cette première révision stabilise le schéma ORM existant. Elle n'ajoute pas encore une clé étrangère au validateur d'article ni une contrainte unique sur `draft_id` : une migration ultérieure devra examiner les données historiques avant de les imposer. Le verrou de publication protège le chemin métier courant ; il ne remplace pas ces futurs invariants SQL.

Le retour arrière initial supprime les tables : il est volontairement réservé aux bases jetables avec `alembic -x allow_drop_baseline=true downgrade base`. Ne pas l'utiliser pour annuler une adoption contenant des données.

Créer un compte approuvé, inscription publique désactivée :

```sh
python -m app.core.manage_users --email redacteur@example.org --role EDITEUR
```

Le mot de passe est demandé au terminal, jamais dans la ligne de commande.

## Workers et intégrations

Les quatre modules workers sont des fonctions appelables avec leurs propres sessions : ingestion des urgences, recherche, enregistrement d'analyse média guidée, notifications. `python -m app.workers.ingestion` exécute un lot ; `/api/workflow/process-pending` conserve le déclenchement supervisé historique.

Aucun ordonnanceur ni processus autonome n'est démarré implicitement. Les requêtes de recherche restent synchrones. Redis n'est pas ajouté : il deviendra utile avec une file durable et une diffusion WebSocket entre processus. L'étape suivante pourra introduire un broker, des identifiants de job, retries, idempotence et une outbox transactionnelle. Les lots actuels ne garantissent pas une exécution concurrente sans conflit.

Gemini reste facultatif. Les réponses structurées des brouillons sont validées avec Pydantic ; une indisponibilité ou une réponse invalide déclenche le moteur local. La clé, le modèle et les délais sont configurables. La compatibilité réelle du modèle et du service externe nécessite une recette avec une clé valide.

Le connecteur indépendant Maharavo est désactivé sans adaptateur documenté. La recherche `/maharavo/research` renvoie 503 et n’utilise plus Gemini sous ce nom. Le socle HTTP asynchrone et les contrats proposés sont détaillés dans [MAHARAVO_INTEGRATION.md](MAHARAVO_INTEGRATION.md). Les analyses média existantes enregistrent des observations fournies par un opérateur.

La passerelle SMS reste un simulateur explicite. Elle n'envoie aucun SMS et ne journalise ni numéro ni contenu. `/sms/citizen` calcule une réponse JSON ; aucun webhook opérateur, accusé de livraison ou envoi réel n'est annoncé.

## Vérification

Depuis `Backend/` :

```sh
python -B -m unittest discover -s app/tests -v
```

Les tests utilisent SQLite en mémoire, sans appel IA externe. Le manifeste de compatibilité conserve les opérations HTTP et champs de réponse relevés avant la restructuration. Les tests couvrent authentification, validations, routes historiques/v1, publication atomique, conflits, SMS, recherche, sessions privées, WebSocket authentifié, injection fournisseur et capacités Maharavo. Les tests Alembic vérifient création, adoption, refus d'un schéma incompatible et génération SQL hors connexion.

Pour tester PostgreSQL, utiliser uniquement une base jetable, puis définir `FANILO_TEST_DATABASE_URL` et relancer la même commande. Les tests HTTP suppriment et recréent les tables dans cette base. Les tests de migrations PostgreSQL utilisent des schémas isolés, et le test de publication concurrente utilise de véritables verrous PostgreSQL.

## Résultats de la première restructuration (historique)

- 17 tests réussis sur un PostgreSQL 17 temporaire, incluant les tests HTTP, WebSocket, concurrence et migrations ; aucun appel fournisseur externe.
- Sur SQLite : 14 tests réussis, 3 tests PostgreSQL ignorés comme prévu.
- Vérification syntaxique Python, `pip check`, `git diff --check` et `docker compose config --quiet` réussis.
- PostgreSQL temporaire arrêté après vérification ; aucune base applicative existante utilisée.
- Construction complète de l'image Docker, Gemini réel, livraison SMS et frontend mobile connecté non vérifiés.

## Limites et prochaines étapes

Cette livraison constitue une base modulaire et testée, sans annoncer la fin de tous les travaux de l'audit. Restent à traiter : limites de débit, restrictions fines par dossier, historique intégral des révisions de brouillons, recherche à grande échelle, contexte conversationnel, collecte planifiée, file durable, diffusion WebSocket partagée, SMS réel et intégration mobile réseau. Les sessions et permissions WebSocket sont désormais revérifiées avant chaque diffusion.

Le frontend Java ME reste une démonstration avec données locales. Les routes historiques sont conservées pour son intégration ultérieure ; cela ne constitue pas une preuve de connexion mobile de bout en bout.

## Responsabilité de chaque fichier Python

Les sources complètes se trouvent aux chemins ci-dessous. Les façades ne dupliquent aucune règle métier.

| Fichier | Responsabilité |
|---|---|
| [app/__init__.py](app/__init__.py) | Déclaration du package, sans tâche ni service démarré à l’import. |
| [app/api/__init__.py](app/api/__init__.py) | Déclaration du package, sans tâche ni service démarré à l’import. |
| [app/api/v1/__init__.py](app/api/v1/__init__.py) | Déclaration du package, sans tâche ni service démarré à l’import. |
| [app/api/v1/endpoints/__init__.py](app/api/v1/endpoints/__init__.py) | Déclaration du package, sans tâche ni service démarré à l’import. |
| [app/api/v1/endpoints/alert.py](app/api/v1/endpoints/alert.py) | Adaptateur HTTP/WebSocket : authentification et connexion des alertes WebSocket. |
| [app/api/v1/endpoints/auth.py](app/api/v1/endpoints/auth.py) | Adaptateur HTTP/WebSocket : inscription et connexion. |
| [app/api/v1/endpoints/copilot.py](app/api/v1/endpoints/copilot.py) | Adaptateur HTTP/WebSocket : recherche, sessions, indexation et déclenchement des alertes. |
| [app/api/v1/endpoints/draft.py](app/api/v1/endpoints/draft.py) | Adaptateur HTTP/WebSocket : lecture des brouillons. |
| [app/api/v1/endpoints/health.py](app/api/v1/endpoints/health.py) | Adaptateur HTTP/WebSocket : sonde de vie HTTP. |
| [app/api/v1/endpoints/maharavo.py](app/api/v1/endpoints/maharavo.py) | Adaptateur HTTP/WebSocket : recherche, analyse guidée et confiance Maharavo. |
| [app/api/v1/endpoints/public.py](app/api/v1/endpoints/public.py) | Adaptateur HTTP/WebSocket : flux public des articles certifiés. |
| [app/api/v1/endpoints/signal.py](app/api/v1/endpoints/signal.py) | Adaptateur HTTP/WebSocket : ingestion et analyse des signaux. |
| [app/api/v1/endpoints/sms.py](app/api/v1/endpoints/sms.py) | Adaptateur HTTP/WebSocket : requête citoyenne du simulateur SMS. |
| [app/api/v1/endpoints/source.py](app/api/v1/endpoints/source.py) | Adaptateur HTTP/WebSocket : création de source. |
| [app/api/v1/endpoints/workflow.py](app/api/v1/endpoints/workflow.py) | Adaptateur HTTP/WebSocket : traitement supervisé, recoupement et publication. |
| [app/api/v1/router.py](app/api/v1/router.py) | Assemblage unique de tous les routeurs. |
| [app/controllers/__init__.py](app/controllers/__init__.py) | Déclaration du package, sans tâche ni service démarré à l’import. |
| [app/controllers/alert_controller.py](app/controllers/alert_controller.py) | Façade de compatibilité vers api/v1/endpoints/alert.py. |
| [app/controllers/auth_controller.py](app/controllers/auth_controller.py) | Façade de compatibilité vers api/v1/endpoints/auth.py. |
| [app/controllers/copilot_controller.py](app/controllers/copilot_controller.py) | Façade de compatibilité vers api/v1/endpoints/copilot.py. |
| [app/controllers/draft_controller.py](app/controllers/draft_controller.py) | Façade de compatibilité vers api/v1/endpoints/draft.py. |
| [app/controllers/health_controller.py](app/controllers/health_controller.py) | Façade de compatibilité vers api/v1/endpoints/health.py. |
| [app/controllers/maharavo_controller.py](app/controllers/maharavo_controller.py) | Façade de compatibilité vers api/v1/endpoints/maharavo.py. |
| [app/controllers/public_controller.py](app/controllers/public_controller.py) | Façade de compatibilité vers api/v1/endpoints/public.py. |
| [app/controllers/signal_controller.py](app/controllers/signal_controller.py) | Façade de compatibilité vers api/v1/endpoints/signal.py. |
| [app/controllers/sms_controller.py](app/controllers/sms_controller.py) | Façade de compatibilité vers api/v1/endpoints/sms.py. |
| [app/controllers/source_controller.py](app/controllers/source_controller.py) | Façade de compatibilité vers api/v1/endpoints/source.py. |
| [app/controllers/workflow_controller.py](app/controllers/workflow_controller.py) | Façade de compatibilité vers api/v1/endpoints/workflow.py. |
| [app/core/__init__.py](app/core/__init__.py) | Déclaration du package, sans tâche ni service démarré à l’import. |
| [app/core/config.py](app/core/config.py) | Configuration Pydantic depuis les variables et le fichier .env, garde-fous de production. |
| [app/core/constants.py](app/core/constants.py) | Mots-clés de veille et réponse neutre SMS partagés. |
| [app/core/errors.py](app/core/errors.py) | Exceptions métier et correspondances de statut. |
| [app/core/manage_users.py](app/core/manage_users.py) | CLI de création de comptes éditoriaux approuvés. |
| [app/core/permissions.py](app/core/permissions.py) | Dépendances FastAPI pour identité et droits de rédaction. |
| [app/core/security.py](app/core/security.py) | Hachage scrypt avec compatibilité bcrypt, JWT liés aux sessions et compte actif. |
| [app/database/__init__.py](app/database/__init__.py) | Réexport de Base, engine, SessionLocal et get_db. |
| [app/database/base.py](app/database/base.py) | Registre DeclarativeBase partagé. |
| [app/database/connection.py](app/database/connection.py) | Moteur SQLAlchemy, pool, sessions et rollback à la sortie en erreur. |
| [app/dependencies.py](app/dependencies.py) | Façade des anciens imports de dépendances. |
| [app/gemini_service.py](app/gemini_service.py) | Façade de l’ancien import Gemini. |
| [app/integrations/__init__.py](app/integrations/__init__.py) | Déclaration du package, sans tâche ni service démarré à l’import. |
| [app/integrations/ai/__init__.py](app/integrations/ai/__init__.py) | Déclaration du package, sans tâche ni service démarré à l’import. |
| [app/integrations/ai/gemini.py](app/integrations/ai/gemini.py) | Transport HTTP Gemini, délais, extraction et validation des réponses. |
| [app/integrations/maharavo/__init__.py](app/integrations/maharavo/__init__.py) | Documentation de la frontière Maharavo, sans API externe inventée. |
| [app/integrations/maharavo/research.py](app/integrations/maharavo/research.py) | Protocole injectable de fournisseur de recherche et adaptateur Gemini. |
| [app/integrations/notifications/__init__.py](app/integrations/notifications/__init__.py) | Déclaration du package, sans tâche ni service démarré à l’import. |
| [app/integrations/notifications/websocket.py](app/integrations/notifications/websocket.py) | Transport de diffusion WebSocket local au processus. |
| [app/integrations/sms/__init__.py](app/integrations/sms/__init__.py) | Déclaration du package, sans tâche ni service démarré à l’import. |
| [app/integrations/sms/gateway.py](app/integrations/sms/gateway.py) | Protocole de passerelle, injection et simulateur sans données personnelles dans les logs. |
| [app/maharavo_service.py](app/maharavo_service.py) | Façade de l’ancien import du service Maharavo. |
| [app/main.py](app/main.py) | Fabrique FastAPI, cycle de vie, CORS et montage des routes historiques/v1. |
| [app/middleware/__init__.py](app/middleware/__init__.py) | Déclaration du package, sans tâche ni service démarré à l’import. |
| [app/middleware/errors.py](app/middleware/errors.py) | Gestionnaires centralisés des erreurs métier, SQL et inattendues. |
| [app/models/__init__.py](app/models/__init__.py) | Registre des modèles de persistance, d’authentification et réexport des noms historiques. |
| [app/models/editorial.py](app/models/editorial.py) | Tables brouillons IA et articles certifiés. |
| [app/models/identity.py](app/models/identity.py) | Tables utilisateurs et contacts de journalistes. |
| [app/models/maharavo.py](app/models/maharavo.py) | Tables recherches, analyses média guidées et évaluations de confiance. |
| [app/models/monitoring.py](app/models/monitoring.py) | Tables sources et signaux bruts. |
| [app/models/research.py](app/models/research.py) | Tables documents, sessions et messages de chat. |
| [app/models/sms.py](app/models/sms.py) | Table historique des requêtes/réponses SMS. |
| [app/notifications.py](app/notifications.py) | Façade de l’ancien gestionnaire WebSocket. |
| [app/repositories/__init__.py](app/repositories/__init__.py) | Réexport des repositories de domaine. |
| [app/repositories/base.py](app/repositories/base.py) | Opérations de persistance élémentaires sans commit. |
| [app/repositories/editorial.py](app/repositories/editorial.py) | Requêtes brouillons/articles et verrou de publication. |
| [app/repositories/identity.py](app/repositories/identity.py) | Requêtes utilisateurs et contacts actifs. |
| [app/repositories/monitoring.py](app/repositories/monitoring.py) | Requêtes sources, volumes temporels et signaux urgents en attente. |
| [app/repositories/research.py](app/repositories/research.py) | Requêtes index documentaire et historique de chat. |
| [app/routes.py](app/routes.py) | Façade de l’ancien import du routeur. |
| [app/schemas/__init__.py](app/schemas/__init__.py) | Réexport des contrats publics historiques. |
| [app/schemas/ai.py](app/schemas/ai.py) | Validation stricte des réponses structurées de brouillon Gemini. |
| [app/schemas/articles.py](app/schemas/articles.py) | Contrats publication et lecture publique. |
| [app/schemas/auth.py](app/schemas/auth.py) | Contrats credentials/jetons et validation email/mot de passe. |
| [app/schemas/drafts.py](app/schemas/drafts.py) | Contrat de lecture des brouillons. |
| [app/schemas/maharavo.py](app/schemas/maharavo.py) | Contrats des trois capacités Maharavo. |
| [app/schemas/research.py](app/schemas/research.py) | Contrats recherche, sessions, messages et réponses du Copilot. |
| [app/schemas/signals.py](app/schemas/signals.py) | Contrats ingestion, analyse et recoupement. |
| [app/schemas/sms.py](app/schemas/sms.py) | Contrats de requête/réponse du simulateur SMS. |
| [app/schemas/sources.py](app/schemas/sources.py) | Contrats de création et lecture des sources. |
| [app/services/__init__.py](app/services/__init__.py) | Façade des fonctions métier historiques. |
| [app/services/auth.py](app/services/auth.py) | Inscription contrôlée et connexion. |
| [app/services/chat.py](app/services/chat.py) | Sessions privées, contrôle de propriété et enregistrement des messages. |
| [app/services/drafts.py](app/services/drafts.py) | Génération IA ou locale et création des brouillons. |
| [app/services/editorial.py](app/services/editorial.py) | Publication autorisée et indexation atomique. |
| [app/services/maharavo.py](app/services/maharavo.py) | Suivi de recherche, observations média et règles de confiance. |
| [app/services/notifications.py](app/services/notifications.py) | Choix des destinataires et composition des alertes. |
| [app/services/research.py](app/services/research.py) | Indexation, recherche lexicale, réponse web ou locale. |
| [app/services/signals.py](app/services/signals.py) | Ingestion, normalisation, urgence et pistes de recoupement. |
| [app/services/sms.py](app/services/sms.py) | Recherche de résumé approuvé et enregistrement de la réponse citoyenne. |
| [app/services/sources.py](app/services/sources.py) | Création des sources et transaction associée. |
| [app/tests/__init__.py](app/tests/__init__.py) | Déclaration du package, sans tâche ni service démarré à l’import. |
| [app/tests/test_backend.py](app/tests/test_backend.py) | Tests HTTP/WebSocket, sécurité, transactions, compatibilité et concurrence PostgreSQL. |
| [app/tests/test_migrations.py](app/tests/test_migrations.py) | Tests de création/adoption/refus/downgrade et SQL hors connexion. |
| [app/tests/test_postgresql_migrations.py](app/tests/test_postgresql_migrations.py) | Tests du schéma neuf et du véritable SQL historique sur PostgreSQL. |
| [app/utils/__init__.py](app/utils/__init__.py) | Déclaration du package, sans tâche ni service démarré à l’import. |
| [app/utils/text.py](app/utils/text.py) | Normalisation et tokenisation sans accès réseau ni base. |
| [app/workers/__init__.py](app/workers/__init__.py) | Façade différée du traitement historique sans lancer de tâche. |
| [app/workers/ingestion.py](app/workers/ingestion.py) | Lot supervisé de signaux urgents avec session autonome. |
| [app/workers/media.py](app/workers/media.py) | Point d’entrée d’enregistrement d’une analyse guidée, avec contrôle du compte. |
| [app/workers/notifications.py](app/workers/notifications.py) | Point d’entrée d’alerte avec passerelle remplaçable. |
| [app/workers/research.py](app/workers/research.py) | Point d’entrée de recherche avec session autonome. |

| Autre fichier | Responsabilité |
|---|---|
| [alembic.ini](alembic.ini) | Localisation des migrations et chemin Python. |
| [alembic/env.py](alembic/env.py) | Exécution Alembic en ligne/hors connexion avec la configuration de l’application. |
| [alembic/script.py.mako](alembic/script.py.mako) | Modèle des prochaines révisions. |
| [alembic/versions/0001_modular_baseline.py](alembic/versions/0001_modular_baseline.py) | Schéma initial figé et adoption explicite validée des bases historiques. |
| [app/tests/legacy_contract.json](app/tests/legacy_contract.json) | Manifeste figé des opérations, réponses HTTP et exigences d’authentification historiques. |
| [app/tests/legacy_response_fields.json](app/tests/legacy_response_fields.json) | Manifeste figé des champs de réponse historiques. |
| [requirements.txt](requirements.txt) | Dépendances d’exécution existantes et pilote PostgreSQL. |
| [requirements-dev.txt](requirements-dev.txt) | Dépendances d’exécution et client HTTP des tests. |
| [.env.example](.env.example) | Variables de configuration documentées. |
| [Dockerfile](Dockerfile) | Image Python 3.12, dépendances et utilisateur applicatif. |
| [.dockerignore](.dockerignore) | Exclusion des secrets et artefacts locaux du contexte Docker. |
| [database/fanilo_postgresql.sql](database/fanilo_postgresql.sql) | Schéma historique conservé ; Alembic pilote désormais les évolutions. |

### Pré-calcul de corroboration

Depuis une actualité, l’application lance en arrière-plan une recherche de sources dans les documents FANILO accessibles à l’utilisateur, GDELT et les flux RSS configurés. Google Fact Check peut également être activé avec `GOOGLE_FACT_CHECK_API_KEY` dans le fichier `Backend/.env` local. OpenRouter propose une affirmation et des évaluations à partir des extraits disponibles : les titres seuls ne suffisent pas, les passages cités doivent être présents dans les extraits et les reprises détectées ne sont pas comptabilisées automatiquement. Le journaliste doit lire les sources, corriger les propositions et valider le calcul. Le pourcentage provisoire n’est disponible qu’avec au moins deux groupes de sources conclusifs ; il ne mesure pas la probabilité de vérité.

Les travaux et leurs résultats sont privés, conservés en mémoire pendant 15 minutes après leur fin et perdus au redémarrage. Cette implémentation locale nécessite un seul processus backend ; un déploiement à plusieurs processus ou serveurs doit utiliser une file de tâches et un cache partagés. Les recherches externes peuvent être indisponibles et Google Fact Check reste facultatif.
