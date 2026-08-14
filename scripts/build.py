#!/usr/bin/env python3
"""
Build script for the MeshCore Empire Coverage report.

Downloads a fresh node snapshot from map.meshcore.io, re-runs the country
assignment (GPS point-in-polygon, prefix fallback) and radio-preset
bucketing, and renders the static index.html served by GitHub Pages.

Usage:
    python3 scripts/build.py

Output:
    index.html   (repo root — this is what GitHub Pages serves)

No third-party dependencies — stdlib only, so it runs unmodified in CI.
"""
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent

NODES_API_URL = "https://map.meshcore.io/api/v1/nodes?short=1"
TEMPLATE_PATH = SCRIPTS_DIR / "template.html"
BORDERS_PATH = SCRIPTS_DIR / "borders.json"
OUTPUT_PATH = REPO_ROOT / "index.html"

COUNTRIES = ["SK", "AT", "HU", "CZ", "DE", "SI", "PL", "IT",
             "CH", "BE", "NL", "LU", "UA", "DK", "HR", "RO", "GR"]

REPEATER_TYPE = 2


def log(msg):
    print(f"[build] {msg}", file=sys.stderr)


def fetch_json(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "meshcore-empire-coverage-build/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def norm(x):
    try:
        return round(float(x), 3)
    except (TypeError, ValueError):
        return None


def bucket(params):
    if not params:
        return "other"
    freq = norm(params.get("freq"))
    bw = norm(params.get("bw"))
    try:
        sf = int(params.get("sf"))
        cr = int(params.get("cr"))
    except (TypeError, ValueError):
        return "other"
    if freq is not None and freq < 800:
        return "eu433"
    if freq == 869.618 and bw == 62.5 and sf == 8 and cr == 8:
        return "sf8cr8"
    if freq == 869.618 and bw == 62.5 and sf == 7 and cr == 5:
        return "sf7cr5"
    if freq == 869.432 and bw == 62.5 and sf == 7 and cr == 5:
        return "cz_narrow"
    if freq == 869.618 and bw == 62.5 and sf == 8 and cr == 5:
        return "sf8cr5"
    if freq == 869.618 and bw == 62.5 and sf == 6 and cr == 8:
        return "pl_sf6cr8"
    if freq == 869.618 and bw == 62.5 and sf == 7 and cr == 8:
        return "sf7cr8"
    if freq == 869.525 and bw == 250.0 and sf == 11 and cr == 5:
        return "eu_dep"
    return "other"


def point_in_ring(x, y, ring):
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-15) + xi):
            inside = not inside
        j = i
    return inside


def build_bbox_index(borders):
    bbox = {}
    for code in COUNTRIES:
        rings = borders[code]
        lons = [pt[0] for r in rings for pt in r]
        lats = [pt[1] for r in rings for pt in r]
        bbox[code] = (min(lons) - 0.05, max(lons) + 0.05, min(lats) - 0.05, max(lats) + 0.05)
    return bbox


def geo_country(lon, lat, borders, bbox):
    for code in COUNTRIES:
        min_lon, max_lon, min_lat, max_lat = bbox[code]
        if min_lon <= lon <= max_lon and min_lat <= lat <= max_lat:
            for ring in borders[code]:
                if point_in_ring(lon, lat, ring):
                    return code
    return None


def prefix_country(name):
    n = (name or "").upper()
    for code in COUNTRIES:
        if n.startswith(code + "-"):
            return code
    return None


def build_points(nodes, borders, bbox):
    now = datetime.now(timezone.utc)
    wide_min_lon = min(b[0] for b in bbox.values())
    wide_max_lon = max(b[1] for b in bbox.values())
    wide_min_lat = min(b[2] for b in bbox.values())
    wide_max_lat = max(b[3] for b in bbox.values())

    points = []
    for n in nodes:
        if n.get("type") != REPEATER_TYPE:
            continue
        lat = n.get("adv_lat")
        lon = n.get("adv_lon")
        name = n.get("adv_name", "")
        assigned = None

        if lat is not None and lon is not None:
            if wide_min_lon <= lon <= wide_max_lon and wide_min_lat <= lat <= wide_max_lat:
                assigned = geo_country(lon, lat, borders, bbox)
        else:
            assigned = prefix_country(name)

        if assigned is None:
            continue

        last_advert = n.get("last_advert")
        advert_age_days = None
        if last_advert:
            dt = datetime.fromisoformat(last_advert.replace("Z", "+00:00"))
            advert_age_days = round((now - dt).total_seconds() / 86400, 2)

        points.append({
            "lat": lat,
            "lon": lon,
            "name": name,
            "c": assigned,
            "b": bucket(n.get("params")),
            "ad": advert_age_days,
        })
    return points


def render(points, borders):
    data = {"points": points, "borders": borders}
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    build_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    html = template.replace("__DATA__", json.dumps(data)).replace("__BUILD_DATE__", build_date)
    return html


def main():
    log(f"fetching node snapshot from {NODES_API_URL}")
    nodes = fetch_json(NODES_API_URL)
    log(f"got {len(nodes)} total nodes")

    borders = json.loads(BORDERS_PATH.read_text(encoding="utf-8"))
    bbox = build_bbox_index(borders)

    points = build_points(nodes, borders, bbox)
    log(f"assigned {len(points)} repeaters across {len(COUNTRIES)} countries")

    html = render(points, borders)
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    log(f"wrote {OUTPUT_PATH} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
