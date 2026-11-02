# FA AI MARINANA — Cahier technique backend

## 1. Responsabilité

Eric prend en charge l’API, la base de données, l’authentification, les droits,
les workers d’orchestration, la persistance, la publication, la synchronisation
hors connexion et la passerelle SMS. Le backend doit empêcher techniquement le
compte IA de publier.

## 2. Architecture et orchestration

Flux cible :

`sources autorisées → ingestion → signaux → dossiers/preuves → service IA → brouillons → validation serveur → publications → portail/cache/SMS`

- API HTTP authentifiée pour les utilisateurs et connecteurs.
- Workers séparés pour l’ingestion, la recherche, l’analyse média, les notifications
  et les tâches longues.
- WebSocket ou polling pour les alertes du tableau de bord.
- Files de tâches avec reprise, idempotence, limite de débit et journal d’erreur.
- États explicites : `en attente`, `en cours`, `terminée`, `partielle`, `échouée`.
- Les pannes et quotas ne doivent jamais être transformés en absence de résultat.

## 3. Authentification et RBAC

Rôles minimum :

- `journaliste` : créer et modifier les dossiers et brouillons ;
- `éditeur` : valider, publier et corriger ;
- `administrateur` : gérer comptes, connecteurs et paramètres techniques ;
- `contributeur` : envoyer des signaux sans publier ;
- `lecteur` : lire les versions publiques.

Les droits sont vérifiés dans l’API et dans la base, pas uniquement dans
l’interface ou le prompt. Un compte de service IA ne peut appeler ni validation ni
publication. Chaque action sensible est journalisée avec utilisateur, version,
date et motif.

## 4. Modèle de données

Entités minimales :

| Entité | Données essentielles |
|---|---|
| `users` | rédaction, rôles, langue, état du compte |
| `sources` | type, URL, autorisation, compétence, dernier contrôle |
| `signals` | source, contenu original, dates, langue, lieu, urgence |
| `cases` | responsable, thème, territoire, confidentialité, état |
| `claims` | formulation atomique, contexte, période, conclusion humaine |
| `evidence` | URL/fichier, extrait, page/minutage, empreinte, visibilité |
| `claim_evidence` | soutien/contradiction/contexte, justification, origine |
| `research_jobs` | plan, requêtes, documents, modèle, durée, erreurs, coût |
| `media_analyses` | fichier, type, outil, observations, indice, limites |
| `drafts` | langue, texte, références, version et état de relecture |
| `publications` | version validée, validateur, date, état actif/retiré |
| `corrections_audit` | auteur, action, versions, date et motif |
| `sms_exchanges` | identifiant, langue, version servie, livraison, rétention |

Les index privés et publics sont séparés ou cloisonnés. Les fichiers privés ne sont
pas servis par une URL prévisible. Les empreintes garantissent l’intégrité du fichier
conservé, pas la véracité de son contenu.

## 5. API d’intégration

Routes cibles :

```text
POST /signals
POST /cases
POST /claims
POST /research-jobs
GET  /research-jobs/{id}
POST /evidence
POST /media-checks
GET  /contacts
GET  /datasets
POST /drafts
POST /drafts/{id}/approve
POST /publications
POST /publications/{id}/corrections
GET  /public/articles
POST /sms/inbound
```

Le navigateur ne transmet jamais un texte libre comme version finale à publier.
`POST /publications` reçoit uniquement l’identifiant d’une version approuvée.

## 6. Publication et validation

1. Recevoir le brouillon et les références produites par Maharavo.
2. Vérifier les droits de l’utilisateur et l’existence des preuves référencées.
3. Figer une version éditoriale.
4. Exiger une validation explicite d’un éditeur.
5. Enregistrer validateur, date, version, langue, résumé et état actif.
6. Indexer uniquement la version publiée pour le portail et le SMS.
7. Créer une nouvelle version lors d’une correction substantielle.

Un brouillon IA, une analyse de confiance ou une alerte urgente ne deviennent jamais
automatiquement publics.

## 7. SMS et accès hors connexion

### SMS aux journalistes

- Déclencher une alerte selon urgence et préférences configurées.
- Envoyer un résumé court, un identifiant et l’action à reprendre.
- Mettre en file les messages, gérer les tentatives, les échecs et la livraison.
- Permettre un accusé de réception sans considérer celui-ci comme une validation.
- Utiliser le réseau mobile et une passerelle SMS ; le téléphone n’est pas supposé
  accéder directement à un satellite.

### SMS public

La requête citoyenne interroge uniquement les publications actives et validées.
Si aucune correspondance exacte n’est trouvée, répondre :

`Aucune vérification publiée trouvée pour cette demande.`

Le service ne lit jamais les brouillons, preuves privées ou analyses IA non validées.

## 8. Sécurité et qualité technique

- Hacher les mots de passe et conserver les secrets hors du code.
- Limiter taille et type des téléversements.
- Bloquer les requêtes serveur vers des adresses internes lors des téléchargements.
- Appliquer quotas, limites de débit, sauvegardes et restauration testée.
- Journaliser sans recopier inutilement les secrets ou numéros privés.
- Définir les durées de conservation et l’effacement des échanges SMS.
- Vérifier qu’aucune donnée privée n’apparaît dans les API publiques, le cache ou SMS.
- Tester refus de publication IA, séparation des index, correction de version et
  reprise après panne de worker.

## 9. Contrat d’intégration avec Maharavo

Eric fournit les identifiants, les données autorisées, les droits et les états de
tâche. Maharavo écrit uniquement dans les espaces `research`, `analysis` et
`drafts`. Le backend valide les schémas reçus, journalise la version du modèle et
rejette toute sortie sans références ou dépassant les limites configurées.

Le backend expose à l’interface les citations, limites, erreurs et états partiels.
Il ne transforme jamais une erreur IA en réponse réussie et ne permet aucune
publication depuis le compte de service IA.
