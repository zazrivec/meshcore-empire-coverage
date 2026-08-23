## Taliansko

- [meshcoreitalia.it](https://www.meshcoreitalia.it/) — hlavný taliansky hub.
- [meshcoreitalia.it/guide](https://www.meshcoreitalia.it/guide/) — návody.
- [meshcoreitalia.it/servizi](https://www.meshcoreitalia.it/servizi/) — služby.
- [nodi.meshcoreitalia.it](https://nodi.meshcoreitalia.it/) — zoznam uzlov.
- [livemap.meshcoreitalia.it](https://livemap.meshcoreitalia.it/) — live mapa siete.
- [analyzer.meshcoreitalia.it](https://analyzer.meshcoreitalia.it/) — analyzátor siete.
- [nexus.meshcoreitalia.it](https://nexus.meshcoreitalia.it/) — nexus/portál.
- [meshcoreitalia.it/news](https://www.meshcoreitalia.it/news/) — novinky.
- [t.me/meshcoreitalia](https://t.me/meshcoreitalia) — Telegram skupina.
- [t.me/meshcore_bot](https://t.me/meshcore_bot) — Telegram bot.

**Oficiálny preset komunity:** hlavná talianska sieť odporúča „EU/UK Narrow" `869.618/62.5/SF8/CR8` (zhoda s 84.0 % dát mapy), no nejde o explicitne vyhlásené celoštátne pravidlo — hlavné stránky meshcoreitalia.it/guide a /servizi ho priamo neuvádzajú.

**Sicília — samostatná 433MHz vetva:** Sicília (najmä okolie Catanie/Acireale) **neprešla celá na 433MHz** — ide o silnú lokálnu vetvu nadväzujúcu na staršiu rádioamatérsku Meshtastic komunitu okolo ARI Catania (zakladateľ IT9KIV, spojenie ~60km Tremestieri Etneo → sever Syrakúz). Dôvody: (1) existujúca 433MHz infraštruktúra/antény, (2) 430–440MHz je skutočné rádioamatérske pásmo (na rozdiel od 868MHz), (3) 433MHz má pri rovnakej vzdialenosti ~6dB menší útlm a lepšie obchádza terén — výhodné pre hornatú Sicíliu (za cenu ~2× väčších antén).

Podľa aktuálneho [NEXUS Italia](https://nexus.meshcoreitalia.it/) zoznamu gatewayov je Sicília **zmiešaná**, nie jednotná: Acireale (433MHz, aktívne), Caltagirone (868MHz, aktívne), Messina/Messina4 (868MHz aj 433MHz, oba neaktívne pri poslednej kontrole).

⚠️ **Regulačné upozornenie:** bez rádioamatérskeho oprávnenia je v Taliansku na 433MHz povolené len bezlicenčné SRD pásmo 433.05–434.79MHz, typicky max. 10dBm ERP + predpísaný duty-cycle — samotná voľba „EU 433MHz" presetu automaticky nezaručuje súlad s licenciou, najmä pri výkonnej anténe.

Ďalšie zdroje: [Community Meshtastic Sicilia @ 433MHz (forum.loraitalia.it)](https://forum.loraitalia.it/d/19-community-meshtastic-sicilia-at-433mhz) · [MeshCore Italia — právny rámec 433MHz](https://www.meshcoreitalia.it/quadro-normativo-frequenza-433-mhz/) · [MeshCore GitHub issue #125 — žiadosť o 433MHz preset](https://github.com/meshcore-dev/MeshCore/issues/125)

**Príkaz pre dominantný preset v sieti** (~84.0% uzlov):

```
set radio 869.618,62.5,8,8
```
