import sys, textwrap
sys.path.insert(0,'.analyse_deps')
import pymupdf as f
D=f.open()
BG='#37515E'; PANEL='#4B616E'; DARK='#1F363E'; GREEN='#00FFC5'; WHITE='#FFFFFF'; MUTED='#C4D0D4'; BORDER='#82949C'
def c(h): return tuple(int(h[i:i+2],16)/255 for i in (1,3,5))
def rect(x,y,w,h,fill,stroke=None,r=0):
 p.draw_rect(f.Rect(x,y,x+w,y+h),color=c(stroke) if stroke else None,fill=c(fill),width=.8, radius=r if r else None)
def txt(x,y,s,size=16,color=WHITE,bold=False,w=None):
 font='B' if bold else 'R'
 if w:
  # deterministic wrapping based on actual font metrics
  words=s.split(); lines=[]; line=''
  for word in words:
   trial=(line+' '+word).strip()
   if fonts[bold].text_length(trial,fontsize=size)>w and line: lines.append(line);line=word
   else: line=trial
  lines.append(line)
 else: lines=s.split('\n')
 for i,line in enumerate(lines): p.insert_text((x,y+size+i*size*1.4),line,fontname=font,fontsize=size,color=c(color))
 return len(lines)*size*1.4
fonts={False:f.Font(fontfile='C:/Windows/Fonts/segoeui.ttf'),True:f.Font(fontfile='C:/Windows/Fonts/segoeuib.ttf')}
def page(w,h,title,sub):
 global p
 p=D.new_page(width=w,height=h)
 p.insert_font(fontname='R',fontfile='C:/Windows/Fonts/segoeui.ttf');p.insert_font(fontname='B',fontfile='C:/Windows/Fonts/segoeuib.ttf')
 rect(0,0,w,h,WHITE)
 txt(32,18,title,20,DARK,True);txt(32,48,sub,12,BG)
 txt(32,h-28,'FAHAIMARINANA  /  CONCEPTION WEB  /  '+str(len(D)),10,BG)
def button(x,y,w,label,secondary=False):
 rect(x,y,w,46,PANEL if secondary else GREEN,GREEN if secondary else None,r=.2)
 kind={'Se déconnecter':'logout','Modifier le profil':'edit','PUBLIER':'send','Parler':'arrow','SE CONNECTER':'arrow'}.get(label)
 if kind:ui_icon(x+24,y+23,kind,WHITE if secondary else DARK,20)
 txt(x+(44 if kind else 16),y+11,label,16,WHITE if secondary else DARK,True)
def field(x,y,w,label,value='',h=50):
 txt(x,y,label,14,WHITE,True);rect(x,y+25,w,h,DARK,BORDER,r=.13);txt(x+14,y+38,value or 'Saisir…',16,MUTED)
def card(x,y,w,h):rect(x,y,w,h,PANEL,BORDER,r=.08)
def media(x,y,w,h,label='Photo / vidéo'):
 rect(x,y,w,h,DARK);rect(x+12,y+12,4,h-24,GREEN);txt(x+28,y+h/2-12,label,16,MUTED,True,w-40)
def score(x,y,value='72 %',label='Crédibilité moyenne'):
 rect(x,y,78,52,DARK);txt(x+9,y+12,value,21,GREEN,True);txt(x+94,y+6,label,16,WHITE,True)
