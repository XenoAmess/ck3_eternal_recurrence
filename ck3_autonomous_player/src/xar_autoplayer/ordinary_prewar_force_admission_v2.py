"""Consume the current typed coalition query for ordinary declaration policy."""

from __future__ import annotations

from collections.abc import Mapping

from .bridge.prewar_force_coalition_v2_contract import assess_prewar_force_risk_v2


PREWAR_FORCE_COALITION_V2_QUERY_KEY = "prewar_force_coalition_coverage_v2_query"
PREWAR_FORCE_COALITION_V2_CAPABILITY = (
    "game.command.query-prewar-force-coalition-coverage-v2-N"
)


def _integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _date_raw(value: object) -> bool:
    return (
        isinstance(value, int) and not isinstance(value, bool)
        and -(1 << 31) <= value < (1 << 31)
    )


def assess_ordinary_prewar_force_admission_v2(
    snapshot: Mapping[str, object] | None,
    declaration: Mapping[str, object],
) -> dict[str, object]:
    """Keep partial/stale coverage separate from an insufficient known margin.

    The Driver supplies a filtered detached envelope. Its independent outer
    receipt and the current snapshot bind the DTO; the domain cannot certify
    its own request, time, actor or declaration. The shared assessor owns the
    integer risk policy and Native mobilization qualification.
    """
    result: dict[str, object] = {
        "status": "unknown",
        "declare_admitted": False,
        "force_risk_qualified": False,
        "reason": "current_force_coalition_query_required",
        "required_prewar_force_coalition_query": None,
    }
    if not isinstance(snapshot, Mapping):
        result["reason"] = "current_snapshot_required"
        return result
    actor = snapshot.get("played_character")
    diagnostics = snapshot.get("diagnostics")
    if (
        snapshot.get("paused") is not True
        or snapshot.get("map_ready") is not True
        or not isinstance(actor, Mapping)
        or actor.get("alive") is not True
        or not _integer(actor.get("character_id"))
        or actor.get("character_id") == 0
        or not isinstance(diagnostics, Mapping)
    ):
        result["reason"] = "current_paused_living_actor_required"
        return result
    hello = diagnostics.get("hello")
    if not isinstance(hello, Mapping) or hello.get("bridge_version") != "0.1.0.4":
        result["reason"] = "current_native_build_required"
        return result
    snapshot_id = snapshot.get("snapshot_id")
    episode_run_id = snapshot.get("episode_run_id")
    lease = {
        "queried_snapshot_id": snapshot_id,
        "queried_revision": snapshot.get("revision"),
        "queried_native_revision": snapshot.get("native_revision"),
        "queried_date_raw": snapshot.get("date_raw"),
        "queried_actor_character_id": actor.get("character_id"),
        "queried_connection_generation": diagnostics.get("connection_generation"),
        "queried_episode_run_id": episode_run_id,
    }
    if (
        not isinstance(snapshot_id, str) or not snapshot_id
        or not all(_integer(lease[key]) for key in (
            "queried_revision", "queried_native_revision",
            "queried_connection_generation",
        ))
        or not _date_raw(lease["queried_date_raw"])
        or (episode_run_id is not None
            and (not isinstance(episode_run_id, str) or not episode_run_id))
    ):
        result["reason"] = "current_snapshot_binding_required"
        return result
    declaration_id = declaration.get("declaration_id")
    if not isinstance(declaration_id, str) or not declaration_id:
        result["reason"] = "current_declaration_identity_required"
        return result
    envelope = snapshot.get(PREWAR_FORCE_COALITION_V2_QUERY_KEY)
    if not isinstance(envelope, Mapping):
        result["required_prewar_force_coalition_query"] = {
            "declaration_id": declaration_id,
            "expected_revision": snapshot["revision"],
            "profile": "v2",
        }
        return result
    if (
        any(key not in envelope or envelope[key] != value for key, value in lease.items())
        or not all(_integer(envelope.get(key)) for key in (
            "queried_revision", "queried_native_revision",
            "queried_actor_character_id", "queried_connection_generation",
        ))
        or not _date_raw(envelope.get("queried_date_raw"))
    ):
        result["reason"] = "force_coalition_query_scope_stale"
        return result
    if envelope.get("accepted") is not True:
        result["reason"] = "force_coalition_query_not_accepted"
        return result
    receipt = envelope.get("execution_receipt")
    request_id = envelope.get("native_request_id")
    value = envelope.get("prewar_force_coalition_coverage_v2")
    if (
        not isinstance(receipt, Mapping)
        or set(receipt) != {"ticket", "query_sequence", "capture_epoch"}
        or not isinstance(request_id, str) or not request_id
        or not isinstance(value, Mapping)
    ):
        result["reason"] = "independent_force_coalition_receipt_required"
        return result
    # A present partial/failed query is consumed as unknown, not queried again.
    if envelope.get("status") != "available":
        result["reason"] = "force_coalition_coverage_partial"
        return result
    try:
        risk = assess_prewar_force_risk_v2(
            value,
            snapshot=snapshot,
            expected_declaration=declaration,
            expected_request_binding={"request_id": request_id, **dict(receipt)},
            expected_request_id=request_id,
        )
    except (TypeError, ValueError) as error:
        result["reason"] = "force_coalition_coverage_invalid"
        result["diagnostic"] = str(error)
        return result
    result["force_risk"] = risk
    result["status"] = risk["status"]
    result["reason"] = risk["reason"]
    result["force_risk_qualified"] = risk.get("force_risk_qualified") is True
    roles = value.get("final_cb_roles")
    final_legal = (
        isinstance(roles, Mapping) and roles.get("final_can_send") is True
    )
    result["declare_admitted"] = (
        risk.get("status") == "qualified"
        and risk.get("force_risk_qualified") is True
        and final_legal
    )
    if risk.get("status") == "qualified" and not final_legal:
        result["status"] = "unknown"
        result["reason"] = "current_selected_native_declaration_legality_required"
    return result
