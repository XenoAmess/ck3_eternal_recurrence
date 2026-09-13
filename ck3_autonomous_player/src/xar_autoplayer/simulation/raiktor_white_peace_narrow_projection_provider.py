"""Project Raiktor white-peace terms from existing safe public queries.

The broad loaded-effect preview remains disabled after reproducible native
crashes.  This provider instead combines the already supported termination
option and narrow Raiktor terms queries on one paused session.  Values copied
from the surrender query are used only where the exact-build scripts execute
the same helper or conditional for white peace; every other dynamic effect is
kept explicit as unobserved.
"""

from __future__ import annotations

import copy

from xar_autoplayer.bridge.raiktor_surrender_session_binding_contract import (
    normalize_raiktor_surrender_aggregate_session_binding,
)
from xar_autoplayer.bridge.war_contract import (
    normalize_war_termination_options,
    normalize_war_termination_terms,
)
from xar_autoplayer.simulation.raiktor_continue_vs_surrender_policy import (
    canonical_policy_input_sha256,
)
from xar_autoplayer.simulation.raiktor_white_peace_comparison_contracts import (
    OBSERVATION_COMPLETENESS_KEYS,
    OBSERVATION_CONTRACT,
    normalize_white_peace_terms_observation,
)


PROVIDER_SCHEMA = "xar.ck3.raiktor_white_peace_narrow_projection_provider.v1"
PROVIDER_ID = "raiktor-white-peace-narrow-projection-v1"
GAME_VERSION = "1.19.0.6"
EXECUTABLE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
EVENT_WAR_SCRIPT_SHA256 = (
    "BD202AE41EBA3A0E1E7E4277D09ED1E8D8C7E66B378308BB417D974331F9C707"
)
WAR_EFFECTS_SCRIPT_SHA256 = (
    "A936E09F448EF715580A918165EAB89A9368AD2D3014E425C998CD9D4F0E8D7D"
)
_RAIKTOR_SLICE = "raiktor_claim_cb_attacker_defeat_disposition"
_UNOBSERVED_DYNAMIC_EFFECTS = [
    "attacker_trait_stress_delta",
    "defender_trait_stress_delta",
    "defender_accolade_glory_delta",
    "participant_ally_fame_deltas",
    "glory_hound_and_antagonistic_clan_opinion_rows",
    "attacker_accolade_white_peace_prestige_delta",
    "laamp_actual_settlement_outside_cb_effect",
]
_SURRENDER_NONVALUED_EFFECTS = {
    "targeting_faction_discontent_delta",
    "glory_hound_vassal_opinion_rows",
    "antagonistic_clan_vassal_opinion_rows",
    "existing_house_feud_score_delta",
    "attacker_mandala_piety_experience_delta",
    "defender_mandala_serenity",
    "defender_accolade_glory",
    "laamp_actual_settlement_outside_cb_effect",
    "war_bound_army_losses",
}


class WhitePeaceNarrowProjectionError(ValueError):
    """The supplied public observations are malformed or cross-session."""


