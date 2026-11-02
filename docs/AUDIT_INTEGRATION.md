# Audit préalable — 2 novembre 2026

## Périmètre et état initial

Audit réalisé avant modification : inventaire et lecture des 150 fichiers texte du backend (8 345 lignes), 13 fichiers Java/manifestes (801 lignes), 12 documents texte (1 713 lignes), README, Compose et configurations. Les documents binaires de référence restent conservés ; leurs versions Markdown et archives ont été examinées. Aucun fichier de consignes AGENTS.md trouvé dans le projet. Aucune base utilisateur ni secret n'a été consulté ou modifié.

Le répertoire contient déjà des changements non commités du connecteur Maharavo et de sa documentation. Ils sont conservés. Ce rapport distingue l'existant des ajouts de cette intervention.

## Architecture découverte

- `Backend/app` : FastAPI synchrone, Pydantic, SQLAlchemy, PostgreSQL/psycopg ; SQLite pour tests isolés. API v1 et alias historiques, services/repositories et façades de compatibilité.
- Trois migrations Alembic : schéma initial, stockage des investigations et RBAC/sessions. Adoption historique explicite et données anciennes en quarantaine.
- Six rôles sans héritage implicite, invitations, sessions révocables, refresh tokens rotatifs, mots de passe scrypt/compatibilité bcrypt. SERVICE_IA ne peut ni valider ni publier, y compris au flush ORM.
- Isolation par rédaction et dataset, clés étrangères composites, vues publiques à champs limités et compte PostgreSQL public distinct requis en production.
- Dossiers, affirmations, preuves et associations existent en SQL ; API dossiers rudimentaire, absence de routes affirmations/lecture des preuves/modification/archivage et pagination.
- Brouillons liés obligatoirement à un signal. Validation liée à la version et empreinte du contenu exact ; modification invalide l'approbation. Publication/correction/retrait et audit des corrections présents. L'historique initial ne conserve pas toutes les versions de brouillons.
- Les workers sont des fonctions supervisées sans file durable. Les appels IA existants sont synchrones. Ne pas annoncer un worker autonome ou une file Celery opérationnels.
- Maharavo : contrats backend proposés et transport indépendant présents, mais aucune implémentation externe, URL/API réelle ni SDK. `/maharavo/research` renvoie 503. Gemini facultatif et pré-analyse locale sont distincts ; les observations média sont saisies, pas une expertise automatisée.
- SMS : recherche dans la vue publique et historique présents ; passerelle explicitement simulée, aucun webhook ou opérateur configuré. Texte sans résultat incorrect par rapport à la mission.
- Hors ligne : aucune API de synchronisation ni cache mobile réel.
- `Touche/front` : Java ME MIDP 2.0/CLDC 1.1, Canvas et composants réutilisables. Connexion par code fixe 1234, chat fictif, listes de publications locales. Aucun client HTTP/JSON ni session réelle. Script de compilation dépendant de chemins machine.

## Risques et dépendances

Les autorisations sont revérifiées par middleware puis dépendances et services éditoriaux ; chaque nouvelle route doit avoir sa politique. L'isolation actuelle autorise le partage au sein d'une rédaction, pas une ACL nominative par dossier. Sources de veille administrées séparément des preuves journalistiques. La recherche lexicale ne prouve pas une confirmation indépendante. Les numéros SMS sont enregistrés dans un historique privé et nécessitent une politique de rétention en déploiement. Limitation des requêtes absente. Les dépendances sont épinglées ; la disponibilité des versions et des fournisseurs distants n'est pas déduite de leur nom.

## Plan adapté, critères et limites

1. Fondations : réutiliser les tables ; migration additive seulement pour l'historique des brouillons. Vérifier la concordance Alembic/ORM et conserver les données.
2. Sécurité : compléter les permissions explicites des nouvelles opérations, conserver les garde-fous IA et tester refus/isolations. Ajouter des limites locales configurables aux entrées publiques sensibles.
3. Investigations : CRUD utile, pagination/filtres, affirmations, lecture/référencement des preuves et relations affirmation/preuve, sources consultables sans droits de configuration. Aucun verdict définitif attribué automatiquement.
4. IA : préserver le connecteur Maharavo fermé sans protocole réel ; fournir une recherche documentaire locale clairement identifiée sur les pièces enregistrées, sans la présenter comme recherche web ou analyse Maharavo.
5. Traitements : ne pas introduire un broker sans fournisseur exploitable ; documenter les traitements supervisés et les limites restantes.
6. Publication : compléter la création humaine et la liste des brouillons liés au dossier, historique des révisions, revue et validation existantes conservées.
7. Services : réponse SMS exacte ; snapshot public vérifiable par empreinte, versions de contenu et suppression des éléments retirés au remplacement atomique du cache.
8. Frontend : vrai HTTP, authentification, erreurs/chargements, parcours dossier/affirmation/preuve/brouillon/relecture/publication et cache exclusivement public dans le client Java ME.
9. Qualité : tests HTTP du parcours local et refus de publication IA, migrations, non-fuite SMS/sync, compilation Java et documentation reproductible.

Une intégration complète avec Maharavo externe et SMS livré ne peut être certifiée sans leurs interfaces et accès réels. Le parcours local doit être présenté avec cette limite explicite. Les tests réseau externes ne seront jamais remplacés par une fausse réussite.
