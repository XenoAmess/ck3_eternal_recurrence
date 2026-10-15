from __future__ import annotations

from types import SimpleNamespace

from xar_autoplayer.bridge import family_opportunity_cooldown_v1 as cooldown
from xar_autoplayer.bridge import service as service_module
from xar_autoplayer.bridge.service import GameplayBridgeService


def frame(date=53200728, *, actor=31254, episode="native-31254-saved"):
    return {"schema": "xar.ck3.planning-source-frame/v1", "status": "complete",
            "snapshot_id": "native:1", "revision": 2, "native_revision": 1,
            "date_raw": date, "actor_character_id": actor,
            "episode_run_id": episode, "connection_generation": 1,
            "bridge_pid": 270044}


def empty_plan(sequence=2):
    return {
        "phase": "native_war_entry_forecast_required", "selected_step": "life-advance",
        "_family_cooldown_ordinary_review_v1": True,
        "current_betrothal_fulfillment": True,
        "current_betrothal_status": "held",
        "current_betrothal_choice": {
            "status": "held", "selected_step": None,
            "reasons": ["actual_pair_not_ready", "native_final_can_send_not_true",
                        "native_outcome_not_marriage"]},
        "current_betrothal_relationship": {
            "schema": "xar.ck3.current-first-heir-relationship.v1",
            "status": "available", "read_only": True, "advertised": False,
            "bilateral_verified": True, "native_revision": 1,
            "root_query_sequence": sequence, "heir_character_id": 40526,
            "betrothed_character_id": 40408,
            "primary_spouse_character_id": None, "spouse_character_ids": []},
        "family_education_needs": {
            "roster_complete": True, "living_child_classification_complete": True,
            "known_empty": True, "rows": []},
        "family_child_education_focus": {
            "observations": [], "pending": None, "receipt": None},
    }


def advanced(start, end):
    return {"status": "executed", "selected_step": "life-advance", "result": {
        "step": "life-advance", "progress_status": "postcondition",
        "starting_date_raw": start, "ending_date_raw": end,
        "paused": True, "active_event": None,
        "pending_character_interaction": None}}


def activate(state_dir):
    first = cooldown.observe_after_turn(
        state_dir, frame(), empty_plan(2), advanced(53200728, 53200896))
    assert first["consecutive_noop_dates"] == 1
    second = cooldown.observe_after_turn(
        state_dir, frame(53200896), empty_plan(3),
        advanced(53200896, 53201064))
    assert second["status"] == "active"
    return second


def test_two_distinct_observed_dates_activate_exact_30_days(tmp_path):
    active = activate(tmp_path)
    until = 53201064 + 30 * 24
    assert active["cooldown_until_date_raw"] == until
    assert cooldown.view(tmp_path, frame(until - 1))["status"] == "active"
    assert cooldown.view(tmp_path, frame(until))["status"] == "inactive"


def test_same_date_or_same_query_never_counts_twice(tmp_path):
    cooldown.observe_after_turn(tmp_path, frame(), empty_plan(2),
                                advanced(53200728, 53200896))
    cooldown.observe_after_turn(tmp_path, frame(), empty_plan(2),
                                advanced(53200728, 53200896))
    state = cooldown.observe_after_turn(tmp_path, frame(53200896), empty_plan(2),
                                        advanced(53200896, 53201064))
    assert state["consecutive_noop_dates"] == 1
    assert state["status"] == "inactive"


def test_unknown_or_material_education_does_not_count(tmp_path):
    incomplete = empty_plan()
    incomplete["family_education_needs"]["roster_complete"] = False
    assert cooldown.observe_after_turn(tmp_path, frame(), incomplete,
                                       advanced(53200728, 53200896))["consecutive_noop_dates"] == 0
    child = empty_plan()
    child["family_education_needs"].update(known_empty=False, rows=[{"child": 1}])
    assert cooldown.observe_after_turn(tmp_path, frame(), child,
                                       advanced(53200728, 53200896))["consecutive_noop_dates"] == 0


