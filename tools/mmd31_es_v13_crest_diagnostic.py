import requests,bs4
u='https://www.resultadosrfef.es/tercera-rfef/grupo-1/clasificacion'
r=requests.get(u,timeout=30,headers={'User-Agent':'MMD31 Personal football research'});print('HTTP',r.status_code)
s=bs4.BeautifulSoup(r.content,'html.parser')
for table in s.find_all('table'):
 if not all(x in table.get_text(' ',strip=True) for x in ['Pts','PJ','GF','GC']):continue
 for tr in table.select('tr')[1:4]:
  print('TR:',str(tr)[:1600])
  for img in tr.find_all('img'):print('IMAGE:',img.attrs)
 break
