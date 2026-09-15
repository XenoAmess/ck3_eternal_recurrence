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
