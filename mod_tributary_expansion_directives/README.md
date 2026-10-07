# Tributary Expansion Directives — 驱策朝贡国

This is the development source for the standalone CK3 mod. Formal releases
must be built with `py tools/build_tributary_expansion_directives_release.py`;
this README and the research notes under `docs/` are excluded from Workshop
staging. The formal runtime tree contains 16 files.

The current source is the **1.0.1 maintenance candidate for CK3 1.20.0.4**.
It updates release metadata while preserving the previous public 1.0.0 gameplay
scripts, nine language files, and thumbnail. CK3 1.20.0.4 live acceptance and
Workshop publication are pending; the compatibility declaration alone is not
live acceptance. The two isolated core/UI inputs and historical coverage gaps
are recorded in
[`docs/ck3-1.20.0.2-tributary-expansion-directives-compatibility-2026-10-01.md`](../docs/ck3-1.20.0.2-tributary-expansion-directives-compatibility-2026-10-01.md).

The mod lets a player suzerain issue a county-expansion directive to a direct
AI tributary. A valid order costs 150 Prestige. The tributary may refuse, or
accept and immediately declare a dedicated conquest war against the selected
neighbor. An optional war subsidy transfers twelve months of the tributary's
income, clamped to 50–500 Gold, only after a valid acceptance.

The 2026-10-07 candidate targets build `25734779`; only the pending runtime descriptor changes. The other 15 runtime files remain exact. Earlier `.3` profiles, Notes and failed attempts are preserved with their original version identity; `.4` live acceptance, the formal tag and publication are pending.
