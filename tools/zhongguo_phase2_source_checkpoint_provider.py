#!/usr/bin/env python3
"""Canonical Phase2 span-source checkpoint registry and restore contract.

The provider consumes checkpoints already produced by a real seed/capture
lineage.  It cannot create events, copy fixtures into a runtime, use the
console, or perform an arbitrary character rebind.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Callable, Final, Mapping

from zg361_phase2_incident_checkpoint_seam import (
    IncidentCheckpointSeamError,
    validate_received_self_incident_checkpoint_receipt,
)
from zhongguo_phase2_event_choreography import Phase2EventSequencePlan


SOURCE_CHECKPOINT_REGISTRY_KIND: Final = (
    "zg361_phase2_canonical_source_checkpoint_registry"
)
LEGACY_SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION: Final = 2
SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION: Final = 3
PRODUCT_ONLY_MULTI_BRANCH_LINEAGE_KIND: Final = (
    "zg361_phase2_product_only_multi_branch_capture_lineage"
)
MULTI_BRANCH_CAPTURE_LINEAGE_MODE: Final = (
    "multi-branch-product-only-multi-session"
)
INCIDENT_STRICT_RECEIPT_FIELD: Final = (
    "received_self_incident_checkpoint_receipt"
)
ENDGAME_MATURE_OWNER_CHARACTER_ID: Final = 32904
ENDGAME_EVENT_SCALAR_CASE_BINDING_AUTHORITY: Final = (
    "paused-zg361we.356-value-scopes+source-trigger-full-guard+"
    "received-self-current-case-provider"
)
_ENDGAME_EVENT_SCALAR_SCOPE_NAMES: Final = (
    "zg361_we_al_cycle",
    "zg361_we_al_case",
)
CHECKPOINT_REQUIRED_HANDLERS: Final = (
    "capture_promotion_compensation",
    "capture_projects_metrics",
    "capture_incidents_operations",
    "capture_cross_cycle_endgame",
)


class Phase2SourceCheckpointError(RuntimeError):
    result: Final = "RED"

    def __init__(self, reason_code: str, evidence: Mapping[str, object]) -> None:
        self.reason_code = reason_code
        self.evidence = {**dict(evidence), "result": "RED", "reason_code": reason_code}
        super().__init__(f"phase-two source checkpoint RED [{reason_code}]")


@dataclass(frozen=True, slots=True)
class Phase2SourceCheckpoint:
    span_id: str
    handler: str
    source_event_definition_key: str
    owner_character_id: int
    player_character_id: int
    date_raw: int
    path: Path
    bytes: int
    sha256: str
    save_lineage_id: str
    source_receipt: Mapping[str, object]
    strict_incident_receipt: Mapping[str, object] | None


RestoreRegisteredCheckpoint = Callable[
    [Phase2SourceCheckpoint], Mapping[str, object]
]


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _lineage_set_bindings(
    value: object,
) -> tuple[tuple[str, str, str | None], ...]:
    rows = value if isinstance(value, list) else []
    bindings: list[tuple[str, str, str | None]] = []
    for raw in rows:
        row = raw if isinstance(raw, Mapping) else {}
        handler = row.get("handler")
        save_lineage_id = row.get("seed_lineage_id")
        capture_lineage = row.get("capture_lineage")
        source_input_sha256 = None
        input_checkpoint_valid = True
        if handler == "capture_incidents_operations":
            input_checkpoint = row.get("capture_run_input_checkpoint")
            input_checkpoint = (
                dict(input_checkpoint)
                if isinstance(input_checkpoint, Mapping)
                else {}
            )
            raw_input_path = input_checkpoint.get("path")
            input_path = (
                Path(raw_input_path).expanduser().resolve()
                if isinstance(raw_input_path, str)
                and Path(raw_input_path).is_absolute()
                else Path()
            )
            source_input_sha256 = str(
                input_checkpoint.get("sha256", "")
            ).upper()
            input_checkpoint_valid = bool(
                re.fullmatch(r"[0-9A-F]{64}", source_input_sha256)
                is not None
                and input_path.is_absolute()
                and input_path.is_file()
                and _positive_int(input_checkpoint.get("bytes"))
                and input_path.stat().st_size == input_checkpoint.get("bytes")
                and _sha256(input_path) == source_input_sha256
            )
        valid = (
            isinstance(handler, str)
            and bool(handler)
            and isinstance(save_lineage_id, str)
            and bool(save_lineage_id)
            and isinstance(capture_lineage, Mapping)
            and capture_lineage.get("seed_lineage_id") == save_lineage_id
            and input_checkpoint_valid
        )
        if not valid:
            return ()
        bindings.append((handler, save_lineage_id, source_input_sha256))
    return tuple(bindings)


def _lineage_set_id(
    bindings: tuple[tuple[str, str, str | None], ...]
) -> str:
    payload = json.dumps(
        [
            {
                "handler": handler,
                "seed_lineage_id": save_lineage_id,
                **(
                    {
                        "capture_run_input_checkpoint_sha256": (
                            source_input_sha256
                        )
                    }
                    if handler == "capture_incidents_operations"
                    and source_input_sha256 is not None
                    else {}
                ),
            }
            for handler, save_lineage_id, source_input_sha256 in bindings
        ],
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return "zg361-phase2-lineage-set-" + hashlib.sha256(payload).hexdigest()


def _multi_branch_lineage(
    value: object, *, lineage_set_id: object
) -> tuple[dict[str, object], dict[str, str]]:
    lineage = dict(value) if isinstance(value, Mapping) else {}
    bindings = _lineage_set_bindings(lineage.get("entry_capture_lineages"))
    handlers = tuple(
        handler for handler, _save_lineage_id, _source_sha in bindings
    )
    valid = (
        isinstance(lineage_set_id, str)
        and bool(lineage_set_id)
        and lineage.get("schema_version") == 2
        and lineage.get("kind") == PRODUCT_ONLY_MULTI_BRANCH_LINEAGE_KIND
        and lineage.get("capture_lineage_mode")
        == MULTI_BRANCH_CAPTURE_LINEAGE_MODE
        and lineage.get("lineage_set_id") == lineage_set_id
        and "seed_lineage_id" not in lineage
        and lineage.get("evidence_class") == "real_ck3"
        and lineage.get("fixture_used") is False
        and lineage.get("console_used") is False
        and handlers == CHECKPOINT_REQUIRED_HANDLERS
        and _lineage_set_id(bindings) == lineage_set_id
    )
    if not valid:
        raise Phase2SourceCheckpointError(
            "source_checkpoint_registry_lineage_set_invalid",
            {
                "lineage_set_id": lineage_set_id,
                "capture_lineage": lineage,
                "observed_handler_lineages": [
                    {
                        "handler": handler,
                        "save_lineage_id": save_lineage_id,
                        **(
                            {
                                "capture_run_input_checkpoint_sha256": (
                                    source_input_sha256
                                )
                            }
                            if source_input_sha256 is not None
                            else {}
                        ),
                    }
                    for handler, save_lineage_id, source_input_sha256 in bindings
                ],
            },
        )
    return lineage, {
        handler: save_lineage_id
        for handler, save_lineage_id, _source_sha in bindings
    }


def _typed_available(group: object, key: str) -> object | None:
    field = group.get(key) if isinstance(group, Mapping) else None
    if not (
        isinstance(field, Mapping)
        and set(field) == {"status", "value", "unavailable_reason"}
        and field.get("status") == "available"
        and field.get("unavailable_reason") is None
    ):
        return None
    return field.get("value")


def _endgame_event_scalar_scopes(context: object) -> dict[str, object]:
    frame = dict(context) if isinstance(context, Mapping) else {}
    saved_rows = frame.get("saved_scopes")
    if not isinstance(saved_rows, list):
        return {}
    result: dict[str, object] = {}
    for name in _ENDGAME_EVENT_SCALAR_SCOPE_NAMES:
        matching = [
            row
            for row in saved_rows
            if isinstance(row, Mapping) and row.get("name") == name
        ]
        if len(matching) != 1:
            return {}
        raw_scope = matching[0].get("scope")
        scope = dict(raw_scope) if isinstance(raw_scope, Mapping) else {}
        identity_value = scope.get("typed_identity")
        identity = (
            dict(identity_value)
            if isinstance(identity_value, Mapping)
            else {}
        )
        if not (
            scope.get("status") == "available"
            and scope.get("raw_type_index") == 9
            and scope.get("type_key") == "value"
            and scope.get("subtype") == 0
            and identity
            == {
                "status": "unavailable",
                "reason": "generic_scope_payload_identity_not_closed",
            }
        ):
            return {}
        result[name] = {
            "status": "available",
            "raw_type_index": 9,
            "type_key": "value",
            "subtype": 0,
            "typed_identity": identity,
        }
    return result


def validate_endgame_maturity_source_receipt(
    value: object,
    *,
    owner_character_id: object,
    player_character_id: object,
    date_raw: object,
) -> dict[str, object]:
    """Recheck that the #356 source is the owner-bound third Workforce cycle."""

    receipt = dict(value) if isinstance(value, Mapping) else {}
    proof = receipt.get("maturity_provider_proof")
    proof = dict(proof) if isinstance(proof, Mapping) else {}
    provider = proof.get("provider_response")
    provider = dict(provider) if isinstance(provider, Mapping) else {}
    provider_binding = provider.get("binding")
    provider_binding = (
        dict(provider_binding) if isinstance(provider_binding, Mapping) else {}
    )
    al_case = provider.get("al_case")
    al_case = dict(al_case) if isinstance(al_case, Mapping) else {}
    history = provider.get("history")
    history = dict(history) if isinstance(history, Mapping) else {}
    slots = proof.get("prior_slots")
    prior_cycles = proof.get("prior_cycle_serials")
    receipt_ids = proof.get("receipt_ids")
    receipt_hashes = proof.get("receipt_hashes")
    current_cycle = proof.get("cycle_serial")
    current_case = proof.get("case_serial")
    subject = receipt.get("subject_character_id")
    switch = receipt.get("maturity_player_switch_receipt")
    switch = dict(switch) if isinstance(switch, Mapping) else {}
    subject_binding = receipt.get("maturity_subject_snapshot_binding")
    subject_binding = (
        dict(subject_binding) if isinstance(subject_binding, Mapping) else {}
    )
    maturity_after_binding = receipt.get(
        "maturity_post_query_snapshot_binding"
    )
    maturity_after_binding = (
        dict(maturity_after_binding)
        if isinstance(maturity_after_binding, Mapping)
        else {}
    )
    source_binding = receipt.get("source_snapshot_binding")
    source_binding = (
        dict(source_binding) if isinstance(source_binding, Mapping) else {}
    )
    post_save_binding = receipt.get("post_save_snapshot_binding")
    post_save_binding = (
        dict(post_save_binding)
        if isinstance(post_save_binding, Mapping)
        else {}
    )
    event_scalar_scopes = _endgame_event_scalar_scopes(
        receipt.get("event_context")
    )
    post_save_event_scalar_scopes = _endgame_event_scalar_scopes(
        receipt.get("post_save_event_context")
    )
    event_case_binding = receipt.get("source_event_case_binding")
    event_case_binding = (
        dict(event_case_binding)
        if isinstance(event_case_binding, Mapping)
        else {}
    )
    raw_history_slots = history.get("slots")
    normalized_slot_values: list[dict[str, int]] = []
    observed_ids: list[int] = []
    observed_hashes: list[int] = []
    slots_valid = isinstance(slots, list) and len(slots) == 2
    if slots_valid:
        for slot in slots:
            if not isinstance(slot, Mapping):
                slots_valid = False
                break
            normalized = dict(slot)
            required = {
                "owner_character_id",
                "subject_character_id",
                "cycle_serial",
                "case_serial",
                "m357_receipt_id",
                "m357_receipt_hash",
                "m358_receipt_id",
                "m358_receipt_hash",
                "m359_receipt_id",
                "m359_receipt_hash",
            }
            if set(normalized) != required or not all(
                _positive_int(item) for item in normalized.values()
            ):
                slots_valid = False
                break
            if normalized.get("owner_character_id") != owner_character_id:
                slots_valid = False
                break
            cast = {key: int(item) for key, item in normalized.items()}
            normalized_slot_values.append(cast)
            observed_ids.extend(
                cast[f"m{milestone}_receipt_id"]
                for milestone in (357, 358, 359)
            )
            observed_hashes.extend(
                cast[f"m{milestone}_receipt_hash"]
                for milestone in (357, 358, 359)
            )
    raw_slots_match = bool(
        isinstance(raw_history_slots, list)
        and len(raw_history_slots) == 3
        and len(normalized_slot_values) == 2
        and all(
            all(
                _typed_available(raw_history_slots[index], key) == field
                for key, field in slot.items()
            )
            for index, slot in enumerate(normalized_slot_values)
        )
        and all(
            isinstance(field, Mapping)
            and field.get("status") == "unavailable"
            and field.get("value") is None
            and field.get("unavailable_reason") == "lifecycle_not_reached"
            for field in (
                raw_history_slots[2].values()
                if isinstance(raw_history_slots[2], Mapping)
                else ()
            )
        )
        and isinstance(raw_history_slots[2], Mapping)
        and len(raw_history_slots[2]) == 10
    )
    expected_event_scalar_binding = {
        "zg361_we_al_cycle": {
            **dict(event_scalar_scopes.get("zg361_we_al_cycle", {})),
            "provider_field": "cycle_serial",
            "provider_value": current_cycle,
        },
        "zg361_we_al_case": {
            **dict(event_scalar_scopes.get("zg361_we_al_case", {})),
            "provider_field": "case_serial",
            "provider_value": current_case,
        },
    }
    transport_pid = source_binding.get("bridge_pid")
    transport_generation = source_binding.get("connection_generation")
    valid = (
        receipt.get("kind")
        == "zg361_phase2_cross_cycle_endgame_source_checkpoint_v1"
        and receipt.get("event_definition_key") == "zg361we.356"
        and owner_character_id == ENDGAME_MATURE_OWNER_CHARACTER_ID
        and receipt.get("owner_character_id") == owner_character_id
        and receipt.get("player_character_id") == player_character_id
        and player_character_id == owner_character_id
        and _positive_int(subject)
        and subject != owner_character_id
        and receipt.get("date_raw") == date_raw
        and receipt.get("generic_character_rebind_used") is True
        and proof.get("schema_version") == 1
        and proof.get("result") == "GREEN"
        and proof.get("evidence_class") == "real_ck3"
        and proof.get("provider_observed") is True
        and proof.get("history_status") == "partial"
        and proof.get("history_count") == 2
        and proof.get("history_effective_count") == 2
        and proof.get("owner_character_id") == owner_character_id
        and proof.get("subject_character_id") == subject
        and _positive_int(current_cycle)
        and _positive_int(current_case)
        and proof.get("third_cycle_source_ready") is True
        and event_case_binding
        == {
            "event_definition_key": "zg361we.356",
            "owner_character_id": owner_character_id,
            "subject_character_id": subject,
            "cycle_serial": current_cycle,
            "case_serial": current_case,
            "event_owner_subject_scopes_observed": True,
            "received_self_current_case_provider_observed": True,
            "numeric_binding_authority": (
                ENDGAME_EVENT_SCALAR_CASE_BINDING_AUTHORITY
            ),
            "event_scalar_saved_scopes": expected_event_scalar_binding,
        }
        and bool(event_scalar_scopes)
        and post_save_event_scalar_scopes == event_scalar_scopes
        and isinstance(prior_cycles, list)
        and len(prior_cycles) == 2
        and all(_positive_int(cycle) for cycle in prior_cycles)
        and prior_cycles
        == [slot["cycle_serial"] for slot in normalized_slot_values]
        and prior_cycles[0] < prior_cycles[1] < current_cycle
        and slots_valid
        and receipt_ids == observed_ids
        and receipt_hashes == observed_hashes
        and len(set(observed_ids)) == 6
        and len(set(observed_hashes)) == 6
        and switch.get("schema_version") == 1
        and switch.get("accepted") is True
        and switch.get("status") == "switched"
        and switch.get("backend_id") == "native-headless"
        and switch.get("step") == f"set-played-character-v1-{subject}"
        and switch.get("from_character_id") == owner_character_id
        and switch.get("to_character_id") == subject
        and switch.get("date_raw") == date_raw
        and switch.get("postcondition_verified") is True
        and switch.get("episode_rebind_performed") is True
        and _positive_int(transport_pid)
        and _positive_int(transport_generation)
        and source_binding.get("player_character_id") == owner_character_id
        and source_binding.get("date_raw") == date_raw
        and post_save_binding.get("player_character_id") == owner_character_id
        and post_save_binding.get("date_raw") == date_raw
        and post_save_binding.get("bridge_pid") == transport_pid
        and post_save_binding.get("connection_generation")
        == transport_generation
        and switch.get("before_revision") == post_save_binding.get("revision")
        and subject_binding.get("player_character_id") == subject
        and subject_binding.get("date_raw") == date_raw
        and subject_binding.get("bridge_pid") == transport_pid
        and subject_binding.get("connection_generation")
        == transport_generation
        and switch.get("after_revision") == subject_binding.get("revision")
        and maturity_after_binding == subject_binding
        and provider.get("schema_version") == 1
        and provider.get("status") == "available"
        and provider.get("case_kind") == "zhongguo.workforce-collective"
        and provider.get("request_nonce") == "zg361.endgame.source.maturity"
        and provider.get("date_raw") == date_raw
        and provider.get("player_character_id") == subject
        and provider.get("subject_character_id") == subject
        and provider.get("requested_owner_character_id") == owner_character_id
        and provider_binding.get("request_nonce")
        == "zg361.endgame.source.maturity"
        and provider_binding.get("snapshot_id")
        == subject_binding.get("snapshot_id")
        and provider_binding.get("revision") == subject_binding.get("revision")
        and provider_binding.get("native_revision")
        == subject_binding.get("native_revision")
        and provider_binding.get("date_raw") == date_raw
        and provider_binding.get("player_character_id") == subject
        and provider_binding.get("subject_character_id") == subject
        and provider_binding.get("owner_character_id") == owner_character_id
        and _typed_available(al_case, "owner_character_id")
        == owner_character_id
        and _typed_available(al_case, "subject_character_id") == subject
        and _typed_available(al_case, "cycle_serial") == current_cycle
        and _typed_available(al_case, "case_serial") == current_case
        and _typed_available(al_case, "state") == 1
        and _typed_available(al_case, "active") is True
        and history.get("status") == "partial"
        and _typed_available(history, "count") == 2
        and history.get("effective_count") == 2
        and raw_slots_match
    )
    if not valid:
        raise Phase2SourceCheckpointError(
            "endgame_source_checkpoint_maturity_invalid",
            {
                "owner_character_id": owner_character_id,
                "player_character_id": player_character_id,
                "date_raw": date_raw,
                "source_receipt": receipt,
            },
        )
    return {
        "result": "GREEN",
        "owner_character_id": owner_character_id,
        "subject_character_id": subject,
        "cycle_serial": current_cycle,
        "case_serial": current_case,
        "history_status": "partial",
        "history_count": 2,
        "history_effective_count": 2,
        "prior_cycle_serials": list(prior_cycles),
        "generic_character_rebind_used": True,
    }


