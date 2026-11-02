import sys, math
sys.path.insert(0,'.analyse_deps')
import pymupdf as f
from collections import Counter
src=f.open(r'C:\Users\Pricio\Downloads\FahAIMarinana – Maquette.pdf')
for n in [0,1]:
 p=src[n].get_pixmap(); print(n,Counter(tuple(p.samples[i:i+3]) for i in range(0,len(p.samples),3)).most_common(3))
