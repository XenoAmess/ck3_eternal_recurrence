"""Explicit .3 stock grant window operations; title transfer requires a holder read."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import uuid
from .ingame_decisions_open_contract import opening_binding
from .nonwar_private_build import private_native_build_identity
from .version_identity import require_exact_native_build

SCHEMA = "ck3_12003_grant_title_picker_v1"
PERMISSION = "_grant_title_picker_private_enabled_v1"
OPERATIONS = frozenset({"query", "prepare", "select", "send"})

def full_id(value: object) -> int:
    if type(value) is not int or not 0 <= value < 2**32 - 1:
        raise ValueError("requires an exact full generation-bearing component ID")
    return value

def title_ids(value: object, *, allow_empty: bool = True) -> list[int]:
    if type(value) is not list or not (0 if allow_empty else 1) <= len(value) <= 64:
        raise ValueError("requires an explicit list of at most 64 full Title IDs")
    ids = [full_id(v) for v in value]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate full Title ID")
    return ids

def request_fields(operation: str, recipient_id: object, targets: object,
                   expected_selected: object, title_id: object = None,
                   desired_selected: object = None) -> dict[str, object]:
    if operation not in OPERATIONS:
        raise ValueError("unsupported grant operation")
    recipient = full_id(recipient_id)
    if not recipient:
        raise ValueError("recipient must be a positive full Character ID")
    targets = title_ids(targets)
    selected = title_ids(expected_selected, allow_empty=operation != "send")
    if operation in {"query", "prepare"} and selected:
        raise ValueError("query/prepare does not accept an assumed selection")
    fields: dict[str, object] = {
        "recipient_character_full_id": recipient,
        "requested_title_full_ids": ",".join(map(str, targets)),
        "expected_selected_title_full_ids": ",".join(map(str, selected)),
    }
    if operation == "select":
        fields["title_full_id"] = full_id(title_id)
        if type(desired_selected) is not bool:
            raise ValueError("desired_selected must be an actual boolean")
        fields["desired_selected"] = desired_selected
    elif title_id is not None or desired_selected is not None:
        raise ValueError("only select accepts a Title ID and desired selection")
    if operation == "send" and set(targets) != set(selected):
        raise ValueError("send must read holders for exactly its complete selected Title set")
    return fields

def _boolean(value: object) -> bool:
    if type(value) is not bool:
        raise ValueError("missing actual boolean")
    return value

def _observation(value: object, targets: list[int]) -> dict:
    if type(value) is not dict:
        raise ValueError("missing native grant observation")
    for key in ("available", "window_visible", "window_binding_verified", "rows_complete"):
        _boolean(value.get(key))
    for key in ("native_can_send", "warning_confirmation_required"):
        if value.get(key) is not None:
            _boolean(value[key])
    rows = value.get("rows")
    if type(rows) is not list or len(rows) > 2048:
        raise ValueError("native grant rows incomplete or exceed bound")
    row_ids, selected = [], []
    for row in rows:
        if type(row) is not dict:
            raise ValueError("invalid grant row")
        row_ids.append(full_id(row.get("title_full_id")))
        if row.get("holder_character_full_id") is not None:
            full_id(row["holder_character_full_id"])
        if _boolean(row.get("selected")):
            selected.append(row["title_full_id"])
        _boolean(row.get("selectable"))
    if len(set(row_ids)) != len(row_ids):
        raise ValueError("ambiguous native Title row identity")
    actual_selected = value.get("selected_title_full_ids")
    if type(actual_selected) is not list or actual_selected != selected:
        raise ValueError("selected set does not match the complete native predicate rows")
    if value["rows_complete"] and not (value["available"] and value["window_visible"]
                                      and value["window_binding_verified"]
                                      and type(value["native_can_send"]) is bool
                                      and type(value["warning_confirmation_required"]) is bool):
        raise ValueError("complete native rows lack their actual window binding")
    holders = value.get("requested_title_holders")
    if type(holders) is not list:
        raise ValueError("missing requested native holder rows")
    if value["available"] and [row.get("title_full_id") for row in holders] != targets:
        raise ValueError("native holder rows differ from the requested complete Title set")
    for row in holders:
        if type(row) is not dict:
            raise ValueError("invalid holder row")
        full_id(row.get("title_full_id"))
        _boolean(row.get("available"))
        if row.get("holder_character_full_id") is not None:
            full_id(row["holder_character_full_id"])
    return value

def normalize_result(raw: object, binding: dict, operation: str, recipient_id: int,
                     targets: list[int], expected_selected: list[int],
                     title_id: int | None = None, desired_selected: bool | None = None) -> dict:
    if type(raw) is not dict or raw.get("schema") != SCHEMA or raw.get("operation") != operation:
        raise ValueError("malformed typed native grant result")
    for key in ("owner_thread_verified", "frame_verified", "source_abi_pins_verified",
                "dispatch_invoked", "native_call_completed", "selection_verified", "transfer_verified"):
        _boolean(raw.get(key))
    if raw.get("business_full_credit") is not False:
        raise ValueError("grant leaf cannot grant full business credit")
    if raw.get("recipient_character_full_id") != recipient_id or type(raw.get("recipient_character_full_id")) is not int:
        raise ValueError("native grant recipient changed")
    if raw["frame_verified"]:
        for key in ("native_revision", "connection_generation", "game_pid", "played_character_id", "date_raw"):
            if type(raw.get(key)) is not int or raw[key] != binding[key]:
                raise ValueError("native grant owner/frame changed")
        if not raw["owner_thread_verified"] or not raw["source_abi_pins_verified"]:
            raise ValueError("native grant lacks owner/method qualification")
    before = _observation(raw.get("before"), targets)
    after = _observation(raw.get("after"), targets)
    if operation == "query" and (raw["dispatch_invoked"] or raw["native_call_completed"]
                                 or raw["selection_verified"] or raw["transfer_verified"]):
        raise ValueError("readonly grant query claims an action")
    if raw["transfer_verified"]:
        if (operation != "send" or not expected_selected or not raw["dispatch_invoked"]
                or not raw["native_call_completed"] or not raw["frame_verified"]
                or set(targets) != set(expected_selected) or not before["rows_complete"]
                or not before["window_binding_verified"] or not after["available"]
                or before["native_can_send"] is not True
                or before["warning_confirmation_required"] is not False
                or set(before["selected_title_full_ids"]) != set(expected_selected)
                or any(row["available"] is not True or row["holder_character_full_id"] != binding["played_character_id"]
                       for row in before["requested_title_holders"])
                or any(row["available"] is not True or row["holder_character_full_id"] != recipient_id
                       for row in after["requested_title_holders"])):
            raise ValueError("claimed transfer lacks complete actual native holder readback")
    if raw["selection_verified"]:
        desired = set(expected_selected)
        if desired_selected:
            desired.add(title_id)
        else:
            desired.discard(title_id)
        if (operation != "select" or not raw["frame_verified"] or not before["rows_complete"] or not after["rows_complete"]
                or set(before["selected_title_full_ids"]) != set(expected_selected)
                or set(after["selected_title_full_ids"]) != desired):
            raise ValueError("selection proof differs from actual full Title set")
    if raw.get("status") not in {"unavailable", "observed", "prepared", "selection_observed",
                                 "selection_changed_observed", "holder_transfer_observed", "pending"}:
        raise ValueError("unknown grant status")
    if type(raw.get("unavailable_reason")) is not str:
        raise ValueError("missing native unavailable reason")
    if raw["status"] != "unavailable" and not raw["frame_verified"]:
        raise ValueError("grant completion lacks fresh frame")
    if raw["status"] == "prepared" and (operation != "prepare" or not after["rows_complete"]
                                       or not after["window_visible"] or not after["window_binding_verified"]):
        raise ValueError("prepared grant window is not actually observed")
    if raw["status"] == "selection_observed" and not raw["selection_verified"]:
        raise ValueError("selection status has no actual complete-set proof")
    if (raw["status"] == "holder_transfer_observed") != raw["transfer_verified"]:
        raise ValueError("status is inconsistent with native holder transfer")
    return dict(raw)

def _write_once(path: Path, value: dict) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())

def execute(driver, operation: str, recipient_id: int, *, expected_revision: int,
            requested_title_full_ids: list[int], expected_selected_title_full_ids: list[int],
            title_full_id: int | None = None, desired_selected: bool | None = None) -> dict:
    if getattr(driver, PERMISSION, False) is not True:
        raise ValueError("grant Title picker requires explicit private authorization")
    if type(expected_revision) is not int or not 0 < expected_revision < 2**64:
        raise ValueError("requires the current positive public revision")
    fields = request_fields(operation, recipient_id, requested_title_full_ids,
                            expected_selected_title_full_ids, title_full_id, desired_selected)
    starting = driver.take_snapshot()
    if starting.get("revision") != expected_revision:
        raise ValueError("grant public revision changed before submission")
    binding = opening_binding(starting)
    step = f"{operation}-grant-title-picker-v1"
    capability = "game.command." + step
    if capability not in driver.capabilities().get("bridge_capabilities", []):
        raise ValueError("loaded native DLL lacks the explicit stock grant operation")
    fields.update({"expected_player_character_id": binding["played_character_id"],
                   "expected_game_pid": binding["game_pid"],
                   "expected_connection_generation": binding["connection_generation"]})
    request_id = "grant-" + uuid.uuid4().hex
    claim = None
    if operation != "query":
        directory = driver._native_driver_state_path().parent / "grant-title-picker-actions"
        directory.mkdir(parents=True, exist_ok=True)
        scope = {k: binding[k] for k in ("game_pid", "played_character_id", "episode_run_id")}
        scope.update({"recipient_id": recipient_id, "operation": operation})
        for previous in directory.glob("*.claim.json"):
            value = json.loads(previous.read_text(encoding="utf-8"))
            if value.get("scope") == scope and not previous.with_suffix(".resolved.json").is_file():
                raise ValueError("an original grant action remains pending/unknown; no retry")
        identity = {"scope": scope, "public_revision": expected_revision, "fields": fields}
        key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        claim = directory / (key + ".claim.json")
        _write_once(claim, {"request_id": request_id, "scope": scope, "identity": identity,
                            "status": "claimed_result_unknown_no_retry"})
    raw = driver._execute_primitive_step(step, expected_revision=expected_revision,
        required_capability=capability, request_fields=fields, protocol_request_id=request_id)
    if (type(raw) is not dict or
            require_exact_native_build(raw.get('exact_build'), raw.get('executable_sha256')) !=
            private_native_build_identity(starting)):
        raise ValueError('native grant result differs from its original connected build')
    result = normalize_result(raw, binding, operation, recipient_id, requested_title_full_ids,
                              expected_selected_title_full_ids, title_full_id, desired_selected)
    ending = driver.take_snapshot()
    ending_binding = opening_binding(ending)
    if private_native_build_identity(starting) != private_native_build_identity(ending):
        raise ValueError('grant action crossed its original exact native build')
    for key in ("connection_generation", "game_pid", "played_character_id", "date_raw", "episode_run_id"):
        if ending_binding[key] != binding[key]:
            raise ValueError("grant action crossed its original paused episode")
    if operation != "send" and ending_binding["native_revision"] != binding["native_revision"]:
        raise ValueError("grant query/selection changed the native campaign frame")
    result.update({"queried_revision": expected_revision, "episode_run_id": binding["episode_run_id"],
                   "uses_mouse": False, "uses_keyboard": False, "uses_ocr": False})
    if claim is not None:
        _write_once(claim.with_suffix(".result.json"), {"request_id": request_id, "result": result})
        # A sent-but-pending command remains unresolved. A fresh query can inspect holders;
        # it does not make another Send permissible by inventing a successful outcome.
        terminal = (not result["dispatch_invoked"] or
                    (operation == "send" and result["transfer_verified"]) or
                    (operation != "send" and result["native_call_completed"] and result["frame_verified"]))
        if terminal:
            _write_once(claim.with_suffix(".resolved.json"), {"request_id": request_id,
                "status": "original_result_observed", "transfer_verified": result["transfer_verified"]})
        result["action_claim_path"] = str(claim)
    return result
