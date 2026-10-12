from __future__ import annotations

from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.army_strengths_profile_contract import (
    require_army_strengths_profile,
    validate_army_strengths_profile_coverage,
)
from xar_autoplayer.bridge.war_contract import (
    army_strength_query_status,
    normalize_army_strengths,
)


PROFILES = (
    ("ordinary_core_v1", "not_requested"),
    ("observed_history_full_v1", "exported_retained"),
)
RETAINED_FAMILIES = (
    "army_natural_phase_observations_v1",
    "actual_army_regular_core_observations_v1",
    "actual_army_daily_assault_preparation_observations_v1",
    "actual_army_assault_placement_observations_v1",
    "army_actual_assault_consumer_observations_v1",
    "actual_army_assault_group_release_observations_v1",
    "native_gathering_due_natural_stage_12004",
    "actual_army_cleanup_observations_v1",
    "actual_army_pre_date_prefix_observations_v1",
)
CORE_FIELDS = (
    "status", "army_id", "native_carmy_id", "scope_role", "war_ids",
    "regiment_count", "current_soldiers", "maximum_soldiers",
    "ai_base_power_raw", "ai_base_power_scale", "unavailable_reason",
)
SCOPE = [{"army_id": 11, "scope_role": "player", "war_ids": [101]}]


def _available_row() -> dict[str, object]:
    return {
        "status": "available", "army_id": 11, "native_carmy_id": 1011,
        "scope_role": "player", "war_ids": [101], "regiment_count": 1,
        "current_soldiers": 900, "maximum_soldiers": 1500,
        "ai_base_power_raw": 180_000_000, "ai_base_power_scale": 100_000,
        "unavailable_reason": None,
    }


def _payload(profile: str, coverage: str, row: dict[str, object]) -> dict[str, object]:
    return {
        "army_strengths_profile": profile,
        "army_observed_phase_coverage": coverage,
        "army_strengths": [row],
    }


def _row_for_profile(profile: str) -> dict[str, object]:
    row = _available_row()
    if profile == "observed_history_full_v1":
        row.update(dict.fromkeys(RETAINED_FAMILIES))
    return row


def _normalize(payload: dict[str, object], profile: str) -> list[dict[str, object]]:
    validate_army_strengths_profile_coverage(payload, expected_profile=profile)
    return normalize_army_strengths(payload["army_strengths"], expected_scope=SCOPE)


@pytest.mark.parametrize("profile,coverage", PROFILES)
def test_exact_profile_names_are_accepted(profile: str, coverage: str) -> None:
    assert require_army_strengths_profile(profile) == profile
    validate_army_strengths_profile_coverage(
        _payload(profile, coverage, _row_for_profile(profile)),
        expected_profile=profile,
    )


@pytest.mark.parametrize("profile", [
    None, False, 0, [], {}, "", "core", "unsupported", "ordinary_core_v1 ",
])
def test_unknown_or_implicit_profile_cannot_fall_back(profile: object) -> None:
    with pytest.raises(ValueError):
        require_army_strengths_profile(profile)


@pytest.mark.parametrize("profile,coverage", PROFILES)
@pytest.mark.parametrize("field", CORE_FIELDS)
def test_profile_coverage_does_not_waive_required_core_fields(
    profile: str, coverage: str, field: str,
) -> None:
    row = _row_for_profile(profile)
    del row[field]
    with pytest.raises(ValueError):
        _normalize(_payload(profile, coverage, row), profile)


def test_ordinary_omission_stays_absent_after_real_row_normalization() -> None:
    row = _normalize(_payload("ordinary_core_v1", "not_requested", _available_row()),
                     "ordinary_core_v1")[0]
    assert all(family not in row for family in RETAINED_FAMILIES)
    assert row["status"] == "available"
    assert row["current_soldiers"] == 900


def test_full_explicit_null_stays_null_without_claiming_observation_ready() -> None:
    row = _normalize(_payload("observed_history_full_v1", "exported_retained",
                              _row_for_profile("observed_history_full_v1")),
                     "observed_history_full_v1")[0]
    for family in RETAINED_FAMILIES:
        assert family in row
        assert row[family] is None
    assert row["status"] == "available"
    assert army_strength_query_status([row]) == "available"


@pytest.mark.parametrize("family", RETAINED_FAMILIES)
def test_ordinary_rejects_even_null_retained_journal(family: str) -> None:
    row = _available_row()
    row[family] = None
    with pytest.raises(ValueError):
        _normalize(_payload("ordinary_core_v1", "not_requested", row), "ordinary_core_v1")


@pytest.mark.parametrize("family", RETAINED_FAMILIES)
def test_full_missing_journal_is_not_equivalent_to_null(family: str) -> None:
    row = _row_for_profile("observed_history_full_v1")
    del row[family]
    with pytest.raises(ValueError):
        _normalize(_payload("observed_history_full_v1", "exported_retained", row),
                   "observed_history_full_v1")


@pytest.mark.parametrize("family", RETAINED_FAMILIES)
def test_exported_coverage_does_not_bypass_strict_family_value_validation(family: str) -> None:
    row = _row_for_profile("observed_history_full_v1")
    row[family] = {}
    with pytest.raises(ValueError):
        _normalize(_payload("observed_history_full_v1", "exported_retained", row),
                   "observed_history_full_v1")


