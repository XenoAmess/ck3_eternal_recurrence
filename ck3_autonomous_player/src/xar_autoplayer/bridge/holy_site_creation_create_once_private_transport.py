"""One explicit creation callback attempt; all ACKs still require world verification."""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
import hashlib
import json
import re
import uuid

from .driver import BridgeUnavailableError, PreSubmissionRevisionMismatchError, UnsupportedStepError
from .ingame_ui_contract import NAVIGATE_CAPABILITY, NAVIGATE_STEP
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .player_holy_site_creation_context_private_transport import normalize_player_holy_site_creation_context_v1
from .relic_action_private_transport import _binding, _machine_identity, _scope
from .version_identity import CK3_12004, require_exact_native_build

PERMISSION = "allow_private_player_holy_site_creation_create_once"
UI_PERMISSION = "allow_private_player_holy_site_creation_ui"
OPERATION = "create_holy_site_once"
KIND = "holy_site_creation"


def validate_preview_identity(value: object) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError("creation requires the exact observed lowercase preview identity")
    return value


def _bool(value: object, field: str) -> bool:
    if type(value) is not bool:
        raise ValueError("native creation callback boolean is missing: " + field)
    return value


def normalize_creation_create_once_result_v1(raw: object, *, before: Mapping[str, object],
        expected_preview_identity_sha256: str) -> dict[str, object]:
    if not isinstance(raw, dict) or raw.get("schema") != "ck3-ingame-ui-window-v1":
        raise ValueError("creation callback lacks the production UI result")
    expected = {"window_kind": KIND, "window_name": "holy_site_creation_window", "requested_subject_id": 0,
        "native_revision": before["native_revision"], "date_raw": before["date_raw"], "paused": True,
        "played_character_id": before["played_character"]["character_id"], "backend_id": "native-headless",
        "native_backend_id": "ck3-1.20.0.4-native-ingame-ui-v1"}
    for key, value in expected.items():
        if type(raw.get(key)) is not type(value) or raw[key] != value:
            raise ValueError("creation callback crossed its actual frame: " + key)
    if require_exact_native_build(raw.get("game_version"), raw.get("executable_sha256")) != CK3_12004:
        raise ValueError("creation callback requires exact CK3 1.20.0.4")
    ui = raw.get("holy_site_creation_ui")
    keys = {"operation", "type_key", "selected", "requested_object_id", "postcondition_observed",
        "selection_verified", "create_dispatched", "context", "business_outcome_observed",
        "expected_preview_identity_sha256"}
    if not isinstance(ui, dict) or set(ui) != keys:
        raise ValueError("creation callback semantic result shape differs")
    if (ui["operation"] != OPERATION or ui["type_key"] is not None or ui["selected"] is not None
            or type(ui["requested_object_id"]) is not int or ui["requested_object_id"] != 0
            or ui["expected_preview_identity_sha256"] != expected_preview_identity_sha256):
        raise ValueError("creation callback lost its exact operation or expected preview identity")
    if any(ui[name] is not False for name in (
            "postcondition_observed", "selection_verified", "business_outcome_observed")):
        raise ValueError("creation callback ACK cannot claim a selected or world postcondition")
    attempted = _bool(raw.get("native_dispatch_attempted"), "native_dispatch_attempted")
    invoked = _bool(raw.get("dispatch_invoked"), "dispatch_invoked")
    pending = _bool(raw.get("verification_pending"), "verification_pending")
    if ui["create_dispatched"] is not attempted or invoked and not attempted:
        raise ValueError("creation callback attempt/invocation observations disagree")
    if raw.get("available") is not False or raw.get("accepted") is not False:
        raise ValueError("creation callback cannot report a completed available action")
    if raw.get("status") != ("verification_pending" if attempted else "unavailable") or pending is not attempted:
        raise ValueError("creation callback must retain its unresolved native attempt")
    if not isinstance(raw.get("unavailable_reason"), str) or not raw["unavailable_reason"]:
        raise ValueError("creation callback must preserve its actual diagnostic")
    context = ui["context"]
    if attempted:
        if context is not None:
            raise ValueError("creation callback must not confuse pre/reset models with a world postcondition")
        if (any(raw.get(name) is not True for name in (
                "application_owner_thread_verified", "gui_owner_binding_verified"))
                or any(type(raw.get(name)) is not int or raw[name] <= 0 for name in (
                    "thread_id", "pump_epoch", "gui_context_address", "gui_owner_address"))
                or raw.get("rng_owner_is_ui_admission_gate") is not False):
            raise ValueError("creation callback lacks its original native owner admission")
        modal = raw.get("modal_admission")
        if (not isinstance(modal, dict) or any(modal.get(name) is not True for name in (
                "attempted", "header_read", "receivers_verified"))
                or type(modal.get("effective_visible_count")) is not int or modal["effective_visible_count"] != 0
                or modal.get("effective_hidden_mask") != 8
                or modal.get("policy") != "refuse_any_effective_visible_receiver"):
            raise ValueError("creation callback lacks the original modal admission observation")
    elif context is not None:
        observed = normalize_player_holy_site_creation_context_v1(context, snapshot=before)
        if observed["capture_epoch"] != raw.get("pump_epoch"):
            raise ValueError("creation callback rejection context belongs to another owner epoch")
    return raw


