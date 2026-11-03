# Héberger le sitemap public

Le fichier `Dockerfile.public` lance uniquement les pages des articles validés et
le sitemap. Il ne rend pas accessibles les routes de connexion, contributions ou
administration. Les contributions encore non vérifiées ne sont pas exposées.

Le service a besoin d'un PostgreSQL joignable depuis l'hébergeur, contenant les
publications et les vues créées par les migrations, et d'un compte PostgreSQL
distinct strictement en lecture sur `public_publications`. Une base accessible
uniquement sur le PC ne sera pas accessible depuis l'hébergeur. Le déploiement
ne copie ni ne synchronise automatiquement la base locale.

Configurer les variables de l'hébergeur :

- `ENVIRONMENT=production` et `AUTO_CREATE_TABLES=false` ;
- `PUBLIC_DATABASE_URL` : URL PostgreSQL du compte public en lecture seule ;
- `DATABASE_URL=postgresql+psycopg://unused@localhost/unused` : valeur non
  connectée utilisée pour satisfaire la configuration commune. Ne pas fournir
  les identifiants privés de la base au service public ;
- `JWT_SECRET` : valeur aléatoire d'au moins 32 octets, conservée secrète ;
- `PUBLIC_SITE_URL` : origine HTTPS publique attribuée à ce service ;
- `PUBLIC_NEWSROOM_ID` : identifiant de la rédaction publique.

Construire `Backend/Dockerfile.public` avec `Backend/` comme contexte. Le service
refuse de démarrer si le compte public possède des droits sur les tables privées.
Les migrations et la création des droits se font séparément, avec un compte
d'administration ; elles ne sont pas exécutées par ce conteneur public.

Après déploiement, vérifier `/api/v1/public/sitemap.xml`, puis soumettre cette
adresse dans Google Search Console. Le sitemap ne garantit pas l'indexation.
