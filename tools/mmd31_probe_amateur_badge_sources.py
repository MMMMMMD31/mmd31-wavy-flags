#!/usr/bin/env python3
"""Read-only, tiny probe of potential public sources for German amateur badges.

Runs only a few request examples and records site/robots access plus candidate
image-link shape. It does not scrape the club catalogue or publish any images.
"""
import json
import re
import time
import urllib.parse
import urllib.robotparser
from pathlib import Path

import requests

ROOT = Path("docs/german-clubs-2026-27/source-probe-20261024")
UA = "MMD31-CrestResearch/1.0 (https://github.com/MMMMMMD31/mmd31-wavy-flags)"
PAGES = [
    "https://www.weltfussball.de/teams/te13259/",
    "https://www.weltfussball.de/teams/te13266/",
    "https://www.weltfussball.de/spielplan/oberliga-schleswig-holstein/",
    "https://www.fupa.net/club/fc-kilia-kiel",
]


def brief(url, response):
    html = response.text
    images = re.findall(r"<img\b[^>]{0,1000}>", html, flags=re.I)
    useful = [
        x for x in images
        if any(z in x.casefold() for z in
               ("wappen", "logo", "kilia", "neum", "hs-data", "club", "team"))
    ]
    candidates = set(re.findall(
        r"https?[^\s\"'<>]{0,220}(?:wappen|logos?)[^\s\"'<>]{0,220}",
        html, flags=re.I,
    ))
    return {
        "url": url, "status": response.status_code,
        "final_url": response.url, "length": len(response.content),
        "page_title": (re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
                       or ["", ""])[1][:150],
        "image_tags": useful[:12],
        "related_links": sorted(candidates)[:14],
        "image_tag_count": len(images),
    }


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    report = []
    robots = {}
    for url in PAGES:
        host = urllib.parse.urlsplit(url).netloc
        if host not in robots:
            rp = urllib.robotparser.RobotFileParser()
            robots_url = "https://" + host + "/robots.txt"
            try:
                r = requests.get(robots_url, headers={"User-Agent": UA}, timeout=16)
                rp.parse(r.text.splitlines()) if r.ok else None
                robots[host] = (rp, r.status_code)
            except Exception as exc:
                robots[host] = (None, str(exc))
        parser, robots_status = robots[host]
        allowed = parser.can_fetch(UA, url) if parser else False
        if not allowed:
            report.append({"url": url, "robots": robots_status,
                           "allowed": False})
            continue
        try:
            response = requests.get(url, headers={"User-Agent": UA}, timeout=24)
            report.append({"robots": robots_status, "allowed": True,
                           **brief(url, response)})
        except Exception as exc:
            report.append({"url": url, "robots": robots_status,
                           "allowed": True, "error": str(exc)})
        time.sleep(2)
    (ROOT / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps([{k: r.get(k) for k in
                       ("url", "robots", "allowed", "status", "image_tag_count")}
                      for r in report], ensure_ascii=False))


if __name__ == "__main__":
    main()
