import requests,bs4,urllib.parse
URLS={
'PORTONOVO':'https://www.portonovosd.es/Club/',
'ANDES':'https://andescf.com/ElClub/escudo.php',
'ERANDIO':'https://www.erandioclub.com/',
'ATL_SANTACRUZ':'https://atleticosantacruz.es/',
'LALIN':'https://www.lalin.gal/',
}
s=requests.Session();s.headers['User-Agent']='Mozilla/5.0 MMD31 academic crest attribution'
for name,url in URLS.items():
 print('===',name,url,flush=True)
 try:
  r=s.get(url,timeout=23);print('HTTP',r.status_code,'size',len(r.content),'end',r.url,flush=True)
  soup=bs4.BeautifulSoup(r.content,'html.parser')
  images=soup.select('img')
  for img in images[:100]:
   alt=img.get('alt','')
   title=img.get('title','')
   source=img.get('src','') or img.get('data-src','')
   if any(x in str(alt+' '+title+' '+source).lower() for x in ['escudo','logo','emblema','portonovo','andes','ande','erandio','santa','lalin','club','im_']):
    print('CANDIDATE',alt[:55],title[:55],urllib.parse.urljoin(r.url,source)[:180],flush=True)
  print('NUM IMAGES',len(images),flush=True)
 except Exception as e:print('ERROR',str(e),flush=True)
