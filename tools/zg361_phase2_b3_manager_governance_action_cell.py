#!/usr/bin/env python3
"""Formal B3 manager-governance transition and postcondition cell.

The cell delegates timeline mutation to the already bounded AI-owned B1
action, then accepts B3 completion only from the dedicated read-only manager
governance provider.  A timeline ACK or the B1 receipt alone is never promoted
to a B3 result.  Deterministic tests may inject the transition executor, but
their output remains fixture evidence and is not live CK3 evidence.
"""

from __future__ import annotations

import copy
from collections.abc import Callable, Mapping
from typing import Protocol

from xar_autoplayer.bridge.zhongguo_ai_owned_case_action import (
    run_zhongguo_ai_owned_case_background_action,
)
from xar_autoplayer.bridge.zhongguo_manager_governance_snapshot_contract import (
    QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CAPABILITY,
)


class B3ManagerGovernanceService(Protocol):
    def capabilities(self) -> dict[str, object]: ...

    def snapshot(self) -> dict[str, object]: ...

    def query_zhongguo_manager_governance_snapshot_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        subject_character_id: int,
        owner_character_id: int,
    ) -> dict[str, object]: ...


BackgroundExecutor = Callable[..., dict[str, object]]


class B3ManagerGovernanceActionCellError(RuntimeError):
    def __init__(self, reason_code: str, evidence: Mapping[str, object]) -> None:
        self.reason_code = reason_code
        self.evidence = {
            **copy.deepcopy(dict(evidence)),
            "result": "RED",
            "reason_code": reason_code,
        }
        super().__init__(f"B3 manager-governance action cell RED [{reason_code}]")


def _positive_character_id(value: object, label: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= 2**31 - 1
    ):
        raise ValueError(f"{label} must be a positive signed CharacterID")
    return value


def _paused_binding(snapshot: object) -> dict[str, object]:
    if not isinstance(snapshot, dict):
        raise B3ManagerGovernanceActionCellError(
            "snapshot_not_an_object", {"snapshot": snapshot}
        )
    revision = snapshot.get("revision")
    native_revision = snapshot.get("native_revision")
    snapshot_id = snapshot.get("snapshot_id")
    played = snapshot.get("played_character")
    player_character_id = (
        played.get("character_id") if isinstance(played, dict) else None
    )
    valid = (
        snapshot.get("paused") is True
        and snapshot.get("map_ready") is True
        and isinstance(snapshot_id, str)
        and bool(snapshot_id)
        and not isinstance(revision, bool)
        and isinstance(revision, int)
        and 0 <= revision <= 2**64 - 1
        and not isinstance(native_revision, bool)
        and isinstance(native_revision, int)
        and 1 <= native_revision <= 2**64 - 1
        and not isinstance(player_character_id, bool)
        and isinstance(player_character_id, int)
        and 1 <= player_character_id <= 2**31 - 1
    )
    if not valid:
        raise B3ManagerGovernanceActionCellError(
            "paused_binding_unavailable", {"snapshot": snapshot}
        )
    return {
        "snapshot_id": snapshot_id,
        "revision": revision,
        "native_revision": native_revision,
        "player_character_id": player_character_id,
    }


def _typed_integer(group: object, key: str) -> int | None:
    if not isinstance(group, Mapping):
        return None
    field = group.get(key)
    if not isinstance(field, Mapping) or field.get("status") != "available":
        return None
    value = field.get("value")
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _terminal_b1_cycle(transition: Mapping[str, object]) -> int | None:
    observations = transition.get("provider_observations")
    if not isinstance(observations, list) or not observations:
        return None
    terminal = observations[-1]
    if not isinstance(terminal, Mapping):
        return None
    identity = terminal.get("case_identity")
    if (
        terminal.get("classification") != "postcondition"
        or not isinstance(identity, list)
        or len(identity) != 2
    ):
        return None
    cycle = identity[0]
    if isinstance(cycle, bool) or not isinstance(cycle, int) or cycle < 1:
        return None
    return cycle


