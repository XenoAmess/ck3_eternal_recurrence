"""Readonly zero-stock capture candidates and exact-zero retained writer facts.

No clock, admission or casualty formula is duplicated. Existing native-produced
next dates and pointer buckets feed the existing source-owned projections.
"""
from __future__ import annotations

from collections.abc import Mapping

from .army_actual_supply_parent_join_summary import join_actual_supply_parent_writer_observations_v1
from .army_next_updater_write_projection import project_source_derived_next_updater_writes_v1
from .army_source_derived_next_daily_supply_frame_projection import project_native_next_daily_supply_schedule_v1
from .army_update_clock_contract import normalize_army_update_clock_v1


def _all_known(values: tuple[bool | None, ...]) -> bool | None:
    if False in values:
        return False
    return True if all(value is True for value in values) else None


def project_zero_stock_next_callback_candidate_12004(row: dict) -> dict:
    """One next-day capture opportunity, conditional on unchanged earlier inputs.

    True selects a useful zero-entry observation window. It does not assert that
    stock remains zero after the rate, a budget is positive, or a writer executes.
    Selected-phase readiness is independent of other unavailable phase headers.
    """
    schedule = project_native_next_daily_supply_schedule_v1(row)
    writes = project_source_derived_next_updater_writes_v1(row)
    clock = normalize_army_update_clock_v1(row.get("army_update_clock_v1"))
    source = schedule.get("source_next_pair") if schedule else None
    coherent = None
    if source and source["ready"] and clock and clock["ready"]:
        if any(clock[left] != source[right] for left, right in (
            ("current_date_raw", "current_date_raw_i32"),
            ("native_day_index", "current_native_day_index_raw_i32"),
        )):
            raise ValueError("zero-stock candidate clock differs from same-row native next seed")
        coherent = True
    frames = schedule["prospective_frames"] if schedule else []
    selected = frames[0] if len(frames) == 1 and source and source["ready"] else None
    positions = (list(selected["matching_positions"])
                 if selected and selected["conditional_bucket_occurrences_ready"] else None)
    count = len(positions) if positions is not None else None
    stock = row.get("current_supply_raw")
    zero = stock == 0 if type(stock) is int and -(1 << 63) <= stock < (1 << 63) else None
    admission = writes["next_admission"]
    admitted = admission["admitted"] if admission["ready"] else None
    typed = (row.get("status") == "available" and type(row.get("native_carmy_id")) is int
             and type(row.get("army_id")) is int)
    candidate = _all_known((typed, zero, count > 0 if count is not None else None,
                            admitted, coherent))
    return dict(
        source="existing_next_pair_bucket_and_updater_gate_join_12004",
        conditional_zero_entry_capture_candidate=candidate,
        observed_current_stock_is_exact_zero=zero,
        same_row_clock_seed_matches=coherent,
        next_date_raw_i32=selected["date_raw_i32"] if selected else None,
        next_native_day_index_raw_i32=selected["native_day_index_raw_i32"] if selected else None,
        next_selected_phase_i32=selected["selected_phase_index_i32"] if selected else None,
        conditional_original_pointer_positions=positions,
        conditional_callback_opportunity_count=count,
        next_admission=admission,
        condition="captured receiver, stock, bucket membership and all non-date gate inputs unchanged through earlier stages",
        repeated_occurrences_are_independent=True,
        successful_updater_count=None,
        zero_stock_at_actual_writer_observed=False,
        physical_loss_observed=False,
        complete_cycle_observed=False,
        full_daily_supply_transition_ready=False,
        full_monthly_ready=False,
    )


def select_actual_zero_stock_supply_preferred_12004(
    row: Mapping, *, game_version: str, executable_sha256: str,
    callback_after_sequence: int, loss_after_sequence: int,
) -> dict:
    """Select single complete direct supply debits with writer-time stock == 0.

    This narrow positive witness deliberately leaves residual, combined and full
    interval totals separate. It does not use callback entry/return stock or net
    Army strength. Exact-build/session normalization remains with the query owner.
    """
    result = dict(source="keyed_daily_supply_preferred_exact_zero_writer_facts",
                  positive_invocations=[], positive_physical_debit_observed=False,
                  selected_invocation_debit_sum=None, unknown_reasons=[],
                  complete_interval_loss_total_ready=False, complete_cycle_observed=False)
    for key in ("actual_supply_callback_observations_v1", "actual_loss_writer_observations_v1"):
        family = row.get(key)
        if not isinstance(family, Mapping) or family.get("observer_installed") is not True:
            result["unknown_reasons"].append(key + ".observer_installed")
    if result["unknown_reasons"]:
        return result
    joined = join_actual_supply_parent_writer_observations_v1(
        row, game_version=game_version, executable_sha256=executable_sha256,
        callback_after_sequence=callback_after_sequence, loss_after_sequence=loss_after_sequence)
    result["unknown_reasons"] = list(joined["unknown_reasons"])
    if result["unknown_reasons"]:
        return result
    callbacks = {event["sequence"]: event for event in
                 row["actual_supply_callback_observations_v1"]["events"]}
    for event in joined["events"]:
        debit = event["physical_debit_soldiers"]
        callback = callbacks.get(event["callback_sequence"])
        if (event["status"] == "joined" and event["source_supply_preferred"] is True
                and type(event["stock_at_writer_entry_raw"]) is int
                and event["stock_at_writer_entry_raw"] == 0
                and type(debit) is int and debit > 0 and callback
                and callback["caller_return_rva"] == 0x2A9AB4B):
            result["positive_invocations"].append(dict(event))
    if result["positive_invocations"]:
        result["positive_physical_debit_observed"] = True
        result["selected_invocation_debit_sum"] = sum(
            event["physical_debit_soldiers"] for event in result["positive_invocations"])
    return result


