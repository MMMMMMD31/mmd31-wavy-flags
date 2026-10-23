#!/usr/bin/env python3
"""Quarantine confirmed generic FFF placeholder PNGs, and 4 ambiguous shared crests.
Original files remain in audit quarantine; never modify team identities.
"""
import csv,shutil
from pathlib import Path
root=Path("flags/clubs/standard/outremer-2026-27")
similar=Path("audit/outremer-2026-27/crest_similarity_audit.csv")
outdir=Path("audit/outremer-2026-27/quarantine")
outdir.mkdir(parents=True,exist_ok=True)
report=Path("audit/outremer-2026-27/quarantine_log.csv")
rows=list(csv.DictReader(similar.open(encoding="utf8")))
ambiguous={"1990262000053","1990262000260","1990262000151","1990262000245"}
problems=[]
for row in rows:
 tid=row["team_id"]
 if row["suspected_fff_placeholder"]=="YES":status="FFF_generic_not_club_crest"
 elif tid in ambiguous:status="same_image_two_different_club_identifiers_to_verify"
 else:continue
 src=root/(tid+".png")
 dst=outdir/(tid+".png")
 if src.exists():
  shutil.copy2(src,dst)
  src.unlink()
 elif not dst.exists():
  raise ValueError(f"Missing image both active and quarantine: {tid}")
 problems.append(dict(team_id=tid,reason=status,sha256=row["sha256"],sha_group=row["sha_group"]))
with report.open("w",encoding="utf8",newline="") as f:
 w=csv.DictWriter(f,fieldnames=["team_id","reason","sha256","sha_group"]);w.writeheader();w.writerows(problems)
print("QUARANTINED",len(problems),"FFF",sum(r["reason"]=="FFF_generic_not_club_crest" for r in problems),
      "uncertain_shared",sum(r["reason"]!="FFF_generic_not_club_crest" for r in problems))
