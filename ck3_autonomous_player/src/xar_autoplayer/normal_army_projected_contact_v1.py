"""Current native ordered Contact inputs for an ordinary endpoint decision."""
from __future__ import annotations

from .bridge.projected_contact_contract import (
    normalize_projected_contact_scope,
    parse_query_projected_contact_scope_v1_step,
    query_projected_contact_scope_v1_step,
)


def select_normal_army_projected_contact_v1(
    snapshot, query_rows, *, subject_army_id, target_province_id,
    incoming_entry_province_id, subject_current_province_id,
    subject_owner_character_id=None,
):
    """Consume an existing query's current target; do not project future troops."""
    request = (subject_army_id, target_province_id, incoming_entry_province_id)
    query_step = query_projected_contact_scope_v1_step(*request)
    missing = {"status": "query_required", "query_step": query_step}
    diagnostics = snapshot.get("diagnostics")
    generation = diagnostics.get("connection_generation") if isinstance(diagnostics, dict) else None
    for row in reversed(query_rows):
        if row.get("ok") is not True or parse_query_projected_contact_scope_v1_step(row.get("step")) != request:
            continue
        result = row.get("result")
        if not isinstance(result, dict) or not all((
            result.get("queried_snapshot_id") == snapshot.get("snapshot_id"),
            result.get("queried_revision") == snapshot.get("revision"),
            result.get("queried_native_revision") == snapshot.get("native_revision"),
            result.get("queried_connection_generation") == generation,
            result.get("queried_episode_run_id") == snapshot.get("episode_run_id"),
        )):
            continue
        try:
            scope = normalize_projected_contact_scope(
                result.get("projected_contact_scope"),
                expected_subject_army_id=subject_army_id,
                expected_target_province_id=target_province_id,
                expected_incoming_entry_province_id=incoming_entry_province_id,
                expected_date_raw=snapshot.get("date_raw"),
                expected_snapshot_revision=snapshot.get("native_revision"),
                expected_subject_current_province_id=subject_current_province_id,
                expected_subject_owner_character_id=subject_owner_character_id,
            )
        except ValueError:
            continue
        return {
            "status": "available", "query_step": query_step,
            "projection": scope, "transition_kind": scope["transition_kind"],
            "subject_side": scope["projected_subject_side"],
            "attacker_army_ids": list(scope["projected_attacker_army_ids"]),
            "defender_army_ids": list(scope["projected_defender_army_ids"]),
            "incoming_attacker_geometry_ready": (
                scope["transition_kind"] == "create_new"
                and scope["projected_subject_side"] == "attacker"
            ),
            "actual_arrival_observed": False, "future_contact_authorized": False,
        }
    return missing
