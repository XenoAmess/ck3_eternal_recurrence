"""War-result dismissal has a six-day observation cadence and a verified close."""

from threading import RLock

from xar_autoplayer.bridge.war_results_window_transport import war_results_window_snapshot_fields
from xar_autoplayer.ordinary_war_results_window_v1 import (
    CLOSE_WAR_RESULTS_WINDOW_V1_CAPABILITY,
    CLOSE_WAR_RESULTS_WINDOW_V1_STEP,
    QUERY_WAR_RESULTS_WINDOW_V1_CAPABILITY,
    QUERY_WAR_RESULTS_WINDOW_V1_STEP,
    plan_ordinary_war_results_window_v1,
)


class _Driver:
    def __init__(self):
        self._driver_state_lock = RLock()
        self._war_results_window_observation = None
        self._war_results_window_query_attempt = None
        self._war_results_window_close_pending = None
        self._war_results_window_last_clear = {
            "episode_run_id": "robert",
            "connection_generation": 3,
            "actor_character_id": 31254,
            "date_raw": 53100000,
            "war_signature": (71,),
        }


def _snapshot(date_raw=53100000, war_ids=(71,)):
    return {
        "snapshot_id": "native:9", "revision": 3, "native_revision": 9,
        "date_raw": date_raw, "episode_run_id": "robert", "paused": True,
        "map_ready": True, "played_character": {"character_id": 31254, "alive": True},
        "diagnostics": {"connection_generation": 3},
        "active_wars": [{"war_id": war_id} for war_id in war_ids],
    }


def test_war_results_six_day_cadence_and_war_transition():
    driver = _Driver()
    assert war_results_window_snapshot_fields(driver, _snapshot(53100000 + 5 * 24))["war_results_window_v1_check_due"] is False
    assert war_results_window_snapshot_fields(driver, _snapshot(53100000 + 6 * 24))["war_results_window_v1_check_due"] is True
    assert war_results_window_snapshot_fields(driver, _snapshot(53100000 + 24, ()))["war_results_window_v1_check_due"] is True


def test_war_results_visible_has_priority_and_never_repeats_pending_close():
    snapshot = _snapshot()
    snapshot["war_results_window_v1_check_due"] = False
    capabilities = (QUERY_WAR_RESULTS_WINDOW_V1_CAPABILITY, CLOSE_WAR_RESULTS_WINDOW_V1_CAPABILITY)
    steps = (QUERY_WAR_RESULTS_WINDOW_V1_STEP, CLOSE_WAR_RESULTS_WINDOW_V1_STEP)
    assert plan_ordinary_war_results_window_v1(snapshot, action_steps=steps, bridge_capabilities=capabilities) is None
    snapshot["war_results_window_v1_check_due"] = True
    assert plan_ordinary_war_results_window_v1(snapshot, action_steps=steps, bridge_capabilities=capabilities)["selected_step"] == QUERY_WAR_RESULTS_WINDOW_V1_STEP
    snapshot["war_results_window_v1_observation"] = {
        "sdk_validation_schema": "war-results-window-source-v1",
        "queried_snapshot_id": "native:9", "queried_revision": 3,
        "queried_native_revision": 9, "queried_date_raw": 53100000,
        "queried_actor_character_id": 31254, "queried_connection_generation": 3,
        "queried_episode_run_id": "robert", "available": True,
        "post_observed": True, "scope_unchanged": True,
        "post_window_present": True, "post_effective_visible": True,
    }
    assert plan_ordinary_war_results_window_v1(snapshot, action_steps=steps, bridge_capabilities=capabilities)["selected_step"] == CLOSE_WAR_RESULTS_WINDOW_V1_STEP
    snapshot["war_results_window_v1_close_pending"] = {"native_request_id": "original"}
    assert plan_ordinary_war_results_window_v1(snapshot, action_steps=steps, bridge_capabilities=capabilities)["selected_step"] == QUERY_WAR_RESULTS_WINDOW_V1_STEP
