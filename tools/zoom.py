import sys
from render import load, render
from PIL import Image
q,t,_=load(sys.argv[1])
views=[(0,0,(0,23,0)),(60,5,(0,23,0)),(90,0,(0,23,0)),(150,5,(0,25,0))]
ims=[render(q,t,yaw=y,pitch=p,size=(420,520),center=c,scale=30) for y,p,c in views]
S=Image.new('RGB',(420*4,520))
for i,im in enumerate(ims): S.paste(im,(420*i,0))
S.save(sys.argv[2])
