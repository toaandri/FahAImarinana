from pathlib import Path
q=Path('.design/build_design.py');s=q.read_text(encoding='utf-8-sig')
s=s.replace("WHITE='#FBEFEF'","WHITE='#FFFFFF'")
pos=s.index('def guide(')
helper='''def icon(cx,cy,kind,color,size=23):
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

'''
s=s[:pos]+helper+s[pos:]
a=s.index('   if desk:\n    for j,lab');b=s.index('   y+=104',a)
s=s[:a]+'''   if desk:
    nav(24+W-680,y+3,640,[0,0,1,2,3,4][idx],False)
   else:
    nav(24+12,y+H-78,W-24,[0,0,1,2,3,4][idx])
'''+s[b:]
s=s.replace('Blanc rosé','Blanc').replace('blanc rosé','blanc')
s=s.replace('Valeurs relevées sur les aplats du PDF rasterisé, sans réinterprétation de teinte','Palette source conservée ; fond rosé remplacé par du blanc à la demande du client')
s=s.replace('Source : « FahAIMarinana – Maquette.pdf », 8 pages.','Révision : fond blanc et navigation à icônes inspirée de la barre mobile originale. Source : « FahAIMarinana – Maquette.pdf », 8 pages.')
s=s.replace('Sur ordinateur : barre supérieure.','Sur ordinateur : barre supérieure arrondie avec icônes et libellés, reprenant la navigation mobile source.')
s=s.replace('bouton de discussion central','bouton de discussion central')
s=s.replace('maison, journal, bulle, plus, utilisateur.','maison, journal, bulle de discussion, plus, utilisateur. La barre reprend la capsule bleu profond du PDF source et son bouton central turquoise circulaire ; aucune initiale ne remplace une icône.')
s=s.replace("FahAIMarinana-Conception-Web-Responsive.pdf","FahAIMarinana-Conception-Web-Responsive-v2.pdf")
q.write_text(s,encoding='utf-8')
