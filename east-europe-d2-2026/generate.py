import csv,requests,re,io,json,unicodedata,hashlib,time
from pathlib import Path
from PIL import Image,ImageOps
from urllib.parse import quote,urlparse,urljoin
BASE=Path(__file__).resolve().parents[1]
DATA=BASE/"east-europe-d2-2026"
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

def footylogos_candidate(name,country):
 # Exact club identity check via the club's own source page.
 try:
  from bs4 import BeautifulSoup
  aliases={'Feniks-Mariupol':'fenix-mariupol',
           'Probiy Horodenka':'nk-probiy-horodenka',
           'Ahrobiznes Volochysk':'fc-ahrobiznes-volochysk',
           'FC Oleksandriya':'fc-oleksandriya',
           'UCSA Tarasivka':'fc-ucsa-tarasivka',
           'Chernihiv':'fc-chernihiv',
           'Nyva Ternopil':'fc-nyva-ternopil',
           'Inhulets Petrove':'fc-inhulets-petrove',
           'Metalist Kharkiv':'fc-metalist-kharkiv',
           'Viktoriya Sumy':'fc-viktoriya-sumy',
           'Prykarpattia-Blaho':'fc-prykarpattia-blaho'}
  wanted=norm(name); v=aliases.get(name,slug(name))
  r=get('https://www.footylogos.com/logos/'+v,timeout=12)
  if not r:return None
  soup=BeautifulSoup(r.text,'html.parser')
  head=soup.find('h1')
  if not head or ('logo' not in head.get_text(' ',strip=True).lower()):return None
  heading=norm(head.get_text(' ',strip=True).split('logo')[0])
  if wanted not in heading and heading not in wanted and norm(v) not in heading:return None
  pics=[]
  for img in soup.find_all('img'):
   desc=img.get('alt','').lower()
   if 'logo' not in desc or ('club' in desc and 'logo' not in desc):continue
   if not any(norm(x) in norm(desc) for x in (name,v)) and wanted not in norm(desc):continue
   for key in ('src','data-src','srcset'):
    raw=img.get(key)
    if not raw:continue
    for part in raw.split(','):
     u=part.strip().split(' ')[0]
     if u.startswith('//'):u='https:'+u
     if u.startswith('/'):u='https://www.footylogos.com'+u
     if u.startswith('https://assets.footylogos.com') and u.split('?')[0].lower().endswith(('.png','.webp','.svg')):
      pics.append(u)
  if pics:return (pics[0],'FootyLogos exact club logo page',name)
  if country=='UA':
   return ('https://assets.footylogos.com/logos/'+v+'-logo-footylogos.svg','FootyLogos exact club SVG identity confirmed',name)
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
TRANSFERMARKT_GROUNDED_CLUB_IDS={
 "Polissya Zhytomyr": 53646,
 "FC Kharkiv": 55686,
 "Karpaty Lviv": 85465,
 "LNZ Cherkasy": 63007,
 "Kolos Kovalivka": 48332,
 "Epitsentr Kamianets-Podilskyi": 84122,
 "Veres Rivne": 26459,
 "Livyi Bereh Kyiv": 86209,
 "Bukovyna Chernivtsi": 21903,
 "Obolon Kyiv": 39097,
 "Kudrivka": 87883,
 "Kryvbas Kryvyi Rih": 3592,
 "FC Zimbru Chișinău": 2714,
 "FC Petrocub Hîncești": 46643,
 "Dacia Buiucani": 39003,
 "FC Milsami Orhei": 30686,
 "FC Politehnica UTM": 90107,
 "FC Real Sireți": 128633,
 "CSF Bălți": 83016,
 "Dinamo Batumi": 11344,
 "Rustavi": 1799,
 "Samgurali Tsqaltubo": 29675,
 "Torpedo Kutaisi": 253,
 "Gagra": 22842,
 "Spaeri": 72702,
 "Meshakhte Tkibuli": 35056,"FC Minsk":23664,"Torpedo-BelAZ Zhodino":7964,"Slavia Mozyr":6423,"Baranovichi":24009,"Arsenal Dzerzhinsk":72822,"Belshina Bobruisk":3886,"Dnepr Mogilev":4394,"Naftan Novopolotsk":8563
}



FOOTY_UKRAINE_VERIFIED_PAGES={
'Viktoriya Sumy':'fc-viktoriya-sumy',
'Feniks-Mariupol':'fenix-mariupol',
'Ahrobiznes Volochysk':'fc-ahrobiznes-volochysk',
'SC Poltava':'sc-poltava',
'FC Oleksandriya':'fc-oleksandriya',
'Prykarpattia-Blaho':'fc-prykarpattia-blaho',
'Metalist Kharkiv':'fc-metalist-kharkiv',
'Nyva Ternopil':'fc-nyva-ternopil',
'Inhulets Petrove':'fc-inhulets-petrove',
'UCSA Tarasivka':'fc-ucsa-tarasivka',
'Chernihiv':'fc-chernihiv',
'Probiy Horodenka':'nk-probiy-horodenka',
}
def ukraine_footy_asset(name):
 slug=FOOTY_UKRAINE_VERIFIED_PAGES.get(name)
 if not slug:return None
 return ('https://assets.footylogos.com/logos/'+slug+'-logo-footylogos.svg','FootyLogos verified 2026 D2 club crest page',name)

