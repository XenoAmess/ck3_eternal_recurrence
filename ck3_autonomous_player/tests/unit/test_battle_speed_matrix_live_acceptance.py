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
        required_capability: str | None = None,
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


def _battle_snapshot() -> dict[str, object]:
    snapshot = _snapshot()
    snapshot["active_wars"] = [{"war_id": 16_777_290}]
    snapshot["player_armies"] = [
        {
            "army_id": 83_886_341,
            "controllable": True,
            "in_combat": True,
            "retreating": False,
        }
    ]
    return snapshot


class _FakeTerminalDriver(_FakeTimelineDriver):
    def __init__(self, *, terminal_after_days: int | None) -> None:
        super().__init__()
        self.snapshot = _battle_snapshot()
        self.terminal_after_days = terminal_after_days
        self.advanced_days = 0

    def _wait_for_life_advance_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        changed = super()._wait_for_life_advance_change(
            after_revision, timeout_seconds=timeout_seconds
        )
        self.advanced_days += 1
        if (
            self.terminal_after_days is not None
            and self.advanced_days >= self.terminal_after_days
        ):
            self.snapshot["player_armies"][0]["in_combat"] = False
            changed = copy.deepcopy(self.snapshot)
        return changed


class _FakeSentinelDriver(_FakeTimelineDriver):
    def __init__(self) -> None:
        super().__init__()
        self.snapshot = _battle_snapshot()
        self.armed: dict[str, object] | None = None

    def _execute_primitive_step(
        self,
        step: str,
        *,
        expected_revision: int | None,
        required_capability: str | None = None,
        timeout_seconds: float,
        internal_semantic_snapshot: bool,
    ) -> dict[str, object]:
        if step.startswith("research-arm-tactical-daily-sentinel-v1-"):
            assert required_capability == HARNESS.TACTICAL_SENTINEL_ARM_CAPABILITY
            self.steps.append(step)
            tokens = step.split("-")
            army_marker = tokens.index("a")
            army_count = int(tokens[army_marker + 1])
            assert len(tokens[army_marker + 2 :]) == army_count
            self.armed = {
                "state": "armed",
                "generation": 1,
                "starting_date_raw": 1000,
                "target_date_raw": 1072,
                "last_observed_date_raw": 1000,
                "trigger_date_raw": 0,
                "speed": 5,
                "mode": "terminal_or_sentinel",
                "army_count": army_count,
                "combat_count": 1,
                "completed_daily_ticks": 0,
                "intermediate_pause_count": 0,
                "trigger_flags": 0,
                "trigger_reasons": [],
                "signed_date_delta_from_target_raw": 0,
                "overshoot_days": -1,
                "pause_wrapper_called": False,
                "pause_observed": False,
                "terminal_observed": False,
                "abnormal": False,
            }
            return {
                "accepted": True,
                "status": "available",
                "tactical_daily_sentinel": copy.deepcopy(self.armed),
            }
        if step == HARNESS.TACTICAL_SENTINEL_STATUS_STEP:
            assert required_capability == HARNESS.TACTICAL_SENTINEL_STATUS_CAPABILITY
            assert self.armed is not None
            self.steps.append(step)
            return {
                "accepted": True,
                "status": "available",
                "tactical_daily_sentinel": copy.deepcopy(self.armed),
            }
        return super()._execute_primitive_step(
            step,
            expected_revision=expected_revision,
            required_capability=required_capability,
            timeout_seconds=timeout_seconds,
            internal_semantic_snapshot=internal_semantic_snapshot,
        )

    def _wait_for_life_advance_snapshot(
        self,
        snapshot: dict[str, object],
        predicate: object,
        *,
        timeout_seconds: float,
    ) -> dict[str, object]:
        assert callable(predicate)
        if predicate(self.snapshot):
            return copy.deepcopy(self.snapshot)
        self._trigger_terminal()
        return copy.deepcopy(self.snapshot)

    def _trigger_terminal(self) -> None:
        assert self.armed is not None
        self.snapshot["date_raw"] = 1024
        self.snapshot["paused"] = True
        self.snapshot["revision"] = int(self.snapshot["revision"]) + 1
        self.snapshot["player_armies"][0]["in_combat"] = False
        self.armed.update(
            {
                "state": "triggered",
                "last_observed_date_raw": 1024,
                "trigger_date_raw": 1024,
                "completed_daily_ticks": 1,
                "trigger_flags": 256,
                "trigger_reasons": ["combat_terminal"],
                "signed_date_delta_from_target_raw": -48,
                "overshoot_days": 0,
                "pause_wrapper_called": True,
                "pause_observed": True,
                "terminal_observed": True,
            }
        )


