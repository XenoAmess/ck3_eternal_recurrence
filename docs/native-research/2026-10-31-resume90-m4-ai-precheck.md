# M4 AI decision precheck projection correction

machine_id: `xenoamess-full-tower-eb9d2c1186`. Observations use UTC, `2026-10-30T16:02:32Z–16:05:37Z`.

The existing Java `DecisionCadenceStudy12004.resourcePrecheck` treated two ten-slot vectors as a wallet comparison over indices 0–7. The actual `1ACA990` producer projects ten signed costs with indices `[0,1,2,4,5,6,8,9]` onto the caller's **eight context budgets**. Only positive costs are compared, and equality is rejected. Costs 3 and 7 are omitted; costs 8 and 9 are inspected. The caller's mode3 budget also contains explicit zero slots and values from several components, so it is not a ten-resource wallet.

The correction changes the existing offline method and its input validation to ten costs plus eight budgets. The original return remains `NATIVE_FINAL_GATES_REQUIRED`: passing this predicate grants no action, quote, affordability or funds. Current published code has no ordinary planner/runtime caller for this study; this is not attributed as a live autoplay failure.

## Actual original-code comparison

The held 335-byte body at `1ACA990..1ACAADF` is retained in the small source metadata resource. A separate owned JVM executes its unchanged 186-byte projection/comparison tail `1ACAA25..1ACAADF`, retaining the original 21-byte prologue and using an explicit software input-copy seam for the ten already-produced costs. The eight-budget receiver is owned input. Earlier eligibility gates and native cost production are not run. No Game process is attached, and no fresh PE read, provider, native Game request or local model request occurs.

The 86 original-tail calls returned 37 accepted prechecks and 49 rejections. The persistent text corpus includes raw-slot isolation, equality, omitted slots, negative/zero costs, negative budgets and signed64 extremes. A separate negative control appends two zeros only to satisfy the old Java ten-budget shape: the old method still disagrees on 13 of 86 outputs, independently establishing the projection error.

Strict Java21 compilation passed for the oracle, baseline and candidate. The same complete JUnit class changes from 4P2F to 6P0F, with zero skips; the corrected corpus method checks all 86 original outputs. No broader Maven/CI or Game result is claimed. The existing JUnit class remains the persistent CI entry; CI reads the small corpus and does not need JNA, executable memory or D-drive archives.

Evidence and reproducible owned oracle: `D:/ck3-state/resume90-root/m4-precheck/` (`M4PrecheckOracle.java`, `oracle-run.log`, `RESULT.json`, `legacy-probe-run.log`). Small source/corpus resources record machine, original bytes/SHA, input seam and result scope. Review active D-only working outputs by `2026-11-06T16:05:37Z` under the shared storage policy; repository regression fixtures remain active test inputs.
