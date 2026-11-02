# Backend FA AI MARINANA — architecture modulaire

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
- Les inscriptions publiques restent disponibles en développement pour les démonstrations historiques ; elles sont désactivées en production. La création d'un compte approuvé passe par la CLI opérateur.

## Configuration

Copier `Backend/.env.example` vers `Backend/.env` pour une exécution Python locale. Le chargeur lit ce fichier une seule fois ; les variables du processus ont priorité. La configuration Pydantic est validée au démarrage. `DATABASE_URL` prime sur les variables `DATABASE_*`.

Pour Docker Compose, utiliser les variables du shell ou le fichier `.env` de la racine : Compose ne charge pas automatiquement `Backend/.env`. Le fichier `Backend/.env` est exclu de l'image par `.dockerignore`.

Développement : renseigner un secret JWT stable pour conserver les sessions entre redémarrages et partager les jetons entre processus. Sans secret, un secret aléatoire temporaire est généré et un avertissement est émis. Aucun secret fixe connu n'est utilisé.

Production : `ENVIRONMENT=production`, `JWT_SECRET` aléatoire d'au moins 32 octets, `ALLOW_PUBLIC_REGISTRATION=false`, `AUTO_CREATE_TABLES=false`. La configuration refuse un secret insuffisant, les inscriptions publiques ou la création implicite de tables. Les identifiants PostgreSQL, origines CORS, HTTPS et sauvegardes doivent être configurés dans l'environnement de déploiement.

## Installation et migrations

Depuis `Backend/`, avec l'environnement Python activé :

```sh
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Pour une base neuve avec Docker, depuis la racine :

```sh
docker compose up --build
```

Compose exécute Alembic avant Uvicorn. PostgreSQL n'est exposé que sur l'interface locale. Le processus applicatif du conteneur utilise un utilisateur non privilégié.

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
python -m app.core.manage_users --email redacteur@example.org --role Editeur
```

Le mot de passe est demandé au terminal, jamais dans la ligne de commande.

## Workers et intégrations

Les quatre modules workers sont des fonctions appelables avec leurs propres sessions : ingestion des urgences, recherche, enregistrement d'analyse média guidée, notifications. `python -m app.workers.ingestion` exécute un lot ; `/api/workflow/process-pending` conserve le déclenchement supervisé historique.

Aucun ordonnanceur ni processus autonome n'est démarré implicitement. Les requêtes de recherche restent synchrones. Redis n'est pas ajouté : il deviendra utile avec une file durable et une diffusion WebSocket entre processus. L'étape suivante pourra introduire un broker, des identifiants de job, retries, idempotence et une outbox transactionnelle. Les lots actuels ne garantissent pas une exécution concurrente sans conflit.

Gemini reste facultatif. Les réponses structurées des brouillons sont validées avec Pydantic ; une indisponibilité ou une réponse invalide déclenche le moteur local. La clé, le modèle et les délais sont configurables. La compatibilité réelle du modèle et du service externe nécessite une recette avec une clé valide.

Maharavo utilise actuellement le fournisseur Gemini partagé, avec un protocole injectable. Aucune API externe Maharavo distincte n'est supposée. Les analyses média enregistrent des observations fournies par un opérateur ; elles ne réalisent pas de détection automatique de manipulation.

La passerelle SMS reste un simulateur explicite. Elle n'envoie aucun SMS et ne journalise ni numéro ni contenu. `/sms/citizen` calcule une réponse JSON ; aucun webhook opérateur, accusé de livraison ou envoi réel n'est annoncé.

## Vérification

Depuis `Backend/` :

```sh
python -B -m unittest discover -s app/tests -v
```

Les tests utilisent SQLite en mémoire, sans appel IA externe. Le manifeste de compatibilité conserve les opérations HTTP et champs de réponse relevés avant la restructuration. Les tests couvrent authentification, validations, routes historiques/v1, publication atomique, conflits, SMS, recherche, sessions privées, WebSocket authentifié, injection fournisseur et capacités Maharavo. Les tests Alembic vérifient création, adoption, refus d'un schéma incompatible et génération SQL hors connexion.

Pour tester PostgreSQL, utiliser uniquement une base jetable, puis définir `FANILO_TEST_DATABASE_URL` et relancer la même commande. Les tests HTTP suppriment et recréent les tables dans cette base. Les tests de migrations PostgreSQL utilisent des schémas isolés, et le test de publication concurrente utilise de véritables verrous PostgreSQL.

## Limites et prochaines étapes

Cette livraison constitue une base modulaire et testée, sans annoncer la fin de tous les travaux de l'audit. Restent à traiter : limites de débit, révocation des jetons, autorisations par rédaction/dossier, audit des décisions, versions et retraits d'articles, contraintes et index SQL harmonisés, recherche à grande échelle, contexte conversationnel, collecte planifiée, file durable, diffusion WebSocket partagée, SMS réel et intégration mobile réseau. Les WebSockets authentifient à la connexion ; expiration et révocation pendant une connexion prolongée restent à gérer.

Le frontend Java ME reste une démonstration avec données locales. Les routes historiques sont conservées pour son intégration ultérieure ; cela ne constitue pas une preuve de connexion mobile de bout en bout.