def _frame(driver: object, expected_revision: int) -> dict[str, object]:
    if (getattr(driver, UI_PERMISSION, False) is not True
            or getattr(driver, PERMISSION, False) is not True):
        raise UnsupportedStepError("creation callback requires both independent explicit permissions")
    if type(expected_revision) is not int or expected_revision <= 0:
        raise ValueError("creation expected_revision must identify an actual public frame")
    snapshot = driver.take_snapshot_without_native_command_history()
    if snapshot.get("revision") != expected_revision:
        raise PreSubmissionRevisionMismatchError("creation public revision is stale")
    actor, diagnostic = snapshot.get("played_character"), snapshot.get("diagnostics")
    if (snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or not isinstance(actor, Mapping) or actor.get("alive") is not True
            or type(actor.get("character_id")) is not int or not 0 < actor["character_id"] < 2**31
            or type(snapshot.get("native_revision")) is not int or snapshot["native_revision"] <= 0
            or type(snapshot.get("date_raw")) is not int or not isinstance(diagnostic, Mapping)
            or type(diagnostic.get("connection_generation")) is not int or diagnostic["connection_generation"] <= 0
            or type(diagnostic.get("bridge_pid")) is not int or diagnostic["bridge_pid"] <= 0
            or private_native_build_identity(snapshot) != CK3_12004):
        raise BridgeUnavailableError("creation callback requires the actual paused exact4 living player/session")
    _scope(snapshot)
    return snapshot


