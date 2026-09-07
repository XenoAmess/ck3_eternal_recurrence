# Mandala Purge — 肃清曼荼罗伪信

This is the development source for the standalone CK3 mod. Formal releases
must be built with `py tools/build_remove_mandala_release.py`; this README and
all test fixtures are intentionally excluded from Workshop staging.

With the default-enabled rule active, the mod removes Mandala governments and
Temple Citadel holdings across the whole map. It also redirects every
successful AI Mandala transition through the common government-change hook and
retains recurring event sweeps as a compatibility fallback.
