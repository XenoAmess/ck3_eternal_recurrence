"""Bounded private first-heir marriage consumer; no public capability claim."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from .environment import write_json_atomic
from .bridge.declaration_contract import is_native_declaration_step
from .bridge.domain_construction_private_transport_v1 import _identity as bridge_process_identity
from .bridge.observed_heir_marriage_private_action_v1 import (
    ALLIANCE_RESULT_STEP, RESULT_STEP, SCHEMA, SUBMIT_STEP,
)
from .bridge.marriage_candidate_alliance_private_transport import (
    SCHEMA as CANDIDATE_PROJECTION_SCHEMA,
)


_LEDGER = "first-heir-marriage-formal-v1.json"
_MAX_BETROTHAL_AGE_GAP_RAW = 2
_SELECTED_VALUE_FIELDS = (
    "played_house_id", "played_dynasty_id", "heir_house_id",
    "heir_dynasty_id", "candidate_house_id", "candidate_dynasty_id",
    "heir_sex_selector_raw", "candidate_sex_selector_raw",
    "matrilineal_option_selected", "effective_matrilineal_if_accepted",
    "predicted_outcome_if_accepted", "heir_is_adult", "candidate_is_adult",
    "heir_adult_measure_raw", "candidate_adult_measure_raw",
    "heir_adult_threshold_raw", "candidate_adult_threshold_raw",
    "grand_wedding_option_selected",
)


def _positive(value: object) -> bool:
    return type(value) is int and value > 0


def _current_first_heir_relation(
    driver: object, snapshot: Mapping[str, object],
) -> dict[str, object] | None:
    """Bind the opted-in current heir read to this formal planning frame."""
    if getattr(driver, "allow_private_current_first_heir_relationship_query", False) is not True:
        return None
    revision = snapshot.get("native_revision")
    if not _positive(revision):
        raise ValueError("current first-heir relation lacks a native revision")
    result = driver.query_current_first_heir_relationship_private_v1(
        expected_native_revision=revision)
    if (not isinstance(result, dict)
            or result.get("schema") != "xar.ck3.current-first-heir-relationship.v1"
            or result.get("status") not in {"available", "unavailable"}
            or result.get("native_revision") != revision
            or result.get("read_only") is not True
            or result.get("advertised") is not False):
        raise ValueError("current first-heir relation crossed the planning frame")
    if result["status"] == "available":
        heir = result.get("heir_character_id")
        spouses = result.get("spouse_character_ids")
        if (not _positive(heir)
                or result.get("bilateral_verified") is not True
                or not isinstance(spouses, list)
                or any(not _positive(value) for value in spouses)
                or any(value is not None and not _positive(value) for value in (
                    result.get("betrothed_character_id"),
                    result.get("primary_spouse_character_id")))):
            raise ValueError("current first-heir relation is incomplete")
    return dict(result)


def _relation_has_partner(relation: Mapping[str, object]) -> bool:
    return (relation.get("betrothed_character_id") is not None
            or relation.get("primary_spouse_character_id") is not None
            or bool(relation.get("spouse_character_ids")))


def _resolved_relation_matches(resolved: Mapping[str, object],
                               relation: Mapping[str, object]) -> bool:
    if resolved.get("heir_character_id") != relation.get("heir_character_id"):
        return False
    candidate = resolved.get("candidate_character_id")
    if not _positive(candidate):
        return False
    if resolved.get("status") == "betrothal":
        return relation.get("betrothed_character_id") == candidate
    if resolved.get("status") == "marriage":
        return (relation.get("primary_spouse_character_id") == candidate
                or candidate in relation.get("spouse_character_ids", []))
    return False


def _rejected_candidates(resolved: Mapping[str, object]) -> frozenset[int]:
    """Carry native-confirmed failures without retrying the same pair."""
    values = resolved.get("rejected_candidate_ids")
    if values is None:
        values = [resolved.get("candidate_character_id")]
    if (not isinstance(values, list) or not values
            or any(not _positive(value) for value in values)
            or len(set(values)) != len(values)):
        raise ValueError("resolved marriage has invalid rejected candidates")
    return frozenset(values)


def _plan_existing_resolution(
    driver: object, planned: dict[str, object], plan: dict[str, object],
    resolved: dict[str, object],
) -> dict[str, object]:
    pid, creation = bridge_process_identity(driver)
    if (pid, creation) != (resolved.get("post_bridge_pid"),
                           resolved.get("post_bridge_creation_date")):
        if resolved.get("status") not in {"marriage", "betrothal"}:
            return {**planned, "plan": {**plan, "selected_step": None,
                "phase": "first_heir_marriage_cold_resolution_unknown",
                "reason": "prior refusal/invalidated journal is not in the cold PID"}}
        source_pending = resolved.get("source_pending")
        if not isinstance(source_pending, dict):
            raise ValueError("resolved marriage lacks cold source pair")
        return {**planned, "plan": {**plan,
            "phase": "first_heir_marriage_cold_material_recheck",
            "selected_step": RESULT_STEP,
            "family_marriage_pending": dict(source_pending),
            "family_marriage_cold_recovery": True,
            "family_marriage_prior_resolution": dict(resolved),
            "reason": "re-read bilateral relation after restoring a prior checkpoint"}}
    source_pending = resolved.get("source_pending")
    recipient = (source_pending.get("recipient_character_id")
                 if isinstance(source_pending, dict) else None)
    alliance = resolved.get("alliance_result")
    if (resolved.get("status") in {"marriage", "betrothal"}
            and _positive(recipient)
            and (not isinstance(alliance, dict)
                 or (alliance.get("bridge_pid"),
                     alliance.get("bridge_creation_date")) != (pid, creation))):
        return {**planned, "plan": {**plan,
            "phase": "first_heir_marriage_actual_alliance_read",
            "selected_step": ALLIANCE_RESULT_STEP,
            "family_marriage_resolved": dict(resolved),
            "family_marriage_status": "actual_alliance_result_pending",
            "reason": "read current player-recipient alliance after material heir relation"}}
    return {**planned, "plan": {**plan,
        "family_marriage_result_consumed": resolved,
        "family_marriage_alliance_status": (
            "recipient_unbound" if resolved.get("material_result") is True
            and not _positive(recipient) else
            alliance.get("status") if isinstance(alliance, dict) else None)}}


def read_family_marriage_ledger(state_dir: Path) -> dict[str, object]:
    path = state_dir / _LEDGER
    if not path.exists():
        return {"schema": "xar.ck3.first-heir-marriage-formal.v1",
                "pending": None, "resolved": None}
    record = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(record, dict)
            or record.get("schema") != "xar.ck3.first-heir-marriage-formal.v1"
            or any(key not in record for key in ("pending", "resolved"))
            or any(record[key] is not None and not isinstance(record[key], dict)
                   for key in ("pending", "resolved"))):
        raise ValueError("first-heir marriage ledger is malformed")
    return record


def _write(state_dir: Path, ledger: Mapping[str, object]) -> None:
    write_json_atomic(state_dir / _LEDGER, dict(ledger))


def _candidate_rejection_reasons(source: Mapping[str, object] | None,
                                 row: Mapping[str, object], *,
                                 rejected_candidate_ids: frozenset[int] = frozenset()) -> list[str]:
    """Use the same narrow value gates for selection and private diagnostics."""
    candidate_id = row.get("candidate_character_id")
    if not _positive(candidate_id):
        return ["invalid_candidate_identity"]
    if not isinstance(source, dict):
        return ["not_in_final_legal_rows"]
    reasons = []
    if candidate_id in rejected_candidate_ids:
        reasons.append("previously_refused_or_invalidated")
    if row.get("status") != "available":
        reasons.append("projection_unavailable")
    if row.get("actor_character_id") != source.get("played_character_id"):
        reasons.append("actor_identity_mismatch")
    if row.get("heir_character_id") != source.get("subject_character_id"):
        reasons.append("heir_identity_mismatch")
    if row.get("recipient_character_id") != source.get("recipient_matchmaker_character_id"):
        reasons.append("recipient_identity_mismatch")
    if (source.get("candidate_dynasty_id") is not None
            and row.get("candidate_dynasty_id") != source["candidate_dynasty_id"]):
        reasons.append("candidate_dynasty_changed_since_ranking")
    if (source.get("candidate_adult_measure_raw") is not None
            and row.get("candidate_adult_measure_raw") !=
            source["candidate_adult_measure_raw"]):
        reasons.append("candidate_age_changed_since_ranking")
    if (source.get("heir_adult_measure_raw") is not None
            and row.get("heir_adult_measure_raw") !=
            source["heir_adult_measure_raw"]):
        reasons.append("heir_age_changed_since_ranking")
    outcome = row.get("predicted_outcome_if_accepted")
    if outcome not in {"marriage", "betrothal"}:
        reasons.append("outcome_unavailable")
    if row.get("heir_betrothed_character_id") is not None:
        reasons.append("heir_already_betrothed")
    if row.get("heir_spouse_character_ids") != []:
        reasons.append("heir_spouse_list_not_empty")
    if row.get("heir_primary_spouse_character_id") is not None:
        reasons.append("heir_primary_spouse_present")
    played_dynasty = row.get("played_dynasty_id")
    if type(played_dynasty) is not int or played_dynasty <= 0:
        reasons.append("played_dynasty_unavailable")
    if played_dynasty != row.get("heir_dynasty_id"):
        reasons.append("heir_dynasty_not_played_dynasty")
    if row.get("played_house_id") != row.get("heir_house_id"):
        reasons.append("heir_house_not_played_house")
    heir_selector = row.get("heir_sex_selector_raw")
    candidate_selector = row.get("candidate_sex_selector_raw")
    if heir_selector not in (0, 1):
        reasons.append("heir_selector_unavailable")
    if candidate_selector not in (0, 1):
        reasons.append("candidate_selector_unavailable")
    if heir_selector in (0, 1) and candidate_selector in (0, 1):
        if candidate_selector == heir_selector:
            reasons.append("same_selector_pair")
        if row.get("effective_matrilineal_if_accepted") is not bool(heir_selector):
            reasons.append("lineality_not_heir_aligned")
    if outcome == "betrothal":
        if (any(type(source.get(key)) is not int for key in (
                "heir_adult_measure_raw", "candidate_adult_measure_raw",
                "played_dynasty_id", "heir_dynasty_id",
                "candidate_dynasty_id"))
                or source.get("realm_backed_actor_recipient") is not True):
            reasons.append("betrothal_ranking_inputs_unavailable")
        # Native compares these exact signed measures with runtime thresholds.
        # A close age gap bounds the match, even when the heir is much younger
        # than the threshold. Raw measures are not a fertility estimate.
        heir_measure = row.get("heir_adult_measure_raw")
        candidate_measure = row.get("candidate_adult_measure_raw")
        heir_threshold = row.get("heir_adult_threshold_raw")
        candidate_threshold = row.get("candidate_adult_threshold_raw")
        if (row.get("grand_wedding_option_selected") is not False
                or row.get("heir_is_adult") not in (True, False)
                or row.get("candidate_is_adult") not in (True, False)
                or (row.get("heir_is_adult") is True
                    and row.get("candidate_is_adult") is True)):
            reasons.append("not_ordinary_minor_betrothal")
        if any(type(value) is not int for value in (
                heir_measure, candidate_measure, heir_threshold,
                candidate_threshold)):
            reasons.append("adult_wait_measure_unavailable")
        else:
            if (row.get("heir_is_adult") is not
                    (heir_measure >= heir_threshold)
                    or row.get("candidate_is_adult") is not
                    (candidate_measure >= candidate_threshold)
                    or abs(heir_measure - candidate_measure) >
                    _MAX_BETROTHAL_AGE_GAP_RAW):
                reasons.append("betrothal_age_gap_out_of_bounds")
        if (type(row.get("candidate_dynasty_id")) is not int
                or row["candidate_dynasty_id"] <= 0
                or row["candidate_dynasty_id"] == played_dynasty):
            reasons.append("betrothal_external_dynasty_unavailable")
        # A same-age external-Dynasty betrothal can secure the heir's future
        # partnership without a realm alliance. Keep the projection readable,
        # but do not turn a missing attempt into an invented ally payoff.
        if not isinstance(row.get("possible_alliance_pairs"), list):
            reasons.append("betrothal_alliance_projection_unavailable")
    if source.get("complete_can_send") is not True:
        reasons.append("native_can_send_not_true")
    if source.get("recipient_answer_allows_send") is not True:
        reasons.append("recipient_answer_blocks_send")
    if source.get("recipient_answer_status_raw") not in (0, 1):
        reasons.append("recipient_answer_status_not_allowed")
    if not _positive(source.get("recipient_ai_accept_raw")):
        reasons.append("recipient_accept_not_positive")
    return reasons


def _private_five_candidate_diagnostic(
    legality: Mapping[str, object], projection: Mapping[str, object],
    snapshot: Mapping[str, object], choice: Mapping[str, object] | None,
    ranking: Mapping[str, object], *,
    rejected_candidate_ids: frozenset[int] = frozenset(),
) -> dict[str, object]:
    """Retain only the five assessed rows, without advertising a query."""
    legal = legality["native_legal_candidates"]
    rows = projection["rows"]
    by_id = {row["candidate_character_id"]: row for row in legal}
    fields = ("status", "actor_character_id", "heir_character_id",
              "recipient_character_id",
              "candidate_character_id", "predicted_outcome_if_accepted",
              "heir_is_adult", "candidate_is_adult",
              "heir_adult_measure_raw", "candidate_adult_measure_raw",
              "heir_adult_threshold_raw", "candidate_adult_threshold_raw",
              "grand_wedding_option_selected",
              "generic_costs",
              "heir_betrothed_character_id", "heir_primary_spouse_character_id",
              "played_house_id", "played_dynasty_id", "heir_house_id",
              "heir_dynasty_id", "candidate_house_id", "candidate_dynasty_id",
              "heir_sex_selector_raw", "candidate_sex_selector_raw",
              "matrilineal_option_selected", "effective_matrilineal_if_accepted")
    observed = []
    for row in rows:
        source = by_id.get(row["candidate_character_id"])
        spouses = row.get("heir_spouse_character_ids")
        pairs = row.get("possible_alliance_pairs")
        observed.append({
            **{field: row.get(field) for field in fields},
            "heir_spouse_count": len(spouses) if isinstance(spouses, list) else None,
            "recipient_ai_accept_raw": source.get("recipient_ai_accept_raw") if source else None,
            "recipient_matchmaker_character_id": (
                source.get("recipient_matchmaker_character_id") if source else None),
            "recipient_answer_status_raw": source.get("recipient_answer_status_raw") if source else None,
            "recipient_answer_allows_send": source.get("recipient_answer_allows_send") if source else None,
            "complete_can_send": source.get("complete_can_send") if source else None,
            "possible_alliance_pairs": ([
                {field: pair[field] for field in (
                    "first_character_id", "second_character_id", "already_allied",
                    "both_have_realm_data", "would_attempt_if_accepted")}
                for pair in pairs
            ] if isinstance(pairs, list) else None),
            "rejection_reasons": _candidate_rejection_reasons(
                source, row, rejected_candidate_ids=rejected_candidate_ids),
        })
    return {"schema": "xar.ck3.first-heir-marriage-private-diagnostic.v1",
            "advertised": False, "read_only": True,
            "source_projection_schema": projection.get("schema"),
            "exact_ck3_build": legality.get("exact_ck3_build"),
            "episode_run_id": snapshot.get("episode_run_id"),
            "date_raw": snapshot.get("date_raw"),
            "native_revision": legality["native_revision"],
            "legality_query_sequence": legality["query_sequence"],
            "observed_first_heir_character_id": legality["observed_first_heir_character_id"],
            "final_legal_candidate_count": len(legal),
            "ranking": dict(ranking),
            "selected_candidate_character_id": (
                choice["candidate_character_id"] if choice else None),
            "rows": observed}


def _rank_five_family_candidates(
    legal_rows: list[dict[str, object]],
    *, rejected_candidate_ids: frozenset[int] = frozenset(),
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Prefer native-final external Dynasty peers before the fixed five-row read."""
    eligible = []
    unknown = 0
    fresh_rows = [row for row in legal_rows
                  if row["candidate_character_id"] not in rejected_candidate_ids]
    for row in fresh_rows:
        heir_age = row.get("heir_adult_measure_raw")
        candidate_age = row.get("candidate_adult_measure_raw")
        played_dynasty = row.get("played_dynasty_id")
        heir_dynasty = row.get("heir_dynasty_id")
        candidate_dynasty = row.get("candidate_dynasty_id")
        realm_backed = row.get("realm_backed_actor_recipient")
        if (any(type(value) is not int or value <= 0 for value in (
                played_dynasty, heir_dynasty, candidate_dynasty))
                or type(heir_age) is not int
                or type(candidate_age) is not int
                or type(realm_backed) is not bool):
            unknown += 1
            continue
        if (heir_dynasty != played_dynasty
                or candidate_dynasty == played_dynasty
                or realm_backed is not True
                or abs(heir_age - candidate_age) > _MAX_BETROTHAL_AGE_GAP_RAW
                or not _positive(row.get("recipient_ai_accept_raw"))):
            continue
        eligible.append(row)
    eligible.sort(key=lambda row: (
        abs(row["heir_adult_measure_raw"] - row["candidate_adult_measure_raw"]),
        -row["recipient_ai_accept_raw"], row["candidate_character_id"]))
    picked = eligible[:5]
    picked_ids = {row["candidate_character_id"] for row in picked}
    fallback = sorted((row for row in fresh_rows
                       if row["candidate_character_id"] not in picked_ids),
                      key=lambda row: (-row["recipient_ai_accept_raw"],
                                       row["candidate_character_id"]))
    picked.extend(fallback[:5 - len(picked)])
    # Keep the fixed five-row native projection when fewer than five fresh
    # candidates remain; old refusals are diagnostics, never selectable.
    if len(picked) < 5:
        rejected = sorted((row for row in legal_rows
                           if row["candidate_character_id"] in rejected_candidate_ids),
                          key=lambda row: (-row["recipient_ai_accept_raw"],
                                           row["candidate_character_id"]))
        picked.extend(rejected[:5 - len(picked)])
    return picked, {"rule": "external_dynasty_realm_backed_age_gap_v1",
                    "age_gap_max_raw": _MAX_BETROTHAL_AGE_GAP_RAW,
                    "prefilter_eligible_count": len(eligible),
                    "value_input_unavailable_count": unknown,
                    "conclusion": (
                        "no_age_matched_external_realm_candidate"
                        if not eligible and not unknown else
                        "unobserved_value_inputs_remain"
                        if not eligible else
                        "bounded_five_row_projection"),
                    "projected_count": len(picked)}


