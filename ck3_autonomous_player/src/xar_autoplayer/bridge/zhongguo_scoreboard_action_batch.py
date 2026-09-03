"""Lifecycle-bound scoreboard action matrix collector.

The collector is fixture-neutral: it records two surface preparations and all
named-widget action probes, but it does not call any surface-transition code
itself.  The managed live runner owns that transition and cleanup.  Each
surface's six actions must remain in one native PID/provider session.  The two
mutually-exclusive player surfaces may be separated only by an attested
canonical checkpoint clean restart; a cross-PID restore is never represented
as one session.  A false production advertisement never prevents the
independent later-query verifier from running, and never becomes a GREEN or
promotion-eligible result.
"""

from __future__ import annotations

from collections.abc import Callable
import re
from typing import Protocol

from .zhongguo_scoreboard_action_cell import (
    run_zhongguo_scoreboard_action_cell,
)


class _ScoreboardService(Protocol):
    def snapshot(self) -> dict[str, object]: ...

    def query_zhongguo_scoreboard_state_v1(
        self, request_nonce: str, *, expected_revision: int
    ) -> dict[str, object]: ...

    def activate_zhongguo_scoreboard_v1(
        self,
        request_nonce: str,
        action: str,
        **arguments: object,
    ) -> dict[str, object]: ...


SurfacePreparer = Callable[[str], dict[str, object]]

_SURFACES = ("managed-capable", "received-only")
_ACTION_PLANS = {
    "managed-capable": (
        ("open", "accepted", None),
        ("switch-received", "accepted", None),
        ("switch-managed", "accepted", None),
        ("switch-system", "accepted", None),
        ("close", "accepted", "close"),
        ("open", "accepted", "open"),
    ),
    "received-only": (
        ("open", "accepted", None),
        ("switch-system", "accepted", None),
        ("switch-received", "accepted", None),
        ("switch-managed", "managed_acl_denied", None),
        ("close", "accepted", "close"),
        ("open", "accepted", "open"),
    ),
}


def _surface_acl_matches(
    surface_id: str, source: dict[str, object]
) -> bool:
    acl = source.get("acl")
    if not isinstance(acl, dict):
        return False
    managed = acl.get("managed")
    received = acl.get("received_self")
    if not isinstance(managed, dict) or not isinstance(received, dict):
        return False
    if surface_id == "managed-capable":
        return (
            managed.get("surface_available") is True
            and managed.get("current_player_can_assess_others") is True
        )
    return (
        managed.get("surface_available") is False
        and managed.get("current_player_can_assess_others") is False
        and received.get("surface_available") is True
        and received.get("current_player_is_subject") is True
    )


def _binding(value: object) -> tuple[object, object, object, object] | None:
    if not isinstance(value, dict):
        return None
    binding = value.get("binding")
    provider = value.get("provider_session_id")
    if not isinstance(binding, dict) or not isinstance(provider, str):
        return None
    connection = binding.get("connection_generation")
    player = binding.get("player_character_id")
    date_raw = binding.get("date_raw")
    if (
        isinstance(connection, bool)
        or not isinstance(connection, int)
        or connection <= 0
        or isinstance(player, bool)
        or not isinstance(player, int)
        or player <= 0
        or isinstance(date_raw, bool)
        or not isinstance(date_raw, int)
    ):
        return None
    return provider, connection, player, date_raw


def _snapshot_binding(value: object) -> dict[str, int] | None:
    if not isinstance(value, dict):
        return None
    diagnostics = value.get("diagnostics")
    played_character = value.get("played_character")
    if not isinstance(diagnostics, dict) or not isinstance(
        played_character, dict
    ):
        return None
    binding = {
        "bridge_pid": diagnostics.get("bridge_pid"),
        "connection_generation": diagnostics.get("connection_generation"),
        "player_character_id": played_character.get("character_id"),
        "date_raw": value.get("date_raw"),
    }
    if not (
        value.get("paused") is True
        and value.get("map_ready") is True
        and all(
            isinstance(item, int) and not isinstance(item, bool)
            for item in binding.values()
        )
        and binding["bridge_pid"] > 0
        and binding["connection_generation"] > 0
        and binding["player_character_id"] > 0
    ):
        return None
    return binding