def provide_raiktor_white_peace_narrow_projection(
    snapshot_value: object | None,
    options_query_value: object | None,
    terms_query_value: object | None,
    *,
    production_live: bool = False,
) -> dict[str, object]:
    """Return one terms observation or typed missing-evidence blockers."""

    if not isinstance(production_live, bool):
        raise WhitePeaceNarrowProjectionError(
            "production_live must be a boolean"
        )
    missing = [
        reason
        for value, reason in (
            (snapshot_value, "paused_snapshot_unavailable"),
            (options_query_value, "termination_options_query_unavailable"),
            (terms_query_value, "raiktor_terms_query_unavailable"),
        )
        if value is None
    ]
    if missing:
        return _result(blockers=missing)
    if not isinstance(snapshot_value, dict):
        raise WhitePeaceNarrowProjectionError("snapshot must be an object")
    if not isinstance(options_query_value, dict):
        raise WhitePeaceNarrowProjectionError(
            "termination options query must be an object"
        )
    if not isinstance(terms_query_value, dict):
        raise WhitePeaceNarrowProjectionError(
            "Raiktor terms query must be an object"
        )

    snapshot = snapshot_value
    raw_options = options_query_value.get("war_termination_options")
    if not isinstance(raw_options, dict):
        raise WhitePeaceNarrowProjectionError(
            "termination options query lacks its result"
        )
    war_id = _positive_int(raw_options.get("war_id"), "war_id")
    snapshot_binding = _snapshot_binding(snapshot, war_id=war_id)
    options = _normalize_options_query(options_query_value, war_id=war_id)
    terms = _normalize_terms_query(terms_query_value, war_id=war_id)
    session_value = terms_query_value.get(
        "raiktor_surrender_aggregate_session"
    )
    if not isinstance(session_value, dict) or session_value.get("status") != (
        "available"
    ):
        failure = (
            session_value.get("failure")
            if isinstance(session_value, dict)
            else None
        )
        code = (
            failure.get("code")
            if isinstance(failure, dict)
            else "unavailable"
        )
        return _result(
            blockers=[f"surrender_aggregate_session_{code}"],
            source_evidence=_source_evidence(terms),
        )

    try:
        session = normalize_raiktor_surrender_aggregate_session_binding(
            session_value,
            expected_snapshot_id=snapshot_binding["snapshot_id"],
            expected_snapshot_revision=snapshot_binding[
                "snapshot_revision"
            ],
            expected_native_revision=snapshot_binding["native_revision"],
            expected_date_raw=snapshot_binding["date_raw"],
            expected_connection_generation=snapshot_binding[
                "connection_generation"
            ],
            expected_episode_run_id=snapshot_binding["episode_run_id"],
            expected_episode_character_id=snapshot_binding[
                "attacker_character_id"
            ],
            expected_process_id=snapshot_binding["process_id"],
            expected_war_id=war_id,
        )
    except ValueError as error:
        raise WhitePeaceNarrowProjectionError(str(error)) from error

    binding = session["binding"]
    aggregate = session["aggregate"]
    aggregate_frame = aggregate["frame"]
    _require_query_binding(
        options_query_value,
        binding=binding,
        episode_field="queried_episode_run_id",
        name="termination options query",
    )
    _require_query_binding(
        terms_query_value,
        binding=binding,
        episode_field="episode_run_id",
        name="Raiktor terms query",
    )
    _require_cross_input_identity(options, terms, aggregate_frame)

    blockers = _readiness_blockers(options, terms)
    if blockers:
        return _result(
            blockers=blockers,
            source_evidence=_source_evidence(terms),
        )

    white_option = options["options"]["white_peace"]
    response = white_option["recipient_response"]
    prestige_factor = terms["attacker_fame"]["cb_prestige_factor"]
    prestige_delta_raw = _checked_multiply(
        prestige_factor["raw"], -5, "white-peace prestige delta"
    )
    release_pairs = [
        {
            "jailer_character_id": row["jailer_character_id"],
            "prisoner_character_id": row["prisoner_character_id"],
        }
        for row in terms["prisoner_release"]["release_pairs"]
    ]
    frame = {
        "snapshot_id": binding["snapshot_id"],
        "snapshot_revision": binding["snapshot_revision"],
        "native_revision": binding["native_revision"],
        "date_raw": binding["date_raw"],
        "connection_id": (
            f"connection-generation:{binding['connection_generation']}"
        ),
        "episode_id": binding["episode_run_id"],
        "ck3_pid": binding["process_id"],
        "paused": True,
        "war_id": binding["war_id"],
        "active_casus_belli_database_index": aggregate_frame[
            "active_casus_belli_database_index"
        ],
        "active_casus_belli_key": "raiktor_claim_cb",
        "primary_attacker_character_id": aggregate_frame[
            "primary_attacker_character_id"
        ],
        "primary_defender_character_id": aggregate_frame[
            "primary_defender_character_id"
        ],
        "claimant_character_id": aggregate_frame[
            "claimant_character_id"
        ],
    }
    option = {
        "context_constructed": white_option["context_constructed"],
        "native_validator": white_option["native_validator_passed"],
        "available": white_option["available"],
        "auto_accept": white_option["auto_accept"],
        "recipient_response": {
            "decision_status_raw": response["decision_status_raw"],
            "would_accept_now": response["would_accept_now"],
        },
    }
    white_terms = {
        "declared_target_title_ids": copy.deepcopy(
            terms["target_title_ids"]
        ),
        "retained_target_title_ids": copy.deepcopy(
            terms["target_title_ids"]
        ),
        "claim_disposition": "retain_and_strengthen_weak",
        "title_holder_change_count": 0,
        "primary_gold_transfer_raw": 0,
        "attacker_prestige_delta_raw": prestige_delta_raw,
        "truce_evaluated_days": terms["truce"]["evaluated_days"],
        "prisoner_release_pairs": release_pairs,
        "favor_hook_will_apply": terms["conditional_favor_hook"][
            "will_apply"
        ],
        "hostage_variant": "none",
    }
    aggregate_sha = canonical_policy_input_sha256(aggregate)
    candidate_sha = canonical_policy_input_sha256(
        {"frame": frame, "white_peace_option": option}
    )
    evidence = _source_evidence(terms)
    source_bundle_sha = canonical_policy_input_sha256(
        {
            "frame": frame,
            "options_query": options,
            "terms_query": terms,
            "surrender_aggregate_sha256": aggregate_sha,
            "source_evidence": evidence,
        }
    )
    observation = normalize_white_peace_terms_observation(
        {
            "schema_version": 1,
            "contract": OBSERVATION_CONTRACT,
            "status": "complete",
            "frame": frame,
            "evaluated_candidate_sha256": candidate_sha,
            "evaluated_surrender_terms_sha256": aggregate_sha,
            "producer": {
                "producer_id": PROVIDER_ID,
                "producer_version": "v1",
                "source_artifact_sha256": source_bundle_sha,
                "production_live": production_live,
            },
            "completeness": {
                key: True for key in sorted(OBSERVATION_COMPLETENESS_KEYS)
            },
            "option": option,
            "terms": white_terms,
            "same_frame_stable": True,
        }
    )
    return _result(
        blockers=[],
        observation=observation,
        source_evidence=evidence,
        unobserved_dynamic_effects=_UNOBSERVED_DYNAMIC_EFFECTS,
        surrender_unobserved_dynamic_effects=(
            _surrender_unobserved_dynamic_effects(terms)
        ),
    )