def successful_supply_occurrences_to_zero_12004(stock_raw, capacity_raw, monthly_raw):
    """Exact count for constant captured signed rate/cap, not a calendar forecast.

    One opportunity means one SUCCESSFUL original bucket pointer callback.
    ADD precedes capacity clamp, so reducing cap does not clamp before ADD.
    First reaching zero may already yield physical loss in that invocation.
    """
    values = dict(current_supply_raw=stock_raw, current_supply_capacity_raw=capacity_raw,
                  current_supply_change_monthly_raw=monthly_raw)
    absent = [key for key, value in values.items()
              if type(value) is not int or not -(1 << 63) <= value < (1 << 63)]
    if absent:
        return dict(ready=False, required_fields=absent, successful_bucket_occurrences=None)
    if stock_raw < 0 or capacity_raw < 0:
        return dict(ready=False, required_fields=["nonnegative_actual_stock_and_capacity"],
                    successful_bucket_occurrences=None)
    if monthly_raw >= 0:
        return dict(ready=False, required_fields=["current_signed_monthly_raw_below_zero"],
                    successful_bucket_occurrences=None)
    after_one = min(capacity_raw, max(0, stock_raw + monthly_raw))
    count = (0 if stock_raw == 0 else 1 if after_one == 0 else
             1 + (after_one + (-monthly_raw) - 1) // (-monthly_raw))
    return dict(ready=True, required_fields=[], successful_bucket_occurrences=count,
                first_successful_post_stock_raw=after_one,
                first_zero_same_invocation_can_apply_supply_loss=True,
                first_new_zero_writer_opportunity=max(1, count),
                bucket_visits=None, actual_days=None,
                condition="same captured rate/cap and successful updater at each original pointer occurrence",
                physical_loss_predicted=False)


def plan_zero_stock_preparation_12004(
    *, army_query, sites, snapshot=None, commands=(), active_wars=None,
    commander_queries=(), available_steps=(), army_ids=(18, 93),
):
    """Compose existing R05/query/preview/war-route decision inputs, with no calls.

    Remote target previews contain current target operands, not an actual
    post-arrival monthly rate or a candidate commander's hypothetical capacity.
    Such gaps stay required_fields. Never copy a current rate to another site.
    """
    from xar_autoplayer.strategy import (
        _audit_war_route, _fresh_move_route_preview, _same_frame_readonly_result_lease,
        enemy_armies_from_wars,
    )
    from .army_commander_assignment import assign_army_commander_v1_step
    from .army_commander_candidates import query_army_commander_candidates_v1_step
    from .army_current_province_supply_contributors_contract import normalize_current_province_supply_contributors_v1
    from .episode04_starvation_loss_12004 import EXE_SHA256
    from .war_contract import preview_move_army_step, move_army_step
    from .army_target_land_supply_projection_12004 import project_conditional_target_land_rate_12004

    if not isinstance(army_query, dict) or not isinstance(sites, dict):
        raise ValueError("existing Army query and site packet must be objects")
    if any(type(value) is not int or value < 0 for value in army_ids):
        raise ValueError("full public Army IDs are required")
    rows = army_query.get("army_strengths", army_query.get("rows", []))
    if not isinstance(rows, list):
        raise ValueError("Army query rows must be an array")
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    available = set(available_steps)
    lease_ready = _same_frame_readonly_result_lease(army_query, snapshot)
    frame_required = [] if lease_ready else ["army_query.same_paused_snapshot_revision_native_revision_generation_episode"]
    source = army_query.get("source")
    if (not isinstance(source, dict) or source.get("game_version") != "1.20.0.4"
            or source.get("executable_sha256") != EXE_SHA256):
        frame_required.append("army_query.source.exact_1_20_0_4_executable_binding")
    if snapshot.get("paused") is not True:
        frame_required.append("snapshot.paused")
    if active_wars is None:
        frame_required.append("same_frame_complete_active_wars_and_enemy_positions_routes")
    elif not isinstance(active_wars, list):
        raise ValueError("actual active_wars must be an array or unknown")
    enemies = list(enemy_armies_from_wars(active_wars)) if isinstance(active_wars, list) else []
    if any(type(enemy.get("current_province_id")) is not int for enemy in enemies):
        frame_required.append("active_wars.enemy_current_province_id")
    site_ids = []
    for site in [*sites.get("candidates", []), *sites.get("anchors", [])]:
        province = site.get("province_id") if isinstance(site, dict) else None
        if type(province) is int and province > 0 and province not in site_ids:
            site_ids.append(province)
    candidates = []
    required_steps = []
    controlled = {value.get("army_id"): value for value in snapshot.get("player_armies", [])
                  if isinstance(value, dict)}
    for army_id in army_ids:
        matching = [value for value in rows if isinstance(value, dict) and value.get("army_id") == army_id]
        row = matching[0] if len(matching) == 1 else {}
        army = controlled.get(army_id, {})
        origin = army.get("current_province_id")
        row_required = list(frame_required)
        if army.get("controllable") is not True:
            row_required.append("snapshot.controllable_player_army")
        if row.get("status") != "available" or type(row.get("native_carmy_id")) is not int:
            row_required.append("available_current_ArmyStrength_with_dual_FullIDs")
        contributor = normalize_current_province_supply_contributors_v1(
            row.get("current_province_supply_contributors_v1"))
        if type(origin) is not int and contributor and type(contributor["province_id"]) is int:
            origin = contributor["province_id"]
            row_required.append("snapshot.current_Province_matches_observed_current_query_Province")
        if contributor:
            if (contributor["subject_army_id"] != army_id
                    or contributor["subject_carmy_id"] != row.get("native_carmy_id")):
                raise ValueError("R05 supply qualification belongs to another Army FullID")
            if type(origin) is int and contributor["province_id"] != origin:
                raise ValueError("R05 current Province differs from snapshot")
        eligible_count = None
        if contributor:
            own = [value for value in contributor["occurrences"] if value["army_id"] == army_id
                   and value["native_carmy_id"] == row.get("native_carmy_id")
                   and value["included"] is True and value["status"] == "available"]
            counts = [value["native_eligible_current_soldiers"] for value in own]
            if counts and all(type(value) is int and value == counts[0] for value in counts):
                eligible_count = counts[0]
        if eligible_count is None:
            row_required.append("current_province_supply_contributors_v1.subject_native_eligible_current_soldiers")
        current_commander = None
        probes = []
        commander_ready = False
        for result in commander_queries:
            if not isinstance(result, dict) or not _same_frame_readonly_result_lease(result, snapshot):
                continue
            family = result.get("army_commander_candidates", result)
            if family.get("army_id") != army_id or family.get("native_carmy_id") != row.get("native_carmy_id"):
                continue
            commander_ready = True
            current_commander = family.get("current_commander", {}).get("character_id")
            for person in family.get("candidates", []):
                character = person.get("character_id")
                if (type(character) is int and character > 0 and character != current_commander
                        and person.get("available") is True and person.get("final_eligibility_observable") is True
                        and person.get("can_assign") is True):
                    probes.append(dict(character_id=character,
                        existing_assignment_step=assign_army_commander_v1_step(army_id, character),
                        actual_lower_capacity_ready=False,
                        required_fields=["actual_assignment_readback.current_supply_capacity_raw",
                                         "actual_assignment_readback.current_supply_change_monthly_raw"]))
        if not commander_ready:
            required_steps.append(query_army_commander_candidates_v1_step(army_id))
        for province in site_ids:
            missing = list(row_required)
            rejected = []
            here = type(origin) is int and province == origin
            preview = None
            route_hops = None
            audit = None
            if type(origin) is not int:
                missing.append("snapshot.current_province_id")
            elif here:
                audit = _audit_war_route([origin], origin_province_id=None,
                                        target_province_id=province, enemies=enemies)
                route_hops = 0
            else:
                preview = _fresh_move_route_preview(list(commands), army_id=army_id,
                    origin_province_id=origin, target_province_id=province,
                    date_raw=snapshot.get("date_raw"), snapshot=snapshot)
                if not preview or preview.get("status") != "available":
                    missing.append("fresh_available_native_route_preview")
                    required_steps.append(preview_move_army_step(army_id, province))
                else:
                    audit = _audit_war_route(preview.get("route_province_ids"),
                        origin_province_id=origin, target_province_id=province, enemies=enemies)
                    route_hops = len(audit.get("route_province_ids", []))
            if audit and audit["status"] == "unsafe":
                rejected.append("ordinary_war_route_audit_unsafe")
            elif not audit or audit["status"] != "safe":
                missing.append("ordinary_war_route_audit_safe")
            rate = row.get("current_supply_change_monthly_raw") if here else None
            target_projection = None
            if not here:
                if preview and preview.get("status") == "available":
                    target_projection = project_conditional_target_land_rate_12004(
                        row,preview,same_frame_inputs=lease_ready)
                    if target_projection["full_land_rate_ready"]:
                        rate=target_projection["conditional_full_land_rate_raw"]
                        if rate>=0:rejected.append("conditional_target_monthly_not_negative")
                    else:
                        missing.extend(target_projection["missing_inputs"])
                        missing.append("actual_target_arrival_ArmyStrength.current_supply_change_monthly_raw")
                else:missing.append("conditional_target_rate_requires_fresh_preview")
            elif type(rate) is int and rate >= 0:
                rejected.append("observed_current_monthly_not_negative")
            if eligible_count is not None and eligible_count <= 0:
                rejected.append("observed_no_positive_supply_eligible_current")
            arithmetic = successful_supply_occurrences_to_zero_12004(
                row.get("current_supply_raw"), row.get("current_supply_capacity_raw"), rate)
            missing.extend(arithmetic["required_fields"])
            if type(origin) is int and here and not contributor:
                missing.append("same_current_Province_native_supply_qualification")
            clock = None
            if all(row.get(key) is not None for key in (
                "army_update_clock_v1", "source_derived_next_daily_supply_frame_inputs_v1",
                "future_daily_supply_schedule_inputs_v1")):
                clock = project_zero_stock_next_callback_candidate_12004(row)
                if here and clock["next_admission"]["admitted"] is False:
                    rejected.append("observed_next_updater_gate_rejected")
                elif here and clock["next_admission"]["admitted"] is not True:
                    missing.append("existing_R05_next_updater_admission")
            else:
                missing.append("existing_R05_next_pair_all30_clock_and_admission")
            if army.get("in_combat") is not False or army.get("retreating") is not False:
                missing.append("snapshot.actual_not_in_combat_and_not_retreating")
            candidates.append(dict(army_id=army_id, native_carmy_id=row.get("native_carmy_id"),
                province_id=province, at_observed_current_Province=here,
                observed_stock_raw=row.get("current_supply_raw"),
                observed_capacity_raw=row.get("current_supply_capacity_raw"),
                observed_current_monthly_raw=row.get("current_supply_change_monthly_raw") if here else None,
                subject_observed_current_monthly_raw=row.get("current_supply_change_monthly_raw"),
                preparation_monthly_raw=rate,
                preparation_rate_basis="observed_current" if here else "conditional_target_after_normal_arrival",
                conditional_target_rate_projection_v1=target_projection,
                actual_arrival_readback_required=not here,
                supply_eligible_current_soldiers=eligible_count,
                successful_opportunities=arithmetic, native_route_hops=route_hops,
                route_audit=audit, route_preview=preview,
                current_commander_character_id=current_commander,
                lower_capacity_probe_candidates=probes,
                lower_capacity_ready=False,
                required_fields=list(dict.fromkeys(missing)), rejected_reasons=rejected,
                existing_R05_clock=clock,
                ready=not missing and not rejected and arithmetic["ready"]))
    ready = sorted((value for value in candidates if value["ready"]), key=lambda value: (
        value["successful_opportunities"]["successful_bucket_occurrences"],
        value["native_route_hops"], value["army_id"], value["province_id"]))
    selected = ready[0] if ready else None
    required_steps = list(dict.fromkeys(required_steps))
    if frame_required or any(not row for row in rows):
        required_steps.insert(0, "query-army-strengths-v1")
    if selected:
        desired=("life-advance-one-day" if selected["at_observed_current_Province"] else
                 move_army_step(selected["army_id"],selected["province_id"]))
        step=desired if desired in available else None
        required_step=None if step else desired
    else:
        step = next((value for value in required_steps if value in available), None)
        required_step = None if step else (required_steps[0] if required_steps else "query-army-strengths-v1")
    return dict(policy="one-life-turn-v1", phase="native_war_r05_zero_stock_preparation",
                selected_step=step, required_step=required_step,
                reason="use observed current or source-bound conditional target negative rate, actual supply eligibility and existing route audit; recapture after arrival",
                r05_zero_stock_preparation_v1=dict(candidates=candidates, selected=selected,
                    ranking="fewest_successful_original_bucket_occurrences_then_native_route_hops",
                    shortest_actual_calendar_preparation_ready=False,
                    required_steps=required_steps,
                    required_fields=list(dict.fromkeys(field for value in candidates for field in value["required_fields"])),
                    physical_loss_observed=False, game_actions_executed=0))
