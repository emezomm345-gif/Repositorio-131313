import sys; sys.path.insert(0,'/home/user/Repositorio-131313/tools')
from render import load, render
from PIL import Image
q,t,_=load(sys.argv[1])
views=[(0,5),(90,5),(180,5),(-90,5),(145,15)]
ims=[render(q,t,yaw=y,pitch=p,size=(400,560),center=(0,14,4),scale=17) for y,p in views]
z=[render(q,t,yaw=y,pitch=p,size=(500,420),center=(0,9,9),scale=30) for y,p in [(90,5),(150,20),(-120,-10)]]
S=Image.new('RGB',(2000,980),(190,205,230))
for i,im in enumerate(ims): S.paste(im,(400*i,0))
for i,im in enumerate(z): S.paste(im,(500*i,560))
S.save(sys.argv[2])
