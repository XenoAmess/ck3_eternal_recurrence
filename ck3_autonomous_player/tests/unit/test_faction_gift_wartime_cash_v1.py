from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from xar_autoplayer import faction_gift_wartime_cash_v1 as cash
from xar_autoplayer.bridge import faction_gift_formal_route_v1 as route
from xar_autoplayer.m5_observed_opportunity_selector import observed_frame


ACTUAL = json.loads((Path(__file__).parent / "fixtures/c11_gift4276_applied4284.json").read_text(encoding="utf-8"))


def inputs(*, gold=100_000_000, wars=True):
    frame = ACTUAL["pre_frame"]
    candidate = deepcopy(ACTUAL["candidate"])
    candidate["observation"]["player_gold_raw"] = gold
    snapshot = {"snapshot_id": frame["snapshot_id"], "revision": frame["revision"],
        "native_revision": frame["native_revision"], "date_raw": frame["date_raw"],
        "episode_run_id": frame["episode_run_id"], "paused": True, "map_ready": True,
        "played_character": {"character_id": frame["actor_character_id"], "alive": True},
        "played_character_gold": {"raw": gold, "scale": 100000},
        "active_wars": [{"war_id": 16777278, "enemy_armies": []}] if wars else [],
        "diagnostics": {"bridge_pid": frame["bridge_pid"],
                        "connection_generation": frame["connection_generation"]}}
    root = {"status": "available", "player_character_id": frame["actor_character_id"],
        "snapshot_revision": frame["native_revision"], "date_raw": frame["date_raw"],
        "player_max_monthly_gold_maintenance_v1": {
            "status": "available", "value": {"raw": 500000, "scale": 100000}}}
    spending = {"status": "observed", "frame": {"actor_character_id": frame["actor_character_id"],
        "native_revision": frame["native_revision"], "date_raw": frame["date_raw"],
        "snapshot_id": frame["snapshot_id"]},
        "budget": {"reserved_raw": {"gold": 5000000}, "active_war_count": len(snapshot["active_wars"])}}
    # Synthetic complete native quote, only to exercise positive qualification;
    # the actual4276 source does not contain this market or these obligations.
    market = {"available": True, "actor_character_id": frame["actor_character_id"],
        "date_raw": frame["date_raw"], "rows": [{"company_id": 9, "employer_id": None,
            "final_terms": {"resource_costs_raw": [30000000] + [0] * 9,
                "resource_scale": 100000, "available": True, "can_hire": True, "can_afford": True},
            "troop_strength": {"available": True, "current_soldiers": 1800},
            "location": {"hire_auto_raise_province_id": 2630,
                "hire_auto_raise_position_ready": True, "hire_auto_raise_attempted_in_active_war": True},
            "readiness_v1": {"hire_ready": True}}]}
    kwargs = {"root": root, "spending": spending, "market": market,
        "market_source_frame": observed_frame(snapshot), "mercenary_ledger": {"pending": None}}
    return snapshot, candidate, kwargs


def test_actual4276_spend_fails_existing_military_floor_without_inventing_quote():
    snapshot, candidate, _ = inputs(gold=ACTUAL["candidate"]["observation"]["player_gold_raw"])
    result = cash.assess_faction_gift_wartime_cash_v1(snapshot, candidate)
    assert result["new_gift_spending_allowed"] is False
    assert result["reason"] == "wartime_gift_would_breach_military_cash_floor"
    assert result["gold_after_gift_raw"] == ACTUAL["post_receipt"]["post_player_gold_raw"] == 19727866
    assert "emergency_quote" not in result
    assert "required_remaining_gold_raw" not in result


def test_peace_and_complete_ample_war_cash_can_still_gift():
    snapshot, candidate, kwargs = inputs(wars=False)
    assert cash.assess_faction_gift_wartime_cash_v1(snapshot, candidate)["new_gift_spending_allowed"] is True
    snapshot, candidate, kwargs = inputs()
    result = cash.assess_faction_gift_wartime_cash_v1(snapshot, candidate, **kwargs)
    assert result["new_gift_spending_allowed"] is True
    assert result["required_remaining_gold_raw"] == 55000000
    assert result["arrival_or_victory_verified"] is False


@pytest.mark.parametrize("damage", ["war_scope", "root", "spending", "market", "old_market", "unknown_hire", "incomplete_cost", "not_affordable"])
def test_missing_current_inputs_defer_only_the_new_gift(damage):
    snapshot, candidate, kwargs = inputs()
    if damage == "war_scope":
        snapshot.pop("active_wars")
    elif damage in {"root", "spending", "market"}:
        kwargs[damage] = None
    elif damage == "old_market":
        kwargs["market_source_frame"] = {**kwargs["market_source_frame"], "native_revision": 1}
    elif damage == "unknown_hire":
        kwargs["mercenary_ledger"] = {"pending": {"status": "unknown"}}
    elif damage == "incomplete_cost":
        kwargs["market"]["rows"][0]["final_terms"]["resource_costs_raw"] = [30000000]
    else:
        kwargs["market"]["rows"][0]["final_terms"]["can_afford"] = False
    result = cash.assess_faction_gift_wartime_cash_v1(snapshot, candidate, **kwargs)
    assert result["status"] == "defer_new_gift"
    assert result["new_gift_spending_allowed"] is False
    if damage == "war_scope":
        assert result["reason"] == "current_war_scope_unobserved"


