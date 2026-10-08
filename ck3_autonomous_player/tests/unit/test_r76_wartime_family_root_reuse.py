"""One new R76 ordinary cold-family root-reuse production compound.

Offline deterministic backend replies reuse committed fixture material.
The service planner, fixed-pair consumer, root-frame validator and current
relationship transport execute their production functions. No old test is
executed, and no native process or live readiness is claimed.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

from test_nonwar_planning_root_reuse import _PlanningDriver
from xar_autoplayer.bridge.campaign_root_context_contract import (
    QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
)
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.family_marriage_formal_consumer import RESULT_STEP


WAR_STEP = "query-war-termination-options-100663329"


class _R76ColdDriver(_PlanningDriver):
    _history_snapshot = NativeHeadlessGameplayDriver._history_snapshot
    # The compound owns only ordinary Family observation. Succession freezing
    # is an unrelated backend seam; production family functions stay intact.
    retain_succession_expectation_v1 = None
    reconcile_retained_succession_transition_v1 = None

    def capabilities(self):
        return {
            **super().capabilities(),
            "action_steps": [QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP, "life-advance", WAR_STEP],
        }

    def _relationship_reply(self, request_id, timeout_seconds):
        response = super()._relationship_reply(request_id, timeout_seconds)
        value = response["result"]
        value.update(
            betrothed_character_id=None,
            primary_spouse_character_id=38718,
            spouse_character_ids=[38718],
            betrothal_actionability=None,
        )
        return response


def _cold_marriage_state(driver: _R76ColdDriver):
    source = {
        "fulfill_existing_betrothal": True,
        "episode_run_id": driver.frame["episode_run_id"],
        "played_character_id": 29829,
        "heir_character_id": 38822,
        "candidate_character_id": 38718,
    }
    record = {
        "schema": "xar.ck3.first-heir-marriage-formal.v1",
        "pending": None,
        "resolved": {
            "status": "marriage",
            "heir_character_id": 38822,
            "candidate_character_id": 38718,
            "post_bridge_pid": 4241,
            "post_bridge_creation_date": "offline-prior-process",
            "source_pending": source,
        },
    }
    (driver.state_dir / "first-heir-marriage-formal-v1.json").write_text(
        json.dumps(record), encoding="utf-8"
    )


def test_r76_ordinary_cold_family_reuses_history_root_but_reads_current_relationship(
    tmp_path: Path, monkeypatch,
):
    monkeypatch.setattr(
        "xar_autoplayer.bridge.domain_construction_private_transport_v1._process_identity",
        lambda _pid: {"creation_date": "fixture-process-4242"},
    )
    # Deterministic upstream war selection reproduces the actual R76
    # observation turn; the complete downstream ordinary service path runs.
    monkeypatch.setattr(
        "xar_autoplayer.bridge.service.choose_one_life_turn",
        lambda *_args, **_kwargs: {
            "policy": "one-life-turn-v1",
            "phase": "native_war_termination_query",
            "selected_step": WAR_STEP,
            "war_id": 100663329,
        },
    )

    results = {}
    for case in ("same_frame_repeat", "native_changed", "date_changed"):
        state_dir = tmp_path / case
        state_dir.mkdir()
        driver = _R76ColdDriver(state_dir)
        driver.frame["active_wars"] = [{"war_id": 100663329, "player_side": "attacker"}]
        _cold_marriage_state(driver)
        seeded_root = driver.execute_step(
            QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
            expected_revision=driver.frame["revision"],
        )
        if case == "native_changed":
            driver.frame["revision"] += 1
            driver.frame["native_revision"] += 1
            driver.frame["snapshot_id"] = f"native:{driver.frame['native_revision']}"
        elif case == "date_changed":
            driver.frame["date_raw"] += 24

        service = GameplayBridgeService(driver)
        count = 2 if case == "same_frame_repeat" else 1
        observed = [service.plan_turn() for _ in range(count)]
        expected_roots = 1 if case == "same_frame_repeat" else 2
        assert driver.root_calls == expected_roots
        assert len(driver.requests) == count
        assert driver.submit_calls == 0
        for row in observed:
            assert row["plan"]["selected_step"] == RESULT_STEP
            assert row["plan"]["phase"] == "current_first_heir_betrothal_cold_material_recheck"
            assert row["plan"]["current_betrothal_cold_recovery"] is True
            assert row["plan"]["current_betrothal_material_recheck"] is True
            relation = row["plan"]["current_betrothal_relationship"]
            assert relation["status"] == "available"
            assert relation["bilateral_verified"] is True
            assert relation["heir_character_id"] == 38822
            assert relation["primary_spouse_character_id"] == 38718
            assert relation["spouse_character_ids"] == [38718]
            assert relation["native_revision"] == driver.frame["native_revision"]
            assert relation["root_query_sequence"] == (
                seeded_root["query_sequence"] if case == "same_frame_repeat"
                else driver.last_root_result["query_sequence"]
            )
        if case == "same_frame_repeat":
            assert observed[0] == observed[1]
        else:
            assert driver.last_root_result["queried_revision"] == driver.frame["revision"]
            assert driver.last_root_result["queried_native_revision"] == driver.frame["native_revision"]
            assert driver.last_root_result["campaign_root_context"]["date_raw"] == driver.frame["date_raw"]
        results[case] = {
            "root_calls": driver.root_calls,
            "fresh_relationship_reads": len(driver.requests),
            "selected_steps": [row["plan"]["selected_step"] for row in observed],
        }
    assert results["same_frame_repeat"]["fresh_relationship_reads"] == 2
