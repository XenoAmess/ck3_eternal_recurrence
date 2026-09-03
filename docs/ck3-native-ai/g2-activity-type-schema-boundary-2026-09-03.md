# G2 activity-type schema boundary (2026-09-03)

## What was completed

This bounded package freezes the currently authored Jingcha activity surface
as a file-only inventory.  It records the source hash, UTF-8 BOM, root key and
27 direct child keys in
`ck3_autonomous_player/native_bridge/research/fixtures/g2_activity_type_schema_boundary_v1.json`.
The companion test uses a tiny brace-depth inventory scanner; it does not try
to parse CK3 activity semantics or assign an opcode to any key.

The root activity's `ai_will_do = { value = 0 }` is recorded as an authoring
intent for the player-facing UI.  It is not presented as a runtime proof that
CK3's AI can never reach an activity path.

## Current boundary

The matching `open_kaishek` preflight boundary remains parser `GREEN` and
validator `RED` with `UNKNOWN_OPCODE` diagnostics for the activity corpus.
The profile does not yet bind activity-type schema, and this package does not
add an allow-list entry, native capability, action step, or readiness bit.
No CK3 process was started, no save was changed, and no mutation was sent.

This is consistent with the broader activity boundary in
[`g2-open-kaishek-activity-schema-red-2026-09-03.md`](g2-open-kaishek-activity-schema-red-2026-09-03.md):
the keys `province_filter`, `phases`, `on_start`, `on_complete`, `ai_will_do`
and `guest_invite_rules` need exact-build ownership, scope and evaluation-time
evidence before a profile change is justified.

## Next admissible step

Freeze the exact CK3 activity-type data for build `1.19.0.6`, then map the
observed top-level keys to native scope and evaluation phases.  Only after
those facts agree should a read-only schema fixture be added.  Until then,
activity planning/joining remains `activity_action_ready=false` and G2's
existing truce/war-bound readiness gates are unchanged.

## Reproduction

```powershell
$env:PYTHONPATH = 'ck3_autonomous_player/src'
& 'Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe' -m pytest -q --disable-warnings `
  ck3_autonomous_player/tests/unit/test_g2_activity_type_schema_boundary.py
```
