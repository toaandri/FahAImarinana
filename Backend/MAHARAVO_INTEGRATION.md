# Maharavo : inspection réelle et socle de connexion

## État de cette livraison

**Aucune connexion réelle à un moteur HTTP Maharavo n'est établie.** Le dépôt inspecté ne fournit ni serveur autonome, ni URL de service, ni OpenAPI/SDK ou protocole d'authentification externe Maharavo. Le connecteur indépendant est préparé et testé localement ; l'adaptateur réel et la recette de bout en bout restent bloqués sur ces informations.

Le code ne déduit aucune route distante à partir du nom du produit. `MAHARAVO_ENABLED=false` est la valeur par défaut. Activer cette variable ou fournir une clé ne suffit pas : un adaptateur conforme à une interface réellement inspectée est également nécessaire. Aucun adaptateur fictif n'est fourni dans le code d'exécution.

## Ce qui a été inspecté avant de coder

- Tous les fichiers du dépôt, y compris les fichiers ignorés hors secrets, caches et environnements.
- [maharavo.md](../docs/specifications/maharavo.md) et [Eric.md](../docs/specifications/Eric.md) : périmètres, responsabilités et contrats fonctionnels attendus, sans protocole HTTP externe.
- Les archives textuelles et les documents Word de spécifications/analyse.
- Les modules `app/maharavo_service.py`, `app/services/maharavo.py`, `app/integrations/maharavo/` et le transport Gemini.
- L'historique Git, notamment le commit `4c7ec4d3df508b2dbd7a9277b0671d786c33f152`, intitulé « Complete Maharavo AI modules ».
- `git ls-remote --heads origin` : une seule branche distante, `main`, à `b9fe2db47c0ae7bcdbed634fe8b62fb87e200586`, identique à la référence locale au moment de l'inspection.

Le commit IA ajoute des routes **du backend**, des tables et des fonctions. Sa recherche appelle `research_web()` de Gemini. Ce n'est pas la documentation d'un serveur Maharavo distinct. Le code recopiait aussi les citations Gemini dans `documents_ouverts`, sans justificatif de consultation.

La recherche publique complémentaire n'a pas fourni de documentation pertinente permettant d'établir une interface Maharavo pour ce projet. Ce constat porte sur les sources inspectées ; il ne prouve pas qu'un autre dépôt ou service privé n'existe pas.

## Comportement actuel du backend

`POST /api/maharavo/research` et son alias v1 conservent leurs contrôles RBAC, mais renvoient **503** avec un message explicite tant que l'interface réelle manque. Ils ne déclenchent pas Gemini, ne créent pas de faux job réussi et n'enregistrent pas de citations comme documents consultés.

Les endpoints `/maharavo/media-analysis` et `/maharavo/confidence` conservent leur fonction d'enregistrement d'observations autorisées ; ils n'annoncent aucune analyse distante. Le Copilot et les brouillons locaux/Gemini existants restent dans leurs modules explicites et ne constituent pas une connexion Maharavo.

Ce changement de comportement de `/maharavo/research` évite précisément de présenter une autre intégration comme une connexion réelle. Les données historiques sont conservées ; aucun historique de recherche n'est réécrit.

## Fichiers et responsabilités

| Fichier | Responsabilité |
|---|---|
| [config.py](app/integrations/maharavo/config.py) | Configuration par environnement, SecretStr, budgets, HTTPS, versions explicites |
| [contracts.py](app/integrations/maharavo/contracts.py) | Proposition de contrat normalisé côté backend pour les sept types de tâches |
| [binding.py](app/integrations/maharavo/binding.py) | Interface d'adaptateur à compléter seulement avec la documentation réelle |
| [transport.py](app/integrations/maharavo/transport.py) | HTTPX asynchrone, timeouts, limites, retries et journalisation technique |
| [limits.py](app/integrations/maharavo/limits.py) | Cadencement partagé des tentatives dans une instance de transport |
| [client.py](app/integrations/maharavo/client.py) | Garde de configuration, adaptation et validation avant retour d'un résultat |
| [provenance.py](app/integrations/maharavo/provenance.py) | Manifeste d'instantanés consultés par un lecteur de confiance du backend |
| [validation.py](app/integrations/maharavo/validation.py) | Corrélation des tâches, empreintes, extraits et références croisées |
| [errors.py](app/integrations/maharavo/errors.py) | Erreurs classifiées, sans contenu distant ni secret dans les messages |
| [research.py](app/integrations/maharavo/research.py) | Point d'injection fermé tant qu'aucun adaptateur réel n'est disponible |
| [test_maharavo_connector.py](app/tests/test_maharavo_connector.py) | Tests unitaires du transport et des contrats, uniquement en mémoire |