def test_emergency_quote_and_unpaid_commitments_are_reserved_after_gift():
    snapshot, candidate, kwargs = inputs(gold=64000000)
    result = cash.assess_faction_gift_wartime_cash_v1(snapshot, candidate, **kwargs)
    assert result["gold_after_gift_raw"] == 54000000
    assert result["required_remaining_gold_raw"] == 55000000
    assert result["new_gift_spending_allowed"] is False


def test_wrapper_reuses_budget_and_current_market_without_native_query(monkeypatch, tmp_path):
    from xar_autoplayer import activity_feast_stage5_budget_v1 as budget
    from xar_autoplayer import war_mercenary_consumer_v1 as mercenary
    snapshot, candidate, kwargs = inputs()
    monkeypatch.setattr(budget, "observe_feast_start_budget_v1", lambda *a, **kw: kwargs["spending"])
    monkeypatch.setattr(mercenary, "_context_with_reference", lambda history, snap:
        (kwargs["market"], {"source_frame": kwargs["market_source_frame"]}))
    monkeypatch.setattr(mercenary, "_ledger", lambda path: kwargs["mercenary_ledger"])
    def no_rpc(*args, **kw):
        raise AssertionError("cash review may not request a fresh native quote")
    driver = SimpleNamespace(state_dir=tmp_path, execute_step=no_rpc)
    result = cash.observe_faction_gift_wartime_cash_v1(driver, snapshot, candidate,
        root=kwargs["root"], history=[])
    assert result["new_gift_spending_allowed"] is True


def test_route_deferral_keeps_repeated_war_clock_turns_without_new_intent(monkeypatch, tmp_path):
    snapshot, candidate, kwargs = inputs(gold=29727866)
    monkeypatch.setattr(route, "read_faction_gift_ledger_v1", lambda state: {"pending": None})
    monkeypatch.setattr(route, "latest_same_frame_faction_root_v1",
        lambda *args: {"status": "targeting_present", "root": kwargs["root"]})
    monkeypatch.setattr(route, "observe_faction_gift_stock_threat_v1", lambda *args, **kw: deepcopy(ACTUAL["stock_threat"]))
    def no_checkpoint(*args):
        raise AssertionError("deferred gift must not ask for a checkpoint")
    monkeypatch.setattr(route, "_current_checkpoint", no_checkpoint)
    driver = SimpleNamespace(state_dir=tmp_path, query_faction_gift_private_candidate_v1=lambda **kw: candidate)
    original = {"revision": snapshot["revision"], "plan": {
        "phase": "native_war_no_safe_route_defensive_hold_progress", "selected_step": "life-advance"}}
    for _ in range(2):
        result = route.plan_faction_gift_private_v1(driver, deepcopy(original), snapshot, [], {"life-advance", "save-checkpoint"})
        assert result["plan"]["selected_step"] == "life-advance"
        assert result["plan"]["phase"] == original["plan"]["phase"]
        assert result["plan"]["faction_gift_spending_deferred_v1"]["new_gift_spending_authorized"] is False
        assert "faction_gift_action" not in result["plan"]
    assert list(tmp_path.iterdir()) == []


def test_already_pending_receipt_precedes_the_new_cash_guard(monkeypatch, tmp_path):
    snapshot, _, _ = inputs(gold=19727866)
    snapshot["native_revision"] = 27
    pending = {"pre_native_snapshot_revision": 26, "source_bridge_pid": 15512,
               "source_bridge_creation_date": "same-owner"}
    monkeypatch.setattr(route, "read_faction_gift_ledger_v1", lambda state: {"pending": pending})
    monkeypatch.setattr(route, "_runtime_identity", lambda driver: (15512, "same-owner"))
    def forbidden(*args, **kwargs):
        raise AssertionError("new spend guard must not requalify an already submitted gift")
    monkeypatch.setattr(cash, "observe_faction_gift_wartime_cash_v1", forbidden)
    planned = {"revision": snapshot["revision"], "plan": {"selected_step": "life-advance"}}
    result = route.plan_faction_gift_private_v1(SimpleNamespace(state_dir=tmp_path), planned, snapshot, [], set())
    assert result["plan"]["selected_step"] == route.RECEIPT_STEP
