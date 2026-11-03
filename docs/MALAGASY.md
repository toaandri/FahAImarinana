# Réponses IA en français et malagasy

Le profil propose Auto, Français et Malagasy. Le choix est conservé dans
`users.response_language` par la migration `0007_response_language`. Le lanceur
`Backend/scripts/run_local.py` applique les migrations au démarrage.

Le chatbot reprend cette préférence et permet de la modifier pour la question en
cours. Auto utilise des indices lexicaux français/malagasy ; une question courte,
ambiguë ou mélangée peut nécessiter de choisir explicitement la langue.

Les routes `/api/v1/copilot/research` et `/sessions/{id}/ask` acceptent le champ
optionnel `language` (`auto`, `fr`, `mg`). Sans ce champ, elles utilisent le profil.
OpenRouter est prioritaire, puis Gemini, puis les documents certifiés locaux.
Le repli local utilise des messages traduits ; les extraits des documents restent
dans leur langue d’origine et sont étiquetés comme tels.

## Traduction d’une réponse

Les boutons « Adika amin’ny teny malagasy » et « Traduire en français » appellent
`POST /api/v1/copilot/translate` avec `text` (12 000 caractères maximum) et
`target_language` (`fr` ou `mg`). L’original et les références restent disponibles
dans l’interface. Les URL du texte sont protégées par des marqueurs et rétablies
après traduction ; une traduction qui supprime ou ajoute un lien est rejetée.

Le serveur utilise successivement :

1. Google Cloud Translation si `GOOGLE_TRANSLATION_API_KEY` est configurée.
2. OpenRouter si `OPENROUTER_API_KEY` est configurée.
3. Gemini si `GEMINI_API_KEY` est configurée.

Sans fournisseur disponible, l’API renvoie `503` et l’interface conserve l’original.
Configurer une clé dédiée à Cloud Translation dans `Backend/.env`, jamais dans
le frontend. La clé Gemini n’active pas automatiquement Cloud Translation :
il faut un projet où cette API est activée, avec facturation et droits appropriés.
Voir la [documentation Google](https://docs.cloud.google.com/translate/docs/translate-text).

## Glossaire et qualité

`Backend/app/utils/journalism_glossary.json` contient un glossaire de départ
français/malagasy transmis aux deux modèles. Ces termes sont indicatifs et
doivent être relus par la rédaction malgachophone. Le glossaire enrichit aussi
les recherches locales par mots-clés ; ce n’est pas un moteur sémantique bilingue.

Le modèle est configurable par `OPENROUTER_MODEL`. Une réponse fluide n’est pas
une preuve d’exactitude ; les sorties et traductions restent des pré-analyses à
relire. Les tests techniques vérifient la transmission de la langue, les préférences,
les replis et la conservation des liens, sans certifier la qualité linguistique.
