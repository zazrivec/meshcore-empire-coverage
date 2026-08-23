## Czechia

- [meshcore.cz](https://meshcore.cz/) — main Czech hub.
- [forum.meshcore.website](https://forum.meshcore.website/) — community forum.
- [mapa.meshcore.cz](https://mapa.meshcore.cz/) — network map.
- [pokryti.meshcore.cz](https://pokryti.meshcore.cz/) — coverage map.
- [analyzer.meshcore.cz](https://analyzer.meshcore.cz/) — network analyzer.
- [meshcore.node.cz](https://meshcore.node.cz/) — node information.
- [t.me/meshcore_cz](https://t.me/meshcore_cz) — Telegram group.
- [blog.eischmann.cz — Introduction to MeshCore](https://blog.eischmann.cz/2026/02/15/uvod-do-meshcore/)
- [petanovo.cz — MeshCore, an open-source communication network](https://www.petanovo.cz/meshcore-opensource-komunikacni-sit/)
- [chiptron.cz — MeshCore as an incompatible alternative to Meshtastic, how to set it up](https://chiptron.cz/meshcore-jako-nekompatibilni-alternativa-k-meshtastic-jak-jej-nastavit-abyste-si-mohli-psat/)
- [amaterskeradio.cz — MeshCore vs. Meshtastic](https://amaterskeradio.cz/cs/meshcore-vs-meschtastic/)

The Czech preset (869.432MHz/BW62.5/SF7/CR5, "Czech Republic Narrow") runs on a different frequency than the surrounding SK/HU/NL and AT/DE/SI blocks — see the "Radio parameter breakdown" section above.

**Community-official preset:** `869.432/62.5/SF7/CR5` — [meshcore.cz](https://meshcore.cz/) states this frequency is a deliberate deviation from the default, giving the Czech network its own 10% duty-cycle allowance independent of the rest of the EU/UK block. Match with map data: ✅ yes ({{PCT}}%).

**Command for the network's dominant preset** (~{{PCT}}% of nodes):

```
set radio 869.432,62.5,7,5
```
