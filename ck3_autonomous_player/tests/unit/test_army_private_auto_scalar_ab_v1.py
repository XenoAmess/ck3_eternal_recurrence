"""The private Army producer can serve AUTO only after exact-frame scalar equality."""

from __future__ import annotations

from copy import deepcopy

import pytest

from test_army_profile_cache_regression import make_scenario
from test_native_bridge_driver import _army_strength
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.driver import UnsupportedStepError
from xar_autoplayer.bridge.private_auto_scalar_ab_control_v1 import selected_mode
from xar_autoplayer.bridge.private_auto_scalar_ab_control_v1 import register_tools


CAPABILITY = "game.command.query-army-strengths-private-auto-scalar-v1"
PROFILE = "private_auto_scalar_v1"
CORE_KEYS = (
    "status", "army_id", "native_carmy_id", "scope_role", "war_ids",
    "regiment_count", "current_soldiers", "maximum_soldiers",
    "ai_base_power_raw", "ai_base_power_scale", "unavailable_reason",
)
OPTIONAL_PAIRS = (
    ("current_supply_raw", "current_supply_scale"),
    ("current_attrition_fraction_raw", "current_attrition_fraction_scale"),
)


def _advertise(scenario) -> None:
    state = scenario.driver.state
    with state._condition:
        state._hello["capabilities"].append(CAPABILITY)
    assert CAPABILITY in scenario.driver.capabilities()["bridge_capabilities"]


def _private_rows() -> list[dict[str, object]]:
    rich = [_army_strength(82, "player", []), _army_strength(81, "player", [45, 46])]
    rows = []
    for raw in rich:
        row = {key: deepcopy(raw[key]) for key in CORE_KEYS}
        for value_key, scale_key in OPTIONAL_PAIRS:
            if value_key in raw:
                row[value_key] = raw[value_key]
                row[scale_key] = raw[scale_key]
        rows.append(row)
    return rows


def _answer_private(scenario, *, change: str | None = None) -> None:
    original_answer = scenario.endpoint.send_hook

    def answer(frame):
        if frame.get("type") != "execute_step" or frame.get("army_strengths_profile") != PROFILE:
            return original_answer(frame)
        rows = _private_rows()
        if change == "soldiers":
            rows[0]["current_soldiers"] += 1
        elif change == "missing_field":
            del rows[0]["ai_base_power_raw"]
        scenario.endpoint.publish({
            "type": "command_result", "protocol_version": 1,
            "request_id": frame["request_id"], "ok": True,
            "result": {
                "step": "query-army-strengths-v1", "accepted": True,
                "status": "available", "query_sequence": 91,
                "army_strengths": rows, "army_strengths_profile": PROFILE,
                "army_observed_phase_coverage": "not_requested",
            },
        })

    scenario.endpoint.send_hook = answer


def _queries(scenario) -> list[dict[str, object]]:
    return [frame for frame in scenario.endpoint.frames if frame.get("type") == "execute_step"]


@pytest.mark.parametrize("advertised", [True, False])
def test_default_or_missing_native_capability_keeps_full_producer(tmp_path, advertised):
    scenario = make_scenario(tmp_path / "state")
    try:
        if advertised:
            _advertise(scenario)
        status = scenario.driver.query_army_private_auto_scalar_ab_v1(
            expected_revision=scenario.before["revision"],
        )
        assert status["mode"] == "off"
        assert status["business_actions_submitted"] == 0
        if not advertised:
            with pytest.raises(UnsupportedStepError):
                scenario.driver.set_army_private_auto_scalar_ab_v1(
                    "compare", expected_revision=scenario.before["revision"],
                )
        result = scenario.driver.query_army_strengths(
            expected_revision=scenario.before["revision"], _auto_core_only=True,
        )
        assert [frame["army_strengths_profile"] for frame in _queries(scenario)] == ["ordinary_core_v1"]
        assert result["army_strengths_profile"] == "ordinary_core_v1"
        assert scenario.driver._army_strength_cache_for_snapshot(
            scenario.before, episode_run_id=scenario.before["episode_run_id"],
        ) is not None
    finally:
        scenario.driver.close()


