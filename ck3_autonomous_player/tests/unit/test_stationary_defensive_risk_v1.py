"""Portable completed-response replay; Native I/O and Game are not called."""
from __future__ import annotations

import copy
import gzip
import json
from pathlib import Path

from xar_autoplayer import strategy


def _fixture() -> dict:
    with gzip.open(Path(__file__).parent / "fixtures/p42_stationary_unavailable_actual.json.gz", "rt", encoding="utf-8") as stream:
        return json.load(stream)


def _helper_case(fixture: dict, *, snapshot=None, rows=None, rejections=None,
                 cap_drop=None, step_drop=None, assaults=None, unsafe=None):
    snapshot = copy.deepcopy(fixture["snapshot"] if snapshot is None else snapshot)
    rows = copy.deepcopy(fixture["command_rows"] if rows is None else rows)
    rejections = copy.deepcopy(fixture["blocked_plan"]["route_rejections"] if rejections is None else rejections)
    army = snapshot["player_armies"][0]
    ids = tuple(sorted({enemy["army_id"] for war in snapshot["active_wars"]
                        for enemy in war["enemy_armies"] if enemy.get("retreating") is not True}))
    caps = set(fixture["capabilities"]["bridge_capabilities"])
    steps = set(fixture["capabilities"]["action_steps"])
    if cap_drop: caps.discard(cap_drop)
    if step_drop: steps.discard(step_drop)
    return strategy._stationary_timeline_unavailable_defensive_one_day_plan(
        rows, snapshot, army, current_province_id=2638, hostile_army_ids=ids,
        stationary_threats=fixture["blocked_plan"]["route_rejections"][0]["conflicts"],
        route_rejections=rejections, active_assaults=assaults or [],
        unsafe_armies=unsafe or [], available_steps=steps, available_capabilities=caps,
        war_summary=[{"war_id": war["war_id"]} for war in snapshot["active_wars"]],
    )


def test_actual_reconstructed_ordinary_choose() -> None:
    f = _fixture()
    # Every result is actual AUTO DTO content. Direct history row wrappers and
    # earlier indexes are reconstructed; this is no claim of raw Driver replay.
    plan = strategy.choose_one_life_turn(
        f["command_rows"], snapshot=f["snapshot"],
        action_steps=f["capabilities"]["action_steps"],
        bridge_capabilities=f["capabilities"]["bridge_capabilities"],
    )
    assert f["blocked_plan"]["phase"] == "native_war_no_safe_exact_route"
    assert plan["phase"] == "native_war_stationary_timeline_unavailable_defensive_one_day_observation"
    assert plan["selected_step"] == "life-advance-one-day"
    assert plan["defensive_risk_watch"]["contact_free_proven"] is False
    assert plan["defensive_risk_watch"]["in_day_contact_or_defeat_possible"] is True
    assert plan["defensive_risk_watch"]["movement_resubmitted"] is False
    assert plan["defensive_risk_watch"]["native_terminal_daily_sentinel_required"] is True


def test_exact_helper_and_negative_frames() -> None:
    f = _fixture()
    plan = _helper_case(f)
    assert plan is not None and plan["selected_step"] == "life-advance-one-day"
    assert plan["defensive_risk_watch"]["native_request_id"] == "step-445-a6d84939bbd5"

    mutations = (
        ("active_event", lambda s: s.__setitem__("active_event", {"instance_id": 1})),
        ("pending_interaction", lambda s: s.__setitem__("pending_character_interaction", {"instance_id": -2})),
        ("modal", lambda s: s.__setitem__("top_exclusive_modal_choice_hint", {"status": "present"})),
        ("terminal", lambda s: s.__setitem__("one_life_terminal", True)),
        ("combat", lambda s: s["player_armies"][0].__setitem__("in_combat", True)),
        ("retreat", lambda s: s["player_armies"][0].__setitem__("retreating", True)),
        ("moving", lambda s: s["player_armies"][0].__setitem__("route_province_ids", [2639])),
        ("enemy_scope", lambda s: s["active_wars"][1]["enemy_armies"].pop()),
        ("new_date", lambda s: s.__setitem__("date_raw", s["date_raw"] + 24)),
    )
    for name, mutation in mutations:
        snapshot = copy.deepcopy(f["snapshot"])
        mutation(snapshot)
        assert _helper_case(f, snapshot=snapshot) is None, name
    for name, kwargs in (
        ("no_arm", {"cap_drop": "game.command.research-arm-tactical-daily-sentinel-v1-N"}),
        ("no_cancel", {"cap_drop": "game.command.research-cancel-tactical-daily-sentinel-v1-generation-N"}),
        ("no_clock", {"step_drop": "life-advance-one-day"}),
        ("assault", {"assaults": [{"status": "active"}]}),
        ("unsafe_army", {"unsafe": [{"army_id": 428}]}),
        ("no_rejection", {"rejections": []}),
    ):
        assert _helper_case(f, **kwargs) is None, name
    wrong = copy.deepcopy(f["command_rows"])
    wrong[-1]["result"]["readonly_unavailable_evidence"]["native_command_result"]["error"] = "other native error"
    assert _helper_case(f, rows=wrong) is None
    wrong = copy.deepcopy(f["command_rows"])
    wrong[-1]["result"]["queried_revision"] += 1
    assert _helper_case(f, rows=wrong) is None
