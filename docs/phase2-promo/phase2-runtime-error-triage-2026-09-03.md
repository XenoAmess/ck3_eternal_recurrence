# Phase 2 CK3 runtime-error triage (2026-09-03)

## Scope

This is an offline evidence ledger for the Phase 2 launch investigation.  The
triage read the archived `error.log`/`debug.log` files and the group/scoreboard
bisect indexes.  It did **not** launch CK3, modify a projection runner, or
modify the ZhongGuo source tree.

## Evidence

| Run / artifact | `error.log` result | Startup boundary observed |
|---|---|---|
| `Z:\ck3_mod_rewrite\_runtime\formal-phase2-product-fixture-release-20260903-rerun` | 0 bytes | Custom events load and `onaction.cpp` reports `Total of : 881`; no `Start loading of history`, `Frontend`, or startup-duration marker before the harness timeout. |
| `Z:\ck3_mod_rewrite\_runtime\phase2-product-only-fullwarm-nosave-nobridge-20260903` | 0 bytes | Product-only load reaches `Total of : 880`; no parser error is recorded before timeout. |
| `Z:\ck3_mod_rewrite\_runtime\formal-phase2-legacy51-20260903` | 1,778 bytes, eight entries | Despite the fixture diagnostics below, the process reaches `Start loading of history`, `Frontend`, `End loading of history`, and `Total startup duration: 51.726461`; report records `result: frontend` and process exit `0`. |
| `Z:\ck3_mod_rewrite\_runtime\formal-phase2-legacy51-currentbridge-20260903` | Same eight fixture entries | Reaches `Frontend` and exits `0`; startup duration is `49.063801` seconds. |
| `Z:\ck3_mod_rewrite\_runtime\formal-phase2-product-noscoreboard-20260903` | Six unknown-effect entries | This is an intentionally incomplete A/B overlay: scoreboard provider files were removed while callers in `zg361_effects.txt` were retained. |

The current ZhongGuo static validator also passes without writing files:

```text
py mod_zhongguo_style/tools/validate_local.py
GREEN: mod_zhongguo_style static checks passed
```

## Interpretation of the diagnostics

### Legacy 51-file fixture

The legacy fixture `events/zga_phase2_seed_events.txt` invokes
`zg361_b1_open_cycle_effect` and `zg361_ip_open_x_case_effect`, but the
legacy-51 projection intentionally does not mount the newer B1/IP/Workforce
effect providers.  CK3 consequently reports the two unknown effects and
cascade messages (`else/else_if not following...` and `Unexpected token...`).
The same projection still reaches `Frontend` and exits cleanly, so these are
projection/fixture dependency diagnostics, not evidence that the base CK3
startup is blocked.

The repeated warnings that
`zg361_scoreboard_managed_owner` and `zg361_scoreboard_managed_n` are set but
unused are likewise emitted by the reduced projection and do not stop startup.

### No-scoreboard A/B

The six unknown effects are exactly the scoreboard update helpers removed for
that A/B (`zg361_patch_scoreboard_b1_post_mark_effect`,
`zg361_update_settled_325_scoreboard_slots_effect`,
`zg361_update_regraded_scoreboard_slots_effect`,
`zg361_clear_scoreboard_m_slots_effect`,
`zg361_write_managed_scoreboard_slot_effect`, and
`zg361_copy_received_scoreboard_slots_effect`).  They are expected when their
providers are deliberately omitted; adding stubs or changing canonical
callers would invalidate the experiment and could create duplicate definitions
in the full product.

### Current broad product

Both current broad runs have an empty `error.log`, and their debug logs stop
after the on-action table is built (`880`/`881`).  There is therefore no
observed current-product parse or unknown-effect error to fix.  The group
bisect index instead shows a 279-file, 29,351,046-byte projection versus the
51-file, 7,137,587-byte baseline; the archived evidence supports treating the
current boundary as a load/working-set bottleneck until a controlled group
reintroduction run proves otherwise.

## Decision

No source patch is justified by the captured runtime evidence.  In particular,
do not add missing-effect stubs, alter the seed fixture, or shrink generated
scoreboard files in the canonical tree based solely on these reduced
projections.  Continue with controlled projection/group A/B work and retain
the archived logs as the failure boundary.  This report intentionally records
`no change` rather than claiming a speculative fix.