def rank_first_heir_marriage_candidates(
    legality: Mapping[str, object], projection: Mapping[str, object],
    *, rejected_candidate_ids: frozenset[int] = frozenset(),
) -> list[dict[str, object]]:
    """Value each distinct projected heir partnership on the same native frame.

    A projected realm alliance attempt is a separate possible consequence, not
    the marriage value or an alliance receipt. Positive recipient AI raw is
    only a send/acceptance clue.
    """
    if (legality.get("status") != "available"
            or projection.get("status") != "available"
            or projection.get("native_revision") != legality.get("native_revision")
            or projection.get("legality_query_sequence") != legality.get("query_sequence")):
        return []
    legal = legality.get("native_legal_candidates")
    rows = projection.get("rows")
    if not isinstance(legal, list) or not isinstance(rows, list) or len(rows) != 5:
        return []
    by_id = {row.get("candidate_character_id"): row for row in legal
             if isinstance(row, dict)}
    choices = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        candidate_id = row.get("candidate_character_id")
        source = by_id.get(candidate_id)
        if _candidate_rejection_reasons(
                source, row, rejected_candidate_ids=rejected_candidate_ids):
            continue
        outcome = row["predicted_outcome_if_accepted"]
        age_gap = abs(row["heir_adult_measure_raw"] -
                      row["candidate_adult_measure_raw"])
        choices.append((outcome == "marriage",
                        -age_gap,
                        source["recipient_ai_accept_raw"], -candidate_id,
                        outcome, candidate_id))
    valued = []
    for _, _, acceptance_raw, _, outcome, candidate_id in sorted(choices, reverse=True):
        selected = next(row for row in rows
                        if row["candidate_character_id"] == candidate_id)
        source = by_id[candidate_id]
        alliance_attempt = any(
            pair.get("first_character_id") == source.get("played_character_id")
            and pair.get("second_character_id") == selected.get("recipient_character_id")
            and pair.get("already_allied") is False
            and pair.get("both_have_realm_data") is True
            and pair.get("would_attempt_if_accepted") is True
            for pair in selected["possible_alliance_pairs"]
        )
        valued.append({
            "candidate_character_id": candidate_id,
            "value": ("unpartnered_first_heir_adult_marriage_opportunity"
                      if outcome == "marriage" else
                      "bounded_first_heir_betrothal_and_realm_alliance_attempt"
                      if alliance_attempt else
                      "bounded_first_heir_external_dynasty_betrothal_opportunity"),
            "predicted_outcome_if_accepted": outcome,
            "realm_alliance_attempt_if_accepted": alliance_attempt,
            "recipient_ai_accept_raw": acceptance_raw,
            "immediate_generic_costs": selected.get("generic_costs"),
            "unpriced": ["child_dynasty_result", "alliance_result",
                         "alliance_war_obligation", "betrothal_break_cost"],
        })
    return valued


