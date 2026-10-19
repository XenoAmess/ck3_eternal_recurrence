"""Offline source-age projection; never grants Continue, Close or SAVE authority.

Call this after a closed batch with its existing small original projections.
A primary-heir scalar cannot replace the original complete title expectation.
No source file, history, Driver, SAVE or game endpoint is read by this module.
"""
from __future__ import annotations

from copy import deepcopy

from xar_autoplayer.bridge.succession_transition_contract import (
    SUCCESSION_RECONCILIATION_V1_SCHEMA,
    normalize_succession_expectation_v1,
)


def _binding(value, *, episode):
    if not isinstance(value, dict):
        raise ValueError("succession freshness source binding is missing")
    fields = ("snapshot_id", "revision", "native_revision", "date_raw")
    if not isinstance(value.get("snapshot_id"), str) or not value["snapshot_id"]:
        raise ValueError("succession freshness snapshot identity is malformed")
    for key in fields[1:]:
        if type(value.get(key)) is not int or value[key] < 0:
            raise ValueError("succession freshness numeric source binding is malformed")
    if episode:
        fields += ("episode_run_id", "episode_character_id")
        if (not isinstance(value.get("episode_run_id"), str) or not value["episode_run_id"]
                or type(value.get("episode_character_id")) is not int
                or value["episode_character_id"] <= 0):
            raise ValueError("succession freshness episode binding is malformed")
    return {key: value[key] for key in fields}


def observe_succession_expectation_freshness_v1(
    reconciliation, *, expectation=None, last_living_frame=None,
):
    """Separate measured source age from unproved pre-death title freshness.

    ``last_living_frame`` is the existing last observed living pre-advance
    binding, not an independently reconstructed frame immediately before death.
    A caller must retain the original source pins and Game identity separately.
    """
    if (not isinstance(reconciliation, dict)
            or reconciliation.get("schema") != SUCCESSION_RECONCILIATION_V1_SCHEMA
            or reconciliation.get("status") != "available"):
        raise ValueError("succession freshness requires the original reconciliation")
    source = _binding(reconciliation.get("predecessor_binding"), episode=True)
    boundary = _binding(reconciliation.get("successor_binding"), episode=False)
    if source["episode_character_id"] != reconciliation.get("predecessor_character_id"):
        raise ValueError("succession freshness predecessor differs")
    age = boundary["date_raw"] - source["date_raw"]
    if age < 0:
        raise ValueError("succession freshness source is after the boundary")
    full = normalize_succession_expectation_v1(expectation) if expectation is not None else None
    if full is not None and full["binding"] != source:
        raise ValueError("complete title expectation belongs to another source frame")
    living = _binding(last_living_frame, episode=True) if last_living_frame is not None else None
    same = None
    living_age = None
    if living is not None:
        if any(living[key] != source[key] for key in ("episode_run_id", "episode_character_id")):
            raise ValueError("last observed living frame belongs to another episode")
        if not source["date_raw"] <= living["date_raw"] <= boundary["date_raw"]:
            raise ValueError("last observed living frame is outside the transition dates")
        same = source == living
        living_age = boundary["date_raw"] - living["date_raw"]
    if full is None:
        title_state = "full_expectation_not_observed"
    elif living is None:
        title_state = "last_living_frame_not_observed"
    else:
        title_state = ("same_as_last_observed_living_frame" if same
                       else "different_from_last_observed_living_frame")
    return {
        "schema": "xar.g2.succession-expectation-freshness-observation.v1",
        "status": "observed",
        "predecessor_binding": deepcopy(source),
        "boundary_binding": deepcopy(boundary),
        "expectation_age_raw_at_boundary": age,
        "expectation_age_days_at_boundary": age / 24,
        "last_observed_living_binding": deepcopy(living),
        "last_observed_living_age_days_at_boundary": None if living_age is None else living_age / 24,
        "same_frame_as_last_observed_living": same,
        "complete_title_expectation_observed": full is not None,
        "complete_title_ids": None if full is None else [row["title"]["title_id"] for row in full["title_expectations"]],
        "all_title_freshness": title_state,
        "fresh_immediately_before_death_claimed": False,
        "reconciliation_verdict_transcribed": reconciliation.get("verdict"),
        "reconciliation_verified_by_this_observer": False,
        "process_birth_verified_by_this_observer": False,
        "replay_allowed": False,
        "business_credit": False,
        "M7_coverage_credit": False,
    }
