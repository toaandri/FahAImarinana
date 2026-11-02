# FA AI MARINANA — Analyse de la vidéo et conformité documentaire

2 novembre 2026 • Annexe au cahier des charges étendu

## Méthode et limites

La vidéo locale `Hackathon_Besoins.mp4` dure environ 4 min 01 s. L’intégralité de sa piste audio a été traitée localement avec le modèle français Vosk small-fr-0.22 ; des images ont été examinées à intervalles de 30 secondes, puis de 10 secondes sur la fin. Il s’agit d’une analyse de transcription automatique et d’images échantillonnées, pas d’une écoute humaine intégrale ni d’une transcription certifiée. Les minutages ci-dessous sont approximatifs et correspondent aux débuts de segments reconnus.

La transcription française est exploitable sur les besoins principaux. Le passage vers 00:58–01:30 comporte du malagasy et des mots insuffisamment reconnus : ne pas en extraire de citation exacte ni de détail technique supplémentaire. Les noms proposés pour la plateforme sont également mal reconnus ; aucun changement de nom n’est déduit. Les fichiers de transcription sont conservés pour vérification, avec un avertissement.

## Besoins retrouvés et traduction dans le cahier

| Passage approximatif | Observation tirée de la vidéo | Exigence correspondante |
|---|---|---|
| 00:11–00:50 | Accélération de la circulation des informations ; qualification, traitement et vérification professionnelle | F01, F02, F03 : signal, affirmation et dossier de preuves |
| 00:30–00:58 | Niveau de confiance fondé sur les éléments et sources vérifiés disponibles | F04 : solidité argumentée par affirmation, distincte de la validation |
| 00:58–01:30 | Passage mal reconnu ; mention identifiable des sources officielles vers 01:10 | F02 : contrôle d’identité et de compétence ; détails non attribués sans vérification complémentaire |
| 01:30–01:49 | Demande d’aide à l’authentification des photos et vidéos diffusées sur les réseaux | F05 : provenance, contexte, recherches inversées et limites |
| 01:49–02:05 | Veille des actualités de Madagascar, rubriques et régions | F01 : veille territorialisée et couverture visible |
| 02:05–02:27 | Demande de malagasy, français et anglais ; suggestion de nom mal reconnue | F10 : trois langues, originaux conservés et traductions relues |
| 02:28–02:43 | Accès dans les zones reculées, souhait sans internet ou par satellite | F11 : cache, synchronisation et dépendances réseau explicitement séparées |
| 02:43–03:23 | Orientation vers les départements, experts et dossiers à consulter ; annuaires à jour, public et privé | F06 : service compétent, documents et contacts ; contrôle des accès |
| 03:23–03:41 | Difficulté d’accès à des données statistiques à jour | F07 : indicateurs sourcés et datés ; le titre visible « Statistiques actualisées » confirme cette interprétation |
| 03:42–04:01 | Aide aux angles de reportage pour les thèmes et actualités | F08 : propositions d’angles, questions et interlocuteurs |

Les idées du porteur correspondent donc très largement aux besoins exprimés. La demande de vidéo est plus large que ce qu’une équipe peut réaliser complètement pendant le hackathon : le cahier propose une version minimale puis des évolutions.

## Ce qui relève des ajouts et choix de conception

La recherche approfondie structurée, les affirmations atomiques, le traitement explicite des contradictions, Google Lens/TinEye/InVID, l’analyse des contenus générés par IA, le workflow de publication, les corrections publiques, les contrôles de confidentialité et la structure des API sont issus des demandes du porteur, des trois cahiers précédents ou de recommandations de conception. Ne pas les présenter comme des citations exactes des intervenants.

L’idée d’un détecteur infaillible « IA ou pas IA » n’est pas retenue. Le contrôle des médias doit porter aussi sur les photos authentiques anciennes, les lieux, les dates et les légendes trompeuses. La demande d’accès satellite est un souhait d’accessibilité à traduire en partenariats matériels, sans en faire une capacité déjà acquise du logiciel.

## Documents précédents : consolidation et corrections

| Document | Apport conservé | Précision ajoutée |
|---|---|---|
| cahier des charges.txt | Veille, assistant, validation humaine, diffusion | Périmètre du hackathon, preuves par affirmation et limites réseau |
| front.txt | Rédaction, public, sources, chat et simulateur SMS | Écrans preuves/médias/annuaire/statistiques ; états non binaires et corrections |
| back.txt | Ingestion, stockage, séparation brouillons/public et rôles | Droits serveur, versions approuvées, origine commune des preuves, recherche bornée |
| Touche/front/front.txt | Interface Java ME et adaptation petits écrans | Document complémentaire : démo statique, sans API réelle ; ne prouve pas l’intégration |

Deux formulations anciennes sont corrigées : « rejeté » ne signifie pas « faux » ; « aucun résultat publié » ne signifie pas automatiquement « nos journalistes sont sur le coup ». La génération à la demande d’une réponse publique est remplacée par la restitution d’un résumé approuvé. Les anciennes promesses de veille exhaustive et d’accès « off-grid » par SMS sont qualifiées.

## Règlement FANILO et standard 42

Règlement téléchargé depuis le lien direct retrouvé à partir de l’annonce de l’Ambassade : https://homemade.mg/media/img/reglement_hackathon_fanilo.pdf

Le texte extrait confirme les équipes de quatre, la fenêtre du 2 novembre à 8 h au 3 novembre à 20 h, le jury du 4 novembre à l’IFM, le pitch de trois minutes maximum et la nécessité d’une application concrète répondant au besoin présenté en vidéo. Les articles 5 et 6 précisent les critères d’évaluation et l’identification des composants tiers et licences. La première page présente une extraction de texte dans un ordre de colonnes perturbé : les détails de mise en page ne sont pas utilisés comme preuves supplémentaires. Les passages essentiels sur calendrier, pitch et critères sont lisibles dans les pages suivantes.

Le PDF local `42_Antananarivo_Standard_Livraison_Hackathons.pdf`, version 1.1 de novembre 2026, a été extrait et lu. Il impose dépôt accessible, README et prototype démontrable, avec soumission par un référent. La grille générique qu’il présente reste adaptable : le cahier ne lui attribue pas une valeur de pondération officielle FANILO.

Le règlement FANILO précise une application concrète là où le standard générique autorise différents formats de démonstrateur. Retenir le niveau d’exigence spécifique FANILO. Les décisions opérationnelles sur place et avenants éventuels priment sur cette lecture documentaire.

## Recommandation de positionnement

Présenter FA AI MARINANA comme un espace de travail de vérification journalistique : qualification → recherche → preuves → conclusion humaine → publication transparente. Montrer un dossier complet plutôt qu’une longue liste de boutons déconnectés. L’annuaire, les statistiques et les angles prennent leur sens lorsqu’ils aident à résoudre ce même dossier. L’accès rural reste une composante démontrable par un article enregistré et un SMS clairement simulé si aucune passerelle réelle n’est connectée.