def icon(cx,cy,kind,color,size=23):
 co=c(color); k=size/24
 def line(points): p.draw_polyline([f.Point(cx+(a-12)*k,cy+(b-12)*k) for a,b in points],color=co,width=1.8)
 if kind==0:
  line([(3,11),(12,3),(21,11),(21,21),(15,21),(15,14),(9,14),(9,21),(3,21),(3,11)])
 elif kind==1:
  line([(5,3),(19,3),(19,21),(5,21),(5,3)])
  for yy in [8,12,16]:line([(8,yy),(16,yy)])
 elif kind==2:
  p.draw_oval(f.Rect(cx-10*k,cy-10*k,cx+10*k,cy+8*k),color=co,width=1.8)
  line([(6,18),(5,23),(11,19)])
  for xx in [-4,0,4]:p.draw_circle(f.Point(cx+xx*k,cy-k),.9*k,color=co,fill=co)
 elif kind==3:
  line([(12,4),(12,20)]);line([(4,12),(20,12)])
 else:
  p.draw_circle(f.Point(cx,cy-6*k),4*k,color=co,width=1.8)
  p.draw_bezier(f.Point(cx-9*k,cy+10*k),f.Point(cx-9*k,cy-1*k),f.Point(cx+9*k,cy-1*k),f.Point(cx+9*k,cy+10*k),color=co,width=1.8)
def ui_icon(cx,cy,kind,color=GREEN,size=22):
 co=c(color); k=size/24
 def pt(a,b):return f.Point(cx+(a-12)*k,cy+(b-12)*k)
 def line(points):p.draw_polyline([pt(a,b) for a,b in points],color=co,width=1.7)
 def circle(a,b,r):p.draw_circle(pt(a,b),r*k,color=co,width=1.7)
 if kind=='history':
  circle(12,12,9);line([(12,6),(12,12),(17,15)]);line([(2,4),(2,9),(7,9)])
 elif kind=='bell':
  line([(4,17),(6,14),(6,9),(8,5),(12,3),(16,5),(18,9),(18,14),(20,17),(4,17)]);line([(10,21),(14,21)])
 elif kind=='globe':
  circle(12,12,10);line([(2,12),(22,12)]);p.draw_oval(f.Rect(pt(7,2),pt(17,22)),color=co,width=1.4)
 elif kind=='settings':
  circle(12,12,6);circle(12,12,2)
  for a in range(0,360,45):
   import math
   aa=math.radians(a);line([(12+7*math.cos(aa),12+7*math.sin(aa)),(12+10*math.cos(aa),12+10*math.sin(aa))])
 elif kind=='logout':
  line([(10,3),(3,3),(3,21),(10,21)]);line([(9,12),(22,12),(17,7)]);line([(22,12),(17,17)])
 elif kind=='edit':line([(4,16),(16,4),(20,8),(8,20),(3,21),(4,16)]);line([(13,7),(17,11)])
 elif kind=='mail':
  line([(2,5),(22,5),(22,19),(2,19),(2,5),(12,13),(22,5)])
 elif kind=='lock':
  line([(5,10),(19,10),(19,22),(5,22),(5,10)]);p.draw_oval(f.Rect(pt(8,1),pt(16,14)),color=co,width=1.6)
 elif kind=='image':
  line([(2,3),(22,3),(22,21),(2,21),(2,3)]);line([(3,18),(9,11),(14,16),(18,12),(22,17)]);circle(16,8,2)
 elif kind=='video':line([(2,5),(16,5),(16,19),(2,19),(2,5)]);line([(16,10),(23,6),(23,18),(16,14)])
 elif kind=='send':line([(3,3),(22,12),(3,21),(7,12),(3,3)]);line([(7,12),(22,12)])
 elif kind=='arrow':line([(3,12),(21,12),(15,6)]);line([(21,12),(15,18)])
 else:icon(cx,cy,1,color,size)

def nav(nx,ny,nw,active,compact=True):
 rect(nx,ny,nw,70,DARK,r=.48)
 labels=['Accueil','Actus','Discuter','Publier','Profil']
 for j,lab in enumerate(labels):
  cx=nx+(j+.5)*nw/5
  if j==2:
   p.draw_circle(f.Point(cx,ny+24),27,color=c(BG),fill=c(BG),width=4)
   p.draw_circle(f.Point(cx,ny+24),23,color=c(GREEN),fill=c(GREEN))
   icon(cx,ny+24,2,DARK,24)
  else:icon(cx,ny+25,j,GREEN if j==active else MUTED,23)
  fs=10 if nw<420 else 12
  tw=fonts[j==active].text_length(lab,fontsize=fs)
  txt(cx-tw/2,ny+47,lab,fs,GREEN if j==active or j==2 else MUTED,j==active)

