"""One new initial-expectation root-reuse compound on the ordinary Service path.

Backend reads are deterministic offline fixtures. Production root materializer,
turn-bundle validation and succession freeze run unchanged. The qualified
Family improvement is present but disabled here; no old test is run.
"""

from __future__ import annotations

import copy
from pathlib import Path

from test_nonwar_planning_root_reuse import _PlanningDriver
from xar_autoplayer.bridge.campaign_root_context_contract import (
    QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
)
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService


class _InitialExpectationDriver(_PlanningDriver):
    _history_snapshot = NativeHeadlessGameplayDriver._history_snapshot
    allow_private_family_marriage_formal_trial = False
    allow_private_current_first_heir_betrothal_fulfillment = False

    def __init__(self, state_dir):
        super().__init__(state_dir)
        self.allow_private_council_action = False
        self.date_change_before_bundle_snapshot = False

    def take_snapshot(self):
        if self.date_change_before_bundle_snapshot:
            self.frame["date_raw"] += 24
            self.date_change_before_bundle_snapshot = False
        return super().take_snapshot()


def test_r76_initial_expectation_reuses_current_root_and_keeps_fresh_defaults(
    tmp_path: Path, monkeypatch,
):
    # Only upstream ordinary choice is deterministic; root, bundle,
    # readiness validation and expectation freezing are production functions.
    monkeypatch.setattr(
        "xar_autoplayer.bridge.service.choose_one_life_turn",
        lambda *_args, **_kwargs: {
            "policy": "one-life-turn-v1",
            "phase": "offline_ordinary_advance",
            "selected_step": "life-advance",
        },
    )
    observed = {}
    for case in (
        "current_root",
        "native_changed",
        "date_changed",
        "date_changes_before_bundle_snapshot",
    ):
        state_dir = tmp_path / case
        state_dir.mkdir()
        driver = _InitialExpectationDriver(state_dir)
        driver.frame.pop("succession_expectation", None)
        seeded = driver.execute_step(
            QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
            expected_revision=driver.frame["revision"],
        )
        assert "binding" not in seeded
        if case == "native_changed":
            driver.frame["revision"] += 1
            driver.frame["native_revision"] += 1
            driver.frame["snapshot_id"] = f"native:{driver.frame['native_revision']}"
        elif case == "date_changed":
            driver.frame["date_raw"] += 24
        elif case == "date_changes_before_bundle_snapshot":
            driver.date_change_before_bundle_snapshot = True

        service = GameplayBridgeService(driver)
        planned = service.plan_turn()
        expected_roots = 1 if case == "current_root" else 2
        assert driver.root_calls == expected_roots
        assert len(driver.retained_bundles) == 1
        assert planned["plan"]["selected_step"] == "life-advance"
        bundle = driver.retained_bundles[0]
        for key in ("snapshot_id", "revision", "native_revision", "date_raw"):
            assert bundle["binding"][key] == driver.frame[key]
            assert driver.frame["succession_expectation"]["binding"][key] == driver.frame[key]
        assert bundle["status"] in {"available", "partial"}
        assert bundle["succession_state"]["status"] == "available"
        assert bundle["readiness"]["succession_partition_ready"] is True
        assert bundle["source"]["query_sequence"] == (
            seeded["query_sequence"] if case == "current_root"
            else driver.last_root_result["query_sequence"]
        )
        # The retained initial expectation is current. A repeated ordinary
        # plan must preserve it without another root or another freeze.
        expectation = copy.deepcopy(driver.frame["succession_expectation"])
        again = service.plan_turn()
        assert again["plan"]["selected_step"] == "life-advance"
        assert driver.root_calls == expected_roots
        assert len(driver.retained_bundles) == 1
        assert driver.frame["succession_expectation"] == expectation
        assert driver.requests == []
        assert driver.submit_calls == 0

        if case == "current_root":
            first = service.query_campaign_root_context_v1(
                expected_revision=driver.frame["revision"]
            )
            public_bundle = service.query_turn_bundle_v1(
                expected_revision=driver.frame["revision"]
            )
            assert driver.root_calls == expected_roots + 2
            assert first["query_sequence"] != seeded["query_sequence"]
            assert public_bundle["source"]["query_sequence"] != first["query_sequence"]
            shared_material = copy.deepcopy(bundle)
            fresh_material = copy.deepcopy(public_bundle)
            shared_material["source"].pop("query_sequence")
            fresh_material["source"].pop("query_sequence")
            assert shared_material == fresh_material
            assert driver.frame["succession_expectation"] == expectation
        observed[case] = {
            "initial_root_calls": expected_roots,
            "current_native_revision": driver.frame["native_revision"],
            "current_date_raw": driver.frame["date_raw"],
            "selected_step": planned["plan"]["selected_step"],
        }
    assert set(observed) == {
        "current_root", "native_changed", "date_changed",
        "date_changes_before_bundle_snapshot",
    }
