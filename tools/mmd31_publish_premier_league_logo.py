#!/usr/bin/env python3
"""Fetch the actual Premier League crest/wordmark without altering its design."""
from pathlib import Path
import requests,io,json,hashlib
from PIL import Image
URL="https://thumb.wikimedia.org/wikipedia/commons/thumb/b/bf/Pl-logo-light.svg/960px-Pl-logo-light.svg.png"
OUT=Path("docs/english-clubs-2026-27/competition")
OUT.mkdir(parents=True,exist_ok=True)
r=requests.get(URL,timeout=30,headers={"User-Agent":"MMD31/1.0 (personal football simulation; 2026 Premier League Wikimedia source attribution)"})
r.raise_for_status()
im=Image.open(io.BytesIO(r.content))
assert im.format=="PNG" and im.width>=300 and im.height>=150,(im.format,im.size)
p=OUT/"premier-league-logo.png"
p.write_bytes(r.content)
json.dump({"identity":"Premier League official logo with crowned lion and wordmark","source_file":"https://commons.wikimedia.org/wiki/File:Pl-logo-light.svg","source_png":URL,"size":list(im.size),"sha256":hashlib.sha256(r.content).hexdigest(),"rights":"Premier League trademark; personal project, not an official affiliation."},open(OUT/"premier-league-logo-source.json","w"),indent=2)
print("VERIFIED:",str(p),len(r.content),im.size)
