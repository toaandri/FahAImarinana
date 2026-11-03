import fs from 'node:fs/promises';
import {FileBlob,PresentationFile} from 'file:///C:/Users/Pricio/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const root='C:/FahAImarinana';
const p=await PresentationFile.importPptx(await FileBlob.load('C:/Users/Pricio/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-operating-review/assets/reference.pptx'));
const cover=p.slides.items[0], demo=p.slides.items[7];
p.slides.keep([0,7]);
function text(s,t,x,y,w,h,size=24,color='#000000',align='left'){const sh=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});sh.text=t;sh.text.style={fontFamily:'Helvetica Neue',fontSize:size,color,alignment:align};sh.text.insets=0;return sh;}
const title=cover.shapes.items.find(s=>s.toSnapshot().name==='Title 3');
for(const sh of [...cover.shapes.items]){if(sh.id!==title.id && sh.toSnapshot().name!=='Straight Connector 7')sh.delete();}
title.text='FahAIMarinana';title.position={left:170,top:295,width:940,height:100};title.text.style={fontFamily:'Helvetica Neue',fontSize:76,color:'#EDF4FF',alignment:'center'};
text(cover,'Myths',440,70,400,65,40,'#EDF4FF','center');
text(cover,'Membre 1 : à compléter\nMembre 2 : à compléter\nMembre 3 : à compléter\nMembre 4 : à compléter',42,78,360,160,22,'#AFC4DA');
text(cover,'Assistance à la vérification journalistique',220,418,840,50,30,'#80C6FF','center');
text(cover,'FANILO 2026',440,620,400,40,22,'#AFC4DA','center');
const dt=demo.shapes.items.find(s=>s.toSnapshot().text==='Intro with four topics');
for(const sh of [...demo.shapes.items]){if(sh.id!==dt.id)sh.delete();}
dt.text='Les interfaces d’accueil';
async function pic(path,x,y,w,h){const b=await fs.readFile(root+'/.slides-build/'+path);return demo.images.add({blob:b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),contentType:'image/png',alt:path,fit:'cover',position:{left:x,top:y,width:w,height:h}});}
// Hardware mockup asset. Screens remain the actual, unmodified application captures.
const X=30,Y=150,W=1220,H=W*829/1897;
await pic('hardware.png',X,Y,W,H);
function device(path,x,y,w,h){return pic(path,X+x/1897*W,Y+y/1897*W,w/1897*W,h/1897*W);}
await device('web.png',64,160,791,486);
await device('tablet.png',918,122,422,595);
await device('mobile-app.png',1398,211,232,500);
await device('sms-screen.png',1687,286,160,186);
for(const [t,x,w] of [['Web',40,550],['Tablette',603,280],['Mobile',915,150],['SMS',1094,160]])text(demo,t,x,654,w,38,24,'#2468FF','center');
cover.speakerNotes.text=`Durée indicative : 1 minute 10.\nBonjour à toutes et à tous. Nous sommes le groupe Myths et nous vous présentons FahAIMarinana, notre projet pour le hackathon FANILO 2026. Notre équipe compte quatre membres, dont les noms seront complétés sur cette diapositive.\nFahAIMarinana répond à un besoin journalistique : disposer d’un espace pour consulter des informations, rassembler des éléments et préparer leur vérification. Quand un contenu circule, le premier enjeu est de comprendre ce qui est affirmé et ce qui reste à confirmer.\nNotre projet propose une assistance fondée sur l’intelligence artificielle. Le principe reste clair : l’IA accompagne le travail de recherche et de préparation, tandis que la validation éditoriale appartient à une personne. Une analyse automatique ne constitue donc pas, à elle seule, une preuve de fiabilité.\nNous avons également travaillé sur l’accès au service depuis plusieurs supports. La diapositive suivante montre nos interfaces web et mobile, puis le principe de l’accès à FahAIMarinana par SMS.`;
demo.speakerNotes.text=`Durée indicative : 1 minute 50.\nVoici les quatre présentations de notre interface d’accueil. Les écrans web, tablette et mobile sont des captures du projet exécuté localement. Le téléphone à touches illustre le parcours par SMS.\nÀ gauche, la version web sur ordinateur offre davantage d’espace. La navigation reste visible sur le côté. L’accueil présente les dernières informations et un accès à la discussion pour poser une question ou préparer une vérification. Les informations externes portent l’indication « non vérifié » : leur présence dans le flux ne signifie pas que nous les avons certifiées.\nAu centre, la tablette reprend le service web avec une disposition adaptée à la largeur de l’écran. L’objectif est de conserver une lecture confortable et un accès simple aux principales actions.\nLa vue suivante provient de l’application mobile, exécutée ici dans son aperçu web. Elle montre son propre accueil, avec les informations et les accès aux fonctions de discussion et de reportage. Cette capture illustre l’interface, elle ne remplace pas un test sur un téléphone physique.\nEnfin, à droite, le téléphone à touches permet de contacter l’IA de FahAIMarinana par SMS. La personne utilise la messagerie habituelle de son téléphone : elle rédige une question, envoie son message au service, puis reçoit une réponse par SMS. Il ne s’agit donc pas d’installer notre application sur ce téléphone. L’objectif est de proposer un accès simple aux personnes qui utilisent un appareil basique. Le visuel montre un exemple d’échange. Dans le projet actuel, l’envoi par opérateur reste simulé : la connexion à une passerelle SMS réelle constitue une étape à réaliser.\nÀ travers ces interfaces, nous souhaitons faciliter l’accès à l’information et accompagner un travail de vérification qui reste sous responsabilité humaine. Merci.\n\nSources : captures locales Frontends/Web sur localhost:8084, Frontend/Mobile sur localhost:8085/home, Le parcours SMS est une maquette illustrative, avec un exemple de dialogue et sans numéro de service inventé. Le connecteur SMS du dépôt reste simulé (Backend/app/integrations/sms/gateway.py). Les appareils et l’écran SMS sont des illustrations générées ; les autres écrans sont des captures réelles.`;
for(let i=0;i<2;i++){const b=await p.slides.items[i].export({format:'png',scale:1});await fs.writeFile(root+'/.slides-build/final-'+(i+1)+'.png',new Uint8Array(await b.arrayBuffer()));}
await (await PresentationFile.exportPptx(p)).save(root+'/.slides-build/candidate.pptx');
console.log('CREATED',p.slides.items.length);