def choose_first_heir_marriage_candidate(
    legality: Mapping[str, object], projection: Mapping[str, object],
    *, rejected_candidate_ids: frozenset[int] = frozenset(),
) -> dict[str, object] | None:
    """Keep the formal single-action policy on the highest ranked choice."""
    valued = rank_first_heir_marriage_candidates(
        legality, projection, rejected_candidate_ids=rejected_candidate_ids)
    return valued[0] if valued else None


def plan_family_marriage_private(driver: object, planned: dict[str, object],
                                 snapshot: Mapping[str, object], *,
                                 prewar_arbitration: bool = False,
                                 wartime_arbitration: bool = False) -> dict[str, object]:
    """Consider marriage at a peaceful opportunity or a deferrable war read.

    The normal turn keeps its life-advance boundary. A pre-war caller must
    explicitly opt in. A wartime caller also opts in and retains the same
    native final legality, value and durable-result gates.
    """
    plan = planned.get("plan")
    if not isinstance(plan, dict):
        return planned
    selected = plan.get("selected_step")
    war_read = (
        wartime_arbitration is True
        and isinstance(selected, str)
        and (selected == "life-advance" or selected.startswith("query-"))
        and isinstance(snapshot.get("active_wars"), list)
        and bool(snapshot["active_wars"])
    )
    if selected != "life-advance" and not (
        prewar_arbitration is True and is_native_declaration_step(selected)
    ) and not war_read:
        return planned
    state_dir = getattr(driver, "state_dir", None)
    if not isinstance(state_dir, Path):
        return {**planned, "plan": {**plan, "selected_step": None,
                                    "reason": "marriage trial needs durable state_dir"}}
    ledger = read_family_marriage_ledger(state_dir)
    pending = ledger["pending"]
    if isinstance(pending, dict):
        if pending.get("episode_run_id") != snapshot.get("episode_run_id"):
            return {**planned, "plan": {**plan, "selected_step": None,
                                        "reason": "unresolved marriage belongs to another episode"}}
        pid, creation = bridge_process_identity(driver)
        cold = (pid, creation) != (pending.get("source_bridge_pid"),
                                   pending.get("source_bridge_creation_date"))
        revision = snapshot.get("native_revision")
        last_checked = pending.get("last_checked_native_revision",
                                   pending.get("pre_native_revision", 0))
        checked_in_this_pid = (
            pending.get("last_checked_bridge_pid") == pid
            and pending.get("last_checked_bridge_creation_date") == creation
        )
        if ((cold and not checked_in_this_pid)
                or (_positive(revision) and revision > last_checked)):
            return {**planned, "plan": {**plan,
                "phase": "first_heir_marriage_result_read",
                "selected_step": RESULT_STEP,
                "family_marriage_pending": dict(pending),
                "family_marriage_cold_recovery": cold,
                "reason": "read proposal resolution and bilateral relation before another send"}}
        return {**planned, "plan": {**plan, "family_marriage_pending": dict(pending),
            "family_marriage_status": (
                "cold_absent_relation_unresolved"
                if pending.get("cold_absent_relation_unresolved") is True
                else "await_later_paused_frame"),
            "family_marriage_outbound_pending_state":
                pending.get("last_outbound_pending_state"),
            "reason": "await later paused frame for marriage result without resubmitting"}}
    resolved = ledger["resolved"]
    rejected_candidate_ids: frozenset[int] = frozenset()
    relation = (_current_first_heir_relation(driver, snapshot)
                if snapshot.get("paused") is True
                and snapshot.get("map_ready") is True
                and _positive(snapshot.get("native_revision")) else None)
    if relation is not None and relation["status"] == "unavailable":
        if (isinstance(resolved, dict)
                and resolved.get("episode_run_id") == snapshot.get("episode_run_id")
                and bridge_process_identity(driver) != (
                    resolved.get("post_bridge_pid"),
                    resolved.get("post_bridge_creation_date"))):
            return _plan_existing_resolution(driver, planned, plan, resolved)
        return {**planned, "plan": {**plan,
            "family_marriage_status": "current_first_heir_relation_unavailable",
            "family_marriage_current_relationship": relation}}
    if isinstance(resolved, dict) and resolved.get("episode_run_id") == snapshot.get("episode_run_id"):
        if relation is not None:
            same_heir = (resolved.get("heir_character_id") ==
                         relation.get("heir_character_id"))
            candidate = resolved.get("candidate_character_id")
            warm_rejection = (
                same_heir and resolved.get("status") in {"refused", "invalidated"}
                and not _relation_has_partner(relation)
                and bridge_process_identity(driver) == (
                    resolved.get("post_bridge_pid"),
                    resolved.get("post_bridge_creation_date")))
            if warm_rejection:
                rejected_candidate_ids = _rejected_candidates(resolved)
                resolved = None
            if resolved is not None:
                matured = (same_heir and resolved.get("status") == "betrothal"
                           and _positive(candidate)
                           and (relation.get("primary_spouse_character_id") == candidate
                                or candidate in relation.get("spouse_character_ids", [])))
                if matured:
                    pid, creation = bridge_process_identity(driver)
                    if (pid, creation) == (resolved.get("post_bridge_pid"),
                                           resolved.get("post_bridge_creation_date")):
                        resolved = {**resolved, "status": "marriage",
                                    "warm_material_transition": "betrothal_to_marriage",
                                    "warm_material_native_revision": snapshot["native_revision"]}
                        resolved.pop("alliance_result", None)
                        _write(state_dir, {**ledger, "resolved": resolved})
                elif (not _resolved_relation_matches(resolved, relation)
                      and (resolved.get("status") in {"marriage", "betrothal"}
                           or not same_heir)):
                    # An old material pair belongs to the old heir or has ended.
                    # Keep its evidence until a new proposal replaces the ledger.
                    resolved = None
        if resolved is not None:
            return _plan_existing_resolution(driver, planned, plan, resolved)
    if relation is not None and _relation_has_partner(relation):
        return {**planned, "plan": {**plan,
            "family_marriage_status": "current_first_heir_already_partnered",
            "family_marriage_current_relationship": relation}}
    if not (snapshot.get("paused") is True and snapshot.get("map_ready") is True
            and snapshot.get("active_event") is None
            and snapshot.get("pending_character_interaction") is None
            and (snapshot.get("active_wars") == [] or war_read)
            and _positive(snapshot.get("native_revision"))):
        return planned
    legality = driver.query_observed_first_heir_marriage_legality_v1(
        expected_native_revision=snapshot["native_revision"])
    if (relation is not None and legality.get("status") == "available"
            and legality.get("observed_first_heir_character_id") !=
                relation["heir_character_id"]):
        raise ValueError("current first-heir relation and legal actor differ")
    legal_rows = legality.get("native_legal_candidates")
    if legality.get("status") != "available" or not isinstance(legal_rows, list):
        return {**planned, "plan": {**plan, "family_marriage_legality": legality}}
    # Preserve the exact five-row projection: value-rank all native-final
    # legal rows on compact same-frame age, Dynasty and realm inputs first.
    ranked, ranking = _rank_five_family_candidates(
        legal_rows, rejected_candidate_ids=rejected_candidate_ids)
    if len(ranked) < 5:
        return {**planned, "plan": {**plan, "family_marriage_status":
                                    "fewer_than_five_projectable_legal_candidates"}}
    projection = driver.query_first_heir_candidate_alliance_projection_private_v1(
        legality=legality,
        candidate_character_ids=[row["candidate_character_id"] for row in ranked[:5]])
    if projection.get("status") != "available":
        return {**planned, "plan": {**plan, "selected_step": None,
            "phase": "first_heir_marriage_observation_unavailable",
            "reason": "one of five exact marriage outcome or lineage reads is unavailable"}}
    if relation is not None:
        for row in projection.get("rows", []):
            if (not isinstance(row, dict)
                    or row.get("heir_character_id") != relation["heir_character_id"]
                    or row.get("heir_betrothed_character_id") !=
                        relation["betrothed_character_id"]
                    or row.get("heir_primary_spouse_character_id") !=
                        relation["primary_spouse_character_id"]
                    or row.get("heir_spouse_character_ids") !=
                        relation["spouse_character_ids"]):
                raise ValueError("current first-heir relation and proposal projection differ")
    choices = rank_first_heir_marriage_candidates(
        legality, projection, rejected_candidate_ids=rejected_candidate_ids)
    choice = choices[0] if choices else None
    diagnostic = _private_five_candidate_diagnostic(
        legality, projection, snapshot, choice, ranking,
        rejected_candidate_ids=rejected_candidate_ids)
    if choice is None:
        return {**planned, "plan": {**plan, "family_marriage_status":
                                    "no_positive_observed_marriage_opportunity",
                                    "family_marriage_private_diagnostic": diagnostic,
                                    "family_marriage_current_relationship": relation}}
    if war_read:
        # Marriage's ordinary native Can Send only excludes a war against the
        # recipient.  The existing family value is independent of spending a
        # war cash reserve, but a prospective ally's future obligation has no
        # observed price.  Keep that unknown and the occupied characters in
        # the decision/ledger instead of treating the war as a zero cost.
        wars = snapshot["active_wars"]
        treasury = snapshot.get("played_character_gold")
        choice = {**choice, "wartime_resource_context": {
            "source_date_raw": snapshot.get("date_raw"),
            "native_revision": snapshot.get("native_revision"),
            "active_war_ids": [
                row.get("war_id") if isinstance(row, Mapping) else None
                for row in wars
            ],
            "observed_treasury": (dict(treasury)
                                  if isinstance(treasury, Mapping) else None),
            "future_war_cash_reserve_raw": None,
            "prospective_ally_war_obligation": "unknown",
            "character_claims": [
                snapshot["played_character"]["character_id"],
                legality["observed_first_heir_character_id"],
                choice["candidate_character_id"],
                next(row["recipient_matchmaker_character_id"] for row in legal_rows
                     if row["candidate_character_id"] == choice["candidate_character_id"]),
            ],
        }}
    return {**planned, "plan": {**plan, "phase": "first_heir_marriage_typed_submit",
        "selected_step": SUBMIT_STEP, "family_marriage_choice": choice,
        "family_marriage_valued_choices": choices,
        "family_marriage_rejected_candidate_ids": sorted(rejected_candidate_ids),
        "family_marriage_legality": legality,
        "family_marriage_current_relationship": relation,
        "family_marriage_private_diagnostic": diagnostic,
        "reason": "submit one observed bounded first-heir marriage or betrothal opportunity"}}


