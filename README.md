# MeshCore Empire Coverage

Analýza rádiových presetov a pokrytia MeshCore repeaterov v 17 krajinách (SK, AT, HU, CZ, DE, SI, PL, IT, CH, BE, NL, LU, UA, DK, HR, RO, GR), postavená na verejných dátach z [map.meshcore.io](https://map.meshcore.io) a [api.meshcore.nz](https://api.meshcore.nz).

Krajina repeatera sa určuje primárne z GPS súradníc (point-in-polygon proti reálnym hraniciam z geoBoundaries.org/OpenStreetMap); prefix v názve (SK-, AT-, ...) sa použije len ako fallback, ak repeater nemá súradnice.

Interaktívna mapa (Leaflet + OpenStreetMap) s klikateľnou legendou presetov — kliknutím na preset ho vypneš/zapneš na mape.

Live stránka: https://zazrivec.github.io/meshcore-empire-coverage/

## Ako to funguje

- `scripts/build.py` — samostatný Python skript (len štandardná knižnica, žiadne
  závislosti), ktorý:
  1. stiahne čerstvý snapshot uzlov z `map.meshcore.io/api/v1/nodes`,
  2. zaradí každý repeater do krajiny (point-in-polygon proti
     `scripts/borders.json`, fallback na prefix v názve ak chýbajú súradnice),
  3. zaradí ho do rádio-preset bucketu podľa reálnych (freq, bw, sf, cr),
  4. dopočíta čerstvosť z `last_advert`,
  5. vyrenderuje `scripts/template.html` (s dátami vloženými ako inline JSON)
     do `index.html` v koreni repa — to je presne to, čo servíruje GitHub Pages.
- `scripts/borders.json` — zjednodušené hranice krajín (z geoBoundaries.org,
  Douglas-Peucker zjednodušenie). Tieto sa nemenia denne, preto sú uložené
  staticky a build ich len číta — nefetchujú sa nanovo pri každom behu.
- `scripts/template.html` — statická HTML/CSS/JS šablóna s placeholdermi
  `__DATA__` (nahradí sa JSON dátami) a `__BUILD_DATE__` (nahradí sa časom
  behu buildu v UTC).

## Ručné spustenie

Vyžaduje len Python 3 (žiadne `pip install`):

```bash
python3 scripts/build.py
```

Tým sa prepíše `index.html` v koreni repa čerstvými dátami. Commit a push
(napr. na GitHub Pages) urob ručne:

```bash
git add index.html
git commit -m "Manual data refresh"
git push
```

Pre kontrolu pred pushnutím stačí otvoriť `index.html` lokálne v prehliadači.

## Automatický build (GitHub Actions)

`.github/workflows/build.yml` spúšťa `scripts/build.py`:

- **Denne** o 04:15 UTC (`cron: '15 4 * * *'`),
- **Na požiadanie** — v GitHub UI: Actions → "Build and deploy coverage
  report" → Run workflow (trigger `workflow_dispatch`).

Workflow po behu skriptu skontroluje, či sa `index.html` skutočne zmenil
(`git diff --cached --quiet`) — ak nie (žiadne nové dáta), nič necommitne.
Ak áno, commitne a pushne priamo do `main`, čím GitHub Pages automaticky
prebuildí live stránku. Beží pod defaultným `GITHUB_TOKEN` (permission
`contents: write` je nastavená v workflow súbore), netreba žiadny ďalší
secret ani PAT.

## Zdroje dát

- `map.meshcore.io/api/v1/nodes` — zoznam uzlov siete (fetchované pri
  každom builde)
- `api.meshcore.nz/api/v1/config` — definície odporúčaných rádio presetov
  (informačný zdroj, použitý pri návrhu preset bucketov v `build.py`; pri
  behu buildu sa už nefetchuje)
- geoBoundaries.org / OpenStreetMap — hranice krajín (`scripts/borders.json`,
  statické) a mapový podklad (Leaflet, dynamicky z OSM tiles)

Dáta sú živý snapshot — čísla sa menia s rastom siete a s každým denným
buildom.
