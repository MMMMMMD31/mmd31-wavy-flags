#!/usr/bin/env python3
"""Quarantine two visually confirmed FFF placeholders; do not delete the teams."""
import shutil,csv
from pathlib import Path
root=Path("flags/clubs/standard/outremer-2026-27")
q=Path("audit/outremer-2026-27/quarantine");q.mkdir(exist_ok=True,parents=True)
for team_id in (1990262000093,1990262000220):
 src=root/(str(team_id)+".png");dst=q/src.name
 if src.is_file():shutil.copy2(src,dst);src.unlink()
 if not dst.is_file():raise ValueError("No quarantined copy for "+str(team_id))
print("Quarantined two FFF placeholders (IDs 1990262000093 and 1990262000220), teams not changed")
