import requests,json,time
from pathlib import Path
names=[
(1884520000104,"AEP Polemidion"),(1884520000109,"Digenis Akritas Morphou"),(1884520000111,"Ermis Aradippou"),
(1884520000202,"Naxxar Lions"),(1884520000203,"Mgarr United"),(1884520000205,"Swieqi United"),(1884520000206,"Pietà Hotspurs"),
(1884520000207,"Victoria Hotspurs"),(1884520000208,"Vittoriosa Stars"),(1884520000209,"Melita FC"),
(1884520000210,"Santa Lucía"),(1884520000211,"Sirens FC"),(1884520000214,"Attard FC"),(1884520000215,"Żebbuġ Rangers"),
(1884520000304,"Hapoel Kfar Shalem"),(1884520000305,"F.C. Kiryat Yam"),(1884520000310,"Ironi Modi'in"),
(1884520000311,"Maccabi Kiryat Gat"),(1884520000313,"Maccabi Herzliya")]
s=requests.Session()
for id_,name in names:
 try:
  r=s.get('https://www.thesportsdb.com/api/v1/json/3/searchteams.php',params={'t':name},timeout=20)
  arr=r.json().get('teams') or []
  print(id_,name,'status',r.status_code,'RESULTS',[(x.get('strTeam'),x.get('strCountry'),str(x.get('strBadge'))[:120]) for x in arr[:4]],flush=True)
 except Exception as e:print(id_,name,'ERROR',str(e)[:140],flush=True)
