import csv,json,os
p="docs/cge-v11-source-audit"
records=json.load(open(p+"/matchday-rankings.json",encoding="utf8"))
with open(p+"/uefa_ratings_slim.tsv","w",encoding="utf8",newline="") as f:
 writer=csv.writer(f,delimiter="\t",lineterminator="\n")
 for r in records:
  if r.get("confederation")!="UEFA" or not isinstance(r.get("elo"),(float,int)):continue
  name=r.get("club","").replace("\t"," ").replace("\n"," ")
  writer.writerow([name,r.get("country",""),round(r["elo"]*10)])
print("OK",os.path.getsize(p+"/uefa_ratings_slim.tsv"))
