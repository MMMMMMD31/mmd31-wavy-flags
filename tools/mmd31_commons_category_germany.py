#!/usr/bin/env python3
"""Batch-match German football crest files from curated Commons categories.

Keeps results separate from the slower individual file search, so workflows
may commit independently without overwriting the existing crest manifest.
"""
import concurrent.futures
import csv
import hashlib
import json
import re
from pathlib import Path

import requests

from mmd31_commons_germany import (
    COMMONS_API, USER_AGENT, club_tokens, draw_image, fetch_json, normalized,
    title_matches,
)

ROOT = Path("docs/german-clubs-2026-27/commons-category-20261024")
BASE_MANIFEST = Path("docs/german-clubs-2026-27/missing-20261024/manifest.json")
SOURCE_CSV = Path("tools/mmd31_remaining_germany_692.csv")
CATEGORIES = (
    "Category:Association football logos of Germany",
    "Category:SVG association football logos of Germany",
)


def fetch_titles(category):
    titles = set()
    cont = {}
    for _ in range(30):
        data = fetch_json({"list": "categorymembers", "cmtitle": category,
                           "cmnamespace": 6, "cmlimit": 500, **cont})
        if not data:
            break
        titles.update(x["title"] for x in data.get("query", {}).get("categorymembers", [])
                      if x["title"].startswith("File:"))
        token = data.get("continue", {}).get("cmcontinue")
        if not token:
            break
        cont = {"cmcontinue": token}
    return titles


def tolerant_exact(club, title):
    if title_matches(club, title):
        return True
    if not title.startswith("File:"):
        return False
    name = title[5:].rsplit(".", 1)[0]
    compact = re.sub("logo|wappen|vereinswappen|emblem|crest", "",
                     "".join(normalized(name).split()))
    expected = "".join(club_tokens(club))
    return len(expected) >= 9 and compact == expected


def image_metadata(item):
    titles = item["candidate_titles"]
    results = fetch_json({"prop": "imageinfo", "titles": "|".join(titles[:8]),
                          "iiprop": "url|mime|extmetadata"})
    if not results:
        return None
    pics = []
    for page in results.get("query", {}).get("pages", {}).values():
        info = (page.get("imageinfo") or [{}])[0]
        url = info.get("url", "")
        if not url.startswith("https://upload.wikimedia.org/"):
            continue
        if info.get("mime") not in ("image/svg+xml", "image/png",
                                   "image/jpeg", "image/webp", "image/gif"):
            continue
        ext = info.get("extmetadata", {})
        pics.append({
            "teamId": item["teamId"], "club": item["club"],
            "source": url, "source_type": "commons_german_football_category",
            "commons_file": page.get("title", ""),
            "source_page": "https://commons.wikimedia.org/wiki/" +
                           page.get("title", "").replace(" ", "_"),
            "license": ext.get("LicenseShortName", {}).get("value", "Unspecified"),
        })
    if not pics:
        return None
    return sorted(pics, key=lambda x: (
        not x["source"].lower().endswith(".svg"), len(x["commons_file"])))[0]


def render(item):
    try:
        response = requests.get(item["source"], headers={"User-Agent": USER_AGENT},
                                timeout=35)
        response.raise_for_status()
        if len(response.content) > 8_000_000:
            return None
        img, rgb = draw_image(response.content)
        target = ROOT / (str(item["teamId"]) + ".png")
        img.save(target, optimize=True)
        item["png_path"] = str(target)
        item["background_rgb"] = rgb
        item["sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
        return item
    except Exception:
        return None


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    old = json.loads(BASE_MANIFEST.read_text(encoding="utf-8"))
    skip = {str(x["teamId"]) for x in old}
    with SOURCE_CSV.open(encoding="utf-8-sig", newline="") as file:
        teams = [x for x in csv.DictReader(file) if x["teamId"] not in skip]
    titles = set()
    for category in CATEGORIES:
        selected = fetch_titles(category)
        print(category, len(selected), flush=True)
        titles.update(selected)
    print("Unique Commons file titles:", len(titles), flush=True)
    matches = []
    for row in teams:
        found = [title for title in titles if tolerant_exact(row["club"], title)]
        if found:
            matches.append({**row, "candidate_titles": sorted(found)})
    print("Exact club name matches:", len(matches), flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        metadata = [x for x in pool.map(image_metadata, matches) if x]
        rendered = [x for x in pool.map(render, metadata) if x]
    (ROOT / "manifest.json").write_text(
        json.dumps(rendered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "status.json").write_text(
        json.dumps({"categories": CATEGORIES, "files_searched": len(titles),
                    "club_matches": len(matches), "published": len(rendered)},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PUBLISHED", len(rendered), flush=True)


if __name__ == "__main__":
    main()
