# Tributary Expansion Directives — 驱策朝贡国

This is the development source for the standalone CK3 mod. Formal releases
must be built with `py tools/build_tributary_expansion_directives_release.py`;
this README and the research notes under `docs/` are excluded from Workshop
staging. The formal runtime tree contains 16 files.

The current source is the **1.0.2 candidate for CK3 1.21.0.3 (Florin)**.
The existing directive, optional subsidy and war-result rules are preserved.
Seven actual stock definitions used by the production/fixture paths are pinned
and checked with the existing validator's explicit `--game-root` option. This
checks source compatibility only; real recipient/title selection, acceptance,
war result, truce direction/expiry and physical Save/Load remain separate.
The canonical Workshop item remains `3801490405`; this candidate is not published.
Historical coverage and failed attempts retain their original build identity.

The mod lets a player suzerain issue a county-expansion directive to a direct
AI tributary. A valid order costs 150 Prestige. The tributary may refuse, or
accept and immediately declare a dedicated conquest war against the selected
neighbor. An optional war subsidy transfers twelve months of the tributary's
income, clamped to 50–500 Gold, only after a valid acceptance.


The historical 1.0.1 / build25734779 record remains in Git and the release changelog; it is not current-machine Florin qualification.
