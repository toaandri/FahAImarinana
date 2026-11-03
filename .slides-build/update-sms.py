from pathlib import Path
p=Path('.slides-build/build.mjs')
s=p.read_text(encoding='utf-8-sig')
s=s.replace("'touche-screen.png'","'sms-screen.png'").replace("['À touches',1094,160]","['SMS',1094,160]")
s=s.replace('La diapositive suivante montre les interfaces telles qu’elles apparaissent dans les applications lancées localement.','La diapositive suivante montre nos interfaces web et mobile, puis le principe de l’accès à FahAIMarinana par SMS.')
s=s.replace('Les images affichées dans les appareils sont des captures du projet exécuté localement le 3 novembre 2026.','Les écrans web, tablette et mobile sont des captures du projet exécuté localement. Le téléphone à touches illustre le parcours par SMS.')
a=s.index('Enfin, à droite, la version Java')
b=s.index('\\nÀ travers ces interfaces',a)
s=s[:a]+'Enfin, à droite, le téléphone à touches permet de contacter l’IA de FahAIMarinana par SMS. La personne utilise la messagerie habituelle de son téléphone : elle rédige une question, envoie son message au service, puis reçoit une réponse par SMS. Il ne s’agit donc pas d’installer notre application sur ce téléphone. L’objectif est de proposer un accès simple aux personnes qui utilisent un appareil basique. Le visuel montre un exemple d’échange. Dans le projet actuel, l’envoi par opérateur reste simulé : la connexion à une passerelle SMS réelle constitue une étape à réaliser.'+s[b:]
s=s.replace('Touche/front/src recompilé et exécuté dans MicroEmulator 2.0.4. Les appareils du montage sont des illustrations générées ; les écrans proviennent des applications.','Le parcours SMS est une maquette illustrative, avec un exemple de dialogue et sans numéro de service inventé. Le connecteur SMS du dépôt reste simulé (Backend/app/integrations/sms/gateway.py). Les appareils et l’écran SMS sont des illustrations générées ; les autres écrans sont des captures réelles.')
p.write_text(s,encoding='utf-8')
f=Path('.slides-build/finalize.mjs');s=f.read_text(encoding='utf-8-sig').replace('outputs/Myths-FahAIMarinana.pptx','outputs/Myths-FahAIMarinana-SMS.pptx').replace('.slides-build/validation.json','.slides-build/validation-sms.json');f.write_text(s,encoding='utf-8')