def guide(title,sections):
 page(840,1000,title,'Référence de conception • 02 novembre 2026')
 y=104
 for head,body in sections:
  txt(40,y,head,21,DARK,True); y+=40
  y+=txt(40,y,body,16,BG,w=748)+28

# cover / scope
guide('FahAIMarinana — Référence web',[
 ('Une interface pour informer et vérifier','Dossier de conception pour le développement avec GitHub Copilot. Six pages conservées, chacune déclinée sur ordinateur, tablette et mobile. Les écrans qui suivent sont dessinés en vectoriel : zoomer pour examiner les textes et les composants.'),
 ('Fidélité au document fourni','Révision : fond blanc et navigation à icônes inspirée de la barre mobile originale. Source : « FahAIMarinana – Maquette.pdf », 8 pages. Conservation des contenus, de la marque FAH AI MARINANA, des familles de couleurs et des fonctions hors direct. Les titres d’actualité sont des exemples du PDF, sans validation éditoriale ni mise à jour.'),
 ('Périmètre retenu','Source 1 → Connexion ; 2 → Accueil ; 3 → Actualités ; 4 → Conversation et vérification IA ; 5 → Publication ; 6 → Profil. Source 7 et 8 supprimées : direct et article issu du reportage. Le bloc Reportage et son bouton caméra disparaissent de l’accueil.'),
 ('Propositions identifiées','La police Segoe UI, la grille desktop, les seuils responsive, les dialogues secondaires, les états de formulaire et les règles d’interaction sont des propositions lorsque le PDF ne les précise pas. Aucun site n’est publié ; ce dossier est le seul livrable.')])
guide('Parcours et navigation',[
 ('Navigation commune','Accueil / Actus / Vérifier / Publier / Profil. Sur ordinateur : barre supérieure arrondie avec icônes et libellés, reprenant la navigation mobile source. Sur tablette et mobile : barre supérieure sous la marque, avec la discussion mise en avant. Aucune navigation en bas. La page de connexion ne comporte pas de navigation applicative.'),
 ('Accès et destinations','Parler sur l’accueil ouvre Vérifier. Les filtres restent dans Actus. Une actualité ouvre un panneau de lecture (proposition), avec titre, source, média et texte disponibles. Retour ferme le panneau et restitue le filtre et la position de défilement.'),
 ('Fonctions secondaires conservées','Mot de passe oublié et inscription : dialogues dédiés proposés, sans inventer de nouvelle page principale. Profil : édition du nom/email, liste des publications, historique, notifications, choix de langue et paramètres dans des panneaux ou dialogues accessibles.'),
 ('Retrait complet du direct','Ne créer aucune route, aucun composant de diffusion, aucun lien Reportage, aucun bouton de démarrage ou d’arrêt de direct. L’import de photos et vidéos dans la conversation et dans la publication reste disponible.'),
 ('Lecture du dossier','Pages suivantes : guide visuel et règles, puis 18 planches — un seul écran par page, aux dimensions de référence indiquées. Les formes médias sont des emplacements fidèles aux maquettes : aucune photographie finale n’était fournie.')])
# palette
page(840,1000,'Palette extraite du document','Palette source conservée ; fond rosé remplacé par du blanc à la demande du client')
for i,(co,name,use) in enumerate([(BG,'Fond principal','Fond des pages et surfaces de marque'),(GREEN,'Accent turquoise','Action principale, sélection, progression'),(WHITE,'Blanc','Bandeau, texte clair, cartes Actus'),(DARK,'Bleu profond','Navigation, champs et médias'),(PANEL,'Surface ardoise','Cartes et panneaux')]):
 y=110+i*130;rect(40,y,110,92,co,BORDER);txt(175,y+5,name+'  '+co,21,DARK,True);txt(175,y+43,use,16,BG,w=610)
