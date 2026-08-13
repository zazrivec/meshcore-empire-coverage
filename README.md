# MeshCore Empire Coverage

Analýza rádiových presetov a pokrytia MeshCore repeaterov v SK, AT, HU, CZ, DE, SI, PL, IT, CH, BE, NL a LU, postavená na verejných dátach z [map.meshcore.io](https://map.meshcore.io) a [api.meshcore.nz](https://api.meshcore.nz).

Krajina repeatera sa určuje primárne z GPS súradníc (point-in-polygon proti reálnym hraniciam z geoBoundaries.org/OpenStreetMap); prefix v názve (SK-, AT-, ...) sa použije len ako fallback, ak repeater nemá súradnice.

Interaktívna mapa (Leaflet + OpenStreetMap) s klikateľnou legendou presetov — kliknutím na preset ho vypneš/zapneš na mape.

Live stránka: https://zazrivec.github.io/meshcore-empire-coverage/

Zdroje dát:
- `map.meshcore.io/api/v1/nodes` — zoznam uzlov siete
- `api.meshcore.nz/api/v1/config` — definície odporúčaných rádio presetov
- geoBoundaries.org / OpenStreetMap — hranice krajín a mapový podklad (Leaflet)

Snapshot dát je z 2026-08-13, čísla sa menia s rastom siete.
