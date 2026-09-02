"""Static execution-readiness projection for a Raiktor surrender.

The existing three-way policy may identify a *static* winner.  That is not an
authorization to mutate CK3.  This module records the remaining decision,
submit, and action-boundary postcondition gates as one deterministic result.

The current v1 six-domain aggregate intentionally lacks connection/episode/PID
binding, persisted-truce expiry, source-specific regiment attribution, and a
post-state observer bundle.  Consequently this projection cannot emit an
action literal today.  Keeping those facts in executable code prevents a
future planner from treating a recommendation, an ACK, or WarID disappearance
as a complete surrender lifecycle.
"""

from __future__ import annotations

from xar_autoplayer.bridge.raiktor_surrender_six_domain_contract import (
    normalize_raiktor_surrender_six_domain,
)
from xar_autoplayer.simulation.raiktor_continue_vs_surrender_policy import (
    canonical_policy_input_sha256,
)
from xar_autoplayer.simulation.raiktor_three_way_exit_policy import (
    POLICY_VERSION as THREE_WAY_POLICY_VERSION,
)


POLICY_VERSION = "raiktor-surrender-execution-policy-v1"

POSTCONDITION_REQUIREMENTS = (
    "old_full_generation_war_id_absent",
    "attacker_and_defender_gold_match_frozen_transfer",
    "attacker_prestige_matches_frozen_delta",
    "declared_target_claims_removed",
    "attacker_to_defender_truce_days_and_expiry_observed",
    "frozen_prisoner_release_pairs_no_longer_held",
    "favor_hook_presence_matches_frozen_will_apply",
    "source_specific_war_bound_regiments_absent",
)

_FRAME_KEYS = {
    "snapshot_id",
    "snapshot_revision",
    "native_revision",
    "date_raw",
    "connection_id",
    "episode_id",
    "ck3_pid",
    "paused",
    "war_id",
    "active_casus_belli_database_index",
    "active_casus_belli_key",
    "primary_attacker_character_id",
    "primary_defender_character_id",
    "claimant_character_id",
}


def project_raiktor_surrender_execution_readiness(
    decision_value: object,
    candidate_value: object,
    surrender_terms_value: object,
) -> dict[str, object]:
    """Project the current fail-closed surrender lifecycle.

    This function is side-effect free.  It neither accepts runtime capability
    booleans nor caller-authored thresholds: those providers do not exist yet.
    Once they do, this contract must be versioned and backed by a paused live
    artifact before any literal can be emitted.
    """

    decision = _normalize_decision(decision_value)
    frame = _candidate_frame(candidate_value)
    terms = normalize_raiktor_surrender_six_domain(
        surrender_terms_value,
        expected_war_id=frame["war_id"],
        expected_snapshot_revision=frame["snapshot_revision"],
        expected_native_revision=frame["native_revision"],
        expected_date_raw=frame["date_raw"],
        expected_attacker_character_id=frame[
            "primary_attacker_character_id"
        ],
        expected_defender_character_id=frame[
            "primary_defender_character_id"
        ],
        expected_claimant_character_id=frame["claimant_character_id"],
    )
    _require_decision_candidate_binding(decision, candidate_value)

    decision_blockers: list[str] = []
    if not (
        decision["static_recommendation_ready"] is True
        and decision["recommended_outcome"] == "surrender"
    ):
        decision_blockers.append(
            "three_way_static_surrender_recommendation_required"
        )
    if decision["production_recommendation_ready"] is not True:
        decision_blockers.append("production_recommendation_not_ready")
    if decision["full_exit_decision_ready"] is not True:
        decision_blockers.append("full_exit_decision_not_ready")

    readiness = terms["readiness"]
    missing_domains = set(terms["missing_domains"])
    terms_blockers: list[str] = []
    if readiness["action_terms_ready"] is not True:
        terms_blockers.append("six_domain_action_terms_not_ready")
    for name in (
        "gold",
        "prestige",
        "prisoner_release",
        "favor_hook",
        "truce",
        "generic_war_bound_current",
    ):
        if name in missing_domains:
            terms_blockers.append(f"{name}_not_ready")

    # The v1 aggregate's exact frame is deliberately narrower than the
    # candidate frame.  Never infer session provenance from its parent.
    terms_blockers.append("six_domain_session_provenance_not_bound")

    truce = terms["domains"]["truce"]
    if truce.get("available") is not True:
        terms_blockers.append("truce_evaluated_days_not_ready")
    else:
        truce_payload = truce["payload"]
        if truce_payload["expiry_observable"] is not True:
            terms_blockers.append("truce_expiry_not_observable")
    if readiness["source_specific_war_bound_ready"] is not True:
        terms_blockers.append("source_specific_war_bound_not_ready")
    if readiness["pre_soldiers_ready"] is not True:
        terms_blockers.append("pre_soldiers_not_ready")
    if readiness["proven_soldier_loss_ready"] is not True:
        terms_blockers.append("proven_soldier_loss_not_ready")

    action_blockers = [
        *decision_blockers,
        *terms_blockers,
        "typed_surrender_submit_not_enabled",
        "pending_submission_and_cooldown_not_evaluated",
        "action_boundary_observers_not_ready",
    ]
    postcondition_blockers = [
        "surrender_action_not_submittable",
        "truce_expiry_post_state_observer_not_ready",
        "source_specific_war_bound_cleanup_observer_not_ready",
        "six_domain_post_state_bundle_not_ready",
    ]

    return {
        "policy_version": POLICY_VERSION,
        "status": "blocked",
        "frame": frame,
        "decision": {
            "policy_version": decision["policy_version"],
            "static_recommendation_ready": decision[
                "static_recommendation_ready"
            ],
            "recommended_outcome": decision["recommended_outcome"],
            "production_recommendation_ready": decision[
                "production_recommendation_ready"
            ],
            "full_exit_decision_ready": decision[
                "full_exit_decision_ready"
            ],
            "ready": not decision_blockers,
            "blockers": decision_blockers,
        },
        "terms": {
            "status": terms["status"],
            "missing_domains": list(terms["missing_domains"]),
            "action_terms_ready": readiness["action_terms_ready"],
            "session_provenance_ready": False,
            "truce_evaluated_days_ready": (
                truce.get("available") is True
            ),
            "truce_expiry_ready": False,
            "source_specific_war_bound_ready": readiness[
                "source_specific_war_bound_ready"
            ],
            "pre_soldiers_ready": readiness["pre_soldiers_ready"],
            "proven_soldier_loss_ready": readiness[
                "proven_soldier_loss_ready"
            ],
            "ready": not terms_blockers,
            "blockers": terms_blockers,
        },
        "action": {
            "ready": False,
            "literal": None,
            "automatic_surrender_ready": False,
            "submit_capability_advertised": False,
            "pending_and_cooldown_clear": False,
            "blockers": action_blockers,
        },
        "postcondition": {
            "ready": False,
            "verified": False,
            "ack_is_postcondition": False,
            "war_id_absence_is_full_postcondition": False,
            "requirements": list(POSTCONDITION_REQUIREMENTS),
            "blockers": postcondition_blockers,
        },
        "next_live_dependencies": [
            "publish_and_live-verify_truce_evaluated_days_and_persisted_expiry",
            "publish_full six-domain connection_episode_pid_binding",
            "publish_source-specific war-bound pre/action-bound/post cleanup",
            "provide campaign owner-budget and white-peace certificates",
            "implement mutually-exclusive typed surrender submit with pending cooldown",
            "observe all eight postconditions in one action-boundary lifecycle",
        ],
        "native_ai_equivalent": False,
        "semantic_optimal": False,
    }