txt(40,790,'Les dégradés de la source comportent plusieurs nuances : #4B616E est une couleur dominante de carte. #C4D0D4 (texte secondaire) et #82949C (bordure) sont des ajouts proposés.',16,BG,w=750)
txt(40,890,'Utiliser du texte bleu profond sur le turquoise. Les scores restent accompagnés d’un libellé : la couleur seule ne porte pas le sens.',16,BG,w=750)
guide('Typographie, grille et composants',[
 ('Typographie proposée','Segoe UI Regular / Bold, repli system-ui, sans-serif. Marque en capitales et AI turquoise ; italique réservé au logotype si l’asset original devient disponible. Titres : 32/40 px desktop, 28/36 tablette, 26/34 mobile. Intertitres 22/30. Corps 16/24. Métadonnées 14/20. Labels 14/20 semi-gras.'),
 ('Grille et rythme','Contenu desktop : largeur max. 1200 px, marges 48 px, 12 colonnes, gouttières 24 px. Tablette : marges 32 px, 8 colonnes, gouttières 24 px. Mobile : marges 20 px, 4 colonnes, gouttières 16 px. Échelle d’espacement : 4, 8, 12, 16, 24, 32, 48, 64 px.'),
 ('Surfaces et actions','Cartes : padding 24 px desktop, 20 px mobile ; rayon cible 16 px. Boutons : hauteur 46–48 px, padding horizontal 16–24 px, rayon cible 12 px. Les planches emploient des contours sobres ; les rayons sont à harmoniser selon ces valeurs dans le code. Primaire turquoise, secondaire ardoise bordée de turquoise.'),
 ('Champs et icônes','Champs : label toujours visible, hauteur 50 px, texte 16 px, bordure ardoise claire. Focus : anneau turquoise 2 px avec décalage 2 px. Icônes proposées : traits 1,75–2 px, boîte 24 px ; maison, journal, bulle de discussion, plus, utilisateur. La barre reprend la capsule bleu profond du PDF source et son bouton central turquoise circulaire ; aucune initiale ne remplace une icône. Toutes les actions ont un libellé accessible. Cible tactile minimale 44 × 44 px.')])
guide('Responsive et accessibilité',[
 ('Seuils proposés','Mobile < 768 px ; tablette de 768 à 1199 px ; ordinateur ≥ 1200 px. Planches de référence : 390, 834 et 1440 px. À 320 px, garder une colonne et replier les options plutôt que réduire la taille du texte. Aucun défilement horizontal de page.'),
 ('Organisation des pages','Accueil : deux colonnes sur ordinateur, pile sur tablette/mobile. Actus : liste avec médias alignés à droite sur tous formats ; filtres sur une rangée défilante si nécessaire. Publication : formulaire et média côte à côte sur ordinateur, sections empilées ailleurs. Profil : identité + préférences en deux colonnes sur ordinateur.'),
 ('Conversation','Colonne de conversation centrée, largeur maximum 880 px. Zone de saisie ancrée en bas de la vue, sans barre de navigation inférieure. Pièces jointes sur une rangée défilante. Le clavier mobile réduit la zone de messages ; garder la saisie visible. Défilement automatique uniquement si l’utilisateur est déjà en bas.'),
 ('Navigation et zoom','Réserver la hauteur de la navigation supérieure dans le flux. Si elle devient fixe au défilement, décaler le contenu de sa hauteur ; respecter les zones de sécurité du téléphone. Aucun bouton ne doit masquer le dernier élément. À 200 % de zoom, laisser le contenu revenir à la ligne. En mobile paysage, autoriser le défilement vertical.'),
 ('Accessibilité','Propositions : ordre de tabulation logique, focus visible, formulaires associés aux labels, erreurs annoncées, nom accessible pour chaque icône et réduction des animations. Pas de carrousel automatique. Scores textuels et sources consultables au clavier.')])