def _strict_incident_receipt(
    value: object,
    *,
    save_lineage_id: str,
    checkpoint_path: Path,
    checkpoint_bytes: object,
    checkpoint_sha256: str,
    owner_character_id: object,
    player_character_id: object,
    date_raw: object,
    event_definition_key: object,
) -> dict[str, object]:
    locator = dict(value) if isinstance(value, Mapping) else {}
    raw_path = locator.get("path")
    path = Path(raw_path).resolve() if isinstance(raw_path, str) else Path()
    expected_bytes = locator.get("bytes")
    expected_sha256 = str(locator.get("sha256", "")).upper()
    locator_valid = (
        locator.get("kind")
        == "zg361_phase2_incidents_operations_source_checkpoint_receipt"
        and isinstance(raw_path, str)
        and path.is_absolute()
        and path.is_file()
        and _positive_int(expected_bytes)
        and path.stat().st_size == expected_bytes
        and re.fullmatch(r"[0-9A-F]{64}", expected_sha256) is not None
        and _sha256(path) == expected_sha256
    )
    if not locator_valid:
        raise Phase2SourceCheckpointError(
            "incident_source_checkpoint_receipt_invalid",
            {
                "receipt_locator": locator,
                "expected_save_lineage_id": save_lineage_id,
            },
        )
    try:
        raw_receipt = json.loads(path.read_text(encoding="utf-8-sig"))
        summary = validate_received_self_incident_checkpoint_receipt(
            raw_receipt,
            expected_seed_lineage_id=save_lineage_id,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise Phase2SourceCheckpointError(
            "incident_source_checkpoint_receipt_unreadable",
            {
                "receipt_path": str(path),
                "message": f"{type(error).__name__}: {error}",
            },
        ) from error
    except IncidentCheckpointSeamError as error:
        raise Phase2SourceCheckpointError(
            "incident_source_checkpoint_receipt_invalid",
            {
                "receipt_path": str(path),
                "upstream_reason_code": error.reason_code,
                "upstream_evidence": error.evidence,
            },
        ) from error

    strict_checkpoint = summary["checkpoint"]
    assert isinstance(strict_checkpoint, Mapping)
    cross_binding_valid = (
        Path(str(strict_checkpoint.get("path"))).resolve() == checkpoint_path
        and strict_checkpoint.get("bytes") == checkpoint_bytes
        and strict_checkpoint.get("sha256") == checkpoint_sha256
        and strict_checkpoint.get("save_lineage_id") == save_lineage_id
        and summary.get("owner_character_id") == owner_character_id
        and summary.get("player_character_id") == player_character_id
        and summary.get("subject_character_id") == player_character_id
        and summary.get("date_raw") == date_raw
        and event_definition_key == "zg361.50"
    )
    if not cross_binding_valid:
        raise Phase2SourceCheckpointError(
            "incident_source_checkpoint_registry_binding_mismatch",
            {
                "receipt_path": str(path),
                "registry_checkpoint_path": str(checkpoint_path),
                "registry_checkpoint_bytes": checkpoint_bytes,
                "registry_checkpoint_sha256": checkpoint_sha256,
                "registry_owner_character_id": owner_character_id,
                "registry_player_character_id": player_character_id,
                "registry_date_raw": date_raw,
                "registry_event_definition_key": event_definition_key,
                "strict_receipt_summary": summary,
            },
        )
    return {
        **summary,
        "receipt": {
            "path": str(path),
            "bytes": int(expected_bytes),
            "sha256": expected_sha256,
        },
    }


def _entry(
    value: object,
    *,
    schema_version: int,
    expected_save_lineage_id: str,
) -> Phase2SourceCheckpoint:
    row = dict(value) if isinstance(value, Mapping) else {}
    checkpoint = row.get("checkpoint")
    checkpoint = dict(checkpoint) if isinstance(checkpoint, Mapping) else {}
    receipt = row.get("source_receipt")
    receipt = dict(receipt) if isinstance(receipt, Mapping) else {}
    raw_path = checkpoint.get("path")
    path = Path(str(raw_path)).resolve() if isinstance(raw_path, str) else Path()
    expected_bytes = checkpoint.get("bytes")
    expected_sha = str(checkpoint.get("sha256", "")).upper()
    owner = row.get("owner_character_id")
    player = row.get("player_character_id")
    date_raw = row.get("date_raw")
    event_key = row.get("source_event_definition_key")
    checkpoint_save_lineage_id = checkpoint.get("save_lineage_id")
    row_lineage_valid = (
        row.get("save_lineage_id") == expected_save_lineage_id
        if schema_version == SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION
        else row.get("save_lineage_id", expected_save_lineage_id)
        == expected_save_lineage_id
    )
    common_valid = (
        isinstance(row.get("span_id"), str)
        and isinstance(row.get("handler"), str)
        and isinstance(event_key, str)
        and bool(event_key)
        and _positive_int(owner)
        and _positive_int(player)
        and isinstance(date_raw, int)
        and not isinstance(date_raw, bool)
        and isinstance(raw_path, str)
        and path.is_absolute()
        and path.is_file()
        and _positive_int(expected_bytes)
        and path.stat().st_size == expected_bytes
        and re.fullmatch(r"[0-9A-F]{64}", expected_sha) is not None
        and _sha256(path) == expected_sha
        and checkpoint_save_lineage_id == expected_save_lineage_id
        and row_lineage_valid
    )
    receipt_valid = (
        receipt.get("result") == "GREEN"
        and receipt.get("evidence_class") == "real_ck3"
        and receipt.get("provider_observed") is True
        and receipt.get("ui_state_verified") is True
        and receipt.get("fixture_used") is False
        and receipt.get("console_used") is False
        and receipt.get("span_id") == row.get("span_id")
        and receipt.get("event_definition_key") == event_key
        and receipt.get("owner_character_id") == owner
        and receipt.get("player_character_id") == player
        and receipt.get("date_raw") == date_raw
        and str(receipt.get("checkpoint_sha256", "")).upper() == expected_sha
        and receipt.get("save_lineage_id") == expected_save_lineage_id
    )
    if not common_valid or not receipt_valid:
        raise Phase2SourceCheckpointError(
            "source_checkpoint_entry_invalid",
            {
                "span_id": row.get("span_id"),
                "handler": row.get("handler"),
                "checkpoint_path": str(path),
                "checkpoint_bytes_match": (
                    path.is_file() and path.stat().st_size == expected_bytes
                ),
                "checkpoint_sha256_match": (
                    path.is_file()
                    and re.fullmatch(r"[0-9A-F]{64}", expected_sha) is not None
                    and _sha256(path) == expected_sha
                ),
                "source_receipt": receipt,
                "expected_save_lineage_id": expected_save_lineage_id,
                "observed_row_save_lineage_id": row.get("save_lineage_id"),
                "observed_checkpoint_save_lineage_id": (
                    checkpoint_save_lineage_id
                ),
            },
        )
    strict_incident_receipt = None
    if row.get("handler") == "capture_incidents_operations":
        if not isinstance(row.get(INCIDENT_STRICT_RECEIPT_FIELD), Mapping):
            raise Phase2SourceCheckpointError(
                "incident_source_checkpoint_receipt_missing",
                {
                    "span_id": row.get("span_id"),
                    "handler": row.get("handler"),
                    "required_field": INCIDENT_STRICT_RECEIPT_FIELD,
                },
            )
        strict_incident_receipt = _strict_incident_receipt(
            row[INCIDENT_STRICT_RECEIPT_FIELD],
            save_lineage_id=expected_save_lineage_id,
            checkpoint_path=path,
            checkpoint_bytes=expected_bytes,
            checkpoint_sha256=expected_sha,
            owner_character_id=owner,
            player_character_id=player,
            date_raw=date_raw,
            event_definition_key=event_key,
        )
    elif INCIDENT_STRICT_RECEIPT_FIELD in row:
        raise Phase2SourceCheckpointError(
            "incident_source_checkpoint_receipt_misrouted",
            {
                "span_id": row.get("span_id"),
                "handler": row.get("handler"),
                "unexpected_field": INCIDENT_STRICT_RECEIPT_FIELD,
            },
        )
    if row.get("handler") == "capture_cross_cycle_endgame":
        validate_endgame_maturity_source_receipt(
            receipt,
            owner_character_id=owner,
            player_character_id=player,
            date_raw=date_raw,
        )
    return Phase2SourceCheckpoint(
        span_id=str(row["span_id"]),
        handler=str(row["handler"]),
        source_event_definition_key=str(event_key),
        owner_character_id=int(owner),
        player_character_id=int(player),
        date_raw=int(date_raw),
        path=path,
        bytes=int(expected_bytes),
        sha256=expected_sha,
        save_lineage_id=expected_save_lineage_id,
        source_receipt=receipt,
        strict_incident_receipt=strict_incident_receipt,
    )


class Phase2SourceCheckpointProvider:
    def __init__(
        self,
        registry: Mapping[str, object] | None,
        *,
        restore_registered_checkpoint: RestoreRegisteredCheckpoint | None,
        expected_seed_lineage_id: str | None = None,
        expected_lineage_set_id: str | None = None,
    ) -> None:
        self.registry = dict(registry) if isinstance(registry, Mapping) else None
        self.restore_registered_checkpoint = restore_registered_checkpoint
        self.expected_seed_lineage_id = expected_seed_lineage_id
        self.expected_lineage_set_id = expected_lineage_set_id
        self._entries: dict[str, Phase2SourceCheckpoint] | None = None

    def preflight(self) -> dict[str, object]:
        if self.registry is None:
            raise Phase2SourceCheckpointError(
                "source_checkpoint_registry_missing",
                {"required_handlers": list(CHECKPOINT_REQUIRED_HANDLERS)},
            )
        registry = self.registry
        schema_version = registry.get("schema_version")
        seed_lineage_id = registry.get("seed_lineage_id")
        lineage_set_id = registry.get("lineage_set_id")
        capture_lineage = registry.get("capture_lineage")
        rows = registry.get("entries")
        common_header_valid = (
            schema_version
            in (
                LEGACY_SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
                SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
            )
            and registry.get("registry_kind") == SOURCE_CHECKPOINT_REGISTRY_KIND
            and registry.get("result") == "GREEN"
            and registry.get("evidence_class") == "real_ck3"
            and registry.get("fixture_used") is False
            and registry.get("console_used") is False
            and isinstance(capture_lineage, Mapping)
            and isinstance(rows, list)
        )
        expected_handler_lineages: dict[str, str] = {}
        lineage_header_valid = False
        if schema_version == LEGACY_SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION:
            lineage_header_valid = bool(
                isinstance(seed_lineage_id, str)
                and seed_lineage_id
                and seed_lineage_id == self.expected_seed_lineage_id
                and self.expected_lineage_set_id is None
                and "lineage_set_id" not in registry
                and capture_lineage.get("seed_lineage_id")
                == seed_lineage_id
            )
            if lineage_header_valid:
                expected_handler_lineages = {
                    handler: seed_lineage_id
                    for handler in CHECKPOINT_REQUIRED_HANDLERS
                }
        elif schema_version == SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION:
            lineage_header_valid = bool(
                isinstance(lineage_set_id, str)
                and lineage_set_id
                and lineage_set_id == self.expected_lineage_set_id
                and self.expected_seed_lineage_id is None
                and "seed_lineage_id" not in registry
            )
            if lineage_header_valid:
                _, expected_handler_lineages = _multi_branch_lineage(
                    capture_lineage,
                    lineage_set_id=lineage_set_id,
                )
        if not common_header_valid or not lineage_header_valid:
            raise Phase2SourceCheckpointError(
                "source_checkpoint_registry_header_invalid",
                {
                    "registry": registry,
                    "expected_seed_lineage_id": self.expected_seed_lineage_id,
                    "expected_lineage_set_id": self.expected_lineage_set_id,
                },
            )
        assert isinstance(schema_version, int)
        assert isinstance(rows, list)
        raw_incident_rows = [
            row
            for row in rows
            if isinstance(row, Mapping)
            and row.get("handler") == "capture_incidents_operations"
        ]
        if any(
            row.get("owner_character_id") == row.get("player_character_id")
            for row in raw_incident_rows
        ):
            raise Phase2SourceCheckpointError(
                "incident_checkpoint_owner_equals_player",
                {
                    "incident_entries": [
                        {
                            "owner_character_id": row.get("owner_character_id"),
                            "player_character_id": row.get("player_character_id"),
                        }
                        for row in raw_incident_rows
                    ],
                    "required_binding": (
                        "played_subject_with_distinct_notice_owner"
                    ),
                },
            )
        entries = [
            _entry(
                row,
                schema_version=schema_version,
                expected_save_lineage_id=expected_handler_lineages.get(
                    str(row.get("handler")) if isinstance(row, Mapping) else "",
                    "",
                ),
            )
            for row in rows
        ]
        handlers = tuple(entry.handler for entry in entries)
        if handlers != CHECKPOINT_REQUIRED_HANDLERS or len(set(handlers)) != len(handlers):
            raise Phase2SourceCheckpointError(
                "source_checkpoint_registry_coverage_invalid",
                {
                    "required_handlers": list(CHECKPOINT_REQUIRED_HANDLERS),
                    "observed_handlers": list(handlers),
                },
            )
        self._entries = {entry.handler: entry for entry in entries}
        incident = self._entries["capture_incidents_operations"]
        assert isinstance(incident.strict_incident_receipt, Mapping)
        return {
            "schema_version": schema_version,
            "result": "GREEN",
            "registry_kind": SOURCE_CHECKPOINT_REGISTRY_KIND,
            **(
                {"seed_lineage_id": seed_lineage_id}
                if schema_version
                == LEGACY_SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION
                else {"lineage_set_id": lineage_set_id}
            ),
            "handler_save_lineage_ids": dict(expected_handler_lineages),
            "required_handlers": list(CHECKPOINT_REQUIRED_HANDLERS),
            "entry_count": len(entries),
            "incident_received_self_checkpoint": dict(
                incident.strict_incident_receipt
            ),
            "restore_interface_available": callable(
                self.restore_registered_checkpoint
            ),
            "fixture_used": False,
            "console_used": False,
        }

    def checkpoint_for_plan(
        self, plan: Phase2EventSequencePlan
    ) -> Phase2SourceCheckpoint:
        preflight = self.preflight()
        if preflight["restore_interface_available"] is not True:
            raise Phase2SourceCheckpointError(
                "registered_checkpoint_restore_provider_missing",
                {"handler": plan.handler, "preflight": preflight},
            )
        assert self._entries is not None
        entry = self._entries.get(plan.handler)
        if entry is None:
            raise Phase2SourceCheckpointError(
                "source_checkpoint_not_registered", {"handler": plan.handler}
            )
        if not (
            entry.span_id == plan.span_id
            and entry.source_event_definition_key == plan.source_event
        ):
            raise Phase2SourceCheckpointError(
                "source_checkpoint_plan_mismatch",
                {
                    "handler": plan.handler,
                    "registered_span_id": entry.span_id,
                    "registered_event": entry.source_event_definition_key,
                    "expected_span_id": plan.span_id,
                    "expected_event": plan.source_event,
                },
            )
        return entry

    def restore(self, plan: Phase2EventSequencePlan) -> dict[str, object]:
        entry = self.checkpoint_for_plan(plan)
        restore = self.restore_registered_checkpoint
        assert callable(restore)
        value = restore(entry)
        receipt = dict(value) if isinstance(value, Mapping) else {}
        if not (
            receipt.get("result") == "GREEN"
            and receipt.get("provider_observed") is True
            and receipt.get("checkpoint_sha256") == entry.sha256
            and receipt.get("save_lineage_id") == entry.save_lineage_id
            and receipt.get("player_character_id") == entry.player_character_id
            and receipt.get("owner_character_id") == entry.owner_character_id
            and receipt.get("date_raw") == entry.date_raw
            and receipt.get("event_definition_key")
            == entry.source_event_definition_key
            and receipt.get("fixture_used") is False
            and receipt.get("console_used") is False
            and receipt.get("generic_character_rebind_used") is False
        ):
            raise Phase2SourceCheckpointError(
                "registered_checkpoint_restore_not_green",
                {
                    "handler": plan.handler,
                    "checkpoint_sha256": entry.sha256,
                    "restore_receipt": receipt,
                },
            )
        return {
            "schema_version": 1,
            "result": "GREEN",
            "span_id": plan.span_id,
            "handler": plan.handler,
            "checkpoint": {
                "path": str(entry.path),
                "bytes": entry.bytes,
                "sha256": entry.sha256,
                "save_lineage_id": entry.save_lineage_id,
            },
            "expected": {
                "event_definition_key": entry.source_event_definition_key,
                "owner_character_id": entry.owner_character_id,
                "player_character_id": entry.player_character_id,
                "date_raw": entry.date_raw,
            },
            "restore_receipt": receipt,
            "fixture_used": False,
            "console_used": False,
            "generic_character_rebind_used": False,
        }


__all__ = [
    "CHECKPOINT_REQUIRED_HANDLERS",
    "ENDGAME_MATURE_OWNER_CHARACTER_ID",
    "INCIDENT_STRICT_RECEIPT_FIELD",
    "LEGACY_SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION",
    "MULTI_BRANCH_CAPTURE_LINEAGE_MODE",
    "PRODUCT_ONLY_MULTI_BRANCH_LINEAGE_KIND",
    "SOURCE_CHECKPOINT_REGISTRY_KIND",
    "SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION",
    "Phase2SourceCheckpoint",
    "Phase2SourceCheckpointError",
    "Phase2SourceCheckpointProvider",
    "RestoreRegisteredCheckpoint",
    "validate_endgame_maturity_source_receipt",
]
