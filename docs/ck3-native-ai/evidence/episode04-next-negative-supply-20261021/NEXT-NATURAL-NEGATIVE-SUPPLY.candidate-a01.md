# Next natural negative-supply opportunity

machine_id: desktop-3fevhd2-1c74096080. Research: 2026-10-21 UTC. Source-only decision recipe; no SDK/Game actions or new qualification. Exact source pins are in the companion index. R226's completed split is consumed and must not be replayed.

The current source-bound result is parent75/child175 at2624, child stock100/cap100/+20 monthly, no headroom and day0. Root's subsequent current survey reports Army18=1194 embarked at8645, stock300/cap300/rate0, and six nearby land previews eligible/+20 with limit4380..5657/usage0. The latter survey is Root-reported, not independently queried by this author. These facts give no negative-rate land route for either small Army.

## What actually makes the land rate negative

The existing conditional .4 target consumer pins original body RVA24E5180,3674B,SHA36ffa60acf90c96a61299625427706a7891c83c8d337d38bb4b5b62c24e72fb3. Its shared arithmetic distinguishes:

- U<=L: eligible may add loaded gain. Ineligible with province component P=0 yields zero, not an automatic supply loss.
- U>L: gain is not added. Loss is the loaded minimum/maximum clamp of excess usage times the loaded slope. Local P-loss must remain negative after the actual commander divisor/clamp for a negative final rate.

Thus enemy territory, walking, siege and winter are not sufficient labels. They matter only through actually captured eligibility, eligible usage U, native limit L, province component P and loaded/commander operands. A reduced winter limit helps only if real U exceeds it; siege soldiers matter only if the native contributor roster includes them. Do not substitute total displayed soldiers or historical6689 for current U.

## Cheapest next discriminator: the already embarked Army

Reuse any already retained Army18 full row; otherwise the owner may obtain one bounded selected full query. Read current_fleet_supply_tick_inputs_v1: current_native_date_low32, fleet_day_raw, loaded_fleet_day_sentinel_raw, terrain_magic_38_raw, terrain_modifier_772_raw, loaded_fleet_loss_raw, commander_modifier_1a9_raw, loaded_divisor_floor_raw, loaded_max_loss_raw; also retain actual current_supply_change_monthly_raw.

The existing fleet projection is explicitly conditional, not next-callback qualification. It identifies concrete zero branches: future fleet date; terrain magic not0x4744624F; or positive terrain772 modifier. If the only blocker is a known finite future date, terrain permits loss, loaded loss is positive, and the commander-adjusted negative branch is supported, the owner can choose a bounded ordinary wait to that date and independently read the actual negative rate. If fields are missing, the due time is too long, or another zero branch remains, do not sail/wait blindly. No new embarkation or troop raising is needed for this discriminator.

After an actual stock decrease, preview a legitimate reachable land destination. The existing conditional target projection can screen it; after arrival, actual full headroom and positive final rate must be reread before one bounded recovery interval. Predicted rate is not observed growth. Army18's stock300 does not imply a short path to R05's stock<10 threshold.

## Land fallback: legitimate native raising, only if worthwhile

The available public read is ck3_query_player_default_raise_v1(expected_revision=F.revision), returning player_default_raise. Require current actor/date/native revision, default_raise_legality_ready, native_default_raise_legal, default_raise_province_id, and unraised_troops_ready/unraised_soldiers/scale1/scope=native_all_actor_categories. Check the actual case/tool capability and current war/cash commitments before acting.

If the returned reserve can plausibly create a real eligible concentration exceeding the selected fresh target limit, the existing normal action is ck3_execute_step(step='raise-troops-default',expected_revision=F.revision), once. This is the native command constructor/final validator/submit_copy path, not the GUI war-raise-all alias. submitted is only an ACK. Independently observe the roster, gathering completion, actual native CArmy resolution and complete eligible contributor union. Raising does not guarantee every reserve soldier arrives in one Army or one province.

For each finite candidate, a fresh preview uses ck3_execute_step(step='preview-move-army-ID-to-TARGET',expected_revision=F.revision). Its route_preview.province_supply.target supplies native usage/limit and captured_target_land_supply_inputs_v1. Existing project_conditional_target_land_rate_12004(selected_full,body['route_preview'],same_frame_inputs=True,selected_rows=actual_union) screens conditional rate. The same-frame lease must be real. If complete inputs do not yield rate<0, do not move merely to seek loss. Actual arrival still requires a fresh full read. Native unraised count, ally labels, route ACK and conditional sums never replace actual U/negative rate.

Only after R08 cleanup, reuse the current finite Move/day path: fresh unique Move, independent stored route, original advance_day(1,...allow_event_boundary=True), modal continuation, and bounded endpoint checks. Consume enough naturally to create headroom, then disperse/return to an actually positive-rate safe point. Stop on unknown action, combat/route invalidation, or missing operands; never repeat split or restart the spent pilot. R05 remains conditional on naturally stock<1000000 and its full native loss fences. The first B growth need not wait for that much longer threshold.
