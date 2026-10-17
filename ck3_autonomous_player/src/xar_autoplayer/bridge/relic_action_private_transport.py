"""Finite relic UI actions through the actual Driver primitive, never retry ACKs."""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import uuid

from .driver import BridgeUnavailableError, PreSubmissionRevisionMismatchError, UnsupportedStepError
from .ingame_ui_contract import NAVIGATE_CAPABILITY, NAVIGATE_STEP
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .player_holy_site_private_transport import _ref
from .player_holy_site_relic_permissions_private_transport import _boolean, _integer
from .title_map_navigation_contract import (
    managed_campaign_title_map_navigation_v1_binding, normalize_title_map_navigation_v1_binding,
)
from .version_identity import CK3_12004, require_exact_native_build

PERMISSION = "allow_private_holy_site_relic_actions"
OPERATIONS = {"select_relic_artifact", "set_relic_slot", "enshrine_relic", "remove_relic"}
WIRE_KEYS = {"relic_artifact_id", "relic_slot_index", "relic_desired_selected",
    "relic_expected_effective_slot_index", "relic_expected_replacing_empty",
    "relic_expected_replacing_artifact_id", "relic_expected_preview_sha256"}


def _new_request_id() -> str:
    return 'relic-action-' + uuid.uuid4().hex


def validate_relic_action_request_v1(operation: str, holy_site_id: int, fields: Mapping[str, object]) -> dict[str, object]:
    if operation not in OPERATIONS or not isinstance(fields, dict) or not set(fields) <= WIRE_KEYS:
        raise ValueError("unsupported finite relic operation or wire fields")
    _ref(holy_site_id, "holy_site_id", nullable=False)
    required = {"relic_artifact_id"}
    if operation == "set_relic_slot":
        required = {"relic_slot_index", "relic_desired_selected"}
    elif operation in {"enshrine_relic", "remove_relic"}:
        required |= {"relic_expected_replacing_empty", "relic_expected_preview_sha256"}
        if operation == "enshrine_relic":
            required.add("relic_expected_effective_slot_index")
        empty = fields.get("relic_expected_replacing_empty")
        _boolean(empty, "expected_replacing_empty")
        if not empty:
            if operation == "remove_relic":
                raise ValueError("remove has no effective destination or replacing artifact")
            required.add("relic_expected_replacing_artifact_id")
    if set(fields) != required:
        raise ValueError("relic action fields must exactly match this operation and frozen replacement")
    for name, value in fields.items():
        if name.endswith("artifact_id"):
            _ref(value, name, nullable=False)
        elif name.endswith("slot_index"):
            _integer(value, name, low=0, high=4095)
        elif name in {"relic_desired_selected", "relic_expected_replacing_empty"}:
            _boolean(value, name)
        elif not isinstance(value, str) or re.fullmatch('[0-9a-f]{64}', value) is None:
            raise ValueError("relic action requires a frozen lowercase SHA-256 preview identity")
    return {"window_kind": "holy_site", "operation": operation, "subject_id": holy_site_id, **fields}


def _selection(value: object, field: str) -> dict[str, object]:
    keys = {"available", "artifact_id", "slot_index", "slot_artifact_ids", "unavailable_reason"}
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError("native relic selection shape differs: " + field)
    _boolean(value["available"], field + ".available")
    _ref(value["artifact_id"], field + ".artifact_id")
    _integer(value["slot_index"], field + ".slot_index", nullable=True, low=0, high=4095)
    if not isinstance(value["unavailable_reason"], str):
        raise ValueError("native relic selection reason must preserve the native string")
    if value["available"]:
        ids = value["slot_artifact_ids"]
        if not isinstance(ids, list) or len(ids) > 4096 or value["unavailable_reason"]:
            raise ValueError("native relic observed slots differ from their bounded source")
        for item in ids:
            _ref(item, field + ".slot artifact_id")
        if value["slot_index"] is not None and value["slot_index"] >= len(ids):
            raise ValueError("native relic selected slot is not an actual row")
    elif value["slot_artifact_ids"] is not None or not value["unavailable_reason"]:
        raise ValueError("unavailable relic selection must keep its diagnostic and null slot array")
    return value


