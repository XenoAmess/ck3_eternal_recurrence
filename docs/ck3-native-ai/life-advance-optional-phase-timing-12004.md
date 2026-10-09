# Optional scalar timing for the slow normal siege day

Root's first actual hot04 speed-five normal siege day retained the exact
one-day paused contract but took **297.111244s** end to end. The selected actual
response is
`D:/codex-ck3-background-spill/g2-live-20261010-r85-retry02/r0084-speed5-native60-hot04/operator/gameplay-responses/110-r0084-sdk5c48-bounded-normal-save01-chunk01-000003-normal.json`;
its bounded once-read projection is
`D:/codex-ck3-background-spill/player-siege-speed5-delivery/ACTUAL-HOT04-FIRST-LIFE-THIN.json`.
It reports `player_siege`, speed5, raw53289504→53289528, generation11, one tick,
zero overshoot and paused. Existing per-phase timing fields were absent.
Neither engine-wait dominance nor a controlled speed comparison is established.

This independent full SDK worktree starts at frozen hot04 source
`5c48c48dff1475993339dce17ddfe35e6e772b95`, whose exact source tree is
`D:/cg-crown-stale-normal026`. The new tree is
`D:/cg-life-phase-timing-hot05`; the running source is untouched. Root's
source binding remains
`D:/codex-ck3-background-spill/g2-live-20261010-r85-retry02/r0084-speed5-native60-hot04/metadata/source-binding01/SOURCE-METADATA.json`.
No new EXE read/hash, native build, project import, test, SDK call, game
operation, live query or response reread is performed by this source owner.

## Four bounded spans, existing logger

The existing `army_query_timing.py` append helper and
`XAR_CK3_ARMY_TIMING_JSONL` environment variable are reused. Logging remains
disabled when that variable is absent. Existing Army callers retain their
default step and row fields; new callers pass an explicit scalar step and the
exact clock wait optionally supplies its already-held scalar date. No gameplay
body, Driver state, history, public MCP schema, WAL or callback is added.
The existing diagnostic schema identifier and nonfatal append-error handling
are retained.

| Stage | Boundaries | Diagnostic step |
| --- | --- | --- |
| `service.normal_plan_turn` | Complete existing normal public plan, including private readers and detached plan projection | `plan-turn` |
| `driver.full_state_persistence` | Existing write-lock wait, complete encoding and atomic replacement; original error/dirty handling retained | `persist-driver-state` |
| `driver.exact_clock_resume_to_paused` | Existing resume helper through the existing paused snapshot wait, before clock status query | `life-advance` |
| `driver.life_advance_total` | Complete normal Driver execute, including existing action recording and full persistence | Actual `life-advance` or `life-advance-one-day` step |

The spans use `try/finally`; existing returns, failure recording, exceptions,
cleanup, lock order, native arm/resume/status order, daily cadence and complete
persistence remain in their original order. No extra state read, file-state
read or snapshot is added. Timing the resume-to-paused interval does not isolate
pure engine work: it includes the existing submission, ACK handling and Python
snapshot/readback work. Persistence timing includes lock wait, encoding and
replacement. These nested spans must not be summed as disjoint phases.

This reversible logging change does not justify another mirror test or replay
of the previous speed/clock fixture. Root reviews the source, performs
`py_compile`, then qualifies the new SDK against the existing paused game and
observes the next natural step. Root sets the environment variable to an
absolute D path with an existing parent directory when starting that SDK.
Readiness is **source-authored, compile/paused qualification/actual timing
NOTRUN**. No actual performance improvement, additional day, saved progress,
capture or G2 completion is claimed.