def _normalize_decision(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("three-way decision must be an object")
    required = {
        "policy_version",
        "static_recommendation_ready",
        "recommended_outcome",
        "production_recommendation_ready",
        "full_exit_decision_ready",
        "pairwise",
    }
    if not required <= set(value):
        raise ValueError("three-way decision is missing execution fields")
    if value["policy_version"] != THREE_WAY_POLICY_VERSION:
        raise ValueError("three-way decision policy version drifted")
    recommendation = value["recommended_outcome"]
    if recommendation not in {None, "continue", "white_peace", "surrender"}:
        raise ValueError("three-way recommendation is invalid")
    return {
        "policy_version": value["policy_version"],
        "static_recommendation_ready": _strict_bool(
            value["static_recommendation_ready"],
            "static_recommendation_ready",
        ),
        "recommended_outcome": recommendation,
        "production_recommendation_ready": _strict_bool(
            value["production_recommendation_ready"],
            "production_recommendation_ready",
        ),
        "full_exit_decision_ready": _strict_bool(
            value["full_exit_decision_ready"],
            "full_exit_decision_ready",
        ),
        "pairwise": value["pairwise"],
    }


def _require_decision_candidate_binding(
    decision: dict[str, object], candidate: object
) -> None:
    pairwise = decision["pairwise"]
    if pairwise is None:
        return
    if not isinstance(pairwise, dict):
        raise ValueError("three-way pairwise result is malformed")
    expected = canonical_policy_input_sha256(candidate)
    if pairwise.get("candidate_sha256") != expected:
        raise ValueError("three-way decision belongs to another candidate")


def _candidate_frame(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or "frame" not in value:
        raise ValueError("candidate frame is unavailable")
    item = value["frame"]
    if not isinstance(item, dict) or set(item) != _FRAME_KEYS:
        raise ValueError("candidate frame schema drifted")
    frame = dict(item)
    for key in ("snapshot_id", "connection_id", "episode_id"):
        if not isinstance(frame[key], str) or not frame[key].strip():
            raise ValueError(f"candidate frame {key} is unavailable")
    for key in (
        "snapshot_revision",
        "native_revision",
        "ck3_pid",
        "war_id",
        "primary_attacker_character_id",
        "primary_defender_character_id",
        "claimant_character_id",
    ):
        _positive_int(frame[key], f"candidate frame {key}")
    _int(frame["date_raw"], "candidate frame date_raw")
    _nonnegative_int(
        frame["active_casus_belli_database_index"],
        "candidate frame active_casus_belli_database_index",
    )
    if (
        frame["paused"] is not True
        or frame["active_casus_belli_key"] != "raiktor_claim_cb"
        or frame["primary_attacker_character_id"]
        == frame["primary_defender_character_id"]
    ):
        raise ValueError("candidate is not an exact paused Raiktor frame")
    return frame


def _strict_bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean")
    return value


def _int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    return value


def _positive_int(value: object, name: str) -> int:
    result = _int(value, name)
    if result <= 0:
        raise ValueError(f"{name} must be positive")
    return result


def _nonnegative_int(value: object, name: str) -> int:
    result = _int(value, name)
    if result < 0:
        raise ValueError(f"{name} must be nonnegative")
    return result
