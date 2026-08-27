from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "native_bridge"
    / "research"
    / "run_battle_speed_matrix_live_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location("battle_speed_matrix_harness", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
HARNESS = importlib.util.module_from_spec(SPEC)
assert isinstance(HARNESS, ModuleType)
SPEC.loader.exec_module(HARNESS)


def _snapshot(
    *,
    date_raw: int = 1000,
    revision: int = 10,
    speed: int = 1,
    paused: bool = True,
    generation: int = 7,
) -> dict[str, object]:
    return {
        "snapshot_id": f"native:{revision}",
        "revision": revision,
        "native_revision": revision + 100,
        "date_raw": date_raw,
        "phase": "map_hud",
        "map_ready": True,
        "paused": paused,
        "speed": speed,
        "episode_character_id": 29_829,
        "episode_run_id": "episode-a",
        "active_event": None,
        "pending_character_interaction": None,
        "active_wars": [],
        "one_life_terminal": False,
        "one_life_terminal_reason": None,
        "player_armies": [],
        "diagnostics": {
            "connection_generation": generation,
            "last_heartbeat": {"sequence": revision + 200},
        },
    }


class _FakeTimelineDriver:
    def __init__(self) -> None:
        self.snapshot = _snapshot()
        self.steps: list[str] = []

    def _execute_primitive_step(
        self,
        step: str,
        *,
        expected_revision: int | None,
        timeout_seconds: float,
        internal_semantic_snapshot: bool,
    ) -> dict[str, object]:
        assert expected_revision is None
        assert timeout_seconds > 0
        assert internal_semantic_snapshot is True
        self.steps.append(step)
        if step.startswith("set-speed-"):
            self.snapshot["speed"] = int(step.rsplit("-", 1)[1])
        elif step == "resume-map":
            self.snapshot["paused"] = False
        elif step == "pause-map":
            self.snapshot["paused"] = True
        else:
            raise AssertionError(step)
        self.snapshot["revision"] = int(self.snapshot["revision"]) + 1
        return {"accepted": True, "status": "queued"}

    def take_internal_semantic_snapshot(self) -> dict[str, object]:
        return copy.deepcopy(self.snapshot)

    def _wait_for_life_advance_snapshot(
        self,
        snapshot: dict[str, object],
        predicate: object,
        *,
        timeout_seconds: float,
    ) -> dict[str, object]:
        assert timeout_seconds > 0
        assert callable(predicate)
        return copy.deepcopy(self.snapshot)

    def _wait_for_life_advance_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        assert after_revision == self.snapshot["revision"]
        assert timeout_seconds > 0
        self.snapshot["date_raw"] = int(self.snapshot["date_raw"]) + 24
        self.snapshot["revision"] = int(self.snapshot["revision"]) + 1
        heartbeat = self.snapshot["diagnostics"]["last_heartbeat"]
        heartbeat["sequence"] = int(heartbeat["sequence"]) + 1
        return copy.deepcopy(self.snapshot)


def test_balanced_five_speed_schedule_is_the_approved_matrix() -> None:
    schedule = HARNESS._balanced_speed_schedule((1, 2, 3, 4, 5), 6)
    assert schedule == [1, 2, 3, 4, 5, 5, 4, 3, 2, 1] * 3
    assert {speed: schedule.count(speed) for speed in range(1, 6)} == {
        speed: 6 for speed in range(1, 6)
    }


