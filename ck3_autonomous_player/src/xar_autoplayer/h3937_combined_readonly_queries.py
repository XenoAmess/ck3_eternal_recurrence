"""Disabled H3937 same-session read-only query sequence.

The caller must own and clean up one qualified managed native session. This
module cannot launch CK3 and never supplies action or date authorization.
"""

from __future__ import annotations

import copy
from typing import Protocol

from .bridge.native_driver import (
    _army_in_combat_or_retreat,
    _army_is_known_stationary,
    _route_contact_hostile_ids,
)
from .bridge.war_contract import (
    normalize_province_local_siege_result,
    normalize_route_contact_horizon,
    query_province_local_siege_step,
    query_route_contact_horizon_step,
)
from .errors import AgentError
from .h3937_paused_war_scope_run import (
    ARMY_ID, EXPECTED_DATE_RAW, EXPECTED_EPISODE_RUN_ID,
    TARGET_PROVINCE_ID, _phase0_scope,
)
from .h3937_stationary_route_contact_query_run import (
    _same_frame, _snapshot_history,
)


H3937_COMBINED_LIVE_AUTHORIZED = False
_COMPLETE_ROUTE_STATUSES = {"complete_empty", "complete_nonempty"}


class ReadOnlyService(Protocol):
    def snapshot(self) -> dict[str, object]: ...

    def execute_step(
        self, step: str, *, expected_revision: int,
    ) -> dict[str, object]: ...


def _complete_published_scope(frame: object) -> dict[str, object] | None:
    """Require explicit per-army route proof for the whole published war row."""
    scope = _phase0_scope(frame)
    if scope is None or not isinstance(frame, dict):
        return None
    war = frame["active_wars"][0]
    subject = next((row for row in frame["player_armies"]
                    if isinstance(row, dict) and row.get("army_id") == ARMY_ID), None)
    if not (
        isinstance(subject, dict)
        and subject.get("route_read_status") == "complete_empty"
        and subject.get("route_source_count") == 0
        and _army_is_known_stationary(subject)
        and not _army_in_combat_or_retreat(subject)
    ):
        return None
    rows = [*frame["player_armies"], *war["allied_armies"],
            *war["enemy_armies"]]
    evidence: dict[int, dict[str, object]] = {}
    for row in rows:
        if not isinstance(row, dict):
            return None
        army_id = row.get("army_id")
        status = row.get("route_read_status")
        count = row.get("route_source_count")
        route = row.get("route_province_ids")
        if (
            type(army_id) is not int or army_id <= 0
            or status not in _COMPLETE_ROUTE_STATUSES
            or type(count) is not int or count < 0
            or not isinstance(route, list) or count != len(route)
            or (status == "complete_empty") != (count == 0)
        ):
            return None
        selected = {"route_read_status": status, "route_source_count": count}
        if army_id in evidence and evidence[army_id] != selected:
            return None
        evidence[army_id] = selected
    hostiles = _route_contact_hostile_ids(frame)
    if (not hostiles
            or list(hostiles) != scope["query_eligible_hostile_army_ids"]
            or len(hostiles) > 64):
        return None
    return {
        **scope,
        "route_read_completeness_proven": True,
        "route_read_evidence_by_army_id": evidence,
        "complete_physical_army_inventory_proven": False,
    }


def _exact_appended_query(
    before: object, after: object, step: str, result: object,
) -> bool:
    old = _snapshot_history(before)
    new = _snapshot_history(after)
    if old is None or new is None or len(new) != len(old) + 1:
        return False
    row = new[-1]
    return bool(
        new[:-1] == old and isinstance(row, dict)
        and row.get("command") == step and row.get("ok") is True
        and row.get("result") == result
    )


def _bound_dynamic_contact_result(
    frame: dict[str, object], result: object, step: str,
    hostiles: tuple[int, ...],
) -> bool:
    if not isinstance(result, dict):
        return False
    diagnostics = frame.get("diagnostics")
    generation = (diagnostics.get("connection_generation")
                  if isinstance(diagnostics, dict) else None)
    sequence = result.get("query_sequence")
    if not (
        result.get("step") == step
        and result.get("accepted") is True
        and result.get("status") == "available"
        and result.get("backend_id") == "native-headless"
        and type(sequence) is int and sequence > 0
        and result.get("snapshot_revision") == frame.get("native_revision")
        and result.get("queried_snapshot_id") == frame.get("snapshot_id")
        and result.get("queried_revision") == frame.get("revision")
        and result.get("queried_native_revision") == frame.get("native_revision")
        and type(generation) is int and generation > 0
        and result.get("queried_connection_generation") == generation
        and result.get("queried_episode_run_id") == EXPECTED_EPISODE_RUN_ID
    ):
        return False
    try:
        normalize_route_contact_horizon(
            result.get("route_contact_horizon"),
            expected_subject_army_id=ARMY_ID,
            expected_target_province_id=TARGET_PROVINCE_ID,
            expected_hostile_army_ids=hostiles,
            expected_date_raw=EXPECTED_DATE_RAW,
            expected_snapshot_revision=int(frame["native_revision"]),
        )
    except (TypeError, ValueError):
        return False
    return True


