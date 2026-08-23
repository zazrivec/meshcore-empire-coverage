## Italy

- [meshcoreitalia.it](https://www.meshcoreitalia.it/) — main Italian hub.
- [meshcoreitalia.it/guide](https://www.meshcoreitalia.it/guide/) — guides.
- [meshcoreitalia.it/servizi](https://www.meshcoreitalia.it/servizi/) — services.
- [nodi.meshcoreitalia.it](https://nodi.meshcoreitalia.it/) — node list.
- [livemap.meshcoreitalia.it](https://livemap.meshcoreitalia.it/) — live network map.
- [analyzer.meshcoreitalia.it](https://analyzer.meshcoreitalia.it/) — network analyzer.
- [nexus.meshcoreitalia.it](https://nexus.meshcoreitalia.it/) — nexus/portal.
- [meshcoreitalia.it/news](https://www.meshcoreitalia.it/news/) — news.
- [t.me/meshcoreitalia](https://t.me/meshcoreitalia) — Telegram group.
- [t.me/meshcore_bot](https://t.me/meshcore_bot) — Telegram bot.

**Community-official preset:** the main Italian network recommends "EU/UK Narrow" `869.618/62.5/SF8/CR8` (matches 84.0% of map data), but this isn't an explicitly declared nationwide rule — the main meshcoreitalia.it/guide and /servizi pages don't state it directly.

**Sicily — a separate 433MHz branch:** Sicily (mainly the Catania/Acireale area) has **not entirely switched to 433MHz** — it's a strong local branch descended from an older amateur-radio Meshtastic community around ARI Catania (founder IT9KIV, ~60km link from Tremestieri Etneo to northern Syracuse). Likely reasons: (1) existing 433MHz infrastructure/antennas, (2) 430–440MHz is genuine amateur-radio spectrum (unlike 868MHz), (3) 433MHz has ~6dB less free-space path loss at the same distance and handles terrain better — useful for mountainous Sicily (at the cost of ~2x larger antennas).

Per the current [NEXUS Italia](https://nexus.meshcoreitalia.it/) gateway list, Sicily is **mixed**, not uniform: Acireale (433MHz, active), Caltagirone (868MHz, active), Messina/Messina4 (868MHz and 433MHz, both inactive at last check).

⚠️ **Regulatory note:** without an amateur radio license, only the unlicensed SRD band 433.05–434.79MHz is permitted in Italy on 433MHz, typically capped at 10dBm ERP plus a mandated duty-cycle — simply picking an "EU 433MHz" preset does not by itself guarantee licence compliance, especially with a high-gain antenna.

Further sources: [Community Meshtastic Sicilia @ 433MHz (forum.loraitalia.it)](https://forum.loraitalia.it/d/19-community-meshtastic-sicilia-at-433mhz) · [MeshCore Italia — 433MHz regulatory framework](https://www.meshcoreitalia.it/quadro-normativo-frequenza-433-mhz/) · [MeshCore GitHub issue #125 — Italian amateur radio 433MHz preset request](https://github.com/meshcore-dev/MeshCore/issues/125)

**Command for the network's dominant preset** (~{{PCT}}% of nodes):

```
set radio 869.618,62.5,8,8
```
