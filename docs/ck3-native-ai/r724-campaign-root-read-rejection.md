# R724 campaign-root paused read rejection

The frozen CK3 build remains `1.19.0.6`, `ck3.exe` SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
This note concerns the production native read path; it does not infer an AI
strategy or advertise a new capability.

R724 official `native-auto-run` attempt 02 stopped at turn 15 with native
`query-campaign-root-context-v1` rejection
`campaign-root snapshot changed or is not ready` after turn 14 had reached
`date_raw=53192712`. The paired driver history records the prior route
sentinel as row 137 and the rejected read as row 138. No new typed move,
terminal action, or save followed that read. At the latest independent paused
material observation, ArmyID 50331653 was already in Province 5615 with a
shorter active route toward 8755. This is evidence of travel after the prior
ETA, while the campaign-root read and successor turn remain RED.

The frozen evidence is in
`Z:\ck3_mod_rewrite_process_assets\g2-gen034-c-r723-eta-20260915\evidence\formal-eta-attempt-02\native-auto-run.stdout.json`
(UTF-16LE). The R724 archive is
`Z:\ck3_mod_rewrite_process_assets\g2-gen034-c-r724-red-20260915`.
The driver records a failed command history row even when the native pipe
returns no result. The bridge rejection text groups snapshot revision drift,
failed snapshot acquisition, and a not-ready paused root; the exact internal
branch for row 138 is **not established** by this output.

The minimum recovery path on this observed read-only failure is one bounded
fresh public snapshot/revision, with the same paused map, game date, actor,
episode, war and army semantic state, and a command-history tail containing
only the failed root read. The same query can then be retried once on that
fresh revision. A second rejection, missing new native revision, changed
gameplay state, or any typed-action history retains the first RED. The runner
must anchor the successful query's `before` and `after` to the fresh paused
frame while preserving both revision IDs and the initial rejection in the
turn record; it still applies its normal same-frame read-only assertion.

The official paired checkpoint at history row 135 (`date_raw=53192568`) was
strictly verified and preflight-ready after R724. Cold recovery from that
save necessarily replays the six days to the R724 material observation. The
runner's earlier generic opaque-auto-turn invalidation marker is not evidence
that the save itself was corrupt. A new frozen runtime and focused official
replay are still required before closing the campaign-root RED or claiming
formal next-turn consumption.

## R11 1.20.0.2 nonwar preparation recovery, 2026-10-02

R11 `formal-r11-02` returned ten turns and nine natural days before its
eleventh call failed in `plan_nonwar_turn -> _prepare_succession_transition_v1
-> query_turn_bundle_v1 -> query_campaign_root_context_v1`. The preserved
last request is `step-47-5343cd7c29b1`,
`query-campaign-root-context-v1`, native `expected_revision=34`; its native
response is `ok=false`,
`application-main typed query failed or its snapshot changed`. The exact
build is CK3 `1.20.0.2`, EXE SHA-256
`AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D`.
Original packets, returned snapshots and traceback remain in
`Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/root-nonwar-live-next/formal-r11-02`.

The final turn snapshot is paused/map-ready at raw `53170320`, native
revision `34`, player `29829`. The subsequent independent final-checkpoint
snapshot publishes native revision `35` at the same date/player/episode;
its active-war rows, player-army rows and gold/prestige/piety equal the prior
snapshot, and its command-history tail contains only the failed root read.
This proves that a fresh paused native frame became available. It does not
identify the native failure branch: `RunTypedQuery12002` combines mailbox
wait failure, unstable envelope, absent typed result, failed final snapshot
capture and final snapshot inequality into this one error. The relevant
`ExecuteTypedQuery12002` and `RunTypedQuery12002` source blocks are identical
in the original frozen `g2live11fix` runtime and the delivery source. A
collector's ordinary typed `unavailable` result alone does not cause this
outer rejection: the campaign executor sets `typed_result=true` after the
reader returns. No specific collector or provider defect is established.

The Python recovery gap was deterministic: the existing R724 catch matched
only the old 1.19 rejection text and lived after planning in
`_execute_planned_turn`. R11 failed before that catch was reached. The
minimum correction accepts the observed 1.20 text at that existing catch
and reuses `_retry_rejected_campaign_root_read` in the living-ruler
succession-preparation branch. It waits at most `1.5` seconds for a new
native revision with the existing unchanged paused-frame/history checks,
then reads the entire turn bundle once and retains the succession
expectation on its fresh public revision. There is no action retry or time
advance in this recovery path. No fresh frame, a changed date/state or a
second rejection retains RED; the second rejection preserves the first
exception and records `second_error`. A recovered nonwar plan carries
lightweight `read_only_query_retry` evidence with both revisions and the
original rejection. The original failed command remains in driver history.