def test_use_only_after_same_identity_comparison_keeps_public_cache_and_explicit_full(tmp_path):
    scenario = make_scenario(tmp_path / "state")
    try:
        _advertise(scenario)
        _answer_private(scenario)
        with pytest.raises(BridgeUnavailableError, match="comparison is required"):
            scenario.driver.set_army_private_auto_scalar_ab_v1(
                "use", expected_revision=scenario.before["revision"],
            )
        scenario.driver.set_army_private_auto_scalar_ab_v1(
            "compare", expected_revision=scenario.before["revision"],
        )
        scenario.driver.query_army_strengths(
            expected_revision=scenario.before["revision"], _auto_core_only=True,
        )
        enabled = scenario.driver.set_army_private_auto_scalar_ab_v1(
            "use", expected_revision=scenario.before["revision"],
        )
        assert enabled["mode"] == "use"
        assert enabled["comparison_verified_for_current_identity"] is True
        result = scenario.driver.query_army_strengths(
            expected_revision=scenario.before["revision"], _auto_core_only=True,
        )
        assert [frame["army_strengths_profile"] for frame in _queries(scenario)] == [
            "ordinary_core_v1", PROFILE, PROFILE,
        ]
        assert result["army_strengths_profile"] == "ordinary_core_v1"
        assert result["army_strengths"] == _private_rows()
        cached = scenario.driver._army_strength_cache_for_snapshot(
            scenario.before, episode_run_id=scenario.before["episode_run_id"],
        )
        assert cached["army_strengths"] == _private_rows()
        result["army_strengths"][0]["war_ids"].append(999)
        assert cached["army_strengths"] == _private_rows()
        explicit = scenario.driver.query_army_strengths(expected_revision=scenario.before["revision"])
        assert _queries(scenario)[-1]["army_strengths_profile"] == "ordinary_core_v1"
        assert "fixed_chunk0_preparation_inputs_v1" in explicit["army_strengths"][0]
        with pytest.raises(ValueError):
            scenario.driver.query_army_strengths(profile=PROFILE, expected_revision=scenario.before["revision"])
    finally:
        scenario.driver.close()


def test_compare_reads_same_frame_and_only_returns_exact_equal_scalar(tmp_path):
    scenario = make_scenario(tmp_path / "state")
    try:
        _advertise(scenario)
        _answer_private(scenario)
        scenario.driver.set_army_private_auto_scalar_ab_v1(
            "compare", expected_revision=scenario.before["revision"],
        )
        result = scenario.driver.query_army_strengths(
            expected_revision=scenario.before["revision"], _auto_core_only=True,
        )
        assert [frame["army_strengths_profile"] for frame in _queries(scenario)] == [
            "ordinary_core_v1", PROFILE,
        ]
        assert result["army_strengths"] == _private_rows()
        assert result["query_sequence"] == 1  # compare publishes old rich result
        assert result["queried_snapshot_id"] == scenario.before["snapshot_id"]
        assert result["queried_native_revision"] == scenario.before["native_revision"]
        status = scenario.driver.query_army_private_auto_scalar_ab_v1(
            expected_revision=scenario.before["revision"],
        )
        assert status["mode"] == "compare"
        assert status["comparison_verified_for_current_identity"] is True
    finally:
        scenario.driver.close()


@pytest.mark.parametrize("change,expected", [
    ("soldiers", "differs from same-frame rich projection"),
    ("missing_field", "malformed rows"),
])
def test_private_mismatch_or_malformed_row_rejects_without_cache(tmp_path, change, expected):
    scenario = make_scenario(tmp_path / "state")
    try:
        _advertise(scenario)
        _answer_private(scenario, change=change)
        scenario.driver.set_army_private_auto_scalar_ab_v1(
            "compare", expected_revision=scenario.before["revision"],
        )
        with pytest.raises(BridgeUnavailableError, match=expected):
            scenario.driver.query_army_strengths(
                expected_revision=scenario.before["revision"], _auto_core_only=True,
            )
        assert scenario.driver._army_strength_query is None
        assert scenario.driver._command_history[-1]["ok"] is False
        assert scenario.driver.query_army_private_auto_scalar_ab_v1(
            expected_revision=scenario.before["revision"],
        )["mode"] == "off"
    finally:
        scenario.driver.close()


