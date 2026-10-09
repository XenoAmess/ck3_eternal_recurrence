# Life advance: no remaining core transcript-export fix at f982

2026-10-10 / ISO 2026-W41. Finite source finding on SDK source
`f9820ecead8be1b9597f710bae34c7ab421136c6`. No production code change,
test, runtime import, SDK operation or game operation was performed.

Root selected ordinary R0084 response
`D:/codex-ck3-background-spill/g2-live-20261010-r85-retry02/r0084-sdkba92-native60-hot03/operator/gameplay-responses/100-r0084-sdkf982-sustained-root03-000014-normal.json`.
This lane obtained its file size and read only its first 4096 bytes, once.
The file is 307292 bytes. Its header records
`2026-10-09T22:00:38.382641+00:00` through
`2026-10-09T22:05:28.124609+00:00`: **289.741968 seconds** end to end.
The visible result prefix identifies `ck3_auto_turn`, selected `life-advance`,
phase `native_war_siege_progress`, and a player siege. Root separately supplied
the actual one-day progression `53289432 -> 53289456`; this lane did not read
the remainder of the response to reverify those fields. No Driver file,
complete response, executable or hash was read.

The scoped hypothesis was an unused full native-command-history export in
the normal life-advance execution path. That hypothesis is negative at this
source. The relevant paths in `bridge/native_driver.py` are already lean:

| Production path | Existing behavior |
| --- | --- |
| `_execute_step_unrecorded` life-advance entry | Captures `take_internal_semantic_snapshot()` before capability projection. |
| `_execute_life_advance` entry | Uses the provided detached semantic entry frame, or an internal semantic snapshot. |
| Siege and assault inputs | Reads the owned transcript under its lock; only selected siege fields escape detached. These history inputs are consumed and cannot simply be removed. |
| `_execute_composite_primitive` speed/event calls | Passes `internal_semantic_snapshot=True`, including the existing revision-race retry. |
| Exact-day sentinel arm/status/cancel | Passes `internal_semantic_snapshot=True`. |
| `_resume_life_advance` and `_pause_life_advance` | Initial requests and existing retries pass `internal_semantic_snapshot=True`; ownership and postcondition reads are semantic snapshots. |
| `_wait_for_life_advance_snapshot` / `_wait_for_life_advance_change` | Waits for public revision changes and returns an internal semantic snapshot, without public history export. |

Inside `_execute_primitive_step`, `internal_semantic_snapshot=True` selects
`take_internal_semantic_snapshot()` before considering
`include_native_command_history`. Adding `include_native_command_history=False`
at those already internal calls would therefore be an inert patch. No such
patch or implementation-mirroring test was authored.

The registered callback delegates to `Service.auto_turn`. Normal native
planning already chooses the internal semantic snapshot and the locked
`_with_internal_planning_view`; its planner intentionally consumes the owned
history. Service's ordinary execution dispatch delegates `life-advance`
without another full snapshot. Sway and feast following-turn snapshots
already request omitted history. These observations do not establish that
every conditional private planner in the entire auto-turn call exports zero
history: the bounded live prefix does not identify all such branches. No
unproven conditional branch was changed or promoted to the cause of this run.

The normal action's required persistence remains observable in source:
`execute_step` records the completed composite, `_record_command` detaches
the current result and appends it to owned history, then calls
`_persist_driver_state`. Successful `life-advance` is not a deferred read-only
step. `_encode_driver_state_locked` serializes the complete owned transcript
directly, without first deep-copying it, and the existing writer atomically
replaces the state file. This is a real full-state persistence barrier; this
lane has no phase timing proving its share of the 289.741968 seconds.
Deferring or trimming that barrier would change the requested persistence
semantics and is outside this attempted history-export fix.

The source lane stops with **NO_CHANGE: core history-export hypothesis
negative**. It does not rerun preview/construction investigations, add a
profiling platform, reduce siege observation or alter war preferences.
Existing Root runtime observations or separately authorized bounded phase
timing would be needed to attribute the remaining end-to-end delay. No test
is required for this documentation-only negative finding. G2, NW2, game-day,
save, inheritance and capability readiness receive no additional credit.

## Later authorized existing-payload phase diagnosis

After the prefix-only finding above, Root explicitly authorized one complete
read of the same 307292-byte response. This lane parsed it once and retained
only bounded selected fields in
`D:/codex-ck3-background-spill/life-advance-history-source/ACTUAL-EXISTING-PHASE-FIELDS.json`.
The earlier prefix-only record remains the account of that earlier operation;
the complete response was not reopened a second time in this phase.

The actual composite requested horizon 1 and `timeline_speed=1`,
`timeline_policy=player_siege`. Its four actions were `set-speed-1`, sentinel
arm, `resume-map`, and sentinel status. The native receipt's generation was 8;
its start, target and stop dates were `53289432`, `53289456`, `53289456`.
It recorded exactly one completed daily tick, no intermediate pause,
`date_deadline` as the only trigger reason, no overshoot, no abnormal/terminal
condition, and an observed native pause. No event was selected and the
composite reported its normal postcondition. This establishes the actual
speed and stop cause. It does not establish engine wait duration.

The existing normalized body has **no phase timing fields**: neither an
action's elapsed wall time, native running-clock interval, nor the required
Driver persistence duration is present. The end-to-end 289.741968 seconds
cannot be divided between engine execution, planning/query work, and complete
state persistence from this payload. In particular, one native daily tick is
not a duration and cannot be used to assign most of the delay to the engine.

At `f982`, `_life_advance_timeline_policy` chooses speed 1 when it observes a
player siege without an active enemy route. `_execute_life_advance` then
reuses the exact-day native sentinel to retain that one-day stop. The source
constructor's default life-advance timeout is 30 seconds, command timeout
10 seconds, and resume/pause retry observation interval 1 second. These are
defaults, not proof of the running SDK's configured values. The receipt itself
contains no timeout configuration. No native AI cadence research or speed
policy design was expanded because the necessary phase attribution is absent.

After Root's seven-day gameplay checkpoint, the smallest useful additional
diagnostic would reuse the existing `army_query_timing.py` writer and
`XAR_CK3_ARMY_TIMING_JSONL`, without gameplay/history serialization:

1. Time Service planning separately from its life-advance dispatch.
2. Time the Driver's existing unrecorded life-advance execution separately
   from the following `_record_command` call. The latter includes the
   unchanged complete-state encode/write barrier.
3. Inside `_advance_exact_day_with_sentinel`, time the existing resume plus
   observed native-stop wait. This separates the running-clock wait from the
   rest of the composite without adding polling or new native queries.

The current optional timer only finishes `mcp.auto_turn_service` for the Army
query branch, and its writer hardcodes `step=query-army-strengths-v1`.
Enabling the environment variable alone therefore cannot answer this
life-advance question. A future small reuse must label the actual step
`life-advance`, preserving the existing Army default, and finish the selected
life-advance stages; it must not mislabel new records as Army measurements.
These stage additions are an unimplemented proposal, not an executed profile.
No SDK source, game speed, callback cadence, policy, persistence, cache,
schema or receipt behavior changed in this diagnosis.