The focused existing `test_r724_campaign_root_read_retry.py` suite passed
all eight tests in `0.022` seconds. Its new production-path case traverses
the real nonwar planner, root normalization, turn-bundle construction and
succession freeze using the preserved full 1.20 Council root DTO with
explicit synthetic revision bindings and R11's exact rejection text.
It verifies two root reads, one wait, fresh expectation binding, original
failure retention and no additional read on the next plan. Separate cases
cover the selected-root execution path, second rejection and changed date.
This is a deterministic offline fixture result, **static-ready**; the
original R11 batch remains RED until a separately recorded live continuation.

```python
import subprocess
from pathlib import Path

repo = Path("Z:/ck3_mod_rewrite/.task-tmp/g2dlv")
subprocess.run([
    "Z:/ck3_mod_rewrite/tools/.venv/Scripts/python.exe", "-X", "utf8",
    "-m", "unittest", "discover", "-s", "ck3_autonomous_player/tests/unit",
    "-p", "test_r724_campaign_root_read_retry.py", "-v",
], cwd=repo, check=True)
```

## 1.20.0.3 v4 internal preparation history gap, 2026-10-02

The preserved `resume-12003/formal-run-v4-03` reached 14 real days, raw
`53173104`, before turn 15 rejected `step-72-91f49d54ba78`,
`query-campaign-root-context-v1`, native `expected_revision=52`, with
`application-main typed query failed or its snapshot changed`. There is
one rejected root request and no fresh-read request after it. This attempt
used source `19a0e94510e8a41e0a7ee83e709a9dd914c5dc30`, the combined law/Feast
v4 DLL, CK3 `1.20.0.3`, EXE SHA-256
`94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6`.
All paths in this section are relative to
`Z:/ck3_mod_rewrite/artifacts/g2-maintainer-2026-10-02`.

The subsequent `resume-12003/checkpoint-v4-14d-01` before-frame has native
revision `53`; the same-PID independent read at
`resume-12003/m6-feast/attempt03/live/readonly-20261001T204003Z` starts at
native revision `55` and returns an available campaign-root DTO. These
three frames retain raw date `53173104`, living actor `29829`, episode,
paused/map-ready state, active-war rows, player-army rows and player
gold/prestige/piety. No source/DLL change or restart occurred between them.
The checkpoint retains all 14 days at full/history row `427`. The failed
batch remains RED; this independent read does not identify which of the
five grouped native callback/envelope/final-snapshot checks rejected the
original query, and does not prove the fresh frame would have arrived
within the existing `1.5`-second wait. The native branch remains unknown.

The Python gap is directly established by the production source:
`plan_nonwar_turn` reads `take_internal_semantic_snapshot`, which omits
`native_command_history`. The existing retry helper requires that history
list before it waits, so preparation returned the original rejection
without entering its fresh-read seam. The earlier Council fixture aliased
its internal read to a public snapshot containing history and missed this
producer difference.

The minimal service correction records the real history length through
the existing locked internal planning view before the root query. Only
after the observed root rejection does it copy the real pre-query history
prefix and pass it to the unchanged retry helper. Normal successful
preparation still avoids copying the transcript. The original paused
frame, new native/public revision, unchanged actor/date/war/army, same
PID/connection and single-failed-read history-tail checks remain intact.
A second query rejection retains the first error and its retry evidence;
no action or time advance is resent.

The focused existing unit module now also binds the actual
`NativeHeadlessGameplayDriver.take_internal_semantic_snapshot`, internal planning
view and history-copy implementations over the frozen 1.20 Council DTO
and explicit synthetic revision bindings. Its added internal-entry case
covers a nonempty prior history, successful fresh binding, changed-date
RED and second-rejection RED. All nine tests in the focused module passed
in `0.022` seconds. This is an offline production-path fixture,
not a live recovery claim. The actively running `formal-run-v4-04` retains
its frozen v4 source and is isolated from this source change. The failure
packet, snapshot comparison, test result and source pins are recorded in
`resume-12003/campaign-root-v4-03-diagnosis/`.
