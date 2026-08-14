#!/usr/bin/env python3
"""
Build script for the MeshCore Empire Coverage report.

Downloads a fresh node snapshot from map.meshcore.io, re-runs the country
assignment (GPS point-in-polygon, prefix fallback) and radio-preset
bucketing, and renders the static index.html served by GitHub Pages.

Usage:
    python3 scripts/build.py

Also writes a small daily snapshot summary to data/YYYY-MM-DD.json (per-country
totals + preset-bucket breakdown, NOT the full point list — kept tiny on
purpose so the history accumulates cheaply in git). On every run it re-reads
the full data/ history and computes trend series (total repeaters per country
per day) that get embedded into the report alongside the current snapshot.

map.meshcore.io itself has no event/history API (verified: /api/v1/nodes is a
full-table dump with no working pagination/since filters, and there is no
per-node advert log) — this daily snapshot is how this project builds its own
trend history over time.

Output:
    index.html        (repo root — this is what GitHub Pages serves)
    data/YYYY-MM-DD.json   (daily summary snapshot, accumulated over time)

No third-party dependencies — stdlib only, so it runs unmodified in CI.
"""
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
DATA_DIR = REPO_ROOT / "data"

NODES_API_URL = "https://map.meshcore.io/api/v1/nodes?short=1"
TEMPLATE_PATH = SCRIPTS_DIR / "template.html"
BORDERS_PATH = SCRIPTS_DIR / "borders.json"
OUTPUT_PATH = REPO_ROOT / "index.html"

COUNTRIES = ["SK", "AT", "HU", "CZ", "DE", "SI", "PL", "IT",
             "CH", "BE", "NL", "LU", "UA", "DK", "HR", "RO", "GR"]

BUCKET_KEYS = ["sf8cr8", "sf7cr5", "cz_narrow", "sf8cr5", "pl_sf6cr8",
               "eu433", "sf7cr8", "eu_dep", "other"]

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


def summarize(points):
    """Tiny per-country / per-bucket count summary — this is what gets
    persisted to data/YYYY-MM-DD.json, not the full point list."""
    by_country = {}
    for c in COUNTRIES:
        by_country[c] = {"total": 0, "buckets": {k: 0 for k in BUCKET_KEYS}}
    for p in points:
        row = by_country.setdefault(p["c"], {"total": 0, "buckets": {k: 0 for k in BUCKET_KEYS}})
        row["total"] += 1
        row["buckets"][p["b"]] = row["buckets"].get(p["b"], 0) + 1
    return {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_repeaters": len(points),
        "by_country": by_country,
    }


def write_daily_snapshot(summary):
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / f"{summary['date']}.json"
    path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    log(f"wrote snapshot {path}")
    return path


def load_history():
    """Read every data/YYYY-MM-DD.json, sorted oldest to newest."""
    if not DATA_DIR.exists():
        return []
    history = []
    for f in sorted(DATA_DIR.glob("*.json")):
        try:
            history.append(json.loads(f.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError) as e:
            log(f"skipping unreadable snapshot {f}: {e}")
    history.sort(key=lambda s: s["date"])
    return history


def build_trends(history):
    """Turn the accumulated daily snapshots into compact time series for the
    report: total repeaters per day (overall + per country)."""
    dates = [h["date"] for h in history]
    grand_total = [h["total_repeaters"] for h in history]
    country_totals = {c: [] for c in COUNTRIES}
    for h in history:
        for c in COUNTRIES:
            row = h.get("by_country", {}).get(c)
            country_totals[c].append(row["total"] if row else 0)
    return {"dates": dates, "grandTotal": grand_total, "countryTotals": country_totals}


def render(points, borders, trends):
    data = {"points": points, "borders": borders, "trends": trends}
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

    summary = summarize(points)
    write_daily_snapshot(summary)

    history = load_history()
    trends = build_trends(history)
    log(f"trend history spans {len(history)} day(s): {trends['dates'][:1]}..{trends['dates'][-1:]}")

    html = render(points, borders, trends)
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    log(f"wrote {OUTPUT_PATH} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