def test_wartime_or_prewar_full_family_read_never_counts_as_ordinary_noop(tmp_path):
    cooldown.observe_after_turn(tmp_path, frame(), empty_plan(2),
                                advanced(53200728, 53200896))
    prewar = empty_plan()
    prewar.pop("_family_cooldown_ordinary_review_v1")
    assert cooldown.observe_after_turn(tmp_path, frame(53200896), prewar,
                                       advanced(53200896, 53201064))["consecutive_noop_dates"] == 0
    after = cooldown.observe_after_turn(tmp_path, frame(53201064), empty_plan(4),
                                        advanced(53201064, 53201208))
    assert after["consecutive_noop_dates"] == 1
    assert after["status"] == "inactive"


def test_material_readback_resets_but_submission_ack_does_not(tmp_path):
    activate(tmp_path)
    ack = {"status": "executed", "selected_step":
           "submit-observed-first-heir-marriage-v1-private", "result": {
               "status": "submitted", "material_result": False}}
    cooldown.observe_after_turn(tmp_path, frame(53201064), {}, ack)
    assert cooldown.view(tmp_path, frame(53201064))["status"] == "active"
    material = {"status": "executed", "selected_step":
                "query-observed-first-heir-marriage-result-v1-private", "result": {
                    "status": "marriage", "material_result": True}}
    assert cooldown.observe_after_turn(tmp_path, frame(53201064), {}, material)["status"] == "inactive"
    assert cooldown.view(tmp_path, frame(53201064))["consecutive_noop_dates"] == 0


def test_child_focus_material_receipt_resets_active_interval(tmp_path):
    activate(tmp_path)
    receipt = {"status": "executed", "selected_step":
               "private-query-child-education-focus-receipt-v1", "result": {
                   "status": "observed_applied", "observed_applied": True}}
    assert cooldown.observe_after_turn(tmp_path, frame(53201064), {}, receipt)["status"] == "inactive"


def test_critical_full_read_inside_active_interval_does_not_count_noop(tmp_path):
    activate(tmp_path)
    state = cooldown.observe_after_turn(tmp_path, frame(53201064), empty_plan(4),
                                        advanced(53201064, 53201208))
    assert state["status"] == "active"
    assert state["consecutive_noop_dates"] == 0


def test_actor_episode_and_cold_rollback_do_not_inherit_future_observation(tmp_path):
    activate(tmp_path)
    assert cooldown.view(tmp_path, frame(53200896))["status"] == "inactive"
    assert cooldown.view(tmp_path, frame(53201064))["status"] == "inactive"
    activate(tmp_path)
    assert cooldown.view(tmp_path, frame(53201064, actor=999))["status"] == "inactive"
    assert cooldown.view(tmp_path, frame(53201064, episode="other"))["status"] == "inactive"


def service(tmp_path, *, pending=None):
    value = object.__new__(GameplayBridgeService)
    value.driver = SimpleNamespace(
        state_dir=tmp_path,
        _with_internal_planning_view=lambda snapshot, planner: {"pending": pending})
    return value


def snapshot(*, date=53201064):
    return {"snapshot_id": "native:1", "revision": 2, "native_revision": 1,
            "date_raw": date, "episode_run_id": "native-31254-saved",
            "played_character": {"character_id": 31254},
            "diagnostics": {"connection_generation": 1, "bridge_pid": 270044},
            "succession_lifecycle": {"lifecycle": "ordinary_campaign_succession"},
            "paused": True, "map_ready": True, "active_wars": [],
            "active_event": None, "pending_character_interaction": None,
            "one_life_terminal_reason": None}


def skip(value, context, *, prewar=False, wartime=False, plan=None):
    return value._skip_private_family_opportunity_during_cooldown_v1(
        {"plan": plan or {"selected_step": "life-advance"}}, context,
        prewar_arbitration=prewar, wartime_arbitration=wartime)