guide('Interactions et états à développer',[
 ('Connexion','Email et mot de passe requis ; afficher/masquer le mot de passe. Erreur près du champ et message général si échec. Bouton en attente pendant l’envoi. Google, Apple et Facebook conservés : branchement aux fournisseurs requis. Mot de passe oublié : email + confirmation ; inscription : email et mot de passe (proposition minimale).'),
 ('Actualités et accueil','Filtres Tous, Vérifiés, Politique et Sport conservés. Sélection unique ; filtre actif turquoise. Les trois repères de dernière information changent l’article au clic, sans lecture automatique. Prévoir chargement, liste vide, erreur et réessayer.'),
 ('Vérifier','Saisir du texte, joindre photo/vidéo, prévisualiser puis retirer les pièces jointes. Lecture des vidéos importées. Envoyer déclenche l’analyse ; réponse avec pourcentage, libellé, résumé, explication et sources. Prévoir analyse en cours, échec et relance. Les scores sont fournis par le service, jamais simulés comme un résultat réel.'),
 ('Publier','Titre, catégorie, source, article et ajout photo/vidéo conservés. Catégories : Politique, Société, Sport, Économie. Proposition : titre, catégorie et texte requis ; source facultative, clairement signalée. Crédibilité « — % » tant que non calculée. Publier : confirmation de réussite ou erreur, sans perdre le brouillon.'),
 ('Profil','Modifier le profil ouvre un formulaire. Mes publications et historique ouvrent des listes ; compteurs issus des données. Notifications, langue et paramètres gardent leurs accès. Langues disponibles à confirmer ; ne proposer que celles réellement traduites. Se déconnecter termine la session et revient à Connexion.')])
