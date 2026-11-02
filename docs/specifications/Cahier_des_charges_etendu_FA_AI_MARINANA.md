# FA AI MARINANA — Cahier des charges étendu

Version 2.0 • 2 novembre 2026 • Projet pour le hackathon FANILO, Madagascar

**Objet :** assister les journalistes dans la veille, la recherche approfondie, la vérification et la préparation éditoriale, puis diffuser uniquement les versions approuvées par la rédaction.

**Statut :** spécification proposée, à distinguer des fonctions déjà réalisées. Les mentions P0, P1 et P2 indiquent respectivement le minimum du hackathon, une première évolution et une ambition ultérieure. Ce document consolide les trois cahiers existants sans les remplacer sur disque.

## 1. Base documentaire et contexte confirmé

Documents locaux étudiés : `cahier des charges.txt`, `front.txt` et `back.txt`. Le document complémentaire `Touche/front/front.txt` décrit une interface Java ME de démonstration, avec données fictives et sans connexion réelle au serveur. Le dossier contient également un backend Python/FastAPI et une interface Java : leur présence ne prouve pas leur fonctionnement complet. La présente mission produit des spécifications, sans modifier ces applications.

L’annonce de l’Ambassade de France décrit un hackathon porté par l’IFM et son service de presse : équipes de quatre, application web ou mobile répondant à un besoin concret des journalistes et professionnels des médias ; travail à 42 Antananarivo, Andraharo, du 2 novembre à 8 h au 3 novembre à 20 h ; jury le 4 novembre de 8 h à 13 h à l’IFM Analakely [S1]. Ces horaires représentent 36 heures, bien que l’annonce utilise également la formule « 48 heures ». Le planning ci-dessous retient la fenêtre horaire explicite, sous réserve des consignes sur place. Ne pas confondre ce projet avec l’initiative homonyme fanilo.org consacrée au leadership féminin.

Les besoins ajoutés par le porteur du projet sont traités comme des exigences proposées, et non comme des obligations attribuées aux organisateurs. Le règlement téléchargé et lu [S2] confirme que le besoin présenté en vidéo constitue le point de départ ; une application concrète est attendue, au-delà d’une simple idée ou maquette (articles 2 et 4). Le pitch est limité à trois minutes. Les horaires et l’équipe de quatre sont confirmés. Voir aussi l’annexe documentaire.

## 2. Problème, promesse et bénéficiaires

Un journaliste peut recevoir une affirmation partagée sur les réseaux sociaux, une photo sans date et plusieurs articles qui recopient la même déclaration. Il doit retrouver l’origine, vérifier le contexte, contacter les interlocuteurs compétents et expliquer au public ce qui est établi ou encore incertain. Aujourd’hui, ces étapes peuvent être dispersées entre recherches, messages et documents.

**Promesse : « D’une affirmation à un dossier de vérification traçable, puis à une publication signée. »**

Le bénéficiaire prioritaire du hackathon est la rédaction. Le portail public, les résumés SMS et l’accès rural prolongent son travail. L’IA collecte et propose ; le journaliste choisit les sujets, mène les entretiens, vérifie, décide du traitement et autorise la publication. Le système doit pouvoir conclure « preuves insuffisantes ».

Rôles : journaliste (dossiers et brouillons), éditeur (validation/publication), administrateur (comptes et connecteurs), contributeur terrain (signalement sans droit de publier), lecteur public (versions publiées). Un administrateur technique n’obtient pas automatiquement le rôle éditorial. Pour une petite équipe, une personne peut cumuler des rôles explicites ; son action reste journalisée.

## 3. Pertinence et faisabilité des idées

| Idée | Appréciation | Périmètre réaliste |
|---|---|---|
| Qualification et traitement des informations | Centrale | P0 : affirmation exacte, thème, lieu, date, urgence et type de contenu |
| Recherche approfondie et recoupement | Centrale | P0 : recherche bornée, sources consultables et contradictions ; élargissement P1 |
| Confiance argumentée | Pertinente avec prudence | P0 : niveau qualitatif par affirmation ; aucun pourcentage de vérité |
| Sources primaires et officielles validées | Centrale, sans équivalence automatique entre officiel et vrai | P0 : identité, compétence, date et indépendance vérifiées |
| Veille nationale Madagascar | Pertinente, couverture progressive | P0 : petit corpus déclaré ; P1 : réseau régional de sources |
| Français, malagasy, anglais | Pertinente | P0 : interface et parcours témoin dans les trois langues ; validation linguistique humaine |
| Authentification des images et vidéos | Pertinente comme enquête de provenance | P0 : contrôle guidé et recherches inversées ; P1 : extraction automatisée et provenance |
| Détection certaine des contenus IA | Promesse à écarter | Aucun détecteur ne doit fournir seul un verdict de vérité |
| Accès rural et hors connexion | Pertinent | P0 : contenus enregistrés ; P1 : synchronisation et SMS sous couverture GSM |
| Satellite | Dépendance matérielle, pas une fonction logicielle autonome | P2 : utilisation d’une connexion fournie par un équipement/partenaire |
| Annuaire des services et personnes ressources | Très concret | P0 : fiches publiques vérifiées, documents et contacts privés séparés |
| Statistiques actualisées | Pertinentes si datées et documentées | P0 : quelques séries sourcées ; P1 : mises à jour planifiées |
| Inspiration et angles de reportage | Très pertinente | P0 : propositions reliées aux faits, questions et interlocuteurs |
| Choix des sujets, rédaction, publication | Aide possible, arbitrage humain | P0 : recommandation, brouillon puis validation explicite |