def _service_snapshot_binding(
    service: _ScoreboardService,
) -> dict[str, int] | None:
    try:
        return _snapshot_binding(service.snapshot())
    except Exception:
        return None


def _clean_restart_receipt_matches(
    preparation: dict[str, object],
    before: dict[str, int],
    after: dict[str, int],
) -> bool:
    lifecycle = preparation.get("lifecycle")
    sha256 = preparation.get("checkpoint_sha256")
    checkpoint_bytes = preparation.get("checkpoint_bytes")
    save_lineage_id = preparation.get("save_lineage_id")
    return bool(
        preparation.get("transition_kind")
        == "canonical-checkpoint-clean-restart"
        and preparation.get("restore_materialized") is True
        and preparation.get("provider_observed") is True
        and isinstance(lifecycle, dict)
        and lifecycle.get("lifecycle_intent") == "restore"
        and lifecycle.get("previous_pid") == before["bridge_pid"]
        and lifecycle.get("pid") == after["bridge_pid"]
        and lifecycle.get("previous_connection_generation")
        == before["connection_generation"]
        and lifecycle.get("connection_generation")
        == after["connection_generation"]
        and after["bridge_pid"] != before["bridge_pid"]
        and after["connection_generation"]
        == before["connection_generation"] + 1
        and isinstance(sha256, str)
        and re.fullmatch(r"[0-9A-F]{64}", sha256) is not None
        and isinstance(checkpoint_bytes, int)
        and not isinstance(checkpoint_bytes, bool)
        and checkpoint_bytes > 0
        and isinstance(save_lineage_id, str)
        and bool(save_lineage_id)
    )


def _preparation_ready(
    surface_id: str,
    preparation: dict[str, object],
    before: dict[str, int] | None,
    after: dict[str, int] | None,
) -> bool:
    if before is None or after is None:
        return False
    common = bool(
        preparation.get("surface_id") == surface_id
        and preparation.get("status") == "ready"
        and preparation.get("evidence_class") == "real_ck3"
        and preparation.get("state_origin") == "product-checkpoint"
        and preparation.get("fixture_used") is False
        and preparation.get("ocr_used") is False
        and preparation.get("coordinates_used") is False
        and preparation.get("console_used") is False
        and preparation.get("generic_character_rebind_used") is False
    )
    if not common:
        return False
    if preparation.get("transition_kind") == "already-ready-product-state":
        return before == after
    return _clean_restart_receipt_matches(preparation, before, after)


def _expected_outcome_verified(
    row: dict[str, object], expected: str
) -> bool:
    result = row.get("action_result")
    if not isinstance(result, dict):
        return False
    if expected == "accepted":
        return (
            result.get("accepted") is True
            and row.get("verified_pass") is True
            and isinstance(row.get("verified_postcondition"), dict)
        )
    return (
        result.get("accepted") is False
        and result.get("rejection_reason") == expected
        and row.get("verified_postcondition") is None
    )


