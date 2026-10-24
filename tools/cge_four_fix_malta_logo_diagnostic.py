import requests,bs4
from urllib.parse import urljoin
for url in ['https://bspfc.com/','https://www.birkirkarafc.com/']:
 try:
  r=requests.get(url,timeout=30,headers={'User-Agent':'Mozilla/5.0'});print('PAGE',r.status_code,r.url,len(r.content))
  soup=bs4.BeautifulSoup(r.content,'html.parser')
  for img in soup.select('img')[:100]:
   src=img.get('src') or img.get('data-src') or ''
   print('IMAGE',img.get('alt'),urljoin(r.url,src))
  for el in soup.select('link[rel~=icon]')[:10]:print('ICON',urljoin(r.url,el.get('href','')))
 except Exception as e:print('ERROR',url,str(e))