def normalize_relic_action_result_v1(raw: object, *, before: Mapping[str, object],
        operation: str, holy_site_id: int, fields: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(raw, dict) or raw.get("schema") != "ck3-ingame-ui-window-v1":
        raise ValueError("native relic action lacks the production navigation result")
    expected = {"window_kind": "holy_site", "window_name": "holy_site_window", "requested_subject_id": holy_site_id,
                "native_revision": before["native_revision"], "date_raw": before["date_raw"], "paused": True,
                "played_character_id": before["played_character"]["character_id"], "backend_id": "native-headless",
                "native_backend_id": "ck3-1.20.0.4-native-ingame-ui-v1"}
    for key, target in expected.items():
        if type(raw.get(key)) is not type(target) or raw[key] != target:
            raise ValueError("native relic action crossed its production frame: " + key)
    if require_exact_native_build(raw.get("game_version"), raw.get("executable_sha256")) != CK3_12004:
        raise ValueError("native relic action result requires exact 1.20.0.4")
    keys = {"available", "status", "loaded_source_pins_verified", "native_dispatch_attempted", "dispatch_invoked",
        "verification_pending", "already_in_requested_state", "selection_postcondition_observed",
        "original_button_enabled_observed", "original_button_enabled", "actual_button_presentation_observed",
        "button_child_path", "frozen_preview_verified", "gameplay_command_may_have_been_queued",
        "business_outcome_observed", "action_ready", "before", "after", "unavailable_reason"}
    nested = raw.get("holy_site_relic_action")
    if not isinstance(nested, dict) or set(nested) != keys:
        raise ValueError("native relic action semantic result shape differs")
    for name in keys - {"status", "original_button_enabled", "button_child_path", "before", "after", "unavailable_reason"}:
        _boolean(nested[name], "relic action " + name)
    for name in ("status", "button_child_path", "unavailable_reason"):
        if not isinstance(nested[name], str):
            raise ValueError("native relic action string is malformed: " + name)
    _boolean(nested["original_button_enabled"], "original_button_enabled", nullable=not nested["original_button_enabled_observed"])
    if not nested["original_button_enabled_observed"] and nested["original_button_enabled"] is not None:
        raise ValueError("unobserved native button predicate cannot become false")
    if nested["business_outcome_observed"] is not False or nested["action_ready"] is not False:
        raise ValueError("native relic ACK cannot claim business success or action readiness")
    if nested["native_dispatch_attempted"] or nested["available"]:
        if (any(raw.get(name) is not True for name in ("application_owner_thread_verified", "gui_owner_binding_verified",
                "window_exists", "effective_visible", "enabled", "subject_id_available"))
                or raw.get("current_subject_id") != holy_site_id
                or any(type(raw.get(name)) is not int or raw[name] <= 0 for name in (
                    "thread_id", "pump_epoch", "gui_context_address", "gui_owner_address"))
                or raw.get("rng_owner_is_ui_admission_gate") is not False):
            raise ValueError("native relic dispatch lacks actual original window and application/GUI owner admission")
        modal = raw.get("modal_admission")
        if (not isinstance(modal, dict) or any(modal.get(name) is not True for name in (
                "attempted", "header_read", "receivers_verified"))
                or type(modal.get("effective_visible_count")) is not int or modal["effective_visible_count"] != 0):
            raise ValueError("native relic dispatch lacks the original modal barrier observation")
    prior = _selection(nested["before"], "before")
    after = _selection(nested["after"], "after")
    for name in ("available", "status", "native_dispatch_attempted", "dispatch_invoked", "verification_pending", "unavailable_reason"):
        if type(raw.get(name)) is not type(nested[name]) or raw[name] != nested[name]:
            raise ValueError("native relic result lost its outer/inner action state: " + name)
    if type(raw.get("accepted")) is not bool or raw["accepted"] != nested["available"]:
        raise ValueError("native relic action acceptance differs from its original result")
    if nested["status"] not in {"unavailable", "acknowledged_verification_pending", "dispatch_result_unknown",
                                "already_in_requested_state_verification_pending"}:
        raise ValueError("native relic action invented a completed business status")
    if nested["available"] != nested["dispatch_invoked"] and not nested["already_in_requested_state"]:
        raise ValueError("native relic availability lacks an original callback ACK")
    if nested["dispatch_invoked"] and not nested["native_dispatch_attempted"] and not nested["already_in_requested_state"]:
        raise ValueError("native relic invocation lacks a consumed native attempt")
    if (nested["native_dispatch_attempted"] or nested["available"]) and not nested["verification_pending"]:
        raise ValueError("native relic attempted action cannot suppress independent verification")
    if nested["already_in_requested_state"] and (nested["native_dispatch_attempted"] or not nested["selection_postcondition_observed"]):
        raise ValueError("native relic no-op lacks an independently observed requested selection")
    gameplay = operation in {"enshrine_relic", "remove_relic"}
    if nested["gameplay_command_may_have_been_queued"] != (gameplay and nested["native_dispatch_attempted"]):
        raise ValueError("native relic queue uncertainty differs from the actual attempted operation")
    if gameplay:
        if nested["selection_postcondition_observed"] or nested["already_in_requested_state"]:
            raise ValueError("selection readback is not an enshrine/remove business postcondition")
        if nested["native_dispatch_attempted"] and (not nested["frozen_preview_verified"]
                or not nested["actual_button_presentation_observed"] or nested["original_button_enabled"] is not True):
            raise ValueError("relic gameplay callback lacked frozen preview and actual original button admission")
    elif nested["frozen_preview_verified"] or nested["gameplay_command_may_have_been_queued"]:
        raise ValueError("selection-only callback cannot claim a gameplay preview or command")
    if nested["selection_postcondition_observed"]:
        if not prior["available"] or not after["available"] or prior["slot_artifact_ids"] != after["slot_artifact_ids"]:
            raise ValueError("native selection postcondition lacks unchanged actual site inventory rows")
        if operation == "select_relic_artifact":
            valid = after["artifact_id"] == fields["relic_artifact_id"] and prior["slot_index"] == after["slot_index"]
        else:
            valid = after["artifact_id"] == prior["artifact_id"] and (
                (after["slot_index"] == fields["relic_slot_index"]) == fields["relic_desired_selected"])
        if not valid:
            raise ValueError("native relic selection postcondition differs from its finite requested state")
    return raw


def _frame(driver: object, expected_revision: int) -> dict[str, object]:
    if getattr(driver, PERMISSION, False) is not True:
        raise UnsupportedStepError("private holy-site relic actions are disabled")
    if type(expected_revision) is not int or expected_revision <= 0:
        raise ValueError("expected_revision must identify the current public frame")
    snapshot = driver.take_snapshot_without_native_command_history()
    actor, diagnostic = snapshot.get("played_character"), snapshot.get("diagnostics")
    if snapshot.get("revision") != expected_revision:
        raise PreSubmissionRevisionMismatchError("relic action public revision is stale")
    if (snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or not isinstance(actor, Mapping) or actor.get("alive") is not True
            or type(actor.get("character_id")) is not int or not 0 < actor["character_id"] < 0xFFFFFFFF
            or type(snapshot.get("native_revision")) is not int or snapshot["native_revision"] <= 0
            or type(snapshot.get("date_raw")) is not int or not isinstance(diagnostic, Mapping)
            or type(diagnostic.get("connection_generation")) is not int or diagnostic["connection_generation"] <= 0
            or type(diagnostic.get("bridge_pid")) is not int or diagnostic["bridge_pid"] <= 0
            or private_native_build_identity(snapshot) != CK3_12004):
        raise BridgeUnavailableError("relic action requires the actual paused exact4 living player/session")
    _scope(snapshot)
    return snapshot


def _scope(snapshot: Mapping[str, object]) -> dict[str, object]:
    if snapshot.get("managed_campaign_run_binding") is not None:
        binding = managed_campaign_title_map_navigation_v1_binding(dict(snapshot))
        return {"kind": "managed_native_campaign_run", "managed_run_id": binding["managed_run_id"]}
    diagnostic = snapshot.get("diagnostics", {})
    binding = normalize_title_map_navigation_v1_binding({key: snapshot.get(key) for key in (
            "snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id")}
            | {"connection_generation": diagnostic.get("connection_generation")})
    return {"kind": "one_life_episode", "episode_run_id": binding["episode_run_id"]}


def _binding(snapshot: Mapping[str, object]) -> tuple:
    diagnostic = snapshot.get("diagnostics", {})
    return (snapshot.get("native_revision"), snapshot.get("date_raw"), snapshot.get("paused"), snapshot.get("map_ready"),
            snapshot.get("played_character"), diagnostic.get("connection_generation"), diagnostic.get("bridge_pid"),
            _scope(snapshot), snapshot.get("managed_campaign_run_binding"), private_native_build_identity(snapshot))


def _machine_identity(driver: object) -> tuple[str, str, dict[str, object]]:
    source = Path(sys.modules[type(driver).__module__].__file__).resolve()
    candidates = [source.parents[4] / 'tools/ck3_live_run_id.py', Path.cwd() / 'tools/ck3_live_run_id.py']
    path = next((item for item in candidates if item.is_file()
                 and (item.parent.parent / 'docs/storage-retention-policy.json').is_file()), None)
    if path is None:
        raise UnsupportedStepError("relic action receipts require the canonical ck3_live_run_id machine reader")
    spec = importlib.util.spec_from_file_location('_xar_relic_action_live_run_id', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    policy_path = path.parent.parent / 'docs/storage-retention-policy.json'
    policy_raw = policy_path.read_bytes()
    policy = json.loads(policy_raw.decode('utf-8-sig'))
    hours = policy['lifecycle']['protection_max_hours']
    if type(hours) is not int or hours <= 0 or not isinstance(policy.get('policy_version'), str):
        raise UnsupportedStepError('Canonical storage protection policy is malformed')
    return module.current_machine_id(), hashlib.sha256(path.read_bytes()).hexdigest(), {
        'policy_version': policy['policy_version'], 'policy_sha256': hashlib.sha256(policy_raw).hexdigest(),
        'policy_path': str(policy_path), 'protection_max_hours': hours}


def execute_relic_action_private_v1(driver: object, *, expected_revision: int, holy_site_id: int,
                                   operation: str, fields: dict[str, object]) -> dict[str, object]:
    request_fields = validate_relic_action_request_v1(operation, holy_site_id, fields)
    before = _frame(driver, expected_revision)
    folder = driver._native_driver_state_path().parent / 'holy-site-relic-action-intents'
    folder.mkdir(parents=True, exist_ok=True)
    machine, machine_source_sha, storage_policy = _machine_identity(driver)
    identity = {"machine_id": machine, "game_version": CK3_12004.game_version,
                "executable_sha256": CK3_12004.executable_sha256,
                "connection_generation": before["diagnostics"]["connection_generation"],
                "scope": _scope(before), "date_raw": before["date_raw"],
                "played_character_id": before["played_character"]["character_id"], **request_fields}
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
    # Bind the owning generation in the full intent identity, while retaining
    # an additional durable exclusion across reconnect/restart generations.
    replay_identity = {key: value for key, value in identity.items() if key != 'connection_generation'}
    replay_digest = hashlib.sha256(json.dumps(replay_identity, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
    claim = folder / (replay_digest + '.pending.json')
    request_id = _new_request_id()
    now = datetime.now(timezone.utc)
    protection_review = (now + timedelta(hours=storage_policy['protection_max_hours'])).isoformat()
    receipt = {"schema": "holy-site-relic-consumed-intent-v1", "machine_id": machine,
               "observed_at_utc": now.isoformat(), "review_after_utc": protection_review,
               "protected_until_utc": protection_review, "storage_policy": storage_policy,
               "retention_reason": "Unresolved exact action intent; no automatic replay across process restart",
               "machine_reader_sha256": machine_source_sha, "request_id": request_id, "intent": identity,
               "intent_sha256": digest, "cross_generation_replay_guard_sha256": replay_digest,
               "expected_public_revision": expected_revision, "expected_native_revision": before["native_revision"],
               "connection_generation": before["diagnostics"]["connection_generation"],
               "automatic_retry": False, "business_outcome_observed": False}
    try:
        with claim.open('x', encoding='utf-8', newline='') as handle:
            json.dump(receipt, handle, ensure_ascii=False, indent=2)
            handle.write('\n')
    except FileExistsError as error:
        raise BridgeUnavailableError("relic action has a consumed unresolved identical intent; inspect independent state and retained receipt; do not retry: " + str(claim)) from error
    raw = None
    try:
        raw = driver._execute_primitive_step(NAVIGATE_STEP, expected_revision=expected_revision,
            required_capability=NAVIGATE_CAPABILITY, include_native_command_history=False,
            protocol_request_id=request_id, request_fields={**request_fields,
                "expected_date_raw": before["date_raw"],
                "expected_player_character_id": before["played_character"]["character_id"],
                "expected_connection_generation": before["diagnostics"]["connection_generation"]})
        after = driver.take_snapshot_without_native_command_history()
        if _binding(after) != _binding(before):
            raise BridgeUnavailableError("relic action crossed its paused build/player/date/session; result may be unknown, do not retry")
        result = normalize_relic_action_result_v1(raw, before=before, operation=operation, holy_site_id=holy_site_id, fields=fields)
    except (PreSubmissionRevisionMismatchError, UnsupportedStepError) as error:
        # Primitive capability/revision failures occur before endpoint send.
        claim.unlink()
        driver._record_command(NAVIGATE_STEP, ok=False, result={"operation": operation,
            "holy_site_id": holy_site_id, "submitted": False}, error=f'{type(error).__name__}: {error}')
        raise
    except Exception as error:
        # A pre-existing create-only receipt deliberately survives a timeout,
        # malformed packet, foreign frame or lost callback result. No replay.
        driver._record_command(NAVIGATE_STEP, ok=False, result={"operation": operation,
            "holy_site_id": holy_site_id, "pending_intent_receipt": str(claim),
            "native_raw_return_receipt": raw.get("native_ui_raw_return_receipt") if isinstance(raw, dict) else None,
            "automatic_retry": False}, error=f'{type(error).__name__}: {error}')
        raise
    nested = result["holy_site_relic_action"]
    outcome_path = folder / (digest + '.' + request_id + '.result.json')
    with outcome_path.open('x', encoding='utf-8', newline='') as handle:
        json.dump({**receipt, "observed_at_utc": datetime.now(timezone.utc).isoformat(),
                   "native_result": nested, "native_raw_return_receipt": result.get("native_ui_raw_return_receipt")},
                   handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    resolved = (not nested["native_dispatch_attempted"] and not nested["gameplay_command_may_have_been_queued"]
                or nested["selection_postcondition_observed"])
    if resolved:
        claim.unlink()
    driver._record_command(NAVIGATE_STEP, ok=True, result={"operation": operation, "holy_site_id": holy_site_id,
        "holy_site_relic_action": nested, "native_raw_return_receipt": result.get("native_ui_raw_return_receipt"),
        "consumed_intent_receipt": str(outcome_path), "automatic_retry": False})
    return {**result, **private_native_provenance(before), "queried_revision": expected_revision,
            "queried_native_revision": before["native_revision"], "queried_connection_generation": before["diagnostics"]["connection_generation"],
            "automatic_retry": False, "business_outcome_observed": False, "action_ready": False,
            "consumed_intent_receipt": str(outcome_path), "identical_intent_replay_blocked": not resolved}