def run_zhongguo_scoreboard_action_batch(
    service: _ScoreboardService,
    *,
    prepare_surface: SurfacePreparer,
    nonce_prefix: str = "zg361.scoreboard.live-batch",
) -> dict[str, object]:
    """Collect the full two-surface matrix without claiming fixture as live."""

    evidence: dict[str, object] = {
        "schema_version": 3,
        "cell_id": "scoreboard_named_widget_action_and_postcondition_matrix",
        "result": "RED",
        "evidence_stage": "transport-batch-unattested",
        "mcp_only": True,
        "ocr_used": False,
        "coordinates_used": False,
        "required_surfaces": list(_SURFACES),
        "required_primitive_actions": [
            "open",
            "switch-managed",
            "switch-received",
            "switch-system",
            "close",
        ],
        "required_reopen_composition": "close-query-open-query",
        "surface_matrix": {},
        "action_matrix": {},
        "all_postconditions_verified": False,
        "all_expected_acl_denials_verified": False,
        "binding_policy": (
            "per-surface-single-session-with-canonical-clean-restart"
        ),
        "global_single_session_required": False,
        "per_surface_single_session_binding_verified": False,
        "cross_surface_clean_restart_verified": False,
        "candidate_batch_complete": False,
        "production_capability_advertised": False,
        "promotion_eligible": False,
        "failure_reason": None,
    }
    all_postconditions = True
    all_denials = True
    all_surfaces = True
    all_bindings = True
    every_accepted_advertised = True
    surface_query_bindings: dict[
        str, tuple[object, object, object, object]
    ] = {}
    surface_snapshot_bindings: dict[str, dict[str, int]] = {}
    cross_surface_restart_verified = False

    try:
        for surface_index, surface_id in enumerate(_SURFACES, start=1):
            before_preparation = _service_snapshot_binding(service)
            preparation = prepare_surface(surface_id)
            if not isinstance(preparation, dict):
                raise ValueError("scoreboard surface preparation is malformed")
            after_preparation = _service_snapshot_binding(service)
            preparation_ready = _preparation_ready(
                surface_id,
                preparation,
                before_preparation,
                after_preparation,
            )
            if surface_index == 2:
                cross_surface_restart_verified = bool(
                    preparation_ready
                    and before_preparation
                    == surface_snapshot_bindings.get("managed-capable")
                    and after_preparation is not None
                    and _clean_restart_receipt_matches(
                        preparation,
                        before_preparation,
                        after_preparation,
                    )
                )
            if not preparation_ready:
                surface_matrix = evidence["surface_matrix"]
                action_matrix = evidence["action_matrix"]
                if not isinstance(surface_matrix, dict) or not isinstance(
                    action_matrix, dict
                ):
                    raise AssertionError("scoreboard evidence shape drifted")
                surface_matrix[surface_id] = {
                    "surface_id": surface_id,
                    "preparation": dict(preparation),
                    "before_preparation_binding": before_preparation,
                    "prepared_binding": after_preparation,
                    "preparation_ready": False,
                    "acl_verified": False,
                    "per_surface_single_session_binding_verified": False,
                    "reopen_verified": False,
                    "reopen_composition": {
                        "strategy": "close-query-open-query",
                        "close_matrix_index": None,
                        "open_matrix_index": None,
                    },
                    "surface_complete": False,
                }
                action_matrix[surface_id] = []
                reason = preparation.get("failure_reason")
                evidence["failure_reason"] = (
                    reason
                    if isinstance(reason, str) and reason
                    else f"scoreboard_surface_preparation_not_ready:{surface_id}"
                )
                return evidence
            action_rows: list[dict[str, object]] = []
            close_row: dict[str, object] | None = None
            reopen_row: dict[str, object] | None = None
            surface_acl_verified = False
            surface_binding_verified = True
            surface_query_binding: (
                tuple[object, object, object, object] | None
            ) = None
            assert after_preparation is not None

            for action_index, (action, expected, reopen_phase) in enumerate(
                _ACTION_PLANS[surface_id], start=1
            ):
                before_action = _service_snapshot_binding(service)
                row = run_zhongguo_scoreboard_action_cell(
                    service,
                    nonce_prefix=(
                        f"{nonce_prefix}.s{surface_index}.a{action_index}"
                    ),
                    requested_action=action,
                )
                after_action = _service_snapshot_binding(service)
                row["surface_id"] = surface_id
                row["matrix_index"] = action_index
                row["expected_outcome"] = expected
                row["reopen_phase"] = reopen_phase
                row["expected_outcome_verified"] = _expected_outcome_verified(
                    row, expected
                )
                row["before_action_binding"] = before_action
                row["after_action_binding"] = after_action
                action_rows.append(row)

                if not (
                    before_action == after_preparation
                    and after_action == after_preparation
                ):
                    surface_binding_verified = False

                source = row.get("source_query")
                if action_index == 1 and isinstance(source, dict):
                    surface_acl_verified = _surface_acl_matches(
                        surface_id, source
                    )
                for observed_frame in (source, row.get("later_query")):
                    observed_binding = _binding(observed_frame)
                    if observed_binding is None:
                        surface_binding_verified = False
                    elif surface_query_binding is None:
                        surface_query_binding = observed_binding
                    elif observed_binding != surface_query_binding:
                        surface_binding_verified = False
                    if observed_binding is not None and (
                        observed_binding[1]
                        != after_preparation["connection_generation"]
                        or observed_binding[2]
                        != after_preparation["player_character_id"]
                        or observed_binding[3] != after_preparation["date_raw"]
                    ):
                        surface_binding_verified = False

                if expected == "accepted":
                    all_postconditions = all_postconditions and bool(
                        row["expected_outcome_verified"]
                    )
                    action_result = row.get("action_result")
                    advertised = (
                        isinstance(action_result, dict)
                        and action_result.get(
                            "production_capability_advertised"
                        )
                        is True
                    )
                    every_accepted_advertised = (
                        every_accepted_advertised and advertised
                    )
                else:
                    all_denials = all_denials and bool(
                        row["expected_outcome_verified"]
                    )
                if reopen_phase == "close":
                    close_row = row
                elif reopen_phase == "open":
                    reopen_row = row

            reopen_verified = bool(
                close_row is not None
                and reopen_row is not None
                and close_row.get("verified_pass") is True
                and reopen_row.get("verified_pass") is True
            )
            surface_complete = bool(
                preparation_ready
                and surface_acl_verified
                and surface_binding_verified
                and reopen_verified
                and all(row["expected_outcome_verified"] for row in action_rows)
            )
            all_surfaces = all_surfaces and surface_complete
            all_bindings = all_bindings and surface_binding_verified
            if surface_query_binding is not None:
                surface_query_bindings[surface_id] = surface_query_binding
            surface_snapshot_bindings[surface_id] = after_preparation
            surface_summary = {
                "surface_id": surface_id,
                "preparation": dict(preparation),
                "before_preparation_binding": before_preparation,
                "prepared_binding": after_preparation,
                "preparation_ready": preparation_ready,
                "acl_verified": surface_acl_verified,
                "per_surface_single_session_binding_verified": (
                    surface_binding_verified
                ),
                "reopen_verified": reopen_verified,
                "reopen_composition": {
                    "strategy": "close-query-open-query",
                    "close_matrix_index": (
                        close_row.get("matrix_index")
                        if close_row is not None
                        else None
                    ),
                    "open_matrix_index": (
                        reopen_row.get("matrix_index")
                        if reopen_row is not None
                        else None
                    ),
                },
                "surface_complete": surface_complete,
            }
            surface_matrix = evidence["surface_matrix"]
            action_matrix = evidence["action_matrix"]
            if not isinstance(surface_matrix, dict) or not isinstance(
                action_matrix, dict
            ):
                raise AssertionError("scoreboard evidence shape drifted")
            surface_matrix[surface_id] = surface_summary
            action_matrix[surface_id] = action_rows

        evidence["all_postconditions_verified"] = all_postconditions
        evidence["all_expected_acl_denials_verified"] = all_denials
        evidence["per_surface_single_session_binding_verified"] = bool(
            len(surface_query_bindings) == len(_SURFACES) and all_bindings
        )
        evidence["cross_surface_clean_restart_verified"] = bool(
            cross_surface_restart_verified
            and len(surface_query_bindings) == len(_SURFACES)
            and surface_query_bindings["managed-capable"][0]
            != surface_query_bindings["received-only"][0]
            and surface_query_bindings["managed-capable"][1] + 1
            == surface_query_bindings["received-only"][1]
        )
        complete = bool(
            all_surfaces
            and all_postconditions
            and all_denials
            and evidence["per_surface_single_session_binding_verified"]
            and evidence["cross_surface_clean_restart_verified"]
        )
        evidence["candidate_batch_complete"] = complete
        evidence["production_capability_advertised"] = bool(
            complete and every_accepted_advertised
        )
        if not complete:
            evidence["failure_reason"] = "scoreboard_candidate_batch_incomplete"
        elif not every_accepted_advertised:
            evidence["failure_reason"] = "production_capability_not_advertised"
        else:
            evidence["result"] = "GREEN"
            evidence["promotion_eligible"] = True
        return evidence
    except Exception as error:
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"
        return evidence


__all__ = ["run_zhongguo_scoreboard_action_batch"]
