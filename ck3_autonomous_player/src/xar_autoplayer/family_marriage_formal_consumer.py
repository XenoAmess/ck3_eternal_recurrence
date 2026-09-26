"""Bounded private first-heir marriage consumer; no public capability claim."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from .environment import write_json_atomic
from .bridge.declaration_contract import is_native_declaration_step
from .bridge.domain_construction_private_transport_v1 import _identity as bridge_process_identity
from .bridge.observed_heir_marriage_private_action_v1 import SCHEMA, SUBMIT_STEP, RESULT_STEP


_LEDGER = "first-heir-marriage-formal-v1.json"
_MAX_BETROTHAL_AGE_GAP_RAW = 2


def _positive(value: object) -> bool:
    return type(value) is int and value > 0


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
                                 row: Mapping[str, object]) -> list[str]:
    """Use the same narrow value gates for selection and private diagnostics."""
    candidate_id = row.get("candidate_character_id")
    if not _positive(candidate_id):
        return ["invalid_candidate_identity"]
    if not isinstance(source, dict):
        return ["not_in_final_legal_rows"]
    reasons = []
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
        pairs = row.get("possible_alliance_pairs")
        if (not isinstance(pairs, list) or not any(
                isinstance(pair, dict)
                and pair.get("first_character_id") == source.get("played_character_id")
                and pair.get("second_character_id") == row.get("recipient_character_id")
                and pair.get("already_allied") is False
                and pair.get("both_have_realm_data") is True
                and pair.get("would_attempt_if_accepted") is True
                for pair in pairs)):
            reasons.append("betrothal_realm_alliance_attempt_unavailable")
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
    ranking: Mapping[str, object],
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
            "rejection_reasons": _candidate_rejection_reasons(source, row),
        })
    return {"schema": "xar.ck3.first-heir-marriage-private-diagnostic.v1",
            "advertised": False, "read_only": True,
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
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Prefer native-final external Dynasty peers before the fixed five-row read."""
    eligible = []
    unknown = 0
    for row in legal_rows:
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
    fallback = sorted((row for row in legal_rows
                       if row["candidate_character_id"] not in picked_ids),
                      key=lambda row: (-row["recipient_ai_accept_raw"],
                                       row["candidate_character_id"]))
    picked.extend(fallback[:5 - len(picked)])
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


def choose_first_heir_marriage_candidate(
    legality: Mapping[str, object], projection: Mapping[str, object],
) -> dict[str, object] | None:
    """Value an adult marriage, or an age-aligned external-dynasty betrothal.

    A projected alliance attempt is a narrow betrothal signal, not an alliance
    receipt. Positive recipient AI raw is only a send/acceptance clue.
    """
    if (legality.get("status") != "available"
            or projection.get("status") != "available"
            or projection.get("native_revision") != legality.get("native_revision")
            or projection.get("legality_query_sequence") != legality.get("query_sequence")):
        return None
    legal = legality.get("native_legal_candidates")
    rows = projection.get("rows")
    if not isinstance(legal, list) or not isinstance(rows, list) or len(rows) != 5:
        return None
    by_id = {row.get("candidate_character_id"): row for row in legal
             if isinstance(row, dict)}
    choices = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        candidate_id = row.get("candidate_character_id")
        source = by_id.get(candidate_id)
        if _candidate_rejection_reasons(source, row):
            continue
        outcome = row["predicted_outcome_if_accepted"]
        age_gap = abs(row["heir_adult_measure_raw"] -
                      row["candidate_adult_measure_raw"])
        choices.append((outcome == "marriage",
                        -age_gap,
                        source["recipient_ai_accept_raw"], -candidate_id,
                        outcome, candidate_id))
    if not choices:
        return None
    _, _, acceptance_raw, _, outcome, candidate_id = max(choices)
    return {"candidate_character_id": candidate_id,
            "value": ("unpartnered_first_heir_adult_marriage_opportunity"
                      if outcome == "marriage" else
                      "bounded_first_heir_betrothal_and_realm_alliance_attempt"),
            "predicted_outcome_if_accepted": outcome,
            "recipient_ai_accept_raw": acceptance_raw,
            "unpriced": ["child_dynasty_result", "alliance_result",
                         "alliance_war_obligation", "betrothal_break_cost"]}


