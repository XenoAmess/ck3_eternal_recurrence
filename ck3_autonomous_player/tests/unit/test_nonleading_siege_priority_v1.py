"""Future RAM candidate, using real Strategy functions and a closed Native DTO.

Only the unchanged portable695 row is actual. Every nonleading/stationary siege
variant below is explicitly synthetic, changing existing DTO fields only. These
checks confer no live siege, move, battle, spending, or title-retention credit.
"""
from __future__ import annotations

from contextlib import contextmanager
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys
import types

import pytest

from tools.g2_saved_campaign.transform_nonleading_siege_priority_v1 import (
    BASE_SHA256, transform_strategy_bytes,
)
from xar_autoplayer.nonleading_player_realm_siege_v1 import (
    nonleading_player_realm_siege_v1,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/xar_autoplayer/strategy.py"
ACTUAL = ROOT / "tests/fixtures/portable_actual_695.json.gz"
ACTUAL_SHA = "da619ee770f2a4c124e9e625a9acc6913b2af96b8b1ab2af90896a67bd5e2937"


@contextmanager
def installed(module):
    import xar_autoplayer
    name = "xar_autoplayer.strategy"
    prior = sys.modules.get(name)
    prior_attribute = getattr(xar_autoplayer, "strategy", None)
    sys.modules[name] = module
    xar_autoplayer.strategy = module
    try:
        yield module
    finally:
        if prior is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = prior
        if prior_attribute is None:
            delattr(xar_autoplayer, "strategy")
        else:
            xar_autoplayer.strategy = prior_attribute


def load_ram(source):
    module = types.ModuleType("xar_autoplayer.strategy")
    module.__package__ = "xar_autoplayer"
    module.__file__ = str(SOURCE)
    with installed(module):
        exec(compile(source, str(SOURCE), "exec"), module.__dict__)
    return module


@pytest.fixture(scope="module")
def models():
    # The large original is read once; both versions compile from these RAM bytes.
    original = SOURCE.read_bytes()
    assert hashlib.sha256(original).hexdigest() == BASE_SHA256
    candidate = transform_strategy_bytes(original)
    assert transform_strategy_bytes(candidate, inverse=True) == original
    return load_ram(original), load_ram(candidate), original, candidate


@pytest.fixture
def actual():
    data = ACTUAL.read_bytes()
    assert hashlib.sha256(data).hexdigest() == ACTUAL_SHA
    return json.loads(gzip.decompress(data))


def synthetic(actual):
    case = copy.deepcopy(actual)
    snapshot = case["snapshot"]
    war = snapshot["active_wars"][0]
    assert war["war_id"] == 100663323
    war["player_is_primary_war_leader"] = False
    for enemy in war["enemy_armies"]:
        # All keys preexist in the actual Native DTO; do not invent Army fields.
        assert {"siege_province_in_player_subrealm", "move_target_province_id",
                "route_province_ids", "route_read_status"}.issubset(enemy)
        enemy.update(siege_province_in_player_subrealm=True,
                     move_target_province_id=None, route_province_ids=[],
                     route_read_status="complete_empty")
    return case


def assessment(module, case, *, controlled=None):
    snapshot = case["snapshot"]
    army = snapshot["player_armies"][0]
    with installed(module):
        return module._primary_defender_siege_relief_assessment(
            snapshot, commands=case["history_rows"],
            active_wars=snapshot["active_wars"],
            controlled_armies=[army] if controlled is None else controlled,
            pursuit_army=army,
        )


def choose(module, case):
    with installed(module):
        return module.choose_one_life_turn(
            case["history_rows"], snapshot=case["snapshot"],
            action_steps=case["action_steps"],
            bridge_capabilities=case["bridge_capabilities"],
            battle_speed_readiness=case["battle_speed_readiness"],
        )


def not_move(plan):
    assert not str(plan.get("selected_step")).startswith("move-army-"), plan


def no_termination_query_channel(case):
    """Synthetic capability variant, not a production configuration change.

    The all-capability variant below must retain its prior termination query.
    With that unrelated readonly channel absent, exercise the genuine ordinary
    planner's existing fall-through into tactical assessment. No results,
    terms, historical permissions, or current native legality are fabricated.
    """
    result = copy.deepcopy(case)
    result["action_steps"] = [step for step in result["action_steps"]
                              if not step.startswith("query-war-termination-options-")]
    return result


def test_exact_inverse_and_drift_refusal(models):
    _, _, original, candidate = models
    assert original != candidate
    with pytest.raises(ValueError, match="preimage"):
        transform_strategy_bytes(original + b"\n")
    with pytest.raises(ValueError):
        transform_strategy_bytes(candidate.replace(b"qualifying defensive", b"changed defensive"), inverse=True)


def test_actual_primary_behavior_is_unchanged(models, actual):
    before, after, _, _ = models
    assert assessment(before, actual) == assessment(after, actual)
    assert choose(before, actual) == choose(after, actual)


def test_nonleading_real_dto_fields_admit_forecast_not_move(models, actual):
    before, after, _, _ = models
    case = synthetic(actual)
    war = case["snapshot"]["active_wars"][0]
    assert nonleading_player_realm_siege_v1(case["snapshot"], war, war["enemy_armies"][0])
    assert assessment(before, case)["status"] == "not_applicable"
    result = assessment(after, case)
    assert result["status"] == "forecast_required", result
    assert result["war_id"] == war["war_id"]
    assert result["reason"] == "qualified_same_frame_combat_forecast_required_for_siege_contact"
    first = choose(after, case)
    assert first["phase"] == "native_war_termination_query", first
    assert first == choose(before, case)  # Existing higher-priority read survives.
    plan = choose(after, no_termination_query_channel(case))
    assert plan.get("siege_relief", {}).get("war_id") == war["war_id"], plan
    assert plan["phase"] == "native_war_siege_forecast_route_preview", plan
    assert plan["selected_step"] == "preview-move-army-167772577-to-2619", plan
    not_move(plan)


@pytest.mark.parametrize("primary,selected", [
    (True, "preview-move-army-167772577-to-2628"),
    (False, "move-army-167772577-to-2628"),
])
def test_preview_retarget_preserves_primary_and_typed_move(models, actual, primary, selected):
    case = synthetic(actual)
    case["snapshot"]["active_wars"][0]["player_is_primary_war_leader"] = primary
    baseline = {"phase": "native_war_route_preview", "selected_step": selected,
                "route_preview": {"target_province_id": 2628}}
    with installed(models[1]):
        result = models[1]._primary_defender_siege_forecast_ingress(
            baseline, commands=case["history_rows"], snapshot=case["snapshot"],
            action_steps=set(case["action_steps"]),
            bridge_capabilities=set(case["bridge_capabilities"]),
        )
    assert result is baseline


@pytest.mark.parametrize("change", [
    "external", "unknown_subrealm", "own_army", "no_native", "moving_enemy",
    "wrong_snapshot_id", "disconnected", "foreign_actor", "bool_score",
])
def test_nonleading_scope_rejects_unqualified_sources(models, actual, change):
    case = synthetic(actual)
    snapshot = case["snapshot"]
    war = snapshot["active_wars"][0]
    enemy = war["enemy_armies"][0]
    if change == "external": enemy["siege_province_in_player_subrealm"] = False
    elif change == "unknown_subrealm": enemy["siege_province_in_player_subrealm"] = None
    elif change == "own_army": enemy["owner_character_id"] = snapshot["played_character"]["character_id"]
    elif change == "no_native": enemy["source"] = "synthetic_or_unknown"
    elif change == "moving_enemy": enemy.update(move_target_province_id=2623, route_province_ids=[2623])
    elif change == "wrong_snapshot_id": snapshot["snapshot_id"] = "native:old"
    elif change == "disconnected": snapshot["diagnostics"]["connected"] = False
    elif change == "foreign_actor": snapshot["played_character"]["alive"] = False
    elif change == "bool_score": war["player_relative_war_score"] = True
    assert not nonleading_player_realm_siege_v1(snapshot, war, enemy)
    # A second qualifying enemy must not turn this outside/unknown enemy into
    # a target merely because it shares the same War.
    with installed(models[1]):
        assert not models[1]._defender_siege_is_relief_relevant(snapshot, war, enemy)


def test_detached_historical_rows_are_not_current_members(models, actual):
    case = synthetic(actual)
    snapshot = case["snapshot"]
    war = snapshot["active_wars"][0]
    assert not nonleading_player_realm_siege_v1(snapshot, copy.deepcopy(war), war["enemy_armies"][0])
    assert not nonleading_player_realm_siege_v1(snapshot, war, copy.deepcopy(war["enemy_armies"][0]))


def test_missing_native_strength_keeps_existing_observation_guard(models, actual):
    after = models[1]
    case = synthetic(actual)
    # The real strength-cache producer owns revision invalidation. This
    # component consumes native row status, not an invented metadata gate.
    case["snapshot"]["army_strengths_status"] = "partial"
    for row in case["snapshot"]["army_strengths"]:
        if row.get("scope_role") == "active_war_enemy" and 100663323 in row["war_ids"]:
            row.update(status="unavailable", current_soldiers=None,
                       maximum_soldiers=None, ai_base_power_raw=None)
    result = assessment(after, case)
    assert result["status"] == "observation_unavailable", result
    not_move(choose(after, case))


def test_no_control_and_weak_army_without_route_do_not_force_move(models, actual):
    after = models[1]
    case = synthetic(actual)
    assert assessment(after, case, controlled=[])["status"] == "not_applicable"
    for row in case["snapshot"]["army_strengths"]:
        if row.get("scope_role") == "player":
            row.update(current_soldiers=1, ai_base_power_raw=1)
    result = assessment(after, case)
    assert result["status"] == "forecast_required", result
    # Counts alone still do not authorize contact; no route/contact/v3 was supplied.
    plan = choose(after, no_termination_query_channel(case))
    not_move(plan)
    assert plan["phase"] == "native_war_siege_forecast_route_preview", plan


def test_unknown_current_move_intent_is_not_reissued(models, actual):
    after = models[1]
    case = synthetic(actual)
    army = case["snapshot"]["player_armies"][0]
    army.update(army_state="moving", army_state_code=7,
                move_target_province_id=2619, route_province_ids=[2619],
                route_read_status="complete_nonempty")
    result = assessment(after, case)
    assert result["status"] == "observation_unavailable", result
    assert result["required_observation"] == "complete-matching-active-native-move-intent-route"
    plan = choose(after, case)
    not_move(plan)
    assert plan["phase"] == "native_war_termination_query", plan
    without_termination = no_termination_query_channel(case)
    before = choose(models[0], without_termination)
    assert before["phase"] == "native_war_route_contact_horizon", before
    plan = choose(after, without_termination)
    assert plan.get("selected_step") is None, plan


def test_mandatory_event_still_precedes_defence(models, actual):
    before, after, _, _ = models
    case = synthetic(actual)
    case["snapshot"]["active_event"] = {"instance_id": 44, "option_count": 2}
    case["action_steps"] += ["select-event-option-1", "select-event-option-2"]
    original = choose(before, case)
    candidate = choose(after, case)
    assert candidate == original
    not_move(candidate)
    assert "event" in candidate.get("phase", ""), candidate
