# Refill integration fixture: reviewer context (2026-10-21)

machine_id: desktop-3fevhd2-1c74096080. Source baseline: 58d6058d9aa202f91f1046753bb5d0df23e55c77.

Official Runner CI 39536664294 failed at step 19, `Test public post-allocation refill capacity scope`; Linear history succeeded. The official job traceback was not available. An independent exact-source local Python reproduction found the integration fixture's reviewed context missing its reviewer. The production preflight correctly refused it with `Actual allocated run reviewer required; never claim Root review`.

The focused candidate ran six methods successfully. Paired strict checking improved the existing module from 35 diagnostics to one unchanged legacy crossed-scope lambda diagnostic; this is not a whole-module strict PASS.

The primary candidate changes its test fixture: it supplies an explicit synthetic non-Root reviewer and retains the real preflight/launcher boundary. Missing, null and mismatched reviewer controls must refuse before launcher, CaseClient or actor execution. No production guard is relaxed. Baseline and candidate evidence is retained below; the sparse-worktree import failure is separate from the reproduced CI cause.

This source-freeze snapshot does not claim a successful later CI run. Publication and new-head CI status are established by their actual receipts. Formal themes remain 8/11; full R08, paid/payer/cadence, native execution and Game qualification do not change.

Evidence: [exact copy plan](evidence/episode04-ci-refill-reviewer-fixture-20261021/EXACT-COPYPLAN.prepared-a02.json). Original HTTP Range refusal remains recorded; no whole job log was downloaded.

The neighboring readiness-handoff fixture is also corrected to materialize its synthetic persisted reviewer/context/frozen argv, rather than providing a nonexistent placeholder pin. Its actual baseline fails and candidate passes one method across three adapter routes; strict diagnostics remain the same seven legacy diagnostics. Production reviewer verification is unchanged.
