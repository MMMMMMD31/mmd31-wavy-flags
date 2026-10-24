import csv,requests,re,io,json,unicodedata,hashlib,time
from pathlib import Path
from PIL import Image,ImageOps
from urllib.parse import quote,urlparse,urljoin
BASE=Path(__file__).resolve().parents[1]
DATA=BASE/"east-europe-d1-2026"
ROWS=list(csv.DictReader(open(DATA/"clubs.csv",encoding="utf-8")))
S=requests.Session();S.headers.update({"User-Agent":"MMD31-Simulator-Crest-Research/1.0 (club identity audit)"})
def slug(s):
 return re.sub('[^a-z0-9]+','-',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()).strip('-')
def norm(s):
 s=slug(s)
 for v in ('football-club-','fc-','cf-','sc-','-football-club','-fc','-cf','-sc'):
  if s.startswith(v):s=s[len(v):]
  if s.endswith(v):s=s[:-len(v)]
 return s
def get(url,params=None,timeout=8):
 try:
  r=S.get(url,params=params,timeout=timeout)
  return r if r.ok else None
 except Exception:return None
def aliases(name):
 alias={
 "FC Kharkiv":["Metalist 1925 Kharkiv","Kharkiv","FC Metalist 1925 Kharkiv"],
 "Dinamo Brest":["Dynamo Brest","FC Dynamo Brest"],
 "Dinamo Minsk":["Dynamo Minsk","FC Dinamo Minsk"],
 "Dnepr Mogilev":["Dnepr Mogilev","Dnyapro Mogilev"],
 "Torpedo-BelAZ Zhodino":["Torpedo Zhodino","Torpedo-BelAZ"],
 "FC Petrocub Hîncești":["Petrocub Hincesti","FC Petrocub"],
 "FC Zimbru Chișinău":["FC Zimbru","Zimbru Chisinau"],
 "FC Milsami Orhei":["FC Milsami","Milsami"],
 "FC Sheriff Tiraspol":["FC Sheriff","Sheriff Tiraspol"],
 "Dinamo Batumi":["FC Dinamo Batumi"],
 "Dinamo Tbilisi":["FC Dinamo Tbilisi"],
 "Dila Gori":["FC Dila Gori"],
 "Torpedo Kutaisi":["FC Torpedo Kutaisi"],
 "Iberia 1999":["Saburtalo Tbilisi","FC Iberia 1999"],
 "Polissya Zhytomyr":["Polissya Zhytomyr","Polissya"],
 "Shakhtar Donetsk":["FC Shakhtar Donetsk"],
 "Dynamo Kyiv":["FC Dynamo Kyiv","Dynamo Kiev"],
 "Zorya Luhansk":["FC Zorya Luhansk","Zorya"],
 "Neman Grodno":["FC Neman Grodno","Neman"],
 "FC Gomel":["Gomel"],
 "FC Vitebsk":["Vitebsk"],
 "FC Minsk":["Minsk"],
 "BATE Borisov":["BATE"],
 "Samgurali Tsqaltubo":["Samgurali"],
 "Meshakhte Tkibuli":["Meshakhte"],
 "FC Real Sireți":["Real Sireti"],
 "CSF Bălți":["Balti","Zaria Balti"],
 "FC Politehnica UTM":["Politehnica UTM"],
 "Kolos Kovalivka":["FC Kolos Kovalivka"],
 "LNZ Cherkasy":["LNZ"],
 "Kudrivka":["FC Kudrivka"],
 "Gagra":["FC Gagra"],
 "Spaeri":["FC Spaeri"],
 "Rustavi":["FC Rustavi"],
 "Baranovichi":["FC Baranovichi"],
 "Maxline Vitebsk":["Maxline","FC Maxline Vitebsk"],
 "Isloch Minsk Raion":["Isloch","FC Isloch"],
 "Slavia Mozyr":["Slavia Mozyr"],
 "Belshina Bobruisk":["Belshina"],
 "Naftan Novopolotsk":["Naftan"],
 "Arsenal Dzerzhinsk":["Arsenal Dzyarzhynsk"],
 "Chornomorets Odesa":["Chornomorets Odessa"],
 "Epitsentr Kamianets-Podilskyi":["Epitsentr"],
 "Bukovyna Chernivtsi":["Bukovyna"],
 "Veres Rivne":["Veres"],
 "Obolon Kyiv":["Obolon"],
 "Dacia Buiucani":["Dacia Buiucani"]
 }
 return [name]+alias.get(name,[])
def guardian_catalog():
 r=get("https://raw.githubusercontent.com/guardian/football-assets/main/source/crests/crests.json",timeout=25)
 result={}
 if r:
  for item in r.json().get('crests',[]):
   nm=item.get('team','');fn=item.get('filename','')
   if nm and fn:result.setdefault(norm(nm),("https://raw.githubusercontent.com/guardian/football-assets/main/source/crests/"+fn,"Guardian football-assets",nm))
 return result
