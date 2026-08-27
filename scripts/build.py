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

The "preset migration" Sankey (see reconcile_flow/build_migration below) is
derived from these same aggregate daily counts, NOT from tracking individual
nodes across days — it's a plausible-minimum-reallocation view of what the
count deltas imply, spanning the same date range as the trend charts.

Output:
    index.html        (repo root — this is what GitHub Pages serves)
    data/YYYY-MM-DD.json   (daily summary snapshot, accumulated over time)

No third-party dependencies — stdlib only, so it runs unmodified in CI.
"""
import json
import re
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
COMMUNITIES_DIR = SCRIPTS_DIR / "communities"
OUTPUT_PATH = REPO_ROOT / "index.html"

# Only the "Community & coordination pages" section is localized — the rest of
# the report (charts, headings, findings) stays Slovak. sk has all 29 country
# files authored directly; en is a full translated fallback for all 29; the
# other languages only translate the countries most relevant to them (see
# scripts/communities/<lang>/ — missing files fall back to en, then sk).
LANGUAGES = ["sk", "en", "de", "hu", "cs", "nl"]
DEFAULT_LANG = "sk"
FALLBACK_LANG = "en"

# The "Zistenia" section mixes two things with very different freshness:
# live numbers (recomputed every build from that day's data) and hand-
# written qualitative analysis/claims (only changes when a human revises
# the text). Bump this manually whenever that prose is edited — it must
# NOT track today's date automatically, or it would falsely imply the
# analysis itself was re-verified on every daily rebuild.
FINDINGS_REVIEWED_DATE = "2026-08-27"

UI_STRINGS = {
    "sk": {
        "lang_name": "Slovenčina",
        "heading": "Komunitné a koordinačné stránky",
        "intro": "Externé, komunitou spravované zdroje pre budovanie a nastavenie MeshCore siete v danej krajine (nie obsah tohto projektu) — hubov, fóra, wiki, mapy. Pokrytie je zámerne postupné; ak vieš o miestnej stránke, ktorá tu chýba, priprav PR do scripts/communities/<jazyk>/<KÓD>.md.",
        "lang_select_label": "Jazyk:",
    },
    "en": {
        "lang_name": "English",
        "heading": "Community & coordination pages",
        "intro": "External, community-maintained resources for building and configuring the MeshCore network in a given country (not content of this project) — hubs, forums, wikis, maps. Coverage is intentionally incremental; if you know of a local page missing here, please open a PR against scripts/communities/<lang>/<CODE>.md.",
        "lang_select_label": "Language:",
    },
    "de": {
        "lang_name": "Deutsch",
        "heading": "Community- und Koordinationsseiten",
        "intro": "Externe, von der Community gepflegte Ressourcen zum Aufbau und zur Konfiguration des MeshCore-Netzwerks im jeweiligen Land (nicht Inhalt dieses Projekts) — Hubs, Foren, Wikis, Karten. Die Abdeckung wächst bewusst schrittweise; wenn du eine hier fehlende lokale Seite kennst, erstelle bitte einen PR gegen scripts/communities/<lang>/<CODE>.md.",
        "lang_select_label": "Sprache:",
    },
    "hu": {
        "lang_name": "Magyar",
        "heading": "Közösségi és koordinációs oldalak",
        "intro": "Külső, a közösség által karbantartott források a MeshCore hálózat kiépítéséhez és beállításához az adott országban (nem ennek a projektnek a tartalma) — közösségi oldalak, fórumok, wikik, térképek. A lefedettség szándékosan fokozatosan bővül; ha ismersz egy itt hiányzó helyi oldalt, kérjük készíts PR-t a scripts/communities/<lang>/<CODE>.md fájlhoz.",
        "lang_select_label": "Nyelv:",
    },
    "cs": {
        "lang_name": "Čeština",
        "heading": "Komunitní a koordinační stránky",
        "intro": "Externí, komunitou spravované zdroje pro budování a nastavení sítě MeshCore v dané zemi (nikoliv obsah tohoto projektu) — huby, fóra, wiki, mapy. Pokrytí je záměrně postupné; pokud víš o místní stránce, která zde chybí, připrav PR do scripts/communities/<lang>/<CODE>.md.",
        "lang_select_label": "Jazyk:",
    },
    "nl": {
        "lang_name": "Nederlands",
        "heading": "Community- en coördinatiepagina's",
        "intro": "Externe, door de community onderhouden bronnen voor het opbouwen en configureren van het MeshCore-netwerk in het betreffende land (geen inhoud van dit project) — hubs, forums, wiki's, kaarten. De dekking groeit bewust stap voor stap; als je een hier ontbrekende lokale pagina kent, maak dan een PR tegen scripts/communities/<lang>/<CODE>.md.",
        "lang_select_label": "Taal:",
    },
}

NEW_KEY = "_new_"        # synthetic source in the migration Sankey: net growth not explained by any shrinking bucket
REMOVED_KEY = "_removed_"  # synthetic target: net shrinkage not absorbed by any growing bucket

COUNTRIES = ["SK", "AT", "HU", "CZ", "DE", "SI", "PL", "IT",
             "CH", "BE", "NL", "LU", "UA", "DK", "HR", "RO", "GR",
             "FR", "LT", "BG", "ES", "PT", "SE", "LV", "IE", "EE", "FI",
             "NO", "GB"]

BUCKET_KEYS = ["sf8cr8", "sf7cr5", "cz_narrow", "sf8cr5", "pl_sf6cr8",
               "eu433", "sf7cr8", "eu_dep", "ib_sf7cr6", "other"]

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
    if freq == 869.618 and bw == 62.5 and sf == 7 and cr == 6:
        return "ib_sf7cr6"
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
    for f in sorted(DATA_DIR.glob("[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].json")):
        try:
            history.append(json.loads(f.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError) as e:
            log(f"skipping unreadable snapshot {f}: {e}")
    history.sort(key=lambda s: s["date"])
    return history


def build_trends(history):
    """Turn the accumulated daily snapshots into compact time series for the
    report: total repeaters per day (overall + per country + per radio-preset
    bucket, summed across all countries) — this is what shows what's growing
    vs. shrinking preset-wise."""
    dates = [h["date"] for h in history]
    grand_total = [h["total_repeaters"] for h in history]

    country_totals = {c: [] for c in COUNTRIES}
    bucket_totals = {k: [] for k in BUCKET_KEYS}
    # Per-country preset trend: countryBucketTotals[country][bucket] = [count per day]
    country_bucket_totals = {c: {k: [] for k in BUCKET_KEYS} for c in COUNTRIES}

    for h in history:
        by_country = h.get("by_country", {})
        for c in COUNTRIES:
            row = by_country.get(c)
            country_totals[c].append(row["total"] if row else 0)
            row_buckets = row["buckets"] if row else {}
            for k in BUCKET_KEYS:
                country_bucket_totals[c][k].append(row_buckets.get(k, 0))
        day_bucket_sums = {k: 0 for k in BUCKET_KEYS}
        for row in by_country.values():
            for k, v in row.get("buckets", {}).items():
                if k in day_bucket_sums:
                    day_bucket_sums[k] += v
        for k in BUCKET_KEYS:
            bucket_totals[k].append(day_bucket_sums[k])

    return {
        "dates": dates,
        "grandTotal": grand_total,
        "countryTotals": country_totals,
        "bucketTotals": bucket_totals,
        "countryBucketTotals": country_bucket_totals,
    }


def reconcile_flow(counts_from, counts_to, bucket_keys):
    """Turn two aggregate bucket-count snapshots (start/end of the tracked
    window) into an IMPLIED minimum-reallocation flow matrix — NOT an
    observed per-node migration (map.meshcore.io/this build don't track
    individual pubkeys across days, only aggregate counts per day). This is
    the same kind of reconciliation used to explain balance-sheet deltas: as
    much as possible is kept on the diagonal (bucket unchanged), remaining
    shrinkage is greedily matched to remaining growth elsewhere, leftover
    shrinkage becomes REMOVED_KEY and leftover growth becomes NEW_KEY.

    Two genuinely different real-world stories can produce an identical pair
    of aggregate snapshots (e.g. simultaneous A->B and B->A churn nets out to
    zero and is invisible here) — this is a lower-bound/plausible-explanation
    view, not a ground truth of who moved where."""
    matrix = {}

    def bump(frm, to, n):
        if n <= 0:
            return
        matrix.setdefault(frm, {})
        matrix[frm][to] = matrix[frm].get(to, 0) + n

    remaining_source = {b: counts_from.get(b, 0) for b in bucket_keys}
    remaining_sink = {b: counts_to.get(b, 0) for b in bucket_keys}

    for b in bucket_keys:
        diag = min(remaining_source[b], remaining_sink[b])
        if diag > 0:
            bump(b, b, diag)
            remaining_source[b] -= diag
            remaining_sink[b] -= diag

    sources = [[b, v] for b, v in remaining_source.items() if v > 0]
    sinks = [[b, v] for b, v in remaining_sink.items() if v > 0]
    i = j = 0
    while i < len(sources) and j < len(sinks):
        sb, sv = sources[i]
        tb, tv = sinks[j]
        n = min(sv, tv)
        bump(sb, tb, n)
        sources[i][1] -= n
        sinks[j][1] -= n
        if sources[i][1] == 0:
            i += 1
        if sinks[j][1] == 0:
            j += 1

    while i < len(sources):
        if sources[i][1] > 0:
            bump(sources[i][0], REMOVED_KEY, sources[i][1])
        i += 1
    while j < len(sinks):
        if sinks[j][1] > 0:
            bump(NEW_KEY, sinks[j][0], sinks[j][1])
        j += 1

    return matrix


def build_migration(trends):
    """Preset-migration Sankey data, spanning the exact same date range as
    the "Trendy podľa presetu" chart (first tracked day -> most recent
    build) — computed purely from the aggregate daily snapshots already in
    data/, via reconcile_flow(). Returns matrix=None if there's under 2 days
    of history yet."""
    dates = trends["dates"]
    if len(dates) < 2:
        return {"matrix": None, "byCountry": {}, "fromDate": None, "toDate": None,
                "bucketKeys": BUCKET_KEYS, "newKey": NEW_KEY, "removedKey": REMOVED_KEY}

    global_from = {k: trends["bucketTotals"][k][0] for k in BUCKET_KEYS}
    global_to = {k: trends["bucketTotals"][k][-1] for k in BUCKET_KEYS}
    global_matrix = reconcile_flow(global_from, global_to, BUCKET_KEYS)

    by_country = {}
    for c in COUNTRIES:
        cbt = trends["countryBucketTotals"].get(c, {})
        c_from = {k: (cbt.get(k) or [0])[0] for k in BUCKET_KEYS}
        c_to = {k: (cbt.get(k) or [0])[-1] for k in BUCKET_KEYS}
        by_country[c] = reconcile_flow(c_from, c_to, BUCKET_KEYS)

    return {
        "matrix": global_matrix,
        "byCountry": by_country,
        "fromDate": dates[0],
        "toDate": dates[-1],
        "bucketKeys": BUCKET_KEYS,
        "newKey": NEW_KEY,
        "removedKey": REMOVED_KEY,
    }


def render_markdown(md_text):
    """Deliberately tiny markdown -> HTML converter: headings (#/##/###),
    unordered lists (- item), **bold**, [text](url) links, ```fenced code
    blocks``` (rendered with a copy-to-clipboard button — see copyCodeBlock()
    in template.html), and paragraphs. NOT a full CommonMark implementation —
    just enough for the hand-authored community pages in
    scripts/communities/. No nested lists."""

    def esc(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def inline(s):
        s = esc(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
        return s

    html_parts = []
    in_list = False
    in_code = False
    code_lines = []
    paragraph_buf = []

    def flush_paragraph():
        if paragraph_buf:
            html_parts.append("<p>" + " ".join(paragraph_buf) + "</p>")
            paragraph_buf.clear()

    def close_list():
        nonlocal in_list
        if in_list:
            html_parts.append("</ul>")
            in_list = False

    lines = md_text.strip("\n").split("\n")
    for raw_line in lines:
        line = raw_line.strip()

        if in_code:
            if line.startswith("```"):
                code_text = esc("\n".join(code_lines))
                html_parts.append(
                    '<div class="code-block-wrap">'
                    '<button type="button" class="copy-btn" onclick="copyCodeBlock(this)" title="Copy" aria-label="Copy">📋</button>'
                    f'<pre><code>{code_text}</code></pre></div>'
                )
                code_lines = []
                in_code = False
            else:
                code_lines.append(raw_line)
            continue

        if line.startswith("```"):
            flush_paragraph()
            close_list()
            in_code = True
            continue

        if not line:
            flush_paragraph()
            close_list()
            continue
        heading = re.match(r"^(#{1,3})\s+(.*)$", line)
        list_item = re.match(r"^[-*]\s+(.*)$", line)
        if heading:
            flush_paragraph()
            close_list()
            level = min(len(heading.group(1)) + 2, 6)  # md h1 -> html h3, stays subordinate to page's own h2s
            html_parts.append(f"<h{level}>{inline(heading.group(2))}</h{level}>")
        elif list_item:
            flush_paragraph()
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            html_parts.append(f"<li>{inline(list_item.group(1))}</li>")
        else:
            close_list()
            paragraph_buf.append(inline(line))

    # Unterminated fence (shouldn't happen in well-formed content) — flush
    # whatever we collected rather than silently dropping it.
    if in_code and code_lines:
        code_text = esc("\n".join(code_lines))
        html_parts.append(
            '<div class="code-block-wrap">'
            '<button type="button" class="copy-btn" onclick="copyCodeBlock(this)" title="Copy" aria-label="Copy">📋</button>'
            f'<pre><code>{code_text}</code></pre></div>'
        )
    flush_paragraph()
    close_list()
    return "\n".join(html_parts)


COUNTRY_NAMES = {
    "sk": {"SK": "Slovensko", "AT": "Rakúsko", "HU": "Maďarsko", "CZ": "Česko", "DE": "Nemecko",
           "SI": "Slovinsko", "PL": "Poľsko", "IT": "Taliansko", "CH": "Švajčiarsko", "BE": "Belgicko",
           "NL": "Holandsko", "LU": "Luxembursko", "UA": "Ukrajina", "DK": "Dánsko", "HR": "Chorvátsko",
           "RO": "Rumunsko", "GR": "Grécko", "FR": "Francúzsko", "LT": "Litva", "BG": "Bulharsko",
           "ES": "Španielsko", "PT": "Portugalsko", "SE": "Švédsko", "LV": "Lotyšsko",
           "IE": "Írsko", "EE": "Estónsko", "FI": "Fínsko", "NO": "Nórsko", "GB": "Spojené kráľovstvo"},
    "en": {"SK": "Slovakia", "AT": "Austria", "HU": "Hungary", "CZ": "Czechia", "DE": "Germany",
           "SI": "Slovenia", "PL": "Poland", "IT": "Italy", "CH": "Switzerland", "BE": "Belgium",
           "NL": "Netherlands", "LU": "Luxembourg", "UA": "Ukraine", "DK": "Denmark", "HR": "Croatia",
           "RO": "Romania", "GR": "Greece", "FR": "France", "LT": "Lithuania", "BG": "Bulgaria",
           "ES": "Spain", "PT": "Portugal", "SE": "Sweden", "LV": "Latvia",
           "IE": "Ireland", "EE": "Estonia", "FI": "Finland", "NO": "Norway", "GB": "United Kingdom"},
    "de": {"SK": "Slowakei", "AT": "Österreich", "HU": "Ungarn", "CZ": "Tschechien", "DE": "Deutschland",
           "SI": "Slowenien", "PL": "Polen", "IT": "Italien", "CH": "Schweiz", "BE": "Belgien",
           "NL": "Niederlande", "LU": "Luxemburg", "UA": "Ukraine", "DK": "Dänemark", "HR": "Kroatien",
           "RO": "Rumänien", "GR": "Griechenland", "FR": "Frankreich", "LT": "Litauen", "BG": "Bulgarien",
           "ES": "Spanien", "PT": "Portugal", "SE": "Schweden", "LV": "Lettland",
           "IE": "Irland", "EE": "Estland", "FI": "Finnland", "NO": "Norwegen", "GB": "Vereinigtes Königreich"},
    "hu": {"SK": "Szlovákia", "AT": "Ausztria", "HU": "Magyarország", "CZ": "Csehország", "DE": "Németország",
           "SI": "Szlovénia", "PL": "Lengyelország", "IT": "Olaszország", "CH": "Svájc", "BE": "Belgium",
           "NL": "Hollandia", "LU": "Luxemburg", "UA": "Ukrajna", "DK": "Dánia", "HR": "Horvátország",
           "RO": "Románia", "GR": "Görögország", "FR": "Franciaország", "LT": "Litvánia", "BG": "Bulgária",
           "ES": "Spanyolország", "PT": "Portugália", "SE": "Svédország", "LV": "Lettország",
           "IE": "Írország", "EE": "Észtország", "FI": "Finnország", "NO": "Norvégia", "GB": "Egyesült Királyság"},
    "cs": {"SK": "Slovensko", "AT": "Rakousko", "HU": "Maďarsko", "CZ": "Česko", "DE": "Německo",
           "SI": "Slovinsko", "PL": "Polsko", "IT": "Itálie", "CH": "Švýcarsko", "BE": "Belgie",
           "NL": "Nizozemsko", "LU": "Lucembursko", "UA": "Ukrajina", "DK": "Dánsko", "HR": "Chorvatsko",
           "RO": "Rumunsko", "GR": "Řecko", "FR": "Francie", "LT": "Litva", "BG": "Bulharsko",
           "ES": "Španělsko", "PT": "Portugalsko", "SE": "Švédsko", "LV": "Lotyšsko",
           "IE": "Irsko", "EE": "Estonsko", "FI": "Finsko", "NO": "Norsko", "GB": "Spojené království"},
    "nl": {"SK": "Slowakije", "AT": "Oostenrijk", "HU": "Hongarije", "CZ": "Tsjechië", "DE": "Duitsland",
           "SI": "Slovenië", "PL": "Polen", "IT": "Italië", "CH": "Zwitserland", "BE": "België",
           "NL": "Nederland", "LU": "Luxemburg", "UA": "Oekraïne", "DK": "Denemarken", "HR": "Kroatië",
           "RO": "Roemenië", "GR": "Griekenland", "FR": "Frankrijk", "LT": "Litouwen", "BG": "Bulgarije",
           "ES": "Spanje", "PT": "Portugal", "SE": "Zweden", "LV": "Letland",
           "IE": "Ierland", "EE": "Estland", "FI": "Finland", "NO": "Noorwegen", "GB": "Verenigd Koninkrijk"},
}


def live_preset_pct(md_text, country, points):
    """Community pages quote a "{{PCT}}% of nodes run this preset" figure.
    Rather than hand-typing a number that goes stale the moment the live
    network shifts, pages contain a `{{PCT}}` placeholder next to the
    `set radio F,BW,SF,CR` command they document; this recomputes the
    match live from the same ≤7-day-fresh points used everywhere else on
    the page (see FILTERS/computeStats('d7') in template.html), so the
    number refreshes on every daily rebuild instead of only when someone
    remembers to edit the markdown."""
    m = re.search(r"set radio\s+([\d.]+),([\d.]+),(\d+),(\d+)", md_text)
    if not m:
        return None
    key = bucket({"freq": m.group(1), "bw": m.group(2), "sf": m.group(3), "cr": m.group(4)})
    fresh = [p for p in points if p["c"] == country and p["ad"] is not None and p["ad"] <= 7]
    sample = fresh if fresh else [p for p in points if p["c"] == country]
    if not sample:
        return None
    match = sum(1 for p in sample if p["b"] == key)
    return round(100 * match / len(sample), 1)


def load_community_bundles(points):
    """Read scripts/communities/<lang>/<CODE>.md for every language x country
    combination. Fallback chain per (lang, code): that language's own file ->
    en/<CODE>.md -> sk/<CODE>.md. Returns {lang: {country_code: html}}, with
    the fallback already resolved (client JS doesn't need its own logic)."""
    raw = {}
    for lang in LANGUAGES:
        lang_dir = COMMUNITIES_DIR / lang
        raw[lang] = {}
        if not lang_dir.exists():
            continue
        for f in lang_dir.glob("*.md"):
            code = f.stem
            if code not in COUNTRIES:
                log(f"skipping scripts/communities/{lang}/{f.name} — {code!r} is not a known country code")
                continue
            text = f.read_text(encoding="utf-8")
            if "{{PCT}}" in text:
                pct = live_preset_pct(text, code, points)
                text = text.replace("{{PCT}}", f"{pct:.1f}" if pct is not None else "?")
            raw[lang][code] = render_markdown(text)

    bundles = {lang: {} for lang in LANGUAGES}
    for lang in LANGUAGES:
        for code in COUNTRIES:
            html = raw[lang].get(code) or raw.get(FALLBACK_LANG, {}).get(code) or raw.get(DEFAULT_LANG, {}).get(code)
            if html is not None:
                bundles[lang][code] = html
    return bundles


def render(points, borders, trends, migration, communities):
    data = {
        "points": points, "borders": borders, "trends": trends, "migration": migration,
        "communities": communities, "communityStrings": UI_STRINGS, "countryNames": COUNTRY_NAMES,
        "languages": LANGUAGES, "defaultLang": DEFAULT_LANG,
    }
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    build_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    html = (template
            .replace("__DATA__", json.dumps(data))
            .replace("__BUILD_DATE__", build_date)
            .replace("__FINDINGS_DATE__", FINDINGS_REVIEWED_DATE))
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

    migration = build_migration(trends)
    if migration["fromDate"]:
        log(f"migration Sankey spans {migration['fromDate']} -> {migration['toDate']} (reconciled from aggregate daily counts)")
    else:
        log("not enough history yet for a migration Sankey (need >=2 days)")

    communities = load_community_bundles(points)
    for lang in LANGUAGES:
        log(f"community bundle '{lang}': {len(communities[lang])}/{len(COUNTRIES)} countries resolved")

    html = render(points, borders, trends, migration, communities)
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    log(f"wrote {OUTPUT_PATH} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