def plan_family_marriage_private(driver: object, planned: dict[str, object],
                                 snapshot: Mapping[str, object], *,
                                 prewar_arbitration: bool = False) -> dict[str, object]:
    """Consider marriage before an opted-in native declaration query or send.

    The normal turn keeps its life-advance boundary. A pre-war caller must
    explicitly opt in; all scene, legality, value and durable-result gates
    below are shared with that normal turn.
    """
    plan = planned.get("plan")
    if not isinstance(plan, dict):
        return planned
    selected = plan.get("selected_step")
    if selected != "life-advance" and not (
        prewar_arbitration is True and is_native_declaration_step(selected)
    ):
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
            "reason": "await later paused frame for marriage result without resubmitting"}}
    resolved = ledger["resolved"]
    if isinstance(resolved, dict) and resolved.get("episode_run_id") == snapshot.get("episode_run_id"):
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
        return {**planned, "plan": {**plan, "family_marriage_result_consumed": resolved}}
    if not (snapshot.get("paused") is True and snapshot.get("map_ready") is True
            and snapshot.get("active_event") is None
            and snapshot.get("pending_character_interaction") is None
            and snapshot.get("active_wars") == []
            and _positive(snapshot.get("native_revision"))):
        return planned
    legality = driver.query_observed_first_heir_marriage_legality_v1(
        expected_native_revision=snapshot["native_revision"])
    legal_rows = legality.get("native_legal_candidates")
    if legality.get("status") != "available" or not isinstance(legal_rows, list):
        return {**planned, "plan": {**plan, "family_marriage_legality": legality}}
    # Preserve the exact five-row projection: value-rank all native-final
    # legal rows on compact same-frame age, Dynasty and realm inputs first.
    ranked, ranking = _rank_five_family_candidates(legal_rows)
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
    choice = choose_first_heir_marriage_candidate(legality, projection)
    diagnostic = _private_five_candidate_diagnostic(
        legality, projection, snapshot, choice, ranking)
    if choice is None:
        return {**planned, "plan": {**plan, "family_marriage_status":
                                    "no_positive_observed_marriage_opportunity",
                                    "family_marriage_private_diagnostic": diagnostic}}
    return {**planned, "plan": {**plan, "phase": "first_heir_marriage_typed_submit",
        "selected_step": SUBMIT_STEP, "family_marriage_choice": choice,
        "family_marriage_legality": legality,
        "family_marriage_private_diagnostic": diagnostic,
        "reason": "submit one observed bounded first-heir marriage or betrothal opportunity"}}


def submit_family_marriage_private(driver: object, *, plan: Mapping[str, object],
                                   snapshot: Mapping[str, object]) -> dict[str, object]:
    state_dir = driver.state_dir
    legality = plan["family_marriage_legality"]
    choice = plan["family_marriage_choice"]
    pid, creation = bridge_process_identity(driver)
    pending = {"schema": SCHEMA, "status": "receipt_pending", "material_result": False,
               "pre_native_revision": snapshot["native_revision"],
               "source_date_raw": snapshot["date_raw"],
               "played_character_id": snapshot["played_character"]["character_id"],
               "heir_character_id": legality["observed_first_heir_character_id"],
               "candidate_character_id": choice["candidate_character_id"],
               "episode_run_id": snapshot["episode_run_id"],
               "source_bridge_pid": pid, "source_bridge_creation_date": creation,
               "submission_state": "may_have_submitted"}
    ledger = read_family_marriage_ledger(state_dir)
    if ledger["pending"] is not None:
        raise ValueError("first-heir marriage already has unresolved submission")
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
        if status != prior["status"] or result.get("material_result") is not True:
            _write(state_dir, {**ledger, "resolved": {
                **prior, "cold_recovery_verified": False}})
            raise ValueError("cold restore lost the earlier bilateral marriage result")
        pid, creation = bridge_process_identity(driver)
        _write(state_dir, {**ledger, "resolved": {
            **prior, "post_bridge_pid": pid,
            "post_bridge_creation_date": creation,
            "cold_recovery_verified": True}})
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
        _write(state_dir, {**ledger, "pending": None, "resolved": resolved})
    elif cold and status == "pending":
        pid, creation = bridge_process_identity(driver)
        _write(state_dir, {**ledger, "pending": {
            **pending, "cold_absent_relation_unresolved": True,
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