@pytest.mark.parametrize("key,value", [
    ("army_strengths_profile", None),
    ("army_strengths_profile", "unsupported"),
    ("army_strengths_profile", "observed_history_full_v1"),
    ("army_observed_phase_coverage", None),
    ("army_observed_phase_coverage", "unknown"),
    ("army_observed_phase_coverage", "unsupported"),
    ("army_observed_phase_coverage", "exported_retained"),
])
def test_unknown_null_or_mismatched_metadata_is_not_ordinary_success(
    key: str, value: object,
) -> None:
    payload = _payload("ordinary_core_v1", "not_requested", _available_row())
    payload[key] = value
    with pytest.raises(ValueError):
        _normalize(payload, "ordinary_core_v1")


@pytest.mark.parametrize("key", ["army_strengths_profile", "army_observed_phase_coverage"])
def test_absent_profile_metadata_cannot_be_backfilled(key: str) -> None:
    payload = _payload("ordinary_core_v1", "not_requested", _available_row())
    del payload[key]
    with pytest.raises(ValueError):
        _normalize(payload, "ordinary_core_v1")


@pytest.mark.parametrize("rows", [None, {}, "unsupported", [None], [False], [[]]])
def test_unavailable_or_malformed_rows_cannot_become_available_empty_rows(rows: object) -> None:
    payload = _payload("ordinary_core_v1", "not_requested", _available_row())
    payload["army_strengths"] = rows
    with pytest.raises(ValueError):
        _normalize(payload, "ordinary_core_v1")


@pytest.mark.parametrize("profile,coverage", PROFILES)
def test_zero_available_strength_is_preserved(profile: str, coverage: str) -> None:
    row = _row_for_profile(profile)
    row.update(regiment_count=0, current_soldiers=0, maximum_soldiers=0, ai_base_power_raw=0)
    normalized = _normalize(_payload(profile, coverage, row), profile)[0]
    assert normalized["status"] == "available"
    assert normalized["current_soldiers"] == 0
    assert normalized["ai_base_power_raw"] == 0
    assert army_strength_query_status([normalized]) == "available"


@pytest.mark.parametrize("profile,coverage", PROFILES)
def test_native_unavailable_null_aggregates_remain_partial(profile: str, coverage: str) -> None:
    row = _row_for_profile(profile)
    row.update(status="unavailable", regiment_count=None, current_soldiers=None,
               maximum_soldiers=None, ai_base_power_raw=None,
               unavailable_reason="regiment_generation_mismatch")
    normalized = _normalize(_payload(profile, coverage, row), profile)[0]
    assert normalized["status"] == "unavailable"
    assert normalized["current_soldiers"] is None
    assert normalized["unavailable_reason"] == "regiment_generation_mismatch"
    assert army_strength_query_status([normalized]) == "partial"
    row["current_soldiers"] = 0
    with pytest.raises(ValueError):
        _normalize(_payload(profile, coverage, row), profile)


@pytest.mark.parametrize("profile,coverage", PROFILES)
@pytest.mark.parametrize("status,days,ready", [
    ("available", 2, True), ("not_gathering", None, True), ("unavailable", None, False),
])
def test_profiles_preserve_actual_gathering_availability(
    profile: str, coverage: str, status: str, days: int | None, ready: bool,
) -> None:
    row = _row_for_profile(profile)
    row.update(gathering_days_status=status, gathering_days_left=days,
               gathering_days_ready=ready)
    normalized = _normalize(_payload(profile, coverage, row), profile)[0]
    assert normalized["gathering_days_status"] == status
    assert normalized["gathering_days_left"] == days
    assert normalized["gathering_days_ready"] is ready


@pytest.mark.parametrize("profile,coverage", PROFILES)
def test_profiles_retain_refill_unknown_inputs_and_regiment_fallback(
    profile: str, coverage: str,
) -> None:
    row = _row_for_profile(profile)
    row["scoped_ordered_refill_inputs_v1"] = {
        "source": "native_scoped_observed_prepared_ordered_refill",
        "status": "unavailable", "unavailable_reason": "manager_roster_unavailable",
        "subject_army_id": 11, "subject_carmy_id": 1011,
        "native_persistent_occurrence_count": None,
        "native_army_refresh_occurrence_count": None,
        "persistent_occurrences": [], "army_refresh_occurrence_indices": [],
        "persistent_regiments": [],
    }
    row["regiment_replenishment_records_v1"] = [{
        "army_regiment_id": 17, "source": "native_all_data_records",
        "status": "unavailable", "ready": False, "native_data_record_count": None,
        "unavailable_reason": "not_captured", "records": [],
    }]
    row["regiment_strengths"] = [{
        "army_regiment_id": 17, "current_soldiers": 900,
        "maximum_soldiers": 1500, "scale": 1,
    }]
    normalized = _normalize(_payload(profile, coverage, row), profile)[0]
    refill = normalized["scoped_ordered_refill_inputs_v1"]
    assert refill == row["scoped_ordered_refill_inputs_v1"]
    assert refill["native_persistent_occurrence_count"] is None
    assert refill["status"] == "unavailable"
    record = normalized["regiment_replenishment_records_v1"][0]
    assert record["ready"] is False
    assert record["native_data_record_count"] is None
    assert record["unavailable_reason"] == "not_captured"
    assert normalized["regiment_strengths"] == row["regiment_strengths"]
