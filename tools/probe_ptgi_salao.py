#!/usr/bin/env python3
import requests,re,json,html
from urllib.parse import urljoin
from pathlib import Path
P=Path("docs/portugal-gibraltar-clubs-2026-27/v1/salao-probe.json")
sources=["https://www.europlan-online.de/waldsportplatz/stadion-83647.html",
         "https://www.zerozero.pt/equipa/salao/12292",
         "https://www.zerozero.pt/equipa/salao/12292?redirm=1"]
output=[]
for url in sources:
    try:
        res=requests.get(url,timeout=30,headers={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"})
        txt=html.unescape(res.text)
        items=[]
        for m in re.finditer(r"<img\\b[^>]+>",txt,re.I):
            tag=m.group(0)
            if any(term in tag.lower() for term in ["salão","salao","12292","wappen"]):
                items.append(tag[:1100])
        for m in re.finditer(r".{0,80}(?:12292_imgbank|salao\\.(?:jpg|png)|salao_[^ ]+).{0,80}",txt,re.I):
            items.append(m.group(0)[:500])
        output.append({"url":url,"status":res.status_code,"chars":len(txt),"candidates":items[:25]})
    except Exception as e:output.append({"url":url,"error":str(e)[:250]})
P.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(output,ensure_ascii=False)[:12000])
