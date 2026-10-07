"""Observe the three original M4 materials in an explicitly chosen window.

This report has no driver, game command or strategy dependency. It reads the
existing material producers; an ACK or a request-outcome string is insufficient.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence


SCHEMA = "xar.ck3.g2_m4_material_window.v1"
# The exact4 native CDate writer divides raw hours by 24, then days by 365.
TWO_GAME_YEARS_RAW = 2 * 365 * 24
PARTS = ("construction", "council", "vassal_or_faction_intervention")


def _object(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def select_m4_window_v1(
    snapshot: Mapping[str, object], *, window_id: str,
    start_date_raw: int, end_date_raw: int,
) -> dict[str, object]:
    """Record an owner's explicit selection, without inventing a past baseline."""
    actor = _object(snapshot.get("played_character")).get("character_id")
    episode = snapshot.get("episode_run_id")
    selected_date = snapshot.get("date_raw")
    if (not isinstance(window_id, str) or not window_id
            or type(actor) is not int or actor <= 0
            or not isinstance(episode, str) or not episode
            or type(selected_date) is not int
            or type(start_date_raw) is not int or type(end_date_raw) is not int
            or not start_date_raw <= selected_date <= end_date_raw
            or not 0 < end_date_raw - start_date_raw <= TWO_GAME_YEARS_RAW):
        raise ValueError("M4 requires an explicit player/episode window of at most two game years")
    return {
        "schema": SCHEMA, "window_id": window_id,
        "episode_run_id": episode, "actor_character_id": actor,
        "start_date_raw": start_date_raw, "end_date_raw": end_date_raw,
        "selected_at_date_raw": selected_date,
        "selection_snapshot_id": snapshot.get("snapshot_id"),
        "selection_source": "explicit_owner_dates",
    }


