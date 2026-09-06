#!/usr/bin/env python3
"""Capture the two real ZhongGuo scoreboard surfaces in one strict order.

This module only coordinates the existing scoreboard checkpoint builder and
capture primitive.  An optional acceptance fixture may carry the played
identity from the managed owner to the received subject, but it may not create
scoreboard state or receipts.  Both surface truths always come from the native
product query consumed by ``capture_current_zhongguo_scoreboard_surface_v1``.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Callable, Final, Mapping, Protocol

from zhongguo_scoreboard_surface_checkpoint_provider import (
    SCOREBOARD_REQUIRED_SURFACES,
    ScoreboardSurfaceService,
    scoreboard_surface_snapshot_binding,
)
from zhongguo_scoreboard_surface_checkpoint_registry import (
    ScoreboardSurfaceCheckpointRegistryBuilder,
    capture_current_zhongguo_scoreboard_surface_v1,
)


IdentityCarrier = Callable[..., Mapping[str, object]]


class ScoreboardSurfaceCaptureService(ScoreboardSurfaceService, Protocol):
    """Existing read-only surface query plus the managed native save seam."""

    def save_checkpoint(
        self, *, expected_revision: int
    ) -> dict[str, object]: ...


class ScoreboardSurfaceCaptureOrchestrationError(RuntimeError):
    """Typed RED emitted before a two-surface registry can be written."""

    result: Final = "RED"

    def __init__(self, reason_code: str, evidence: Mapping[str, object]) -> None:
        self.reason_code = reason_code
        self.evidence = {
            **deepcopy(dict(evidence)),
            "result": "RED",
            "reason_code": reason_code,
        }
        super().__init__(f"scoreboard surface capture RED [{reason_code}]")


def _fail(reason_code: str, **evidence: object) -> None:
    raise ScoreboardSurfaceCaptureOrchestrationError(reason_code, evidence)


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _typed_available(value: object) -> object | None:
    row = value if isinstance(value, Mapping) else {}
    if (
        set(row) == {"status", "value", "unavailable_reason"}
        and row.get("status") == "available"
        and row.get("unavailable_reason") is None
    ):
        return row.get("value")
    return None


def _validate_identity_carrier(
    value: object,
    *,
    owner_character_id: int,
    subject_character_id: int,
    date_raw: int,
) -> dict[str, object]:
    receipt = deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    fixture_used = receipt.get("identity_carrier_fixture_used")
    valid = bool(
        receipt.get("result") == "GREEN"
        and isinstance(fixture_used, bool)
        and receipt.get("fixture_wrote_scoreboard_state") is False
        and receipt.get("fixture_wrote_scoreboard_receipt") is False
        and receipt.get("surface_truth_source") == "native-product-query"
        and receipt.get("provider_observed") is True
        and receipt.get("action_ack_used_as_identity_postcondition") is False
        and receipt.get("owner_character_id") == owner_character_id
        and receipt.get("subject_character_id") == subject_character_id
        and receipt.get("player_character_id_before") == owner_character_id
        and receipt.get("player_character_id_after") == subject_character_id
        and receipt.get("date_raw") == date_raw
    )
    if not valid:
        _fail(
            "scoreboard_identity_carrier_receipt_invalid",
            expected_owner_character_id=owner_character_id,
            expected_subject_character_id=subject_character_id,
            expected_date_raw=date_raw,
            identity_carrier_receipt=receipt,
        )
    return receipt


def _acl(value: Mapping[str, object], key: str) -> Mapping[str, object]:
    acl = value.get("acl")
    acl = acl if isinstance(acl, Mapping) else {}
    row = acl.get(key)
    return row if isinstance(row, Mapping) else {}


def _validate_pair_relationships(
    registry: Mapping[str, object],
    *,
    owner_character_id: int,
    subject_character_id: int,
) -> None:
    entries = registry.get("entries")
    rows = entries if isinstance(entries, list) else []
    if (
        tuple(
            row.get("surface_id") if isinstance(row, Mapping) else None
            for row in rows
        )
        != SCOREBOARD_REQUIRED_SURFACES
        or len(rows) != 2
        or not all(isinstance(row, Mapping) for row in rows)
    ):
        _fail(
            "scoreboard_surface_pair_coverage_invalid",
            required_surfaces=list(SCOREBOARD_REQUIRED_SURFACES),
            registry=registry,
        )
    managed = rows[0]
    received = rows[1]
    assert isinstance(managed, Mapping)
    assert isinstance(received, Mapping)
    managed_query = managed.get("source_query")
    received_query = received.get("source_query")
    managed_query = (
        managed_query if isinstance(managed_query, Mapping) else {}
    )
    received_query = (
        received_query if isinstance(received_query, Mapping) else {}
    )
    managed_acl = _acl(managed_query, "managed")
    received_acl = _acl(received_query, "received_self")
    pair_valid = bool(
        managed.get("player_character_id") == owner_character_id
        and managed.get("owner_character_id") == owner_character_id
        and _typed_available(managed_acl.get("owner_character_id"))
        == owner_character_id
        and _typed_available(managed_acl.get("first_subject_character_id"))
        == subject_character_id
        and received.get("player_character_id") == subject_character_id
        and received.get("owner_character_id") == owner_character_id
        and _typed_available(received_acl.get("owner_character_id"))
        == owner_character_id
        and _typed_available(received_acl.get("subject_character_id"))
        == subject_character_id
        and _typed_available(received_acl.get("first_row_character_id"))
        == subject_character_id
        and all(
            _positive_int(_typed_available(received_acl.get(key)))
            for key in ("cycle_serial", "result_case_serial", "b1_case_serial")
        )
    )
    if not pair_valid:
        _fail(
            "scoreboard_surface_pair_identity_invalid",
            expected_owner_character_id=owner_character_id,
            expected_subject_character_id=subject_character_id,
            managed_entry=managed,
            received_entry=received,
        )


def capture_managed_received_scoreboard_surfaces_v1(
    service: ScoreboardSurfaceCaptureService,
    builder: ScoreboardSurfaceCheckpointRegistryBuilder,
    *,
    received_subject_character_id: int,
    identity_carrier: IdentityCarrier,
    registry_path: Path,
) -> dict[str, object]:
    """Capture managed -> identity-only transition -> received, then write.

    The output path is not touched until both native queries, both saves, the
    identity-only carrier receipt, and the cross-surface owner/subject tuple
    have all passed their strict contracts.
    """

    if not _positive_int(received_subject_character_id):
        raise ValueError("received_subject_character_id must be positive")
    if not callable(identity_carrier):
        raise ValueError("identity_carrier must be callable")
    if not isinstance(registry_path, Path):
        raise ValueError("registry_path must be a pathlib.Path")

    managed_capture = capture_current_zhongguo_scoreboard_surface_v1(
        service, builder, "managed-capable"
    )
    managed_contract = managed_capture.get("query_contract")
    managed_contract = (
        managed_contract if isinstance(managed_contract, Mapping) else {}
    )
    owner = managed_contract.get("player_character_id")
    date_raw = managed_contract.get("date_raw")
    if not (
        _positive_int(owner)
        and isinstance(date_raw, int)
        and not isinstance(date_raw, bool)
        and owner != received_subject_character_id
    ):
        _fail(
            "scoreboard_managed_capture_identity_invalid",
            managed_capture=managed_capture,
            received_subject_character_id=received_subject_character_id,
        )
    assert isinstance(owner, int)
    assert isinstance(date_raw, int)

    before_transition = scoreboard_surface_snapshot_binding(
        service.snapshot()
    )
    if not (
        before_transition.get("player_character_id") == owner
        and before_transition.get("date_raw") == date_raw
    ):
        _fail(
            "scoreboard_identity_carrier_precondition_drifted",
            managed_capture=managed_capture,
            before_transition=before_transition,
        )

    raw_carrier = identity_carrier(
        expected_owner_character_id=owner,
        expected_subject_character_id=received_subject_character_id,
        expected_date_raw=date_raw,
    )
    carrier = _validate_identity_carrier(
        raw_carrier,
        owner_character_id=owner,
        subject_character_id=received_subject_character_id,
        date_raw=date_raw,
    )
    after_transition = scoreboard_surface_snapshot_binding(
        service.snapshot()
    )
    transition_valid = bool(
        after_transition.get("player_character_id")
        == received_subject_character_id
        and after_transition.get("date_raw") == date_raw
        and after_transition.get("bridge_pid")
        == before_transition.get("bridge_pid")
        and after_transition.get("connection_generation")
        == before_transition.get("connection_generation")
        and int(after_transition.get("revision", -1))
        > int(before_transition.get("revision", -1))
        and int(after_transition.get("native_revision", -1))
        > int(before_transition.get("native_revision", -1))
    )
    if not transition_valid:
        _fail(
            "scoreboard_identity_carrier_postcondition_invalid",
            before_transition=before_transition,
            after_transition=after_transition,
            identity_carrier_receipt=carrier,
        )

    received_capture = capture_current_zhongguo_scoreboard_surface_v1(
        service, builder, "received-only"
    )
    registry_candidate = builder.finalize()
    _validate_pair_relationships(
        registry_candidate,
        owner_character_id=owner,
        subject_character_id=received_subject_character_id,
    )
    registry = builder.write(registry_path)
    fixture_used = bool(carrier["identity_carrier_fixture_used"])
    return {
        "schema_version": 1,
        "result": "GREEN",
        "surface_truth_source": "native-product-query",
        "surface_capture_order": list(SCOREBOARD_REQUIRED_SURFACES),
        "managed_capture": managed_capture,
        "identity_carrier": carrier,
        "received_capture": received_capture,
        "registry": registry,
        "identity_carrier_fixture_used": fixture_used,
        "fixture_used": fixture_used,
        "fixture_wrote_scoreboard_state": False,
        "fixture_wrote_scoreboard_receipt": False,
        "scoreboard_surface_state_fixture_used": False,
        "scoreboard_surface_receipt_fixture_used": False,
        "action_ack_used_as_surface_truth": False,
    }


__all__ = [
    "IdentityCarrier",
    "ScoreboardSurfaceCaptureService",
    "ScoreboardSurfaceCaptureOrchestrationError",
    "capture_managed_received_scoreboard_surfaces_v1",
]
