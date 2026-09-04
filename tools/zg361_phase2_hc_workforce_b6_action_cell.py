#!/usr/bin/env python3
"""B6 career-HC half of the Phase-2 ``hc-workforce`` gameplay cell.

The existing M360 action executor queries the real event and submits route B.
This cell then crosses an explicit owner-to-subject session seam and requires a
new fixed native query to observe the route receipt, zero manager cost, and the
conserved career-HC partition.  The action ACK never counts as that result.
"""

from __future__ import annotations

import copy
from collections.abc import Callable, Mapping
from pathlib import Path
import sys
from typing import Protocol


ROOT = Path(__file__).resolve().parents[1]
AUTOPLAYER_SRC = ROOT / "ck3_autonomous_player" / "src"
if str(AUTOPLAYER_SRC) not in sys.path:
    sys.path.insert(0, str(AUTOPLAYER_SRC))

from xar_autoplayer.bridge.zhongguo_career_hc_workforce_postcondition_contract import (  # noqa: E402
    QUERY_ZHONGGUO_CAREER_HC_WORKFORCE_V1_CAPABILITY,
)
from zhongguo_phase2_workforce_action import (  # noqa: E402
    submit_m360_route_action,
)


class B6CareerHcWorkforceService(Protocol):
    def capabilities(self) -> dict[str, object]: ...

    def snapshot(self) -> dict[str, object]: ...

    def query_zhongguo_career_hc_workforce_postcondition_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]: ...


ActionExecutor = Callable[..., dict[str, object]]
SubjectServiceFactory = Callable[
    [Mapping[str, object]], B6CareerHcWorkforceService
]


class B6CareerHcWorkforceActionCellError(RuntimeError):
    def __init__(self, reason_code: str, evidence: Mapping[str, object]) -> None:
        self.reason_code = reason_code
        self.evidence = {
            **copy.deepcopy(dict(evidence)),
            "result": "RED",
            "reason_code": reason_code,
        }
        super().__init__(f"B6 career-HC workforce cell RED [{reason_code}]")


def _integer(value: object, label: str, *, minimum: int = 0) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= 2**63 - 1
    ):
        raise ValueError(f"{label} must be an integer in range")
    return value


def _positive(value: object, label: str) -> int:
    result = _integer(value, label, minimum=1)
    if result > 2**31 - 1:
        raise ValueError(f"{label} must be a positive signed CharacterID")
    return result


def _paused_binding(snapshot: object) -> dict[str, int | str]:
    if not isinstance(snapshot, Mapping):
        raise B6CareerHcWorkforceActionCellError(
            "subject_snapshot_not_an_object", {"snapshot": snapshot}
        )
    played = snapshot.get("played_character")
    player = played.get("character_id") if isinstance(played, Mapping) else None
    try:
        revision = _integer(snapshot.get("revision"), "snapshot.revision")
        native_revision = _integer(
            snapshot.get("native_revision"), "snapshot.native_revision", minimum=1
        )
        date_raw = _integer(snapshot.get("date_raw"), "snapshot.date_raw")
        player_id = _positive(player, "snapshot.played_character.character_id")
    except ValueError as error:
        raise B6CareerHcWorkforceActionCellError(
            "subject_paused_binding_unavailable", {"snapshot": snapshot}
        ) from error
    snapshot_id = snapshot.get("snapshot_id")
    if (
        snapshot.get("paused") is not True
        or snapshot.get("map_ready") is not True
        or not isinstance(snapshot_id, str)
        or not snapshot_id
    ):
        raise B6CareerHcWorkforceActionCellError(
            "subject_paused_binding_unavailable", {"snapshot": snapshot}
        )
    return {
        "snapshot_id": snapshot_id,
        "revision": revision,
        "native_revision": native_revision,
        "date_raw": date_raw,
        "player_character_id": player_id,
    }


def _typed(group: object, key: str, label: str) -> object:
    if not isinstance(group, Mapping):
        raise ValueError(f"{label} is not an object")
    field = group.get(key)
    if not isinstance(field, Mapping):
        raise ValueError(f"{label}.{key} is not typed")
    if field.get("status") != "available" or field.get("unavailable_reason") is not None:
        raise ValueError(f"{label}.{key} is unavailable")
    return field.get("value")


def _identity(group: object, label: str) -> tuple[int, int, int, int]:
    return (
        _positive(_typed(group, "owner_character_id", label), f"{label}.owner"),
        _positive(_typed(group, "subject_character_id", label), f"{label}.subject"),
        _integer(_typed(group, "cycle_serial", label), f"{label}.cycle", minimum=1),
        _integer(_typed(group, "case_serial", label), f"{label}.case", minimum=1),
    )


