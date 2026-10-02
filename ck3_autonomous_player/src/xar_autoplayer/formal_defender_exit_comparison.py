"""Pure, fail-closed comparison of de-jure surrender cost and continuation risk.

This module validates a proposed evidence bundle and performs only
componentwise arithmetic. It does not assign utility weights, recommend an
outcome, construct a game step, or authenticate external evidence.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any


POLICY = "formal-primary-defender-de-jure-exit-comparison-v1"
FRAME_KEYS = frozenset({
    "snapshot_id", "revision", "native_revision", "date_raw",
    "episode_run_id", "connection_generation", "checkpoint_sha256",
    "war_id", "primary_attacker_character_id",
    "primary_defender_character_id", "casus_belli_key",
    "casus_belli_database_index", "target_title_ids",
})
RESOURCES = frozenset({
    "gold", "prestige", "prestige_experience", "piety",
    "piety_experience", "legitimacy", "stress",
})
OPERATION_KINDS = frozenset({
    "title_holder", "title_liege", "character_liege", "claim",
})


def _integer(value: object, *, positive: bool = False) -> bool:
    return type(value) is int and -(2**63) <= value <= 2**63 - 1 and (
        not positive or value > 0
    )


def _sha(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        character in "0123456789ABCDEF" for character in value
    )


def _frame(frame: object) -> bool:
    if not isinstance(frame, dict) or set(frame) != FRAME_KEYS:
        return False
    if not all(_integer(frame[key], positive=True) for key in (
        "revision", "native_revision", "connection_generation", "war_id",
        "primary_attacker_character_id", "primary_defender_character_id",
    )):
        return False
    if not _integer(frame["date_raw"], positive=True):
        return False
    if frame["primary_attacker_character_id"] == frame["primary_defender_character_id"]:
        return False
    if not all(isinstance(frame[key], str) and frame[key] for key in (
        "snapshot_id", "episode_run_id",
    )) or not _sha(frame["checkpoint_sha256"]):
        return False
    if (
        frame["casus_belli_key"] != "individual_county_de_jure_cb"
        or frame["casus_belli_database_index"] != 17
    ):
        return False
    titles = frame["target_title_ids"]
    return bool(
        isinstance(titles, list) and titles
        and all(_integer(title, positive=True) for title in titles)
        and len(titles) == len(set(titles))
    )


def _bound(payload: object, frame: dict[str, object]) -> bool:
    return isinstance(payload, dict) and payload.get("frame") == frame


def _unavailable(reason: str, frame: object) -> dict[str, object]:
    return {
        "policy": POLICY,
        "status": "unavailable",
        "reason": reason,
        "frame": copy.deepcopy(frame) if _frame(frame) else None,
        "comparison": None,
        "comparison_sha256": None,
        "recommended_outcome": None,
        "action_literal": None,
    }


def _operations(value: object, *, require_targets: set[int] | None) -> bool:
    if not isinstance(value, list):
        return False
    seen: set[tuple[str, int, int | None, int | None]] = set()
    holder_targets: set[int] = set()
    for row in value:
        if not isinstance(row, dict) or set(row) != {
            "kind", "entity_id", "before_id", "after_id"
        }:
            return False
        kind, entity_id = row["kind"], row["entity_id"]
        before, after = row["before_id"], row["after_id"]
        if (
            not isinstance(kind, str)
            or kind not in OPERATION_KINDS
            or not _integer(entity_id, positive=True)
            or not all(item is None or _integer(item, positive=True)
                       for item in (before, after))
            or before == after
        ):
            return False
        identity = (kind, entity_id, before, after)
        if identity in seen:
            return False
        seen.add(identity)
        if kind == "title_holder":
            holder_targets.add(entity_id)
    return require_targets is None or require_targets <= holder_targets


def _resource_rows(value: object, parties: set[int], *, bounds: bool) -> dict[tuple[int, str], Any] | None:
    if not isinstance(value, list) or len(value) != 14:
        return None
    result: dict[tuple[int, str], Any] = {}
    expected_keys = {"character_id", "resource", "lower_raw", "upper_raw", "scale"} if bounds else {
        "character_id", "resource", "raw", "scale"
    }
    for row in value:
        if not isinstance(row, dict) or set(row) != expected_keys:
            return None
        character_id, resource = row["character_id"], row["resource"]
        if (
            not _integer(character_id, positive=True)
            or character_id not in parties
            or not isinstance(resource, str)
            or resource not in RESOURCES
            or row["scale"] != 100_000
        ):
            return None
        identity = character_id, resource
        if identity in result:
            return None
        if bounds:
            lower, upper = row["lower_raw"], row["upper_raw"]
            if not _integer(lower) or not _integer(upper) or lower > upper:
                return None
            result[identity] = lower, upper
        else:
            raw = row["raw"]
            if not _integer(raw):
                return None
            result[identity] = raw
    if set(result) != {(party, resource) for party in parties for resource in RESOURCES}:
        return None
    return result


def _digest(payload: dict[str, object]) -> str | None:
    try:
        encoded = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("ascii")
    except (TypeError, ValueError, OverflowError):
        return None
    return hashlib.sha256(encoded).hexdigest().upper()


def compare_defender_dejure_surrender_cost_to_continuation_risk(
    frame: object, option: object, terms: object, continuation_risk: object,
) -> dict[str, object]:
    """Compare exact signed resource deltas to bounded continuation intervals.

    A successful result is structural and componentwise, never a recommendation.
    Producer authenticity and the strategy threshold are separate requirements.
    """
    if not _frame(frame):
        return _unavailable("frame_invalid", frame)
    if not _bound(option, frame):
        return _unavailable("option_frame_mismatch", frame)
    if not _bound(terms, frame):
        return _unavailable("terms_frame_mismatch", frame)
    if not _bound(continuation_risk, frame):
        return _unavailable("continuation_frame_mismatch", frame)
    if not (
        set(option) == {
            "schema", "frame", "outcome", "absolute_outcome", "source",
            "native_legal_now", "recipient_accepts_now", "query_sequence",
            "evidence_sha256",
        }
        and option["schema"] == "xar.ck3.defender-dejure-exit-option.v1"
        and option["outcome"] == "surrender"
        and option["absolute_outcome"] == "attacker_victory"
        and option["source"] == "native"
        and option["native_legal_now"] is True
        and option["recipient_accepts_now"] is True
        and _integer(option["query_sequence"], positive=True)
        and _sha(option["evidence_sha256"])
    ):
        return _unavailable("option_not_current_legal_accepted_surrender", frame)
    parties = {
        frame["primary_attacker_character_id"],
        frame["primary_defender_character_id"],
    }
    if not (
        set(terms) == {
            "schema", "frame", "outcome", "material_complete",
            "runtime_target_scope_title_id", "cb_prestige_factor",
            "title_vassal_delta", "signed_resource_delta",
            "directed_truce", "conditional_resource_effects",
            "evidence_sha256",
        }
        and terms["schema"] == "xar.ck3.defender-dejure-exit-terms-complete.v1"
        and terms["outcome"] == "surrender"
        and terms["material_complete"] is True
        and _integer(terms["runtime_target_scope_title_id"], positive=True)
        and terms["runtime_target_scope_title_id"] in frame["target_title_ids"]
        and _sha(terms["evidence_sha256"])
    ):
        return _unavailable("material_terms_missing_or_unbound", frame)
    factor = terms["cb_prestige_factor"]
    if not (
        isinstance(factor, dict)
        and set(factor) == {"raw", "scale", "evidence_sha256"}
        and _integer(factor["raw"])
        and factor["raw"] >= 0
        and factor["scale"] == 100_000
        and _sha(factor["evidence_sha256"])
    ):
        return _unavailable("cb_prestige_factor_unavailable", frame)
    title = terms["title_vassal_delta"]
    if not (
        isinstance(title, dict)
        and set(title) == {"status", "operations", "evidence_sha256"}
        and title["status"] == "complete"
        and _sha(title["evidence_sha256"])
        and _operations(title["operations"], require_targets=set(frame["target_title_ids"]))
    ):
        return _unavailable("target_title_vassal_transfer_unavailable", frame)
    exit_resources = _resource_rows(terms["signed_resource_delta"], parties, bounds=False)
    if exit_resources is None:
        return _unavailable("signed_resource_delta_unavailable", frame)
    truce = terms["directed_truce"]
    if not (
        isinstance(truce, dict)
        and set(truce) == {
            "owner_character_id", "toward_character_id", "days",
            "expiry_date_raw", "evidence_sha256",
        }
        and truce["owner_character_id"] == frame["primary_attacker_character_id"]
        and truce["toward_character_id"] == frame["primary_defender_character_id"]
        and _integer(truce["days"], positive=True)
        and _integer(truce["expiry_date_raw"], positive=True)
        and truce["expiry_date_raw"] > frame["date_raw"]
        and _sha(truce["evidence_sha256"])
    ):
        return _unavailable("directed_truce_unavailable", frame)
    conditional = terms["conditional_resource_effects"]
    if not (
        isinstance(conditional, dict)
        and set(conditional) == {
            "status", "effect_tree_sha256", "covered_effect_node_ids",
            "unresolved_effect_node_ids", "evidence_sha256",
        }
        and conditional["status"] == "complete"
        and _sha(conditional["effect_tree_sha256"])
        and _sha(conditional["evidence_sha256"])
        and isinstance(conditional["covered_effect_node_ids"], list)
        and bool(conditional["covered_effect_node_ids"])
        and all(isinstance(node, str) and node for node in conditional["covered_effect_node_ids"])
        and len(conditional["covered_effect_node_ids"]) == len(set(conditional["covered_effect_node_ids"]))
        and conditional["unresolved_effect_node_ids"] == []
    ):
        return _unavailable("conditional_resource_effects_unresolved", frame)
    risk = continuation_risk
    if not (
        set(risk) == {
            "schema", "frame", "status", "horizon_days", "resource_delta_bounds",
            "title_vassal_risk", "war_score_bounds", "contact_partition",
            "evidence_sha256",
        }
        and risk["schema"] == "xar.ck3.defender-dejure-continuation-risk.v1"
        and risk["status"] == "bounded_complete"
        and _integer(risk["horizon_days"], positive=True)
        and _sha(risk["evidence_sha256"])
    ):
        return _unavailable("continuation_risk_incomplete", frame)
    risk_resources = _resource_rows(risk["resource_delta_bounds"], parties, bounds=True)
    if risk_resources is None:
        return _unavailable("continuation_resource_bounds_incomplete", frame)
    title_risk = risk["title_vassal_risk"]
    if not (
        isinstance(title_risk, dict)
        and set(title_risk) == {"status", "possible_operations", "evidence_sha256"}
        and title_risk["status"] == "bounded_complete"
        and _sha(title_risk["evidence_sha256"])
        and _operations(title_risk["possible_operations"], require_targets=None)
    ):
        return _unavailable("continuation_title_vassal_risk_incomplete", frame)
    score = risk["war_score_bounds"]
    if not (
        isinstance(score, dict)
        and set(score) == {"lower", "upper"}
        and _integer(score["lower"])
        and _integer(score["upper"])
        and -100 <= score["lower"] <= score["upper"] <= 100
    ):
        return _unavailable("continuation_score_bounds_incomplete", frame)
    contact = risk["contact_partition"]
    if not (
        isinstance(contact, dict)
        and set(contact) == {"status", "participant_army_ids", "evidence_sha256"}
        and contact["status"] == "complete"
        and _sha(contact["evidence_sha256"])
        and isinstance(contact["participant_army_ids"], list)
        and bool(contact["participant_army_ids"])
        and all(_integer(army_id, positive=True) for army_id in contact["participant_army_ids"])
        and len(contact["participant_army_ids"]) == len(set(contact["participant_army_ids"]))
    ):
        return _unavailable("continuation_contact_partition_incomplete", frame)

    resource_comparison = []
    for character_id, resource in sorted(exit_resources):
        exit_raw = exit_resources[character_id, resource]
        lower, upper = risk_resources[character_id, resource]
        relation = (
            "below_continuation_range" if exit_raw < lower else
            "above_continuation_range" if exit_raw > upper else
            "within_continuation_range"
        )
        resource_comparison.append({
            "character_id": character_id,
            "resource": resource,
            "exit_delta_raw": exit_raw,
            "continuation_lower_raw": lower,
            "continuation_upper_raw": upper,
            "scale": 100_000,
            "relation": relation,
        })
    comparison = {
        "frame": copy.deepcopy(frame),
        "outcome": "surrender",
        "horizon_days": risk["horizon_days"],
        "runtime_target_scope_title_id": terms["runtime_target_scope_title_id"],
        "cb_prestige_factor": copy.deepcopy(factor),
        "exit_title_vassal_operations": copy.deepcopy(title["operations"]),
        "continuation_possible_title_vassal_operations": copy.deepcopy(title_risk["possible_operations"]),
        "exit_directed_truce": copy.deepcopy(truce),
        "continuation_war_score_bounds": copy.deepcopy(score),
        "resource_delta_interval_relations": resource_comparison,
        "evidence_sha256": {
            "native_option": option["evidence_sha256"],
            "material_terms": terms["evidence_sha256"],
            "continuation_risk": risk["evidence_sha256"],
        },
        "aggregate_preference": None,
        "aggregate_preference_reason": "documented_risk_policy_and_utility_order_missing",
    }
    digest = _digest(comparison)
    return {
        "policy": POLICY,
        "status": "componentwise_comparable_no_policy",
        "frame": copy.deepcopy(frame),
        "comparison": comparison,
        "comparison_sha256": digest,
        "recommended_outcome": None,
        "action_literal": None,
    }


def formal_surrender_action_preconditions(
    comparison: object, policy_selection: object, exact_checkpoint_authority: object,
) -> dict[str, object]:
    """Check structure only; authority authenticity and game submission stay external."""
    result = {
        "status": "unavailable",
        "reason": None,
        "structural_prerequisites_present": False,
        "external_authority_verified": False,
        "fresh_native_revalidation_complete": False,
        "submission_enabled": False,
        "action_literal": None,
    }
    if not isinstance(comparison, dict) or comparison.get("status") != "componentwise_comparable_no_policy":
        result["reason"] = "comparison_unavailable"
        return result
    frame = comparison.get("frame")
    digest = comparison.get("comparison_sha256")
    payload = comparison.get("comparison")
    if not (
        comparison.get("policy") == POLICY
        and _frame(frame)
        and isinstance(payload, dict)
        and payload.get("frame") == frame
        and payload.get("aggregate_preference") is None
        and comparison.get("recommended_outcome") is None
        and comparison.get("action_literal") is None
        and _sha(digest)
        and _digest(payload) == digest
    ):
        result["reason"] = "comparison_binding_invalid"
        return result
    if not (
        isinstance(policy_selection, dict)
        and set(policy_selection) == {
            "schema", "frame", "comparison_sha256", "selected_outcome",
            "policy_document_sha256", "risk_contract_sha256",
        }
        and policy_selection["schema"] == "xar.ck3.formal-exit-policy-selection.v1"
        and policy_selection["frame"] == frame
        and policy_selection["comparison_sha256"] == digest
        and policy_selection["selected_outcome"] == "surrender"
        and _sha(policy_selection["policy_document_sha256"])
        and _sha(policy_selection["risk_contract_sha256"])
    ):
        result["reason"] = "documented_policy_selection_missing_or_unbound"
        return result
    if not (
        isinstance(exact_checkpoint_authority, dict)
        and set(exact_checkpoint_authority) == {
            "schema", "frame", "comparison_sha256", "checkpoint_sha256",
            "outcome", "scope", "authority_id", "consumed",
        }
        and exact_checkpoint_authority["schema"] == "xar.ck3.exact-checkpoint-exit-authority.v1"
        and exact_checkpoint_authority["frame"] == frame
        and exact_checkpoint_authority["comparison_sha256"] == digest
        and exact_checkpoint_authority["checkpoint_sha256"] == frame["checkpoint_sha256"]
        and exact_checkpoint_authority["outcome"] == "surrender"
        and exact_checkpoint_authority["scope"] == "one_exact_checkpoint"
        and isinstance(exact_checkpoint_authority["authority_id"], str)
        and bool(exact_checkpoint_authority["authority_id"])
        and exact_checkpoint_authority["consumed"] is False
    ):
        result["reason"] = "exact_checkpoint_authority_missing_or_unbound"
        return result
    result.update({
        "status": "structural_prerequisites_present_submission_disabled",
        "reason": "authority_authenticity_and_fresh_native_option_not_verified",
        "structural_prerequisites_present": True,
    })
    return result


__all__ = [
    "compare_defender_dejure_surrender_cost_to_continuation_risk",
    "formal_surrender_action_preconditions",
]