@pytest.mark.parametrize(
    ("speeds", "message"),
    [
        ((1, 1), "duplicates"),
        ((0, 1), "1..5"),
        ((1, 6), "1..5"),
    ],
)
def test_speed_request_rejects_duplicate_or_out_of_range_values(
    speeds: tuple[int, ...], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        HARNESS._validate_speed_request(
            "stop-envelope", speeds, samples_per_speed=1, target_days=1
        )


def test_stop_envelope_accepts_all_five_but_battle_refuses_four_and_five() -> None:
    HARNESS._validate_speed_request(
        "stop-envelope", (1, 2, 3, 4, 5), samples_per_speed=6, target_days=1
    )
    HARNESS._validate_speed_request(
        "battle-parity", (1, 2, 3), samples_per_speed=6, target_days=1
    )
    with pytest.raises(ValueError, match="same-day"):
        HARNESS._validate_speed_request(
            "battle-parity", (1, 4, 5), samples_per_speed=1, target_days=1
        )
    with pytest.raises(ValueError, match="speed 1 plus"):
        HARNESS._validate_speed_request(
            "battle-parity", (1,), samples_per_speed=1, target_days=1
        )


def test_active_battle_is_explicit_stop_envelope_scenario_not_neutral() -> None:
    snapshot = _snapshot()
    snapshot["active_wars"] = [{"war_id": 7}]
    snapshot["player_armies"] = [
        {
            "army_id": 83_886_341,
            "controllable": True,
            "in_combat": True,
            "retreating": False,
        }
    ]
    assert HARNESS._neutral_start_reason(snapshot) == "active_war"
    assert HARNESS._battle_start_reason(snapshot, 83_886_341) is None


def test_timeline_slice_uses_requested_primitive_and_proves_final_pause() -> None:
    driver = _FakeTimelineDriver()
    starting = driver.take_internal_semantic_snapshot()
    result = HARNESS._run_timeline_slice(
        driver,
        starting,
        speed=4,
        target_days=1,
        timeout_seconds=5.0,
    )
    final = driver.take_internal_semantic_snapshot()
    postconditions = HARNESS._slice_postconditions(
        result, starting=starting, final=final
    )

    assert driver.steps == ["set-speed-4", "resume-map", "pause-map"]
    assert result["first_target_observed_date_raw"] == 1024
    assert result["final_paused_date_raw"] == 1024
    assert final["paused"] is True
    assert final["speed"] == 4
    assert postconditions["ok"] is True
    assert postconditions["metrics"]["elapsed_days"] == 1
    assert postconditions["metrics"]["settle_overshoot_days"] == 0


def test_metric_derivation_separates_observation_and_pause_settle_overshoot() -> None:
    result = {
        "starting_date_raw": 1000,
        "target_date_raw": 1024,
        "first_target_observed_date_raw": 1048,
        "final_paused_date_raw": 1072,
        "slice_started_ns": 1_000_000_000,
        "first_target_observed_ns": 4_000_000_000,
        "final_observed_ns": 5_000_000_000,
        "resume_action": {"observed_ns": 2_000_000_000},
        "pause_action": {"submit_ns": 4_100_000_000},
    }
    metrics = HARNESS._derive_slice_metrics(result)
    assert metrics["elapsed_days"] == 3
    assert metrics["observation_overshoot_days"] == 1
    assert metrics["settle_overshoot_days"] == 2
    assert metrics["running_wall_ms"] == 2000.0
    assert metrics["pause_settle_ms"] == 900.0

    result["final_paused_date_raw"] = 1071
    non_integral = HARNESS._derive_slice_metrics(result)
    assert non_integral["raw_delta_integral_days"] is False
    assert non_integral["elapsed_days"] is None


def test_pause_ack_is_not_treated_as_completion() -> None:
    starting = _snapshot()
    final = _snapshot(date_raw=1024, revision=12, speed=2, paused=False)
    result = {
        "requested_speed": 2,
        "starting_date_raw": 1000,
        "target_date_raw": 1024,
        "first_target_observed_date_raw": 1024,
        "final_paused_date_raw": 1024,
        "slice_started_ns": 1,
        "first_target_observed_ns": 2,
        "final_observed_ns": 3,
        "resume_action": {"observed_ns": 1},
        "pause_action": {
            "submit_ns": 2,
            "ack_ns": 2,
            "attempts": [{"result": {"accepted": True}}],
        },
        "interrupt_reason": None,
        "error": None,
    }
    postconditions = HARNESS._slice_postconditions(
        result, starting=starting, final=final
    )
    assert postconditions["checks"]["final_paused"] is False
    assert postconditions["ok"] is False

    contaminated = _snapshot(date_raw=1024, revision=12, speed=2, paused=True)
    contaminated["active_event"] = {"instance_id": "event-1"}
    contaminated_result = HARNESS._slice_postconditions(
        result, starting=starting, final=contaminated
    )
    assert contaminated_result["checks"]["final_uncontaminated"] is False
    assert contaminated_result["ok"] is False


def test_battle_normalization_ignores_binding_metadata_but_not_roster() -> None:
    frame = {
        "snapshot_revision": 100,
        "observed_date_raw": 2000,
        "combat_id": 335_544_325,
        "phase": "main",
        "attacker": {
            "ordered_armies": [
                {"public_cunit_id": 10, "owner_character_id": 29_829}
            ],
            "participant_hard_ledger": [
                {"participant_character_id": 29_829, "hard_casualties_raw": 7}
            ],
        },
    }
    rebound = copy.deepcopy(frame)
    rebound["snapshot_revision"] = 999
    rebound["queried_revision"] = 555
    assert HARNESS._normalized_battle_frame_hash(frame) == (
        HARNESS._normalized_battle_frame_hash(rebound)
    )

    changed = copy.deepcopy(rebound)
    changed["attacker"]["ordered_armies"].append(
        {"public_cunit_id": 11, "owner_character_id": 36_108}
    )
    assert HARNESS._normalized_battle_frame_hash(frame) != (
        HARNESS._normalized_battle_frame_hash(changed)
    )


def _battle_row(
    index: int,
    speed: int,
    *,
    elapsed_days: int,
    after_hash: str,
) -> dict[str, object]:
    return {
        "sample_index": index,
        "requested_speed": speed,
        "final_paused_date_raw": 1000 + elapsed_days * 24,
        "operational_ok": True,
        "metrics": {"elapsed_days": elapsed_days},
        "battle": {
            "before_normalized_frame_sha256": "START",
            "after_normalized_frame_sha256": after_hash,
        },
    }


def test_battle_summary_compares_only_matching_elapsed_groups() -> None:
    rows = [
        _battle_row(1, 1, elapsed_days=1, after_hash="DAY1"),
        _battle_row(2, 2, elapsed_days=1, after_hash="DAY1"),
        _battle_row(3, 3, elapsed_days=2, after_hash="DAY2"),
    ]
    summary = HARNESS._summarize_battle_parity(rows, (1, 2, 3))
    assert summary["by_speed"]["2"]["status"] == "matched"
    assert summary["by_speed"]["3"]["status"] == "insufficient_matched_elapsed"
    assert summary["parity_ok"] is False
    assert summary["ok"] is False

    rows.append(_battle_row(4, 1, elapsed_days=2, after_hash="DAY2"))
    matched = HARNESS._summarize_battle_parity(rows, (1, 2, 3))
    assert matched["by_speed"]["3"]["status"] == "matched"
    assert matched["ok"] is True


def test_battle_summary_reports_calculation_mismatch_in_comparable_group() -> None:
    rows = [
        _battle_row(1, 1, elapsed_days=1, after_hash="BASELINE"),
        _battle_row(2, 2, elapsed_days=1, after_hash="DIFFERENT"),
    ]
    summary = HARNESS._summarize_battle_parity(rows, (1, 2))
    assert summary["by_speed"]["2"]["status"] == "mismatch"
    assert summary["by_speed"]["2"]["mismatch_group_count"] == 1
    assert summary["ok"] is False
