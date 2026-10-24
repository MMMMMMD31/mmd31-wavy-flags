#!/usr/bin/env python3
"""Find exact-name German club crests on Wikimedia Commons and publish PNGs.

Only unambiguous filenames naming the club itself are accepted. This utility
does not generate imitation badges or infer a logo from club colours.
"""
from __future__ import annotations

import concurrent.futures
import csv
import hashlib
import io
import json
import re
import time
import unicodedata
from collections import Counter
from pathlib import Path

import cairosvg
import requests
from PIL import Image

REPO_DIR = Path("docs/german-clubs-2026-27/missing-20261024")
LIST = Path("tools/mmd31_remaining_germany_692.csv")
MANIFEST = REPO_DIR / "manifest.json"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "MMD31-ClubCrest-Audit/1.2 (https://github.com/MMMMMMD31/mmd31-wavy-flags)"
WORDS = {"logo", "wappen", "vereinswappen", "vereinslogo", "emblem", "crest", "badge"}


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold()).replace("ß", "ss")
    value = "".join(c for c in value if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9]+", value))


def club_tokens(name: str) -> list[str]:
    tokens = normalized(name).split()
    if tokens[-1:] in (["ii"], ["iii"], ["u23"], ["u21"]):
        tokens.pop()
    return tokens


def title_matches(club: str, file_title: str) -> bool:
    if not file_title.startswith("File:"):
        return False
    name = file_title[5:].rsplit(".", 1)[0]
    tokens = normalized(name).split()
    if any(x in tokens for x in ("historisch", "historical", "alt", "old", "entwurf")):
        return False
    tokens = [x for x in tokens if x not in WORDS]
    target = club_tokens(club)
    return len(target) >= 2 and tokens == target


def fetch_json(params: dict, retries: int = 4) -> dict | None:
    for i in range(retries):
        try:
            response = requests.get(
                COMMONS_API, params={"action": "query", "format": "json", **params},
                headers={"User-Agent": USER_AGENT}, timeout=30,
            )
            if response.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 + 2 * i)
                continue
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError):
            time.sleep(1 + i)
    return None


def find_file(row: dict) -> dict | None:
    """Only select an exactly matching club-name filename in Commons File space."""
    name = row["club"]
    files = {}
    for query in (name + " logo", name):
        found = fetch_json({"list": "search", "srnamespace": 6,
                            "srsearch": query, "srlimit": 25})
        if not found:
            continue
        for result in found.get("query", {}).get("search", []):
            title = result.get("title", "")
            if title_matches(name, title):
                files[title] = True
        if files:
            break
    if not files:
        return None
    titles = sorted(files, key=lambda s: (not s.lower().endswith(".svg"), len(s)))
    result = fetch_json({"prop": "imageinfo", "titles": "|".join(titles[:8]),
                         "iiprop": "url|mime|extmetadata"})
    if not result:
        return None
    candidates = []
    for page in result.get("query", {}).get("pages", {}).values():
        info = (page.get("imageinfo") or [{}])[0]
        url = info.get("url", "")
        mime = info.get("mime", "")
        if not url.startswith("https://upload.wikimedia.org/"):
            continue
        if mime not in ("image/svg+xml", "image/png", "image/jpeg", "image/webp"):
            continue
        meta = info.get("extmetadata", {})
        license_name = meta.get("LicenseShortName", {}).get("value", "Unspecified")
        candidates.append({
            "teamId": row["teamId"], "club": name,
            "source": url, "source_type": "commons_exact_filename",
            "commons_file": page.get("title", ""),
            "license": license_name,
            "source_page": "https://commons.wikimedia.org/wiki/" +
                           page.get("title", "").replace(" ", "_"),
        })
    if not candidates:
        return None
    return sorted(candidates, key=lambda c: (
        not c["source"].lower().endswith(".svg"), len(c["commons_file"])))[0]


def draw_image(source: bytes) -> tuple[Image.Image, list[int]]:
    if b"<svg" in source[:20000].lower():
        source = cairosvg.svg2png(bytestring=source, output_width=480)
    img = Image.open(io.BytesIO(source)).convert("RGBA")
    box = img.getchannel("A").getbbox()
    if not box:
        raise ValueError("No visible logo")
    img = img.crop(box)
    reduced = img.copy()
    reduced.thumbnail((120, 120))
    colors = Counter()
    for red, green, blue, alpha in reduced.getdata():
        if alpha >= 75 and max(red, green, blue) - min(red, green, blue) >= 36:
            colors[(red // 32, green // 32, blue // 32)] += alpha
    if colors:
        rough = colors.most_common(1)[0][0]
        bg = [min(255, int((c * 32 + 16) * .74 + 255 * .26)) for c in rough]
    else:
        bg = [102, 119, 148]
    img.thumbnail((104, 84), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (120, 96), (*bg, 255))
    canvas.alpha_composite(img, ((120 - img.width) // 2, (96 - img.height) // 2))
    return canvas.convert("RGB"), bg


def publish(candidate: dict) -> dict | None:
    try:
        response = requests.get(candidate["source"], headers={"User-Agent": USER_AGENT},
                                timeout=35)
        response.raise_for_status()
        if len(response.content) > 8_000_000:
            return None
        image, color = draw_image(response.content)
        path = REPO_DIR / (candidate["teamId"] + ".png")
        image.save(path, optimize=True)
        candidate["png_path"] = str(path)
        candidate["background_rgb"] = color
        candidate["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        return candidate
    except Exception:
        return None


def main() -> None:
    REPO_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    seen = {str(row["teamId"]) for row in manifest}
    with LIST.open(encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["teamId"] not in seen]
    print(f"Commons exact-title research: {len(rows)} clubs remaining", flush=True)
    candidates = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for index, result in enumerate(pool.map(find_file, rows), 1):
            if result:
                candidates.append(result)
            if index % 50 == 0:
                print(f"Checked {index}/{len(rows)}; exact matches {len(candidates)}",
                      flush=True)
    print(f"Rendering {len(candidates)} sourced crests", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        additions = [item for item in pool.map(publish, candidates) if item]
    merged = manifest + additions
    MANIFEST.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    status = json.loads((REPO_DIR / "status.json").read_text(encoding="utf-8"))
    status["published"] = len(merged)
    status["remaining"] = status["original_missing"] - len(merged)
    status["commons_exact_added"] = len(additions)
    status["commons_checked"] = len(rows)
    (REPO_DIR / "status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2)
                                           + "\n", encoding="utf-8")
    print(json.dumps({"added": len(additions), "total": len(merged),
                      "remaining": status["remaining"]}), flush=True)


if __name__ == "__main__":
    main()
