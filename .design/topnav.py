from pathlib import Path
p=Path('.design/build_design.py');s=p.read_text(encoding='utf-8')
s=s.replace('FahAIMarinana-Conception-Web-Responsive-v3.pdf','FahAIMarinana-Conception-Web-Responsive-v4.pdf')
s=s.replace('nav(24+12,y+H-78,W-24,[0,0,1,2,3,4][idx])','nav(24+12,y+84,W-24,[0,0,1,2,3,4][idx])')
s=s.replace('   y+=104\n','   y+=104 if desk else 176\n')
# grow compact pages to preserve comfortable bottom space
s=s.replace("  page(W+48,H+144,","  if not desk: H+=96\n  page(W+48,H+144,")
s=s.replace('by=88+H-(178 if not desk else 100)','by=88+H-100')
s=s.replace('Sur tablette et mobile : barre inférieure fixe, avec Vérifier mis en avant.','Sur tablette et mobile : barre supérieure sous la marque, avec la discussion mise en avant. Aucune navigation en bas.')
s=s.replace('au-dessus de la navigation compacte','sans barre de navigation inférieure')
s=s.replace('Réserver la hauteur de la navigation et safe-area-inset-bottom en bas du contenu.','Réserver la hauteur de la navigation supérieure dans le flux. Si elle devient fixe au défilement, décaler le contenu de sa hauteur ; respecter les zones de sécurité du téléphone.')
s=s.replace('BottomNav','CompactTopNav')
s=s.replace('navigation compacte sans recouvrement du contenu','navigation supérieure sans recouvrement du contenu')
p.write_text(s,encoding='utf-8')
