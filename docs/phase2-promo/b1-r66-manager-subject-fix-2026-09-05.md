# R66 B1 dual-role identity fix — 2026-09-05

Status: `static-ready / production-live-pending`. This package did not start
or attach CK3. Root owns the next frozen candidate and live gate; no commit
was made by this package.

## Observed failure, not a speculative collision

Frozen `Z:\b3r66\cell\final_debug.log` lines 4139 onward identify player
Character `29037` as both an active manager and the emperor's subject:

- 11:15:16: own manager cycle/case/state `19/19/1`; incoming subject `1/1`.
- 11:15:18: the same character's shared cycle/case is now `1/1`; incoming `2/2`.
- 11:16:25 (`.100`, line 4599): saved ticket `17/17/1` versus current `2/2/1`.

The first two writes prove the actual-use field collision. They do **not**
prove ticket 17 was the latest valid manager ticket: manager-only historical
witnesses, not the queued ticket or overwritten subject fields, determine
migration. A genuinely stale ticket must remain stale.

The real path is superior `open_cycle` → per-subject `initialize_subject_case`
while the subject has its own active manager cycle → manager delayed `.100`.
This also ran in the reverse direction before the fix: a manager increment
could overwrite its identity as a subject in its superior's cohort.

R66 `final_error.log` line 14144 onward separately records unset
`capital_county` from `finalize_subject_facts` through `open_shadow` →
`run_review` → `.102`. Root's same-run diagnostic also located Character
`45425`'s unavailable weak reference being read repeatedly downstream of
`.102`; reusing the existing availability prune at that entry is the limited
fix. These are business failures, not global error-count inference.

## Production changes and ownership

| Role / path | Current serial fields |
| --- | --- |
| Manager opener, stage tickets, policy debt, quota/calibration/publication | `zg361_b1_manager_cycle_serial`, `zg361_b1_manager_case_serial` |
| Subject initializer, self/shadow/peer, pending deadline, subject facts/results | Existing `zg361_b1_cycle_serial`, `zg361_b1_case_serial` |
| Mixed subject-list / owner comparison | Subject old field on the left, manager new field on the right |
| Central publication hook, frozen tuple, pump, delayed manager continuation | New manager fields |
| B2 KPI owner-side source and Incident expected/cohort source | New manager fields; their subject ABI fields remain unchanged |
| MG distribution policy | New manager cycle only; organization/refusal keep subject cycle |
| Promotion manager witness / GUI projection | New manager fields; read-only GUI does not migrate |

Authoritative B1 generator writes the product artifacts. The new
`zg361_b1_manager_identity_effects.txt` contains exactly **one** migration
effect; it is not appended to the legacy 42/36 definition shards.

`zg361_b1_migrate_manager_identity_effect` fills each missing new field
independently and never overwrites an existing new identity:

- Cycle recovery: `zg361_b1_policy_next_review_serial - 1`.
- Case recovery: `zg361_b1_m053_receipt_serial`.

Each witness has one manager-only producer. The helper reads neither old
shared field; absent witnesses do not manufacture identity. New managers
are initialized by the real opener with independent counters at zero before
increment. Calls occur at opener, all manager delayed entries, before an
active manager's subject initialization, and Central's independent manager
entry points. Subject-only entry points and native subject ABI are unchanged.

The no-capital branch sets `baseline_available=0` and `baseline_state_delta=0`
with marker `ZG361B1:baseline-unavailable-no-capital`. The difficulty adjustment
already starts at zero. The capital-present calculation is unchanged. Frozen
start facts, KPI, roster membership and cohort denominator are preserved.

Both `.100` and `.102` now call the existing `prune_unavailable_subjects`
before their first roster consumer. Its `is_alive` semantics are unchanged;
no `is_landed` filter was added, so living departed subjects remain in cohort.
`.103` and later pruning behavior were not expanded.

## Validation and file-boundary evidence

- B1 generator: **13** current generated outputs, BOM retained.
- B1 tests normal / `-O`: **63 / 63 GREEN** each, including four focused
  regressions for migration/shard, source-derived R66 assignment vectors,
  manager entries versus subject ABI, and no-capital preservation. Existing
  weak-subject test now covers both `.100` and `.102` prune-before-consumption.
- External Central/B2/Incident/MG suites normal / `-O`: **164 tests plus
  677 subtests GREEN** each, reported by the exclusive external-consumer writer.
- Promotion D0 witness normal / `-O`: **4 / 4 GREEN** each.
- `validate_local.py`, root `tools/validate_static.py`, `git diff --check`: GREEN.
- Effect boundary: **428 files / 3721 effects**, target misses 0, >20
  violations 0, maximum non-legacy definitions 10. Legacy counts remain 42/36;
  this change grants no new >20 exception.

The numeric regression is explicitly a narrow source-derived assignment
model, not CK3 execution. `open_kaishek`'s current finite runtime does not
certify the full production effect/list chain, so parser success must not be
described as runtime reproduction.

Keep the earlier file-boundary lesson separate from this business cause:
file boundaries/size remain a likely contributor to the earlier startup RED;
this R66 evidence establishes serial aliasing after successful load. If the
next candidate regresses to loading-performance RED, inspect its exact shard
sizes and try a purpose split, keeping each new shard at 1–10 effects and
never silently adding a >20 exception.

## Remaining live gates

1. The same human may receive new subject cycles while its independent
   manager identity and valid manager ticket continue through `.100/.102`.
2. A still-valid saved manager pair resumes via its private witnesses;
   genuinely obsolete tickets stay no-op. Do not force recovery to ticket 17.
3. Capital-less living departed subjects retain frozen evidence without
   baseline native-read errors. The existing `is_alive` pruning actually
   prevents the observed unavailable weak-object reads at D+300.
4. Player Central source chain reaches `.146` and D+1 `.147` with correct
   frozen owner/cycle/case. AI silent summary/abort is not player closure.

Frozen log SHA-256:

- `Z:\b3r66\cell\final_debug.log`:
  `8CEB947FA316EA1418626340425D4570F47ED8673643858B0C18DEC0DEB5BBCD`.
- `Z:\b3r66\cell\final_error.log`:
  `A60B2BBC08192D031D77C812E78CC57181F93DDAE1E88BCFBB36AF2C2D61F58C`.

Exact CK3 build: `1.19.0.6`, EXE SHA-256
`2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`.