def submit_family_marriage_private(driver: object, *, plan: Mapping[str, object],
                                   snapshot: Mapping[str, object]) -> dict[str, object]:
    state_dir = driver.state_dir
    legality = plan["family_marriage_legality"]
    choice = plan["family_marriage_choice"]
    diagnostic = plan.get("family_marriage_private_diagnostic")
    candidate = choice.get("candidate_character_id")
    legal_rows = legality.get("native_legal_candidates")
    observed_rows = (diagnostic.get("rows")
                     if isinstance(diagnostic, Mapping) else None)
    legal_matches = ([row for row in legal_rows if isinstance(row, Mapping)
                      and row.get("candidate_character_id") == candidate]
                     if isinstance(legal_rows, list) else [])
    observed_matches = ([row for row in observed_rows if isinstance(row, Mapping)
                         and row.get("candidate_character_id") == candidate]
                        if isinstance(observed_rows, list) else [])
    if (len(legal_matches) != 1 or len(observed_matches) != 1
            or diagnostic.get("selected_candidate_character_id") != candidate
            or diagnostic.get("native_revision") != legality.get("native_revision")
            or diagnostic.get("legality_query_sequence") != legality.get("query_sequence")
            or diagnostic.get("date_raw") != snapshot.get("date_raw")
            or diagnostic.get("episode_run_id") != snapshot.get("episode_run_id")
            or legality.get("exact_ck3_build") != "1.19.0.6"
            or diagnostic.get("exact_ck3_build") != legality.get("exact_ck3_build")
            or diagnostic.get("source_projection_schema") !=
                CANDIDATE_PROJECTION_SCHEMA
            or observed_matches[0].get("rejection_reasons") != []):
        raise ValueError("first-heir marriage recipient lacks selected final-legal proof")
    recipient = legal_matches[0].get("recipient_matchmaker_character_id")
    if (not _positive(recipient)
            or observed_matches[0].get("recipient_character_id") != recipient
            or observed_matches[0].get("recipient_matchmaker_character_id") != recipient):
        raise ValueError("first-heir marriage recipient changed before submission")
    if getattr(driver, "allow_private_current_first_heir_relationship_query", False) is True:
        relation = plan.get("family_marriage_current_relationship")
        if (not isinstance(relation, Mapping)
                or relation.get("status") != "available"
                or relation.get("bilateral_verified") is not True
                or relation.get("native_revision") != snapshot.get("native_revision")
                or relation.get("heir_character_id") !=
                    legality.get("observed_first_heir_character_id")
                or _relation_has_partner(relation)
                or observed_matches[0].get("heir_betrothed_character_id") !=
                    relation.get("betrothed_character_id")
                or observed_matches[0].get("heir_primary_spouse_character_id") !=
                    relation.get("primary_spouse_character_id")
                or observed_matches[0].get("heir_spouse_count") !=
                    len(relation.get("spouse_character_ids", []))):
            raise ValueError("first-heir marriage lacks current same-frame relation proof")
    # The selected native projection reads this direction before the proposal.
    # It does not establish the recipient-to-player direction or causality.
    pairs = observed_matches[0].get("possible_alliance_pairs")
    player_recipient_pairs = ([pair for pair in pairs
                               if isinstance(pair, Mapping)
                               and pair.get("first_character_id") ==
                                   snapshot["played_character"]["character_id"]
                               and pair.get("second_character_id") == recipient]
                              if isinstance(pairs, list) else [])
    prior_player_allied = (player_recipient_pairs[0].get("already_allied")
                           if len(player_recipient_pairs) == 1 and
                           type(player_recipient_pairs[0].get("already_allied")) is bool
                           else None)
    alliance_attempt = any(
        pair.get("already_allied") is False
        and pair.get("both_have_realm_data") is True
        and pair.get("would_attempt_if_accepted") is True
        for pair in player_recipient_pairs
    )
    if choice.get("realm_alliance_attempt_if_accepted") is not alliance_attempt:
        raise ValueError("first-heir alliance claim changed before submission")
    selected_row = observed_matches[0]
    selected_value_projection = {
        "schema": "xar.ck3.first-heir-marriage-selected-value-projection.v1",
        "evidence_kind": "preproposal_native_projection",
        "exact_ck3_build": legality.get("exact_ck3_build"),
        "source_projection_schema": diagnostic["source_projection_schema"],
        "source_native_revision": legality["native_revision"],
        "source_legality_query_sequence": legality["query_sequence"],
        "source_date_raw": snapshot["date_raw"],
        "source_episode_run_id": snapshot["episode_run_id"],
        "played_character_id": snapshot["played_character"]["character_id"],
        "heir_character_id": legality["observed_first_heir_character_id"],
        "candidate_character_id": candidate,
        "recipient_character_id": recipient,
        **{field: selected_row.get(field) for field in _SELECTED_VALUE_FIELDS},
        # These inputs bound a future lineage estimate. No child exists in
        # this read, and neither the marriage nor its alliance is proven here.
        "child_dynasty_prediction_basis_fields": [
            "heir_dynasty_id", "candidate_dynasty_id",
            "heir_sex_selector_raw", "candidate_sex_selector_raw",
            "effective_matrilineal_if_accepted",
        ],
        "child_dynasty_prediction_status": "basis_only_unpriced",
        "predicted_child_dynasty_id": None,
        "unobserved_at_submission": [
            "actual_marriage_or_betrothal_result",
            "native_child_dynasty_result",
            "future_child_identity_and_dynasty",
            "actual_alliance_result",
        ],
        "missing_preproposal_fields": [
            field for field in _SELECTED_VALUE_FIELDS
            if selected_row.get(field) is None
        ],
    }
    pid, creation = bridge_process_identity(driver)
    pending = {"schema": SCHEMA, "status": "receipt_pending", "material_result": False,
               "pre_native_revision": snapshot["native_revision"],
               "source_date_raw": snapshot["date_raw"],
               "played_character_id": snapshot["played_character"]["character_id"],
               "heir_character_id": legality["observed_first_heir_character_id"],
               "candidate_character_id": choice["candidate_character_id"],
               "recipient_character_id": recipient,
               "preproposal_played_has_recipient_alliance": prior_player_allied,
               "preproposal_realm_alliance_attempt_if_accepted": alliance_attempt,
               "selected_value_projection": selected_value_projection,
               "episode_run_id": snapshot["episode_run_id"],
               "source_bridge_pid": pid, "source_bridge_creation_date": creation,
               "submission_state": "may_have_submitted"}
    wartime_context = choice.get("wartime_resource_context")
    if wartime_context is not None:
        if (not isinstance(wartime_context, Mapping)
                or wartime_context.get("source_date_raw") != snapshot.get("date_raw")
                or wartime_context.get("native_revision") != snapshot.get("native_revision")
                or not isinstance(snapshot.get("active_wars"), list)
                or not snapshot["active_wars"]
                or wartime_context.get("active_war_ids") != [
                    row.get("war_id") if isinstance(row, Mapping) else None
                    for row in snapshot["active_wars"]
                ]
                or wartime_context.get("observed_treasury") !=
                    snapshot.get("played_character_gold")
                or wartime_context.get("character_claims") != [
                    snapshot["played_character"]["character_id"],
                    legality["observed_first_heir_character_id"],
                    candidate, recipient,
                ]):
            raise ValueError("first-heir marriage wartime resource frame changed")
        pending["wartime_resource_context"] = dict(wartime_context)
    ledger = read_family_marriage_ledger(state_dir)
    if ledger["pending"] is not None:
        raise ValueError("first-heir marriage already has unresolved submission")
    prior_rejected = plan.get("family_marriage_rejected_candidate_ids", [])
    if (not isinstance(prior_rejected, list)
            or any(not _positive(value) for value in prior_rejected)
            or len(set(prior_rejected)) != len(prior_rejected)
            or candidate in prior_rejected):
        raise ValueError("first-heir marriage has invalid prior refusal history")
    resolved = ledger.get("resolved")
    matching_refusal = (
        isinstance(resolved, dict)
        and resolved.get("episode_run_id") == snapshot.get("episode_run_id")
        and resolved.get("heir_character_id") == pending["heir_character_id"]
        and resolved.get("status") in {"refused", "invalidated"})
    if matching_refusal:
        if (_rejected_candidates(resolved) != frozenset(prior_rejected)
                or bridge_process_identity(driver) != (
                    resolved.get("post_bridge_pid"),
                    resolved.get("post_bridge_creation_date"))):
            raise ValueError("first-heir marriage prior refusal changed before submission")
    elif prior_rejected:
        raise ValueError("first-heir marriage prior refusal changed before submission")
    pending["prior_rejected_candidate_ids"] = prior_rejected
    _write(state_dir, {**ledger, "pending": pending})
    result = driver.submit_observed_first_heir_marriage_private_v1(
        legality=legality, candidate_character_id=choice["candidate_character_id"])
    pending.update(result)
    pending["submission_state"] = "receipt_pending"
    _write(state_dir, {**ledger, "pending": pending})
    return pending


