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
