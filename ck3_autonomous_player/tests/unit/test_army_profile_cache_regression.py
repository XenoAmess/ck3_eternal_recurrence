"""Army profile caches are exact-frame reads, exercised through the real Driver."""
from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from unittest import mock

import pytest

from test_native_bridge_driver import (
    FakeEndpoint, _army, _army_strength, _hello, _snapshot, _war,
)
from xar_autoplayer.bridge.army_strengths_profile_contract import OBSERVED_PHASE_KEYS
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver


CORE = "ordinary_core_v1"
FULL = "observed_history_full_v1"
PROFILE = "army_strengths_profile"
COVERAGE = "army_observed_phase_coverage"
STEP = "query-army-strengths-v1"


@dataclass
class Scenario:
    driver: NativeHeadlessGameplayDriver
    endpoint: FakeEndpoint
    before: dict[str, object]

    def query(self, profile: str = CORE) -> dict[str, object]:
        return self.driver.query_army_strengths(
            profile=profile, expected_revision=int(self.before["revision"]),
        )

    def cached(self, snapshot=None, *, profile: str = CORE):
        snapshot = self.before if snapshot is None else snapshot
        return self.driver._army_strength_cache_for_snapshot(
            snapshot, episode_run_id=snapshot.get("episode_run_id"), profile=profile,
        )


def make_scenario(state_dir: Path, *, projection: str = "one_life") -> Scenario:
    endpoint = FakeEndpoint()
    driver = NativeHeadlessGameplayDriver(
        endpoint.pipe_name, endpoint=endpoint, state_dir=state_dir,
        command_timeout_seconds=0.1, episode_projection=projection,
    )
    first, second = _army(82), _army(81)
    wars = [_war(45, allied_armies=[second]), _war(46, allied_armies=[second])]
    endpoint.publish(_hello("game.state.snapshot", "game.command.query-army-strengths-v1"))
    endpoint.publish(_snapshot(
        40, played_character={"character_id": 707, "alive": True},
        player_armies=[first, second], active_wars=wars,
    ))
    before = driver.take_internal_semantic_snapshot()
    sequence = 0

    def answer(frame):
        nonlocal sequence
        if frame.get("type") != "execute_step":
            return
        assert frame["step"] == STEP
        profile = frame[PROFILE]
        sequence += 1
        rows = [_army_strength(82, "player", []), _army_strength(81, "player", [45, 46])]
        if profile == FULL:
            for row in rows:
                row.update({key: None for key in OBSERVED_PHASE_KEYS})
        endpoint.publish({
            "type": "command_result", "protocol_version": 1,
            "request_id": frame["request_id"], "ok": True,
            "result": {
                "step": STEP, "accepted": True, "status": "available",
                "query_sequence": sequence, "army_strengths": rows,
                PROFILE: profile,
                COVERAGE: "not_requested" if profile == CORE else "exported_retained",
            },
        })

    endpoint.send_hook = answer
    return Scenario(driver, endpoint, before)


@pytest.fixture
def scenario(tmp_path):
    value = make_scenario(tmp_path / "state")
    try:
        yield value
    finally:
        value.driver.close()


def test_real_query_publishes_detached_cache_and_public_copies(scenario):
    result = scenario.query()
    assert scenario.endpoint.frames[-1][PROFILE] == CORE
    assert result[PROFILE] == CORE and result[COVERAGE] == "not_requested"
    result["army_strengths"][1]["war_ids"].append(999)

    with mock.patch(
        "xar_autoplayer.bridge.native_driver.normalize_army_strengths",
        side_effect=AssertionError("a validated cache hit must not re-normalize"),
    ):
        first = scenario.cached()
        assert first["army_strengths"][1]["war_ids"] == [45, 46]
        first["army_strengths"][1]["war_ids"].clear()
        public = scenario.driver.take_snapshot()
        assert public[PROFILE] == CORE and public[COVERAGE] == "not_requested"
        public["army_strengths"][1]["war_ids"].append(1000)
        again = scenario.cached()
    assert again["army_strengths"][1]["war_ids"] == [45, 46]
    assert again["queried_revision"] == scenario.before["revision"]
    assert again["queried_date_raw"] == scenario.before["date_raw"]