# screens
names=['Connexion','Accueil','Actualités','Vérifier une information','Publier un article','Profil']
news=[('2424.mg','Jeux Olympiques de la Jeunesse 2026 : la compétition historique de Dakar lancée le 31 octobre'),('France24.com','Les relations avec nos partenaires africains ont changé, affirme Bruno Fuchs'),('TVM.mg','Coopération russo-malgache : la TVM lance « Russamada TV »'),('24h mada.mg','Moramanga : violentes chutes de grêle dans la commune'),('[Source]','[Titre de l’actualité sur deux ou trois lignes]'),('[Source]','[Titre de l’actualité sur deux ou trois lignes]')]
for idx,name in enumerate(names):
 for W,kind in [(1440,'Ordinateur'),(834,'Tablette'),(390,'Mobile')]:
  mob=W==390; desk=W==1440; margin=20 if mob else 32 if not desk else 48
  H=1160 if idx==2 else 1120 if idx==4 else 1000
  if mob and idx in [1,5]:H=1120
  if not desk: H+=96
  page(W+48,H+144,name+' • '+kind,str(W)+' px • un écran par planche • contenu et états de référence')
  # translate everything via page transformation not needed offset: screen starts y=88
  rect(24,88,W,H,BG)
  x=24+margin; y=88; cw=W-2*margin
  if idx!=0:
   rect(24,y,W,76,WHITE);txt(x,y+24,'FAH',18,BG,True);txt(x+42,y+20,'AI',24,GREEN,True);txt(x+76,y+24,'MARINANA',18,BG,True)
   if not mob and not desk: txt(24+W-125,y+28,'• En ligne',14,BG)
   if desk:
    nav(24+W-680,y+3,640,[0,0,1,2,3,4][idx],False)
   else:
    nav(24+12,y+84,W-24,[0,0,1,2,3,4][idx])
   y+=104 if desk else 176
   txt(x,y,name,28 if not mob else 26,WHITE,True);y+=60
  if idx==0:
   fw=min(440,cw);fx=24+(W-fw)/2
   txt(fx,y+65,'FAH AI MARINANA',28,GREEN,True,w=fw);txt(fx,y+125,'Connectez-vous à votre espace',21,WHITE,True,w=fw)
   field(fx,y+195,fw,'Adresse email','adresse@email.mg');field(fx,y+300,fw,'Mot de passe','••••••••     Afficher');txt(fx,y+390,'Mot de passe oublié ?',15,GREEN,True)
   button(fx,y+447,fw,'SE CONNECTER');txt(fx,y+526,'ou se connecter avec',15,MUTED)
   for j,lab in enumerate(['Google','Apple','Facebook']):button(fx+j*(fw+12)/3,y+568,(fw-24)/3,lab,True)
   txt(fx,y+700,'Vous n’avez pas de compte ?',16,WHITE,w=fw);txt(fx,y+735,'Inscrivez-vous ici',16,GREEN,True)
  elif idx==1:
   col=(cw-24)/2 if desk else cw
   card(x,y,col,320);txt(x+24,y+22,'Dernière information',21,WHITE,True);media(x+24,y+70,col-48,140,'[Titre de l’information]');score(x+24,y+232,'85 %','Crédibilité');txt(x+24,y+294,'[Source]                         1 / 3',14,MUTED)
   xx=x+col+24 if desk else x; yy=y if desk else y+344
   card(xx,yy,col,320);txt(xx+24,yy+26,'Discuter et vérifier',24,WHITE,True,w=col-48);txt(xx+24,yy+100,'Envoyez un texte, une photo ou une vidéo à FahAIMarinana.',18,WHITE,w=col-48);button(xx+24,yy+235,col-48,'Parler')
  elif idx==2:
   labs=['Tous','Vérifiés','Politique','Sport']; xx=x
   for lab in labs:
    ww=72 if mob else 110;rect(xx,y,ww,40,GREEN if lab=='Tous' else PANEL,BORDER);txt(xx+10,y+10,lab,13,DARK if lab=='Tous' else WHITE,True);xx+=ww+8
   y+=64
   for so,title in news:
    hh=130 if mob else 120
    rect(x,y,cw,hh-8,WHITE);mw=76 if mob else 164
    txt(x+16,y+12,so+'  [heure]',13,BG,True,w=cw-mw-44);txt(x+16,y+40,title,14 if mob else 18,BG,True,w=cw-mw-50);media(x+cw-mw-16,y+20,mw,76,'Visuel' if mob else 'Média');y+=hh
  elif idx==3:
   ww=min(cw,880);xx=24+(W-ww)/2
   card(xx,y,ww,100);txt(xx+20,y+16,'AI • Bonjour ! Envoyez-moi un texte, une photo ou une vidéo : je vérifie l’information.',16,WHITE,w=ww-40)
   media(xx+ww/2,y+120,ww/2,100,'Vidéo  •  0:24');rect(xx+20,y+238,ww-20,60,GREEN);txt(xx+36,y+255,'[Message de l’utilisateur]',16,DARK,w=ww-52)
   card(xx,y+322,ww,245);score(xx+16,y+342);txt(xx+16,y+410,'[Résumé de la vérification]',16,WHITE,True,w=ww-32);txt(xx+16,y+456,'[Explication de l’IA : ce qui est confirmé, ce qui reste à vérifier]',16,WHITE,w=ww-32);txt(xx+16,y+530,'[Source 1]    [Source 2]',14,GREEN,True)
   by=88+H-100;txt(xx,by-38,'Pièces jointes : photo ×   vidéo ×',14,MUTED,w=ww);rect(xx,by,ww,56,DARK);ui_icon(xx+24,by+28,'image',MUTED,22);ui_icon(xx+60,by+28,'video',MUTED,22);txt(xx+86,by+17,'Écrire un message…',14,MUTED);p.draw_circle(f.Point(xx+ww-28,by+28),20,color=c(GREEN),fill=c(GREEN));ui_icon(xx+ww-28,by+28,'send',DARK,20)
  elif idx==4:
   col=(cw-32)/2 if desk else cw
   field(x,y,col,'Titre','Le titre de votre article');y+=108
   txt(x,y,'Catégorie',14,WHITE,True);y+=30
   xx=x
   for j,lab in enumerate(['Politique','Société','Sport','Économie']):
    ww=(col-12)/2 if mob else (col-24)/4
    if mob and j==2:y+=46;xx=x
    rect(xx,y,ww,36,GREEN if j==0 else PANEL,BORDER);txt(xx+10,y+8,lab,14,DARK if j==0 else WHITE,True);xx+=ww+8
   y+=65
   mx=x+col+32 if desk else x;my=252 if desk else y
   card(mx,my,col,230);media(mx+16,my+16,col-32,120,'+ Ajouter un média');txt(mx+16,my+153,'Photo    /    Vidéo',16,GREEN,True);txt(mx+16,my+190,'— %  Crédibilité',16,WHITE)
   if not desk:y=my+255
   field(x,y,col,'Source (facultatif)','Adresse ou nom de la source');y+=108
   field(x,y,col,'Votre article','Écrivez ou collez votre article…',170);y+=220
   button(x,y,col,'PUBLIER')
  elif idx==5:
   col=(cw-24)/2 if desk else cw
   card(x,y,col,278)
   p.draw_circle(f.Point(x+49,y+49),29,color=c(GREEN),fill=c(GREEN))
   icon(x+49,y+49,4,DARK,30)
   txt(x+92,y+23,'[Nom de l’utilisateur]',18,WHITE,True,w=col-112)
   ui_icon(x+28,y+104,'mail',MUTED,18);txt(x+46,y+92,'[adresse@email.mg]',15,MUTED,w=col-66)
   button(x+20,y+132,col-40,'Modifier le profil',True)
   sw=(col-40)/3
   for j,(value,lab) in enumerate([('[0]','Publications'),('[0]','Vérifications'),('[0] %','Crédibilité')]):
    sx=x+20+j*sw
    txt(sx+4,y+201,value,22,GREEN,True);txt(sx+4,y+239,lab,12,WHITE)
    if j:p.draw_line(f.Point(sx-7,y+202),f.Point(sx-7,y+256),color=c(BORDER),width=.6)
   xx=x+col+24 if desk else x; yy=y if desk else y+302
   for lab,kind in [('Mes publications','document'),('Historique des vérifications','history'),('Notifications','bell'),('Langue : Français','globe'),('Paramètres','settings')]:
    card(xx,yy,col,62);ui_icon(xx+27,yy+31,kind)
    txt(xx+50,yy+20,lab,14 if mob else 16,WHITE,True,w=col-83)
    p.draw_polyline([f.Point(xx+col-25,yy+26),f.Point(xx+col-20,yy+31),f.Point(xx+col-25,yy+36)],color=c(MUTED),width=1.6)
    yy+=72
   button(xx,yy+12,col,'Se déconnecter',True)

