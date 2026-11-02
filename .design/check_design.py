import sys
sys.path.insert(0,'.analyse_deps')
import pymupdf as f
from PIL import Image,ImageDraw
d=f.open('FahAIMarinana-Conception-Web-Responsive.pdf')
ids=[3,5,6,8,11,14,17,20,23]
a=Image.new('RGB',(1500,2100),'#ddd')
for j,i in enumerate(ids):
 p=d[i]; pix=p.get_pixmap(matrix=f.Matrix(min(480/p.rect.width,650/p.rect.height),min(480/p.rect.width,650/p.rect.height)));im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples);a.paste(im,((j%3)*500,(j//3)*700));ImageDraw.Draw(a).text(((j%3)*500,(j//3)*700+670),str(i+1),fill='black')
a.save('.design/check.png')
for i,p in enumerate(d):
 for b in p.get_text('dict')['blocks']:
  for l in b.get('lines',[]):
   for s in l['spans']:
    if s['bbox'][2]>p.rect.width or s['bbox'][3]>p.rect.height:print('overflow',i+1,s['text'])
print('pages',len(d),'bytes',__import__('os').path.getsize('FahAIMarinana-Conception-Web-Responsive.pdf'))
