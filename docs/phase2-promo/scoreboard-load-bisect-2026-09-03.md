# Phase 2 CK3 startup: scoreboard load bisect (2026-09-03)

## Finding

The current product-only launch reaches `>>> Total of : 880` and the
product+fixture launch reaches `>>> Total of : 881`, then spends CPU and grows
to approximately 16.6 GB private memory without reaching `Frontend`.  The
fixture is not required to reproduce the stall.  Scoreboard expansion is a
large changed input, but a no-scoreboard A/B still stalls at roughly 10 GB;
the broader cause is the 279-file projection introduced by the Phase 2/G2
runtime integration.  Scoreboard remains a useful first bisect because its
three generated files are self-contained and easy to swap.

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

`106c6db` is the largest single scoreboard expansion: it adds
`B1_OBJECT_FIELDS` and per-slot/per-route frozen-object projections to the
scoreboard generator.  The generated effects file grows from 9,155 to 72,425
lines and the GUI slot projection grows from 3,210 to 13,374 lines.  In the
same current projection, however, the new workforce/phase3/career/credit
runtime files add roughly 22 MB and hundreds of thousands of script lines.
The no-scoreboard result proves that this broader static parser/load cost must
also be bisected; product-only stalls because CK3 compiles every mounted file
before any fixture event can run.

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

Run `legacy-51-allold` from the group-bisect directory first with the exact
Steam executable/profile/bridge pair already used by the formal startup
harness; it is the actual Aug-30 51-file product.  Then add one group at a
time (`workforce`, `phase3`, `career`, `feedback`, `credit`, `incident`,
`b1`, `manager`, `b2`, and `scoreboard`).  The smaller scoreboard-only
variants in the sibling scoreboard-bisect directory distinguish GUI/effect
pressure.  If the 51-file baseline reaches `Frontend` and any single group
does not, that group is the minimum load blocker.  Do not alter canonical
source until this live A/B confirms the causal boundary.

This report is an evidence ledger only; it does not claim a production/live
fix until a fresh controlled CK3 run reaches `Frontend` and exits cleanly.
