# Authentification, sessions et RBAC

Le contrôle est explicite, sans hiérarchie implicite entre rôles. Les anciennes valeurs `Journaliste` et `Editeur` sont migrées vers `JOURNALISTE` et `EDITEUR`. Aucun compte existant n'est promu administrateur. Les anciennes routes `/api/...` et leurs alias `/api/v1/...` restent disponibles.

## Matrice métier

| Fonction | JOURNALISTE | EDITEUR | ADMINISTRATEUR | CONTRIBUTEUR | LECTEUR | SERVICE_IA |
|---|---|---|---|---|---|---|
| Lire les articles publics | Oui | Oui | Oui | Oui | Oui | Oui |
| Créer un dossier | Oui | Non | Non | Non | Non | Non |
| Consulter les dossiers privés | Oui | Oui | Non | Non | Non | Non |
| Ajouter une preuve | Oui | Non | Non | Non | Non | Non |
| Recherche | Oui | Non | Non | Non | Non | Selon scopes |
| Enregistrer une analyse | Oui | Non | Non | Non | Non | Selon scopes |
| Créer un brouillon | Oui | Non | Non | Non | Non | Selon scopes |
| Lire les brouillons | Oui | Oui | Non | Non | Non | Réponse de sa création uniquement |
| Modifier un brouillon | Oui | Non | Non | Non | Non | Non |
| Relire / valider une version | Non | Oui | Non | Non | Non | Jamais |
| Publier / corriger / retirer | Non | Oui | Non | Non | Non | Jamais |
| Gérer les comptes | Non | Non | Oui | Non | Non | Non |
| Gérer les connecteurs | Non | Non | Oui | Non | Non | Non |
| Paramètres techniques | Non | Non | Oui | Non | Non | Non |
| Soumettre et compléter ses signalements | Non | Non | Non | Oui | Non | Non |
| Traitement supervisé des signaux | Non | Non | Non | Non | Non | Scopes tasks.run et drafts.create |

Chaque compte authentifié peut consulter son profil et gérer ses propres sessions. Le lecteur ne peut consulter aucun contenu éditorial privé. Les articles et le simulateur de consultation SMS restent accessibles sans compte.

Les permissions additionnelles restent explicites : alertes de lecture pour journalistes/éditeurs, déclenchement d'alertes pour éditeurs, réindexation pour administrateurs. Les autorisations sont définies dans [rbac.py](app/core/rbac.py), sans wildcard administrateur.

Un administrateur ne peut pas changer son propre rôle via l'API. Il peut nommer d'autres personnes par invitation, conformément à sa fonction de gestion des comptes. Son compte administrateur reste interdit de publication. Une identité de service a un type `service` immuable et un rôle fixé à `SERVICE_IA`, protégés aussi par la base ; elle ne peut pas être transformée en éditeur.

## Inscription contrôlée et premier administrateur

Appliquer les migrations, puis créer le premier compte via la CLI opérateur depuis `Backend/` :

```sh
alembic upgrade head
python -m app.core.manage_users --email administrateur@example.org --role ADMINISTRATEUR
```

Le mot de passe est saisi au terminal. La CLI est une opération de confiance de l'administrateur système, distincte d'une inscription publique.

Parcours normal :

1. L'administrateur se connecte avec `POST /api/auth/login`.
2. Il appelle `POST /api/admin/invitations` avec `email` et un rôle humain explicite.
3. Il transmet lui-même le secret d'invitation au destinataire ; aucune messagerie n'est appelée automatiquement.
4. Le destinataire utilise `POST /api/auth/register` avec `email`, `mot_de_passe` et `invitation_token`.

L'invitation est liée à l'email normalisé, à la rédaction, au dataset, à son émetteur et au rôle accordé. Elle expire après 48 heures par défaut et n'est utilisable qu'une fois. Le rôle et le périmètre ne sont jamais pris dans le corps libre de l'inscription. Une invitation dont l'émetteur n'est plus un administrateur actif est refusée.

`ALLOW_PUBLIC_REGISTRATION` reste accepté comme ancienne variable, mais ne permet jamais de contourner les invitations. Sa valeur recommandée est false. Les réponses contenant des secrets portent `Cache-Control: no-store`.

## Sessions et jetons

- Access token JWT HS256 : 15 minutes par défaut, avec `sub`, `sid`, `jti`, `ver`, `type`, `iat`, `nbf`, `exp`, `iss` et `aud`.
- Refresh token opaque aléatoire : durée absolue de 30 jours par défaut. Seul son SHA-256 est enregistré ; le secret aléatoire n'est pas stocké en clair.
- Une connexion crée une session distincte ; un refresh renouvelle les deux jetons et consomme le refresh précédent.
- La réutilisation d'un refresh déjà consommé révoque toute sa session, y compris les nouveaux access tokens de cette session.
- Un refresh dont le secret est faux ne peut pas révoquer une session légitime.
- Chaque appel authentifié consulte le compte et la session dans PostgreSQL. Le rôle dans le JWT n'accorde aucun droit : la base reste l'autorité.
- Déconnexion, suspension, changement de rôle et changement de mot de passe invalident immédiatement les sessions concernées pour les requêtes suivantes.
- Les diffusions WebSocket revérifient la session et les permissions avant chaque envoi. Une connexion révoquée est fermée avant de recevoir la prochaine alerte.