« Angles de reportage » désigne ici la manière journalistique d’aborder un sujet. « Statistiques actualisées » est l’interprétation retenue pour « statiques actualisés » ; le suivi de fraîcheur s’applique aussi aux autres données.

## 4. Parcours fonctionnel de référence

1. Le journaliste importe un lien, un texte, une image, une vidéo ou un document autorisé ; une source de veille peut également créer un signal.
2. Le système propose une ou plusieurs affirmations vérifiables. Le journaliste confirme leur formulation exacte, sans transformer une opinion en fait démontrable.
3. Il précise les personnes/organismes concernés, le lieu, la période et le sens des termes. « Demain » est converti selon la date du message original, sans supposer la date de consultation.
4. L’assistant cherche l’origine : auteur, document primaire, première occurrence retrouvée et chaîne de reprises. La première occurrence retrouvée n’est pas présentée comme la première publication absolue.
5. Il rassemble des éléments favorables et contradictoires, regroupe les copies d’une même origine et signale les documents manquants.
6. Le journaliste ouvre les preuves, sollicite les personnes ressources, vérifie le terrain et documente les réponses ou absences de réponse.
7. L’assistant propose une conclusion motivée, des limites, des angles et un brouillon. Les affirmations sans preuve sont marquées, non complétées par invention.
8. L’éditeur valide une version précise, ses traductions et son résumé public. Le serveur contrôle les droits et conserve la signature.
9. Le public reçoit la version publiée avec sources communicables, date, méthode, limites et corrections. Un changement substantiel déclenche une nouvelle validation.

La décision « ne pas traiter », « poursuivre l’enquête » ou « archiver » est distincte du verdict sur les faits. Rejeter un signal ne signifie pas qu’il est faux.

## 5. Exigences fonctionnelles détaillées

### F01 — Qualification et veille Madagascar — P0 puis P1

Chaque signal comporte texte original, langue, source et lien, auteur connu ou inconnu, date de publication et de collecte, territoire, thèmes, urgence et pièces jointes. Les filtres couvrent notamment gouvernance, société, économie, santé, environnement et services essentiels. Les lieux utilisent un référentiel versionné : région, district, commune lorsqu’ils sont identifiables ; ne pas deviner une localisation à partir de la langue.

P0 : importer manuellement et consulter un flux public autorisé ou un corpus de démonstration explicitement étiqueté. P1 : collecte planifiée de sources approuvées, déduplication, alertes et suivi de disponibilité. Ne pas annoncer « Madagascar entier » ou « 24/7 » sans mesure de couverture et service effectivement actif. L’écran expose les zones et langues peu couvertes.

La viralité indique une priorité d’examen, jamais la fiabilité. Un échec de collecte doit afficher « collecte interrompue » plutôt qu’un fil vide interprétable comme une absence d’événement. Aucun accès implicite aux groupes privés ou données non autorisées ; les accès API, licences et quotas sont des dépendances à vérifier.

### F02 — Dossier d’affirmation et sources — P0

Une affirmation est atomique : « Le service X est suspendu à Y le jour Z », plutôt qu’un article entier évalué globalement. Le dossier conserve la citation originale et sa traduction séparée, le contexte, les preuves, les questions ouvertes et le responsable.

Chaque preuve précise : titre, auteur/organisme, URL ou référence documentaire, extrait exact et page/minutage, date du fait, publication, consultation, caractère primaire/secondaire, caractère officiel, périmètre de compétence, origine commune éventuelle, accessibilité et niveau de confidentialité. Un fichier original autorisé est conservé avec empreinte, version et droits d’accès. Une empreinte garantit un contrôle d’intégrité du fichier conservé, pas la véracité de son contenu.

