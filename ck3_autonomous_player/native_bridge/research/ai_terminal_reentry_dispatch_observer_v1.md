# Private AI winner terminal reentry dispatch observer V1

This observer is a passive, exact-build research probe for CUnit `16777231`
after CombatID `16777218`. It is **OFF** in the default build. A dedicated
private DLL requires
`-DXAR_CK3_ENABLE_AI_TERMINAL_REENTRY_DISPATCH_OBSERVER_V1=ON`.
It must be injected by the managed suspended-start path before CK3's primary
thread resumes. The observer never calls a native game mutator itself: it
intercepts only naturally reached builder and submit calls and invokes each
original trampoline exactly once.

The admitted executable is CK3 `1.19.0.6`, SHA-256
`2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`.
The install transaction checks all four exact byte anchors: builder entry
`0x186B190` (15 bytes), its dispatcher call `0x187235D` (5 bytes), submit
entry `0x973E00` (15 bytes), and builder submit call `0x186B2C5` (5 bytes).
It creates two private executable trampolines, patches builder then submit,
and restores the builder if submit installation fails. Any unproven rollback
rejects the suspended launch. The patch is process-lifetime pinned; do not
hot-unload the DLL.

The only private readback step is
`query-ai-terminal-reentry-dispatch-v1-16777231-16777218`. Its private
capability marker is
`game.command.query-ai-terminal-reentry-dispatch-v1-private`, advertised
only by the ON build. The promo `capture_session.py` owner must also receive
`--enable-private-ai-reentry-observer` and
`--private-ai-reentry-dll-sha256 <exact-private-DLL-SHA256>`; the request
channel then accepts only `{ "action": "private_ai_terminal_reentry",
"step": <exact-step>, "expected_revision": <positive-public-revision> }`.
This uses the already owning driver connection and never opens a second
pipe. Direct ordinary `ck3_execute_step` remains outside the public
`action_steps` allowlist.

The readback requires a
stable paused snapshot and returns `observer.installed`, `failure_flags`,
matching-call counters, `overflow_count`, and every retained record in a
fixed 64-slot array. A record includes both caller return RVAs, thread ID,
full CUnit ID, builder and command targets, kind `2`, route kind `2`, direct
target flag, AI channel flags `7`, raw move mode, queue Boolean, and the
terminal journal correlation fields. A true queue return proves clone/queue
acceptance, not eventual execution; the paused terminal-transition and route
queries must still show the same date, CUnit, and target.

The game-thread submit hook samples only fixed command header bytes, the
game-state date, and the terminal journal's **atomic latest sequence**. It
does not scan terminal journal records. On the stable paused readback the
worker scans the terminal journal and marks `terminal_before_submit` only if
the exact CombatID event sequence is nonzero and no later than the sampled
cutoff, its date is no later than the command date, and the CUnit identity
matches. The caller must additionally require `terminal_normal_result`,
`cunit_was_terminal_winner`, `terminal_capture_failure_flags == 0`,
`command_header_valid`, `queue_accepted`, and all observer failures and
overflow counts zero. A later matching event cannot be used to backfill
provenance. This readback has only been tested offline; no live conclusion is
claimed by this source change.

The terminal journal's scalar latest-sequence store uses release ordering
after publishing a record; the hook's acquire load observes that cutoff.
The observer's active-state and original-trampoline publications use
release/acquire. Each record's payload is written once, then `count` is
published with release ordering; the paused worker reads count with acquire
ordering. The fixed capture guard uses acquire/release and records reentry
as a failure. The overflow counter is relaxed because it is diagnostic and
the failure bit is published with acquire/release. The terminal journal's
non-atomic record payload is read only after the bridge verifies a stable
paused frame; reading it on the running game thread would risk a C++ data
race on ring wraparound.

Focused offline check:

```text
ctest --test-dir <private-build> -R xar_ck3_ai_terminal_reentry_dispatch_observer_v1 --output-on-failure
```

The source contract verifies the full executable SHA and all four RVA byte
anchors. The native test covers admission and quiescence gates, exact caller
bytes, two-anchor installation and rollback, command-header identity,
terminal cutoff/date/winner correlation, bounded capacity and reentry state.