def collect_h3937_combined_reads_in_session(
    service: ReadOnlyService,
) -> dict[str, object]:
    """Collect at most two queries in one paused frame; outer cleanup remains RED."""
    if H3937_COMBINED_LIVE_AUTHORIZED is not True:
        raise AgentError("H3937 combined read-only collector has no live authorization")
    frames: list[dict[str, object]] = []
    envelopes: list[dict[str, object]] = []
    steps: list[str] = []
    error: str | None = None
    checks: dict[str, bool] = {}
    scope: dict[str, object] | None = None
    try:
        first = service.snapshot()
        frames.append(copy.deepcopy(first))
        scope = _complete_published_scope(first)
        checks["complete_native_published_scope"] = scope is not None
        if scope is None:
            raise AgentError("H3937 native-published war or route scope incomplete")
        province_step = query_province_local_siege_step(TARGET_PROVINCE_ID)
        steps.append(province_step)
        province_result = service.execute_step(
            province_step, expected_revision=int(first["revision"]),
        )
        envelopes.append(copy.deepcopy(province_result))
        middle = service.snapshot()
        frames.append(copy.deepcopy(middle))
        checks["province_same_frame"] = _same_frame(first, middle)
        checks["province_scope_unchanged"] = (
            _complete_published_scope(middle) == scope)
        checks["province_exact_history"] = _exact_appended_query(
            first, middle, province_step, province_result)
        province = normalize_province_local_siege_result(
            province_result,
            expected_step=province_step,
            expected_province_id=TARGET_PROVINCE_ID,
            expected_snapshot_revision=int(first["native_revision"]),
            expected_date_raw=EXPECTED_DATE_RAW,
        )
        checks["province_available"] = province["status"] == "available"
        if not all(checks.values()):
            raise AgentError("H3937 province 2610 read-only proof incomplete")
        assert isinstance(middle, dict)
        hostiles = _route_contact_hostile_ids(middle)
        checks["dynamic_hostiles_match_war_row"] = (
            list(hostiles) == scope["query_eligible_hostile_army_ids"])
        if not checks["dynamic_hostiles_match_war_row"]:
            raise AgentError("H3937 dynamic hostile roster changed")
        contact_step = query_route_contact_horizon_step(
            ARMY_ID, TARGET_PROVINCE_ID, hostiles)
        steps.append(contact_step)
        contact_result = service.execute_step(
            contact_step, expected_revision=int(middle["revision"]),
        )
        envelopes.append(copy.deepcopy(contact_result))
        last = service.snapshot()
        frames.append(copy.deepcopy(last))
        checks["contact_same_frame"] = _same_frame(middle, last)
        checks["contact_scope_unchanged"] = (
            _complete_published_scope(last) == scope)
        checks["contact_exact_history"] = _exact_appended_query(
            middle, last, contact_step, contact_result)
        checks["dynamic_contact_bound"] = _bound_dynamic_contact_result(
            middle, contact_result, contact_step, hostiles)
        checks["query_sequence_consecutive"] = bool(
            type(province_result.get("query_sequence")) is int
            and type(contact_result.get("query_sequence")) is int
            and contact_result["query_sequence"]
            == province_result["query_sequence"] + 1)
        if not all(checks.values()):
            raise AgentError("H3937 dynamic route-contact read-only proof incomplete")
    except Exception as caught:
        error = f"{type(caught).__name__}: {caught}"
    observed = error is None and all(checks.values())
    return {
        "schema": "xar.ck3.h3937-combined-readonly-inner-v1",
        "observed": observed,
        "status": "READ_ONLY_INNER_OBSERVED" if observed else "RED",
        "outer_session_cleanup_verified": False,
        "physical_army_inventory_completeness_proven": False,
        "action_authorized": False,
        "date_advance_authorized": False,
        "gameplay_actions": 0,
        "query_attempts": len(steps),
        "steps": steps,
        "envelopes": envelopes,
        "frames": frames,
        "scope": scope,
        "checks": checks,
        "error": error,
    }