Une source primaire peut être un témoin direct, une donnée originale ou un document de première main ; elle n’est pas nécessairement institutionnelle. Une déclaration officielle prouve d’abord ce que l’organisme déclare. L’identité est contrôlée par le domaine, la page institutionnelle ou un canal de confirmation indépendant. Un badge ou un logo ne suffit pas. Une capture d’écran seule ne valide pas son auteur. Les sources intéressées et conflits d’intérêts sont signalés.

Deux médias reprenant la même dépêche comptent comme une origine documentaire. Le système recherche aussi les contradictions. Si un document ne peut être consulté, il reste une piste non vérifiée, sans citation inventée.

### F03 — Recherche approfondie — P0 borné, P1 étendu

Avant de chercher, l’assistant affiche le sujet, les questions, la période, les langues, les territoires et les limites. Paramètres proposés pour la démo : au plus 10 résultats candidats et 5 documents ouverts par recherche, arrêt à 90 secondes, limites configurables. Ces valeurs sont des objectifs de conception, pas des performances déjà mesurées.

Le moteur utilise un connecteur de recherche web réellement disponible et les archives autorisées. Une recherche vectorielle dans les seuls documents internes ne doit pas être présentée comme une enquête sur le web. Le journaliste peut compléter les résultats manuellement. Les recherches FR/MG/EN gardent les formulations originales et signalent une traduction incertaine.

Sortie : synthèse avec références cliquables par fait, chronologie, tableau des accords/désaccords, sources effectivement ouvertes, pistes non consultées, lacunes et prochaine action. Le système journalise requêtes, heures, documents et version de modèle. Un fournisseur indisponible entraîne un état explicite, sans prétendre que la recherche a eu lieu. Les textes web sont des données à analyser, jamais des instructions autorisant des actions.

### F04 — Niveau de confiance et conclusion — P0

Afficher séparément trois dimensions : identité de la source, solidité des preuves pour l’affirmation précise et état de validation éditoriale. Aucun score global d’un média ou d’une personne ne remplace l’examen de chaque élément.

| Niveau de solidité proposé | Conditions et message |
|---|---|
| Non évalué | Pièces non examinées ; aucune conclusion |
| Faible | Origine incertaine, pièce isolée ou contexte manquant |
| Moyen | Éléments partiels, recoupement incomplet ou contradiction non résolue |
| Élevé | Origine contrôlée, pièces pertinentes au lieu et à la période, recoupement indépendant lorsque possible, limites documentées |

Une contradiction majeure non résolue ou une pièce décisive non authentifiée interdit le niveau « élevé ». Pour un document primaire unique qui fait autorité sur un acte précis, l’absence de seconde source est expliquée ; ne pas simuler l’indépendance. Le niveau est une appréciation documentaire motivée, pas une probabilité statistique de vérité.

L’IA propose ; le journaliste peut modifier avec justification. Les conclusions éditoriales possibles sont : confirmé sur le périmètre examiné, infirmé, trompeur/hors contexte, partiellement confirmé, non vérifiable à ce stade. La conclusion et le niveau de confiance sont deux champs distincts. Les anciennes formules de score fondées sur le nombre de sources concordantes ou officielles doivent être remplacées avant usage réel.

### F05 — Vérification des photos, vidéos et audios — P0 guidé, P1 outillé

Objectif : retrouver la provenance et vérifier ce que le média permet réellement d’affirmer, notamment les contenus authentiques réutilisés hors contexte.

Procédure : conserver l’original autorisé ; relever URL, compte, légende, date et format ; examiner les métadonnées disponibles ; extraire des images clés pour une vidéo ; effectuer des recherches inversées ; comparer les occurrences et dates ; vérifier lieu et période ; demander si possible la confirmation du créateur ; consigner le résultat et ses limites.

Google Lens permet la recherche à partir d’une image [S3]. TinEye recherche des correspondances et versions [S4]. InVID propose notamment des outils de vérification et d’extraction d’images clés [S5]. Dans le MVP, fournir une procédure et des accès externes, puis enregistrer le résultat obtenu par le journaliste. Ne pas promettre une API gratuite ou une automatisation intégrée sans vérifier les conditions de chaque outil. Ne pas transmettre un média confidentiel à ces services sans autorisation adaptée.

La provenance C2PA, lorsqu’elle existe et peut être vérifiée, apporte des informations sur l’historique et l’intégrité associés au fichier ; elle ne démontre pas à elle seule la vérité de la scène [S6]. Son absence ne prouve pas une manipulation. Les métadonnées peuvent être absentes ou modifiées. Un indice de génération IA reste auxiliaire, avec méthode et limites ; il ne devient jamais « ce contenu est faux ». Distinguer : provenance inconnue, ancien contenu réutilisé, montage établi, déclaration de génération IA, soupçon non confirmé. Le verdict éditorial appartient à l’humain.

### F06 — Annuaire des services et personnes ressources — P0