def test_exact_frame_cache_exposes_detached_core_after_manager_input_projection(scenario):
    scenario.query()
    expected_core_rows = copy.deepcopy(scenario.driver.take_snapshot()["army_strengths"])
    with scenario.driver._driver_state_lock:
        stored_rows = scenario.driver._army_strength_query["army_strengths"]
        # A real normalized row has larger manager inputs than this small fixture.
        # They are retained for managers but must not be cloned into snapshots.
        stored_rows[1]["manager_inputs"] = {"regiments": [{"soldiers": [3, 4]}]}

    cached = scenario.cached()
    assert cached is not None
    assert cached["army_strengths"] == expected_core_rows
    public = scenario.driver.take_snapshot()
    assert public["army_strengths"] == expected_core_rows

    cached["army_strengths"][1]["war_ids"].append(999)
    public["army_strengths"][1]["war_ids"].append(1000)
    with scenario.driver._driver_state_lock:
        assert stored_rows[1]["war_ids"] == [45, 46]
        assert stored_rows[1]["manager_inputs"]["regiments"][0]["soldiers"] == [3, 4]
    assert scenario.cached()["army_strengths"] == expected_core_rows


@pytest.mark.parametrize("field", [
    "snapshot_id", "revision", "native_revision", "date_raw",
    "connection_generation", "episode_run_id",
])
def test_binding_mismatch_never_reuses_published_query(scenario, field):
    scenario.query()
    changed = copy.deepcopy(scenario.before)
    if field == "connection_generation":
        changed["diagnostics"][field] = (changed["diagnostics"].get(field) or 0) + 1
    elif field == "episode_run_id":
        changed[field] = "another-episode"
    elif field == "snapshot_id":
        changed[field] = "native:another-frame"
    else:
        changed[field] += 1
    assert scenario.cached(changed) is None
    assert scenario.driver._army_strength_query is None


@pytest.mark.parametrize("change", ["row_order", "scope_role", "war_order", "missing_army"])
def test_ordered_scope_changes_do_not_reuse_cache(scenario, change):
    scenario.query()
    changed = copy.deepcopy(scenario.before)
    if change == "row_order":
        changed["player_armies"].reverse()
    elif change == "scope_role":
        # Army 81 stays in position two with the same war IDs, but becomes an ally.
        changed["player_armies"] = changed["player_armies"][:1]
    elif change == "war_order":
        changed["active_wars"].reverse()
    else:
        changed["player_armies"] = changed["player_armies"][1:]
    assert scenario.cached(changed) is None
    assert scenario.driver._army_strength_query is None


@pytest.mark.parametrize("published,requested", [(CORE, FULL), (FULL, CORE)])
def test_profiles_are_not_interchangeable_even_in_the_same_frame(scenario, published, requested):
    result = scenario.query(published)
    assert result[PROFILE] == published
    assert scenario.cached(profile=published) is not None
    assert scenario.cached(profile=requested) is None
    assert scenario.driver._army_strength_query is None


def test_full_snapshot_is_not_advertised_as_an_ordinary_cache(scenario):
    full = scenario.query(FULL)
    assert all(key in full["army_strengths"][0] for key in OBSERVED_PHASE_KEYS)
    public = scenario.driver.take_snapshot()
    assert public["army_strengths"] == []
    assert public["army_strengths_status"] is None
    assert scenario.driver._army_strength_query is None
    ordinary = scenario.query()
    assert not any(key in ordinary["army_strengths"][0] for key in OBSERVED_PHASE_KEYS)


