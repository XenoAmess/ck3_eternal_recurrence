"""One approved mechanism scenario through the existing typed frontend model.

This is not a normal-campaign actor bypass. The external preparation/profile
bytes are pinned by the host; native model identity is observed before Start.
"""
from __future__ import annotations

import json
import os
import time

from .driver import BridgeUnavailableError
from .frontend_fixture_start_contract import (
    FAITH_E01_PROFILE_ID, fixture_frontend_target, require_fixture_frontend_build,
)

PROBE = "probe-frontend-bookmark-model-faith-e01-v1"
BOOKMARK = "activate-frontend-select-bookmark-faith-e01-v1"
CHARACTER = "select-frontend-bookmark-character-faith-e01-v1"
START = "activate-frontend-start-selected-bookmark-faith-e01-v1"
PROBE_CAPABILITY = "game.command.probe-frontend-bookmark-model-v1"
SELECT_CAPABILITY = "game.command.activate-frontend-select-supported-1066-character-v1"
START_CAPABILITY = "game.command.activate-frontend-start-selected-bookmark-v1"


def require_scenario_selected(value: object, target: dict) -> dict:
    expected = {"schema": "ck3-frontend-selected-fixture-scenario-candidate-v1",
        "status": "ready", "read_only": True, "profile_id": FAITH_E01_PROFILE_ID,
        "selected_bookmark_key": target["bookmark_key"],
        "selected_character_name_key": target["character_name_key"],
        "selected_character_government_key": target["government_key"],
        "selected_bookmark_start_date_raw": target["start_date_raw"]}
    if not isinstance(value, dict) or any(type(value.get(key)) is not type(wanted) or value[key] != wanted
            for key, wanted in expected.items()) or value.get("selected_bookmark_group_key") not in (
            None, target["bookmark_group_key"]):
        raise ValueError("fixture scenario lacks its actual selected native model")
    return value


def require_scenario_start_submission(value: object) -> dict:
    if not isinstance(value, dict):
        raise ValueError("fixture scenario Start submission is not an object")
    target = fixture_frontend_target(value.get("policy_binding"))
    expected = {"schema": "ck3-frontend-fixture-scenario-start-submission-v1", "schema_version": 1,
        "profile_id": FAITH_E01_PROFILE_ID, "status": "acknowledged_verification_pending",
        "accepted": True, "pre_start_identity_proven": True, "postcondition_verified": False,
        "fixture_target_identity_proven": False, "requested_character_name_key": target["character_name_key"],
        "uses_ocr": False, "uses_keyboard": False, "uses_mouse": False}
    if any(type(value.get(key)) is not type(wanted) or value[key] != wanted for key, wanted in expected.items()):
        raise ValueError("fixture scenario Start submission has unadmitted identity or proof")
    require_scenario_selected(value.get("selected_candidate"), target)
    ack = value.get("acknowledgement")
    if not isinstance(ack, dict) or any(ack.get(key) != wanted for key, wanted in {
            "step": START, "accepted": True, "status": "acknowledged_verification_pending",
            "backend_id": "native-headless"}.items()):
        raise ValueError("fixture scenario Start ACK is malformed")
    binding = value.get("binding")
    if not isinstance(binding, dict) or set(binding) != {"bridge_pid", "connection_generation"} or any(
            type(binding[key]) is not int or binding[key] <= 0 for key in binding):
        raise ValueError("fixture scenario lacks its actual frontend process binding")
    return value


def _require_actual4_capabilities(capabilities: dict) -> dict:
    binding = require_fixture_frontend_build(capabilities)
    rows = [capabilities]
    while rows:
        row = rows.pop()
        if not isinstance(row, dict):
            continue
        rows.extend(row.get("backends", []))
        diagnostics = row.get("diagnostics")
        hello = diagnostics.get("hello") if isinstance(diagnostics, dict) else None
        if isinstance(hello, dict) and hello.get("pid") == binding["bridge_pid"] and (
                hello.get("connection_generation") == binding["connection_generation"]) and (
                hello.get("expected_ck3_version") != "1.20.0.4"):
            raise ValueError("episode01 fixture scenario is bound only to actual 1.20.0.4")
    return binding


