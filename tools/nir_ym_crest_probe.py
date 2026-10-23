import json,requests,re,bs4
from pathlib import Path
from urllib.parse import urlparse
s=requests.Session();s.headers.update({"User-Agent":"Mozilla/5.0 (compatible; MMD31 crest research; +https://github.com/MMMMMMD31/mmd31-wavy-flags)"})
urls=[
"https://www.442teamwear.com/all-club-shops/st-patricks-ym-travel-mug-steel/",
"https://442teamwear.com/all-club-shops/st-patricks-ym-travel-mug-steel/",
"https://tamhi.org/sports-club/st-patricks-ym-fc/",
"https://www.tamhi.org/sports-club/st-patricks-ym-fc/",
"https://tamhi.org/wp-json/wp/v2/search?search=st%20patricks%20ym",
"https://tamhi.org/wp-json/wp/v2/sports_club?slug=st-patricks-ym-fc",
"https://www.thenafl.co.uk/data/clubs-dev.json",
"https://www.thenafl.co.uk/data/tables.json",
"https://www.footballgroundmap.com/team/st-patricks-ym",
"https://www.europlan-online.de/index.php?search=St+Patricks+YM&s=suche",
"https://www.google.com/search?tbm=isch&q=%22St+Patricks+YM%22+crest",
]
rows=[]
for url in urls:
 try:
  r=s.get(url,timeout=17);soup=bs4.BeautifulSoup(r.text,'html.parser')
  row={"url":url,"status":r.status_code,"length":len(r.content),"title":soup.title.get_text() if soup.title else "","final":r.url}
  if 'json' in r.headers.get('content-type',''):
   j=r.json()
   if isinstance(j,list):
    row["matching_clubs"]=[v for v in j if isinstance(v,dict) and ("st patrick" in str(v).lower() or "stpatrick" in str(v).lower())][:6]
   else:
    txt=json.dumps(j);row["mentions"]=txt.lower().count("st patrick");row["snips"]=[txt[max(0,m.start()-250):m.start()+450] for m in list(re.finditer(r"st patrick",txt,re.I))[:6]]
  else:
   row["images"]=[{"alt":i.get("alt",""),"src":i.get("src",""),"data-src":i.get("data-src",""),"class":str(i.get("class"))[:80]} for i in soup.find_all("img") if i.get("src") and ('pat' in str(i).lower() or 'club' in str(i).lower() or 'logo' in str(i).lower())][:60]
   row["ogimages"]=[x.get("content") for x in soup.find_all("meta") if x.get("property") in ("og:image","twitter:image")]
   row["matches"]=[r.text[max(0,m.start()-130):m.start()+220] for m in list(re.finditer(r"st[. ]?patricks|st[. ]?patrick's|st-patricks|stpatrick|clubs_logo",r.text,re.I))[:9]]
  rows.append(row)
 except Exception as e:rows.append({"url":url,"error":str(e)[:250]})
out=Path("docs/nir-clubs-2026-27/v13-extension/ym-crest-probe.json");out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(rows,ensure_ascii=False,indent=2))
for row in rows:print(row['url'],row.get('status'),row.get('length'),row.get('error',''))