class _FakeLostRunningSentinelDriver(_FakeSentinelDriver):
    def _wait_for_life_advance_snapshot(
        self,
        snapshot: dict[str, object],
        predicate: object,
        *,
        timeout_seconds: float,
    ) -> dict[str, object]:
        assert timeout_seconds > 0
        assert callable(predicate)
        if self.armed is not None and self.snapshot.get("paused") is False:
            self._trigger_terminal()
            return copy.deepcopy(self.snapshot)
        return super()._wait_for_life_advance_snapshot(
            snapshot, predicate, timeout_seconds=timeout_seconds
        )


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


def test_terminal_accepts_all_five_but_ongoing_battle_refuses_four_and_five() -> None:
    HARNESS._validate_speed_request(
        "stop-envelope", (1, 2, 3, 4, 5), samples_per_speed=6, target_days=1
    )
    HARNESS._validate_speed_request(
        "battle-parity", (1, 2, 3), samples_per_speed=6, target_days=1
    )
    HARNESS._validate_speed_request(
        "sentinel-envelope",
        (1, 2, 3, 4, 5),
        samples_per_speed=1,
        target_days=3,
    )
    HARNESS._validate_speed_request(
        "terminal-parity",
        (1, 2, 3, 4, 5),
        samples_per_speed=1,
        target_days=1,
        terminal_max_days=45,
        terminal_max_pause_lag_days=1,
    )
    with pytest.raises(ValueError, match="same-day"):
        HARNESS._validate_speed_request(
            "battle-parity", (1, 4, 5), samples_per_speed=1, target_days=1
        )
    with pytest.raises(ValueError, match="speed 1 plus"):
        HARNESS._validate_speed_request(
            "sentinel-envelope", (1,), samples_per_speed=1, target_days=1
        )
    with pytest.raises(ValueError, match="speed 1 plus"):
        HARNESS._validate_speed_request(
            "battle-parity", (1,), samples_per_speed=1, target_days=1
        )
    with pytest.raises(ValueError, match="speed 1 plus"):
        HARNESS._validate_speed_request(
            "terminal-parity", (1,), samples_per_speed=1, target_days=1
        )


