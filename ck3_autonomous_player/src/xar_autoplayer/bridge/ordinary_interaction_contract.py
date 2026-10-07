"""Fresh ordinary interaction terms and a single pending command receipt.

Public revisions never stand in for native revisions or business outcomes.
Character IDs retain all 32 bits, including their generation. No caller supplies
an actor, a process, an event expectation, an option vector, or a native address.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import re

from .current_actor_stress_adjustment_contract import stress_query_binding, same_stress_query_frame
from .version_identity import CK3_12003, CK3_12004, require_exact_native_build
from .ingame_decisions_open_contract import EXE_SHA256
from .nonwar_private_build import private_native_build_identity

QUERY_STEP = "query-character-interaction-ordinary-v1"
QUERY_CAPABILITY = "game.query.character-interaction-ordinary.v1"
INITIATE_STEP = "initiate-character-interaction-ordinary-v1"
INITIATE_CAPABILITY = "game.command.initiate-character-interaction-ordinary-v1"
QUERY_SCHEMA = "ck3-character-interaction-ordinary-context-v1"
INITIATE_SCHEMA = "ck3-character-interaction-ordinary-initiation-v1"
QUERY_PAYLOAD = "character_interaction_ordinary_context"
INITIATE_PAYLOAD = "character_interaction_ordinary_initiation"
PROOFS = ("source_code_pins_verified", "actor_binding_verified", "recipient_binding_verified",
          "owner_thread_verified", "tls_verified", "frame_verified")
ROLES = ("actor_id", "recipient_id", "secondary_actor_id", "secondary_recipient_id", "intermediary_id", "sixth_role_id")
COST_ORDER = ["gold", "prestige", "piety", "renown", "influence", "herd", "treasury", "treasury_or_gold", "merit", "barter_goods"]
FRAME_KEYS = {"snapshot_revision", "date_raw", "game_pid", "connection_generation"}
COMMON_KEYS = {"schema", "status", "source", "read_only", "exact_build", "executable_sha256",
               *FRAME_KEYS, "player_character_id", "recipient_id", "interaction_key", *PROOFS,
               "owner_thread_id", "owner_pump_epoch", "business_postcondition_verified"}
TERM_KEYS = {"actor_alive", "recipient_alive", "definition_stable_hash", "declared_option_count",
             "selected_option_count", "special_payload_present", "shown", "can_send", "costs_raw",
             "auto_accept", "recipient_score_raw", "intermediary_score_raw", "outer_answer_status"}
QUERY_KEYS = COMMON_KEYS | TERM_KEYS | {"effective_roles", "cost_scale", "cost_order",
             "native_context_available", "ordinary_context_supported", "active_event_present",
             "incoming_interaction_present", "ready_to_initiate", "unavailable_reason", "unsupported_reason"}
INITIATE_KEYS = COMMON_KEYS | {"native_call_completed", "dispatch_invoked", "native_queue_result",
                "queue_submitted", "verification_pending", "postcondition_verified", "reason", "preflight_context"}
ENVELOPE_COMMON = {"step", "accepted", "status", "read_only", "query_sequence", *FRAME_KEYS, "backend_id"}
QUERY_ENVELOPE_KEYS = ENVELOPE_COMMON | {QUERY_PAYLOAD}
INITIATE_ENVELOPE_KEYS = ENVELOPE_COMMON | {INITIATE_PAYLOAD}
PUBLIC_BINDING_KEYS = {"queried_snapshot_id", "queried_revision", "queried_native_revision"}
QUERY_PUBLIC_KEYS = QUERY_ENVELOPE_KEYS | PUBLIC_BINDING_KEYS | {"ordinary_interaction_context_ready"}
INITIATE_PUBLIC_KEYS = INITIATE_ENVELOPE_KEYS | PUBLIC_BINDING_KEYS | {
    "after_snapshot_id", "after_revision", "after_native_revision", "after_control_frame_verified",
    "action_request_id", "action_claim_path", "business_effects_verified", "full_product_acceptance_credit"}


def _integer(value: object, minimum: int, maximum: int, name: str) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer in {minimum}..{maximum}")
    return value


def validate_interaction_key(value: object) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[A-Za-z0-9_]{1,128}", value, flags=re.ASCII) is None:
        raise ValueError("interaction_key must be exact ASCII [A-Za-z0-9_]{1,128}")
    return value


def validate_recipient_id(value: object) -> int:
    return _integer(value, 1, 2**32 - 2, "recipient_id")


def interaction_binding(snapshot: object, expected_revision: object, *, initiating: bool = False) -> dict[str, object]:
    binding = stress_query_binding(snapshot, expected_revision)
    if initiating and (snapshot.get("active_event") is not None or snapshot.get("pending_character_interaction") is not None):
        raise ValueError("ordinary initiation requires no active event or incoming interaction")
    return {**binding, "active_event_present": snapshot.get("active_event") is not None,
            "incoming_interaction_present": snapshot.get("pending_character_interaction") is not None}


def same_query_frame(before: dict, after: object, binding: dict) -> bool:
    original = {key: val for key, val in binding.items() if key not in {"active_event_present", "incoming_interaction_present"}}
    return (same_stress_query_frame(before, after, original)
            and private_native_build_identity(before)==private_native_build_identity(after))


def after_control_binding(before: dict, after: object, binding: dict) -> dict:
    """Accept legal business changes, while pinning the actual control frame."""
    if not isinstance(after, dict):
        raise ValueError("ordinary initiation lacks an actual after snapshot")
    later = interaction_binding(after, after.get("revision"))
    if private_native_build_identity(before)!=private_native_build_identity(after):
        raise ValueError("ordinary initiation changed its exact native build")
    for key in ("game_pid", "connection_generation", "played_character_id", "date_raw", "episode_run_id"):
        if later[key] != binding[key]:
            raise ValueError(f"ordinary initiation changed control identity {key}")
    for key in ("speed", "paused", "map_ready", "local_player_id", "episode_character_id"):
        if type(after.get(key)) is not type(before.get(key)) or after.get(key) != before.get(key):
            raise ValueError(f"ordinary initiation changed control frame {key}")
    if later["revision"] < binding["revision"] or later["native_revision"] < binding["native_revision"]:
        raise ValueError("ordinary initiation after revision moved backwards")
    return later


def _exact(value: dict, key: str, expected: object) -> None:
    if type(value.get(key)) is not type(expected) or value[key] != expected:
        raise ValueError(f"ordinary interaction {key} is mismatched")


def _reason(value: object, name: str) -> None:
    if not isinstance(value, str) or not 1 <= len(value) <= 512:
        raise ValueError(f"{name} requires a bounded nonempty reason")


def _common(value: object, keys: set, binding: dict, interaction_key: str, recipient_id: int,
            schema: str, source: str, read_only: bool, status: str) -> dict:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError("ordinary interaction payload is not closed")
    build = require_exact_native_build(value.get("exact_build"), value.get("executable_sha256"))
    if build not in (CK3_12003, CK3_12004):
        raise ValueError("ordinary interaction requires an exact .3/.4 native build")
    source = source.replace('1.20.0.3', build.game_version)
    for key, expected in {"schema": schema, "status": status, "source": source, "read_only": read_only,
            "exact_build": build.game_version, "snapshot_revision": binding["native_revision"],
            "date_raw": binding["date_raw"], "game_pid": binding["game_pid"],
            "connection_generation": binding["connection_generation"],
            "player_character_id": binding["played_character_id"], "recipient_id": recipient_id,
            "interaction_key": interaction_key, "business_postcondition_verified": False}.items():
        _exact(value, key, expected)
    for key in PROOFS:
        if type(value[key]) is not bool:
            raise ValueError(f"ordinary interaction proof {key} is malformed")
    _integer(value["owner_thread_id"], 0, 2**32 - 1, "owner_thread_id")
    _integer(value["owner_pump_epoch"], 0, 2**64 - 1, "owner_pump_epoch")
    return value


def require_result_build(raw, snapshot, payload_key):
    value = raw.get(payload_key) if isinstance(raw, dict) else None
    if not isinstance(value, dict) or require_exact_native_build(
            value.get('exact_build'), value.get('executable_sha256')) != private_native_build_identity(snapshot):
        raise ValueError('ordinary interaction result differs from its connected native build')


def normalize_context_payload(raw: object, binding: dict, interaction_key: str, recipient_id: int) -> dict:
    validate_interaction_key(interaction_key)
    validate_recipient_id(recipient_id)
    status = raw.get("status") if isinstance(raw, dict) else None
    if status not in {"available", "unavailable"}:
        raise ValueError("ordinary context status is malformed")
    value = _common(raw, QUERY_KEYS, binding, interaction_key, recipient_id, QUERY_SCHEMA,
                    "native_current_ordinary_interaction_context_1.20.0.3", True, status)
    for key in ("native_context_available", "ordinary_context_supported", "active_event_present",
                "incoming_interaction_present", "ready_to_initiate"):
        if type(value[key]) is not bool:
            raise ValueError(f"ordinary context {key} is malformed")
    for key in ("active_event_present", "incoming_interaction_present"):
        _exact(value, key, binding[key])
    _exact(value, "cost_scale", 100000)
    _exact(value, "cost_order", COST_ORDER)
    roles = value["effective_roles"]
    if not isinstance(roles, dict) or set(roles) != set(ROLES):
        raise ValueError("ordinary context role inventory is malformed")
    if status == "unavailable":
        if any(value[key] is not None for key in TERM_KEYS) or any(roles[key] is not None for key in ROLES):
            raise ValueError("unavailable ordinary terms must be an all-null group")
        for key in ("native_context_available", "ordinary_context_supported", "ready_to_initiate"):
            _exact(value, key, False)
        _reason(value["unavailable_reason"], "unavailable_reason")
        _reason(value["unsupported_reason"], "unsupported_reason")
        return deepcopy(value)
    if any(value[key] is not True for key in PROOFS) or value["unavailable_reason"] is not None:
        raise ValueError("available ordinary context lacks actual proofs")
    _integer(value["owner_thread_id"], 1, 2**32 - 1, "owner_thread_id")
    _integer(value["owner_pump_epoch"], 1, 2**64 - 1, "owner_pump_epoch")
    _exact(value, "native_context_available", True)
    for key in ("actor_alive", "recipient_alive", "special_payload_present", "shown", "can_send", "auto_accept"):
        if type(value[key]) is not bool:
            raise ValueError(f"ordinary context term {key} is malformed")
    for key in ("definition_stable_hash", "declared_option_count", "selected_option_count"):
        _integer(value[key], 0, 2**32 - 1, key)
    if value["selected_option_count"] > value["declared_option_count"]:
        raise ValueError("ordinary selected option count exceeds declared count")
    for key in ROLES:
        if roles[key] is not None:
            _integer(roles[key], 0, 2**32 - 2, key)
    if roles["actor_id"] is None or roles["recipient_id"] is None:
        raise ValueError("available ordinary context lacks final actor and recipient roles")
    if not isinstance(value["costs_raw"], list) or len(value["costs_raw"]) != 10:
        raise ValueError("ordinary context costs require exactly ten raw amounts")
    for cost in value["costs_raw"]:
        _integer(cost, -(2**63), 2**63 - 1, "costs_raw")
    for key in ("recipient_score_raw", "intermediary_score_raw"):
        _integer(value[key], -(2**63), 2**63 - 1, key)
    _integer(value["outer_answer_status"], 0, 2, "outer_answer_status")
    ordinary = (value["declared_option_count"] == 0 and value["selected_option_count"] == 0
                and value["special_payload_present"] is False)
    _exact(value, "ordinary_context_supported", ordinary)
    if ordinary:
        if value["unsupported_reason"] is not None:
            raise ValueError("supported ordinary context carries an unsupported reason")
    else:
        _reason(value["unsupported_reason"], "unsupported_reason")
    ready = (ordinary and value["actor_alive"] and value["recipient_alive"] and value["shown"]
             and value["can_send"] and not value["active_event_present"] and not value["incoming_interaction_present"])
    _exact(value, "ready_to_initiate", ready)
    return deepcopy(value)


def _envelope(raw: object, keys: set, binding: dict, step: str, read_only: bool, statuses: set) -> dict:
    if not isinstance(raw, dict) or set(raw) != keys or raw.get("status") not in statuses:
        raise ValueError("ordinary interaction envelope is not closed")
    for key, expected in {"step": step, "accepted": True, "read_only": read_only, "backend_id": "native-headless",
            "snapshot_revision": binding["native_revision"], "date_raw": binding["date_raw"],
            "game_pid": binding["game_pid"], "connection_generation": binding["connection_generation"]}.items():
        _exact(raw, key, expected)
    _integer(raw["query_sequence"], 1, 2**64 - 1, "query_sequence")
    return raw


def normalize_native_query(raw: object, binding: dict, interaction_key: str, recipient_id: int) -> dict:
    value = _envelope(raw, QUERY_ENVELOPE_KEYS, binding, QUERY_STEP, True, {"available", "unavailable"})
    context = normalize_context_payload(value[QUERY_PAYLOAD], binding, interaction_key, recipient_id)
    _exact(context, "status", value["status"])
    return deepcopy(value)


def project_query(raw: object, binding: dict, interaction_key: str, recipient_id: int) -> dict:
    result = normalize_native_query(raw, binding, interaction_key, recipient_id)
    return {**result, "queried_snapshot_id": binding["snapshot_id"], "queried_revision": binding["revision"],
            "queried_native_revision": binding["native_revision"],
            "ordinary_interaction_context_ready": result["status"] == "available"}


def normalize_public_query(raw: object, binding: dict, interaction_key: str, recipient_id: int) -> dict:
    if not isinstance(raw, dict) or set(raw) != QUERY_PUBLIC_KEYS:
        raise ValueError("public ordinary query is not closed")
    expected = project_query({key: raw[key] for key in QUERY_ENVELOPE_KEYS}, binding, interaction_key, recipient_id)
    for key in QUERY_PUBLIC_KEYS - QUERY_ENVELOPE_KEYS:
        _exact(raw, key, expected[key])
    return deepcopy(raw)


def normalize_native_initiation(raw: object, binding: dict, interaction_key: str, recipient_id: int) -> dict:
    value = _envelope(raw, INITIATE_ENVELOPE_KEYS, binding, INITIATE_STEP, False, {"pending", "not_dispatched"})
    ack = _common(value[INITIATE_PAYLOAD], INITIATE_KEYS, binding, interaction_key, recipient_id,
                  INITIATE_SCHEMA, "native_current_ordinary_interaction_command_1.20.0.3", False, value["status"])
    preflight = normalize_context_payload(ack["preflight_context"], binding, interaction_key, recipient_id)
    if (preflight['exact_build'] != ack['exact_build'] or
            preflight['executable_sha256'].upper() != ack['executable_sha256'].upper()):
        raise ValueError('ordinary initiation and preflight native builds differ')
    for key in ("native_call_completed", "dispatch_invoked", "queue_submitted", "verification_pending", "postcondition_verified"):
        if type(ack[key]) is not bool:
            raise ValueError(f"ordinary initiation {key} is malformed")
    queue = ack["native_queue_result"]
    if queue not in {"not_attempted", "unavailable", "rejected", "submitted"}:
        raise ValueError("ordinary initiation queue classification is malformed")
    _exact(ack, "queue_submitted", queue == "submitted")
    _exact(ack, "verification_pending", ack["dispatch_invoked"])
    _exact(ack, "postcondition_verified", False)
    _exact(ack, "status", "pending" if ack["dispatch_invoked"] else "not_dispatched")
    if ack["dispatch_invoked"]:
        if queue == "not_attempted" or any(ack[key] is not True for key in PROOFS) or preflight["ready_to_initiate"] is not True:
            raise ValueError("ordinary dispatch lacks actual ready preflight and proofs")
        _integer(ack["owner_thread_id"], 1, 2**32 - 1, "owner_thread_id")
        _integer(ack["owner_pump_epoch"], 1, 2**64 - 1, "owner_pump_epoch")
    elif queue != "not_attempted" or ack["queue_submitted"]:
        raise ValueError("ordinary non-dispatch must retain not_attempted")
    if queue == "submitted":
        if ack["native_call_completed"] is not True or ack["reason"] is not None:
            raise ValueError("submitted ordinary queue receipt is inconsistent")
    else:
        _reason(ack["reason"], "reason")
    return deepcopy(value)


def project_initiation(raw: object, binding: dict, interaction_key: str, recipient_id: int,
                       after: dict, request_id: str, claim: Path) -> dict:
    result = normalize_native_initiation(raw, binding, interaction_key, recipient_id)
    return {**result, "queried_snapshot_id": binding["snapshot_id"], "queried_revision": binding["revision"],
            "queried_native_revision": binding["native_revision"], "after_snapshot_id": after["snapshot_id"],
            "after_revision": after["revision"], "after_native_revision": after["native_revision"],
            "after_control_frame_verified": True, "action_request_id": request_id, "action_claim_path": str(claim),
            "business_effects_verified": False, "full_product_acceptance_credit": False}


def normalize_public_initiation(raw: object, binding: dict, interaction_key: str, recipient_id: int, after: dict) -> dict:
    if not isinstance(raw, dict) or set(raw) != INITIATE_PUBLIC_KEYS:
        raise ValueError("public ordinary initiation is not closed")
    for key in ("action_request_id", "action_claim_path"):
        if not isinstance(raw[key], str) or not raw[key]:
            raise ValueError(f"public ordinary initiation lacks {key}")
    # The driver preserves its first after read. A wrapper may observe a later
    # published state while the same paused command is still only pending.
    # Validate that earlier observation without relabeling it as the latest one.
    observed_revision = _integer(after["revision"], binding["revision"], 2**64 - 1, "observed after_revision")
    observed_native = _integer(after["native_revision"], binding["native_revision"], 2**64 - 1, "observed after_native_revision")
    recorded = {**after,
        "revision": _integer(raw["after_revision"], binding["revision"], observed_revision, "after_revision"),
        "native_revision": _integer(raw["after_native_revision"], binding["native_revision"], observed_native, "after_native_revision"),
        "snapshot_id": raw["after_snapshot_id"]}
    for endpoint in (binding, after):
        if recorded["revision"] == endpoint["revision"]:
            _exact(recorded, "native_revision", endpoint["native_revision"])
        if recorded["native_revision"] == endpoint["native_revision"]:
            _exact(recorded, "snapshot_id", endpoint["snapshot_id"])
    if binding["native_revision"] < recorded["native_revision"] < observed_native:
        # StateSnapshotFrame uses this native revision identity (bridge.cpp).
        _exact(recorded, "snapshot_id", f"native:{recorded['native_revision']}")
    expected = project_initiation({key: raw[key] for key in INITIATE_ENVELOPE_KEYS}, binding, interaction_key,
                                  recipient_id, recorded, raw["action_request_id"], Path(raw["action_claim_path"]))
    for key in INITIATE_PUBLIC_KEYS - INITIATE_ENVELOPE_KEYS:
        _exact(raw, key, expected[key])
    return deepcopy(raw)


def claim_identity(binding: dict, interaction_key: str, recipient_id: int, host_provenance=None) -> dict:
    created = None
    if host_provenance is not None:
        if not isinstance(host_provenance, dict) or set(host_provenance) != {
                "process_create_time", "profile_sha256", "session_id", "pipe_name", "guard_profile_sha256"}:
            raise ValueError("ordinary host provenance must be a closed internal profile binding")
        created = host_provenance["process_create_time"]
        if type(created) not in (int, float) or not math.isfinite(created) or created <= 0:
            raise ValueError("ordinary host provenance lacks actual process creation time")
        for key in ("profile_sha256", "guard_profile_sha256"):
            if not isinstance(host_provenance[key], str) or re.fullmatch(r"[0-9a-f]{64}", host_provenance[key]) is None:
                raise ValueError("ordinary host provenance lacks a frozen profile hash")
        if (not isinstance(host_provenance["session_id"], str)
                or re.fullmatch(r"[0-9a-f]{32}", host_provenance["session_id"]) is None
                or host_provenance["pipe_name"] != "\\\\.\\pipe\\xar_profile_" + host_provenance["session_id"]):
            raise ValueError("ordinary host provenance lacks the exact active profile session/pipe")
    return {"game_pid": binding["game_pid"], "actor_id": binding["played_character_id"],
            "process_create_time": created,
            "interaction_key": interaction_key,
            "recipient_id": recipient_id, "action": "initiate_ordinary"}


def create_once_claim(directory: Path, binding: dict, interaction_key: str, recipient_id: int, request_id: str,
                      *, host_provenance=None) -> Path:
    """Never reinterpret an ACK, heartbeat, reconnect or query as a new round."""
    identity = claim_identity(binding, interaction_key, recipient_id, host_provenance)
    directory.mkdir(parents=True, exist_ok=True)
    matching = []
    for previous_path in directory.glob("*.claim.json"):
        try:
            previous = json.loads(previous_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise ValueError("ordinary claim evidence is unreadable; no retry") from error
        prior_identity = previous.get("action_identity")
        stable_pair = {key: value for key, value in identity.items() if key != "process_create_time"}
        if isinstance(prior_identity, dict) and all(prior_identity.get(key) == val for key, val in stable_pair.items()):
            if prior_identity != identity:
                raise ValueError("ordinary claim process provenance changed; unresolved evidence cannot be bypassed")
            ordinal = _integer(previous.get("claim_ordinal"), 0, 2**32 - 1, "claim_ordinal")
            matching.append((ordinal, previous_path))
    lineage = None
    ordinal = 0
    if matching:
        from .ordinary_interaction_host_release import consume_next_intent_permit
        matching.sort()
        if [item[0] for item in matching] != list(range(len(matching))):
            raise ValueError("ordinary claim lineage is incomplete; no retry")
        ordinal, previous_path = matching[-1]
        try:
            # This x-created consumption happens before the new claim/send. A
            # crash or claim write failure permanently consumes the permit.
            lineage = consume_next_intent_permit(previous_path, identity, binding, request_id)
        except (OSError, ValueError) as error:
            raise ValueError("ordinary initiation is already claimed; independent new-round proof is required") from error
        ordinal += 1
    claim = directory / (hashlib.sha256(json.dumps(identity, sort_keys=True).encode("utf-8")).hexdigest()
                         + f".{ordinal:08d}.claim.json")
    with claim.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump({"schema": "ck3-ordinary-interaction-once-claim-v1", "request_id": request_id,
                   "binding": binding, "action_identity": identity, "claim_ordinal": ordinal,
                   "host_provenance": host_provenance,
                   "new_intent_lineage": lineage,
                   "status": "claimed_result_unknown_no_retry"}, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    return claim


def preserve_receipt(claim: Path, request_id: str, result: dict) -> None:
    """Append actual receipt evidence; this intentionally grants no replay credit."""
    with claim.with_suffix(".receipt.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump({"schema": "ck3-ordinary-interaction-pending-receipt-v1", "request_id": request_id,
                   "result": result, "business_postcondition_verified": False}, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
