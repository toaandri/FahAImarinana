import sys
sys.path.insert(0,'.analyse_deps')
import pymupdf as f
from PIL import Image,ImageDraw
d=f.open(r'C:\Users\Pricio\Downloads\FahAIMarinana – Maquette.pdf')
a=Image.new('RGB',(1600,1732),'#dddddd')
for i,p in enumerate(d):
 pix=p.get_pixmap(matrix=f.Matrix(1.3,1.3)); im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples); a.paste(im,((i%4)*400,(i//4)*866+30)); ImageDraw.Draw(a).text(((i%4)*400+10,(i//4)*866+5),str(i+1),fill='black')
a.save('.design/source.png')
from collections import Counter
print(Counter(round(x,5) for p in d for dr in p.get_drawings() for x in [dr.get('fill')] if x).most_common(20) if False else Counter(str(dr.get('fill')) for p in d for dr in p.get_drawings()).most_common(16))
