# Interactive Steam startup context discovery

Source task: [More Tenets Slots migration plan](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/master/docs/migration-plan-2026-11-18.md). Ownership: the startup URL shape and background Steam state probe are shared infrastructure; product source and migration results stay in the independent repository.

On `machine_id: pc-20260924rtuf-f11af23c08`, the normally restarted Steam client `11.23.65.88` exposed its owned `SharedJSContext` with the already qualified `steamui/sp.js` (16,224,005 bytes, SHA-256 `4b818cd371388e06c66fe8c0bb592b7dfd4a6fb55eb56844d1b360b64aec3046`). Its interactive startup query omitted `SILENT_STARTUP`. The probe incorrectly required that field, returning `context_unavailable` after the native provider correctly declined to qualify an online zero sample.

The existing discovery now accepts the same exact required startup fields with an optional boolean `SILENT_STARTUP`. No getter, native offset, source qualification or ownership check changed. A regression exercises the actual `target_candidates` consumer for interactive and both explicit silent forms. All 22 probe tests and strict mypy for the complete modified production module passed.

At `2026-11-18T16:00:01.514590Z`, the actual background probe returned `status=online / offline_mode=false`, method `cef_app_getters`, current Steam PID19844 and owned helper PID19248. Both fixed getters agreed; this is state observation, not proof of download completion, account occupancy or product acceptance. Raw before/after receipts remain in the independent task's ignored `artifacts/upgrade-20261118/` directory, subject to its retention policy. The initial unavailable result remains preserved.
