import csv,collections,json
from pathlib import Path
root=Path("docs/cge-v8-contrast-audit")
with (root/"all_branches_120x96_contrast.csv").open(newline="",encoding="utf8") as f:
 r=list(csv.DictReader(f))
suspect=[x for x in r if x["automatedScreen"]!="SCREEN_OK"]
uni={}
for x in suspect:
 k=(x["teamIdFromFilename"],x["gitBlobSHA"])
 if k not in uni:
  uni[k]={**x,"numberReferences":0}
 uni[k]["numberReferences"]+=1
with (root/"flagged_contrast_unique.csv").open("w",newline="",encoding="utf8") as f:
 w=csv.DictWriter(f,fieldnames=[*r[0].keys(),"numberReferences"])
 w.writeheader();w.writerows(uni.values())
print("FLAGGED",len(suspect),"UNIQUE",len(uni))
