# Mandala Purge — 肃清曼荼罗伪信

This is the development source for the standalone CK3 mod. Formal releases
must be built with `py tools/build_remove_mandala_release.py`; this README and
all test fixtures are intentionally excluded from Workshop staging.

The 1.0.2 candidate targets CK3 1.21.0 (Florin). Its existing government and
holding rules are retained; the new engine's source dependencies and isolated
business acceptance are checked before publishing to the existing item 3797711947.

With the default-enabled rule active, the mod removes Mandala governments and
Temple Citadel holdings across the whole map. It also redirects every
successful AI Mandala transition through the common government-change hook and
retains recurring event sweeps as a compatibility fallback.

2026-11-18：1.0.2 已完成 CK3 1.21.0 实机与公开更新、完整 Notes、真实缓存加载及离线收尾，见 [永久发布记录](../docs/release-changelogs/remove-mandala/1.0.2.md)。