def _snapshot_binding(
    snapshot: dict[str, object], *, war_id: int
) -> dict[str, object]:
    diagnostics = snapshot.get("diagnostics")
    played = snapshot.get("played_character")
    wars = snapshot.get("active_wars")
    if not isinstance(diagnostics, dict) or not isinstance(played, dict):
        raise WhitePeaceNarrowProjectionError(
            "snapshot lacks diagnostics or played character"
        )
    if not isinstance(wars, list):
        raise WhitePeaceNarrowProjectionError("snapshot lacks active wars")
    attacker_id = _positive_int(
        snapshot.get("episode_character_id"), "episode_character_id"
    )
    if played.get("character_id") != attacker_id:
        raise WhitePeaceNarrowProjectionError(
            "played character is not the episode character"
        )
    candidates = [
        war
        for war in wars
        if isinstance(war, dict)
        and war.get("war_id") == war_id
        and war.get("player_side") == "attacker"
        and war.get("player_is_primary_war_leader") is True
    ]
    if len(candidates) != 1:
        raise WhitePeaceNarrowProjectionError(
            "snapshot must contain the selected primary-attacker war exactly once"
        )
    if snapshot.get("paused") is not True:
        raise WhitePeaceNarrowProjectionError("snapshot must be paused")
    return {
        "snapshot_id": _nonempty_string(
            snapshot.get("snapshot_id"), "snapshot_id"
        ),
        "snapshot_revision": _positive_int(
            snapshot.get("revision"), "revision"
        ),
        "native_revision": _positive_int(
            snapshot.get("native_revision"), "native_revision"
        ),
        "date_raw": _integer(snapshot.get("date_raw"), "date_raw"),
        "connection_generation": _positive_int(
            diagnostics.get("connection_generation"),
            "connection_generation",
        ),
        "episode_run_id": _nonempty_string(
            snapshot.get("episode_run_id"), "episode_run_id"
        ),
        "attacker_character_id": attacker_id,
        "process_id": _positive_int(
            diagnostics.get("bridge_pid"), "bridge_pid"
        ),
        "war_id": war_id,
    }


def _normalize_options_query(
    query: dict[str, object], *, war_id: int
) -> dict[str, object]:
    if query.get("accepted") is not True or query.get("status") != "available":
        raise WhitePeaceNarrowProjectionError(
            "termination options query is not available"
        )
    try:
        return normalize_war_termination_options(
            query.get("war_termination_options"), expected_war_id=war_id
        )
    except ValueError as error:
        raise WhitePeaceNarrowProjectionError(str(error)) from error