Le frontend doit sérialiser ses demandes de refresh : deux utilisations concurrentes du même refresh déclenchent volontairement la protection contre la réutilisation. Un ancien access token reste utilisable jusqu'à son expiration tant que sa session n'est pas révoquée ; la rotation du refresh ne remplace pas la révocation de session.

Les jetons sont transportés dans le corps JSON des réponses et via l'en-tête `Authorization: Bearer ...` pour les appels authentifiés. Aucun refresh token n'est accepté comme access token et aucun secret n'est placé dans l'URL. Le stockage sécurisé des jetons dans le client et HTTPS restent des responsabilités du déploiement et du frontend.

### Endpoints d'authentification

| Méthode | Route | Usage |
|---|---|---|
| POST | /api/auth/register | Inscription avec invitation |
| POST | /api/auth/login | Connexion humaine |
| POST | /api/auth/service-token | Connexion d'une identité de service |
| POST | /api/auth/refresh | Rotation du refresh token |
| GET | /api/auth/me | Identité et permissions actuelles |
| GET | /api/auth/sessions | Sessions du compte courant |
| DELETE | /api/auth/sessions/{id} | Révoquer une de ses sessions |
| POST | /api/auth/logout | Révoquer la session courante |
| POST | /api/auth/logout-all | Révoquer toutes ses sessions |
| POST | /api/auth/password | Changer le mot de passe et révoquer ses sessions |

Les réponses d'inscription, de connexion et de refresh conservent `access_token` et `token_type`, et ajoutent `refresh_token`, `expires_in`, `refresh_expires_in` et `session_id`.

### Hachage des mots de passe

Les nouveaux secrets utilisent scrypt avec sel aléatoire de 16 octets, N=32768, r=8, p=1 et résultat de 32 octets. Le format contient une version des paramètres pour permettre une évolution contrôlée. Les anciens hashes bcrypt restent vérifiables et sont remplacés par scrypt après une connexion réussie. Aucune troncature silencieuse des mots de passe n'est effectuée ; les nouveaux mots de passe peuvent contenir jusqu'à 1024 caractères, avec une limite de 4096 octets UTF-8.

## Comptes IA

`POST /api/admin/service-accounts` crée une identité avec un `client_id`, un `client_secret` affiché une seule fois et une liste de scopes parmi :

- research.run
- analyses.write
- drafts.create
- tasks.run

Le secret est haché comme un mot de passe. La connexion humaine est refusée pour ce compte ; il utilise `/api/auth/service-token`. Ses permissions effectives sont l'intersection entre le rôle SERVICE_IA et ses scopes configurés. Aucun scope de publication, correction ou validation ne peut lui être attribué par cette API.

L'enregistrement d'une analyse de confiance n'autorise pas à renseigner une validation éditoriale. Un journaliste ou une IA doit laisser cette dimension à `non_evalue` ; la validation d'une version passe par le parcours éditeur distinct.

## Contrôles serveur

1. Le [middleware ASGI](app/middleware/authorization.py) vérifie l'authentification et la politique méthode/chemin avant l'analyse des corps privés. Les routes API inconnues sont refusées.
2. Les dépendances FastAPI `require_permission` réappliquent les contrôles et établissent le périmètre de rédaction/dataset.
3. Les services de validation, publication, correction et administration contrôlent leurs permissions directement : un appel Python ne contourne pas les contrôles HTTP.
4. Le hook ORM bloque aussi les transitions de validation/publication/audit sans acteur autorisé. Les sessions système réservées aux migrations et fixtures sont des capacités de confiance, jamais des dépendances HTTP.
5. Les contraintes et triggers SQL empêchent la conversion d'une identité IA en identité humaine. Les clés étrangères composites et les vues publiques de la phase de persistance sont conservées.

Un test parcourt OpenAPI pour vérifier que chaque opération privée a une politique de middleware. La séparation des rôles ne remplace pas le cloisonnement des rédactions : les deux s'appliquent simultanément.

## Validation et publication

<OPENROUTER_API_KEY>

1. Le journaliste crée le dossier et le brouillon, éventuellement avec l'aide d'un compte IA.
2. `GET /api/drafts/{id}/version` retourne la version du brouillon aux journalistes et éditeurs.
3. `PATCH /api/drafts/{id}` exige `expected_version`. Toute modification incrémente la version et annule sa validation.
4. L'éditeur peut relire avec `POST /api/workflow/drafts/{id}/review`.
5. Il valide avec `POST /api/workflow/drafts/{id}/validate`, en fournissant `expected_version` et les champs finaux de publication.
6. Il publie avec `/publish`. Le contenu doit correspondre exactement au contenu approuvé et la version doit toujours être courante, sinon 409.
7. Les corrections et retraits passent par `/api/workflow/publications/{id}/correct` et `/withdraw`, avec une justification et un audit transactionnel.

