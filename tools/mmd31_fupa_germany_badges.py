#!/usr/bin/env python3
"""Careful German amateur badge discovery on public FuPa club profiles.

No club is accepted from a fuzzy match: the profile's logo alt text must
identify precisely the club (or the real first team of a reserve side).
Respect robots.txt and stagger all profile/image requests.
"""
import argparse
import csv
import hashlib
import io
import json
import re
import time
import unicodedata
import urllib.parse
import urllib.robotparser
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from PIL import Image

from mmd31_commons_germany import draw_image

ROOT = Path("docs/german-clubs-2026-27/fupa-authenticated-20261024")
LIST = Path("tools/mmd31_germany_remaining_531.csv")
BASE = "https://www.fupa.net/club/"
UA = "MMD31-AuthenticCrestAudit/1.0 (https://github.com/MMMMMMD31/mmd31-wavy-flags)"
HEADERS = {"User-Agent": UA, "Accept": "text/html,image/avif,image/webp,image/*,*/*"}


def de_ascii(s):
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        s = s.replace(a, b).replace(a.upper(), b.upper())
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c))


def norm(s):
    s = de_ascii(s).casefold()
    return " ".join(re.findall(r"[a-z0-9]+", s))


def slug(name):
    return "-".join(norm(name).split())


def root_club(name):
    return re.sub(r"\s+(?:II|III|IV|U23|U21|U19|B)$", "", name, flags=re.I)


def robots_allowed(host, url, cache):
    if host not in cache:
        rp = urllib.robotparser.RobotFileParser()
        response = requests.get("https://" + host + "/robots.txt",
                                headers=HEADERS, timeout=20)
        if not response.ok:
            cache[host] = None
        else:
            rp.parse(response.text.splitlines())
            cache[host] = rp
    return cache[host] is not None and cache[host].can_fetch(UA, url)


def candidate_logos(html, expected):
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for tag in soup.find_all("img"):
        alt = tag.get("alt", "")
        match = re.match(r"^\s*(.*?)\s+Vereinswappen\s*$", alt, re.I)
        if not match or norm(match.group(1)) != norm(expected):
            continue
        url = tag.get("src", "")
        if not url.startswith("https://image.fupa.net/club/"):
            continue
        out.append((alt, url))
    return out


def fetch_one(row, robots):
    name = row["club"]
    expected = root_club(name)
    url = BASE + slug(expected)
    if not robots_allowed("www.fupa.net", url, robots):
        return {"teamId": row["teamId"], "club": name,
                "reason": "profile disallowed by robots"}
    try:
        response = requests.get(url, headers=HEADERS, timeout=26)
    except requests.RequestException as exc:
        return {"teamId": row["teamId"], "club": name,
                "reason": type(exc).__name__}
    if response.status_code != 200:
        return {"teamId": row["teamId"], "club": name,
                "reason": f"club profile HTTP {response.status_code}"}
    candidates = candidate_logos(response.text, expected)
    if not candidates:
        return {"teamId": row["teamId"], "club": name,
                "reason": "no precise club-name crest on page"}
    _alt, img_url = candidates[0]
    higher = re.sub(r"/\d+x\d+\.(?:jpeg|jpg|png)$", "/256x256.jpeg",
                    img_url, flags=re.I)
    for source in dict.fromkeys((higher, img_url)):
        if not robots_allowed("image.fupa.net", source, robots):
            return {"teamId": row["teamId"], "club": name,
                    "reason": "image disallowed by robots"}
        try:
            pic = requests.get(source, headers=HEADERS, timeout=25)
            if not pic.ok or len(pic.content) > 4_000_000:
                continue
            original = Image.open(io.BytesIO(pic.content))
            original.verify()
            if min(original.size) < 24:
                continue
            image, rgb = draw_image(pic.content)
            return {"teamId": row["teamId"], "club": name, "source": source,
                    "source_page": response.url, "source_type": "fupa_exact_club_profile",
                    "background_rgb": rgb, "_image": image}
        except Exception:
            continue
    return {"teamId": row["teamId"], "club": name,
            "reason": "crest image unavailable or invalid"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--limit", type=int, default=8)
    args = ap.parse_args()
    ROOT.mkdir(parents=True, exist_ok=True)
    with LIST.open(encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))[args.offset:args.offset + args.limit]
    old_path = ROOT / "manifest.json"
    previous = json.loads(old_path.read_text()) if old_path.exists() else []
    existing = {x["teamId"] for x in previous}
    pending = [x for x in rows if x["teamId"] not in existing]
    robots = {}
    failures, collected = [], []
    for i, row in enumerate(pending, 1):
        try:
            result = fetch_one(row, robots)
        except Exception as exc:
            result = {"teamId": row["teamId"], "club": row["club"],
                      "reason": "unexpected " + type(exc).__name__}
        if "_image" in result:
            image = result.pop("_image")
            path = ROOT / (row["teamId"] + ".png")
            image.save(path, optimize=True)
            result["png_path"] = str(path)
            result["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            collected.append(result)
        else:
            failures.append(result)
        print(f"CHECK {i}/{len(pending)} {row['club']}: "
              f"{'CREST' if 'png_path' in result else result['reason']}",
              flush=True)
        time.sleep(2)
    # Do not accept identical files for unrelated clubs: they may be generic
    # placeholders rather than club-specific emblems.
    by_hash = {}
    for item in collected:
        by_hash.setdefault(item["sha256"], []).append(item)
    generic = {sha for sha, items in by_hash.items()
               if len({norm(root_club(x["club"])) for x in items}) > 1}
    valid = [x for x in collected if x["sha256"] not in generic]
    for x in collected:
        if x["sha256"] in generic:
            failures.append({"teamId": x["teamId"], "club": x["club"],
                             "reason": "duplicate generic badge content"})
            (ROOT / (x["teamId"] + ".png")).unlink(missing_ok=True)
    (ROOT / "manifest.json").write_text(
        json.dumps(previous + valid, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    (ROOT / "status.json").write_text(json.dumps({
        "offset": args.offset, "limit": args.limit, "profiles_checked": len(pending),
        "added": len(valid), "total": len(previous) + len(valid),
        "failed": failures,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PUBLISHED", len(valid), "TOTAL", len(previous) + len(valid),
          "FAILED", len(failures))


if __name__ == "__main__":
    main()