def _normalize_terms_query(
    query: dict[str, object], *, war_id: int
) -> dict[str, object]:
    if query.get("accepted") is not True or query.get("status") != "available":
        raise WhitePeaceNarrowProjectionError(
            "Raiktor terms query is not available"
        )
    try:
        terms = normalize_war_termination_terms(
            query.get("war_termination_terms"), expected_war_id=war_id
        )
    except ValueError as error:
        raise WhitePeaceNarrowProjectionError(str(error)) from error
    if terms.get("supported_slice") != _RAIKTOR_SLICE:
        raise WhitePeaceNarrowProjectionError(
            "terms query is not the Raiktor narrow slice"
        )
    return terms


def _require_query_binding(
    query: dict[str, object],
    *,
    binding: dict[str, object],
    episode_field: str,
    name: str,
) -> None:
    expected = {
        "queried_snapshot_id": binding["snapshot_id"],
        "queried_revision": binding["snapshot_revision"],
        "queried_native_revision": binding["native_revision"],
        "queried_connection_generation": binding["connection_generation"],
        episode_field: binding["episode_run_id"],
    }
    drift = [key for key, value in expected.items() if query.get(key) != value]
    if drift:
        raise WhitePeaceNarrowProjectionError(
            f"{name} crossed its paused session: {', '.join(drift)}"
        )


def _require_cross_input_identity(
    options: dict[str, object],
    terms: dict[str, object],
    aggregate_frame: dict[str, object],
) -> None:
    option_cb = options.get("active_casus_belli_identity")
    terms_cb = terms.get("casus_belli")
    if not isinstance(option_cb, dict) or not isinstance(terms_cb, dict):
        raise WhitePeaceNarrowProjectionError("casus belli identity is missing")
    expected = {
        "war_id": aggregate_frame.get("war_id"),
        "database_index": aggregate_frame.get(
            "active_casus_belli_database_index"
        ),
        "canonical_key": "raiktor_claim_cb",
    }
    observed = (
        {
            "war_id": options.get("war_id"),
            "database_index": option_cb.get("database_index"),
            "canonical_key": option_cb.get("canonical_key"),
        },
        {
            "war_id": terms.get("war_id"),
            "database_index": terms_cb.get("database_index"),
            "canonical_key": terms_cb.get("canonical_key"),
        },
    )
    if any(item != expected for item in observed):
        raise WhitePeaceNarrowProjectionError(
            "options, terms and aggregate identify different wars"
        )
    if options.get("player_side") != "attacker" or options.get(
        "player_is_primary_war_leader"
    ) is not True:
        raise WhitePeaceNarrowProjectionError(
            "Raiktor projection requires the primary attacker"
        )
    if terms.get("claimant_character_id") != aggregate_frame.get(
        "claimant_character_id"
    ):
        raise WhitePeaceNarrowProjectionError("claimant identity drifted")


def _readiness_blockers(
    options: dict[str, object], terms: dict[str, object]
) -> list[str]:
    blockers: list[str] = []
    white = options["options"]["white_peace"]
    response = white["recipient_response"]
    if options.get("cb_allows_white_peace") is not True:
        blockers.append("casus_belli_forbids_white_peace")
    if not (
        white.get("context_constructed") is True
        and white.get("native_validator_passed") is True
        and white.get("available") is True
    ):
        blockers.append("white_peace_native_option_unavailable")
    if response.get("status") != "available":
        blockers.append("white_peace_final_recipient_response_unavailable")
    fame = terms.get("attacker_fame")
    if not isinstance(fame, dict) or fame.get("actual_delta_observable") is not True:
        blockers.append("white_peace_prestige_factor_unavailable")
    truce = terms.get("truce")
    if not isinstance(truce, dict) or truce.get(
        "evaluated_days_observable"
    ) is not True:
        blockers.append("white_peace_truce_duration_unavailable")
    prisoners = terms.get("prisoner_release")
    if not isinstance(prisoners, dict) or prisoners.get(
        "actual_pairs_observable"
    ) is not True:
        blockers.append("white_peace_prisoner_release_scan_unavailable")
    favor = terms.get("conditional_favor_hook")
    if not isinstance(favor, dict) or favor.get(
        "actual_applies_observable"
    ) is not True:
        blockers.append("white_peace_favor_condition_unavailable")
    return blockers