def test_terminal_request_rejects_invalid_bounds() -> None:
    with pytest.raises(ValueError, match="terminal-max-days.*positive"):
        HARNESS._validate_speed_request(
            "terminal-parity",
            (1, 5),
            samples_per_speed=1,
            target_days=1,
            terminal_max_days=0,
        )
    with pytest.raises(ValueError, match="pause-lag-days.*nonnegative"):
        HARNESS._validate_speed_request(
            "terminal-parity",
            (1, 5),
            samples_per_speed=1,
            target_days=1,
            terminal_max_pause_lag_days=-1,
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


def test_terminal_slice_runs_speed_five_until_subject_leaves_and_pauses() -> None:
    driver = _FakeTerminalDriver(terminal_after_days=2)
    starting = driver.take_internal_semantic_snapshot()
    result = HARNESS._run_terminal_slice(
        driver,
        starting,
        subject_army_id=83_886_341,
        speed=5,
        terminal_max_days=3,
        timeout_seconds=5.0,
    )
    final = driver.take_internal_semantic_snapshot()
    postconditions = HARNESS._terminal_slice_postconditions(
        result,
        subject_army_id=83_886_341,
        starting=starting,
        final=final,
    )

    assert driver.steps == ["set-speed-5", "resume-map", "pause-map"]
    assert result["first_terminal_observed_date_raw"] == 1048
    assert result["interrupt_reason"] is None
    assert result["error"] is None
    assert final["paused"] is True
    assert final["speed"] == 5
    assert postconditions["checks"]["final_subject_left_combat"] is True
    assert postconditions["metrics"]["terminal_observed_elapsed_days"] == 2
    assert postconditions["ok"] is True


def test_sentinel_slice_stops_natively_without_intermediate_external_pause() -> None:
    driver = _FakeSentinelDriver()
    starting = driver.take_internal_semantic_snapshot()
    result = HARNESS._run_sentinel_slice(
        driver,
        starting,
        subject_army_id=83_886_341,
        speed=5,
        target_days=3,
        sentinel_mode="terminal",
        timeout_seconds=5.0,
    )
    final = driver.take_internal_semantic_snapshot()
    postconditions = HARNESS._sentinel_slice_postconditions(
        result, starting=starting, final=final
    )

    assert driver.steps == [
        "set-speed-5",
        (
            "research-arm-tactical-daily-sentinel-v1-"
            "1000-to-1072-speed-5-mode-terminal-a-1-83886341"
        ),
        "resume-map",
        HARNESS.TACTICAL_SENTINEL_STATUS_STEP,
    ]
    assert result["emergency_pause_action"] is None
    assert result["final_paused_date_raw"] == 1024
    assert postconditions["metrics"]["intermediate_pause_count"] == 0
    assert postconditions["metrics"]["terminal_observed"] is True
    assert postconditions["metrics"]["native_overshoot_days"] == 0
    assert postconditions["ok"] is True


def test_sentinel_resume_is_never_retried_when_running_frame_is_missed() -> None:
    driver = _FakeLostRunningSentinelDriver()
    starting = driver.take_internal_semantic_snapshot()
    result = HARNESS._run_sentinel_slice(
        driver,
        starting,
        subject_army_id=83_886_341,
        speed=5,
        target_days=3,
        sentinel_mode="terminal",
        timeout_seconds=5.0,
    )
    final = driver.take_internal_semantic_snapshot()
    postconditions = HARNESS._sentinel_slice_postconditions(
        result, starting=starting, final=final
    )

    assert driver.steps.count("resume-map") == 1
    assert result["resume_action"]["running_observed"] is False
    assert result["emergency_pause_action"] is None
    assert postconditions["checks"]["resume_submitted_exactly_once"] is True
    assert postconditions["ok"] is True


def test_sentinel_arm_literal_watches_the_complete_requested_army_set() -> None:
    driver = _FakeSentinelDriver()
    starting = driver.take_internal_semantic_snapshot()
    result = HARNESS._run_sentinel_slice(
        driver,
        starting,
        subject_army_id=357,
        sentinel_army_ids=(357, 33_554_657),
        speed=5,
        target_days=3,
        sentinel_mode="terminal",
        timeout_seconds=5.0,
    )
    final = driver.take_internal_semantic_snapshot()
    postconditions = HARNESS._sentinel_slice_postconditions(
        result, starting=starting, final=final
    )

    assert result["sentinel_army_ids"] == [357, 33_554_657]
    assert result["arm_step"].endswith("-a-2-357-33554657")
    assert result["arm_result"]["tactical_daily_sentinel"]["army_count"] == 2
    assert postconditions["checks"]["arm_binding_acknowledged"] is True
    assert postconditions["ok"] is True


def test_sentinel_army_set_validation_is_bounded_and_subject_bound() -> None:
    assert HARNESS._normalize_sentinel_army_ids(357, None) == (357,)
    assert HARNESS._normalize_sentinel_army_ids(
        357, [357, 33_554_657]
    ) == (357, 33_554_657)
    with pytest.raises(ValueError, match="include --subject-army-id"):
        HARNESS._normalize_sentinel_army_ids(357, [33_554_657])
    with pytest.raises(ValueError, match="duplicates"):
        HARNESS._normalize_sentinel_army_ids(357, [357, 357])
    with pytest.raises(ValueError, match="at most 64"):
        HARNESS._normalize_sentinel_army_ids(1, list(range(1, 66)))


def _sentinel_summary_row(
    speed: int,
    *,
    terminal_observed: bool,
    journal_available: bool,
) -> dict[str, object]:
    row: dict[str, object] = {
        "requested_speed": speed,
        "operational_ok": True,
        "metrics": {
            "native_trigger_reasons": (
                ["combat_terminal"]
                if terminal_observed
                else ["date_deadline"]
            ),
            "native_overshoot_days": 0,
            "intermediate_pause_count": 0,
            "terminal_observed": terminal_observed,
            "abnormal": False,
        },
        "sentinel": {
            "mode": "terminal",
            "before_normalized_frame_sha256": "SAME-START",
            "zero_external_pause_or_rich_query_between_resume_and_stop": True,
        },
        "terminal": {"status": "not_observed"},
    }
    if journal_available:
        row["terminal"] = {
            "status": "available",
            "pause_lag_days": 0,
            "outcome_without_battle_warscore_sha256": "SAME-CORE-OUTCOME",
        }
    return row


def test_terminal_sentinel_date_fallback_cannot_pass_crush_gate() -> None:
    rows = [
        _sentinel_summary_row(
            speed, terminal_observed=False, journal_available=False
        )
        for speed in (1, 5)
    ]
    summary = HARNESS._summarize_sentinel_envelope(rows, (1, 5))

    assert summary["all_arms_operational"] is True
    assert summary["terminal_outcome_parity_passed"] is False
    assert summary["by_speed"]["5"]["crush_terminal_gate_passed"] is False
    assert summary["speed5_candidate_gate_passed"] is False
    assert summary["ok"] is False


def test_terminal_sentinel_requires_cursor_bound_same_day_outcome_parity() -> None:
    rows = [
        _sentinel_summary_row(
            speed, terminal_observed=True, journal_available=True
        )
        for speed in (1, 5)
    ]
    summary = HARNESS._summarize_sentinel_envelope(rows, (1, 5))

    assert summary["terminal_outcome_parity_passed"] is True
    assert summary["by_speed"]["1"]["crush_terminal_gate_passed"] is True
    assert summary["by_speed"]["5"]["crush_terminal_gate_passed"] is True
    assert summary["speed5_candidate_gate_passed"] is True
    assert summary["ok"] is True


def test_terminal_max_days_red_still_proves_pause() -> None:
    driver = _FakeTerminalDriver(terminal_after_days=None)
    starting = driver.take_internal_semantic_snapshot()
    result = HARNESS._run_terminal_slice(
        driver,
        starting,
        subject_army_id=83_886_341,
        speed=4,
        terminal_max_days=2,
        timeout_seconds=5.0,
    )
    final = driver.take_internal_semantic_snapshot()
    postconditions = HARNESS._terminal_slice_postconditions(
        result,
        subject_army_id=83_886_341,
        starting=starting,
        final=final,
    )

    assert result["interrupt_reason"] == "terminal_max_days_exceeded"
    assert result["first_terminal_observed_date_raw"] is None
    assert driver.steps[-1] == "pause-map"
    assert final["paused"] is True
    assert postconditions["ok"] is False


def test_terminal_running_throughput_excludes_pause_overshoot_days() -> None:
    metrics = HARNESS._derive_terminal_metrics(
        {
            "starting_date_raw": 1000,
            "first_terminal_observed_date_raw": 1048,
            "final_paused_date_raw": 1072,
            "slice_started_ns": 1_000_000_000,
            "first_terminal_observed_ns": 4_000_000_000,
            "final_observed_ns": 5_000_000_000,
            "resume_action": {"observed_ns": 2_000_000_000},
            "pause_action": {"submit_ns": 4_100_000_000},
        }
    )
    assert metrics["terminal_observed_elapsed_days"] == 2
    assert metrics["elapsed_days"] == 3
    assert metrics["game_days_per_running_second"] == 1.0
    assert metrics["game_days_per_end_to_end_second"] == 0.75


def test_terminal_bound_uses_exact_journal_date_not_external_observation() -> None:
    slice_result = {
        "starting_date_raw": 1000,
        "terminal_bound_date_raw": 2080,
        # Speed 4/5 external observation is allowed to arrive one day later.
        "first_terminal_observed_date_raw": 2104,
    }
    assert HARNESS._terminal_date_within_slice_bound(slice_result, 2080) is True
    assert HARNESS._terminal_date_within_slice_bound(slice_result, 2104) is False


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


def _terminal_frame(
    *, requested_cursor: int | None, event_sequence: int
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "available",
        "battle_terminal_transition_ready": True,
        "snapshot_revision": 110,
        "observed_date_raw": 1072,
        "terminal_journal": {
            "requested_after_sequence": requested_cursor,
            "oldest_available_sequence": 1,
            "latest_sequence": event_sequence,
            "event_sequence": event_sequence,
            "event_status": "observed",
        },
        "prior": {
            "combat_id": 335_544_325,
            "terminal_kind": "normal_result",
            "terminal_date_raw": 1048,
            "suppress_normal_result_envelopes": False,
            "phase_raw": 3,
            "phase_day": 33,
            "winner_raw": 1,
            "finalized_before": False,
            "daily_guard_raw": 0,
            "province_id": 2586,
            "battle_result_id": 91,
            "wipe_raw": False,
            "attacker_primary_participant_character_id": 29_829,
            "defender_primary_participant_character_id": 36_108,
            "attacker_public_cunit_ids_in_stored_order": [83_886_341],
            "defender_public_cunit_ids_in_stored_order": [357, 33_554_657],
            "battle_warscore": {
                "status": "recorded",
                "war_id": 16_777_290,
                "war_battle_row_index": 3,
                "value_raw_q100000": -275_000,
                "winner_is_war_attacker": False,
                "combat_side0_is_war_attacker": True,
                "attacker_relative_delta_raw_q100000": -275_000,
            },
        },
        "removal": {
            "prior_combat_strictly_resolves": False,
            "prior_province_contains_prior_combat_id": False,
            "result_strictly_resolves": True,
            "result_relevant_player_count": 1,
        },
        "subject": {"exists": True, "active_combat_id": None},
        "successor": {
            "state": "none",
            "matching_combat_ids_in_native_order": [],
        },
    }


class _FakeTerminalService:
    def __init__(self, frame: dict[str, object]) -> None:
        self.frame = frame
        self.query_sequence = 40
        self.calls: list[tuple[int, int, int, int | None]] = []

    def query_battle_terminal_transition_v1(
        self,
        combat_id: int,
        subject_army_id: int,
        *,
        expected_revision: int,
        after_terminal_sequence: int | None,
    ) -> dict[str, object]:
        self.calls.append(
            (
                combat_id,
                subject_army_id,
                expected_revision,
                after_terminal_sequence,
            )
        )
        self.query_sequence += 1
        return {
            "query_sequence": self.query_sequence,
            "battle_terminal_transition": copy.deepcopy(self.frame),
        }


class _FakeRefreshService:
    def __init__(self, snapshot: dict[str, object]) -> None:
        self.refreshed = copy.deepcopy(snapshot)

    def snapshot(self) -> dict[str, object]:
        return copy.deepcopy(self.refreshed)


def test_terminal_cursor_refreshes_revision_without_crossing_frame() -> None:
    prior = _snapshot(revision=10)
    refreshed = _snapshot(revision=12)
    service = _FakeRefreshService(refreshed)
    assert HARNESS._refresh_paused_query_snapshot(service, prior) == refreshed

    service.refreshed["date_raw"] = int(prior["date_raw"]) + 24
    with pytest.raises(
        RuntimeError, match="paused query refresh crossed the battle arm frame"
    ):
        HARNESS._refresh_paused_query_snapshot(service, prior)


class _FakeRestoreService:
    def __init__(self) -> None:
        self.restore_calls: list[int] = []
        self.wait_calls: list[tuple[int, float]] = []

    def snapshot(self) -> dict[str, object]:
        return _snapshot(revision=31)

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        self.wait_calls.append((after_revision, timeout_seconds))
        return _snapshot(revision=32)

    def restore_checkpoint(self, *, expected_revision: int) -> dict[str, object]:
        self.restore_calls.append(expected_revision)
        if len(self.restore_calls) == 1:
            raise HARNESS.BridgeUnavailableError(
                "native gameplay revision mismatch: expected 31, current 32"
            )
        return {"accepted": True, "status": "restored"}


def test_restore_retries_one_pre_submit_revision_race() -> None:
    service = _FakeRestoreService()
    assert HARNESS._restore_checkpoint_with_revision_retry(service) == {
        "accepted": True,
        "status": "restored",
    }
    assert service.restore_calls == [31, 32]
    assert service.wait_calls == [(31, 2.0)]


def test_terminal_cursor_excludes_old_same_combat_event_after_restore() -> None:
    service = _FakeTerminalService(
        _terminal_frame(requested_cursor=None, event_sequence=7)
    )
    result = HARNESS._terminal_cursor_pair(
        service,
        combat_id=335_544_325,
        subject_army_id=83_886_341,
        snapshot=_snapshot(),
    )
    assert result["ok"] is True
    assert result["cursor"] == 7
    assert [call[3] for call in service.calls] == [None, None]


def test_terminal_outcome_requires_new_cursor_bound_event() -> None:
    service = _FakeTerminalService(
        _terminal_frame(requested_cursor=7, event_sequence=8)
    )
    result = HARNESS._terminal_outcome_pair(
        service,
        combat_id=335_544_325,
        subject_army_id=83_886_341,
        after_terminal_sequence=7,
        snapshot=_snapshot(),
    )
    assert result["ok"] is True
    assert [call[3] for call in service.calls] == [7, 7]
    assert result["projection"]["terminal_date_raw"] == 1048
    assert result["projection"]["phase_day"] == 33
    assert isinstance(result["normalized_outcome_sha256"], str)
    assert isinstance(result["outcome_without_battle_warscore_sha256"], str)

    stale = _FakeTerminalService(
        _terminal_frame(requested_cursor=7, event_sequence=7)
    )
    stale_result = HARNESS._terminal_outcome_pair(
        stale,
        combat_id=335_544_325,
        subject_army_id=83_886_341,
        after_terminal_sequence=7,
        snapshot=_snapshot(),
    )
    assert stale_result["ok"] is False


def test_terminal_projection_ignores_late_pause_state_but_not_outcome() -> None:
    frame = _terminal_frame(requested_cursor=7, event_sequence=8)
    base = HARNESS._terminal_outcome_projection(frame)
    late = copy.deepcopy(frame)
    late["snapshot_revision"] = 999
    late["observed_date_raw"] = 1120
    late["terminal_journal"]["oldest_available_sequence"] = 3
    late["terminal_journal"]["latest_sequence"] = 12
    late["terminal_journal"]["event_sequence"] = 12
    late["subject"] = {"exists": True, "active_combat_id": 335_544_326}
    late["successor"] = {
        "state": "residual_new_combat",
        "matching_combat_ids_in_native_order": [335_544_326],
    }
    assert HARNESS._canonical_sha256(base) == HARNESS._canonical_sha256(
        HARNESS._terminal_outcome_projection(late)
    )

    changed = copy.deepcopy(frame)
    changed["prior"]["terminal_date_raw"] += 24
    assert HARNESS._canonical_sha256(base) != HARNESS._canonical_sha256(
        HARNESS._terminal_outcome_projection(changed)
    )
    changed = copy.deepcopy(frame)
    changed["prior"]["defender_public_cunit_ids_in_stored_order"].append(99)
    assert HARNESS._canonical_sha256(base) != HARNESS._canonical_sha256(
        HARNESS._terminal_outcome_projection(changed)
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


def _terminal_row(
    index: int,
    speed: int,
    *,
    outcome_hash: str,
    before_hash: str = "START",
    elapsed_days: int = 3,
    non_warscore_hash: str = "CORE",
    warscore_raw: int = 2_133_250,
) -> dict[str, object]:
    return {
        "sample_index": index,
        "requested_speed": speed,
        "final_paused_date_raw": 1000 + elapsed_days * 24,
        "operational_ok": True,
        "metrics": {"elapsed_days": elapsed_days, "total_wall_ms": 1000 / speed},
        "terminal": {
            "before_normalized_frame_sha256": before_hash,
            "normalized_outcome_sha256": outcome_hash,
            "outcome_without_battle_warscore_sha256": non_warscore_hash,
            "battle_warscore_value_raw_q100000": warscore_raw,
            "pause_lag_days": speed % 2,
        },
    }


def test_terminal_summary_compares_outcome_not_external_pause_date() -> None:
    rows = [
        _terminal_row(
            speed,
            speed,
            outcome_hash="SAME",
            elapsed_days=2 + speed,
        )
        for speed in range(1, 6)
    ]
    summary = HARNESS._summarize_terminal_parity(rows, (1, 2, 3, 4, 5))
    assert all(
        summary["comparisons_to_speed_1"][str(speed)]["status"] == "matched"
        for speed in range(2, 6)
    )
    assert summary["parity_ok"] is True
    assert summary["ok"] is True


def test_terminal_summary_reports_outcome_or_seed_mismatch() -> None:
    rows = [
        _terminal_row(1, 1, outcome_hash="BASE"),
        _terminal_row(2, 4, outcome_hash="DIFFERENT"),
        _terminal_row(3, 5, outcome_hash="BASE", before_hash="OTHER-SEED"),
    ]
    summary = HARNESS._summarize_terminal_parity(rows, (1, 4, 5))
    assert (
        summary["comparisons_to_speed_1"]["4"]["status"]
        == "terminal_outcome_mismatch"
    )
    assert (
        summary["comparisons_to_speed_1"]["5"]["status"]
        == "starting_frame_mismatch"
    )
    assert summary["ok"] is False


def test_terminal_summary_marks_within_speed_nondeterminism_inconclusive() -> None:
    rows = [
        _terminal_row(1, 1, outcome_hash="A", warscore_raw=2_131_550),
        _terminal_row(2, 2, outcome_hash="B", warscore_raw=2_137_600),
        _terminal_row(3, 2, outcome_hash="C", warscore_raw=2_133_250),
        _terminal_row(4, 1, outcome_hash="C", warscore_raw=2_133_250),
    ]
    summary = HARNESS._summarize_terminal_parity(rows, (1, 2))
    assert summary["within_speed_not_reproducible"] == ["1", "2"]
    assert (
        summary["comparisons_to_speed_1"]["2"]["status"]
        == "baseline_not_reproducible"
    )
    assert summary["outcome_without_battle_warscore_all_equal"] is True
    assert summary["parity_ok"] is False
    assert summary["ok"] is False
