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

## Additive passive result and fallback readback

The same default-OFF private build now also records up to 64 builder outcomes
in `observer.builder_outcomes` and counts matching submissions at the outer
fallback call `0x1872611` in `fallback_submit_matching_calls`. The existing
private step and `schema_version=1` remain additive: existing builder-site
records retain their meaning, while each record has `submit_site=1` (builder) or `2` (outer
fallback). A fallback record has `builder_return_rva=0` and
`builder_target_province_id=-1`; it is **not** automatically attributed to a
particular earlier builder. Both sites enter the already hooked `0x973E00`,
so no third live code patch is installed. Every intercepted call invokes its
original trampoline exactly once.

For a matching builder, the hook reads global byte `module+0x5762480`
immediately before and after the original call, then reads caller-owned result
bytes `+8/+9`. These are before/after samples, **not** a sample at the exact
`0x186B278` test instruction. The exact-build control-flow map and the
count of builder-site submit calls permit these classifications:

| `+8` | `+9` | Builder-site calls | Outcome |
| --- | --- | --- | --- |
| 0 | 0 | 0 | `1` unhandled; only this class may enter outer fallback |
| 1 | 0 | 0 | `2` early return after builder accepted target |
| 1 | 1 | 0 | `3` bypassed builder submit at the shared global gate |
| 1 | 1 | 1 | `4` builder submit reached, regardless of queue acceptance |

All other combinations become `0` unclassified and set an identity failure.
Each outcome keeps target/CUnit/thread/date, terminal-journal sequence cutoff,
both global-byte values and validity booleans, the raw result bytes and their
validity, call count, and class. Read/capacity/reentry failures retain their
existing failure flags; either fixed array overflowing is RED. This is a
static classification of the path just executed, while the meaning of the
global byte's bits and its writer remain open; see the
[bounded static analysis](../../../docs/ck3-native-ai/winner-ai-builder-submit-gate.md).
A later live attempt must
still correlate terminal sequence, same-frame route, and fallback record
independently; no inference is backfilled into attempt 065.

Installation still requires a suspended primary thread, exact EXE admission,
the two original entry/caller anchors, and now also checks the unpatched
fallback call, builder gate test, and result-byte writes before patching.
The private build remains opt-in with
`-DXAR_CK3_ENABLE_AI_TERMINAL_REENTRY_DISPATCH_OBSERVER_V1=ON`; this source
change does not launch or attach to CK3.

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
anchors plus four new interpreted RVA anchors. The native test covers
classification and bounded builder-outcome storage, admission and quiescence
gates, exact caller
bytes, two-anchor installation and rollback, command-header identity,
terminal cutoff/date/winner correlation, bounded capacity and reentry state.
