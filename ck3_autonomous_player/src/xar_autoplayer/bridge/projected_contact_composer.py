"""Compose read-only query configs from fresh native arrival observations.

This module calls no bridge or game API. The native projection remains a
hypothetical arrival against the current target state, and an existing v2
request remains a fixed-contact diagnostic without reinforcement or win odds.
"""
from __future__ import annotations

from datetime import datetime, timezone

from .combat_contract import combat_simulation_encounter_scope
from .projected_contact_contract import (
    normalize_projected_contact_scope,
    projected_contact_subject_scope,
    query_projected_contact_scope_v1_step,
)
from .public_unit_contract import public_cunit_id


def _province(value: object, name: str) -> int:
    if type(value) is not int or not 1 <= value <= 2**31 - 1:
        raise ValueError(f"{name} must be a positive int32")
    return value


def _binding(snapshot: dict[str, object]) -> dict[str, object]:
    if snapshot.get("paused") is not True:
        raise ValueError("query composition requires a fresh paused snapshot")
    for name, low, high in (("revision", 0, 2**64 - 1),
                            ("native_revision", 1, 2**64 - 1),
                            ("date_raw", -(2**31), 2**31 - 1)):
        value = snapshot.get(name)
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"snapshot lacks a valid {name}")
    diagnostics = snapshot.get("diagnostics")
    return {
        **{name: snapshot.get(name) for name in
           ("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id")},
        "connection_generation": diagnostics.get("connection_generation")
        if isinstance(diagnostics, dict) else None,
        "composed_at_utc": datetime.now(timezone.utc).isoformat(),
        "expected_revision_source": "fresh public snapshot revision",
        "calls_executed": False,
    }


def _call(tool: str, arguments: dict[str, object], revision: int) -> dict[str, object]:
    return {"tool": tool, "arguments": {**arguments, "expected_revision": revision},
            "revision_argument": "expected_revision", "revision_source": "revision"}


def _same_receipt_binding(receipt: object, binding: dict[str, object], label: str) -> dict[str, object]:
    if not isinstance(receipt, dict):
        raise ValueError(f"{label} must be the native query response object")
    for name in ("snapshot_id", "revision", "native_revision", "episode_run_id"):
        if receipt.get("queried_" + name) != binding[name]:
            raise ValueError(f"{label} belongs to another {name}; refresh stage A")
    if receipt.get("queried_connection_generation") != binding["connection_generation"]:
        raise ValueError(f"{label} belongs to another connection generation")
    if receipt.get("accepted") is not True or receipt.get("status") != "available":
        raise ValueError(f"{label} is unavailable")
    return receipt


def _preview_edge(snapshot: dict[str, object], preview_response: object,
                  binding: dict[str, object]) -> dict[str, object]:
    receipt = _same_receipt_binding(preview_response, binding, "route preview")
    preview = receipt.get("route_preview")
    if not isinstance(preview, dict) or preview.get("status") != "available":
        raise ValueError("route preview is unavailable")
    subject = public_cunit_id(preview.get("army_id"), "preview army_id")
    actual = projected_contact_subject_scope(snapshot, subject)
    origin = _province(preview.get("origin_province_id"), "preview origin_province_id")
    target = _province(preview.get("target_province_id"), "preview target_province_id")
    route_values = preview.get("route_province_ids")
    if (not isinstance(route_values, list) or origin != actual["current_province_id"]
            or preview.get("previewed_date_raw") != binding["date_raw"]
            or receipt.get("step") != f"preview-move-army-{subject}-to-{target}"):
        raise ValueError("route preview actual subject or date binding disagrees")
    route = [_province(item, "route_province_ids") for item in route_values]
    remaining = route[1:] if route and route[0] == origin else route
    if not remaining or remaining[-1] != target:
        raise ValueError("arrival projection requires a route ending at the target")
    entry = remaining[-2] if len(remaining) > 1 else origin
    query_projected_contact_scope_v1_step(subject, target, entry)
    return {"subject_army_id": subject, "subject_current_province_id": origin,
            "target_province_id": target, "incoming_entry_province_id": entry,
            "route_province_ids": route, "incoming_edge_source": "fresh native preview last edge"}


def compose_arrival_refresh_calls(snapshot: dict[str, object], subject_army_id: int,
                                  target_province_id: int) -> dict[str, object]:
    """Stage A refreshes the actual subject and previews its current native route."""
    binding = _binding(snapshot)
    subject = public_cunit_id(subject_army_id, "subject_army_id")
    actual = projected_contact_subject_scope(snapshot, subject)
    target = _province(target_province_id, "target_province_id")
    return {"status": "prepared_read_only_calls", "stage": "refresh_actual_inputs",
            "revision_metadata": binding,
            "actual_subject_current_province_id": actual["current_province_id"],
            "calls": [
                _call("ck3_query_army_strengths", {"army_ids": [subject]}, binding["revision"]),
                _call("ck3_query_army_commander_candidates_v1", {"army_id": subject}, binding["revision"]),
                _call("ck3_execute_step", {"step": f"preview-move-army-{subject}-to-{target}"}, binding["revision"]),
            ]}


