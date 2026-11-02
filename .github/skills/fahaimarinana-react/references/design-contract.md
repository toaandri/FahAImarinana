# Contrat visuel V4

## Couleurs et texte

| Token | Valeur | Usage |
|---|---|---|
| background | #37515E | Fond principal de l’application |
| surface | #4B616E | Cartes |
| deep | #1F363E | Navigation, champs, médias |
| accent | #00FFC5 | Actions, sélection et icônes |
| white | #FFFFFF | Bandeau, cartes d’actualité et textes clairs |
| muted | #C4D0D4 | Texte secondaire sur fond sombre |
| border | #82949C | Bordures |

Ne plus utiliser #FBEFEF. Texte bleu profond sur fond blanc/turquoise. Police Segoe UI, system-ui, sans-serif. Corps 16/24 px ; métadonnées 14/20 ; titres mobile 26/34, tablette 28/36, desktop 32/40. Aucun texte globalement en italique.

Espacements : 4, 8, 12, 16, 24, 32, 48, 64 px. Cartes rayon 16, padding 20 mobile / 24 desktop ; boutons hauteur 46–48 et rayon 12 ; champs hauteur 50. Les rayons uniformisés du guide sont la cible de code ; ne pas reproduire les petites variations de tracé du PDF.

## Layout

Mobile < 768 ; tablette 768–1199 ; ordinateur >= 1200 px. Marges 20 / 32 / 48 px ; contenu max 1200 px. Ne pas diminuer la police pour tout faire entrer.

Bandeau blanc : marque FAH AI MARINANA, AI turquoise. Navigation supérieure sur tous les formats, intégrée au bandeau desktop et sous la marque sur tablette/mobile. Capsule profonde ; Accueil (maison), Actus (journal), Discuter (bulle), Publier (plus), Profil (utilisateur). Discuter est le bouton central circulaire turquoise, distinct de l’état actif de page. État actif turquoise avec libellé et aria-current pour la route concernée. Aucun menu inférieur. Le bandeau et la navigation restent dans le flux ; sticky n’est qu’une proposition si cela n’occulte rien.

Connexion sans navigation applicative. Ne pas afficher le titre de la planche, ses dimensions, le numéro de page ou le pied documentaire dans le site.

## Pages

- Connexion : marque, email, mot de passe et commande afficher/masquer, récupération, connexion, Google/Apple/Facebook, inscription. Colonne max 440 px.
- Accueil : Dernière information (titre, média, score 85 % d’exemple, source, 3 positions) et carte Discuter et vérifier avec action Parler. Deux colonnes desktop, pile ailleurs. Pas de Reportage.
- Actualités : filtres Tous, Vérifiés, Politique, Sport ; 6 entrées de la référence avec source, heure, titre et média à droite. Garder les titres du PDF comme exemples. Ne pas ajouter des images inventées comme contenu validé.
- Vérifier : accueil IA, média utilisateur, message utilisateur turquoise, résultat 72 % d’exemple, résumé, explication et sources. Colonne max 880 px. Prévisualisation et suppression des pièces jointes ; saisie avec icônes photo/vidéo et bouton Envoyer circulaire. Le compositeur peut être ancré en bas : ce n’est pas une barre de navigation. Le clavier ne doit pas le masquer.
- Publier : titre, catégories Politique/Société/Sport/Économie, import photo/vidéo, crédibilité « — % » avant analyse, source, texte, Publier. Deux colonnes desktop ; pile compacte ailleurs. Préserver les données et les états d’envoi.
- Profil : avatar rond, nom/email, crayon + Modifier le profil ; trois compteurs distincts Publications/Vérifications/Crédibilité. Puis document + Mes publications ; horloge + Historique des vérifications ; cloche + Notifications ; globe + Langue : Français ; roue + Paramètres. Chevron à droite de chaque ligne. Sortie + Se déconnecter en bouton bordé. Deux colonnes desktop, pile ailleurs. Garder les labels même avec les icônes.

## Interactions et limites

Les panneaux de lecture d’actualité, d’édition du profil, d’inscription, de récupération et des listes du profil sont des propositions du dossier. Préserver les parcours existants compatibles. Les exigences métier manquantes ne doivent pas être présentées comme validées.

Prévoir chargement, erreur avec relance, vide, succès et disabled. Champs avec label visible et message d’erreur associé. Icônes décoratives masquées aux lecteurs d’écran ; boutons sans texte avec nom accessible. Focus visible ; cibles 44 × 44 px ; pas d’animation automatique du carrousel. Ne jamais coder un score fixe comme réponse d’analyse réelle.