def espn_catalog():
 result={}
 for league in ('blr.1','ukr.1','geo.1','mda.1','uefa.champions','uefa.europa','uefa.europa.conf'):
  r=get("https://site.web.api.espn.com/apis/site/v2/sports/soccer/"+league+"/teams",{'limit':500})
  if not r:continue
  try:
   for item in r.json()['sports'][0]['leagues'][0]['teams']:
    t=item['team'];l=t.get('logos') or [];u=l[0].get('href','') if l else ''
    if not u:continue
    for n in (t.get('name'),t.get('displayName'),t.get('shortDisplayName')):
     if n:result.setdefault(norm(n),(u,"ESPN",n))
  except Exception:pass
 return result
def sportsdb(name):
 for n in aliases(name)[:3]:
  r=get("https://www.thesportsdb.com/api/v1/json/123/searchteams.php",{'t':n})
  if not r:continue
  try:
   for x in r.json().get('teams') or []:
    if x.get('strSport')!='Soccer' or not x.get('strBadge'):continue
    if norm(x.get('strTeam','')) in [norm(z) for z in aliases(name)]:
     return x['strBadge'],"TheSportsDB exact identity",x['strTeam']
  except Exception:pass
 return None
def wiki(name):
 # Wikipedia page photo must be a crest, rather than a stadium or team photograph.
 for alt in aliases(name)[:3]:
  for title in (alt+" F.C.",alt+" football club"):
   r=get('https://en.wikipedia.org/w/api.php',{'action':'query','format':'json','generator':'search','gsrsearch':'intitle:'+title,'gsrlimit':3,'prop':'pageimages','piprop':'original'})
   if not r:continue
   try:
    for p in r.json().get('query',{}).get('pages',{}).values():
     title=p.get('title','');u=p.get('original',{}).get('source','')
     if not u or not any(norm(z) in norm(title) for z in aliases(name) if len(norm(z))>3):continue
     base=urlparse(u).path.lower()
     if (base.endswith(('.svg','.png','.webp')) and any(x in base for x in ('crest','logo','badge','fc.svg','fc.png','fc-','f.c.'))):
      return u,"Wikipedia original crest",title
   except Exception:pass
 return None
def render(url):
 r=get(url,timeout=16)
 if not r:return None
 data=r.content
 if len(data)<150 or len(data)>8000000:return None
 if b'<svg' in data[:400] or urlparse(url).path.lower().endswith('.svg'):
  try:
   import cairosvg
   data=cairosvg.svg2png(bytestring=data,output_width=500,output_height=500)
  except Exception:return None
 try:
  im=Image.open(io.BytesIO(data)).convert('RGBA')
  if min(im.size)<70:return None
  return im
 except Exception:return None
def plate(im):
 from collections import Counter
 bbox=im.getbbox()
 if bbox:im=im.crop(bbox)
 im.thumbnail((86,78),Image.Resampling.LANCZOS)
 colors=[(r//40,g//40,b//40) for r,g,b,a in im.getdata() if a>200 and max(r,g,b)-min(r,g,b)>38 and max(r,g,b)<248]
 vals=Counter(colors).most_common(1)
 bg=tuple(min(236,x*40+20) for x in vals[0][0]) if vals else (43,58,111)
 out=Image.new('RGBA',(120,96),bg+(255,))
 out.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
 return out.convert('RGB'),bg
g=guardian_catalog();e=espn_catalog()
saved={}
try:
 saved={r['team_id']:r for r in json.loads((DATA/'badges-manifest.json').read_text())['records']}
except Exception:pass
records=[]
for row in ROWS:
 team=row['club'];country=row['country'];id=row['team_id'];cand=[]
 for n in aliases(team):
  for catalog in (e,g):
   z=catalog.get(norm(n))
   if z and z not in cand:cand.append(z)
 extra=sportsdb(team)
 if extra:cand.append(extra)
 if not cand:
  extra=wiki(team)
  if extra:cand.append(extra)
 record={'team_id':id,'country':country,'club':team,'status':'MISSING','sourceUrl':'','sourceProvider':'','sourceMatchedName':'','path':'','width':None,'height':None,'color':'','visuallyConfirmed':False}
 for u,provider,match in cand:
  image=render(u)
  if not image:continue
  pic,color=plate(image)
  fn=f"docs/club-flags/east-europe-d1-2026/{country.lower()}/{slug(team)}.png"
  dst=BASE/fn;dst.parent.mkdir(parents=True,exist_ok=True);pic.save(dst,'PNG')
  with Image.open(dst) as check:
   assert check.size==(120,96) and check.format=='PNG'
  record.update(status='SOURCE_PNG_GENERATED_IDENTITY_VISUAL_REVIEW',sourceUrl=u,sourceProvider=provider,sourceMatchedName=match,path=fn,width=120,height=96,color='#%02x%02x%02x'%color)
  break
 if record['status']=='MISSING' and id in saved:
  past=saved[id];dst=BASE/past.get('path','')
  if dst.is_file():record=past
 records.append(record)
 print(team,record['status'],flush=True)
manifest={'count':len(records),'generated':sum(1 for x in records if x['status']!='MISSING'),'records':records}
(DATA/'badges-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