def test_identity_change_revokes_use_before_private_query(tmp_path):
    scenario = make_scenario(tmp_path / "state")
    try:
        _advertise(scenario)
        _answer_private(scenario)
        scenario.driver.set_army_private_auto_scalar_ab_v1(
            "compare", expected_revision=scenario.before["revision"],
        )
        scenario.driver.query_army_strengths(
            expected_revision=scenario.before["revision"], _auto_core_only=True,
        )
        scenario.driver.set_army_private_auto_scalar_ab_v1(
            "use", expected_revision=scenario.before["revision"],
        )
        changed = deepcopy(scenario.before)
        changed["diagnostics"]["connection_generation"] += 1
        assert selected_mode(scenario.driver, changed) == "off"
        assert scenario.driver.query_army_private_auto_scalar_ab_v1(
            expected_revision=scenario.before["revision"],
        )["mode"] == "off"
    finally:
        scenario.driver.close()


def test_armed_comparison_never_rebinds_itself_to_a_new_actor(tmp_path):
    scenario = make_scenario(tmp_path / "state")
    try:
        _advertise(scenario)
        scenario.driver.set_army_private_auto_scalar_ab_v1(
            "compare", expected_revision=scenario.before["revision"],
        )
        changed = deepcopy(scenario.before)
        changed["played_character"]["character_id"] += 1
        assert selected_mode(scenario.driver, changed) == "off"
        assert scenario.driver.query_army_private_auto_scalar_ab_v1(
            expected_revision=scenario.before["revision"],
        )["comparison_verified_for_current_identity"] is False
    finally:
        scenario.driver.close()


def test_mcp_hook_changes_only_local_research_mode(tmp_path):
    scenario = make_scenario(tmp_path / "state")
    class Server:
        def __init__(self):
            self.tools = {}
            self.annotations = {}

        def tool(self, *, annotations=None):
            def install(function):
                self.tools[function.__name__] = function
                self.annotations[function.__name__] = annotations
                return function
            return install

    try:
        _advertise(scenario)
        _answer_private(scenario)
        server = Server()
        marker = object()
        register_tools(server, scenario.driver, marker)
        assert server.annotations["ck3_query_army_private_auto_scalar_ab_v1"] is marker
        before = len(scenario.endpoint.frames)
        configured = server.tools["ck3_set_army_private_auto_scalar_ab_v1"](
            "compare", scenario.before["revision"],
        )
        assert configured["mode"] == "compare"
        assert configured["business_actions_submitted"] == 0
        assert len(scenario.endpoint.frames) == before
        with pytest.raises(BridgeUnavailableError, match="source revision changed"):
            server.tools["ck3_set_army_private_auto_scalar_ab_v1"](
                "use", scenario.before["revision"] + 1,
            )
        status = server.tools["ck3_query_army_private_auto_scalar_ab_v1"](
            scenario.before["revision"],
        )
        assert status["mode"] == "compare"
        comparison = server.tools["ck3_compare_army_private_auto_scalar_ab_v1"](
            scenario.before["revision"],
        )
        assert server.annotations["ck3_compare_army_private_auto_scalar_ab_v1"] is marker
        assert comparison["status"] == "same_frame_equal"
        assert comparison["rich_result"]["query_sequence"] == 1
        assert comparison["control"]["comparison_verified_for_current_identity"] is True
        assert comparison["business_actions_submitted"] == 0
        assert [frame["army_strengths_profile"] for frame in _queries(scenario)] == [
            "ordinary_core_v1", PROFILE,
        ]
    finally:
        scenario.driver.close()
