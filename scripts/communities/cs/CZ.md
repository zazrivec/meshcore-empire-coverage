## Česko

- [meshcore.cz](https://meshcore.cz/) — hlavní český hub.
- [forum.meshcore.website](https://forum.meshcore.website/) — komunitní fórum.
- [mapa.meshcore.cz](https://mapa.meshcore.cz/) — mapa sítě.
- [pokryti.meshcore.cz](https://pokryti.meshcore.cz/) — mapa pokrytí.
- [analyzer.meshcore.cz](https://analyzer.meshcore.cz/) — analyzátor sítě.
- [meshcore.node.cz](https://meshcore.node.cz/) — informace o uzlech.
- [t.me/meshcore_cz](https://t.me/meshcore_cz) — Telegram skupina.
- [blog.eischmann.cz — Úvod do MeshCore](https://blog.eischmann.cz/2026/02/15/uvod-do-meshcore/)
- [petanovo.cz — MeshCore, opensource komunikační síť](https://www.petanovo.cz/meshcore-opensource-komunikacni-sit/)
- [chiptron.cz — MeshCore jako nekompatibilní alternativa k Meshtastic, jak jej nastavit](https://chiptron.cz/meshcore-jako-nekompatibilni-alternativa-k-meshtastic-jak-jej-nastavit-abyste-si-mohli-psat/)
- [amaterskeradio.cz — MeshCore vs. Meshtastic](https://amaterskeradio.cz/cs/meshcore-vs-meschtastic/)

Český preset (869.432MHz/BW62.5/SF7/CR5, "Czech Republic Narrow") běží na jiné frekvenci než okolní SK/HU/NL i AT/DE/SI blok — viz sekci "Rozdělení rádiových parametrů" výše.

**Oficiální preset komunity:** `869.432/62.5/SF7/CR5` — [meshcore.cz](https://meshcore.cz/) uvádí tuto frekvenci jako záměrnou odchylku od standardu, aby síť získala vlastní 10% duty-cycle limit v ČR nezávislý na zbytku EU/UK bloku. Shoda s daty mapy: ✅ ano ({{PCT}}%).

**Příkaz pro dominantní preset v síti** (~{{PCT}}% uzlů):

```
set radio 869.432,62.5,7,5
```
