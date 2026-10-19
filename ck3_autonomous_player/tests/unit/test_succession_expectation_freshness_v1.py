"""Bounded offline age diagnostics and the actual ordinary refresh seam."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "ck3_autonomous_player/src"))
sys.path.insert(0, str(REPO / "tools"))

from test_r76_initial_succession_root_reuse import _InitialExpectationDriver
from xar_autoplayer.bridge.campaign_root_context_contract import QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP
from xar_autoplayer.bridge.service import GameplayBridgeService

from g2_saved_campaign.succession_expectation_freshness_v1 import observe_succession_expectation_freshness_v1


def test_historical_old_projection_and_primary_heir_do_not_become_fresh_all_titles():
    source = json.loads((REPO / "docs/ck3-native-ai/evidence/p50r1-natural-successor-actual-2026-10-18.json").read_bytes())
    reconciliation = source["reconciliation"]
    preserved = copy.deepcopy(reconciliation)
    primary = source["supplemental_living_heir_evidence"]["normal_AUTO357"]["planning_source_frame"]
    last_living = {key: primary[key] for key in ("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id")}
    last_living["episode_character_id"] = primary["actor_character_id"]
    result = observe_succession_expectation_freshness_v1(reconciliation, last_living_frame=last_living)
    assert result["expectation_age_days_at_boundary"] == 3121
    assert result["last_observed_living_age_days_at_boundary"] == 7
    assert result["all_title_freshness"] == "full_expectation_not_observed"
    assert result["complete_title_ids"] is None
    assert result["same_frame_as_last_observed_living"] is False
    assert not result["fresh_immediately_before_death_claimed"]
    assert not result["replay_allowed"] and not result["business_credit"] and not result["M7_coverage_credit"]
    assert reconciliation == preserved


def test_ordinary_planner_refreshes_3121_day_estate_once_from_existing_full_root(tmp_path, monkeypatch):
    # Upstream action choice is synthetic; production Service/root materializer,
    # turn-bundle validator and complete per-title freeze run unchanged.
    monkeypatch.setattr("xar_autoplayer.bridge.service.choose_one_life_turn", lambda *_a, **_k: {
        "policy": "one-life-turn-v1", "phase": "offline_ordinary_advance", "selected_step": "life-advance"})
    driver = _InitialExpectationDriver(tmp_path)
    driver.frame.pop("succession_expectation", None)
    service = GameplayBridgeService(driver)
    service.plan_turn()
    old = copy.deepcopy(driver.frame["succession_expectation"])
    driver.frame.update(date_raw=driver.frame["date_raw"] + 3121 * 24,
                        native_revision=driver.frame["native_revision"] + 1,
                        revision=driver.frame["revision"] + 1)
    driver.frame["snapshot_id"] = f"native:{driver.frame['native_revision']}"
    driver.execute_step(QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP, expected_revision=driver.frame["revision"])
    roots = driver.root_calls
    retained = len(driver.retained_bundles)
    planned = service.plan_turn()
    current = copy.deepcopy(driver.frame["succession_expectation"])
    assert planned["plan"]["selected_step"] == "life-advance"
    assert current["binding"]["date_raw"] - old["binding"]["date_raw"] == 3121 * 24
    assert driver.root_calls == roots  # Reuses the already observed same-frame complete root.
    assert len(driver.retained_bundles) == retained + 1
    expected_rows = [{key: row[key] for key in ("title", "first_heir_character_id", "primary")}
                     for row in driver.retained_bundles[-1]["succession_state"]["value"]["partition"]["value"]["title_heirs"]]
    assert current["title_expectations"] == expected_rows
    service.plan_turn()
    assert driver.root_calls == roots and len(driver.retained_bundles) == retained + 1
    reconciliation = {"schema": "xar.ck3.succession-reconciliation/v1", "status": "available",
                      "predecessor_binding": current["binding"], "predecessor_character_id": current["predecessor_character_id"],
                      "successor_binding": {**current["binding"], "date_raw": current["binding"]["date_raw"] + 7 * 24}}
    result = observe_succession_expectation_freshness_v1(reconciliation, expectation=current,
                                                       last_living_frame=current["binding"])
    assert result["expectation_age_days_at_boundary"] == 7
    assert result["same_frame_as_last_observed_living"] is True
    assert result["all_title_freshness"] == "same_as_last_observed_living_frame"
    assert not result["fresh_immediately_before_death_claimed"]
    wrong = copy.deepcopy(current)
    wrong["binding"]["native_revision"] += 1
    with pytest.raises(ValueError, match="another source frame"):
        observe_succession_expectation_freshness_v1(reconciliation, expectation=wrong)
    with pytest.raises(ValueError, match="another episode"):
        observe_succession_expectation_freshness_v1(reconciliation, last_living_frame={**current["binding"], "episode_run_id": "another"})
