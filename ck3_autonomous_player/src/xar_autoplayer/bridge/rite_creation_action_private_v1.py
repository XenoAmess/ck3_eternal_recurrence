"""Exact .4 RiteCreationWindow actions; private adapter, never a legality model.

The native owner mints the preview identity. Python neither hashes a guessed draft
nor treats an ACK as a new Faith/Rite. Final confirmation has a durable no-retry
claim before the existing real primitive sends its first request.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import ntpath
import sys
from threading import RLock
from typing import Literal, Protocol, TypedDict
import uuid

from .driver import BridgeUnavailableError, PreSubmissionRevisionMismatchError, UnsupportedStepError
from .ingame_decisions_open_contract import opening_binding
from .version_identity import CK3_12004, require_exact_native_backend, require_exact_native_build


Outcome = Literal["create_faith", "create_rite", "edit_rite"]
NameField = Literal["name", "adjective", "adherent", "adherent_plural", "description"]
NAME_FIELDS: frozenset[str] = frozenset(("name", "adjective", "adherent", "adherent_plural", "description"))
KINDS: frozenset[str] = frozenset(("create_faith", "create_rite", "edit_rite"))
_KEY = re.compile(r"[a-z0-9_]{1,128}\Z")


class RiteNames(TypedDict):
    name: str
    adjective: str
    adherent: str
    adherent_plural: str
    description: str


class CoreTenetSelection(TypedDict):
    slot_index: int
    tenet_key: str


class DoctrineSelection(TypedDict):
    group_key: str
    doctrine_key: str


class SubmittedPayload(TypedDict):
    schema: Literal["xar.ck3-rite-submitted-payload.v1"]
    outcome_kind: Outcome
    source_rite_id: int
    source_faith_id: int
    actor_faith_id: int
    names: RiteNames
    core_tenets: list[CoreTenetSelection]
    doctrines: list[DoctrineSelection]


class CurrentRitePoststate(TypedDict):
    schema: Literal["ck3_12004_rite_creation_poststate_v1"]
    observed: bool
    unavailable_reason: str | None
    source_rite_id_anchor: int
    rite_id: int | None
    faith_id: int | None
    religion_id: int | None
    founder_character_id: int | None
    names: RiteNames | None
    core_tenets: list[CoreTenetSelection] | None
    doctrines: list[DoctrineSelection] | None
    confirmation_modal_open: bool | None
    creation_window_visible: bool | None


class RiteActionState(Protocol):
    def wait_for_command_result(self, request_id: str, timeout_seconds: float) -> object: ...


class RiteActionDriver(Protocol):
    allow_private_player_rite_creation_actions: bool
    _rite_creation_observed_preview_v1: object
    state: RiteActionState

    def capabilities(self) -> Mapping[str, object]: ...
    def take_snapshot_without_native_command_history(self) -> Mapping[str, object]: ...
    def _native_driver_state_path(self) -> Path: ...
    def _execute_primitive_step(self, step: str, *, expected_revision: int,
            required_capability: str, request_fields: dict[str, object],
            include_native_command_history: bool, protocol_request_id: str,
            protocol_result_evidence_path: Path) -> object: ...
    def player_rite_creation_action_private_v1(self, *, operation: str, expected_revision: int,
            expected_source_rite_id: int, **selectors: object) -> dict[str, object]: ...
    def collect_player_rite_creation_action_result_private_v1(self, *, action_request_id: str,
            timeout_seconds: float = 0.0) -> dict[str, object]: ...


def object_map(value: object, label: str) -> dict[str, object]:
    """Copy an untrusted mapping only after validating all keys as strings."""
    if not isinstance(value, Mapping):
        raise ValueError("missing object: " + label)
    result: dict[str, object] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("non-string field: " + label)
        result[key] = item
    return result


def exact_integer(value: object, label: str, low: int = 0, high: int = 0xFFFFFFFE) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError("invalid " + label)
    return value


def outcome(value: object) -> Outcome:
    if value == "create_faith" and type(value) is str:
        return "create_faith"
    if value == "create_rite" and type(value) is str:
        return "create_rite"
    if value == "edit_rite" and type(value) is str:
        return "edit_rite"
    raise ValueError("invalid actual Rite outcome kind")


def _text(value: object, label: str) -> str:
    if type(value) is not str:
        raise ValueError("invalid " + label)
    return value


def _definition(value: object, label: str) -> str:
    result = _text(value, label)
    if not _KEY.fullmatch(result):
        raise ValueError("invalid " + label)
    return result


def parse_names(value: object) -> RiteNames:
    row = object_map(value, "Rite names")
    if set(row) != NAME_FIELDS:
        raise ValueError("Rite names fields differ from the native contract")
    return {"name": _text(row["name"], "name"), "adjective": _text(row["adjective"], "adjective"),
        "adherent": _text(row["adherent"], "adherent"),
        "adherent_plural": _text(row["adherent_plural"], "adherent_plural"),
        "description": _text(row["description"], "description")}


def parse_core_tenets(value: object) -> list[CoreTenetSelection]:
    if not isinstance(value, list) or len(value) > 64:
        raise ValueError("invalid complete Rite core collection")
    result: list[CoreTenetSelection] = []
    keys: set[str] = set()
    for index, item in enumerate(value):
        row = object_map(item, "core selection")
        if set(row) != {"slot_index", "tenet_key"}:
            raise ValueError("core selection fields differ from the native contract")
        slot = exact_integer(row["slot_index"], "core slot", 0, 63)
        key = _definition(row["tenet_key"], "Tenet key")
        if slot != index or key in keys:
            raise ValueError("complete core slots are not ordered and unique")
        keys.add(key)
        result.append({"slot_index": slot, "tenet_key": key})
    return result


def parse_doctrines(value: object) -> list[DoctrineSelection]:
    if not isinstance(value, list) or len(value) > 64:
        raise ValueError("invalid complete Rite doctrine collection")
    result: list[DoctrineSelection] = []
    groups: set[str] = set()
    for item in value:
        row = object_map(item, "doctrine selection")
        if set(row) != {"group_key", "doctrine_key"}:
            raise ValueError("doctrine selection fields differ from the native contract")
        group = _definition(row["group_key"], "Doctrine group")
        if group in groups:
            raise ValueError("complete doctrine groups are not unique")
        groups.add(group)
        result.append({"group_key": group, "doctrine_key": _definition(row["doctrine_key"], "Doctrine key")})
    return sorted(result, key=lambda row: row["group_key"])


def submitted_payload_from_draft(value: object) -> SubmittedPayload:
    draft = object_map(value, "submitted native draft")
    if draft.get("observed") is not True:
        raise ValueError("submitted native draft was not observed")
    return {"schema": "xar.ck3-rite-submitted-payload.v1", "outcome_kind": outcome(draft.get("actual_outcome_kind")),
        "source_rite_id": exact_integer(draft.get("source_rite_id"), "source Rite"),
        "source_faith_id": exact_integer(draft.get("source_faith_id"), "source Faith"),
        "actor_faith_id": exact_integer(draft.get("actor_faith_id"), "actor Faith"),
        "names": parse_names(draft.get("names")),
        "core_tenets": parse_core_tenets(draft.get("selected_core_tenets")),
        "doctrines": parse_doctrines(draft.get("selected_doctrines"))}


def parse_submitted_payload(value: object) -> SubmittedPayload:
    row = object_map(value, "retained submitted payload")
    if set(row) != set(SubmittedPayload.__annotations__) or row.get("schema") != "xar.ck3-rite-submitted-payload.v1":
        raise ValueError("retained submitted payload schema changed")
    return {"schema": "xar.ck3-rite-submitted-payload.v1", "outcome_kind": outcome(row["outcome_kind"]),
        "source_rite_id": exact_integer(row["source_rite_id"], "source Rite"),
        "source_faith_id": exact_integer(row["source_faith_id"], "source Faith"),
        "actor_faith_id": exact_integer(row["actor_faith_id"], "actor Faith"),
        "names": parse_names(row["names"]), "core_tenets": parse_core_tenets(row["core_tenets"]),
        "doctrines": parse_doctrines(row["doctrines"])}


def parse_current_rite_poststate(value: object) -> CurrentRitePoststate:
    row = object_map(value, "independent current Rite")
    if set(row) != set(CurrentRitePoststate.__annotations__) or row.get("schema") != "ck3_12004_rite_creation_poststate_v1":
        raise ValueError("independent current Rite schema changed")
    observed = row["observed"]
    if type(observed) is not bool:
        raise ValueError("independent current Rite availability is malformed")
    reason = row["unavailable_reason"]
    if (observed and reason is not None) or (not observed and (type(reason) is not str or not reason)):
        raise ValueError("independent current Rite lost its availability reason")
    refs: dict[str, int | None] = {}
    for key in ("rite_id", "faith_id", "religion_id", "founder_character_id"):
        refs[key] = None if row[key] is None else exact_integer(row[key], key)
    flags: dict[str, bool | None] = {}
    for key in ("confirmation_modal_open", "creation_window_visible"):
        flag = row[key]
        if flag is not None and type(flag) is not bool:
            raise ValueError("independent current Rite modal flag is malformed")
        flags[key] = flag
    result: CurrentRitePoststate = {"schema": "ck3_12004_rite_creation_poststate_v1", "observed": observed,
        "unavailable_reason": None if reason is None else _text(reason, "poststate reason"),
        "source_rite_id_anchor": exact_integer(row["source_rite_id_anchor"], "source Rite anchor"),
        "rite_id": refs["rite_id"], "faith_id": refs["faith_id"], "religion_id": refs["religion_id"],
        "founder_character_id": refs["founder_character_id"],
        "names": None if row["names"] is None else parse_names(row["names"]),
        "core_tenets": None if row["core_tenets"] is None else parse_core_tenets(row["core_tenets"]),
        "doctrines": None if row["doctrines"] is None else parse_doctrines(row["doctrines"]),
        "confirmation_modal_open": flags["confirmation_modal_open"],
        "creation_window_visible": flags["creation_window_visible"]}
    if observed and any(value is None for value in (result["rite_id"], result["faith_id"],
            result["religion_id"], result["names"], result["core_tenets"], result["doctrines"],
            result["confirmation_modal_open"], result["creation_window_visible"])):
        raise ValueError("observed independent current Rite is incomplete")
    return result


def poststate_matches_payload(payload: SubmittedPayload, current: CurrentRitePoststate, actor_id: int) -> bool:
    if (not current["observed"] or current["source_rite_id_anchor"] != payload["source_rite_id"]
            or current["confirmation_modal_open"] is not False
            or current["creation_window_visible"] is not False or current["names"] != payload["names"]
            or current["core_tenets"] != payload["core_tenets"] or current["doctrines"] != payload["doctrines"]):
        return False
    if payload["outcome_kind"] == "edit_rite":
        return current["rite_id"] == payload["source_rite_id"] and current["faith_id"] == payload["source_faith_id"]
    if current["rite_id"] == payload["source_rite_id"] or current["founder_character_id"] != actor_id:
        return False
    if payload["outcome_kind"] == "create_faith":
        return current["faith_id"] != payload["source_faith_id"]
    return current["faith_id"] == payload["source_faith_id"]


def different_business_intent(first: SubmittedPayload, second: SubmittedPayload) -> bool:
    return (first["outcome_kind"] != second["outcome_kind"] or first["names"] != second["names"]
            or first["core_tenets"] != second["core_tenets"] or first["doctrines"] != second["doctrines"])



STEP = "player-rite-creation-action-v1"
CAPABILITY = "player_rite_creation_action_v1"
DOMAIN_KEY = CAPABILITY
BODY_KEY = "rite_creation_action"
SCHEMA = "ck3_12004_rite_creation_action_v1"
OPERATIONS = frozenset(("open_create_draft", "open_edit_current_rite_draft", "select_core_tenet",
    "select_doctrine", "set_name_field", "preview", "prepare_confirmation", "confirm_once",
    "observe_current_rite", "cancel_draft"))
READ_OPERATIONS = frozenset(("preview", "observe_current_rite"))
_IDENTITY = re.compile(r"[0-9a-f]{64}\Z")
_CLAIM_LOCK = RLock()
_MAX_SAFE_JSON_INTEGER = (1 << 53) - 1


class ConfirmClaim(TypedDict):
    schema: Literal["xar.ck3-rite-confirm-once.v2"]
    machine_id: str
    observed_at_utc: str
    request_id: str
    identity: dict[str, object]
    binding: dict[str, object]
    fields: dict[str, object]
    status: Literal["claimed_result_unknown_no_retry"]
    native_result_file: str
    submitted_payload: SubmittedPayload
    predecessor_request_id: str | None


class CompletionReceipt(TypedDict):
    schema: Literal["xar.ck3-rite-confirm-completed.v1"]
    machine_id: str
    observed_at_utc: str
    action_request_id: str
    claim_sha256: str
    original_native_result_sha256: str
    poststate_native_result_file: str
    poststate_native_result_sha256: str
    poststate_binding: dict[str, object]
    current_rite_poststate: CurrentRitePoststate
    business_outcome_verified: Literal[True]
    automatic_retry: Literal[False]


def _request_id(value: object) -> str:
    if type(value) is not str or not re.fullmatch(r"rite-action-[0-9a-f]{32}", value):
        raise ValueError("invalid original Rite action request ID")
    return value


def _local_filename(value: object) -> str:
    if (type(value) is not str or not value or Path(value).name != value
            or ntpath.basename(value) != value or value in (".", "..")):
        raise ValueError("retained Rite evidence filename is malformed")
    return value


def _read_object(path: Path) -> dict[str, object]:
    value: object = json.loads(path.read_text(encoding="utf-8"))
    return object_map(value, "retained " + path.name)


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_claim(value: object) -> ConfirmClaim:
    row = object_map(value, "retained confirmation claim")
    if set(row) != set(ConfirmClaim.__annotations__) or row.get("schema") != "xar.ck3-rite-confirm-once.v2":
        raise BridgeUnavailableError("legacy or malformed Rite claim has no verified submitted payload; no successor")
    request_id = _request_id(row["request_id"])
    machine = row["machine_id"]
    timestamp = row["observed_at_utc"]
    if type(machine) is not str or not machine or type(timestamp) is not str or not timestamp:
        raise ValueError("retained Rite claim provenance is malformed")
    if row["status"] != "claimed_result_unknown_no_retry":
        raise ValueError("retained Rite claim status changed")
    predecessor = row["predecessor_request_id"]
    if predecessor is not None:
        predecessor = _request_id(predecessor)
        if predecessor == request_id:
            raise ValueError("Rite claim is its own predecessor")
    fields = object_map(row["fields"], "retained original fields")
    source_id = exact_integer(fields.get("expected_source_rite_id"), "retained source Rite")
    expected_fields = request_fields("confirm_once", source_id,
        expected_preview_identity=fields.get("expected_preview_identity"),
        expected_outcome_kind=fields.get("expected_outcome_kind"))
    expected_fields["action_id"] = request_id
    if fields != expected_fields:
        raise ValueError("retained original confirmation fields changed")
    binding = object_map(row["binding"], "retained original binding")
    payload = parse_submitted_payload(row["submitted_payload"])
    identity = object_map(row["identity"], "retained original identity")
    if (identity != _intent_identity_v1(binding, source_id) or payload["source_rite_id"] != source_id
            or payload["outcome_kind"] != fields["expected_outcome_kind"]):
        raise ValueError("retained submitted payload differs from its original intent")
    exact_integer(binding.get("played_character_id"), "retained played character")
    return {"schema": "xar.ck3-rite-confirm-once.v2", "machine_id": machine,
        "observed_at_utc": timestamp, "request_id": request_id, "identity": identity,
        "binding": binding, "fields": fields, "status": "claimed_result_unknown_no_retry",
        "native_result_file": _local_filename(row["native_result_file"]),
        "submitted_payload": payload, "predecessor_request_id": predecessor}


def _same_actor_scope(first: Mapping[str, object], second: Mapping[str, object]) -> bool:
    return ({key: value for key, value in first.items() if key != "source_rite_id"}
        == {key: value for key, value in second.items() if key != "source_rite_id"})


def _matching_packet(path: Path, claim: ConfirmClaim) -> dict[str, object]:
    packet = _read_object(path)
    if (packet.get("type") != "command_result" or type(packet.get("protocol_version")) is not int
            or packet["protocol_version"] != 1 or packet.get("request_id") != claim["request_id"]
            or packet.get("ok") is not True):
        raise BridgeUnavailableError("original Rite result is not a matching completed native dispatch")
    result = normalize_result(packet.get("result"), binding=claim["binding"], fields=claim["fields"])
    leaf = object_map(result[BODY_KEY], "original submitted result")
    if leaf["native_dispatch_attempted"] is not True or leaf["dispatch_invoked"] is not True:
        raise BridgeUnavailableError("original native dispatch result is unknown or not invoked; no successor")
    return packet


def _poststate_follows_original(original: Mapping[str, object], poststate: Mapping[str, object],
        original_binding: Mapping[str, object], poststate_binding: Mapping[str, object]) -> None:
    for key in ("game_pid", "connection_generation"):
        if (type(original_binding.get(key)) is not int or type(poststate_binding.get(key)) is not int
                or original_binding[key] != poststate_binding[key]):
            raise BridgeUnavailableError("Rite completion crossed the original native process/connection")
    first = object_map(object_map(object_map(original.get("result"), "original result")[BODY_KEY],
        "original leaf")["frame"], "original frame")
    last = object_map(object_map(object_map(poststate.get("result"), "poststate result")[BODY_KEY],
        "poststate leaf")["frame"], "poststate frame")
    if (exact_integer(last.get("capture_epoch"), "poststate epoch", 1, (1 << 64) - 1)
            <= exact_integer(first.get("capture_epoch"), "original epoch", 1, (1 << 64) - 1)):
        raise BridgeUnavailableError("independent Rite poststate did not follow the original native dispatch")


def _read_completed(root: Path, claim_path: Path, claim: ConfirmClaim) -> CompletionReceipt:
    path = root / (claim["request_id"] + ".completed.json")
    if not path.is_file():
        raise BridgeUnavailableError("Rite confirmation still has an unknown result; no successor")
    row = _read_object(path)
    if (set(row) != set(CompletionReceipt.__annotations__)
            or row.get("schema") != "xar.ck3-rite-confirm-completed.v1"
            or row.get("machine_id") != _machine_id() or row.get("action_request_id") != claim["request_id"]
            or row.get("claim_sha256") != _file_sha256(claim_path)
            or row.get("business_outcome_verified") is not True or row.get("automatic_retry") is not False):
        raise BridgeUnavailableError("Rite completion receipt differs from its immutable claim")
    original_path = root / claim["native_result_file"]
    original_packet = _matching_packet(original_path, claim)
    if row["original_native_result_sha256"] != _file_sha256(original_path):
        raise BridgeUnavailableError("original Rite dispatch evidence changed")
    post_path = root / _local_filename(row["poststate_native_result_file"])
    if row["poststate_native_result_sha256"] != _file_sha256(post_path):
        raise BridgeUnavailableError("independent Rite poststate evidence changed")
    post_binding = object_map(row["poststate_binding"], "retained poststate binding")
    packet = _read_object(post_path)
    if (packet.get("type") != "command_result" or packet.get("ok") is not True
            or type(packet.get("protocol_version")) is not int or packet["protocol_version"] != 1):
        raise BridgeUnavailableError("independent Rite poststate packet is malformed")
    post_request = _request_id(packet.get("request_id"))
    if post_path.name != post_request + ".native-result.json":
        raise BridgeUnavailableError("independent Rite evidence filename differs from the original native request")
    _poststate_follows_original(original_packet, packet, claim["binding"], post_binding)
    post_result = normalize_result(packet.get("result"), binding=post_binding,
        fields={"operation": "observe_current_rite", "expected_source_rite_id": claim["submitted_payload"]["source_rite_id"]})
    current = parse_current_rite_poststate(object_map(post_result[BODY_KEY], "poststate leaf")["current_rite_poststate"])
    if (current != parse_current_rite_poststate(row["current_rite_poststate"])
            or not _same_actor_scope(claim["identity"], _intent_identity_v1(post_binding, claim["submitted_payload"]["source_rite_id"]))
            or not poststate_matches_payload(claim["submitted_payload"], current,
                exact_integer(claim["binding"].get("played_character_id"), "played character"))):
        raise BridgeUnavailableError("independent Rite poststate no longer proves the submitted payload")
    observed = row["observed_at_utc"]
    if type(observed) is not str or not observed:
        raise ValueError("completion observation time is missing")
    return {"schema": "xar.ck3-rite-confirm-completed.v1", "machine_id": _machine_id(),
        "observed_at_utc": observed, "action_request_id": claim["request_id"],
        "claim_sha256": _file_sha256(claim_path), "original_native_result_sha256": _file_sha256(original_path),
        "poststate_native_result_file": post_path.name, "poststate_native_result_sha256": _file_sha256(post_path),
        "poststate_binding": post_binding, "current_rite_poststate": current,
        "business_outcome_verified": True, "automatic_retry": False}


def _successor_claim_path(root: Path, key: str, identity: Mapping[str, object],
        payload: SubmittedPayload) -> tuple[Path, str | None]:
    """Append to one actor/scope chain; an unknown claim blocks even a new source."""
    claims: dict[str, tuple[Path, ConfirmClaim]] = {}
    for index, path in enumerate(root.glob("*.claim.json")):
        if index >= 128:
            raise BridgeUnavailableError("bounded Rite claim chain lookup exceeded")
        row = _read_object(path)
        if not _same_actor_scope(object_map(row.get("identity"), "claim identity"), identity):
            continue
        claim = _parse_claim(row)
        if claim["machine_id"] != _machine_id() or claim["request_id"] in claims:
            raise BridgeUnavailableError("Rite claim owner or chain is ambiguous")
        claims[claim["request_id"]] = (path, claim)
    if not claims:
        return root / (key + ".claim.json"), None
    predecessors = {claim["predecessor_request_id"] for _, claim in claims.values()
        if claim["predecessor_request_id"] is not None}
    if any(request_id not in claims for request_id in predecessors):
        raise BridgeUnavailableError("Rite successor chain lost an original predecessor")
    heads = set(claims) - predecessors
    if len(heads) != 1:
        raise BridgeUnavailableError("Rite successor chain is ambiguous")
    for path, claim in claims.values():
        _read_completed(root, path, claim)
    previous_id = next(iter(heads))
    previous = claims[previous_id][1]
    if not different_business_intent(previous["submitted_payload"], payload):
        raise BridgeUnavailableError("new Rite draft repeats the already completed business intent")
    return root / (key + "." + previous_id + ".successor.claim.json"), previous_id


def _require_no_pending_confirmation(root: Path, identity: Mapping[str, object]) -> None:
    """Closing a draft cannot withdraw an already queued or unknown command."""
    for index, path in enumerate(root.glob("*.claim.json")):
        if index >= 128:
            raise BridgeUnavailableError("bounded Rite cancellation claim lookup exceeded")
        row = _read_object(path)
        if not _same_actor_scope(object_map(row.get("identity"), "claim identity"), identity):
            continue
        claim = _parse_claim(row)
        if claim["machine_id"] != _machine_id():
            raise BridgeUnavailableError("Rite cancellation claim belongs to another machine")
        _read_completed(root, path, claim)


def _integer(value: object, label: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError("invalid " + label)
    return value


def request_fields(operation: str, expected_source_rite_id: int, **selectors: object) -> dict[str, object]:
    """Definition keys are selectors; actor/Faith/pointers/paths never enter JSON."""
    if operation not in OPERATIONS:
        raise ValueError("unknown Rite creation operation")
    _integer(expected_source_rite_id, "expected_source_rite_id", 0, 0xFFFFFFFE)
    expected = {
        "select_core_tenet": {"core_slot_index", "tenet_key"},
        "select_doctrine": {"group_key", "doctrine_key"},
        "set_name_field": {"name_field", "text"},
        "prepare_confirmation": {"expected_preview_identity", "expected_outcome_kind"},
        "confirm_once": {"expected_preview_identity", "expected_outcome_kind"},
    }.get(operation, set())
    if set(selectors) != expected:
        raise ValueError("unexpected or missing Rite creation selector")
    for key in ("tenet_key", "group_key", "doctrine_key"):
        value = selectors.get(key)
        if key in selectors and (type(value) is not str or not _KEY.fullmatch(value)):
            raise ValueError("invalid definition key: " + key)
    if operation == "select_core_tenet":
        _integer(selectors["core_slot_index"], "core_slot_index", 0, 63)
    if operation == "set_name_field":
        name, text = selectors["name_field"], selectors["text"]
        if type(name) is not str or name not in NAME_FIELDS or type(text) is not str:
            raise ValueError("invalid actual name field")
        maximum = 4096 if name == "description" else 256
        if len(text.encode("utf-8")) > maximum or any(ord(c) < 32 and not (name == "description" and c in "\n\t") for c in text):
            raise ValueError("name text exceeds bounded UTF-8 input or contains control bytes")
    if operation in ("prepare_confirmation", "confirm_once"):
        token, kind = selectors["expected_preview_identity"], selectors["expected_outcome_kind"]
        if type(token) is not str or not _IDENTITY.fullmatch(token) or kind not in KINDS:
            raise ValueError("invalid original preview identity/outcome assertion")
    return {"operation": operation, "expected_source_rite_id": expected_source_rite_id, **selectors}


def _binding(snapshot: Mapping[str, object], expected_revision: int) -> dict[str, object]:
    _integer(expected_revision, "expected_revision", 1, _MAX_SAFE_JSON_INTEGER)
    if type(snapshot.get("revision")) is not int or snapshot.get("revision") != expected_revision:
        raise PreSubmissionRevisionMismatchError("Rite creation public revision changed")
    try:
        bound = object_map(opening_binding(snapshot), "opening binding")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    for key in ("native_revision", "connection_generation"):
        _integer(bound.get(key), key, 1, _MAX_SAFE_JSON_INTEGER)
    hello = object_map(object_map(snapshot["diagnostics"], "diagnostics")["hello"], "hello")
    if require_exact_native_build(hello["expected_ck3_version"], hello["expected_ck3_sha256"]) != CK3_12004:
        raise BridgeUnavailableError("Rite creation actions require exact .4")
    if snapshot.get("episode_projection") == "native_campaign":
        from .title_map_navigation_contract import managed_campaign_title_map_navigation_v1_binding
        try:
            managed_campaign_title_map_navigation_v1_binding(snapshot)
        except ValueError as error:
            raise BridgeUnavailableError(str(error)) from error
        managed = object_map(deepcopy(snapshot["managed_campaign_run_binding"]), "managed campaign binding")
        # Use the allocator's real persistent state directory. Run ID, frozen
        # argv, connection, date and preview changes cannot create a fresh
        # confirmation scope after an unknown result. This is not a one-life
        # episode and the snapshot/episode_run_id are never rewritten.
        bound["managed_campaign_run_binding"] = managed
        state_dir = managed["state_dir"]
        if type(state_dir) is not str:
            raise BridgeUnavailableError("managed campaign state directory is malformed")
        bound["intent_scope"] = {"kind": "managed_campaign_state_v1",
            "state_dir": ntpath.normcase(ntpath.normpath(state_dir))}
    elif type(bound["episode_run_id"]) is not str or not bound["episode_run_id"]:
        raise BridgeUnavailableError("Rite creation requires a durable actual episode or verified managed campaign")
    return bound


def _intent_identity_v1(binding: Mapping[str, object], source_rite_id: int) -> dict[str, object]:
    identity = {"played_character_id": binding["played_character_id"], "source_rite_id": source_rite_id}
    if "intent_scope" in binding:
        identity["managed_campaign_intent_scope"] = deepcopy(binding["intent_scope"])
    else:
        identity["episode_run_id"] = binding["episode_run_id"]
    return identity


def normalize_result(raw: object, *, binding: Mapping[str, object], fields: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(raw, dict):
        raise ValueError("missing original Rite action result")
    if require_exact_native_backend(raw.get("game_version"), raw.get("executable_sha256"),
            raw.get("backend_id"), suffix="rite-creation-action-v1") != CK3_12004:
        raise ValueError("foreign Rite action build")
    if (raw.get("step") != STEP or raw.get("domain_key") != DOMAIN_KEY
            or raw.get("accepted") is not True or raw.get("private_build") is not True
            or raw.get("advertised") is not False
            or raw.get("snapshot_revision") != binding["native_revision"]
            or raw.get("date_raw") != binding["date_raw"]
            or raw.get("read_only") is not (fields["operation"] in READ_OPERATIONS)):
        raise ValueError("Rite action envelope frame/operation changed")
    leaf = raw.get(BODY_KEY)
    if not isinstance(leaf, dict) or leaf.get("schema") != SCHEMA or leaf.get("operation") != fields["operation"]:
        raise ValueError("malformed original Rite action leaf")
    for key in ("available", "native_dispatch_attempted", "dispatch_invoked", "verification_pending",
            "original_writer_may_have_been_queued", "business_outcome_observed", "preview_identity_available",
            "complete_command_payload_observed", "original_writer_inputs_observed"):
        if type(leaf.get(key)) is not bool:
            raise ValueError("missing actual Rite action flag: " + key)
    if leaf["business_outcome_observed"] is not False:
        raise ValueError("writer return cannot prove a new Faith/Rite")
    if not leaf["available"] and (type(leaf.get("unavailable_reason")) is not str or not leaf["unavailable_reason"]):
        raise ValueError("unavailable native action lost its diagnostic")
    if leaf["available"] and leaf.get("unavailable_reason") is not None:
        raise ValueError("available native action retains failure")
    if leaf["dispatch_invoked"] and not leaf["native_dispatch_attempted"]:
        raise ValueError("native dispatch flags disagree")
    if fields["operation"] != "confirm_once" and leaf["original_writer_may_have_been_queued"]:
        raise ValueError("preparing the modal is not final submission")
    if fields["operation"] in READ_OPERATIONS and (leaf["native_dispatch_attempted"] or leaf["dispatch_invoked"]):
        raise ValueError("read-only Rite observation invoked a native writer")
    frame = leaf.get("frame")
    if not isinstance(frame, dict):
        raise ValueError("missing native Rite action frame")
    for key in ("connection_generation", "native_revision", "date_raw", "played_character_id"):
        if type(frame.get(key)) is not int or frame[key] != binding[key]:
            raise ValueError("original Rite action frame changed: " + key)
    _integer(frame.get("capture_epoch"), "capture_epoch", 1, _MAX_SAFE_JSON_INTEGER)
    for key in ("draft", "modal", "full_can", "quote"):
        if not isinstance(leaf.get(key), dict) or type(leaf[key].get("observed")) is not bool:
            raise ValueError("missing actual Rite action component: " + key)
    draft, modal, can, quote = (leaf[key] for key in ("draft", "modal", "full_can", "quote"))
    if draft["observed"] and draft.get("source_rite_id") != fields["expected_source_rite_id"]:
        raise ValueError("actual source Rite differs from assertion")
    for key in ("can_create", "can_edit"):
        if can.get(key) is not None and type(can[key]) is not bool:
            raise ValueError("malformed full native Can")
        if not can["observed"] and can.get(key) is not None:
            raise ValueError("unobserved native Can was filled")
    if quote.get("raw_scale") != 100000:
        raise ValueError("Rite quote raw scale changed")
    for key in ("piety_cost_raw", "piety_missing_signed_raw"):
        if quote.get(key) is not None:
            _integer(quote[key], key, -(1 << 63), (1 << 63) - 1)
    if quote.get("has_enough_piety") is not None and type(quote["has_enough_piety"]) is not bool:
        raise ValueError("malformed original piety admission")
    token = leaf.get("preview_identity")
    if leaf["preview_identity_available"]:
        if (type(token) is not str or not _IDENTITY.fullmatch(token)
                or not all(leaf[key]["observed"] for key in ("draft", "modal", "full_can", "quote"))
                or draft.get("actual_outcome_kind") not in KINDS
                or leaf.get("complete_command_payload_observed") is not True
                or leaf.get("original_writer_inputs_observed") is not True
                or type(leaf.get("native_command_text_bytes")) is not int or leaf["native_command_text_bytes"] <= 0
                or type(leaf.get("native_command_text_sha256")) is not str
                or not _IDENTITY.fullmatch(leaf["native_command_text_sha256"])):
            raise ValueError("preview identity lacks actual native components")
        if (any(type(can.get(key)) is not bool for key in ("can_create", "can_edit"))
                or any(type(quote.get(key)) is not int for key in ("piety_cost_raw", "piety_missing_signed_raw"))
                or type(quote.get("has_enough_piety")) is not bool
                or modal.get("stage") not in ("none", "confirmation")
                or not isinstance(draft.get("names"), dict) or set(draft["names"]) != NAME_FIELDS
                or any(type(value) is not str for value in draft["names"].values())
                or not isinstance(draft.get("selected_core_tenets"), list)
                or not isinstance(draft.get("selected_doctrines"), list)):
            raise ValueError("preview identity filled incomplete original draft/Can/quote inputs")
        for key in ("source_rite_id", "source_faith_id", "actor_faith_id"):
            _integer(draft.get(key), key, 0, 0xFFFFFFFE)
    elif token is not None:
        raise ValueError("unavailable preview identity was invented")
    if fields["operation"] == "confirm_once" and leaf.get("action_id") != fields.get("action_id"):
        raise ValueError("native confirmation action identity changed")
    if fields["operation"] == "observe_current_rite":
        current = parse_current_rite_poststate(leaf.get("current_rite_poststate"))
        if current["source_rite_id_anchor"] != fields["expected_source_rite_id"]:
            raise ValueError("independent current Rite observation lost its original source anchor")
    return {**deepcopy(raw), "business_outcome_verified": False, "action_ready": False,
        "automatic_retry": False, "source_and_runtime_qualification_distinct": True}


def _machine_id() -> str:
    """Reuse the canonical allocator; no copied machine-ID algorithm."""
    path = Path(__file__).resolve().parents[4] / "tools/ck3_live_run_id.py"
    if not path.is_file():
        raise BridgeUnavailableError("canonical machine ID helper is unavailable")
    name = "_xar_rite_creation_live_run_id"
    module = sys.modules.get(name)
    if module is None:
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise BridgeUnavailableError("canonical machine ID helper cannot be imported")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    result: object = module.current_machine_id()
    if type(result) is not str or not result:
        raise BridgeUnavailableError("canonical machine ID helper returned an invalid ID")
    return result


def _save_exclusive(path: Path, record: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(record, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def _release_known_unsubmitted(claim: Path, request_id: str, reason: str) -> None:
    """Retain the complete intent before releasing an authoritatively unsent one."""
    with _CLAIM_LOCK:
        original = _read_object(claim)
        if original.get("request_id") != request_id:
            raise BridgeUnavailableError("Rite claim changed during known-no-dispatch resolution")
        _save_exclusive(claim.parent / (request_id + ".safe-no-dispatch.json"), {
            "schema": "xar.ck3-rite-confirm-known-no-dispatch.v1", "machine_id": original["machine_id"],
            "observed_at_utc": datetime.now(timezone.utc).isoformat(), "reason": reason, "original_claim": original,
            "automatic_retry": False})
        claim.unlink()


def execute_private_v1(driver: RiteActionDriver, *, operation: str, expected_revision: int,
        expected_source_rite_id: int, observed_preview: Mapping[str, object] | None = None,
        **selectors: object) -> dict[str, object]:
    if operation == "cancel_draft":
        # Keep the pending-claim admission and native close inside the same
        # process lock used by final confirmation claim creation.
        with _CLAIM_LOCK:
            return _execute_private_locked_v1(driver, operation=operation, expected_revision=expected_revision,
                expected_source_rite_id=expected_source_rite_id, observed_preview=observed_preview, **selectors)
    return _execute_private_locked_v1(driver, operation=operation, expected_revision=expected_revision,
        expected_source_rite_id=expected_source_rite_id, observed_preview=observed_preview, **selectors)


def _execute_private_locked_v1(driver: RiteActionDriver, *, operation: str, expected_revision: int,
        expected_source_rite_id: int, observed_preview: Mapping[str, object] | None = None,
        **selectors: object) -> dict[str, object]:
    fields = request_fields(operation, expected_source_rite_id, **selectors)
    if getattr(driver, "allow_private_player_rite_creation_actions", False) is not True:
        raise BridgeUnavailableError("private Rite creation actions are disabled")
    capabilities = driver.capabilities().get("bridge_capabilities")
    if not isinstance(capabilities, list) or CAPABILITY not in capabilities:
        raise UnsupportedStepError("this DLL does not implement the exact .4 Rite action candidate")
    before = driver.take_snapshot_without_native_command_history()
    bound = _binding(before, expected_revision)
    root = driver._native_driver_state_path().parent / "rite-creation-actions"
    root.mkdir(parents=True, exist_ok=True)
    if operation == "cancel_draft":
        with _CLAIM_LOCK:
            _require_no_pending_confirmation(root, _intent_identity_v1(bound, expected_source_rite_id))
    request_id = "rite-action-" + uuid.uuid4().hex
    claim = None
    if operation == "confirm_once":
        if observed_preview is None:
            observed_preview = getattr(driver, "_rite_creation_observed_preview_v1", None)
        if not isinstance(observed_preview, Mapping):
            raise BridgeUnavailableError("final confirmation requires an actual post-modal preview")
        preview = object_map(normalize_result(dict(observed_preview), binding=bound,
            fields={"operation": "preview", "expected_source_rite_id": expected_source_rite_id})[BODY_KEY], "preview")
        draft, modal, can = (object_map(preview[key], key) for key in ("draft", "modal", "full_can"))
        kind = fields["expected_outcome_kind"]
        if (preview["preview_identity_available"] is not True
                or preview["preview_identity"] != fields["expected_preview_identity"]
                or draft.get("actual_outcome_kind") != kind
                or modal.get("stage") != "confirmation" or modal.get("active") is not True
                or modal.get("same_draft_window_bound") is not True or modal.get("native_can_accept") is not True
                or can.get("can_edit" if kind == "edit_rite" else "can_create") is not True):
            raise BridgeUnavailableError("actual original confirmation/modal/full Can proof is unavailable")
        # Native revision, connection, quote, preview token and requested outcome
        # deliberately do not create a fresh retry scope after an unknown result.
        identity = _intent_identity_v1(bound, expected_source_rite_id)
        key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        evidence = root / (key + "." + request_id + ".native-result.json")
        submitted_payload = submitted_payload_from_draft(draft)
        fields["action_id"] = request_id
        try:
            with _CLAIM_LOCK:
                claim, predecessor = _successor_claim_path(root, key, identity, submitted_payload)
                record: ConfirmClaim = {"schema": "xar.ck3-rite-confirm-once.v2", "machine_id": _machine_id(),
                    "observed_at_utc": datetime.now(timezone.utc).isoformat(), "request_id": request_id,
                    "identity": identity, "binding": bound, "fields": fields,
                    "status": "claimed_result_unknown_no_retry", "native_result_file": evidence.name,
                    "submitted_payload": submitted_payload, "predecessor_request_id": predecessor}
                _save_exclusive(claim, record)
        except FileExistsError as error:
            raise BridgeUnavailableError("Rite confirmation already claimed for this actual source/episode; no retry") from error
    else:
        evidence = root / (request_id + ".native-result.json")
    if operation not in READ_OPERATIONS:
        driver._rite_creation_observed_preview_v1 = None
    # The existing primitive maps public expected_revision to the real native
    # revision. Its preserved raw command_result retains the native backend_id;
    # its normal return projects that field to native-headless, so is not proof.
    try:
        driver._execute_primitive_step(STEP, expected_revision=expected_revision, required_capability=CAPABILITY,
            request_fields={**fields, "expected_connection_generation": bound["connection_generation"],
                "expected_date_raw": bound["date_raw"], "expected_player_character_id": bound["played_character_id"]},
            include_native_command_history=False, protocol_request_id=request_id,
            protocol_result_evidence_path=evidence)
    except (UnsupportedStepError, PreSubmissionRevisionMismatchError):
        # These exact primitive errors precede endpoint.send. Generic errors,
        # rejection exceptions and timeouts remain unknown and retain the claim.
        if claim is not None:
            _release_known_unsubmitted(claim, request_id, "existing_primitive_rejected_before_endpoint_send")
        raise
    packet = _read_object(evidence)
    if (packet.get("type") != "command_result" or type(packet.get("protocol_version")) is not int or packet.get("protocol_version") != 1
            or packet.get("request_id") != request_id or packet.get("ok") is not True):
        raise BridgeUnavailableError("Rite action retained result mismatch; no retry")
    try:
        result = normalize_result(packet.get("result"), binding=bound, fields=fields)
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    result_leaf = object_map(result[BODY_KEY], "normalized action leaf")
    if operation == "preview" and result_leaf["preview_identity_available"]:
        driver._rite_creation_observed_preview_v1 = deepcopy(packet["result"])
    known_no_dispatch = (claim is not None and not result_leaf["native_dispatch_attempted"]
        and not result_leaf["original_writer_may_have_been_queued"])
    if known_no_dispatch and claim is not None:
        _release_known_unsubmitted(claim, request_id, "matching_original_native_result_proves_no_dispatch_and_no_possible_queue")
    managed_provenance = ({"managed_campaign_run_binding": deepcopy(bound["managed_campaign_run_binding"]),
        "intent_scope": deepcopy(bound["intent_scope"])} if "intent_scope" in bound else {})
    return {**result, **managed_provenance, "episode_run_id": bound["episode_run_id"], "queried_revision": expected_revision,
        "known_no_dispatch_intent_released": known_no_dispatch,
        "native_result_receipt": str(evidence), "action_request_id": request_id,
        "uses_mouse": False, "uses_keyboard": False, "uses_ocr": False}


def collect_private_result_v1(driver: RiteActionDriver, *, action_request_id: str,
        timeout_seconds: float = 0.0) -> dict[str, object]:
    """Collect only the retained original result; never dispatch or clear a claim."""
    if type(action_request_id) is not str or not re.fullmatch(r"rite-action-[0-9a-f]{32}", action_request_id):
        raise ValueError("invalid original Rite action request ID")
    if type(timeout_seconds) not in (int, float) or not 0 <= timeout_seconds <= 30:
        raise ValueError("invalid bounded result collection timeout")
    root = driver._native_driver_state_path().parent / "rite-creation-actions"
    matches: list[tuple[Path | None, dict[str, object]]] = []
    for index, path in enumerate(root.glob("*.claim.json")):
        if index >= 128:
            raise BridgeUnavailableError("bounded Rite claim lookup exceeded; retain original request, do not resend")
        claim = _read_object(path)
        if claim.get("request_id") == action_request_id:
            matches.append((path, claim))
    if not matches:
        resolved = root / (action_request_id + ".safe-no-dispatch.json")
        if resolved.is_file():
            matches.append((None, object_map(_read_object(resolved)["original_claim"], "resolved original claim")))
    if len(matches) != 1 or matches[0][1].get("machine_id") != _machine_id():
        raise BridgeUnavailableError("original local Rite claim is missing or ambiguous")
    claim_path, claim = matches[0]
    filename = claim.get("native_result_file")
    if type(filename) is not str or Path(filename).name != filename:
        raise BridgeUnavailableError("retained Rite claim path is malformed")
    evidence = root / filename
    if evidence.is_file():
        packet = json.loads(evidence.read_text(encoding="utf-8"))
    else:
        if claim_path is None:
            return {"status": "known_no_dispatch", "action_request_id": action_request_id,
                "known_no_dispatch_intent_released": True, "automatic_retry": False,
                "business_outcome_verified": False, "action_ready": False}
        received = driver.state.wait_for_command_result(action_request_id, float(timeout_seconds))
        if received is None:
            return {"status": "pending_unknown", "action_request_id": action_request_id,
                "automatic_retry": False, "business_outcome_verified": False, "action_ready": False}
        packet = object_map(received, "retained native packet")
        _save_exclusive(evidence, packet)
    if (packet.get("type") != "command_result" or packet.get("protocol_version") != 1
            or packet.get("request_id") != action_request_id or packet.get("ok") is not True):
        raise BridgeUnavailableError("original Rite result rejected or malformed; claim retained, no resend")
    try:
        result = normalize_result(packet.get("result"), binding=object_map(claim["binding"], "original binding"),
            fields=object_map(claim["fields"], "original fields"))
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    result_leaf = object_map(result[BODY_KEY], "normalized collected leaf")
    known_no_dispatch = (not result_leaf["native_dispatch_attempted"]
        and not result_leaf["original_writer_may_have_been_queued"])
    if claim_path is not None and known_no_dispatch:
        _release_known_unsubmitted(claim_path, action_request_id, "matching_late_native_result_proves_no_dispatch_and_no_possible_queue")
    return {**result, "status_scope": "original_request_result_only_not_current_legality",
        "known_no_dispatch_intent_released": known_no_dispatch,
        "action_request_id": action_request_id, "native_result_receipt": str(evidence)}


def verify_completed_private_v1(driver: RiteActionDriver, *, action_request_id: str,
        expected_revision: int) -> dict[str, object]:
    """Read persisted current Rite through the existing native owner, never reopen a draft.

    The original claim and result remain immutable. A completed receipt permits
    one explicitly different successor; it never resubmits the original action.
    """
    _request_id(action_request_id)
    if getattr(driver, "allow_private_player_rite_creation_actions", False) is not True:
        raise BridgeUnavailableError("private Rite creation actions are disabled")
    before = driver.take_snapshot_without_native_command_history()
    bound = _binding(before, expected_revision)
    root = driver._native_driver_state_path().parent / "rite-creation-actions"
    matches: list[tuple[Path, ConfirmClaim]] = []
    for index, path in enumerate(root.glob("*.claim.json")):
        if index >= 128:
            raise BridgeUnavailableError("bounded original Rite claim lookup exceeded")
        row = _read_object(path)
        if row.get("request_id") == action_request_id:
            matches.append((path, _parse_claim(row)))
    if len(matches) != 1:
        raise BridgeUnavailableError("original local Rite claim is missing or ambiguous")
    claim_path, claim = matches[0]
    payload = claim["submitted_payload"]
    if (claim["machine_id"] != _machine_id()
            or not _same_actor_scope(claim["identity"], _intent_identity_v1(bound, payload["source_rite_id"]))):
        raise BridgeUnavailableError("current Rite owner, machine or actor differs from the original intent")
    completed_path = root / (action_request_id + ".completed.json")
    if completed_path.is_file():
        receipt = _read_completed(root, claim_path, claim)
        return {**receipt, "status": "completed", "status_scope": "retained_verified_completion",
            "completion_receipt": str(completed_path), "action_ready": False}
    original_path = root / claim["native_result_file"]
    if not original_path.is_file():
        collected = collect_private_result_v1(driver, action_request_id=action_request_id)
        if not original_path.is_file():
            return {"status": "pending_unknown", "action_request_id": action_request_id,
                "automatic_retry": False, "business_outcome_verified": False,
                "action_ready": False, "original_result": collected}
    original_packet = _matching_packet(original_path, claim)
    observation = execute_private_v1(driver, operation="observe_current_rite",
        expected_revision=expected_revision, expected_source_rite_id=payload["source_rite_id"])
    leaf = object_map(observation[BODY_KEY], "current Rite observation")
    current = parse_current_rite_poststate(leaf.get("current_rite_poststate"))
    actor = exact_integer(bound.get("played_character_id"), "current played character")
    if not poststate_matches_payload(payload, current, actor):
        return {"status": "poststate_mismatch", "action_request_id": action_request_id,
            "automatic_retry": False, "business_outcome_verified": False, "action_ready": False,
            "current_rite_poststate": current, "poststate_observation": observation}
    evidence_value = observation["native_result_receipt"]
    if type(evidence_value) is not str:
        raise BridgeUnavailableError("independent Rite observation lost its actual evidence path")
    evidence = Path(evidence_value)
    if evidence.parent.resolve() != root.resolve():
        raise BridgeUnavailableError("independent Rite observation evidence escaped the local owner")
    _poststate_follows_original(original_packet, _read_object(evidence), claim["binding"], bound)
    receipt = {"schema": "xar.ck3-rite-confirm-completed.v1", "machine_id": _machine_id(),
        "observed_at_utc": datetime.now(timezone.utc).isoformat(), "action_request_id": action_request_id,
        "claim_sha256": _file_sha256(claim_path), "original_native_result_sha256": _file_sha256(original_path),
        "poststate_native_result_file": evidence.name, "poststate_native_result_sha256": _file_sha256(evidence),
        "poststate_binding": bound, "current_rite_poststate": current,
        "business_outcome_verified": True, "automatic_retry": False}
    with _CLAIM_LOCK:
        if not completed_path.exists():
            _save_exclusive(completed_path, receipt)
        verified = _read_completed(root, claim_path, claim)
    return {**verified, "status": "completed", "status_scope": "independent_current_rite_matches_submitted_payload",
        "completion_receipt": str(completed_path), "action_ready": False}


def evaluate_independent_poststate_v1(*, before_snapshot: Mapping[str, object],
        after_snapshot: Mapping[str, object], before_context: Mapping[str, object],
        after_context: Mapping[str, object], expected_outcome_kind: str,
        quoted_piety_cost_raw: int | None) -> dict[str, object]:
    """Use existing actual context/snapshot readers; this function sends nothing.