L'ancienne route `/publish` conserve son URL et son corps, mais une validation préalable par un éditeur est désormais obligatoire. Les autorisations anciennes donnant la publication aux journalistes sont volontairement retirées.

## Dossiers, contributions et administration

- Dossiers : GET/POST `/api/cases`, GET `/api/cases/{id}`, POST `/api/cases/{id}/evidence`.
- Contributions : POST `/api/contributions/signals`, GET `/api/contributions/{id}`, POST `/api/contributions/{id}/information`. Un contributeur ne complète que ses propres signalements et ne peut pas choisir un dossier privé arbitraire.
- Comptes : GET `/api/admin/users`, PATCH `/api/admin/users/{id}`, POST `/api/admin/invitations` et `/api/admin/service-accounts`.
- Connecteurs : GET/POST `/api/sources`, PATCH `/api/sources/{id}` pour activer/désactiver ou modifier la fréquence.
- Paramètres : GET `/api/admin/settings`, PUT `/api/admin/settings/{key}`. La liste est limitée à `ingestion_batch_size` (1–100) et `research_result_limit` (1–20), utilisés par les services. Aucun réglage de rôle, secret JWT ou identifiant de base n'est exposé par ces endpoints.

## Migration et configuration

[0003_auth_rbac.py](alembic/versions/0003_auth_rbac.py) ajoute les sessions, refresh tokens, invitations, contributions et paramètres techniques, ainsi que les métadonnées de validation des brouillons. Les deux premières migrations restent inchangées. Les jetons historiques sans session sont refusés après déploiement ; les utilisateurs doivent se reconnecter. Les comptes et mots de passe existants sont conservés.

```sh
alembic upgrade head
```

La migration est exécutée en ligne et refuse un retour arrière automatique susceptible de réactiver les anciens droits. Les paramètres sont documentés dans `.env.example` : JWT_SECRET, JWT_EXPIRE_MINUTES, JWT_ISSUER, JWT_AUDIENCE, REFRESH_EXPIRE_DAYS et INVITATION_EXPIRE_HOURS.

## Vérification

Depuis `Backend/` :

```sh
python -B -m unittest discover -s app/tests -v
```

Les tests utilisent SQLite en mémoire ou, avec `FANILO_TEST_DATABASE_URL`, une base PostgreSQL strictement jetable. Ils vérifient chaque rôle avec des requêtes permises et interdites, les refus hors HTTP, la rotation/relecture des refresh tokens, la révocation, les invitations, les hashes, les types de jetons, la version approuvée, les contributions privées, les WebSockets révoqués et la couverture des politiques. Les tests PostgreSQL vérifient aussi les refresh concurrents et la migration réelle.

Résultats de cette livraison : 54 tests réussis sur PostgreSQL 17 ; sur SQLite, 47 tests réussis et 7 tests PostgreSQL ignorés comme prévu. La syntaxe Python, `pip check`, `git diff --check` et `docker compose config --quiet` ont également été vérifiés. Aucune migration n'a été appliquée à une base applicative existante.

## Fichiers principaux

| Fichier | Responsabilité |
|---|---|
| [core/rbac.py](app/core/rbac.py) | Rôles, permissions explicites et contrôles métier |
| [core/security.py](app/core/security.py) | Scrypt, compatibilité bcrypt et vérification des JWT/sessions |
| [core/permissions.py](app/core/permissions.py) | Identité et injection des permissions dans FastAPI |
| [core/route_policies.py](app/core/route_policies.py) | Politiques méthode/chemin et liste des routes publiques |
| [middleware/authorization.py](app/middleware/authorization.py) | Vérification des permissions avant les endpoints privés |
| [models/authentication.py](app/models/authentication.py) | Sessions, refresh tokens hachés et invitations |
| [models/administration.py](app/models/administration.py) | Contributions privées et paramètres techniques bornés |
| [services/auth.py](app/services/auth.py) | Connexion, inscription contrôlée, rotation et révocation |
| [services/administration.py](app/services/administration.py) | Invitations, comptes, services IA et paramètres |
| [services/draft_workflow.py](app/services/draft_workflow.py) | Versions, relecture et validation du contenu exact |
| [api/v1/endpoints/auth.py](app/api/v1/endpoints/auth.py) | API d'authentification et gestion des sessions |
| [api/v1/endpoints/admin.py](app/api/v1/endpoints/admin.py) | API administrative, sans permission de publication |
| [api/v1/endpoints/investigations.py](app/api/v1/endpoints/investigations.py) | Dossiers, preuves et signalements autorisés |
| [core/manage_users.py](app/core/manage_users.py) | Création du premier administrateur par l'opérateur |
| [0003_auth_rbac.py](alembic/versions/0003_auth_rbac.py) | Migration du schéma et des anciens rôles |
| [test_auth_rbac.py](app/tests/test_auth_rbac.py) | Matrice HTTP des rôles et tests de sécurité des sessions |