def run_b6_career_hc_workforce_gameplay_action_cell(
    owner_service: object,
    *,
    subject_service_factory: SubjectServiceFactory | None,
    request_nonce: str = "zg361.p2.hc-workforce.b6.post",
    action_executor: ActionExecutor = submit_m360_route_action,
) -> dict[str, object]:
    """Submit real M360 route B, then prove the career-HC postcondition."""

    if not isinstance(request_nonce, str) or not request_nonce:
        raise ValueError("request_nonce must be non-empty")
    evidence: dict[str, object] = {
        "schema_version": 1,
        "kind": "zg361_phase2_hc_workforce_b6_action_cell",
        "span_id": "phase2_hc_workforce",
        "producer_key": "hc-workforce",
        "result": "RED",
        "readiness": "static-ready-live-pending",
        "route": "B",
        "gameplay_action_executed": False,
        "provider_postcondition_observed": False,
        "action_ack_is_business_postcondition": False,
        "fixture_evidence_is_live": False,
        "owner_action": None,
        "subject_binding": None,
        "postcondition": None,
        "checks": None,
    }

    action = action_executor(owner_service, route="B")
    evidence["owner_action"] = copy.deepcopy(action)
    binding = action.get("binding") if isinstance(action, Mapping) else None
    if not (
        isinstance(action, Mapping)
        and action.get("result") == "ACKED"
        and action.get("business_receipt_claimed") is False
        and isinstance(binding, Mapping)
        and binding.get("route") == "B"
        and binding.get("option_number") == 2
    ):
        raise B6CareerHcWorkforceActionCellError(
            "m360_route_b_action_not_acked", evidence
        )
    try:
        owner = _positive(binding.get("owner_character_id"), "action owner")
        subject = _positive(binding.get("subject_character_id"), "action subject")
        action_date = _integer(binding.get("date_raw"), "action date")
    except ValueError as error:
        raise B6CareerHcWorkforceActionCellError(
            "m360_route_b_action_binding_invalid", evidence
        ) from error
    if owner == subject:
        raise B6CareerHcWorkforceActionCellError(
            "m360_owner_subject_not_distinct", evidence
        )
    evidence["gameplay_action_executed"] = True

    if subject_service_factory is None:
        raise B6CareerHcWorkforceActionCellError(
            "subject_provider_session_required", evidence
        )
    subject_service = subject_service_factory(binding)
    capabilities = subject_service.capabilities()
    advertised = (
        capabilities.get("bridge_capabilities")
        if isinstance(capabilities, Mapping)
        else None
    )
    if not (
        isinstance(advertised, list)
        and QUERY_ZHONGGUO_CAREER_HC_WORKFORCE_V1_CAPABILITY in advertised
    ):
        raise B6CareerHcWorkforceActionCellError(
            "career_hc_workforce_provider_unavailable",
            {**evidence, "bridge_capabilities": advertised},
        )

    after = _paused_binding(subject_service.snapshot())
    evidence["subject_binding"] = after
    if (
        after["player_character_id"] != subject
        or after["date_raw"] != action_date
    ):
        raise B6CareerHcWorkforceActionCellError(
            "subject_provider_binding_drifted", evidence
        )
    try:
        postcondition = (
            subject_service.query_zhongguo_career_hc_workforce_postcondition_v1(
                request_nonce,
                expected_revision=int(after["revision"]),
                owner_character_id=owner,
            )
        )
    except Exception as error:
        raise B6CareerHcWorkforceActionCellError(
            "career_hc_workforce_query_failed",
            {
                **evidence,
                "error_type": type(error).__name__,
                "error": str(error),
            },
        ) from error
    evidence["postcondition"] = copy.deepcopy(postcondition)

    try:
        receipt = postcondition.get("m360_receipt")
        case = postcondition.get("m360_identity")
        partition = postcondition.get("career_hc_partition")
        route_cost = postcondition.get("route_b_cost")
        readiness = postcondition.get("readiness")
        receipt_identity = _identity(receipt, "m360_receipt")
        case_identity = _identity(case, "m360_identity")
        hc_values = {
            key: _integer(
                _typed(partition, key, "career_hc_partition"),
                f"career_hc_partition.{key}",
            )
            for key in (
                "authorized", "available", "reserved", "occupied", "frozen",
                "reclaimed",
            )
        }
        hc_sum = sum(
            hc_values[key]
            for key in ("available", "reserved", "occupied", "frozen", "reclaimed")
        )
        checks = {
            "provider_status_available": postcondition.get("status") == "available"
            and postcondition.get("unavailable_reason") is None,
            "provider_readiness_green": isinstance(readiness, Mapping)
            and readiness.get("ready") is True,
            "subject_binding_exact": postcondition.get("player_character_id") == subject
            and postcondition.get("subject_character_id") == subject
            and postcondition.get("requested_owner_character_id") == owner,
            "same_m360_case_identity": receipt_identity == case_identity
            and case_identity[0] == owner
            and case_identity[1] == subject,
            "route_b_receipt_observed": receipt.get("provider_observed") is True
            and _typed(receipt, "state", "m360_receipt") == 4
            and _typed(receipt, "choice", "m360_receipt") == 2,
            "career_hc_partition_observed": isinstance(partition, Mapping)
            and partition.get("provider_observed") is True,
            "career_hc_partition_conserved": hc_values["authorized"] == hc_sum
            and _typed(partition, "conserved", "career_hc_partition") is True,
            "route_b_manager_cost_zero": isinstance(route_cost, Mapping)
            and route_cost.get("provider_observed") is True
            and _typed(route_cost, "manager_cost_total", "route_b_cost") == 0,
            "action_ack_not_used_as_result": action.get("business_receipt_claimed")
            is False,
        }
    except (AttributeError, TypeError, ValueError) as error:
        raise B6CareerHcWorkforceActionCellError(
            "career_hc_workforce_postcondition_malformed",
            {**evidence, "error": str(error)},
        ) from error
    evidence["checks"] = checks
    failed = [name for name, passed in checks.items() if passed is not True]
    if failed:
        raise B6CareerHcWorkforceActionCellError(
            "career_hc_workforce_postcondition_not_green",
            {**evidence, "failed_checks": failed},
        )

    evidence["provider_postcondition_observed"] = True
    evidence["result"] = "GREEN"
    evidence["evidence_class"] = (
        "provider-observed-live-only-when-run-against-exact-build-ck3"
    )
    return evidence


__all__ = [
    "B6CareerHcWorkforceActionCellError",
    "B6CareerHcWorkforceService",
    "run_b6_career_hc_workforce_gameplay_action_cell",
]
