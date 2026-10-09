# Crown readonly query recovery on a published newer frame

## Actual trigger and native branch

The ordinary `normal026` call on SDK source
`f9820ecead8be1b9597f710bae34c7ab421136c6`, with qualified Native60
`30605664d00c845b4fa7a736d157903169a1e70b`, returned
`private crown-law native RED: nonwar private snapshot revision is stale or malformed`.
Root retained the actual 579-byte error and timing (196.421917 seconds) under
`D:/codex-ck3-background-spill/r0084-hot03-normal026-diagnosis`.
This source package does not reread the error or the opaque Driver state.

The exact-build branch in `native_bridge/src/bridge.cpp` rejects the request
before `HandleNonwarPrivate12002` when parsing fails, the expected native
revision is zero/differs, there is no previous snapshot, the current snapshot
cannot be read, or it differs from the published previous snapshot. The shared
error does not identify which predicate failed in normal026. There is no
evidence that the request used a public revision as a native revision:
`realm_law_formal_private_transport._send` already sends `before.native_revision`.

```mermaid
flowchart TD
  A[Registered ordinary auto_turn] --> B[Service plan_turn]
  B --> C[Ordinary precedence still selects life-advance]
  C --> D[Crown formal readonly query from cached semantic frame]
  D --> E{Native request matches published current frame?}
  E -->|yes| F[Native final law quote and resource costs]
  E -->|no| G[Actual stale-or-malformed RED before native law operation]
  G --> H{A newer native frame is actually published within original timeout?}
  H -->|yes| I[Bind its public and native revisions; repeat readonly query once]
  H -->|no| J[Preserve original failure; no repeat request]
  I --> F
  I -->|second rejection| J
  F --> K[Existing Crown decision and ordinary executor]
  G -. exact predicate in actual026 unknown .-> U[No narrower native failure receipt]
```

`auto_turn` evaluates `plan_turn` before entering `_execute_planned_turn`.
The Crown consumer's first formal query was not covered by its later optional
cooldown-query exception handler. Consequently this read failure stopped the
ordinary call before action execution. Existing Council source and its focused
regression already demonstrate an analogous native stale rejection followed by
a published newer observer frame; that precedent is reused without replaying it.

## Minimal source change

Only `realm_law_formal_private_transport.py` changes in production. It uses the
existing internal semantic snapshot for frame fields rather than exporting and
copying command history. Only the formal readonly QUERY's exact native stale
error is classified for recovery. The query waits through the existing native
state `wait_for_public_change` primitive and requires an actually newer native
revision before issuing one replacement readonly query. Both attempts and the
wait share the original timeout; the returned quote records its actual rebound
public/native revisions. Every successful quote still passes the existing full
native payload, paused actor/date, build, cost and candidate validation.

Other native errors, malformed responses, submission and receipt behavior are
unchanged. This is not replay of normal026, a blind live retry, a law enactment,
or a new policy/clock/schema/permission gate. A newly bound read can inform the
existing ordinary policy; final permission, costs and independent material
receipt still belong to their existing paths.

## Qualification boundary

The focused new registered Service/MCP regression uses explicitly synthetic
paused frames and source-shaped quote envelopes to reproduce the rejected old
native revision and subsequent observer publication. It reaches the actual
ordinary planning/Crown/Driver transport path; the external executor is a spy.
It also retains failures when no newer native frame appears, a different native
error occurs, or the second read is rejected. No existing native producer,
calendar policy, speed5 qualification or live query is replayed.

Root's sole focused FIRST completed with exit0/GREEN on
`5c48c48dff1475993339dce17ddfe35e6e772b95`, from
2026-10-09T22:43:50.131726Z to 22:43:58.338534Z. The test runner reported
`1 passed in 7.57s`: one registered compound with four scenes. This combined
SDK contains Crown source `b75d907b8ed043ec37e101ee509f61bd59913fc3`
on base `f9820ecead8be1b9597f710bae34c7ab421136c6`, followed by the
separately qualified speed5 cherry-pick. No speed5 test or native producer was
replayed. The original Crown commit can be adopted independently where speed5
is already integrated.

| Focused scene | Native request revisions | Executor seam entered |
| --- | --- | --- |
| Exact stale rejection, then published newer frame | 10, 11 | Yes, once |
| Different native error | 10 | No |
| Replacement read also rejected | 10, 11 | No |
| No newer native frame before the shared deadline | 10 | No |

The positive scene retains the rejected packet, returns the actually rebound
public3/native11 quote, and uses less than the original timeout for its second
request. The three negative scenes preserve their errors and do not enter the
executor. All native requests are readonly QUERY messages. The test's messages,
quotes and paused frames are explicitly synthetic; its final executor is the
documented external spy. This qualifies the production registered planning and
transport recovery for the deterministically reproduced failure sequence. It
does not establish that the live normal026 call has been repaired or identify
the particular native predicate that rejected that actual frame.

Receipts:

- `D:/codex-ck3-background-spill/r0084-hot03-normal026-source/root-first01/ROOT-FIRST-RESULT.json`
- `D:/codex-ck3-background-spill/r0084-hot03-normal026-source/root-first01/OBSERVED.json`
- `D:/codex-ck3-background-spill/r0084-hot03-normal026-source/ROOT-FIRST-QUALIFICATION-THIN.json`

Status: `static-ready`, with the new focused registered fixture qualification
GREEN; live recovery remains unverified. The actual normal026 RED is retained
and was not replayed. No author tests, project imports, build, EXE/bin reads,
hashes, SDK/Game calls or actions. Root FIRST records zero pipe operations,
game operations, native actions and old tests replayed. No M7, birth, natural
succession or G2 completion credit. Root's fresh post-error snapshot separately
reported public14/native59/raw53289504/pausedtrue; that observation is not
evidence of which native rejection predicate fired. Hot04's combined source
remains frozen; this qualification update is a separate documentation commit.