def _source_evidence(terms: dict[str, object]) -> dict[str, object]:
    provenance = terms.get("provenance")
    if not isinstance(provenance, dict):
        raise WhitePeaceNarrowProjectionError(
            "Raiktor terms lack exact-build provenance"
        )
    expected = {
        "game_version": GAME_VERSION,
        "executable_sha256": EXECUTABLE_SHA256,
        "event_war_script_sha256": EVENT_WAR_SCRIPT_SHA256,
        "war_effects_script_sha256": WAR_EFFECTS_SCRIPT_SHA256,
    }
    if any(provenance.get(key) != value for key, value in expected.items()):
        raise WhitePeaceNarrowProjectionError(
            "Raiktor terms exact-build provenance drifted"
        )
    return {
        **expected,
        "projection_rules": {
            "claims": "raiktor_claim_cb.on_white_peace retain; strengthen weak",
            "gold": "raiktor_claim_cb.on_white_peace has no primary transfer",
            "prestige": "setup_claim_cb(victory=no) factor multiplied by -5",
            "prisoners": "shared show_pow_release_message_effect",
            "favor": "identical attacker-to-claimant conditional",
            "truce": "shared standard_truce_duration_days expression",
            "hostages": "raiktor_claim_cb allow_hostages=no",
        },
        "copied_same_frame_domains": [
            "cb_prestige_factor",
            "prisoner_release_pairs",
            "conditional_favor_hook_application",
            "standard_truce_duration_days",
        ],
    }


def _surrender_unobserved_dynamic_effects(
    terms: dict[str, object]
) -> list[str]:
    values = terms.get("unobserved_dynamic_effects")
    if not isinstance(values, list):
        raise WhitePeaceNarrowProjectionError(
            "Raiktor terms lack unobserved dynamic effects"
        )
    result = [
        value for value in values if value in _SURRENDER_NONVALUED_EFFECTS
    ]
    if set(result) != _SURRENDER_NONVALUED_EFFECTS:
        raise WhitePeaceNarrowProjectionError(
            "Raiktor surrender uncertainty set drifted"
        )
    return result


def _result(
    *,
    blockers: list[str],
    observation: dict[str, object] | None = None,
    source_evidence: dict[str, object] | None = None,
    unobserved_dynamic_effects: list[str] | None = None,
    surrender_unobserved_dynamic_effects: list[str] | None = None,
) -> dict[str, object]:
    return {
        "schema": PROVIDER_SCHEMA,
        "provider": PROVIDER_ID,
        "status": "available" if observation is not None else "evidence_required",
        "observation_ready": observation is not None,
        "production_live": bool(
            observation is not None
            and observation["producer"]["production_live"] is True
        ),
        "white_peace_observation": observation,
        "source_evidence": source_evidence,
        "unobserved_dynamic_effects": list(
            unobserved_dynamic_effects or _UNOBSERVED_DYNAMIC_EFFECTS
        ),
        "surrender_unobserved_dynamic_effects": list(
            surrender_unobserved_dynamic_effects or []
        ),
        "blockers": blockers,
        "boundaries": [
            "read_only_python_projection_over_existing_safe_queries",
            "raiktor_claim_cb_only",
            "broad_loaded_effect_preview_remains_disabled",
            "copied_values_require_exact_shared_script_expressions",
            "unobserved_dynamic_effects_are_not_zero",
            "provider_does_not_authorize_or_submit_an_action",
        ],
    }


def _checked_multiply(value: object, factor: int, name: str) -> int:
    result = _integer(value, name) * factor
    if not -(2**63) <= result <= 2**63 - 1:
        raise WhitePeaceNarrowProjectionError(f"{name} overflowed int64")
    return result


def _integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise WhitePeaceNarrowProjectionError(f"{name} must be an integer")
    return value


def _positive_int(value: object, name: str) -> int:
    result = _integer(value, name)
    if result <= 0:
        raise WhitePeaceNarrowProjectionError(f"{name} must be positive")
    return result


def _nonempty_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise WhitePeaceNarrowProjectionError(
            f"{name} must be a nonempty string"
        )
    return value


__all__ = [
    "PROVIDER_ID",
    "PROVIDER_SCHEMA",
    "WhitePeaceNarrowProjectionError",
    "provide_raiktor_white_peace_narrow_projection",
]
