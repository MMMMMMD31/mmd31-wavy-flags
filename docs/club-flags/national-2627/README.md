# MMD31 — French National 1 & National 2 (2026–27)

## IMPORTANT: Test branch, incomplete crest collection

The 2026/27 federation renamed its divisions: National 1 (level 4, formerly National 2) has three groups of 16; National 2 (level 5, formerly National 3) has eight groups of 14.

- `roster.txt`: 160 teams, ordered by official 2026/27 geographic groups.
- `build.py`: formats each **sourced real club crest** as a 120×96 PNG on a dominant-color field, plus a 120×96 transparent wavy Victory PNG.
- `n1/standard/`, `n1/victory/`, `n2/standard/`, `n2/victory/`: verified published assets, not a promise that all 160 exist yet.
- `crest-audit.json`: provenance and `status` per team. The latest reviewed snapshot confirms 110 real sourced crest pairs (220 PNGs). 50 identities still lack sufficiently validated crests and are deliberately not assigned other clubs' badges.
- Beware similarly named rugby clubs and opponent logos shown on web match pages; the render script is intentionally conservative.

**Never reference an unverified GitHub PNG in a game save.** The compatible MMD31 test JSON uses published PNGs for the 110 verified clubs and the original game placeholder for the remaining 50.

The official 2026–27 groups are detailed at https://www.fff.fr/article/17102-les-groupes-pour-la-saison-2026-2027.html

The archive is a test dataset. Team Elo/attributes are provisional estimates on the existing MMD31 scale, not verified match-by-match Elo or independent academy scores. The new stages still require an in-game simulation test, especially promotions and relegations, before production use.