def run_b3_manager_governance_gameplay_action_cell(
    service: B3ManagerGovernanceService,
    *,
    manager_character_id: int,
    subordinate_character_id: int,
    request_nonce_prefix: str = "zg361.b3.manager",
    background_executor: BackgroundExecutor = (
        run_zhongguo_ai_owned_case_background_action
    ),
) -> dict[str, object]:
    """Advance the manager's subordinate cycle and prove the joined B3 facts."""

    manager = _positive_character_id(
        manager_character_id, "manager_character_id"
    )
    subordinate = _positive_character_id(
        subordinate_character_id, "subordinate_character_id"
    )
    if manager == subordinate:
        raise ValueError("manager and subordinate CharacterIDs must differ")
    if not isinstance(request_nonce_prefix, str) or not request_nonce_prefix:
        raise ValueError("request_nonce_prefix must be non-empty")

    capabilities = service.capabilities()
    bridge_capabilities = (
        capabilities.get("bridge_capabilities")
        if isinstance(capabilities, Mapping)
        else None
    )
    if not (
        isinstance(bridge_capabilities, list)
        and QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CAPABILITY
        in bridge_capabilities
    ):
        raise B3ManagerGovernanceActionCellError(
            "manager_governance_provider_unavailable",
            {"bridge_capabilities": bridge_capabilities},
        )

    before = _paused_binding(service.snapshot())
    player = int(before["player_character_id"])
    if manager == player:
        raise B3ManagerGovernanceActionCellError(
            "manager_must_be_bounded_ai",
            {"binding": before, "manager_character_id": manager},
        )

    transition = background_executor(
        service,
        owner_character_id=manager,
        subject_character_id=subordinate,
        request_nonce_prefix=f"{request_nonce_prefix}.b1",
        require_transition=True,
    )
    if not (
        isinstance(transition, Mapping)
        and transition.get("result") == "GREEN"
        and transition.get("gameplay_action_executed") is True
        and transition.get("gameplay_action_complete") is True
        and transition.get("background_business_complete") is True
        and transition.get("action_ack_is_business_postcondition") is False
        and transition.get("terminal_condition")
        == "new_allowlisted_roster_lock_receipt"
    ):
        raise B3ManagerGovernanceActionCellError(
            "manager_subordinate_transition_not_green",
            {"transition": transition},
        )
    b1_cycle = _terminal_b1_cycle(transition)
    if b1_cycle is None:
        raise B3ManagerGovernanceActionCellError(
            "manager_subordinate_receipt_unbound",
            {"transition": transition},
        )

    after = _paused_binding(service.snapshot())
    if after["player_character_id"] != player:
        raise B3ManagerGovernanceActionCellError(
            "played_character_drifted",
            {"before": before, "after": after},
        )
    try:
        postcondition = service.query_zhongguo_manager_governance_snapshot_v1(
            f"{request_nonce_prefix}.post",
            expected_revision=int(after["revision"]),
            subject_character_id=manager,
            owner_character_id=player,
        )
    except Exception as error:
        raise B3ManagerGovernanceActionCellError(
            "manager_governance_postcondition_query_failed",
            {
                "binding": after,
                "error_type": type(error).__name__,
                "error": str(error),
            },
        ) from error

    binding = (
        postcondition.get("binding")
        if isinstance(postcondition, Mapping)
        else None
    )
    readiness = (
        postcondition.get("readiness")
        if isinstance(postcondition, Mapping)
        else None
    )
    f_case = (
        postcondition.get("f_case")
        if isinstance(postcondition, Mapping)
        else None
    )
    team_snapshot = (
        postcondition.get("team_snapshot")
        if isinstance(postcondition, Mapping)
        else None
    )
    f035 = postcondition.get("f035") if isinstance(postcondition, Mapping) else None
    f032 = postcondition.get("f032") if isinstance(postcondition, Mapping) else None
    checks = {
        "provider_status_available": isinstance(postcondition, Mapping)
        and postcondition.get("status") == "available"
        and postcondition.get("unavailable_reason") is None,
        "provider_readiness_green": isinstance(readiness, Mapping)
        and readiness.get("ready") is True,
        "manager_binding_exact": isinstance(binding, Mapping)
        and binding.get("subject_character_id") == manager
        and binding.get("owner_character_id") == player
        and binding.get("subject_binding_kind")
        == "bounded_ai_direct_manager",
        "bounded_ai_dependency_observed": isinstance(binding, Mapping)
        and binding.get("bounded_ai_manager_dependency")
        == "zg361-bounded-ai-direct-manager-selection-v1",
        "case_identity_exact": _typed_integer(f_case, "owner_character_id")
        == player
        and _typed_integer(f_case, "subject_character_id") == manager,
        "team_snapshot_consumes_b1_cycle": _typed_integer(
            team_snapshot, "source_cycle"
        )
        == b1_cycle,
        "distribution_lifecycle_ready": isinstance(readiness, Mapping)
        and readiness.get("distribution_lifecycle_ready") is True,
        "component8_lifecycle_ready": isinstance(readiness, Mapping)
        and readiness.get("component8_lifecycle_ready") is True,
        "f035_receipt_present": isinstance(f035, Mapping)
        and isinstance(f035.get("receipt"), Mapping),
        "f032_receipt_present": isinstance(f032, Mapping)
        and isinstance(f032.get("receipt"), Mapping),
    }
    failed = [name for name, passed in checks.items() if passed is not True]
    if failed:
        raise B3ManagerGovernanceActionCellError(
            "manager_governance_postcondition_not_green",
            {
                "binding": after,
                "b1_cycle": b1_cycle,
                "checks": checks,
                "failed_checks": failed,
                "postcondition": postcondition,
            },
        )

    return {
        "schema_version": 1,
        "kind": "zg361_b3_manager_governance_gameplay_action_cell",
        "result": "GREEN",
        "evidence_class": "provider-observed-live-when-run-against-ck3",
        "fixture_evidence_is_live": False,
        "mcp_only": True,
        "ocr_used": False,
        "coordinates_used": False,
        "test_ui_used": False,
        "action_ack_is_business_postcondition": False,
        "manager_character_id": manager,
        "subordinate_character_id": subordinate,
        "superior_character_id": player,
        "source_b1_cycle": b1_cycle,
        "transition": copy.deepcopy(dict(transition)),
        "postcondition": copy.deepcopy(dict(postcondition)),
        "checks": checks,
    }


__all__ = [
    "B3ManagerGovernanceActionCellError",
    "B3ManagerGovernanceService",
    "run_b3_manager_governance_gameplay_action_cell",
]
