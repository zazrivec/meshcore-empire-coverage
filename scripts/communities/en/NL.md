## Netherlands

- [localmesh.nl](https://www.localmesh.nl/en/meshcore/) — main Dutch hub.
- [localmesh.nl/community](https://www.localmesh.nl/en/community/) — community.
- [localmesh.nl/meshcore-region-configuration](https://www.localmesh.nl/en/meshcore-region-configuration/) — regional repeater configuration.
- [localmesh.nl/map](https://www.localmesh.nl/en/map/) — coverage map.
- [localmesh.nl/meshcore-performance-tuning](https://www.localmesh.nl/en/meshcore-performance-tuning/) — performance tuning.
- [localmesh.nl/meshcore-repeater-setup](https://www.localmesh.nl/en/meshcore-repeater-setup/) — repeater setup.
- [localmesh.nl/repeaters-wanted](https://www.localmesh.nl/en/repeaters-wanted/) — Repeaters Wanted.

Regional structure based on provinces (Noord-Holland, Zuid-Holland, Utrecht, Gelderland, Brabant...) — a repeater gets the tags `nl` + `nl-<province>` (e.g. `nl-dr` for Drenthe). Coordination happens via the Telegram group.

**Community-official preset:** the mandatory "Netherlands" preset `869.618/62.5/SF7/CR5` — [localmesh.nl](https://www.localmesh.nl/en/meshcore-repeater-setup/) repeatedly stresses that everyone must use it. Match with map data: ✅ yes (66.3% — the shortfall is unmigrated nodes).

**Command for the network's dominant preset** (~66.3% of nodes):

```
set radio 869.618,62.5,7,5
```
