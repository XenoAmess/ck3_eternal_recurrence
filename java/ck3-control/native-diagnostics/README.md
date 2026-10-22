# Native clock failure diagnostics

This independent Java module is a pure diagnostic reader and classifier. It has
no Game, HTTP, file-write, process-control, retry or recovery capability. It does
not replace the frozen Source32 SDK or authorize continuing a failed request.

The input `xar.native-clock-failure-observation/v1` is a new, strict normalized
projection, limited to 16 KiB. Callers supply an independently retained source
SHA-256 and control sequence. Matching those pins does not authenticate arbitrary
projection content: the producer must retain and verify its original evidence.
This parser validates the projection's types, exact fields, bounds and internal
consistency; it does not read or hash the original file itself.

The golden `src/test/resources/native-clock-failure-n46-11558.normalized.json`
was manually extracted on machine `xenoamess-full-tower-eb9d2c1186` from the
retained AUTO 11558 response, observed 2026-10-22 12:39:22.706907 UTC. Its original
SHA-256 is `a29abe49623a8da965af385526b2b9a22ad0ed30d321d0ac340d4149fc74d9de`.
**The fixture is a projection, not the original response or an equivalent byte
encoding.** No personal filesystem path is published.

Projection mapping:

In the table, `F` is the JSON Pointer
`/result/structured_content/diagnostics/exact_day_clock_failure_v1` in the same
original response pinned above. `cleanup_final` is one of that response's cached
samples, not a later RPC or a new observation made by this module.

| New fields | Original response fields |
| --- | --- |
| source schema, target, credit, never_replay | `F/schema`, `F/target_date_raw`, `F/credit`, `F/never_replay` |
| source control_sequence | `/request/sequence` |
| observed_at_utc | `/ended_at_utc` |
| wait_identity, arm_generation, flags | `F/wait_progress/identity`, `F/wait_progress/arm_generation`, `F/wait_progress/flags` |
| starting / wait_final | `F/starting_frame`, `F/last_wait_frame`; nested `connection`, `cached_heartbeat`, `cached_owner`, `cached_observer` |
| progress metric records | `F/wait_progress/metrics/{owner,verified,heartbeat,observer_completed_ms}` arrays using `F/wait_progress/columns` |
| heartbeat_events / maximum_heartbeat_gap_ms | `F/wait_progress/heartbeats`, `F/wait_progress/max_heartbeat_gap_ms` |
| cleanup_attempts | `F/cleanup_actions/rows/0/ack`, `F/cleanup_actions/rows/1/ack` |
| cleanup_tail heartbeat/owner/observer | `F/cached_native_clock_summary_v1/samples/3` (`phase=cleanup_final`); heartbeat fields, `mailbox/value`, `observer/value/completed_ms` |
| cleanup_tail.paused_after_cleanup=null | No pause post-state was observed; the earlier cleanup_before_pause_frame is not a cleanup post-state |

The fixture machine ID is the verified execution-machine attribution in the N46
run evidence, not a field invented inside the original failed MCP response.
Normalized uint64 counters/times/armed generation/flags use canonical decimal
strings. Magnitudes and identity are retained. Original numeric fields are not
accepted as aliases in this new string domain. Safe numeric IDs and revisions
reject bool, float and string tokens. PID uses the Win32 uint32 domain.

Required nullable fields distinguish explicit JSON null from a missing key:
`last_change_ms=null` means no change time was observed, pause `accepted=null`
means an unknown ACK field, and `paused_after_cleanup=null` means no observed
post-state. Missing fields and unavailable complete-frame metrics fail closed.
The model does not manufacture missing legacy samples or turn empty buckets into
proof. It retains original collector flags, missing/reset counts and the
non-atomic/native-event-time-unverified limitations.

Classification separates transport, owner progress, ACKs and native pause
post-state. A configurable stall threshold is diagnostic, never an execution
timeout or action policy. A brief interruption is not a permanent-deadlock
finding. Every assessment has zero credit, `neverReplay=true`, and
`resumeAuthorized=false`, even when a later paused post-state is supplied.

Build/verification is performed by the designated Maven build owner after this
module is added to the parent reactor. This module does not modify that parent
or install tools. The tests use this portable fixture and malformed derivatives;
they do not open the Game, source runtime, Driver or SAVE files.