def selected_model(model: dict, target: dict, *, require_selected: bool) -> dict:
    keys = model.get("candidate_keys")
    index = model.get("supported_1066_candidate_index")
    selected = model.get("selected_character_index")
    if not (model.get("accepted") is True and model.get("status") == "identity_ready"
            and model.get("candidate_identity_ready") is True
            and model.get("selected_bookmark_key") == target["bookmark_key"]
            and model.get("selected_bookmark_group_key") in (None, target["bookmark_group_key"])
            and type(model.get("selected_date_low_raw")) is int
            and model["selected_date_low_raw"] == target["start_date_raw"]
            and isinstance(keys, list) and type(index) is int and 0 <= index < len(keys)
            and keys[index] == target["character_name_key"]
            and type(selected) is int and -1 <= selected < len(keys)
            and (not require_selected or selected == index)
            and model.get("supported_1066_government_key") == target["government_key"]
            and model.get("supported_1066_date_matches") is True):
        raise BridgeUnavailableError("episode01 native bookmark identity is not ready; "
            f"reason={model.get('unavailable_reason')!r}, bookmark={model.get('selected_bookmark_key')!r}, "
            f"selected={selected!r}, target={index!r}")
    return require_scenario_selected({"schema": "ck3-frontend-selected-fixture-scenario-candidate-v1",
        "status": "ready", "read_only": True, "profile_id": FAITH_E01_PROFILE_ID,
        "selected_bookmark_key": model["selected_bookmark_key"],
        "selected_bookmark_group_key": model.get("selected_bookmark_group_key"),
        "selected_character_name_key": keys[index],
        "selected_character_government_key": model["supported_1066_government_key"],
        "selected_bookmark_start_date_raw": model["selected_date_low_raw"],
        "native_model": model}, target)


def submit_scenario_start(driver) -> dict:
    policy = getattr(driver, "frontend_fixture_start_policy_binding", None)
    target = fixture_frontend_target(policy)
    if driver.episode_projection != "native_campaign" or not policy.get("policy_sha256") or driver.state_dir is None:
        raise BridgeUnavailableError("scenario Start requires the bound native_campaign fixture policy")
    binding = _require_actual4_capabilities(driver.capabilities())
    path = driver.state_dir / "frontend-fixture-start-requests.jsonl"

    def journal(phase, **detail):
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"phase": phase, "binding": binding, **detail}, ensure_ascii=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    def bound():
        if _require_actual4_capabilities(driver.capabilities()) != binding:
            raise BridgeUnavailableError("scenario selection crossed the admitted frontend process")

    def execute(step):
        bound()
        capability = PROBE_CAPABILITY if step == PROBE else (START_CAPABILITY if step == START else SELECT_CAPABILITY)
        return driver._execute_primitive_step(step, expected_revision=0,
            required_capability=capability, allow_frontend_revision_zero=True)

    def wait_model(require_selected):
        deadline = time.monotonic() + min(10.0, driver.frontend_transition_timeout_seconds)
        while True:
            model = execute(PROBE)
            try:
                value = selected_model(model, target, require_selected=require_selected)
            except BridgeUnavailableError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(min(0.1, max(0, deadline - time.monotonic())))
            else:
                return model, value

    # Share the existing fixture claim file: changing tools or reconnecting cannot
    # submit a second Start after an unknown result.
    with driver._driver_state_lock:
        if getattr(driver, "_frontend_fixture_start_claimed", False):
            raise BridgeUnavailableError("fixture Start was already attempted; requests cannot be replayed")
        with path.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps({"phase": "claimed-before-any-mutation", "binding": binding,
                "policy_binding": policy}, ensure_ascii=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        driver._frontend_fixture_start_claimed = True
    before = driver.query_frontend_gui_route_v1()
    if before.get("route") != "bookmarks":
        raise BridgeUnavailableError("scenario Start requires the actual bookmarks route")
    model = execute(PROBE)
    bookmark_ack = None
    if model.get("selected_bookmark_key") != target["bookmark_key"]:
        journal("before-native-bookmark-selection-request", step=BOOKMARK, retry_allowed=False)
        bookmark_ack = execute(BOOKMARK)
        model, _ = wait_model(False)
    else:
        selected_model(model, target, require_selected=False)
    selection_ack = None
    if model["selected_character_index"] != model["supported_1066_candidate_index"]:
        journal("before-native-selection-request", step=CHARACTER, retry_allowed=False)
        selection_ack = execute(CHARACTER)
    _, selected = wait_model(True)
    bound()
    if driver.query_frontend_gui_route_v1().get("route") != "bookmarks":
        raise BridgeUnavailableError("scenario Start lost the actual selected-bookmark route")
    journal("before-native-start-request", step=START, selected_candidate=selected, retry_allowed=False)
    ack = execute(START)
    result = require_scenario_start_submission({"schema": "ck3-frontend-fixture-scenario-start-submission-v1",
        "schema_version": 1, "profile_id": FAITH_E01_PROFILE_ID, "accepted": True,
        "status": "acknowledged_verification_pending", "pre_start_identity_proven": True,
        "postcondition_verified": False, "fixture_target_identity_proven": False,
        "requested_character_name_key": target["character_name_key"], "policy_binding": policy,
        "binding": binding, "before": before, "selected_candidate": selected,
        "bookmark_acknowledgement": bookmark_ack, "selection_acknowledgement": selection_ack,
        "acknowledgement": ack, "uses_ocr": False, "uses_keyboard": False, "uses_mouse": False})
    journal("native-start-acknowledged-post-state-pending", acknowledgement=ack)
    return result
