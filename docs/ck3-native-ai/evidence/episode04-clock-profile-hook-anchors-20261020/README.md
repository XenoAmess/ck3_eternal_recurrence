# Clock profiling source-comparison repair

machine_id: `desktop-3fevhd2-1c74096080`; reviewed 2026-10-20 15:23Z.

Current c1b03 CI step53 failed before behavior comparison: all three legacy
`UNPROFILE_HUNKS` contiguous blocks matched zero times. Commit43653fc1 inserted
independent wait-progress observation between the clock-profile import/start,
finish and candidate-observe statements. Frozen bc638 still matched all three.
This is demonstrated by exact Git source bytes in SOURCE-COMPARISON.actual.json;
the original failed CI log stays in the previous read-only lane.

The candidate changes only UNPROFILE_HUNKS into four strictly unique pieces:
clock-profile import, start, finish, and observe-if. The existing uniqueness
assert, real method extraction, success/exception comparisons, command/action
comparisons, CPU lifecycle and observation-phase assertions all remain intact.
AST-AND-TREE-READBACK proves the test AST is identical except this literal table.
No assertion is deleted, no skip added, and the compared implementations differ:
the baseline strips those 513 bytes while the original methods retain them.
New wait_progress start/finish/observe calls remain unchanged on both sides.

The original two source-behavior tests were each run once against exact c1b03
driver bytes and once against exact frozen bc638 driver bytes: four executions,
all PASS, original Popen waits0. For c1b03, its complete original wait-progress
and failure-diagnostic modules were loaded in memory from the same Git commit;
the run did not silently swallow a missing-module import by using old bc code.
Unchanged helper module hashes and the retained3061B fixture are source-pinned.
The source fixture describes historical mocked test inputs, not current CK3.

Only existing Native/OS/scheduling test fakes executed. This proves the existing
focused comparisons pass with strict independent anchors on these two sources;
it does not qualify all clock behavior, live runtime, the complete CI matrix,
or any R08 business result. No222-test rerun, SDK, game, compile or source-tree
edit occurred. Both1.65MiB driver blobs stayed in memory and were not copied.

Review/apply CLOCK-PROFILE-HOOK-ANCHORS.candidate.patch to the single tracked
test path. Read-only cached-index apply/whitespace check returned0. After normal
integration/publication, a new exact-head official CI result is still required;
the previous c1b03 whole-CI RED remains historical. D remains frozen bc638 clean.
