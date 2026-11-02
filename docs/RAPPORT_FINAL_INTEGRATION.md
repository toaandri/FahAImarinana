# Rapport de livraison — FA AI MARINANA

Date : 2 novembre 2026. Le parcours documentaire et éditorial **local** fonctionne et a été testé depuis le client Java ME vers un vrai backend. L'intégration globale avec Maharavo externe et un opérateur SMS n'est pas terminée : leurs interfaces réelles et accès ne sont pas disponibles dans le dépôt.

## 1. Architecture initiale

Backend déjà modulaire : Python/FastAPI, Pydantic, SQLAlchemy, PostgreSQL/psycopg, Alembic, API v1 et alias historiques. RBAC à six rôles, invitations, sessions révocables, validation de version exacte, isolation rédaction/dataset et projections SQL publiques existaient. Le frontend Java ME utilisait un code d'accès fixe, des réponses fictives et des listes locales. Les workers étaient des fonctions supervisées sans file durable. Le connecteur Maharavo, déjà en cours de modification au début de cette intervention, ne disposait d'aucune interface fournisseur réelle.

Le [rapport d'audit préalable](AUDIT_INTEGRATION.md) a précédé les modifications. Les fonctionnalités et changements déjà présents sont conservés. Des commits ont aussi été ajoutés au dépôt pendant la session ; aucun commit, reset, push ou déploiement n'a été exécuté par cette intervention.

## 2. Modifications réalisées

- Dossiers : pagination, filtres, recherche, modification avec détection de conflit et archivage.
- Affirmations : création et consultation ; aucun verdict humain accepté arbitrairement à la création.
- Preuves : consultation, saisie de références originales/source/date, associations proposées avec affirmation, refus des liens inter-dossiers et doublons.
- Brouillons : création humaine rattachée au signal/dossier/affirmation ; révision accessible en POST pour MIDP, validation précédente invalidée après modification et historique privé immuable des événements.
- Recherche : résultats lexicaux locaux persistés avec extraits et références, limites explicites et état partiel si le dossier dépasse la limite de traitement. Aucun résultat local présenté comme Maharavo ou recherche web.
- Traitements : file persistante en base, worker par lots, prise atomique, états d'échec, annulation et récupération des traitements interrompus.
- Public : instantané complet, empreintes/ETag, date de synchronisation et cache RMS atomique ; un retrait disparaît du cache après synchronisation réussie.
- SMS : consultation HTTP des seules publications actives et texte imposé sans résultat ; livraison opérateur toujours indisponible.
- Sécurité : nouvelles permissions explicites, politiques couvrant toutes les routes, quotas publics/authentification par processus/IP, réponses privées sans cache HTTP et limite de taille d'article.
- Mobile : véritable connexion email/mot de passe, tokens en mémoire et refresh, menus selon permissions, parcours documentaire/éditeur, états chargement/erreur/vides, pagination et confirmations humaines. Les écrans fictifs ont été remplacés par ces opérations réelles.

## 3. Fichiers créés pendant l'intégration

```text
Backend/alembic/versions/0004_draft_history.py
Backend/app/models/revisions.py
Backend/app/schemas/investigations.py
Backend/app/services/investigations.py
Backend/app/services/tasks.py
Backend/app/services/synchronization.py
Backend/app/middleware/rate_limit.py
Backend/app/workers/research_queue.py
Backend/app/tests/test_integration_workflow.py
Backend/scripts/run_local.py
Backend/scripts/verify_postgresql.py
Backend/scripts/verify_mobile.py
Touche/front/MANIFEST.MF
Touche/front/src/network/Json.java
Touche/front/src/network/Api.java
Touche/front/src/network/PublicCache.java
Touche/front/src/screens/ApiForm.java
Touche/front/src/screens/EntryForm.java
Touche/front/src/screens/NewsroomScreen.java
Touche/front/src/screens/CaseScreen.java
Touche/front/src/screens/LinkEvidenceScreen.java
Touche/front/src/screens/ResourceScreen.java
Touche/front/src/screens/DraftScreen.java
Touche/front/tests/CodecTest.java
Touche/front/tests/MobileSmoke.java
docs/AUDIT_INTEGRATION.md
docs/INTEGRATION_TECHNIQUE.md
docs/RAPPORT_FINAL_INTEGRATION.md
```

Les JAR/JAD construits sont dans `Touche/front/build/`, ignoré par Git ; les anciennes distributions de `deploy/` restent conservées. Une partie des fichiers ci-dessus est désormais déjà suivie dans les commits arrivés pendant la session ; cet inventaire décrit le travail, pas seulement le dernier `git status`.

## 4. Fichiers existants modifiés

```text
.gitignore
README.md
docker-compose.yml
Backend/.env.example
Backend/ARCHITECTURE.md
Backend/PERSISTENCE.md
Backend/app/main.py
Backend/app/core/config.py
Backend/app/core/constants.py
Backend/app/core/rbac.py
Backend/app/core/route_policies.py
Backend/app/database/scope.py
Backend/app/database/guards.py
Backend/app/models/__init__.py
Backend/app/repositories/publications.py
Backend/app/schemas/articles.py
Backend/app/schemas/editorial.py
Backend/app/schemas/signals.py
Backend/app/services/signals.py
Backend/app/services/sms.py
Backend/app/services/drafts.py
Backend/app/services/draft_workflow.py
Backend/app/services/editorial.py
Backend/app/api/v1/endpoints/investigations.py
Backend/app/api/v1/endpoints/draft.py
Backend/app/api/v1/endpoints/public.py
Backend/app/tests/fixtures.py
Backend/app/tests/test_backend.py
Touche/lancement.sh
Touche/front/src/screens/LoginScreen.java
Touche/front/src/screens/ChatScreen.java
Touche/front/src/screens/SmsNewsScreen.java
Touche/front/src/screens/PublicationScreen.java
```

Les autres modifications Maharavo déjà présentes au démarrage n'ont pas été effacées. Le manifeste historique des routes est conservé ; son test tient explicitement compte du nouveau 422 associé aux paramètres de pagination publique.

## 5. Base de données

Nouvelle table : `draft_revisions`, ajoutée par Alembic `0004_draft_history`. Champs : brouillon, acteur, version, événement, snapshot JSON, timestamps et périmètre/confidentialité. Index par brouillon/identifiant et rédaction/dataset/date. Contraintes de version, événements, visibilité et clés étrangères composites. Triggers d'immutabilité SQLite et PostgreSQL, dont interdiction de TRUNCATE PostgreSQL.

Les tables `cases`, `claims`, `evidence`, `claim_evidence`, `signals`, `drafts`, `research_jobs`, `publications`, `corrections_audit` et `sms_exchanges` sont réutilisées. Leurs colonnes ne sont pas recréées. Les empreintes publiques et l'état de synchronisation sont calculés/enregistrés dans le cache du client ; aucune table redondante n'est ajoutée à cette fin. Aucune donnée utilisateur existante n'a été supprimée et aucune base applicative persistante n'a été migrée pendant la recette.

## 6. Endpoints disponibles

Le [catalogue détaillé des endpoints](INTEGRATION_TECHNIQUE.md#api-ajoutée-ou-complétée) décrit les contrats, permissions, pagination et erreurs. Les ajouts principaux sont les ressources `/cases/{id}/claims`, `/evidence`, `/drafts`, `/research`, `/research/tasks`, les associations affirmation/preuve, `/research-jobs/{id}`, `/drafts/{id}/history`, `/drafts/{id}/revisions` et `/public/sync`. Les routes existantes d'authentification, administration, validation, publication, correction et retrait sont conservées. OpenAPI reste accessible à `/docs` et `/openapi.json` lorsque le serveur est lancé.

## 7. Intégrations réalisées

Intégrations réelles vérifiées : Java ME → HTTP FastAPI → SQLAlchemy ; PostgreSQL avec migrations et contrôles de concurrence existants ; recherche locale → stockage ; éditeur humain → publication publique ; consultation HTTP SMS → vue publique ; flux public → stockage RMS du mobile.

Les sessions éditoriales et journalistiques sont distinctes dans le test réseau. Les extraits privés ne figurent jamais dans le flux public ni dans les réponses SMS. Le compte IA reste exclu de validation/publication dans les tests HTTP et les gardes de données.

## 8–9. Tests exécutés et résultats

| Vérification | Résultat final |
|---|---|
| Suite PostgreSQL 17 temporaire, `scripts/verify_postgresql.py` | **87 tests réussis, aucun ignoré**, 41,015 s. Inclut migrations neuves/historiques, comparaison ORM, rôle public en lecture seule, concurrence éditoriale et refresh, contrôles d'accès et nouvelles recherches/tâches/synchronisation. |
| Suite SQLite isolée, `unittest discover` | **87 tests exécutés : 80 réussis, 7 spécifiques PostgreSQL ignorés**, 27,211 s ; contrôle ciblé des deux modifications successives également réussi après la dernière correction. |
| Java ME réel, `scripts/verify_mobile.py` | **`CODEC_TEST_OK` et `MOBILE_SMOKE_OK`**, y compris démarrage par `run_local.py`, authentifications distinctes, création/révision/recherche, relecture/validation/publication, SMS HTTP, historique, cache RMS et suppression après retrait. |
| Distribution mobile | Compilation réussie ; JAR et JAD générés dans `Touche/front/build/`. Avertissements Java 8 et collections non génériques attendus pour ce code MIDP. |
| Configuration Docker Compose | `docker compose config --quiet` réussi. Aucun build/démarrage Docker complet annoncé. |
| Dépendances Python | `pip check` : aucune dépendance cassée. Ce contrôle n'est pas un audit de vulnérabilités des fournisseurs. |
| Syntaxe et différences | Analyse syntaxique Python et `bash -n` réussies ; `git diff --check` vérifié après correction documentaire. |

Les tests emploient exclusivement des données explicitement réservées aux tests. Le test Maharavo préexistant vérifie les contrats, les erreurs, les timeouts et les résultats partiels avec transport unitaire ; il n'appelle pas un vrai moteur. Les clusters, backends et données temporaires des recettes ont été arrêtés/nettoyés. Aucun serveur de production n'est lancé par ces tests.

## 10. Problèmes non résolus

Le moteur Maharavo externe, la recherche web approfondie fournie par ce moteur, l'envoi SMS opérateur et le workflow linguistique de traduction validée restent non disponibles. Restent aussi : ACL nominative par dossier, tous les états éditoriaux indicatifs, notifications de soumission, administration mobile complète, ingestion documentaire/upload et expertise média automatisée. La file implémentée traite les recherches locales, pas ces fournisseurs absents.

Le client a été vérifié sous MicroEmulator headless ; l'intégralité des interactions tactiles et le déploiement sur téléphone CLDC physique restent à recetter. Les réponses mobiles sont limitées à 256 Kio et le snapshot serveur à 2 000 publications. Un ancien article retiré peut subsister sur un appareil resté hors réseau ; la date et l'avertissement de péremption sont affichés.

## 11. Simulations ou indisponibilités

Le simulateur SMS préexistant reste explicitement un simulateur ; il n'a pas été substitué à un fournisseur réel. `/sms/citizen` est une véritable consultation HTTP, sans livraison. `/maharavo/research` conserve 503 tant qu'aucun adaptateur réel n'est documenté/configuré. La recherche documentaire nouvelle est **locale et lexicale**, pas une analyse Maharavo simulée. Les anciens contenus fictifs de l'interface ont été retirés des écrans exécutés ; seules les fixtures de tests/démonstration séparées restent fictives.

## 12. Configuration nécessaire

`Backend/.env.example` reste la référence. PostgreSQL : `DATABASE_URL` ou les variables `DATABASE_*` ; identité publique distincte `PUBLIC_DATABASE_URL` obligatoire en production. Sécurité : secret JWT stable, paramètres de session/invitation, origines CORS, création implicite désactivée et inscriptions sur invitation.

Nouvelles variables : `AUTH_REQUESTS_PER_MINUTE`, `PUBLIC_REQUESTS_PER_MINUTE`, toutes deux à 60 par défaut, par processus/IP. Les variables `MAHARAVO_*` et `GEMINI_*` restent facultatives et distinctes. `SMS_BACKEND=simulation` décrit l'état réel. `MICROEMU_HOME` désigne une installation locale de l'émulateur. Le lanceur local crée un secret JWT persistant protégé si absent, dans un dossier exclu de Git.

## 13. Commandes de lancement

Depuis la racine, après installation des dépendances :

```sh
.venv/bin/python Backend/scripts/run_local.py --create-account
.venv/bin/python Backend/scripts/run_local.py
MICROEMU_HOME=/chemin/vers/microemulator-2.0.4 bash Touche/lancement.sh
```

Répéter la création interactive pour disposer des rôles administrateur, journaliste et éditeur. Les mots de passe sont choisis et saisis au terminal, jamais fournis par défaut. Le backend écoute sur `http://127.0.0.1:8000` et expose `/docs`. Le guide donne les commandes exactes d'installation, PostgreSQL, Alembic, worker et tests, ainsi qu'un parcours manuel complet.

## 14. Prochaines améliorations

Priorité : fournir et inspecter le protocole/SDK réel de Maharavo et un fournisseur SMS autorisé, puis terminer leur adaptateur, orchestration et recette. Ensuite : traduction avec validation linguistique, soumission/notifications éditoriales explicites, ACL de dossier, uploads sécurisés, sélecteurs documentaires mobiles et administration complète. Pour la production : quotas distribués, snapshots paginés, TLS, sauvegardes/restauration, supervision et politique de rétention SMS. Ne pas annoncer l'intégration globale terminée avant ces recettes.
