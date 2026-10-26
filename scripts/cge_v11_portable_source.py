import json,re,unicodedata,base64,hashlib,os
d=json.load(open("docs/cge-v11-source-audit/matchday-rankings.json",encoding="utf-8"))
P={"fc","afc","fk","ac","as","sk","sc","cf","cd","ss","sv","sd","hsk","gnk","nk","pfk","cfr","sfc","fkc","fsv","bk","if","u","ud"}
S={"fc","afc","fk","ac","cf","sc","football","club","calcio"}
def norm(s):
 s=unicodedata.normalize("NFD",s.lower())
 s="".join(x for x in s if not unicodedata.combining(x))
 for a,b in [("ł","l"),("ø","o"),("ð","d"),("þ","th"),("æ","ae"),("ß","ss")]:s=s.replace(a,b)
 tokens=re.findall("[a-z0-9]+",s)
 while len(tokens)>1 and tokens[0] in P:tokens.pop(0)
 while len(tokens)>1 and tokens[-1] in S:tokens.pop()
 return " ".join(tokens)
def fnv32(s):
 h=2166136261
 for c in s:
  h=((h^ord(c))*16777619)&0xffffffff
 return h
seen={};collided=set()
for r in d:
 if r.get("confederation")!="UEFA" or not isinstance(r.get("elo"),(float,int)):continue
 k=fnv32(r["country"]+"|"+norm(r["club"]))
 e=round(r["elo"]*10)
 if k in seen and seen[k]!=e:collided.add(k)
 else:seen[k]=e
for k in collided:seen.pop(k,None)
buf=bytearray()
for k,v in seen.items():buf+=k.to_bytes(4,"little")+v.to_bytes(2,"little")
b64=base64.b64encode(buf).decode("ascii")
out="docs/cge-v11-source-audit/uefa_hashed_b64.txt"
open(out,"w").write(b64)
open("docs/cge-v11-source-audit/uefa_hashed_metadata.json","w").write(json.dumps({"entries":len(seen),"collisions_removed":len(collided),"bytes":len(buf),"base64_length":len(b64),"sha256":hashlib.sha256(buf).hexdigest()},indent=2))
print("ENTRIES",len(seen),"BYTES",len(buf),"B64",len(b64),flush=True)
