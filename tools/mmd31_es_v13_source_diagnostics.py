import requests,bs4,urllib.parse
URLS={
'ATL_MARBELLA':'https://futbolme.com/resultados-directo/equipo/atletico-de-marbella-balompie/38387/calendario',
'CD_LAGUNA_MATCH':'https://futbolme.com/resultados-directo/partido/cd-laguna-ud-san-fernando/1356966',
'PORTONOVO':'https://www.portonovosd.es/Club/',
'ANDES':'https://andescf.com/ElClub/escudo.php',
'ERANDIO':'https://www.erandioclub.com/',
'ATL_SANTACRUZ':'https://atleticosantacruz.es/',
'LALIN':'https://futbolme.com/resultados-directo/equipo/cd-lalin/271/calendario/',
'PORTONOVO_SECOND':'https://www.lapreferente.com/E8090/portonovo-sd/datos-club.html',
'MONTIJO':'https://futbolme.com/resultados-directo/equipo/ud-montijo/2243/calendario',
'LALIN_B':'https://www.resultados-futbol.com/equipo/Cd-Lalin-Senior/2014',
'PORTONOVO_C':'https://futbolme.com/resultados-directo/equipo/portonovo-sd/540/clasificacion/',
}
s=requests.Session();s.headers['User-Agent']='Mozilla/5.0 MMD31 academic crest attribution'
for name,url in URLS.items():
 print('===',name,url,flush=True)
 try:
  r=s.get(url,timeout=23);print('HTTP',r.status_code,'size',len(r.content),'end',r.url,flush=True)
  soup=bs4.BeautifulSoup(r.content,'html.parser')
  images=soup.select('img')
  for img in images[:115]:
   alt=img.get('alt','')
   title=img.get('title','')
   source=img.get('src','') or img.get('data-src','')
   if name in ('ATL_MARBELLA','CD_LAGUNA_MATCH') or any(x in str(alt+' '+title+' '+source).lower() for x in ['escudo','logo','emblema','portonovo','andes','ande','erandio','santa','lalin','club','im_','badge','equipo','crest','montijo']):
    print('CANDIDATE',alt[:55],title[:55],urllib.parse.urljoin(r.url,source)[:180],flush=True)
  print('NUM IMAGES',len(images),flush=True)
 except Exception as e:print('ERROR',str(e),flush=True)
