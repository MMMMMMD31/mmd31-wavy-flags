# MMD31 — French National 1 & National 2 2026–2027 club flags

This is an **isolated, verified asset snapshot**. The default branch `main` was not changed.

- 160 new club teams in the offline JSON (49 National 1, 111 National 2).
- **111 clubs** currently have authentic crest-based flags published here.
- **222 PNG files**, exactly one 120 × 96 `standard` and one 120 × 96 `victory` flag per supported club.
- PNG URL convention: `docs/club-flags/national-2627/{n1|n2}/{standard|victory}/{club-slug}.png`
- The remaining **49 clubs** must keep placeholder images until their real badge can be sourced and reviewed. Do not invent URLs or reuse another club's badge.
- Source audit: [crest-audit.json](crest-audit.json).

**Image policy:** real club crests, centered on the dominant badge color; victory flags waved on transparent outer background. Club crests may be trademarks of their owners.

The corresponding complete Dexie JSON is generated from `MMD31_NATIONAL_1_2_2026_27_OFFLINE_COMPLETE_TEST.json`, changing only `flagUrl` and `victoryFlagUrl` in `teams` and `userTeams`. It should be tested using Replace Database on a backup copy before being treated as a working release.

Snapshot source commit: `5847e46fced8a33c5683dae0abfa39e2b602bf33`.