def compose_projected_contact_calls(snapshot: dict[str, object], preview_response: object) -> dict[str, object]:
    """Stage B uses the fresh preview's final edge as incoming position input."""
    binding = _binding(snapshot)
    edge = _preview_edge(snapshot, preview_response, binding)
    arguments = {name: edge[name] for name in
                 ("subject_army_id", "target_province_id", "incoming_entry_province_id")}
    return {"status": "prepared_read_only_calls", "stage": "project_current_target_state",
            "revision_metadata": binding, "preview_binding": edge,
            "calls": [_call("ck3_query_projected_contact_scope_v1", arguments, binding["revision"])]}


def compose_projected_combat_calls(
    snapshot: dict[str, object], preview_response: object, projection_response: object, *,
    attacker_entry_province_id: int | None = None,
    attacker_entry_provenance: str | None = None,
) -> dict[str, object]:
    """Stage C preserves projected sides/order in an existing v2 diagnostic.

    For create_new with an attacking subject, its incoming edge is the attacker
    edge. A defending subject or join_existing needs an independently supplied
    attacker edge; the arriving player's edge is never renamed to fill it.
    """
    binding = _binding(snapshot)
    edge = _preview_edge(snapshot, preview_response, binding)
    receipt = _same_receipt_binding(projection_response, binding, "projected contact")
    subject = projected_contact_subject_scope(snapshot, edge["subject_army_id"])
    expected_step = query_projected_contact_scope_v1_step(
        edge["subject_army_id"], edge["target_province_id"], edge["incoming_entry_province_id"])
    if receipt.get("step") != expected_step:
        raise ValueError("projected contact does not use the preview's incoming edge")
    scope = normalize_projected_contact_scope(
        receipt.get("projected_contact_scope"),
        expected_subject_army_id=edge["subject_army_id"],
        expected_target_province_id=edge["target_province_id"],
        expected_incoming_entry_province_id=edge["incoming_entry_province_id"],
        expected_date_raw=binding["date_raw"], expected_snapshot_revision=binding["native_revision"],
        expected_subject_current_province_id=subject["current_province_id"],
        expected_subject_owner_character_id=subject["owner_character_id"],
    )
    result = {"status": "available", "stage": "compose_fixed_contact_v2_diagnostic",
              "revision_metadata": binding, "preview_binding": edge,
              "projected_contact_scope": scope, "calls": [],
              "diagnostic_contract": "hypothetical_fixed_contact_against_current_target_state",
              "limitations": ["No future reinforcement, ongoing battle resume, or win odds claim."]}
    if scope["transition_kind"] == "none":
        return {**result, "composition_status": "complete_no_contact"}
    attackers = scope["projected_attacker_army_ids"]
    defenders = scope["projected_defender_army_ids"]
    try:
        encounter = combat_simulation_encounter_scope(snapshot, attackers, defenders)
    except ValueError as error:
        return {**result, "composition_status": "outside_existing_v2_encounter_scope",
                "composition_detail": str(error)}
    result["common_war_ids"] = encounter["common_war_ids"]
    if scope["transition_kind"] == "create_new" and scope["projected_subject_side"] == "attacker":
        entry = edge["incoming_entry_province_id"]
        if attacker_entry_province_id is not None and attacker_entry_province_id != entry:
            raise ValueError("new attacking subject's v2 edge must match its native preview")
        provenance = "attacking subject's fresh native preview last edge"
    else:
        if attacker_entry_province_id is None or not isinstance(attacker_entry_provenance, str) or not attacker_entry_provenance.strip():
            return {**result, "composition_status": "requires_independent_attacker_entry",
                    "composition_detail": "Incoming subject edge is not the v2 attacker edge for this native role/transition."}
        entry = _province(attacker_entry_province_id, "attacker_entry_province_id")
        provenance = attacker_entry_provenance
    if entry == edge["target_province_id"]:
        raise ValueError("attacker_entry_province_id must differ from the target")
    # Ordered participant arrays are copied without sorting, partitioning, or
    # inferring a player-attacker role from the movement direction.
    result["attacker_entry_binding"] = {"attacker_entry_province_id": entry,
                                        "source": provenance}
    result["composition_status"] = "prepared_read_only_calls"
    result["calls"] = [
        _call("ck3_query_army_strengths", {"army_ids": [*attackers, *defenders]}, binding["revision"]),
        _call("ck3_query_combat_simulation_inputs", {
            "target_province_id": edge["target_province_id"],
            "attacker_entry_province_id": entry,
            "attacker_army_ids": list(attackers), "defender_army_ids": list(defenders),
        }, binding["revision"]),
    ]
    return result