Créer des fiches organisme/service/personne : domaine d’expertise, compétence géographique, institution, fonction, langue, canal professionnel public, heures de disponibilité si connues, origine de la fiche, date de dernière confirmation, date de révision et responsable. Proposer le service à contacter et la pièce à demander pour chaque affirmation, plutôt qu’inventer une autorité compétente.

Exemples de catégories à renseigner avec de vrais contacts vérifiés : statistique publique, météorologie, gestion des risques, opérateurs de services essentiels, collectivités, universités et associations spécialisées. Aucun nom ni numéro fictif ne doit ressembler à un contact réel vérifié.

Séparer l’annuaire public des contacts privés, des informateurs protégés et des notes d’enquête. Le lecteur ne voit jamais les coordonnées privées. Une recherche « publique » ne doit pas interroger ces pièces, même si elles existent dans le même système. Prévoir désactivation des contacts obsolètes et demande de rectification. L’accès aux documents privés nécessite une autorisation ; le projet ne donne aucun pouvoir d’accès administratif supplémentaire.

### F07 — Données et statistiques actualisées — P0 restreint, P1 automatisé

Chaque indicateur affiche valeur, unité, territoire, période mesurée, définition, méthode, producteur, document primaire, date de publication, date de collecte et version. Distinguer données provisoires/révisées, taux/effectifs et valeurs nominales/réelles selon le sujet. Comparer seulement des périodes et périmètres compatibles, ou expliquer la rupture méthodologique.

« Dernières données disponibles » ne signifie pas « mesure du jour ». Une série ancienne reste datée ; aucune IA ne complète les périodes absentes par un chiffre inventé. P0 : petit jeu documenté. P1 : connecteurs et calendrier de révision. Fraîcheur proposée : signal urgent revu après 24 h, annuaire après 90 jours, statistique selon le calendrier du producteur ; ces délais sont configurables et ne transforment pas automatiquement une information en fausse.

### F08 — Inspiration, choix éditorial et rédaction — P0

Pour chaque dossier, proposer trois angles différents avec intérêt public, public concerné, ancrage local, preuves disponibles, questions à poser, interlocuteurs, terrain à visiter et limites. L’outil aide à prioriser selon impact, urgence, nouveauté, état des preuves et faisabilité ; la rédaction décide. Les tendances ne suffisent pas à justifier un reportage.

Exemple fictif sur une interruption d’eau : angle service (« quels quartiers et quelles solutions ? »), angle terrain (« conséquences sur une école ou un centre de santé »), angle responsabilité (« annonces, moyens et délais documentés »). Les conséquences restent des questions à enquêter tant qu’elles ne sont pas établies.

Les brouillons peuvent comprendre titre, chapô, plan, résumé, questions d’entretien, encadré de méthode et version SMS. Aucune citation, interview, scène ou donnée n’est inventée. Les hypothèses et propos attribués sont identifiés ; une synthèse n’est pas présentée comme un reportage de terrain. Les traductions, titres et résumés ne doivent pas durcir le sens des preuves.

### F09 — Publication transparente et corrections — P0

Machine d’états : signal → qualifié → recherche en cours → dossier prêt pour relecture → validé → publié. États complémentaires : recherche bloquée, preuves insuffisantes, archivé, correction requise, retiré. Une conclusion « non vérifiable » peut donner lieu à un article expliquant les limites, après décision éditoriale.

Conditions serveur pour publier : utilisateur habilité, version attendue inchangée, auteur/validateur, affirmation et conclusion, preuves ou motif explicite d’insuffisance, résumé relu, classification des pièces et absence de coordonnées privées dans la sortie. L’approbation porte sur une version figée ; une modification ultérieure crée un nouveau brouillon. La publication est idempotente pour éviter les doublons.

La page publique affiche affirmation examinée, conclusion nuancée, signature, dates de publication et de mise à jour, méthode, sources communicables, limites, rôle de l’IA et lien de signalement d’erreur. Une source protégée peut être décrite sans révéler son identité ; sa protection est expliquée. Prévoir historique des rectifications et retrait motivé. La transparence ne signifie pas exposer tout le dossier privé.

### F10 — Multilingue — P0 témoin, P1 généralisé

Prévoir FR, MG et EN pour l’interface, la recherche et les publications. Stocker langue d’origine, original et traductions séparées. Afficher les versions réellement disponibles ; aucune traduction non relue n’hérite automatiquement de la validation de l’original. Les noms, montants, lieux et dates font l’objet d’un contrôle explicite. Les variantes linguistiques malagasy nécessitent des relecteurs compétents et une évaluation sur des exemples locaux. Si aucune version validée n’existe dans la langue demandée, proposer une langue disponible avec accord de lecture.

### F11 — Rural, hors connexion, SMS et satellite — P0 puis P1/P2