def test_only_peaceful_ordinary_opportunity_skips(tmp_path):
    activate(tmp_path)
    value = service(tmp_path)
    assert skip(value, snapshot())["plan"]["family_opportunity_cooldown_v1"]["status"] == "active"
    assert skip(value, snapshot(), prewar=True) is None
    assert skip(value, snapshot(), wartime=True) is None
    for key, replacement in (
            ("active_wars", [{"war_id": 1}]),
            ("active_event", {"id": 1}),
            ("pending_character_interaction", {"id": 2}),
            ("one_life_terminal_reason", "dead"),
            ("paused", False)):
        changed = snapshot()
        changed[key] = replacement
        assert skip(value, changed) is None
    changed = snapshot()
    changed["succession_lifecycle"]["lifecycle"] = "succession_pending"
    assert skip(value, changed) is None
    assert skip(value, snapshot(), plan={"selected_step": "query-faction-alerts"}) is None


def test_active_interval_returns_before_any_family_native_reader(tmp_path):
    activate(tmp_path)
    value = service(tmp_path)
    # This driver exposes no family Native query. Reaching the original route
    # would fail; a valid interval returns the unchanged life-advance step.
    planned = {"plan": {"selected_step": "life-advance"}}
    returned = value._plan_private_family_opportunity_v1(planned, snapshot())
    assert returned["plan"]["selected_step"] == "life-advance"
    assert returned["plan"]["family_opportunity_cooldown_v1"]["status"] == "active"


def test_only_actual_ordinary_peace_family_query_gets_counting_marker(tmp_path, monkeypatch):
    value = service(tmp_path)
    value.driver.allow_private_current_first_heir_betrothal_fulfillment = True
    value._plan_private_family_education_v1 = lambda planned, snapshot, **kw: planned
    monkeypatch.setattr(service_module,
        "plan_current_first_heir_betrothal_fulfillment_private",
        lambda driver, planned, snapshot, **kw: {**planned, "plan": {
            **planned["plan"], "current_betrothal_fulfillment": True,
            "current_betrothal_relationship": {"native_revision": 1}}})
    planned = {"plan": {"selected_step": "life-advance"}}
    normal = value._plan_private_family_opportunity_v1(planned, snapshot())
    assert normal["plan"]["_family_cooldown_ordinary_review_v1"] is True
    war = snapshot()
    war["active_wars"] = [{"war_id": 1}]
    assert "_family_cooldown_ordinary_review_v1" not in value._plan_private_family_opportunity_v1(
        planned, war)["plan"]
    assert "_family_cooldown_ordinary_review_v1" not in value._plan_private_family_opportunity_v1(
        planned, snapshot(), prewar_arbitration=True)["plan"]


def test_pending_education_and_marriage_work_bypass_cooldown(tmp_path):
    activate(tmp_path)
    assert skip(service(tmp_path, pending={"id": 1}), snapshot()) is None
    # The family ledger's exact filename is an implementation detail; use its
    # canonical writer path to prove that any pending material work wins.
    from xar_autoplayer import family_marriage_formal_consumer as family
    family._write(tmp_path, {"schema": "xar.ck3.first-heir-marriage-formal.v1",
                             "pending": {"request": 1}, "resolved": None})
    assert skip(service(tmp_path), snapshot()) is None


def test_existing_child_focus_pending_scan_is_shared_with_skip_gate(tmp_path):
    value = service(tmp_path)
    source = {"episode_run_id": "native-31254-saved", "controller_full_id": 31254}
    frame_input = snapshot()
    history = [{"ok": True, "command": "private-select-child-education-focus-v1",
                "result": {"action_request_id": "A", "status": "submitted_verification_pending",
                           "pre_frame": source}}]
    pending = value._unresolved_family_child_focus_v1(frame_input, history)
    assert pending["pending"]["action_request_id"] == "A"
