#!/usr/bin/env python3
"""Audits club-badge-like 120x96 PNGs in ALL repo Git refs, with neutral findings.
Does not replace logos, forge badges, or claim game rendering test.
"""
import subprocess,re,io,csv,math,collections,json,hashlib
from PIL import Image,ImageStat
from pathlib import Path

ROOT=Path("docs/cge-v8-contrast-audit")
ROOT.mkdir(parents=True,exist_ok=True)
cmd=lambda *x:subprocess.run(x,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout
refs=cmd("git","for-each-ref","--format=%(refname)","refs/remotes/origin/").decode().splitlines()
refs=[x for x in refs if x and not x.endswith("/HEAD")]
print("BRANCHES",len(refs),flush=True)
imgs={}
for ref in refs:
    try:
        out=cmd("git","ls-tree","-r","--full-tree",ref).decode("utf8","replace")
        for l in out.splitlines():
            if not l.startswith("100644 blob "):continue
            meta,path=l.split("\t",1)
            if not path.startswith("docs/") or not path.lower().endswith(".png"):continue
            if not re.search(r"/\d{6,18}\.png$",path):continue
            sha=meta.split()[2]
            imgs[(ref,path)]=sha
    except Exception as e:print("TREE_ERR",ref,str(e),flush=True)
print("CANDIDATES",len(imgs),flush=True)
stats_cache={}
rows=[]
for j,((ref,path),sha) in enumerate(imgs.items()):
    if sha not in stats_cache:
        try:
            data=cmd("git","cat-file","blob",sha)
            image=Image.open(io.BytesIO(data))
            if image.size!=(120,96):stats_cache[sha]=None;continue
            image=image.convert("RGB")
            px=image.load()
            corners=[px[x,y] for x,y in [(0,0),(119,0),(0,95),(119,95),(2,2),(117,2),(2,93),(117,93)]]
            bkg=tuple(sorted(t[k] for t in corners)[len(corners)//2] for k in range(3))
            corner_spread=max(sum(abs(a[k]-bkg[k]) for k in range(3)) for a in corners)
            def diff(p):return (sum((p[k]-bkg[k])**2 for k in range(3)))**.5
            differences=[diff(px[x,y]) for y in range(8,88,2) for x in range(8,112,2)]
            occupied=sum(q>=30 for q in differences)/len(differences)
            fg=[q for q in differences if q>=18]
            contrast=sum(fg)/len(fg) if fg else 0
            bright=sum(bkg)/3
            is_uniform=corner_spread<35
            if is_uniform and occupied<.015:status="SEVERE_LOW_VISIBILITY"
            elif is_uniform and occupied<.04:status="SMALL_OR_LOW_VISIBILITY"
            elif is_uniform and contrast<43:status="WEAK_COLOR_SEPARATION"
            else:status="SCREEN_OK"
            stats_cache[sha]=(occupied,round(contrast,1),int(corner_spread),status)
        except Exception as e:
            stats_cache[sha]=("","","","READ_ERROR:"+str(e)[:120])
    stat=stats_cache[sha]
    if stat is None:continue
    match=re.search(r"/(\d{6,18})\.png$",path)
    rows.append((match.group(1),ref.removeprefix("refs/remotes/origin/"),path,sha,*stat))
with (ROOT/"all_branches_120x96_contrast.csv").open("w",newline="",encoding="utf8") as f:
    w=csv.writer(f)
    w.writerow(["teamIdFromFilename","branch","path","gitBlobSHA","foregroundCoverage","separationScore","cornerSpread","automatedScreen"])
    w.writerows(sorted(rows))
summary=dict(totalCandidates=len(imgs),assessed=len(rows),uniqueFiles=len(stats_cache),branches=len(refs),
             statuses=dict(collections.Counter(r[-1] for r in rows)))
(ROOT/"summary.json").write_text(json.dumps(summary,indent=2))
print("AUDIT_DONE",summary,flush=True)