P0 : interface sobre, texte prioritaire, téléchargement explicite d’articles publics validés, date de dernière synchronisation et consultation hors ligne. Une page jamais enregistrée ne devient pas disponible magiquement sans réseau. La recherche en direct et le modèle distant restent indisponibles pendant une coupure ; l’interface le dit.

P1 : prise de notes locale, file d’attente et synchronisation au retour du réseau ; traiter les conflits de versions sans écraser une validation. Les documents confidentiels ne sont pas mis en cache par défaut. Prévoir suppression des données locales et déconnexion sûre sur appareil partagé.

Le SMS fonctionne sans forfait de données, mais nécessite couverture mobile, téléphone alimenté, passerelle/opérateur compatible, numéro et budget. Une messagerie internet ne remplace pas le SMS en absence de réseau de données. Le MVP peut montrer un simulateur marqué « simulation », sans prétendre envoyer de vrais SMS.

Le service public restitue un résumé exact déjà validé, avec identifiant, date et langue. Pas de génération libre à l’envoi. Si aucun article correspondant n’existe : « Aucune vérification publiée trouvée pour cette demande. » Ne pas affirmer que des journalistes travaillent sur le sujet si aucun dossier n’a été ouvert. Éviter les rapprochements approximatifs entre localités/dates et prévoir le coût des messages segmentés.

Le satellite apporte éventuellement une connexion via terminal, énergie, abonnement et cadre d’exploitation à vérifier avec un partenaire. L’application peut utiliser cette connexion comme toute autre liaison ; aucune couverture universelle ni accès satellite direct de tous les téléphones n’est promis. Relais communautaires et radios sont des pistes P2, après accords éditoriaux et opérationnels.

## 6. Interfaces attendues

| Écran | Contenu et actions |
|---|---|
| Connexion et compte | Authentification réelle si connecté, rôles, langue ; mode démo visible |
| Veille | Sources actives, dernier passage, territoires couverts, signaux, filtres ; créer un dossier |
| Dossier de vérification | Affirmation exacte, chronologie, matrice preuve/contre-preuve, niveau motivé, tâches et responsable |
| Assistant de recherche | Plan, recherche en cours/arrêtée, citations, limites, pistes non ouvertes |
| Analyse média | Original autorisé, métadonnées, images clés, recherches externes et journal des constats |
| Annuaire et documents | Service compétent, contacts vérifiés, dates, droits public/privé |
| Statistiques | Série, unité, période, méthode, source, fraîcheur et révisions |
| Atelier éditorial | Angles, questions, brouillon, références et traduction à relire |
| Relecture/publication | Version figée, réserves, pièces communicables, résumé et validation |
| Public | Articles publiés, méthode, limites, corrections, langues disponibles, lecture enregistrée |
| Administration | Comptes, connecteurs, budgets, journaux et incidents |

Sur ordinateur, les trois panneaux déjà décrits restent possibles ; sur mobile, les remplacer par des onglets ou étapes lisibles. Le statut doit être écrit, pas seulement codé par couleur. Conserver l’identité bleu pétrole/turquoise existante si souhaitée, avec contrastes lisibles, navigation clavier et textes adaptatifs.

## 7. Architecture cible et cohérence avec l’existant

Le backend FastAPI/PostgreSQL présent dans le dossier est la base à réutiliser sous réserve de vérification. Le cahier initial cite React/Next.js, mais l’interface locale utilise Java. Il faut choisir une seule interface principale pour la démonstration plutôt que promettre une migration et plusieurs clients complets.

Choix recommandé : conserver le client qui permet de montrer le parcours complet le plus vite ; prévoir une PWA pour le futur accès web/mobile et son cache hors ligne. Java ME reste un client de consultation simplifié ou une maquette si ses données sont statiques. Il n’est pas assimilé à une PWA et sa compatibilité réseau devra être testée sur les appareils visés. Le grand public sur téléphone basique peut être servi par SMS plutôt que par un assistant IA embarqué.

Architecture logique : sources autorisées → ingestion → dossiers et preuves privés → assistant de recherche → brouillon → validation serveur → versions publiques en lecture seule → portail/cache/SMS. Les tâches longues passent par un worker. Recherche sémantique facultative après mise en place des preuves et des droits ; elle ne constitue pas une source en elle-même.

Le compte de service IA ne peut pas publier. Les autorisations sont contrôlées dans l’API et la base, pas seulement dans l’interface ou le prompt. Les index privés et publics sont séparés ou cloisonnés avec des droits effectivement testés. La sortie SMS ne voit que les versions publiées encore actives.

## 8. Modèle de données et contrats d’API proposés

