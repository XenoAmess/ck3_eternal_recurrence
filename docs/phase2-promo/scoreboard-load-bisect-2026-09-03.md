# Phase 2 CK3 startup: scoreboard load bisect (2026-09-03)

## Finding

The current product-only launch reaches `>>> Total of : 880` and the
product+fixture launch reaches `>>> Total of : 881`, then spends CPU and grows
to approximately 16.6 GB private memory without reaching `Frontend`.  The
fixture is not required to reproduce the stall.  The strongest changed input
is the generated scoreboard projection, not the native bridge or legal gate.

The 2026-08-30 GREEN run used the exact scoreboard blobs from commit
`b5a0b0e` (`Implement phase-two performance case workflow`).  The current
branch accumulated several static expansions afterwards:

| revision | snapshots effect file | scripted-GUI slots | scoreboard GUI |
| --- | ---: | ---: | ---: |
| `b5a0b0e` (Aug 30 GREEN) | 480,700 B | 76,973 B | 704,330 B |
| `cd27d28` | 1,837,786 B | 548,507 B | 861,264 B |
| `ae9a1e7` | 2,770,552 B | 1,056,144 B | 910,567 B |
| `106c6db` | 5,172,933 B | 1,361,031 B | 946,735 B |
| `0bf1a66` (current) | 5,417,763 B | 1,463,854 B | 954,650 B |

`106c6db` is the largest single expansion: it adds `B1_OBJECT_FIELDS` and
per-slot/per-route frozen-object projections to the scoreboard generator.
The generated effects file grows from 9,155 to 72,425 lines (10 to 10
top-level effects, but much larger effect bodies).  The GUI slot projection
grows from 3,210 to 13,374 lines.  This is a static parser/load-cost change;
product-only also stalls because CK3 must compile these files before any
fixture event can run.

## Disposable A/B material

The following directories are outside Git and are safe to delete after the
startup experiment:

`Z:\ck3_mod_rewrite\_runtime\phase2-scoreboard-bisect-20260903\`

`index.json` records four 279-file variants.  All non-scoreboard files are
copied from the current formal product+fixture profile.  The variants are:

* `current`: all current generated scoreboard files.
* `legacy-all`: all three scoreboard files replaced by their `b5a0b0e` blobs.
* `legacy-effects`: only `zg361_generated_scoreboard_snapshots.txt` replaced.
* `legacy-slots-gui`: only `zg361_generated_scoreboard_slots.txt` and
  `gui/zg361_scoreboard.gui` replaced.

The variants are for a single controlled startup bisect.  They are not a
release projection and must not be committed as product content.  Do not
replace canonical source files until a live A/B confirms the causal boundary.

## Recommended order

Run `legacy-all` first with the exact Steam executable/profile/bridge pair
already used by the formal startup harness.  If it reaches `Frontend`, run
`legacy-effects`, then `legacy-slots-gui`; this distinguishes parser pressure
from GUI-only pressure.  If `legacy-all` still stalls, the scoreboard growth
is not sufficient by itself and the next bisect should cover the other
post-`b5a0b0e` generated runtime files.

This report is an evidence ledger only; it does not claim a production/live
fix until a fresh controlled CK3 run reaches `Frontend` and exits cleanly.