def create_holy_site_once_private_v1(driver: object, *, expected_preview_identity_sha256: str,
        expected_revision: int) -> dict[str, object]:
    preview = validate_preview_identity(expected_preview_identity_sha256)
    before = _frame(driver, expected_revision)
    folder = driver._native_driver_state_path().parent / "holy-site-creation-create-once-intents"
    folder.mkdir(parents=True, exist_ok=True)
    machine, machine_source_sha, policy = _machine_identity(driver)
    identity = {"machine_id": machine, "game_version": CK3_12004.game_version,
        "executable_sha256": CK3_12004.executable_sha256, "scope": _scope(before),
        "date_raw": before["date_raw"], "played_character_id": before["played_character"]["character_id"],
        "connection_generation": before["diagnostics"]["connection_generation"],
        "operation": OPERATION, "window_kind": KIND, "subject_id": 0,
        "expected_preview_identity_sha256": preview}
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    replay_identity = {key: value for key, value in identity.items() if key != "connection_generation"}
    replay = hashlib.sha256(json.dumps(replay_identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    claim = folder / (replay + ".pending.json")
    request_id = "creation-create-" + uuid.uuid4().hex
    now = datetime.now(timezone.utc)
    review = (now + timedelta(hours=policy["protection_max_hours"])).isoformat()
    receipt = {"schema": "holy-site-creation-consumed-intent-v1", "machine_id": machine,
        "observed_at_utc": now.isoformat(), "review_after_utc": review, "protected_until_utc": review,
        "storage_policy": policy, "machine_reader_sha256": machine_source_sha,
        "retention_reason": "Unresolved creation intent; no automatic replay or claim expiry after callback ACK",
        "request_id": request_id, "intent": identity, "intent_sha256": digest,
        "cross_generation_replay_guard_sha256": replay, "expected_public_revision": expected_revision,
        "expected_native_revision": before["native_revision"], "automatic_retry": False,
        "business_outcome_observed": False, "action_ready": False}
    try:
        with claim.open("x", encoding="utf-8", newline="") as handle:
            json.dump(receipt, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    except FileExistsError as error:
        raise BridgeUnavailableError("creation has an unresolved identical consumed intent; observe world state and retained receipt; do not retry: " + str(claim)) from error
    raw = None
    try:
        raw = driver._execute_primitive_step(NAVIGATE_STEP, expected_revision=expected_revision,
            required_capability=NAVIGATE_CAPABILITY, include_native_command_history=False,
            protocol_request_id=request_id, request_fields={"operation": OPERATION, "window_kind": KIND,
                "subject_id": 0, "expected_preview_identity_sha256": preview,
                "expected_date_raw": before["date_raw"],
                "expected_player_character_id": before["played_character"]["character_id"],
                "expected_connection_generation": before["diagnostics"]["connection_generation"]})
        after = driver.take_snapshot_without_native_command_history()
        if _binding(after) != _binding(before):
            raise BridgeUnavailableError("creation crossed its paused build/player/date/session; result may be unknown, do not retry")
        result = normalize_creation_create_once_result_v1(raw, before=before,
            expected_preview_identity_sha256=preview)
    except (PreSubmissionRevisionMismatchError, UnsupportedStepError) as error:
        claim.unlink()
        driver._record_command(NAVIGATE_STEP, ok=False,
            result={"operation": OPERATION, "submitted": False}, error=f"{type(error).__name__}: {error}")
        raise
    except Exception as error:
        driver._record_command(NAVIGATE_STEP, ok=False, result={"operation": OPERATION,
            "pending_intent_receipt": str(claim), "automatic_retry": False,
            "native_raw_return_receipt": raw.get("native_ui_raw_return_receipt") if isinstance(raw, dict) else None},
            error=f"{type(error).__name__}: {error}")
        raise
    ui = result["holy_site_creation_ui"]
    outcome = folder / (digest + "." + request_id + ".result.json")
    with outcome.open("x", encoding="utf-8", newline="") as handle:
        json.dump({**receipt, "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "native_result": ui, "native_dispatch_attempted": result["native_dispatch_attempted"],
            "native_raw_return_receipt": result.get("native_ui_raw_return_receipt")},
            handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    if not result["native_dispatch_attempted"]:
        claim.unlink()
    driver._record_command(NAVIGATE_STEP, ok=True, result={"operation": OPERATION,
        "holy_site_creation_ui": ui, "native_raw_return_receipt": result.get("native_ui_raw_return_receipt"),
        "consumed_intent_receipt": str(outcome), "automatic_retry": False})
    return {**result, **private_native_provenance(before), "queried_revision": expected_revision,
        "queried_native_revision": before["native_revision"],
        "queried_connection_generation": before["diagnostics"]["connection_generation"],
        "automatic_retry": False, "business_outcome_observed": False, "action_ready": False,
        "consumed_intent_receipt": str(outcome),
        "identical_intent_replay_blocked": result["native_dispatch_attempted"]}