| Entité | Champs ou relations essentiels |
|---|---|
| Utilisateur | rédaction, rôles, état du compte, langue |
| Source | identité, type, URL, primaire/officielle, compétence, dernier contrôle, accès autorisé |
| Signal | source, contenu original, dates distinctes, langue, lieu, urgence |
| Dossier | journaliste responsable, thème, territoire, confidentialité, état |
| Affirmation | formulation atomique, contexte, période, proposition/conclusion humaine |
| Preuve | fichier/URL, extrait, page/minutage, origine, date, empreinte, visibilité |
| Lien affirmation-preuve | soutien/contradiction/contexte, justification, origine commune |
| Recherche | plan, requêtes, documents ouverts, modèle, durée, erreurs et coût |
| Analyse média | original, images clés, outils, observations, limites, opérateur |
| Contact/service | compétence, coordonnées publiques/privées, source, date de confirmation |
| Série statistique | définition, unité, périmètre, période, valeur, source et version |
| Brouillon/traduction | langue, texte, références, version source et état de relecture |
| Validation/publication | validateur, version, heure, résumé approuvé, état actif/retiré |
| Correction et audit | auteur, objet, action, versions, date et motif |
| Échange SMS | identifiant, langue, publication/version servie, livraison ; rétention limitée |

Routes cibles, à adapter aux conventions existantes : `POST /signals`, `POST /cases`, `POST /claims`, `POST /research-jobs`, `GET /research-jobs/{id}`, `POST /evidence`, `POST /media-checks`, `GET /contacts`, `GET /datasets`, `POST /drafts`, `POST /drafts/{id}/approve`, `POST /publications`, `POST /publications/{id}/corrections`, `GET /public/articles`, `POST /sms/inbound`.

Une publication référence un identifiant de version approuvée, jamais un texte libre envoyé par le navigateur au moment de publier. Les recherches ont des états en attente/en cours/terminée/partielle/échouée. Les pièces privées ne sont pas exposées par une URL prévisible. L’ajout de ces routes est une exigence cible, pas un constat de leur disponibilité actuelle.

## 9. Exigences de qualité et protection

Authentification, mots de passe hachés, secrets de configuration hors du code, droits par rôle et par rédaction, protection des téléversements, limites de taille et de débit, sauvegarde et restauration vérifiée. Les téléchargements web doivent empêcher l’accès aux adresses internes du serveur et limiter les types et tailles de fichiers. Le contenu collecté ne peut modifier les consignes du système ni déclencher une publication.

Les pièces sensibles ne sont pas envoyées par défaut à un fournisseur IA externe. Le choix d’un traitement local ou d’un fournisseur autorisé dépend des règles de la rédaction et des garanties contractuelles. Journaliser les actions sans recopier systématiquement les secrets ou numéros privés. Définir les durées de conservation et procédures d’effacement avant exploitation réelle. Les obligations juridiques et droits de réutilisation restent à faire valider selon les données et le déploiement retenus ; ce document ne prétend pas les certifier.

Objectifs à mesurer : pages textuelles légères (cible 200 Ko hors médias), première lecture utile en moins de 5 secondes sur une liaison de test annoncée à 400 kbit/s, liste API en moins de 2 secondes sur corpus témoin de 100 dossiers. Recherche documentaire bornée à 90 secondes avec résultat partiel explicite. Ces objectifs n’impliquent pas des résultats d’essais déjà obtenus. Les médias lourds ne se chargent qu’à la demande.

## 10. Périmètre du hackathon et feuille de route

**P0 obligatoire :** un parcours de bout en bout avec import de signal, affirmation précise, pièces consultables, recoupement explicite, confiance motivée, proposition d’angles, brouillon, validation humaine et page publique. Ajouter un annuaire réduit, quelques statistiques sourcées et un parcours FR/MG/EN relu. Si le temps manque, réduire le nombre de sources et de sujets, sans supprimer les contrôles de publication ni la traçabilité.

**P0 démontrable selon capacité :** une recherche web réelle et bornée, un contrôle média guidé avec résultat enregistré, consultation hors ligne d’un article public, simulateur SMS. Les fonctions simulées portent un bandeau ; une démonstration préchargée n’est pas qualifiée de collecte en direct.

**P1 après hackathon :** connecteurs réels supplémentaires, extraction vidéo automatisée, annuaire entretenu, statistiques planifiées, SMS réel, synchronisation, tests malagasy élargis et pilote dans plusieurs rédactions/régions.

**P2 :** couverture nationale instrumentée, partenaires ruraux/radios, intégration de provenances avancées, connexion satellite par partenaire et capacité locale de recherche. Chaque évolution dépend d’un budget, de droits d’accès et de mesures de qualité.

Hors périmètre : publication autonome, détecteur IA infaillible, accès aux dossiers privés sans permission, accès garanti sans aucun réseau, veille exhaustive de tous les réseaux sociaux, application complète sur tous les modèles de téléphones.