An identity pattern and a wallet/quote comparison are separate observations.
They do not prove selected doctrine parameters, or that adoption is now legal.
"""
    from .player_religion_context_private_transport import _CONTEXT_KEYS, normalize_player_religion_context_v1
    if expected_outcome_kind not in KINDS:
        raise ValueError("unknown expected native outcome")
    bound = [_binding(snapshot, _integer(snapshot.get("revision"), "revision", 1, (1 << 64) - 1))
        for snapshot in (before_snapshot, after_snapshot)]
    for key in ("connection_generation", "game_pid", "played_character_id", "date_raw", "episode_run_id",
            "intent_scope", "managed_campaign_run_binding"):
        if bound[0].get(key) != bound[1].get(key):
            raise ValueError("poststate crossed owner, actor, episode or paused date")
    contexts = []
    for value, snapshot in ((before_context, before_snapshot), (after_context, after_snapshot)):
        if (value.get("read_only") is not True or value.get("domain_key") != "player_religion_context_v1"
                or value.get("queried_revision") != snapshot.get("revision")
                or value.get("snapshot_revision") != snapshot.get("native_revision")):
            raise ValueError("independent religion query provenance/frame is missing")
        if require_exact_native_backend(value.get("game_version"), value.get("executable_sha256"),
                value.get("backend_id"), suffix="player-religion-context-v1") != CK3_12004:
            raise ValueError("poststate religion query belongs to another build")
        contexts.append(normalize_player_religion_context_v1({key: value[key] for key in _CONTEXT_KEYS}, snapshot=snapshot))
    first, last = contexts
    ids = ("rite_id", "faith_id", "religion_id", "faith_main_rite_id")
    complete = all(value["available"] and all(type(value[key]) is int and value[key] != 0xFFFFFFFF for key in ids) for value in contexts)
    matches = None
    if complete:
        same_religion = first["religion_id"] == last["religion_id"]
        if expected_outcome_kind == "create_faith":
            matches = same_religion and last["faith_id"] != first["faith_id"] and last["rite_id"] != first["rite_id"]
        elif expected_outcome_kind == "create_rite":
            matches = same_religion and last["faith_id"] == first["faith_id"] and last["rite_id"] != first["rite_id"]
        else:
            matches = all(first[key] == last[key] for key in ids)
    wallets: list[int | None] = []
    for snapshot in (before_snapshot, after_snapshot):
        wallet = snapshot.get("played_character_piety")
        if wallet is None:
            wallets.append(None)
        elif not isinstance(wallet, dict) or set(wallet) != {"raw", "scale"} or wallet["scale"] != 100000:
            raise ValueError("actual piety wallet is malformed")
        else:
            wallets.append(_integer(wallet["raw"], "piety wallet", -(1 << 63), (1 << 63) - 1))
    if quoted_piety_cost_raw is not None:
        _integer(quoted_piety_cost_raw, "quoted piety cost", -(1 << 63), (1 << 63) - 1)
    first_wallet, last_wallet = wallets
    delta = last_wallet - first_wallet if first_wallet is not None and last_wallet is not None else None
    comparison = "unknown" if delta is None or quoted_piety_cost_raw is None else (
        "equal" if delta == -quoted_piety_cost_raw else "different")
    return {"scope": "independent religion identity and actual piety wallet comparison",
        "expected_outcome_kind": expected_outcome_kind, "identity_pattern_matches": matches,
        "before_ids": {key: first[key] for key in ids}, "after_ids": {key: last[key] for key in ids},
        "after_current_rite_is_main": (last["rite_id"] == last["faith_main_rite_id"]) if complete else None,
        "piety_before_raw": wallets[0], "piety_after_raw": wallets[1], "piety_delta_raw": delta,
        "quoted_piety_cost_raw": quoted_piety_cost_raw, "piety_quote_comparison": comparison,
        "edit_payload_changed_observed": False, "other_resource_effects_verified": False,
        "doctrine_parameters_verified": False, "adoption_native_permission_verified": False,
        "business_outcome_verified": False, "action_ready": False,
        "follow_up": "Read actual current/main Rite core and parameter bags, directional hostility and normal adoption Can; edit also requires actual changed payload readback."}
