#!/usr/bin/env python3
"""Capture auditable, date-stamped Ligue 2 Elo values, not fabricated ratings."""
import requests,bs4,re,json
from pathlib import Path
from urllib.parse import urljoin
B=Path(__file__).resolve().parent
s=requests.Session();s.headers.update({"User-Agent":"Mozilla/5.0 (MMD31 football analysis)"})
url="https://www.footballratings.org/leagues/ligue-2"
teams={}
try:
 soup=bs4.BeautifulSoup(s.get(url,timeout=25).text,"html.parser")
 urls={}
 for a in soup.find_all("a",href=True):
  if "/clubs/" in a["href"]:
   urls[a.get_text(" ",strip=True).lower()]=urljoin(url,a["href"])
 for key,page in urls.items():
  try:
   h=bs4.BeautifulSoup(s.get(page,timeout=18).text,"html.parser")
   full=h.get_text(" ",strip=True)
   match=re.search(r"Current Rating\\s*([0-9][0-9,]+)",full,re.I)
   dat=re.search(r"Current Rating\\s*[0-9][0-9,]+\\s*(\\d{1,2} [A-Za-z]+ 2026)",full,re.I)
   if match:
    teams[key]={"elo":int(match.group(1).replace(",","")),"date":dat.group(1) if dat else "October 2026","source":page}
  except Exception:pass
except Exception as exc:print("Elo collection warning",str(exc))
out={"source":url,"values":teams}
(B/"ligue2-elo-observations.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf8")
print("verified ratings",len(teams),sorted(teams))