## 11. Planning proposé pour quatre personnes

Planning relatif depuis le lancement, à adapter au temps restant le 2 novembre ; il ne suppose pas que les travaux préparatoires sont autorisés par le règlement.

| Fenêtre | Résultat collectif |
|---|---|
| H0–H3 | Périmètre, scénario, corpus autorisé, contrats et rôles arrêtés |
| H3–H12 | Dossiers/preuves et droits ; écrans reliés à des données persistées |
| H12–H22 | Recherche, recoupement, rédaction, validation et publication intégrés |
| H22–H28 | Média guidé, langue témoin, annuaire, statistiques, lecture enregistrée et SMS simulé selon avancement |
| H28–H33 | Recette, erreurs réseau, confidentialité, corrections et répétition du scénario |
| H33–H36 | Gel, paquet de livraison, lancement sur autre machine et préparation jury |

Répartition : membre 1, recherche/IA et preuves ; membre 2, API/base/droits/publication ; membre 3, interface rédaction ; membre 4, consultation publique, langue, corpus et démonstration. L’intégration, la relecture et les essais restent collectifs. Ne pas reporter le premier parcours intégré aux dernières heures.

## 12. Recette et critères d’acceptation

| Test | Attendu vérifiable | Priorité |
|---|---|---|
| T01 Signal vers affirmation | Citation originale, lieu et période conservés ; correction humaine possible | P0 |
| T02 Copies de sources | Trois reprises d’une même origine ne deviennent pas trois confirmations indépendantes | P0 |
| T03 Source officielle | Identité, compétence et extrait sont documentés ; aucune confiance automatique | P0 |
| T04 Contradiction | Une contradiction majeure reste visible et bloque une confiance élevée non justifiée | P0 |
| T05 Citation | Chaque fait de synthèse renvoie à une pièce effectivement consultée, sinon porte une réserve | P0 |
| T06 Publication interdite | Compte IA ou utilisateur sans rôle éditorial : refus serveur et aucune sortie publique | P0 |
| T07 Version modifiée | Une approbation ancienne ne permet pas de publier un texte modifié | P0 |
| T08 Confidentialité | Contact/preuve privé absent des API publiques, recherche publique, cache et SMS | P0 |
| T09 Transparence | Signature, méthode, dates, limites et sources communicables visibles | P0 |
| T10 Correction | Nouvelle version signée ; historique et résumé public mis à jour | P0 |
| T11 SMS | Sujet inconnu : réponse neutre ; sujet connu : résumé approuvé exact et bonne version | P0 si montré |
| T12 Déconnexion | Article enregistré consultable, fraîcheur visible, recherche web signalée indisponible | P0 si montré |
| T13 Média ancien | Une image authentique ancienne ne valide pas automatiquement l’événement actuel | P0 si montré |
| T14 Langues | Noms, chiffres et dates cohérents sur trois versions témoins relues ; traduction non validée non publiée | P0 |
| T15 Donnée ancienne | Période mesurée distincte de date de collecte ; aucun chiffre manquant inventé | P0 |
| T16 Recherche en échec | État partiel/échec visible, aucune fausse affirmation de recherche terminée | P0 si recherche réelle |

Corpus de recette proposé : dix cas dont trois reprises d’une même source, une contradiction, une donnée périmée, un média hors contexte, une affirmation sans preuve et un document privé. Les cas sont fictifs ou réutilisés avec autorisation, sans fausse accusation contre une personne réelle. Faire examiner la pertinence journalistique par un professionnel si disponible. Rapporter le nombre de citations exactes, de fuites privées et de publications non autorisées ; les deux derniers doivent être nuls. Cette section définit les essais à réaliser : elle ne déclare pas l’application testée.

## 13. Scénario de démonstration proposé

Durée maximale réglementaire : trois minutes (article 4). Prévoir environ 30 secondes de problème, 110 secondes de démonstration et 40 secondes d’utilité, limites et suite.

Une rumeur fictive annonce une interruption d’eau dans une commune. Le journaliste confirme la phrase exacte et sa date. L’assistant retrouve une publication d’origine et deux reprises, qui sont regroupées. Un communiqué et une pièce contradictoire sont affichés. Une ancienne photo est identifiée comme non probante pour le lieu ou la date annoncés. Le dossier indique les points établis et manquants, puis propose un service à contacter et trois angles. Le journaliste corrige le brouillon ; l’éditeur publie la version signée. Le public lit la méthode et le résumé, puis la même version est consultée hors connexion ou dans le simulateur SMS. Les données simulées sont signalées dès l’ouverture.

## 14. Coûts, risques et décisions ouvertes

