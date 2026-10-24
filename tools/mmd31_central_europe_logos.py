#!/usr/bin/env python3
"""Audit real 2026/27 top-flight badges, publish game-sized PNG assets.

The current-season club lists come from the national league operators. Club
artwork comes from explicitly named FootyLogos download pages, with manually
verified Transfermarkt fallback for the two newly promoted Hungarian clubs.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import time
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from PIL import Image

from mmd31_commons_germany import draw_image


ROOT = Path("docs/central-europe-d1-2026-27/verified")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MMD31/2026-27 badge verification)",
           "Accept": "image/avif,image/webp,image/svg+xml,image/png,image/jpeg,*/*"}
COLLECTIONS = {
    "CZ": "https://www.footylogos.com/competition/chance-liga",
    "SK": "https://www.footylogos.com/competition/nike-liga",
    "HU": "https://www.footylogos.com/competition/nb1-hungary",
}
FEDERATIONS = {
    "CZ": ("Ligová fotbalová asociace (LFA)",
           "https://europeanleagues.com/wp-content/uploads/LFA_01_CMYK_poz.png"),
    "SK": ("Únia ligových klubov (ÚLK)",
           "https://api.sportnet.online/data/ppo/ulk.futbalnet.sk/logo"),
    "HU": ("Magyar Labdarúgó Szövetség (MLSZ)",
           "https://mlsz.jegy.hu/images/articles/valogatottjegy_mlsz_hu/mlsz_logo.png"),
}
CLUBS = {
    "CZ": [
        (1971262000001, "SK Slavia Praha"),
        (1971262000002, "AC Sparta Praha"),
        (1971262000003, "FC Viktoria Plzeň"),
        (1971262000004, "FC Hradec Králové"),
        (1971262000005, "FK Jablonec"),
        (1971262000006, "FC Slovan Liberec"),
        (1971262000007, "SK Sigma Olomouc"),
        (1971262000008, "SK Artis Brno"),
        (1971262000009, "Bohemians Praha 1905"),
        (1971262000010, "FK Teplice"),
        (1971262000011, "FK Mladá Boleslav"),
        (1971262000012, "1. FC Slovácko"),
        (1971262000013, "FC Baník Ostrava"),
        (1971262000014, "FK Pardubice"),
        (1971262000015, "FC Zlín"),
        (1971262000016, "FC Zbrojovka Brno"),
    ],
    "SK": [
        (1971262000101, "ŠK Slovan Bratislava"),
        (1971262000102, "FC DAC 1904 Dunajská Streda"),
        (1971262000103, "FC Spartak Trnava"),
        (1971262000104, "MŠK Žilina"),
        (1971262000105, "MFK Zemplín Michalovce"),
        (1971262000106, "FK Železiarne Podbrezová"),
        (1971262000107, "FC Košice"),
        (1971262000108, "AS Trenčín"),
        (1971262000109, "MFK Skalica"),
        (1971262000110, "MFK Ružomberok"),
        (1971262000111, "KFC Komárno"),
        (1971262000112, "MFK Dukla Banská Bystrica"),
    ],
    "HU": [
        (1971262000201, "Debreceni VSC (DVSC)"),
        (1971262000202, "ETO FC Győr"),
        (1971262000203, "Ferencvárosi TC"),
        (1971262000204, "Kispest-Honvéd FC"),
        (1971262000205, "Kisvárda Master Good"),
        (1971262000206, "MTK Budapest"),
        (1971262000207, "Nyíregyháza Spartacus FC"),
        (1971262000208, "Paksi FC"),
        (1971262000209, "Puskás Akadémia FC"),
        (1971262000210, "Újpest FC"),
        (1971262000211, "Vasas FC"),
        (1971262000212, "ZTE FC (Zalaegerszeg)"),
    ],
}
TRANSFERMARKT_FALLBACK = {"Kispest-Honvéd FC": 709, "Vasas FC": 5378}
ALIASES = {
    "SK Slavia Praha": "Slavia Praha",
    "AC Sparta Praha": "Sparta Praha",
    "FC Viktoria Plzeň": "Viktoria Plzeň",
    "Bohemians Praha 1905": "Bohemians Praha",
    "FC Zlín": "FC Zlin",
    "FC Zbrojovka Brno": "Zbrojovka Brno",
    "1. FC Slovácko": "1 FC Slovácko",
    "FC Baník Ostrava": "FC Banik Ostrava",
    "FC DAC 1904 Dunajská Streda": "DAC 1904 Dunajská Streda",
    "Debreceni VSC (DVSC)": "Debrecen",
    "ETO FC Győr": "Győr",
    "Ferencvárosi TC": "Ferencvaros TC",
    "Kisvárda Master Good": "Kisvárda",
    "Nyíregyháza Spartacus FC": "Nyíregyháza Spartacus",
    "Paksi FC": "Paksi",
    "ZTE FC (Zalaegerszeg)": "ZTE Zalaegerszeg",
}


def norm(s):
    s = unicodedata.normalize("NFKD", s.casefold())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9]+", s))


def get(url):
    r = requests.get(url, headers=HEADERS, timeout=35)
    r.raise_for_status()
    return r


def collection_links(country):
    html = get(COLLECTIONS[country]).text
    soup = BeautifulSoup(html, "html.parser")
    links = {}
    for a in soup.find_all("a", href=True):
        url = urljoin(COLLECTIONS[country], a["href"])
        if not re.match(r"https://www\.footylogos\.com/logos/[^/?#]+$", url):
            continue
        slug = urlparse(url).path.rsplit("/", 1)[-1]
        links[slug] = (norm(a.get_text(" ", strip=True)), url)
    print("COLLECTION", country, len(links), list(links)[:25], flush=True)
    return links


def choose_slug(name, links):
    desired = norm(ALIASES.get(name, name))
    scores = []
    for slug, (label, url) in links.items():
        candidate = norm(slug.replace("-", " "))
        direct = SequenceMatcher(None, desired, candidate).ratio()
        text = SequenceMatcher(None, desired, label).ratio()
        scores.append((max(direct, text), slug, url, label))
    score, slug, url, label = sorted(scores, reverse=True)[0]
    if score < .55:
        raise ValueError(f"ambiguous: target={name!r} match={slug!r} score={score:.2f}")
    return slug, url, score


def source_from_slug(slug):
    page_url = f"https://www.footylogos.com/logos/{slug}"
    soup = BeautifulSoup(get(page_url).text, "html.parser")
    direct = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or ""
        alt = img.get("alt", "").lower()
        if "logo" in alt and "assets.footylogos.com" in src:
            direct.append(urljoin(page_url, src))
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "assets.footylogos.com" in href and ("logo" in href or "png" in href):
            direct.append(urljoin(page_url, href))
    direct.extend([f"https://assets.footylogos.com/logos/{slug}-logo-footylogos.svg",
                   f"https://assets.footylogos.com/logos/{slug}-logo-footylogos.png"])
    errors = []
    for url in dict.fromkeys(direct):
        try:
            result = get(url)
            payload = result.content
            if len(payload) > 7_000_000 or len(payload) < 300:
                raise ValueError("invalid byte count")
            image, bg = draw_image(payload)
            return image, bg, result.url, payload, page_url
        except Exception as e:
            errors.append(str(e)[:110])
    raise ValueError("footylogos download failed: " + " | ".join(errors[:3]))


def source_from_transfermarkt(name):
    club_id = TRANSFERMARKT_FALLBACK[name]
    for size in ("norm", "head"):
        url = f"https://tmssl.akamaized.net/images/wappen/{size}/{club_id}.png"
        try:
            result = get(url)
            payload = result.content
            image, bg = draw_image(payload)
            return image, bg, result.url, payload, f"https://www.transfermarkt.com/verein/{club_id}"
        except Exception as exc:
            print("TRANSFERMARKT RETRY", name, str(exc)[:80], flush=True)
    raise ValueError("no verified Transfermarkt crest for " + name)


def operator_logo(country):
    name, url = FEDERATIONS[country]
    result = get(url)
    payload = result.content
    if b"<svg" in payload[:20000].lower():
        import cairosvg
        payload = cairosvg.svg2png(bytestring=payload, output_width=512)
    image = Image.open(io.BytesIO(payload)).convert("RGBA")
    if not image.getchannel("A").getbbox():
        raise ValueError("blank operator logo")
    image = image.crop(image.getchannel("A").getbbox())
    image.thumbnail((476, 476), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (512, 512), "white")
    canvas.paste(image, ((512-image.width)//2,(512-image.height)//2), image)
    path = ROOT / f"operator-{country.lower()}.png"
    canvas.save(path, optimize=True)
    return {"country":country, "name":name,"source":result.url,"path":str(path),"size":[512,512]}


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    manifests, failures, logos = [], [], []
    for country, clubs in CLUBS.items():
        links = collection_links(country)
        occupied = {}
        for idx, (tid, name) in enumerate(clubs,1):
            try:
                if name in TRANSFERMARKT_FALLBACK:
                    image, bg, source, payload, page_url = source_from_transfermarkt(name)
                    matched = f"transfermarkt/{TRANSFERMARKT_FALLBACK[name]}"
                    score = 1
                else:
                    matched, page_url, score = choose_slug(name, links)
                    if matched in occupied:
                        raise ValueError(f"reused crest page {matched} for {occupied[matched]}")
                    image, bg, source, payload, page_url = source_from_slug(matched)
                    occupied[matched] = name
                if image.size != (120, 96):
                    raise ValueError("incorrect output dimension")
                if len(set(image.resize((28, 22)).getdata())) < 12:
                    raise ValueError("placeholder / flat logo")
                path = ROOT / f"{tid}.png"
                image.save(path, optimize=True)
                manifests.append({"country":country,"teamId":tid,"club":name,
                                  "original_source":source,"profile":page_url,
                                  "matched_slug":matched,"confidence":round(score,3),
                                  "bg_rgb":bg,"raw_sha256":hashlib.sha256(payload).hexdigest(),
                                  "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                                  "path":str(path),"size":[120,96]})
                print(f"OK {country} {idx}/{len(clubs)} {name} {matched}",flush=True)
            except Exception as exc:
                failures.append({"country":country,"teamId":tid,"club":name,
                                 "reason":str(exc)[:550]})
                print("FAILED",country,name,repr(exc),flush=True)
            time.sleep(.2)
        try:
            logos.append(operator_logo(country))
        except Exception as exc:
            failures.append({"country":country,"type":"operator_logo","reason":str(exc)[:550]})
    seen = {}
    for item in manifests:
        digest=item["raw_sha256"]
        if digest in seen:
            failures.append({"teamId":item["teamId"],"reason":f"duplicate raw badge of {seen[digest]}"})
        seen[digest] = item["teamId"]
    status={"expected":sum(map(len,CLUBS.values())), "verified":len(manifests),
            "operator_verified":len(logos),"failures":failures,
            "league_collections":COLLECTIONS,
            "provenance":"Official 2026/27 league lineups; named image pages with raw SHA-256"}
    (ROOT/"manifest.json").write_text(json.dumps(manifests,ensure_ascii=False,indent=2)+"\n")
    (ROOT/"operators.json").write_text(json.dumps(logos,ensure_ascii=False,indent=2)+"\n")
    (ROOT/"status.json").write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n")
    print("FINAL STATUS",json.dumps(status,ensure_ascii=False),flush=True)


if __name__ == "__main__":
    main()