def query_family_marriage_result_private(driver: object, *,
                                         pending: Mapping[str, object],
                                         cold: bool) -> dict[str, object]:
    state_dir = driver.state_dir
    method = (driver.query_observed_first_heir_marriage_cold_result_private_v1
              if cold else driver.query_observed_first_heir_marriage_result_private_v1)
    result = method(pending=dict(pending))
    ledger = read_family_marriage_ledger(state_dir)
    prior = ledger["resolved"]
    recheck = (cold and ledger["pending"] is None
               and isinstance(prior, dict)
               and prior.get("source_pending") == dict(pending))
    if not recheck and ledger["pending"] != dict(pending):
        raise ValueError("first-heir marriage pending identity changed")
    status = result["status"]
    if recheck:
        matured = prior["status"] == "betrothal" and status == "marriage"
        if (status != prior["status"] and not matured
                or result.get("material_result") is not True):
            _write(state_dir, {**ledger, "resolved": {
                **prior, "cold_recovery_verified": False}})
            raise ValueError("cold restore lost the earlier bilateral marriage result")
        pid, creation = bridge_process_identity(driver)
        verified = {**prior, "status": status,
                    "post_bridge_pid": pid,
                    "post_bridge_creation_date": creation,
                    "cold_recovery_verified": True}
        if matured:
            # A bilateral betrothal may become a bilateral marriage while the
            # game advances. The previous alliance read belongs to that older
            # relation and must be observed again in this PID.
            verified.pop("alliance_result", None)
            verified["cold_material_transition"] = "betrothal_to_marriage"
            verified["cold_material_native_revision"] = result["post_native_revision"]
        _write(state_dir, {**ledger, "resolved": verified})
        return result
    if status in {"marriage", "betrothal", "refused", "invalidated"}:
        pid, creation = bridge_process_identity(driver)
        resolved = {"status": status, "material_result": result["material_result"],
                    "episode_run_id": pending["episode_run_id"],
                    "heir_character_id": pending["heir_character_id"],
                    "candidate_character_id": pending["candidate_character_id"],
                    "post_native_revision": result["post_native_revision"],
                    "cold_recovery": cold, "source_pending": dict(pending),
                    "post_bridge_pid": pid,
                    "post_bridge_creation_date": creation}
        if status in {"refused", "invalidated"}:
            prior_ids = pending.get("prior_rejected_candidate_ids", [])
            if (not isinstance(prior_ids, list)
                    or any(not _positive(value) for value in prior_ids)
                    or len(set(prior_ids)) != len(prior_ids)
                    or pending["candidate_character_id"] in prior_ids):
                raise ValueError("first-heir marriage rejection history is invalid")
            resolved["rejected_candidate_ids"] = [
                *prior_ids, pending["candidate_character_id"]]
        _write(state_dir, {**ledger, "pending": None, "resolved": resolved})
    elif cold and status == "pending":
        pid, creation = bridge_process_identity(driver)
        _write(state_dir, {**ledger, "pending": {
            **pending, "cold_absent_relation_unresolved": True,
            "last_outbound_pending_state": result.get("outbound_pending_state"),
            "last_outbound_pending_id": result.get("outbound_pending_id"),
            "last_outbound_pending_age_days":
                result.get("outbound_pending_age_days"),
            "last_outbound_pending_ai_reply_cutoff_days":
                result.get("outbound_pending_ai_reply_cutoff_days"),
            "last_checked_native_revision": result["post_native_revision"],
            "last_checked_bridge_pid": pid,
            "last_checked_bridge_creation_date": creation}})
    elif status in {"pending", "accepted_pending"}:
        pid, creation = bridge_process_identity(driver)
        _write(state_dir, {**ledger, "pending": {
            **pending, "last_checked_native_revision": result["post_native_revision"],
            "last_checked_bridge_pid": pid,
            "last_checked_bridge_creation_date": creation}})
    return result


