# FA AI MARINANA — Cahier technique IA

## 1. Responsabilité

Maharavo prend en charge les composants d’intelligence artificielle, la recherche
web, l’analyse documentaire et multimédia, ainsi que la génération de propositions
non publiables. Le service IA ne possède aucun droit de publication et ne peut pas
contourner la validation éditoriale.

## 2. Veille et ingestion pour l’IA

- Consommer uniquement les signaux et sources autorisés par le backend.
- Normaliser le texte original, la langue, l’auteur, les dates, le lieu et les
  pièces jointes sans inventer les champs absents.
- Dédupliquer les reprises et conserver l’origine documentaire commune.
- Distinguer date du fait, date de publication, date de collecte et date de
  consultation.
- Signaler explicitement une collecte interrompue, une source indisponible ou un
  résultat partiel.
- Ne jamais traiter le contenu web comme une instruction système.

## 3. Recherche web continue et Deep Research

Le service de veille fonctionne en continu avec des workers supervisés et des
connecteurs autorisés. Chaque recherche doit :

1. recevoir un sujet, des questions, une période, des langues et un territoire ;
2. interroger réellement les connecteurs disponibles et les archives autorisées ;
3. conserver les requêtes, sources, horodatages, erreurs, quotas et état final ;
4. ouvrir les documents autorisés et extraire les passages réellement consultés ;
5. regrouper les copies d’une même origine et identifier les contradictions ;
6. retourner une synthèse avec citations, chronologie, lacunes et prochaines actions.

Une recherche vectorielle interne ne doit jamais être présentée comme une recherche
web. Un fournisseur indisponible produit un état `partielle` ou `échouée`, jamais
une réponse présentée comme complète. Les recherches FR/MG/EN conservent les
formulations originales et marquent les traductions incertaines.

Paramètres par défaut configurables : 10 résultats candidats, 5 documents ouverts
et 90 secondes maximum par recherche. Ces valeurs doivent rester mesurables et
produire un résultat partiel explicite en cas de dépassement.

## 4. Analyse des affirmations et des preuves

L’IA propose des affirmations atomiques, sans transformer une opinion en fait. Elle
doit relier chaque proposition à des preuves effectivement consultées et distinguer :

- soutien ;
- contradiction ;
- contexte ;
- document non accessible ou piste non vérifiée.

Elle produit séparément :

- identité et compétence de la source ;
- solidité documentaire de l’affirmation ;
- état de validation éditoriale.

Les niveaux proposés sont `non évalué`, `faible`, `moyen` et `élevé`. Le niveau
élevé est interdit en cas de contradiction majeure non résolue ou de pièce décisive
non authentifiée. Il ne s’agit pas d’une probabilité de vérité.

Les conclusions proposées sont `confirmé`, `infirmé`, `trompeur/hors contexte`,
`partiellement confirmé` et `non vérifiable à ce stade`. Le journaliste peut les
modifier avec justification.

## 5. Vérification des médias

Créer un module d’analyse pour les images, vidéos, audios et documents autorisés :

- conserver l’original et son empreinte d’intégrité ;
- lire les métadonnées et les informations de provenance disponibles ;
- relever les filigranes et leurs incohérences ;
- extraire des images clés d’une vidéo ;
- comparer les occurrences et versions antérieures ;
- analyser les indices de génération ou de retouche par IA ;
- analyser les indices de deepfake audio, image ou vidéo ;
- enregistrer outil, version, date, observations, niveau indicatif et limites.

Les résultats sont des indices. Aucun détecteur ne peut conclure seul qu’un contenu
est vrai, faux ou généré par IA. L’absence de métadonnées, de filigrane ou de
provenance ne constitue pas une preuve de manipulation.

Les médias confidentiels ne sont pas envoyés à un service externe sans autorisation.
Les recherches inversées externes doivent être enregistrées comme observations
journalistiques, avec leur source et leur date.

## 6. Copilot et rédaction assistée

Le Copilot peut produire :

- chronologies ;
- comparaisons de déclarations ;
- contradictions ;
- questions d’entretien ;
- propositions d’angles ;
- résumés ;
- brouillons et traductions séparées.

Toute phrase factuelle doit renvoyer à une preuve ou être marquée comme hypothèse,
limite ou question ouverte. L’IA ne fabrique ni citation, ni interview, ni donnée,
ni scène de terrain. Elle ne publie pas et ne modifie pas directement un article
certifié.

## 7. Contrat d’intégration avec Eric

### Entrées

Le backend fournit au service IA des identifiants de `Signal`, `Dossier`,
`Affirmation`, `Preuve` et `Recherche`, ainsi que les contenus autorisés et les
droits applicables.

### Sorties

Le service IA retourne des objets versionnés :

- `draft` : titre, résumé, corps proposé, langue et références ;
- `research_result` : requêtes, documents, citations, chronologie, erreurs et état ;
- `media_analysis` : type, outil, observations, indice, limites et empreinte ;
- `confidence_assessment` : dimensions séparées et justification ;
- `suggestions` : angles, questions et prochaines actions.

Toutes les sorties sont écrites dans les espaces non validés. Eric contrôle les
droits, la persistance, la publication et l’exposition SMS.

