#!/usr/bin/env python3
"""Inspect alternative websites to find real, correctly affiliated 2026/27 crest source URLs."""
import requests,re,json,html
from urllib.parse import urljoin
from pathlib import Path
SITES=[
 ("Bota Fogo AASM","https://aatletismosmiguel.pt/our-team/",["bota-fogo","bota fogo","botafogo"]),
 ("CD Santo António blog","https://emblemasdeportugal.blogspot.com/2011/01/clube-desportivo-santo-antonio.html",["santo","emblemasdeportugal"]),
 ("Vitória Pico Pedra FPF","https://vemjogar.fpf.pt/clube/awBQ/vitoria-clube-pico-pedra",["eea1fd","media/file","pico da pedra"]),
 ("Bota Fogo zerozero DK","https://www.zerozero.dk/equipa/bota-fogo/4714",["bota fogo","logo","imgbank"]),
 ("CD Santo António kit","https://www.footballkitarchive.com/fr/maillot-domicile-cd-santo-antonio-2026-27-514665/",["santo antonio","logo","badge"])
]
out=[]
for title,url,terms in SITES:
 try:
  r=requests.get(url,timeout=20,headers={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"})
  raw=html.unescape(r.text)
  snippets=[]
  for term in terms:
   match=re.search(re.escape(term),raw,re.I)
   if match:
    snippets.append({"term":term,"context":raw[max(0,match.start()-1250):min(len(raw),match.end()+1300)]})
  images=re.findall(r"<(?:img|meta|source)\b[^>]+>",raw,re.I)
  out.append({"title":title,"url":url,"status":r.status_code,"images_n":len(images),"head_html":raw[:500],"matches":snippets[:6],"images":images[:250]})
 except Exception as e:out.append({"title":title,"url":url,"error":str(e)})
Path('docs/portugal-gibraltar-clubs-2026-27/v1/probe-alternative-sources.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps([{"title":x["title"],"status":x.get("status"),"imgs":x.get("images_n"),"error":x.get("error")} for x in out],ensure_ascii=False))
