from pathlib import Path
q=Path('.design/build_design.py');s=q.read_text(encoding='utf-8')
s=s.replace("FahAIMarinana-Conception-Web-Responsive-v2.pdf","FahAIMarinana-Conception-Web-Responsive-v3.pdf")
pos=s.index('def nav(')
helper='''def ui_icon(cx,cy,kind,color=GREEN,size=22):
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

'''
s=s[:pos]+helper+s[pos:]
s=s.replace("rect(x,y+25,w,h,DARK,BORDER);txt(x+14,y+38,value or 'Saisir…',16,MUTED)","rect(x,y+25,w,h,DARK,BORDER,r=.13);txt(x+14,y+38,value or 'Saisir…',16,MUTED)")
# button icons with consistent left alignment
old="rect(x,y,w,46,PANEL if secondary else GREEN,GREEN if secondary else None,r=.2);txt(x+16,y+11,label,16,WHITE if secondary else DARK,True)"
new="""rect(x,y,w,46,PANEL if secondary else GREEN,GREEN if secondary else None,r=.2)
 kind={'Se déconnecter':'logout','Modifier le profil':'edit','PUBLIER':'send','Parler':'arrow','SE CONNECTER':'arrow'}.get(label)
 if kind:ui_icon(x+24,y+23,kind,WHITE if secondary else DARK,20)
 txt(x+(44 if kind else 16),y+11,label,16,WHITE if secondary else DARK,True)"""
assert old in s;s=s.replace(old,new)
a=s.index('  elif idx==5:');b=s.index("\nguide('Architecture",a)
s=s[:a]+'''  elif idx==5:
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
''' +s[b:]
# compose attachments with real media symbols
old="txt(xx+12,by+17,'Photo  Vidéo',13,GREEN);txt(xx+112,by+17,'Message…',14,MUTED);txt(xx+ww-30,by+15,'→',20,GREEN,True)"
new="ui_icon(xx+24,by+28,'image',MUTED,22);ui_icon(xx+60,by+28,'video',MUTED,22);txt(xx+86,by+17,'Écrire un message…',14,MUTED);p.draw_circle(f.Point(xx+ww-28,by+28),20,color=c(GREEN),fill=c(GREEN));ui_icon(xx+ww-28,by+28,'send',DARK,20)"
assert old in s;s=s.replace(old,new)
# remove right status hidden behind desktop nav
s=s.replace('if not mob: txt(24+W-125', 'if not mob and not desk: txt(24+W-125')
# add spec page before metadata
pos=s.index('D.set_metadata')
s=s[:pos]+'''guide('Finitions — icônes et hiérarchie',[
 ('Profil : repères visuels utiles','Chaque ligne associe une icône turquoise de 22 px, un libellé et un chevron : document pour les publications, horloge pour l’historique, cloche pour les notifications, globe pour la langue et roue pour les paramètres. L’avatar rond et les trois compteurs séparés clarifient l’identité et l’activité.'),
 ('Actions cohérentes','Modifier le profil : crayon. Déconnexion : sortie. Publier : envoi. Connexion et Parler : flèche. Une icône accompagne le texte ; elle ne le remplace pas. Les actions sociales conservent leur nom : utiliser les marques officielles lors du développement.'),
 ('Conversation','Les commandes photo et vidéo utilisent des icônes distinctes ; le bouton Envoyer est circulaire et turquoise. Les boutons sans libellé visible doivent exposer un nom accessible et une infobulle sur ordinateur. La cible tactile reste au moins 44 px.'),
 ('Cohérence de finition','Fond blanc, cartes arrondies, champs arrondis, tracés homogènes et contours discrets. Les icônes servent à reconnaître les actions. Ne pas en ajouter aux titres ou aux paragraphes sans utilité fonctionnelle. Conserver une seule famille de pictogrammes en production.')])
''' +s[pos:]
q.write_text(s,encoding='utf-8')
