# B1 human manager/subject identity diagnostics — 2026-09-05

Status: `static-ready / diagnostic-live-pending`. No CK3 session was started
or attached by this work package. This does not close the promotion source.

## Why this observation is needed

R59 and R61 contain stale B1 tickets and central aborts, but the previous
constant log messages do not identify their manager. The repeated
`eligible AI central portfolio completed silently` line is also emitted by
`zg361_p2c_abort_stale_effect` through its summary helper; it is not evidence
of successful AI completion. In R61 final_debug lines 10106–10107 the silent
summary is immediately followed by typed RED. R59 shows the same pairing.

There is a concrete production data-flow collision candidate:

1. `zg361_b1_open_cycle_effect` increments the manager's
   `zg361_b1_cycle_serial` and `zg361_b1_case_serial`, then initializes every
   reviewable direct subject.
2. `zg361_b1_initialize_subject_case_effect` writes those **same field names**
   on each subject using the superior's values. A subject can also be a
   celestial duke-or-higher manager with its own active cycle.
3. The manager's delayed `.100` requires the current fields to equal the
   saved manager ticket. A differing superior write can therefore invalidate
   the manager ticket. Conversely, a later manager increment can invalidate
   that character's subject identity in its superior's cohort.

Both roles are reachable through existing product paths: the seed bootstrap
calls the real superior's public B1 opener; yearly playable pulse calls
`zg361_jingcha_annual_dispatch_effect` → `zg361_issue_jingcha_mandate_effect`
→ the same opener, and common-superior synchronization schedules manager
`.90` events. R59 additionally has real player mandate logs at final_debug
4123 and 17331; each is immediately preceded by an ignored cycle-open log.
The saved native `.200` event has owner `29628` and player subject `29037`.
These establish reachable dual roles, **not the two numeric writes or their
inequality in this run**. The exact cause of the player's missing `.146`
remains unproved; a broad field migration has not been implemented.

The player's timeline also includes a real title transition: R59 native
`.0630` at date_raw `53147256` binds actor `32904` and recipient `29037`.
Vanilla `ep3_interactions_events.txt:4580` executes
`governor_resignation_title_transfer_effect` in its sole option. The next
day's `.0002` binds new_holder `29037` and previous_holder `28557`. This is
not a business-neutral notification and may change the frozen roster.
Existing B1 departure reconciliation is separate from owner-ticket identity;
neither path may be presumed to explain all stale messages without evidence.

## Minimal implementation

The B1 generator now emits two inline, human-only observations:

- Before subject initialization, only when the human subject already has
  `zg361_b1_cycle_active`: log the subject and initializing ROOT identity,
  the subject's current manager cycle/case/state, and the superior's incoming
  subject cycle/case.
- In `.100`'s existing stale branch, only for the human ROOT: log the current
  manager cycle/case/state alongside the already-saved ticket scopes.

Each newly read variable is guarded by `has_variable`. Identity anchors and
numeric snapshots use only `save_temporary_scope_as` and
`save_temporary_scope_value_as`; no durable variable, policy, counter, ticket,
or event scheduling is changed. `debug_log_scopes = yes` emits the existing
saved ticket directly, without additional reads of possibly absent ticket
values. This avoids appending diagnostic fields to inherited event contracts.
The native output's actual scope/value presentation is still live-pending.

Primary syntax examples are the exact-build vanilla
`events/yearly_events/yearly_events_3.txt:89–96` (temporary numeric scopes)
and `events/varangian_events.txt:212–213` (debug marker plus scope dump).

Search the next candidate log for `ZG361B1_DIAG:`. A manager/subject overwrite
is established for the player only when an identified active manager's
before/incoming values differ and the later stale ticket/current values
correspond. Equal values or a different failure instead keep this hypothesis
open. No AI-only abort or global weak-reference error count establishes it.

## Validation and file boundary

- `gen_361_b1_runtime.py`: generated all 12 outputs.
- `test_zg361_b1_runtime.py`: **59/59 GREEN**, including temporary-only,
  human-gated and variable-guarded diagnostic contracts.
- `effect_file_boundaries.py`: **427 files / 3720 effects**, target misses 0,
  greater-than-20 violations 0, maximum non-legacy definitions 10.
- No new top-level effect was added; legacy B1 counts remain **42 / 36**.
  The first legacy shard is now **259453 bytes**; the event file is
  **30647 bytes**. The user-requested purpose-split rule remains unchanged.
- `open_kaishek` at `84a2b18fedad74de37bf5cd0472519ee321f367d` cannot execute
  these product effects: its `set_variable`/`change_variable` descriptors
  are not certified runtime handlers, and the full vassal/list scope chain
  is unsupported. Finite-runtime reproduction is **not-applicable**, not
  GREEN. Parser support must not be reported as numerical execution.
- Exact CK3 build: `1.19.0.6`; EXE SHA-256
  `2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`.

Frozen log evidence reused, not regenerated:

| Artifact | SHA-256 |
| --- | --- |
| `Z:\b3r59\cell\final_debug.log` | `D404E49705F654280BAE7AAA46BA76A861B7B9E74459F8C4D261E10D4B2449DD` |
| `Z:\b3r59\cell\final_error.log` | `EAFB87A6B170FEADB7048675D29841559D7A597E79FCAAEE619EAA446102E061` |
| `Z:\b3r61\cell\final_debug.log` | `8065414FD3038E6337FDCEB54BE7150420D02EA804E7B4F09046D19A050E4780` |
| `Z:\b3r61\cell\final_error.log` | `0C6D0896DFCFFFA3DC6BFE74615CF18A4E9A9B81B1713E37086FE25A366B43A5` |

The coordinator owns the daily/weekly report merge and commit/push. The
active `Z:\p2w\p` candidate is a separate frozen tree and was not modified.
