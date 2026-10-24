#!/usr/bin/env python3
import requests,json
from bs4 import BeautifulSoup
urls=['https://www.foot24.be/nl/competities/2de-afdeling-voetb-vl-a-5','https://www.foot24.be/nl/competities/3de-afdeling-voetb-vl-b-5']
out=[]
for url in urls:
 try:
  r=requests.get(url,timeout=25,headers={'User-Agent':'Mozilla/5.0'})
  html=r.text;soup=BeautifulSoup(html,'html.parser')
  print('PAGE',r.status_code,len(html),url,flush=True)
  for a in soup.select('a[href*="/clubs/"]')[:25]:
   el=a.find('img')
   out.append({'text':a.get_text(' ',strip=True)[:110],'href':a.get('href'),'img':str(el)[:500] if el else None,'parent':str(a.parent)[:700]})
  for img in soup.select('img')[:30]:
   out.append({'img':str(img)[:350],'context':img.parent.get_text(' ',strip=True)[:100]})
 except Exception as e:out.append({'url':url,'error':str(e)})
open('docs/belgian-d4-d5-2026-27/v17/foot24_probe.json','w').write(json.dumps(out,ensure_ascii=False,indent=2))