def test_diagnostic_payload_cannot_poison_a_previously_valid_ordinary_cache(scenario):
    scenario.query()
    assert scenario.cached() is not None

    def wrong_profile(frame):
        if frame.get("type") != "execute_step":
            return
        row = _army_strength(82, "player", [])
        # Deliberately invalid diagnostic data: profile rejection must precede
        # row validation, and this sizable response must never become a cache.
        row.update({key: None for key in OBSERVED_PHASE_KEYS})
        row["native_gathering_due_natural_stage_12004"] = {"records": ["x" * 1024] * 96}
        scenario.endpoint.publish({
            "type": "command_result", "protocol_version": 1,
            "request_id": frame["request_id"], "ok": True,
            "result": {
                "step": STEP, "accepted": True, "status": "available",
                "query_sequence": 9, "army_strengths": [row],
                PROFILE: FULL, COVERAGE: "exported_retained",
            },
        })

    scenario.endpoint.send_hook = wrong_profile
    with pytest.raises(BridgeUnavailableError, match="profile disagrees"):
        scenario.query()
    assert scenario.driver._army_strength_query is None
    assert scenario.driver.take_snapshot()["army_strengths"] == []
    assert scenario.driver._command_history[-1]["ok"] is False


def test_core_reply_with_a_null_journal_is_rejected_without_reusing_old_cache(scenario):
    scenario.query()

    def mixed_reply(frame):
        if frame.get("type") != "execute_step":
            return
        rows = [_army_strength(82, "player", []), _army_strength(81, "player", [45, 46])]
        rows[0][OBSERVED_PHASE_KEYS[0]] = None
        scenario.endpoint.publish({
            "type": "command_result", "protocol_version": 1,
            "request_id": frame["request_id"], "ok": True,
            "result": {"step": STEP, "accepted": True, "status": "available",
                       "query_sequence": 2, "army_strengths": rows,
                       PROFILE: CORE, COVERAGE: "not_requested"},
        })

    scenario.endpoint.send_hook = mixed_reply
    with pytest.raises(BridgeUnavailableError, match="ordinary Army profile exported"):
        scenario.query()
    assert scenario.driver._army_strength_query is None
    assert scenario.driver._command_history[-1]["ok"] is False


def test_native_full_refusal_has_no_core_retry_or_old_cache_fallback(scenario):
    scenario.query()
    previous_requests = len(scenario.endpoint.frames)

    def reject_full(frame):
        if frame.get("type") != "execute_step":
            return
        assert frame[PROFILE] == FULL
        scenario.endpoint.publish({
            "type": "command_result", "protocol_version": 1,
            "request_id": frame["request_id"], "ok": False,
            "error": "observed-history profile unavailable in this build",
        })

    scenario.endpoint.send_hook = reject_full
    with pytest.raises(BridgeUnavailableError, match="unavailable"):
        scenario.query(FULL)
    assert len(scenario.endpoint.frames) == previous_requests + 1
    assert scenario.endpoint.frames[-1][PROFILE] == FULL
    assert scenario.driver._army_strength_query is None
    assert scenario.driver.take_snapshot()["army_strengths"] == []
    assert scenario.driver._command_history[-1]["ok"] is False


@pytest.mark.parametrize("removed_or_changed", ["validation_schema", COVERAGE])
def test_legacy_or_wrong_coverage_cache_is_not_blessed(scenario, removed_or_changed):
    scenario.query()
    with scenario.driver._driver_state_lock:
        if removed_or_changed == "validation_schema":
            scenario.driver._army_strength_query.pop(removed_or_changed)
        else:
            scenario.driver._army_strength_query[removed_or_changed] = "exported_retained"
    assert scenario.cached() is None
    assert scenario.driver._army_strength_query is None


def test_unpaused_snapshot_does_not_expose_cache(scenario):
    scenario.query()
    changed = copy.deepcopy(scenario.before)
    changed["paused"] = False
    assert scenario.cached(changed) is None