guide('Architecture de référence pour Copilot',[
 ('Routes proposées','/connexion, /accueil, /actualites, /verifier, /publier et /profil. Protéger les routes selon la session réelle. Aucun chemin /live ou /reportage. Les liens secondaires peuvent être gérés par des dialogues ou panneaux ; conserver leur état et permettre leur fermeture avec Échap.'),
 ('Composants réutilisables','AppShell, Brand, DesktopNav, CompactTopNav, PageTitle, Button, TextField, SelectableChip, Card, MediaPreview, CredibilityBadge, SourceLink, NewsItem, ChatMessage, AttachmentList, Composer, ProfileStats, SettingsRow et Dialog. Même couleur, taille, focus et espacement pour chaque occurrence.'),
 ('Organisation des sections','Accueil : LatestInformation + VerificationCTA. Actus : CategoryFilters + NewsList + ArticlePanel. Vérifier : MessageList + AnalysisResult + Composer. Publier : ArticleFields + CategoryPicker + MediaUploader + PublishAction. Profil : IdentityCard + Stats + AccountActions.'),
 ('Contrats de données proposés','Article : id, titre, source, date, catégorie, média, texte, score. Vérification : id, entrées, statut, résumé, explication, score, sources. Profil : nom, email, publications, vérifications, crédibilité. Ne pas définir de formule de crédibilité arbitraire dans l’interface.'),
 ('Livraison et vérifications','Vérifier les six routes à 390, 834 et 1440 px, puis à 320 px et avec zoom 200 %. Contrôler navigation clavier, états vides, envoi en cours, erreurs et retour arrière. Brancher authentification, stockage, analyse et publication à de vrais services avant usage.')])
