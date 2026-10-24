#!/usr/bin/env python3
"""Publish uniquely identified 2026/27 German club emblems from public Transfermarkt CDN.

Club-to-ID mappings were individually verified against indexed Transfermarkt
club profiles. Ambiguous clubs are excluded; generic images are rejected.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import time
from collections import defaultdict
from pathlib import Path

import requests
from PIL import Image
from mmd31_commons_germany import draw_image

ROWS = Path("tools/mmd31_germany_tm_verified_55.csv")
ROOT = Path("docs/german-clubs-2026-27/transfermarkt-verified-20261024")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MMD31-CGE-ClubCrestAudit/1.0)",
    "Referer": "https://www.transfermarkt.de/",
    "Accept": "image/png,image/webp,image/jpeg,*/*",
}
ALLOWED_DUPLICATE_PAIRS = {frozenset(("FK Pirmasens", "FK Pirmasens II"))}


def load_badge(row: dict) -> dict:
    club_id = row["tmClubId"]
    failures = []
    for size in ("norm", "head"):
        url = f"https://tmssl.akamaized.net/images/wappen/{size}/{club_id}.png"
        try:
            res = requests.get(url, headers=HEADERS, timeout=27)
            if res.status_code != 200:
                failures.append(f"{size}: HTTP {res.status_code}")
                continue
            if not 80 <= len(res.content) <= 4_000_000:
                failures.append(f"{size}: image byte length invalid")
                continue
            original = Image.open(io.BytesIO(res.content))
            original.load()
            if min(original.size) < 24:
                failures.append(f"{size}: image resolution too low")
                continue
            # Reject blank placeholders or flat-colour pixels.
            sample = original.convert("RGBA").resize((40, 40))
            if len(set(sample.getdata())) < 8:
                failures.append(f"{size}: generic uniform image")
                continue
            image, bg = draw_image(res.content)
            return {
                "teamId": row["teamId"],
                "club": row["club"],
                "transfermarkt_id": club_id,
                "source": res.url,
                "source_page": f"https://www.transfermarkt.de/jumplist/startseite/verein/{club_id}",
                "source_type": ("transfermarkt_verified_federation_league_alias"
                                if row["club"] == "SV Scharmbeck-Pattensen-Axstedt"
                                else "transfermarkt_exact_profile_club_id"),
                "official_name": ("SG Scharmbeck-Pattensen-Ashausen"
                                  if row["club"] == "SV Scharmbeck-Pattensen-Axstedt"
                                  else row["club"]),
                "background_rgb": bg,
                "raw_sha256": hashlib.sha256(res.content).hexdigest(),
                "_image": image,
            }
        except Exception as exc:
            failures.append(f"{size}: {type(exc).__name__}")
    return {"teamId": row["teamId"], "club": row["club"],
            "reason": "; ".join(failures)}


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    with ROWS.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    file = ROOT / "manifest.json"
    previous = json.loads(file.read_text()) if file.exists() else []
    existing = {x["teamId"] for x in previous}
    additions, failures = [], []
    for i, row in enumerate(rows, 1):
        if row["teamId"] in existing:
            continue
        result = load_badge(row)
        if "_image" in result:
            result["_image"] = result.pop("_image")
            additions.append(result)
            print(f"{i}/{len(rows)} FOUND {row['club']} (TM {row['tmClubId']})", flush=True)
        else:
            failures.append(result)
            print(f"{i}/{len(rows)} NO BADGE {row['club']}: {result['reason']}", flush=True)
        time.sleep(0.4)
    groups = defaultdict(list)
    for item in additions:
        groups[item["raw_sha256"]].append(item)
    valid = []
    for item in additions:
        same = groups[item["raw_sha256"]]
        names = {r["club"] for r in same}
        if len(names) > 1 and frozenset(names) not in ALLOWED_DUPLICATE_PAIRS:
            failures.append({"teamId": item["teamId"], "club": item["club"],
                             "reason": "same original image as unrelated club"})
            continue
        image = item.pop("_image")
        path = ROOT / (item["teamId"] + ".png")
        image.save(path, optimize=True)
        item["png_path"] = str(path)
        item["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        valid.append(item)
    file.write_text(json.dumps(previous + valid, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    status = {
        "checked": len(rows), "new_verified": len(valid),
        "total_verified": len(previous) + len(valid),
        "failed": failures, "provenance": "manually matched Transfermarkt club ID",
    }
    (ROOT / "status.json").write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n",
                                     encoding="utf-8")
    print("RESULT", status["new_verified"], "VALID", len(valid),
          "FAILED", len(failures), flush=True)


if __name__ == "__main__":
    main()