def collect_m4_materials_v1(
    *, episode_run_id: str, actor_character_id: int,
    construction: Mapping[str, object] | None = None,
    council: Mapping[str, object] | None = None,
    sway: Mapping[str, object] | None = None,
    campaign_root: Mapping[str, object] | None = None,
    faction_receipts: Sequence[Mapping[str, object]] = (),
) -> list[dict[str, object]]:
    """Project small existing ledgers and complete faction receipt sidecars.

    Sway's resolved ledger has no episode field. Its binding is the supplied
    restored-state episode; its original full-instance material remains intact.
    """
    rows: list[dict[str, object]] = []

    def append(part: str, identity: object, start: object, material: object,
               verified: bool, source: str, **fields: object) -> None:
        rows.append({"part": part, "action_id": identity,
                     "action_date_raw": start, "material_date_raw": material,
                     "material_verified": verified, "source": source, **fields})

    construction = _object(construction)
    receipts = construction.get("applied_prior", [])
    receipts = list(receipts) if isinstance(receipts, list) else []
    receipts.append(construction.get("applied"))
    for item in receipts:
        row = _object(item)
        if not row or row.get("episode_run_id") != episode_run_id:
            continue
        # Cold completion reads retain the original start material separately.
        first = _object(row.get("start_receipt")) or row
        append("construction", row.get("action_request_id"),
               first.get("pre_date_raw"), first.get("post_date_raw"),
               row.get("status") == "applied"
               and row.get("postcondition_verified") is True
               and row.get("actor_character_id") == actor_character_id,
               "construction-formal-pending-v1.json",
               completion_status=row.get("completion_status"),
               next_turn_consumed_observed=None)

    council = _object(council)
    applied = _object(council.get("applied"))
    if applied and applied.get("episode_run_id") == episode_run_id:
        receipt = _object(_object(applied.get("receipt")).get("council_assign_councillor_receipt"))
        ack = _object(_object(applied.get("action_ack")).get("council_assign_councillor_ack"))
        independent = _object(applied.get("independent_position"))
        candidate = applied.get("candidate_character_id")
        verified = (applied.get("status") == "applied"
                    and receipt.get("status") == "applied"
                    and receipt.get("postcondition_verified") is True
                    and receipt.get("owner_character_id") == actor_character_id
                    and type(candidate) is int and candidate > 0
                    and receipt.get("incumbent_character_id") == candidate
                    and independent.get("incumbent_character_id") == candidate
                    and receipt.get("action_request_id") == applied.get("action_request_id"))
        append("council", applied.get("action_request_id"), ack.get("pre_date_raw"),
               receipt.get("post_date_raw"), verified, "private-council-formal-v1.json",
               position_key=receipt.get("position_key"),
               next_turn_consumed_observed=applied.get("next_turn_consumed"),
               following_date_raw=applied.get("next_turn_date_raw"))

    resolved = _object(_object(sway).get("resolved"))
    material = _object(resolved.get("material_intervention"))
    if material:
        modifier = _object(material.get("scheme_sway_opinion"))
        native_receipt = _object(resolved.get("native_receipt"))
        root = _object(campaign_root)
        target = material.get("target_character_id")
        direct = root.get("direct_landed_vassal_character_ids")
        vassal_observed = (root.get("status") == "available"
                           and root.get("player_character_id") == actor_character_id
                           and root.get("date_raw") == material.get("source_date_raw")
                           and isinstance(direct, list) and target in direct)
        verified = (resolved.get("postcondition_verified") is True
                    and resolved.get("actor_character_id") == actor_character_id
                    and material.get("actor_character_id") == actor_character_id
                    and material.get("action_id") == resolved.get("action_id")
                    and material.get("scheme_instance_id") == native_receipt.get("scheme_instance_id")
                    and material.get("scheme_instance_generation") == native_receipt.get("scheme_instance_generation")
                    and material.get("dedicated_benefit_observed") is True
                    and modifier.get("observed") is True and modifier.get("present") is True
                    and type(modifier.get("value")) is int and modifier["value"] > 0)
        append("vassal_or_faction_intervention", material.get("action_id"),
               resolved.get("post_date_raw"), material.get("source_date_raw"),
               verified and vassal_observed, "active-scheme-sway-formal-private-v1.json",
               subtype="sway", target_character_id=target,
               dedicated_material_verified=verified,
               direct_vassal_relationship_observed=vassal_observed,
               incremental_named_gain_observed=material.get("incremental_named_gain_observed"),
               next_turn_consumed_observed=material.get("next_turn_consumed"),
               following_date_raw=material.get("following_date_raw"))

    for sidecar in faction_receipts:
        receipt = _object(sidecar.get("receipt"))
        if sidecar.get("episode_run_id") != episode_run_id:
            continue
        verified = (receipt.get("schema_version") == 1
                    and receipt.get("status") in {"mitigated", "left"}
                    and receipt.get("postcondition_verified") is True
                    and receipt.get("mitigation_applied") is True
                    and receipt.get("player_character_id") == actor_character_id
                    and receipt.get("post_gift_opinion_present") is True
                    and type(receipt.get("post_gift_opinion_modifier_value")) is int
                    and receipt["post_gift_opinion_modifier_value"] > 0)
        append("vassal_or_faction_intervention", receipt.get("request_id"),
               sidecar.get("pre_date_raw"), receipt.get("post_observed_date_raw"),
               verified, "complete_faction_gift_receipt_sidecar",
               subtype="faction_gift", source_faction_id=receipt.get("source_faction_id"),
               next_turn_consumed_observed=None)
    return rows


def project_m4_window_progress_v1(
    window: Mapping[str, object], materials: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Report material readiness; leave authoritative milestone credit to Root."""
    if window.get("schema") != SCHEMA:
        raise ValueError("M4 explicit window schema differs")
    start, end = window["start_date_raw"], window["end_date_raw"]
    observed: list[dict[str, object]] = []
    for material in materials:
        action_date, material_date = material.get("action_date_raw"), material.get("material_date_raw")
        action_in_window = type(action_date) is int and start <= action_date <= end
        material_in_window = type(material_date) is int and start <= material_date <= end
        verified = material.get("material_verified") is True
        observed.append({**material, "action_in_window": action_in_window,
                         "material_in_window": material_in_window,
                         "qualifies_window_material": verified and action_in_window and material_in_window})
    parts = {
        part: {"material_observed": any(row["part"] == part and row["qualifies_window_material"] for row in observed),
               "observations": [row for row in observed if row["part"] == part]}
        for part in PARTS
    }
    completed = sum(value["material_observed"] for value in parts.values())
    return {"schema": "xar.ck3.g2_m4_material_window_progress.v1", "window": dict(window),
            "parts": parts, "material_parts_observed": completed, "material_parts_total": 3,
            "three_window_materials_observed": completed == 3,
            "authoritative_milestone_credit_written": False,
            "game_commands_issued": 0}
