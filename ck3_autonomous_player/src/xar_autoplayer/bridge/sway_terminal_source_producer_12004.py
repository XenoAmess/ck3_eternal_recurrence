"""Compose copied Sway source evidence without querying or persisting state."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .active_scheme_sway_completion_termination_private_transport import (
    normalize_sway_common_native_end_12004,
)
from .sway_completion_causal_private_12004 import (
    consume_sway_end_causal_12004,
    normalize_sway_end_invocation_12004,
)
from .version_identity import CK3_12004, require_exact_native_build


_ORIGINAL_12003 = (
    "1.20.0.3", "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6",
)
_IDENTITY_FIELDS = ("actor_character_id", "target_character_id", "scheme_instance_id")
_JOURNALS = {
    "execution": ("sway_completion_execution", "xar.ck3.sway-completion-execution.v1"),
    "termination": ("sway_completion_termination", "xar.ck3.sway-completion-termination.v1"),
}


def _uint(value: object, bits: int = 32, *, minimum: int = 0) -> bool:
    return type(value) is int and minimum <= value < 1 << bits


def _signed32(value: object) -> bool:
    return type(value) is int and -(1 << 31) <= value < 1 << 31


def _actual4(value: Mapping[str, object]) -> None:
    build = value.get("build_version", value.get("exact_ck3_build"))
    digest = value.get("executable_sha256", value.get("exe_sha256"))
    if (("exact_ck3_build" in value and value["exact_ck3_build"] != build)
            or ("exe_sha256" in value and value["exe_sha256"] != digest)):
        raise ValueError("Sway producer build aliases disagree")
    if require_exact_native_build(build, digest) != CK3_12004:
        raise ValueError("Sway producer requires qualified exact 1.20.0.4")


def _original(resolved: Mapping[str, object]) -> dict[str, object]:
    receipt = resolved.get("native_receipt")
    if receipt is None:
        from ..sway_formal_consumer import _resolved_instance_identity

        observed = _resolved_instance_identity(resolved)
        if (resolved.get("status") != "applied" or resolved.get("postcondition_verified") is not True
                or observed is None):
            raise ValueError("Sway producer lacks the recovered instance observation")
        actor, target = resolved.get("actor_character_id"), resolved.get("target_character_id")
        full_id, generation = observed["scheme_instance_id"], observed["scheme_instance_generation"]
        if (not all(_uint(item) and item != 0xFFFFFFFF for item in (actor, target, full_id))
                or not _uint(generation, 8) or generation != full_id >> 24):
            raise ValueError("Sway producer recovered full identity is malformed")
        source_read = observed["source_read"]
        origin = (source_read.get("exact_ck3_build"), source_read.get("exe_sha256"))
        if origin != _ORIGINAL_12003:
            _actual4(source_read)
        return {
            "action_id": resolved["action_id"], "actor_character_id": actor,
            "target_character_id": target, "scheme_instance_id": full_id,
            "scheme_instance_generation": generation,
            "original_exact_ck3_build": origin[0], "original_exe_sha256": origin[1],
            "original_identity_source_kind": "matching_active_readback_recovery",
            "submission_receipt_available": False,
            "recovered_instance_observation": deepcopy(dict(observed)),
        }
    if (resolved.get("status") != "applied" or resolved.get("postcondition_verified") is not True
            or not isinstance(receipt, Mapping)
            or receipt.get("schema") != "active-scheme-sway-formal-private-v1"
            or receipt.get("stage") != "applied" or receipt.get("postcondition_verified") is not True
            or not isinstance(resolved.get("action_id"), str) or not resolved["action_id"]
            or receipt.get("action_id") != resolved["action_id"]):
        raise ValueError("Sway producer lacks the original applied instance receipt")
    actor = resolved.get("actor_character_id")
    target = resolved.get("target_character_id")
    full_id = receipt.get("scheme_instance_id")
    generation = receipt.get("scheme_instance_generation")
    if (not all(_uint(item) and item != 0xFFFFFFFF for item in (actor, target, full_id))
            or not _uint(generation, 8) or generation != full_id >> 24):
        raise ValueError("Sway producer original full identity is malformed")
    origin = (receipt.get("exact_ck3_build"), receipt.get("exe_sha256"))
    if origin != _ORIGINAL_12003:
        _actual4(receipt)
    return {
        "action_id": resolved["action_id"], "actor_character_id": actor,
        "target_character_id": target, "scheme_instance_id": full_id,
        "scheme_instance_generation": generation,
        "original_exact_ck3_build": origin[0], "original_exe_sha256": origin[1],
    }


def _same_instance(value: Mapping[str, object], original: Mapping[str, object]) -> bool:
    return all(type(value.get(field)) is int and value[field] == original[field]
               for field in (*_IDENTITY_FIELDS, "scheme_instance_generation"))


def _journal(value: Mapping[str, object] | None, kind: str) -> dict[str, object] | None:
    if value is None:
        return None
    key, schema = _JOURNALS[kind]
    if value.get("type") == "command_result":
        result = value.get("result")
        if (value.get("protocol_version") != 1 or value.get("ok") is not True
                or not isinstance(result, Mapping) or result.get("accepted") is not True
                or result.get("private_build") is not True or result.get("read_only") is not True
                or not isinstance(result.get(key), Mapping)):
            raise ValueError("Sway producer native command frame is malformed")
        _actual4(result)
        read = deepcopy(dict(result[key]))
        for field in ("build_version", "executable_sha256"):
            if field in read and read[field] != result.get(field):
                raise ValueError("Sway producer journal differs from its native envelope")
            read[field] = result.get(field)
        # Native envelopes carry the frame stamp; copied retained records keep their own dates.
        read["source_snapshot_revision"] = result.get("snapshot_revision")
        read["source_date_raw"] = result.get("date_raw")
    else:
        read = deepcopy(dict(value))
    _actual4(read)
    if (read.get("schema") != schema or type(read.get("available")) is not bool
            or type(read.get("retention_gap")) is not bool
            or not isinstance(read.get("records"), list)
            or any(not isinstance(record, dict) for record in read["records"])
            or any(not _uint(read.get(field)) or read[field] == 0xFFFFFFFF for field in _IDENTITY_FIELDS)):
        raise ValueError("Sway producer retained journal is malformed")
    generation = read["scheme_instance_id"] >> 24
    if "scheme_instance_generation" in read and (
            type(read["scheme_instance_generation"]) is not int or read["scheme_instance_generation"] != generation):
        raise ValueError("Sway producer journal generation differs from its full ID")
    read["scheme_instance_generation"] = generation
    return read


def _completion(value: Mapping[str, object] | None, original: Mapping[str, object]) -> dict[str, object] | None:
    if value is None:
        return None
    _actual4(value)
    if value.get("schema") != "xar.ck3.sway_completion.v1":
        raise ValueError("Sway producer completion source schema is malformed")
    if value.get("available") is not True or not _same_instance(value, original):
        return None
    if (not _uint(value.get("snapshot_revision"), 64, minimum=1)
            or not _signed32(value.get("date_raw"))):
        raise ValueError("Sway producer completion frame stamp is malformed")
    return deepcopy(dict(value))


def _current_status(read: Mapping[str, object] | None) -> dict[str, object] | None:
    if read is None or any(read.get(field) is not True for field in (
            "instance_source_observed", "instance_present", "exact_instance_join_ready", "native_status_observed")):
        return None
    if read.get("storage_slot_reused") is not False:
        return None
    status = read.get("native_status_raw")
    if type(status) is not int or status not in (0, 1):
        return None
    owner = read.get("native_owner_raw")
    allowed_owners = (read["actor_character_id"],) if status == 0 else (read["actor_character_id"], 0xFFFFFFFF)
    if type(owner) is not int or owner not in allowed_owners:
        return None
    if type(read.get("native_terminal_state_observed")) is not bool or read["native_terminal_state_observed"] != (status == 1):
        raise ValueError("Sway producer current native status and terminal flag disagree")
    return {"native_status_raw": status,
            "native_status_key": "continue" if status == 0 else "terminated_unattributed",
            "native_terminal_state_observed": status == 1,
            "terminal_cause_observed": False, "source_snapshot_revision": read["snapshot_revision"],
            "source_date_raw": read["date_raw"], "copied_completion_read": deepcopy(dict(read))}


def _retained_end(read: Mapping[str, object] | None, original: Mapping[str, object]) -> dict[str, object] | None:
    if (read is None or read.get("available") is not True or read.get("retention_gap") is not False
            or not _same_instance(read, original)):
        return None
    for record in reversed(read["records"]):
        if not _same_instance(record, original) or "native_invocation" not in record:
            continue
        invocation = normalize_sway_end_invocation_12004(record["native_invocation"], record)
        if (invocation["post_frame_observed"] is not True
                or type(record.get("pre_status")) is not int or record["pre_status"] != 0
                or type(record.get("pre_owner")) is not int
                or record["pre_owner"] != original["actor_character_id"]
                or any(record.get(field) is not True for field in (
                    "executing_source_observed", "post_read_succeeded", "post_instance_present",
                    "post_exact_instance_join_ready", "post_status_observed", "native_terminal_state_observed",
                    "native_terminal_transition_observed"))
                or record.get("post_storage_slot_reused") is not False
                or type(record.get("post_status")) is not int or record["post_status"] != 1
                or type(record.get("post_owner")) is not int
                or record["post_owner"] not in (original["actor_character_id"], 0xFFFFFFFF)):
            continue
        return {"native_status_raw": 1, "native_status_key": "terminated_unattributed",
                "native_terminal_state_observed": True, "terminal_cause_observed": False,
                "source_kind": "copied_retained_end_original_return",
                "copied_termination_record": deepcopy(record),
                "source_read": {
                    "snapshot_revision": read.get("source_snapshot_revision", read.get("snapshot_revision")),
                    "date_raw": read.get("source_date_raw", read.get("date_raw")),
                    "exact_ck3_build": read.get("build_version", read.get("exact_ck3_build")),
                    "exe_sha256": read.get("executable_sha256", read.get("exe_sha256")),
                }}
    return None


def _common_end_source(
    read: Mapping[str, object] | None, original: Mapping[str, object],
) -> dict[str, object] | None:
    if read is None or not _same_instance(read, original) or "common_native_end" not in read:
        return None
    family = normalize_sway_common_native_end_12004(read["common_native_end"], read)
    if not _same_instance(family, original):
        return None
    # Preserve partial and status0 returns independently of terminal admission.
    return deepcopy(family)


def _retained_common_end(
    family: Mapping[str, object] | None, read: Mapping[str, object] | None,
    original: Mapping[str, object],
) -> dict[str, object] | None:
    if family is None or family["available"] is not True or read is None:
        return None
    for record in reversed(family["records"]):
        entry, returned = record["entry"], record["returned"]
        if (record["original_forwarded_once"] is not True
                or record["original_returned"] is not True
                or any(frame["scheme_full_id_observed"] is not True
                       or frame["scheme_full_id_raw_u32"] != original["scheme_instance_id"]
                       or frame["scheme_instance_generation_u8"] != original["scheme_instance_generation"]
                       for frame in (entry, returned))
                or returned["status_observed"] is not True or returned["status_raw_i32"] != 1
                or returned["owner_observed"] is not True
                or returned["owner_character_full_id_raw_u32"] not in (
                    original["actor_character_id"], 0xFFFFFFFF)):
            continue
        # The query stamp dates this copied read, never the native end event.
        revision = read.get("source_snapshot_revision", read.get("snapshot_revision"))
        date = read.get("source_date_raw", read.get("date_raw"))
        source_read = {
            "snapshot_revision": revision if _uint(revision, 64, minimum=1) else None,
            "date_raw": date if _signed32(date) else None,
            "exact_ck3_build": read.get("build_version", read.get("exact_ck3_build")),
            "exe_sha256": read.get("executable_sha256", read.get("exe_sha256")),
        }
        return {
            "original_instance": deepcopy(dict(original)),
            "source_kind": "copied_common_native_end_original_return",
            "native_status_raw": 1, "native_status_key": "terminated_unattributed",
            "native_terminal_state_observed": True, "terminal_cause_observed": False,
            "copied_common_native_end_record": deepcopy(record),
            "copied_common_native_end_provenance": deepcopy({
                key: value for key, value in family.items() if key != "records"}),
            "source_read": source_read,
        }
    return None


def _modifier(value: object) -> dict[str, object]:
    if (not isinstance(value, Mapping) or set(value) != {"observed", "present", "value"}
            or type(value["observed"]) is not bool or type(value["present"]) is not bool
            or value["present"] and (value["observed"] is not True or not _signed32(value["value"]))
            or not value["present"] and value["value"] is not None):
        raise ValueError("Sway producer named modifier is malformed")
    return deepcopy(dict(value))


def _material(value: Mapping[str, object] | None, completion: Mapping[str, object] | None,
              original: Mapping[str, object]) -> dict[str, object] | None:
    if value is None:
        return None
    _actual4(value)
    if value.get("schema") != "xar.ck3.sway-outcome-opinion-v1":
        raise ValueError("Sway producer named opinion source schema is malformed")
    if (value.get("available") is not True or completion is None
            or any(type(value.get(field)) is not int or value[field] != original[field]
                   for field in ("actor_character_id", "target_character_id"))
            or type(value.get("date_raw")) is not int or value["date_raw"] != completion["date_raw"]
            or type(value.get("snapshot_revision")) is not int
            or value["snapshot_revision"] != completion["snapshot_revision"]):
        return None
    sway = _modifier(value.get("scheme_sway_opinion"))
    blocker = _modifier(value.get("sway_blocker_opinion"))
    return {**deepcopy(dict(original)), "source_kind": "copied_native_named_opinion_same_completion_frame",
            "source_snapshot_revision": value["snapshot_revision"], "source_date_raw": value["date_raw"],
            "scheme_sway_opinion": sway, "sway_blocker_opinion": blocker,
            "dedicated_benefit_observed": None if not sway["observed"] else sway["present"] and sway["value"] > 0,
            "dedicated_setback_observed": None if not blocker["observed"] else blocker["present"],
            "incremental_named_gain_observed": None, "terminal_cause_observed": False,
            "copied_opinion_read": deepcopy(dict(value))}


def compose_sway_terminal_sources_12004(
    *, original_resolved: Mapping[str, object], completion_read: Mapping[str, object] | None = None,
    execution_frame: Mapping[str, object] | None = None,
    termination_frame: Mapping[str, object] | None = None,
    opinion_read: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Return independent source planes for the original full instance.

    Journal arguments accept copied command_result frames or already normalized
    retained reads. No state, clock, native call or lifecycle persistence changes.
    Notification titles and historical material summaries never become cause inputs.
    """
    original = _original(original_resolved)
    completion = _completion(completion_read, original)
    execution = _journal(execution_frame, "execution")
    termination = _journal(termination_frame, "termination")
    common_end = _common_end_source(termination, original)
    pair = None
    causal = None
    if (execution is not None and termination is not None
            and _same_instance(execution, original) and _same_instance(termination, original)):
        pair = {"execution_read": execution, "termination_read": termination}
        causal = consume_sway_end_causal_12004(**pair)
    material = _material(opinion_read, completion, original)
    historical = original_resolved.get("material_intervention")
    retained_material = None
    if isinstance(historical, Mapping) and _same_instance(historical, original):
        retained_material = {"source_kind": "historical_derived_ledger_summary",
                             "current_native_material_observation": False,
                             "terminal_cause_input": False, "copied_summary": deepcopy(dict(historical))}
    return {
        "schema": "xar.ck3.sway-terminal-source-composition.12004.v1",
        "original_instance": original,
        "current_instance_observation": _current_status(completion),
        "retained_end_observation": _retained_end(termination, original),
        "common_native_end_source": deepcopy(common_end),
        "retained_common_end_observation": _retained_common_end(common_end, termination, original),
        "cause_input_pair": deepcopy(pair), "causal_observation": deepcopy(causal),
        "terminal_cause_observed": causal is not None,
        "terminal_cause_key": None if causal is None else causal["cause_key"],
        "named_material_observation": material, "retained_material_context": retained_material,
        "invalidation_notification_terminal_cause_qualified": False,
        "invalidation_missing": "exact_12004_notification_binding_and_dynamic_end_relationship_unavailable",
    }