@pytest.mark.parametrize("field", ["revision", "date_raw"])
def test_query_rejects_changed_after_view_before_cache_publication(scenario, field):
    original = scenario.driver.take_internal_semantic_snapshot
    original_answer = scenario.endpoint.send_hook
    query_sent = False

    def answer(frame):
        nonlocal query_sent
        original_answer(frame)
        if frame.get("type") == "execute_step":
            query_sent = True

    scenario.endpoint.send_hook = answer

    def changed_after():
        snapshot = original()
        if query_sent:
            snapshot = copy.deepcopy(snapshot)
            snapshot[field] += 1
        return snapshot

    with mock.patch.object(scenario.driver, "take_internal_semantic_snapshot", side_effect=changed_after):
        with pytest.raises(BridgeUnavailableError, match="crossed a snapshot revision"):
            scenario.query()
    assert len([frame for frame in scenario.endpoint.frames if frame.get("type") == "execute_step"]) == 1
    assert scenario.driver._army_strength_query is None
    assert scenario.driver._command_history[-1]["ok"] is False


def test_native_campaign_same_frame_actor_change_never_reuses_cache(tmp_path):
    value = make_scenario(tmp_path / "campaign", projection="native_campaign")
    try:
        value.query()
        assert value.cached() is not None
        changed = copy.deepcopy(value.before)
        changed["played_character"]["character_id"] = 709
        assert value.cached(changed) is None
        assert value.driver._army_strength_query is None
        assert value.driver._episode_run_id is None
    finally:
        value.driver.close()


def test_old_six_field_binding_cannot_acquire_actor_identity(scenario):
    scenario.query()
    with scenario.driver._driver_state_lock:
        scenario.driver._army_strength_query["cache_binding"].pop("actor_character_id")
    assert scenario.cached() is None
    assert scenario.driver._army_strength_query is None


@pytest.mark.parametrize("change", ["actor", "dead", "map_unready"])
def test_native_campaign_actor_drift_after_send_does_not_publish_cache(tmp_path, change):
    value = make_scenario(tmp_path / "campaign", projection="native_campaign")
    try:
        original = value.driver.take_internal_semantic_snapshot
        original_answer = value.endpoint.send_hook
        query_sent = False

        def answer(frame):
            nonlocal query_sent
            original_answer(frame)
            if frame.get("type") == "execute_step":
                query_sent = True

        value.endpoint.send_hook = answer

        def changed_after():
            snapshot = original()
            if query_sent:
                snapshot = copy.deepcopy(snapshot)
                if change == "actor":
                    snapshot["played_character"]["character_id"] = 709
                elif change == "dead":
                    snapshot["played_character"]["alive"] = False
                else:
                    snapshot["map_ready"] = False
            return snapshot

        with mock.patch.object(value.driver, "take_internal_semantic_snapshot", side_effect=changed_after):
            with pytest.raises(BridgeUnavailableError, match="played actor or playable state"):
                value.query()
        assert len([frame for frame in value.endpoint.frames if frame.get("type") == "execute_step"]) == 1
        assert value.driver._army_strength_query is None
        assert value.driver._command_history[-1]["ok"] is False
        assert value.driver._episode_run_id is None
    finally:
        value.driver.close()


def test_native_campaign_public_and_internal_views_keep_cache_without_one_life_binding(tmp_path):
    value = make_scenario(tmp_path / "campaign", projection="native_campaign")
    try:
        assert value.before.get("episode_run_id") is None
        value.query()
        for snapshot in (value.driver.take_snapshot(), value.driver.take_internal_semantic_snapshot()):
            assert [row["army_id"] for row in snapshot["army_strengths"]] == [82, 81]
            assert snapshot[PROFILE] == CORE
            assert snapshot[COVERAGE] == "not_requested"
            assert snapshot.get("episode_run_id") is None
        value.endpoint.publish(_snapshot(
            41, played_character={"character_id": 709, "alive": True},
            player_armies=[_army(82, owner_character_id=709), _army(81, owner_character_id=709)],
            active_wars=[],
        ))
        changed = value.driver.take_snapshot()
        assert changed["played_character"]["character_id"] == 709
        assert changed.get("episode_run_id") is None
        assert value.driver._episode_character_id is None
        assert value.driver._episode_run_id is None
        assert changed["army_strengths"] == []
    finally:
        value.driver.close()
