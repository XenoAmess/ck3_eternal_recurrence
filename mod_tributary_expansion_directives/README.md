# Tributary Expansion Directives — 驱策朝贡国

This is the development source for the standalone CK3 mod. Formal releases
must be built with `py tools/build_tributary_expansion_directives_release.py`;
this README and the research notes under `docs/` are excluded from Workshop
staging. The formal runtime tree contains 16 files.

The mod lets a player suzerain issue a county-expansion directive to a direct
AI tributary. A valid order costs 150 Prestige. The tributary may refuse, or
accept and immediately declare a dedicated conquest war against the selected
neighbor. An optional war subsidy transfers twelve months of the tributary's
income, clamped to 50–500 Gold, only after a valid acceptance.
