# R132 manager-cycle recovery evidence (2026-09-06)

## Observed failure

R131 saved a real paused checkpoint after the typed player changed from
CharacterID `29037` to manager CharacterID `32904`. The checkpoint itself is
valid (`57,501,846` bytes; SHA-256
`6E85CC496B67B04B4B33AE4CD17416BDD9A735155F3A7179222BDA6F351905F6`),
but it is not a final manager seed. The same run logged
`review_now=RED` and `b1_inactive=RED` before the save. R132 then proved that
waiting one day cannot repair this state: the one-shot handoff carrier had
already failed, and speed 5 advanced from `53147040` to `53147088` between
Python polls. This is a fixture/seed-contract RED, not a product RED.

## Recovery contract

The continuation now treats the R131 checkpoint as an active-cycle source.
It uses the existing native/MCP product timeline driver at speed 5 and stops
only on one paused frame where all four observations agree:

- `review_now_eligible=true`
- `b1_active=false`
- `central_active=false`
- `pp_active=false`

It does not open a new review at that boundary. The normal source-capture
contracts remain frozen to the original player and are not rewritten.
Recovery derives a separate manager-only contract: event key, bounded date,
saved-scope names/types, option shape and selection postcondition remain
mandatory, while old-world non-root character IDs become typed character
requirements and the root is rebound to the current native player. Unknown
events still stop before selection. If PP begins, `zg361pp.9100` uses the real
batch route 1; itemized `zg361pp.146-.191` is not the recovery target.

The acceptance-only manager fixture now retries its eligibility effect every
0.5 seconds after its one-time diagnostic. It never clears product state.
When the complete business gate becomes true, it consumes only its stale
`zga_phase2_manager_seed_handoff_pending` flag, reselects one real direct
reviewable vassal, and opens the existing typed capture event. The runner
then freezes the recovered date as both the maximum and expected event date,
settles paused for at least one second, and uses the existing final
materializer/save-checkpoint path.

## Operational rules retained

- CK3 launch remains serial and exclusive; unrelated static work may run in
  parallel.
- Product timelines default to speed 5. Exact-day evidence must use a native
  paused boundary, never 100 ms Python polling as a date sentinel.
- Do not restart CK3 between scenarios when mounted mod/runtime bytes are
  unchanged and a healthy retained session exists. R132 was already cleaned
  up, so the corrected fixture requires one fresh launch.
- Effect files remain purpose-split: target 1-10 top-level effects, hard
  maximum 20 without a documented live exception. File size is treated as a
  mandatory split defect, not a question deferred until a performance RED.
- Loader evidence and business evidence stay separate. A 303/303 loader
  GREEN cannot promote an invalid manager seed, and a seed-fixture RED cannot
  demote release-identical product bytes without a product diagnostic.

## Static evidence before the next live attempt

The manager fixture, promotion timeline runner and seed-capture runner pass in
both normal Python and `python -O` modes. Live readiness remains pending until
the corrected run produces the exact clean-boundary observation, typed
manager/subject capture, native checkpoint hash and controlled cleanup.