def query_family_marriage_alliance_result_private(
    driver: object, *, resolved: Mapping[str, object],
) -> dict[str, object]:
    """Consume one current native alliance read without resending the proposal."""
    state_dir = driver.state_dir
    ledger = read_family_marriage_ledger(state_dir)
    if ledger["pending"] is not None or ledger["resolved"] != dict(resolved):
        raise ValueError("first-heir alliance read lacks its resolved receipt")
    pending = resolved.get("source_pending")
    recipient = (pending.get("recipient_character_id")
                 if isinstance(pending, Mapping) else None)
    if (resolved.get("status") not in {"marriage", "betrothal"}
            or resolved.get("material_result") is not True
            or not _positive(recipient)):
        raise ValueError("first-heir alliance read lacks a bound material pair")
    result = driver.query_observed_first_heir_marriage_alliance_result_private_v1(
        resolved=dict(resolved), recipient_character_id=recipient)
    pid, creation = bridge_process_identity(driver)
    before = pending.get("preproposal_played_has_recipient_alliance")
    after = result.get("played_has_recipient_alliance")
    transition = (f"observed_{str(before).lower()}_to_{str(after).lower()}"
                  if type(before) is bool and type(after) is bool else "unknown")
    observation = {
        "status": result["alliance_status"],
        "recipient_character_id": recipient,
        "played_has_recipient_alliance": result.get("played_has_recipient_alliance"),
        "recipient_has_played_alliance": result.get("recipient_has_played_alliance"),
        "preproposal_played_has_recipient_alliance": (
            before if type(before) is bool else None),
        "played_to_recipient_alliance_transition": transition,
        "relationship_status": result.get("relationship_status"),
        "native_revision": result.get("native_revision"),
        "bridge_pid": pid, "bridge_creation_date": creation,
    }
    _write(state_dir, {**ledger, "resolved": {
        **resolved, "alliance_result": observation}})
    return result