HTTPX est désormais une dépendance d'exécution dans `requirements.txt`, pas seulement une dépendance de test.

## Contrats proposés, à confronter au moteur réel

Les schémas sont identifiés par `fa-ai-marinana.proposal.v1`. **Ils ne sont pas présentés comme des schémas officiellement acceptés par Maharavo.** Un adaptateur documenté devra transformer le protocole réel vers ce contrat normalisé, sans inventer de champs de provenance ou de version absents de la réponse réelle.

Types de tâches :

- research → espace research ;
- document_analysis, claim_extraction, source_matching, contradiction_analysis, synthesis → espace analysis ;
- draft_preparation → espace drafts.

Le résultat exige `task_id`, `task_type`, `status`, `model_version`, `generated_at`, `space`, `sources`, `evidence`, `analysis`, `limitations` et `errors`. Les valeurs completed/partial/failed sont des états **terminaux** du contrat proposé ; le protocole réel de soumission/polling/webhook reste à documenter. Aucun faux polling n'est implémenté.

Les sous-modèles décrivent des affirmations proposées, des rapprochements, des contradictions, des analyses documentaires et un brouillon non validé. Les listes, textes et identifiants sont bornés. Les champs inconnus sont refusés, notamment les tentatives d'ajouter publication, validation ou validateur. Les espaces publics ne sont pas acceptés.

Le JSON Schema décrit les contraintes structurelles. Les contraintes entre références et les preuves de consultation nécessitent aussi `validation.py` ; elles ne sont pas garanties par le JSON Schema seul.

## Références et consultation effective

Le validateur n'accepte aucune URL simplement citée par le modèle comme preuve d'une consultation.

Il exige un manifeste émis côté backend par un lecteur de confiance après matérialisation des textes, avec identifiants de document et consultation, URL, date et SHA-256 du texte exact. Le manifeste est lié à une tâche et un périmètre rédaction/dataset ; il ne doit jamais être construit depuis la réponse du modèle ou un corps HTTP arbitraire.

Chaque référence doit :

1. exister dans le manifeste autorisé ;
2. conserver l'identifiant de consultation, l'URL, l'empreinte et la date enregistrés ;
3. fournir un extrait exact présent dans le texte consulté ;
4. être reliée aux affirmations, analyses ou brouillons par des identifiants existants et uniques.

Un rapprochement exige plusieurs documents effectivement présents. Une contradiction exige plusieurs extraits distincts, éventuellement d'un même document. Un horodatage de génération incohérent, une version inattendue, une référence hors manifeste, un extrait inventé ou une limite dépassée entraîne un refus du résultat complet ; aucun tronquage silencieux ne masque le défaut.

**Limite fondamentale :** l'instantané prouve la lecture du texte par le backend et permet de vérifier les citations. Il ne prouve pas, à lui seul, que le moteur distant a ouvert un document web ou réellement utilisé chaque passage. La trace de consultation réelle du moteur devra être inspectée et reliée à ce manifeste selon son protocole documenté. Tant que cette interface manque, aucune recherche distante n'est acceptée. La vérification des références ne prouve pas non plus la vérité sémantique d'une synthèse.

La nouvelle recherche web pourra découvrir des sources inconnues ; elles devront d'abord être matérialisées et enregistrées par un chemin de consultation de confiance avant acceptation. Le code ne télécharge jamais automatiquement une URL fournie par une réponse IA.

## Transport, quotas et erreurs

