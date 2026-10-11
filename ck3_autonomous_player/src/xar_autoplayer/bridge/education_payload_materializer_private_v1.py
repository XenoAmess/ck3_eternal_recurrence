"""Construct an education payload from a supplied current ordinary query.

This private leaf performs no query, native call, command, or dispatch. The
review token binds source content and requested full IDs. It is not an action
authorization or evidence that the native education materializer is qualified.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import re

from .nonwar_private_build import private_native_build_identity
from .ordinary_interaction_contract import interaction_binding, normalize_public_query
from .version_identity import CK3_12004


INTERACTION_KEY = "educate_child_interaction"
REVIEW_SCHEMA = "xar.ck3.education-payload-review-private.v1"
REQUEST_SCHEMA = "xar.ck3.education-payload-reviewed-request-private.v1"
PAYLOAD_SCHEMA = "xar.ck3.education-payload-materialization-private.v1"
_REQUEST_KEYS = {
    "schema", "request_id", "review_token", "expected_snapshot_id",
    "expected_revision", "expected_native_revision", "recipient_id",
    "child_full_id", "guardian_full_id", "requested_option_keys",
}


def _full_id(value: object, name: str) -> int:
    if type(value) is not int or not 1 <= value <= 0xFFFFFFFE:
        raise ValueError(f"{name} requires a complete unsigned Character ID")
    return value


def _option_keys(value: object) -> list[str]:
    if type(value) not in (list, tuple) or len(value) > 4096:
        raise ValueError("requested_option_keys requires a bounded explicit list")
    keys = list(value)
    if (any(type(key) is not str or re.fullmatch(r"[A-Za-z0-9_]{1,128}", key) is None
            for key in keys) or len(set(keys)) != len(keys)):
        raise ValueError("requested option keys must be exact distinct ASCII keys")
    return keys


def _digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=True, allow_nan=False).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def prepare_education_payload_review_v1(
    query: object, snapshot: object, *, expected_revision: int,
    recipient_id: int, child_full_id: int, guardian_full_id: int,
    requested_option_keys: object = None,
) -> dict[str, object]:
    """Preserve native terms and prepare only an observed, exact role selection.

    Current typed rows preserve actual per-ordinal bank selection separately
    from the legacy flag getter's first-match result. The optional leaf is
    validated by the existing ordinary query normalizer before use here.
    An older query without that leaf retains its count-only qualification.
    """
    recipient_id = _full_id(recipient_id, "recipient_id")
    child_full_id = _full_id(child_full_id, "child_full_id")
    guardian_full_id = _full_id(guardian_full_id, "guardian_full_id")
    if child_full_id == guardian_full_id:
        raise ValueError("education child and guardian must differ")
    keys = None if requested_option_keys is None else _option_keys(requested_option_keys)
    if private_native_build_identity(snapshot) != CK3_12004:
        raise ValueError("education payload requires the exact current 1.20.0.4 build")
    binding = interaction_binding(snapshot, expected_revision)
    source = normalize_public_query(query, binding, INTERACTION_KEY, recipient_id)
    native = source["character_interaction_ordinary_context"]
    roles = deepcopy(native["effective_roles"])
    intent = {
        "recipient_id": recipient_id,
        "child_full_id": child_full_id,
        "guardian_full_id": guardian_full_id,
        "requested_option_keys": keys,
    }
    selected = native["selected_option_count"]
    declared = native["declared_option_count"]
    row_leaf = native.get("education_option_rows")
    rows_available = isinstance(row_leaf, dict) and row_leaf["status"] == "available"
    # The shared ordinary normalizer owns the closed row schema. Keep the
    # complete source rows, including duplicate flags and byte values 2..255.
    rows = deepcopy(row_leaf["rows"]) if rows_available else None
    selected_rows = [row for row in rows if row["ordinal_selected"]] if rows_available else None
    selected_key_unavailable = rows_available and any(
        row["canonical_flag_key"] is None for row in selected_rows
    )
    observed_keys = (list(dict.fromkeys(row["canonical_flag_key"] for row in selected_rows))
                     if rows_available and not selected_key_unavailable else None)
    reason = None
    if native["status"] != "available":
        reason = "native_context_unavailable"
    elif roles["secondary_recipient_id"] is None or roles["secondary_actor_id"] is None:
        reason = "education_secondary_roles_unavailable"
    elif (roles["secondary_recipient_id"] != child_full_id
          or roles["secondary_actor_id"] != guardian_full_id):
        reason = "education_selected_full_roles_mismatch"
    elif keys is None:
        reason = "education_option_intent_unsupplied"
    elif row_leaf is not None and not rows_available:
        reason = "education_option_rows_unavailable"
    elif rows_available and selected_key_unavailable:
        reason = "observed_selected_option_key_unavailable"
    elif rows_available and set(keys) != set(observed_keys):
        reason = "education_selected_option_intent_mismatch"
    elif not rows_available and keys:
        reason = "requested_option_flag_identity_unpublished"
    elif not rows_available and selected != 0:
        reason = "observed_selected_option_identity_unpublished"
    elif native["special_payload_present"]:
        reason = "education_special_payload_materialization_unqualified"

    known_empty = native["status"] == "available" and (
        not selected_rows if rows_available else row_leaf is None and selected == 0
    )
    option_source = {
        "status": ("known_empty" if known_empty else
                   "available" if observed_keys is not None else "unavailable"),
        "declared_option_count": declared,
        # This earlier-stage getter count remains independent of bank rows.
        "selected_option_count": selected,
        "selected_ordinal_count": len(selected_rows) if rows_available else None,
        "selected_option_keys": observed_keys if rows_available else [] if known_empty else None,
        # Do not substitute the old DIPLO5 positional mask for current flags.
        "native_selected_option_mask": None,
        "native_option_rows": rows,
        "raw_education_option_rows": deepcopy(row_leaf),
    }
    payload = None
    token = None
    if reason is None:
        payload = {
            "interaction_key": INTERACTION_KEY,
            "full_id_encoding": "uint32_generation_preserved",
            "effective_roles": deepcopy(roles),
            "semantic_subject_character_id": child_full_id,
            "semantic_object_character_id": guardian_full_id,
            "selected_option_keys": observed_keys if rows_available else [],
            "all_declared_options_off": known_empty,
            "declared_option_count": declared,
            "selected_option_count": selected,
        }
        if rows_available:
            # Leave the legacy count-only semantic payload byte-for-byte
            # equivalent when the optional typed leaf is absent. Its existing
            # content token does not change merely by adding support here.
            payload.update({
                "selected_ordinal_count": len(selected_rows),
                "native_option_rows": deepcopy(rows),
                "selected_option_ordinals": [row["declared_ordinal"] for row in selected_rows],
                "selected_option_flags_full_u32": [row["flag_full_u32"] for row in selected_rows],
                "option_bank_values_u8": [row["bank_value_u8"] for row in rows],
            })
        token = _digest({"source_query": source, "request_intent": intent,
                         "semantic_payload": payload})
    return {
        "schema": REVIEW_SCHEMA,
        "status": "available" if reason is None else "unavailable",
        "reason": reason,
        "read_only": True,
        "request_intent": intent,
        "source_query": deepcopy(source),
        "effective_roles": roles,
        "option_source": option_source,
        "requested_shown": native["shown"] if reason is None else None,
        "requested_can_send": native["can_send"] if reason is None else None,
        "semantic_payload": payload,
        "review_token": token,
        "generic_ordinary_context_supported": native["ordinary_context_supported"],
        "native_materialization_ready": False,
        "dispatch_ready": False,
        "submitted": False,
        "material_result": False,
    }


def materialize_reviewed_education_payload_v1(
    reviewed_request: object, query: object, snapshot: object,
) -> dict[str, object]:
    """Consume a content-bound review request into a memory-free payload.

    This revalidates the supplied query and snapshot. It never constructs a
    CCharacterInteractionContext or a send command and never executes a step.
    """
    if type(reviewed_request) is not dict or set(reviewed_request) != _REQUEST_KEYS:
        raise ValueError("education reviewed request must have the exact private fields")
    request = reviewed_request
    if request["schema"] != REQUEST_SCHEMA:
        raise ValueError("education reviewed request schema is mismatched")
    if (type(request["request_id"]) is not str
            or re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", request["request_id"]) is None):
        raise ValueError("education request_id must be a bounded exact ASCII ID")
    if (type(request["review_token"]) is not str
            or re.fullmatch(r"[0-9a-f]{64}", request["review_token"]) is None):
        raise ValueError("education review token must bind the prepared content")
    for key in ("expected_revision", "expected_native_revision"):
        if type(request[key]) is not int or not 1 <= request[key] <= 0xFFFFFFFFFFFFFFFF:
            raise ValueError(f"education {key} must preserve its exact revision")
    prepared = prepare_education_payload_review_v1(
        query, snapshot, expected_revision=request["expected_revision"],
        recipient_id=request["recipient_id"], child_full_id=request["child_full_id"],
        guardian_full_id=request["guardian_full_id"],
        requested_option_keys=request["requested_option_keys"],
    )
    if prepared["status"] != "available":
        raise ValueError("education payload unavailable: " + prepared["reason"])
    source = prepared["source_query"]
    if (type(request["expected_snapshot_id"]) is not str
            or request["expected_snapshot_id"] != source["queried_snapshot_id"]
            or request["expected_native_revision"] != source["queried_native_revision"]
            or request["review_token"] != prepared["review_token"]):
        raise ValueError("education reviewed source, token, or frame changed")
    return {
        "schema": PAYLOAD_SCHEMA,
        "status": "constructed_offline",
        "read_only": True,
        "request_id": request["request_id"],
        "review_token": prepared["review_token"],
        "review_binding_verified": True,
        "queried_snapshot_id": source["queried_snapshot_id"],
        "queried_revision": source["queried_revision"],
        "queried_native_revision": source["queried_native_revision"],
        "request_intent": deepcopy(prepared["request_intent"]),
        "semantic_payload": deepcopy(prepared["semantic_payload"]),
        "source_query": deepcopy(source),
        "requested_shown": prepared["requested_shown"],
        "requested_can_send": prepared["requested_can_send"],
        "generic_ordinary_context_supported": prepared["generic_ordinary_context_supported"],
        "native_materialization_ready": False,
        "native_materialization_reason": "education_all_roles_options_command_join_unqualified",
        "dispatch_ready": False,
        "dispatch_invoked": False,
        "submitted": False,
        "material_result": False,
    }
