import os,json,gzip,base64,zlib,collections
P="docs/cge-v11-source-audit"
a=json.load(open(P+"/matchday-rankings.json"))
eu=[x for x in a if x.get("confederation")=="UEFA"]
small=[[x.get("club",""),x.get("country",""),round(float(x.get("elo",0)),1)] for x in eu if isinstance(x.get("elo"),(float,int))]
raw=json.dumps(small,ensure_ascii=False,separators=(",",":")).encode("utf8")
encoded=base64.b64encode(zlib.compress(raw,9)).decode()
open(P+"/UEFA_NAME_COUNTRY_ELO_ZLIB_BASE64.txt","w").write(encoded)
countries=collections.Counter(x[1] for x in small)
open(P+"/uefa_stats.json","w").write(json.dumps({"all":len(a),"uefa":len(small),"raw":len(raw),"compressed_b64":len(encoded),"countries":countries},indent=2))
print("UEFA",len(small),"BASE64",len(encoded))