Postes à chiffrer : recherche web et accès plateformes, appels IA, hébergement/base/stockage, SMS entrants et sortants, maintenance des sources, relecture malagasy, sécurité, accès terrain ; matériel/énergie/abonnement satellite seulement en P2. Prévoir quotas par utilisateur, plafond quotidien et arrêt avec résultat partiel. Aucun tarif fournisseur non vérifié n’est figé dans ce cahier.

Risques principaux : périmètre trop large (réduire à un parcours), API inaccessible (import et corpus déclaré), sources qui se copient (origines regroupées), hallucinations (pièces citées et relecture), faible qualité en malagasy (relecture et mesure), fuite d’informateurs (droits et séparation), données vieillissantes (dates et alertes), confusion démo/production (bandeaux explicites).

Décisions à prendre avant mise en production : client principal et appareils cibles, fournisseurs et licences, rédaction responsable, critères d’habilitation des éditeurs, jeu de sources initial, politique de confidentialité/rétention, opérateur SMS et financement. Aucun de ces points ne bloque la définition du prototype ; chacun conditionne le déploiement réel correspondant.

## 15. Livrables attendus de l’équipe

Application démontrable, procédure de lancement reproductible, configuration d’exemple sans secrets, schéma et jeu de données autorisé, description des fonctions réelles/simulées/à venir, résultats de recette, scénario de démonstration et limites connues. Le présent cahier n’est pas un engagement de déploiement ni une preuve de conformité du code existant.

Le standard local de 42 (version 1.1, novembre 2026, pages 2–11) exige : dépôt GitHub accessible au jury, README complet, prototype démontrable, référent chargé de soumettre les liens avant l’échéance. Convention de nommage : `42hackathon-[evenement]-[equipe]`. La branche principale doit fonctionner ; chaque membre contribue avec son compte ; vérifier le lancement depuis un clone propre. Le README présente problème/solution, fonctionnalités réalisées, technologies, installation, démonstration, limites, équipe et outils IA utilisés. Aucun secret ni donnée personnelle réelle dans le dépôt ; utiliser un jeu fictif, anonymisé ou fourni par l’organisation. Le prototype peut fonctionner localement, mais le règlement spécifique FANILO exige une application concrète : ne pas s’arrêter à une maquette statique.

Le règlement FANILO, article 5, retient : pertinence du besoin, utilité et facilité d’usage, contribution à la résilience informationnelle, qualité technique/fonctionnalité, potentiel de développement et qualité du pitch. Il n’annonce pas de pondération. La grille générique sur 100 du standard 42 ne doit donc pas être présentée comme la grille officielle FANILO. L’article 6 demande d’identifier les composants tiers, leurs versions et licences ; il précise que les organisateurs n’acquièrent pas la propriété des créations, tout en prévoyant une autorisation de communication sur les projets. Le canal exact de remise reste celui communiqué sur place.

## 16. Sources et méthode documentaire

Sources web consultées le 2 novembre 2026. Les exigences fonctionnelles et choix techniques sont des recommandations du présent cahier, et non des citations du règlement.

- **[S1]** Ambassade de France à Madagascar, annonce du hackathon FANILO : https://fr.linkedin.com/posts/ambassade-de-france-a-madagascar_appel%C3%A0candidatures-fanilo-hackathon-activity-7518700879483527168-Ee_3
- **[S2]** Règlement indiqué dans l’annonce, téléchargé et lu : https://homemade.mg/media/img/reglement_hackathon_fanilo.pdf — copie locale dans les livrables. L’extraction de la première page présente un ordre de colonnes perturbé ; articles 4 à 6 lisibles dans l’extraction, exigences retenues ci-dessus.
- **[S3]** Google, recherche par image : https://support.google.com/websearch/answer/1325808?co=GENIE.Platform%3DAndroid&hl=en
- **[S4]** TinEye, fonctionnement et recherche inversée : https://help.tineye.com/article/233-how-does-tineye-work ; https://tineye.com/how
- **[S5]** InVID, outils de vérification : https://www.invid-project.eu/tools-and-services/invid-verification-plugin/
- **[S6]** C2PA, explication des garanties de provenance : https://c2pa.org/specifications/specifications/2.2/explainer/Explainer.html

Les observations de la vidéo et du standard PDF sont consignées dans `Analyse_video_et_conformite.md`, avec leur niveau de couverture. L’audio complet de la vidéo de 4 min 01 s a fait l’objet d’une transcription automatique locale, accompagnée d’un examen d’images échantillonnées. Les besoins de qualification, confiance, médias, veille, langues, accès rural, annuaire, statistiques et angles sont retrouvés ; le passage malagasy vers 00:58–01:30 reste insuffisamment reconnu. Les recherches approfondies structurées et outils nommés sont des ajouts du porteur et choix de conception, non des citations de la vidéo.