MMD31_D2_CLUB_ID_CRESTS = {
  "Slutsksakhar Slutsk": 27238,
  "Energetik-BGU Minsk": 27204,
  "Kommunalnik Slonim": 24175,
  "Volna Pinsk": 24177,
  "Uni X-Labs Minsk": 98588,
  "Orsha": 32976,
  "Osipovichy": 32474,
  "Kulykiv-Bilka": 112110,
  "SC Poltava": 81401,
  "FC Oleksandriya": 18303,
  "Lokomotyv Kyiv": 27227,
  "Gareji Sagarejo": 61358,
  "Telavi": 41310,
  "Shturmi": 98682,
  "Samtredia": 2950,
  "Merani Martvili": 31551,
  "Aragvi Dusheti": 51588,
  "Sioni Bolnisi": 10531,
  "Odishi 1919": 49352,
  "Kolkheti 1913 Poti": 28971,
  "Gori": 61250
}


MOLDOVA_ARCHIVE_ALIASES={
 'CF Univer Comrat':['Univer Comrat','Univer'],
 'FCM Ungheni':['FCM Ungheni'],
 'Vulturii Cutezători Sîngerei':['Vulturii Cutezatori','Vulturii'],
 'CSF Spartanii Sportul Chișinău':['Spartanii Selemet','Spartanii Sportul','Sparta Selemet'],
 'FC Iskra Rîbnița':['Iskra-Ribinita','Iskra'],
 'FC Stăuceni':['Stauceni'],
 'FC Victoria Ialoveni':['Victoria Bardar','Victoria'],
 'CF Oguz Comrat':['Oguzsport','Oguz'],
 'FC Fălești':['Flacara Falesti','Flacara','Falesti'],
 'FC Național Ialoveni':['National Ialoveni','National']
}
def moldova_archive():
 # Public club crest archive labelled with the 2026/27 Moldovan Liga 1 groups.
 from urllib.parse import urljoin
 out={};audit=[]
 r=get('https://escudosfc.com.br/mol.htm',timeout=35)
 if not r:return out
 try:
  from bs4 import BeautifulSoup
  soup=BeautifulSoup(r.content,'html.parser')
  for img in soup.find_all('img'):
   url=img.get('src') or img.get('data-src') or ''
   title=img.get('alt') or img.get('title') or ''
   if not url or not title:continue
   url=urljoin('https://escudosfc.com.br/mol.htm',url)
   audit.append({'text':title,'url':url})
   if urlparse(url).path.lower().endswith(('.png','.jpg','.jpeg','.webp')):
    out.setdefault(norm(title),(url,"EscudosFC Moldova 2026/27 league crest archive",title))
  (DATA/'archive-moldova-image-index.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
 except Exception as exc:
  (DATA/'archive-moldova-image-index.json').write_text(json.dumps({'error':str(exc)},ensure_ascii=False))
 return out

PARENT_LOGOS={
 'Dinamo-2 Minsk':('by','dinamo-minsk'),
 'Minsk B':('by','fc-minsk'),
 'BATE-2 Borisov':('by','bate-borisov'),
 'Gomel B':('by','fc-gomel'),
 'Kolos-2 Kovalivka':('ua','kolos-kovalivka'),
 'Polissya-2 Zhytomyr':('ua','polissya-zhytomyr'),
 'Zimbru-2 Chișinău':('md','fc-zimbru-chisinau')
}
def family_candidate(name):
 if name not in PARENT_LOGOS:return None
 c,slug=PARENT_LOGOS[name]
 url="https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-east-europe-d1-2026-v13-badges/docs/club-flags/east-europe-d1-2026/"+c+"/"+slug+".png"
 return (url,"Official parent-club crest (reserve)",name)

g=guardian_catalog();e=espn_catalog();md_archive=moldova_archive()
saved={}
try:
 saved={r['team_id']:r for r in json.loads((DATA/'badges-manifest.json').read_text())['records']}
except Exception:pass
records=[]
for row in ROWS:
 team=row['club'];country=row['country'];id=row['team_id'];cand=[]
 if id in saved:
  prev=saved[id];p=BASE/prev.get('path','')
  if prev.get('status')!='MISSING' and p.is_file():
   try:
    with Image.open(p) as ver:
     if ver.size==(120,96) and ver.format=='PNG':
      records.append(prev)
      print(team,"PREVIOUS_PNG_PRESERVED",flush=True)
      continue
   except Exception:pass

 if country=='MD':
  for alias in MOLDOVA_ARCHIVE_ALIASES.get(team,[team]):
   if norm(alias) in md_archive:
    cand.append(md_archive[norm(alias)])
    break
 tm_checked=MMD31_D2_CLUB_ID_CRESTS.get(team)
 if tm_checked:
  cand.append((f"https://tmssl.akamaized.net/images/wappen/head/{tm_checked}.png","Transfermarkt documented club profile ID",team))
 parent=family_candidate(team)
 if parent:cand.append(parent)
 ua=ukraine_footy_asset(team)
 if ua:cand.append(ua)
 for n in aliases(team):
  for catalog in (e,g):
   z=catalog.get(norm(n))
   if z and z not in cand:cand.append(z)
 tm_id=TRANSFERMARKT_GROUNDED_CLUB_IDS.get(team)
 if tm_id:cand.append((f'https://tmssl.akamaized.net/images/wappen/head/{tm_id}.png','Transfermarkt club identity verified via public league roster',team))
 extra=sportsdb(team)
 if extra:cand.append(extra)
 if not cand:
  extra=footylogos_candidate(team,country)
  if extra:cand.append(extra)
 if not cand:
  extra=wiki(team)
  if extra:cand.append(extra)
 record={'team_id':id,'country':country,'club':team,'status':'MISSING','sourceUrl':'','sourceProvider':'','sourceMatchedName':'','path':'','width':None,'height':None,'color':'','visuallyConfirmed':False}
 for u,provider,match in cand:
  image=render(u)
  if not image:continue
  pic,color=plate(image)
  fn=f"docs/club-flags/east-europe-d2-2026/{country.lower()}/{slug(team)}.png"
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