guide('Points à confirmer et critères de fidélité',[
 ('Propositions à valider au développement','La source ne définit pas les écrans d’inscription, de récupération, d’édition du profil ni les listes secondaires. Les dialogues et panneaux décrits dans ce dossier préservent ces accès sans ajouter de parcours majeur. Les champs exacts, les langues et les règles de validation métier restent à confirmer.'),
 ('Médias et identité','Les zones de média reproduisent les emplacements des maquettes. Remplacer leurs libellés par les contenus disponibles, avec texte alternatif. Aucun logo vectoriel séparé n’était fourni : la marque est recomposée en texte et devra être remplacée par l’asset officiel s’il existe.'),
 ('États de crédibilité','85 %, 72 % et [0] % reprennent les exemples du document. « — % » indique une analyse absente. Ne pas déduire de seuils de confiance à partir de ces exemples ; demander au service d’analyse le score et son libellé.'),
 ('Critères d’acceptation','Six pages principales présentes, trois tailles chacune ; palette de référence respectée ; contenus et accès hors direct conservés ; aucun point d’entrée vers le live ; textes sélectionnables et lisibles ; navigation supérieure sans recouvrement du contenu ; formulaires et médias utilisables au clavier.'),
 ('Nature du livrable','Ce PDF est une référence de conception et d’implémentation. Les planches représentent un état par page ; les autres états sont spécifiés dans le guide. Aucun site, hébergement ou service en ligne n’a été créé.')])
guide('Finitions — icônes et hiérarchie',[
 ('Profil : repères visuels utiles','Chaque ligne associe une icône turquoise de 22 px, un libellé et un chevron : document pour les publications, horloge pour l’historique, cloche pour les notifications, globe pour la langue et roue pour les paramètres. L’avatar rond et les trois compteurs séparés clarifient l’identité et l’activité.'),
 ('Actions cohérentes','Modifier le profil : crayon. Déconnexion : sortie. Publier : envoi. Connexion et Parler : flèche. Une icône accompagne le texte ; elle ne le remplace pas. Les actions sociales conservent leur nom : utiliser les marques officielles lors du développement.'),
 ('Conversation','Les commandes photo et vidéo utilisent des icônes distinctes ; le bouton Envoyer est circulaire et turquoise. Les boutons sans libellé visible doivent exposer un nom accessible et une infobulle sur ordinateur. La cible tactile reste au moins 44 px.'),
 ('Cohérence de finition','Fond blanc, cartes arrondies, champs arrondis, tracés homogènes et contours discrets. Les icônes servent à reconnaître les actions. Ne pas en ajouter aux titres ou aux paragraphes sans utilité fonctionnelle. Conserver une seule famille de pictogrammes en production.')])
D.set_metadata({'title':'FahAIMarinana — Conception web responsive','author':'FahAIMarinana','subject':'Maquettes et spécifications pour GitHub Copilot'})
D.set_toc([[1,'Périmètre et fidélité',1],[1,'Navigation',2],[1,'Palette',3],[1,'Guide visuel',4],[1,'Responsive',5],[1,'Interactions',6]]+[[1,n+' — 3 formats',7+i*3] for i,n in enumerate(names)]+[[1,'Architecture',25],[1,'Points à confirmer',26]])
D.save('C:/FahAImarinana/FahAIMarinana-Conception-Web-Responsive-v4.pdf',garbage=4,deflate=True)
print('PDF',len(D),'pages')

