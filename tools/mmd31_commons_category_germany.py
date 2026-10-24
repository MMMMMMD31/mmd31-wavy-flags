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
    "Category:Logos of sports clubs in Germany",
    "Category:SVG sports logos of Germany",
    "Category:DJK-Sportverein",
)

# Manually reviewed aliases for file names that use a club's official longer
# legal name, year of foundation, normalized transliteration, or local shorthand.
# No approximate/fuzzy matches are ever applied automatically.
CURATED_ALIASES = {
    "1898200000026": "File:ESC Geestemünde logo.png",
    "1898200000118": "File:Siegburger SV Logo.svg",
    "1898200000119": "File:VfL 08 Vichttal Logo.svg",
    "1898200000120": "File:SSV Merten 1925 Logo.png",
    "1898200000150": "File:TSV Victoria Clarholz Logo.svg",
    "1898200000186": "File:FC-Holzhausen (Logo, 2024).png",
    "1898200000189": "File:FC 1931 Eddersheim Logo.svg",
    "1898200000245": "File:1. FC Amberg.png",
    "1898200000276": "File:Logo TSV Nbg Buch.png",
    "1898200000313": "File:FC Sonthofen logo.png",
    "1898200000331": "File:Arminia Ludwigshafen.gif",
    "1898200000346": "File:VfR Baumholder logo.png",
    "1898200000356": "File:SV Viktoria Goch Logo.svg",
    "1898200000359": "File:VfB Speldorf.svg",
    "1898200000374": "File:SC Kapellen-Erft.png",
    "1898200000375": "File:DJK Neuss-Gnadental.png",
    "1898200000390": "File:VfB Merseburg Logo.png",
    "1898200000402": "File:Logo Deutz 05.svg",
    "1898200000425": "File:SV Helpenstein Logo.png",
    "1898200000427": "File:Union Schafhausen Logo.svg",
    "1898200000429": "File:Sportfreunde Uevekoven Logo.svg",
    "1898200000438": "File:FV 09 Schwalbach.png",
    "1898200000442": "File:Spvgg Quierschied Wappen.png",
    "1898200000443": "File:Sc reisbach logo.jpg",
    "1898200000451": "File:BSG Stahl Brandenburg Logo 2022.svg",
    "1898200000472": "File:VfB Fortuna Biesdorf Logo.png",
    "1898200000500": "File:1. Suhler SV 06.svg",
    "1898200000506": "File:FC Oberlausitz Neugersdorf.svg",
    "1898200000519": "File:SuS Neuenkirchen Logo.png",
    "1898200000546": "File:SG Finnentrop Bamenohl Logo.svg",
    "1898200000559": "File:VfB Friedrichshafen logo.svg",
    "1898200000560": "File:Calcio Leinfelden-Echterdingen (Logo).png",
    "1898200000561": "File:FC-Rottenburg Vereinswappen.svg",
    "1898200000562": "File:SKV Rutesheim emblem.svg",
    "1898200000580": "File:FC Denzlingen Wappen.png",
    "1898200000602": "File:MSV Pampow Logo.png",
    "1898200000620": "File:OSC Vellmar.gif",
    "1898200000629": "File:SC Waldgirmes.svg",
    "1898200000633": "File:Wappen FV Biebrich 02.png",
    "1898200000660": "File:SpVgg 03 Neu-Isenburg Logo.gif",
    "1898200000678": "File:Germania Schnelsen Logo.png",
    "1898200000692": "File:Meiendorfer SV 1949.gif",
    "1898200000727": "File:Offizielles Wappen des 1. SC Göttingen 05.svg",
    "1898200000737": "File:SVG Göttingen Logo.png",
    "1898200000756": "File:SG 74 Hannover logo.svg",
    "1898200000761": "File:SV Ahlerstedt-Ottendorf.gif",
    "1898200000774": "File:Sv eintracht nordhorn.svg",
    "1898200000821": "File:VfB Linz Logo.svg",
    "1898200000404": "File:SSV Homburg-Nuembrecht Logo.png",
    "1898200000504": "File:FV-Dresden-06-Laubegast2.gif",
    "1898200000129": "File:FSV Neunkirchen-Seelscheid Logo.svg",
    "1898200000337": "File:Eintracht Bad Kreuznach logo.svg",
    "1898200000059": "File:Schwarz-Weiß Rehden.svg",
    "1898200000306": "File:Wappen des SV Planegg-Krailling e.V..png",
    "1898200000022": "File:BTS Neustadt hochauflösendes Logo.png",
    "1898200000228": "File:Pfaffenhofen-Ilm FSV 1919.jpg",
    "1898200000348": "File:ASV Einigkeit Süchteln.gif",
    "1898200000492": "File:SV Blau-Weiß 91 Bad Frankenhausen logo.png",
    "1898200000664": "File:Logo Alsterbrüder, Hamburg.png",
    "1898200000699": "File:Wappen der SGG Rot-Schwarz Kiel.gif",
    "1898200000066": "File:VfV Hildesheim Logo.svg",
}


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
    previous_manifest = ROOT / "manifest.json"
    already_published = (
        json.loads(previous_manifest.read_text(encoding="utf-8"))
        if previous_manifest.exists() else []
    )
    previous_ids = {str(x["teamId"]) for x in already_published}
    with SOURCE_CSV.open(encoding="utf-8-sig", newline="") as file:
        teams = [x for x in csv.DictReader(file) if x["teamId"] not in skip]
    titles = set()
    for category in CATEGORIES:
        selected = fetch_titles(category)
        print(category, len(selected), flush=True)
        titles.update(selected)
    print("Unique Commons file titles:", len(titles), flush=True)
    (ROOT / "catalog_titles.json").write_text(
        json.dumps(sorted(titles), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    matches = []
    for row in teams:
        found = [title for title in titles if tolerant_exact(row["club"], title)]
        alias = CURATED_ALIASES.get(row["teamId"])
        if alias in titles and alias not in found:
            found.append(alias)
        if found:
            matches.append({**row, "candidate_titles": sorted(found)})
    print("Exact club name matches:", len(matches), flush=True)
    new_matches = [x for x in matches if x["teamId"] not in previous_ids]
    print("Matches not yet published:", len(new_matches), flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        metadata = [x for x in pool.map(image_metadata, new_matches) if x]
        rendered = [x for x in pool.map(render, metadata) if x]
    combined = already_published + rendered
    (ROOT / "manifest.json").write_text(
        json.dumps(combined, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "status.json").write_text(
        json.dumps({"categories": CATEGORIES, "files_searched": len(titles),
                    "club_matches": len(matches), "added_this_run": len(rendered),
                    "published": len(combined)},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PUBLISHED", len(combined), "ADDED", len(rendered), flush=True)


if __name__ == "__main__":
    main()