- Client `httpx.AsyncClient`, avec fermeture explicite via `aclose()`.
- Délais distincts de connexion, lecture, écriture et attente de connexion ; budget total incluant attente de quota et backoff.
- Maximum de deux tentatives simultanées par transport et trente appels/minute par défaut ; chaque retry consomme aussi un créneau.
- Reprises bornées avec backoff exponentiel et jitter sur erreurs transitoires.
- Un POST n'est **jamais** rejoué si le fournisseur ne documente pas une garantie d'idempotence et le nom de son en-tête. Aucun nom d'en-tête fournisseur n'est supposé.
- Un Retry-After compatible avec le budget est respecté ; un délai excessif provoque un refus plutôt qu'une reprise trop précoce.
- Aucun retry des refus d'authentification, erreurs de contrat, références invalides ou tailles excessives.
- Pas de redirections ; pas de proxy hérité implicitement de l'environnement ; URL HTTPS sans identifiants ni clé en paramètres.
- Vérification de la taille déclarée et de la taille réellement lue, y compris sans Content-Length. Les réponses compressées sont refusées pour éviter une décompression non bornée.
- JSON strict : clés dupliquées, constantes non finies, encodage invalide et contenus non JSON sont refusés.
- Les annulations asynchrones sont propagées.

Le limiteur est **par instance/processus**, pas un quota distribué global. Quand le fournisseur sera branché, l'application devra partager une instance par contexte de fournisseur et la fermer à l'arrêt ; une coordination Redis pourra être nécessaire si plusieurs processus partagent un quota fournisseur global.

## Clés, journaux et versions

La clé distincte `MAHARAVO_API_KEY` est un SecretStr. L'adaptateur réel devra déterminer son en-tête d'authentification à partir de la documentation réelle. La clé n'appartient ni aux prompts ni aux contrats de tâche. Rotation par la configuration et remplacement contrôlé du client ; aucun secret n'est affiché dans la documentation ou les fixtures.

Les journaux du connecteur contiennent uniquement identifiant/type de tâche, version du protocole/modèle, tentative, code HTTP, durée, compteurs et code d'erreur interne. Ils ne contiennent ni corps, ni documents privés, ni en-têtes d'authentification, ni réponse brute.

Les versions autorisées sont configurées explicitement. Le résultat doit correspondre à la version exacte demandée ; aucun fallback de modèle silencieux n'est accepté. La provenance de la version réelle devra être fournie par le protocole du moteur, pas reconstruite arbitrairement depuis une variable d'environnement.

## Publication, permissions et persistance

Le connecteur n'importe aucun modèle SQLAlchemy ni service de publication et n'exécute aucun ordre retourné par le modèle. Ses seuls espaces normalisés sont research, analysis et drafts. Le RBAC SERVICE_IA, l'immutabilité du type de compte IA et les contrôles de validation/publication du backend restent en place.

La persistance et l'orchestration réelles des résultats ne sont pas branchées tant que l'adaptateur et les preuves de consultation manquent. Un résultat unit-test validé ne constitue pas un brouillon publiable. Toute future écriture devra rester privée, appliquer le périmètre serveur et préserver le workflow de validation humaine existant.

Aucune migration n'est nécessaire pour le socle livré ; aucune base applicative existante n'a été modifiée.

## Éléments manquants pour terminer la connexion réelle

Il faut un chemin de code, un dépôt, un SDK ou une documentation technique contenant :

1. L'adresse du service, ses opérations et ses méthodes HTTP.
2. Le mécanisme d'authentification et les règles d'utilisation/rotation des clés.
3. Les exemples ou schémas de requêtes/réponses, erreurs et états asynchrones.
4. Les versions de protocole et de modèle réellement disponibles.
5. Les garanties d'idempotence, quotas et délais.
6. Les traces de documents réellement ouverts, empreintes et passages consultés.
7. Un environnement de recette autorisé, distinct de la production.

Ces informations permettront d'implémenter un `DocumentedAdapter`, de brancher la persistance/orchestration puis d'effectuer une recette réelle. Aucun endpoint distant n'est ajouté à titre d'hypothèse.

## Tests

```sh
python -B -m unittest discover -s app/tests -p test_maharavo_connector.py -v
python -B -m unittest discover -s app/tests -v
```

Le fichier de tests contient un `FixtureAdapter` et des domaines `.invalid` explicitement fictifs, avec `httpx.MockTransport`. Ils vérifient le code sans serveur distant et ne sont pas disponibles dans la configuration d'exécution. Aucun test ne prétend avoir appelé Maharavo réel.

Résultats de cette livraison : les 25 tests spécifiques au connecteur passent. La suite complète exécute 79 tests sur SQLite en mémoire : 72 réussites et 7 tests propres à PostgreSQL ignorés comme prévu. La syntaxe Python, les JSON Schema générés, `pip check` et `git diff --check` ont également été vérifiés. Cette validation ne constitue pas une recette de connexion réelle, ni un nouveau test de déploiement PostgreSQL.
