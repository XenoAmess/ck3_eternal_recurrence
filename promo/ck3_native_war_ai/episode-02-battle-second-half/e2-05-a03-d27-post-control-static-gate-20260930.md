# E2-05 d26→d27: same-run post-control source gate

Prepared 2026-09-30 CST from #451 HEAD `d921dd3a0fdf627b342959b8ec86e047a923e459`. This is a static code candidate. It did not start CK3, take a screen lease, record video, advance a date, or establish a new day-27 outcome.

## Frozen gap

The a02 source was d26 save SHA-256 `C1276153435766A875B0984F1A3AD426CB3AFCFB6EC33061CEE6650538CFFD2B` with its own save receipt SHA-256 `78931511D31E8400334D28DAD276F4CCDFBB342A901FC00B0BAFDCDEDA29584C`. The 600-second a02 raw is SHA-256 `7FC3D614C50AD958DA57359248A196A230BD2B0B5B511EF242596837042C1C0F`. Its `d27-after.control` is a post-snapshot, not a battle-control response; `d27-player-knights.control` is null. The a02 managed trace has no `knight_selects` field and reports failure flags 1040. It contains an event row, but no saved d27 life read for CharacterID 33437. Therefore the a02 death state, selector values, and native post-control remain unknown.

## Small source change

`remaining_live_step.advance` already issues a same-revision `ck3_query_battle_control_snapshot_v1` after d11's one-day action and trace finish. The same post-query now applies to `e2-05-d26`, with `subject_army_id=18` and `expected_revision` taken from that run's paused d27 post-snapshot. Its response is retained as `e2-05-d26-post-control` and rechecked against the same wrapper/native revision, snapshot ID, date_raw `53146872`, actor 29829, CombatID 16777218, province 2633 and battle-control readiness. A missing, failed or mismatched query produces `RED_PRESERVED`; the one-day request is never retried. The resulting receipt remains `ONE_DAY_ADVANCED_UNREVIEWED` even when this check passes: it is not a selector, death, visual, clean-span or human-review verdict.

The change does not alter the old source/DLL pins. The current `e2-05-d26` track still pins DLL `EB643577E0DE6214582A667B3C6C52DB712CA75E46374BECB9DB5C36204F67E7`, which predates the selector ring. It is **not** an executable a03 selector admission. A future a03-specific operator must bind an independently reviewed selector-capable DLL/injector, the exact d26 source pair and one-action state machine, then include this post-control read without weakening the a02 track's historical binding.

## Next independent evidence gates

1. Before live work, freeze the a03 source, EXE, DLL, injector, helper and no-launch receipt. Review the selector hook ABI and explicit hook-install/readiness response. The selector ring's selected candidate words are opaque tokens; it does not expose a raw draw or the complete candidate list. Missing or ambiguous rows stay unknown.
2. In one new managed a03 attempt, require paused d26 pre-control, one recorded d26→d27 action, the saved trace finish from that action, paused d27 post-snapshot and the new same-revision post-control response. Archive every native request/response and its exact bytes. If the query is unavailable after the action, preserve the advanced RED attempt and complete cleanup; do not repeat the date action.
3. Preserve the new attempt's d26 checkpoint before a separate, create-exclusive d27 `ck3_save_checkpoint(expected_revision=<fresh d27 revision>)` can overwrite the fixed save path. Re-snapshot after saving, because revision may change. Bind an immutable d27 save and native receipt to the strict offline CharacterID 33437 reader. Its saved-state life result cannot be labelled a same-frame live character query.
4. The d27 recorder mark must identify the **actual** post-snapshot and post-control response bytes plus its original screenshot inside that recorder's bounds. A `post_control` field in an operator result alone does not repair the old a02 mark or certify a clean span. The selector row, life report, battle-control and original frames must all come from the new run before revising the K05 explanatory card.

Focused offline test `test_e205_post_control_is_required_after_exactly_one_day` covers available, wrong CombatID and query-error outcomes, checks one date action and the expected post-snapshot revision. The full `test_remaining_live_step.py` suite passed 17/17 in normal Python and 17/17 under `-O` with the verified main-worktree Python 3.14.7 interpreter. This only verifies the static helper branch and synthetic receipts.
