"""One new whole-cash-wire to formal chooser case; authored, Root runs it.

Controlled production envelopes and existing construction fixtures are used.
No SDK, live process, game, native producer build or gameplay action is used.
"""

from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_construction_formal_private_consumer import Driver, root
from test_construction_monthly_budget_v1 import cash_fixture
from test_construction_economic_outcome_v1 import completed_receipt
from xar_autoplayer.bridge import domain_construction_private_transport_v1 as transport
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.bridge.war_cash_private_transport_v1 import CURRENT_STEP
from xar_autoplayer.construction_formal_consumer import (
    SUBMIT_STEP, plan_construction_private, read_construction_ledger,
    write_construction_ledger,
)
from xar_autoplayer import m5_formal_proposal_collector as m5_collector
from xar_autoplayer import m5_peacetime_proposal_sources_v1 as m5_sources


def test_current_cash_wire_drives_real_new_quote_decision_without_old_debit_or_baseline(tmp_path):
    class CashConstructionDriver(Driver):
        query_construction_cash_outcome_private_v1 = NativeHeadlessGameplayDriver.query_construction_cash_outcome_private_v1
        query_war_cash_current_resources_private_v1 = NativeHeadlessGameplayDriver.query_war_cash_current_resources_private_v1
        query_m5_joint_proposal_sources_private_v1 = NativeHeadlessGameplayDriver.query_m5_joint_proposal_sources_private_v1

        def take_internal_semantic_snapshot(self):
            return self.take_snapshot()

        def wait_for_command_result(self, request_id, timeout):
            request = self.requests[-1]
            if request["step"] != CURRENT_STEP:
                return super().wait_for_command_result(request_id, timeout)
            return {
                "type": "command_result", "protocol_version": 1,
                "request_id": request_id, "ok": True,
                "result": {
                    "step": CURRENT_STEP, "accepted": True, "status": "available",
                    "private_build": True, "read_only": True, "advertised": False,
                    "backend_id": "native-headless", "war_cash_current_resources": deepcopy(self.cash),
                },
            }

    observations = []
    for route, expenses, expected_step in (
        ("standalone", 380_000, SUBMIT_STEP),
        ("standalone", 20_450_000, "life-advance"),
        ("m5", 380_000, SUBMIT_STEP),
        ("m5", 20_450_000, "life-advance"),
    ):
        directory = tmp_path / f"{route}-{expenses}"
        directory.mkdir()
        driver = CashConstructionDriver(directory)
        driver.allow_private_construction_formal_trial = True
        driver.allow_private_m5_joint_collector = True
        driver.snapshot["diagnostics"] = {"hello": {
            "expected_ck3_version": CK3_12004.game_version,
            "expected_ck3_sha256": CK3_12004.executable_sha256,
        }}
        driver.cash = cash_fixture(gold=50_000_000, gross=450_000, expenses=expenses,
                                   current=200_000, all_raised=500_000)
        driver.cash.update(snapshot_revision=driver.snapshot["native_revision"],
                           date_raw=driver.snapshot["date_raw"])
        receipt = completed_receipt()
        receipt.update(
            action_request_id="controlled-old-building", actor_character_id=29829,
            episode_run_id=driver.snapshot["episode_run_id"],
            post_native_revision=2, post_date_raw=driver.snapshot["date_raw"] - 24,
            pre_date_raw=driver.snapshot["date_raw"] - 48,
            post_bridge_pid=4242, post_bridge_creation_date="controlled-process",
            completion_observed_date_raw=driver.snapshot["date_raw"] - 24,
            completion_last_check_date_raw=driver.snapshot["date_raw"] - 24,
            pre_player_monthly_gold_income_raw=None,
            observed_player_monthly_gold_income_raw=(None if route == "standalone" else 450_000),
            income_observed_date_raw=driver.snapshot["date_raw"] - 24,
        )
        # The completed previous building is in another barony. Its paid30M
        # is already in current50M treasury; new native quote is15M elsewhere.
        receipt["candidate"].update(
            barony_title_id=2174, province_id=2629, building_type_id=628, slot_index=1,
            stock_gold_cost_raw=30_000_000, gold_before_raw=80_000_000,
        )
        receipt["construction_province_income_observation"].update(
            barony_title_id=2174, province_id=2629,
            date_raw=receipt["completion_observed_date_raw"],
        )
        receipt["start_receipt"] = {
            "status": "applied", "postcondition_verified": True,
            "action_request_id": receipt["action_request_id"],
            "post_player_gold_raw": 50_000_000,
        }
        write_construction_ledger(directory, {
            "schema": "xar.ck3.construction_formal_pending_v1", "pending": None,
            "applied": receipt, "applied_prior": [],
        })
        baseline = {"revision": 3, "plan": {
            "policy": "one-life-turn-v1", "selected_step": "life-advance"}}
        history = root()
        history[0]["result"]["campaign_root_context"]["player_monthly_gold_income"]["raw"] = 450_000
        steps = {"life-advance", "query-campaign-root-context-v1", SUBMIT_STEP}
        with (
            patch.object(transport, "_identity", return_value=(4242, "controlled-process")),
            patch.object(m5_collector, "construction_process_identity", return_value=(4242, "controlled-process")),
            patch.object(m5_sources, "construction_process_identity", return_value=(4242, "controlled-process")),
        ):
            if route == "m5":
                selected = m5_collector.plan_m5_formal_query_only(
                    driver, baseline, snapshot=driver.take_snapshot(),
                    history=history, available_steps=steps,
                )["plan"]
            else:
                selected = plan_construction_private(
                    driver, baseline, driver.take_snapshot(), history, steps,
                )["plan"]
        assert selected["selected_step"] == expected_step
        if route == "m5":
            assert selected["phase"] == (
                "m5_joint_construction_typed_submit" if expected_step == SUBMIT_STEP
                else "m5_joint_construction_cash_budget_deferred")
            assert selected["m5_joint_query_only"]["dispatch"]["reservation"]["domain"] == "building"
            assert selected["m5_joint_formal_action_ready"] is (expected_step == SUBMIT_STEP)
        assert [request["step"] for request in driver.requests] == [CURRENT_STEP, transport.QUERY_NATIVE]
        assert driver.allow_private_war_cash_query is True
        assert selected["construction_cash_outcome"]["current_cash_scenarios"]["construction_gold_cost_raw"] == 0
        assert selected["construction_cash_outcome"]["current_cash_scenarios"]["scenarios"]["current"]["scenario_floor_ready"] is True
        consumed = selected["construction_receipt_consumed"]
        assert consumed["action_request_id"] == "controlled-old-building"
        assert consumed["observed_player_monthly_gold_income_raw"] == 450_000
        assert "pre_cash_v2" not in consumed
        assert consumed["post_cash_v2"]["current_treasury"]["raw"] == 50_000_000
        durable = read_construction_ledger(directory)["applied"]
        assert durable["action_request_id"] == consumed["action_request_id"]
        if route == "standalone":
            assert durable == consumed
        assert selected["construction_economic_outcome"]["readiness"]["player_net_monthly_change_ready"] is False
        assert selected["construction_economic_outcome"]["readiness"]["net_benefit_ready"] is False
        quote = selected["construction_private_query"]
        budget = quote["construction_monthly_budget"]
        assert quote["candidate"]["stock_gold_cost_raw"] == 15_000_000
        assert quote["status"] == "selected"
        assert quote["candidate"]["building_type_id"] == 24
        assert quote["world"]["native_final_legality_evaluated"] is True
        assert quote["pre_cash_v2"]["current_treasury"]["raw"] == 50_000_000
        assert budget["construction_gold_cost_raw"] == 15_000_000
        assert budget["scenarios"]["current"]["cash_after_construction_and_commitments_raw"] == 35_000_000
        assert budget["scenarios"]["current"]["scenario_floor_ready"] is (expected_step == SUBMIT_STEP)
        assert budget["existing_commitment_gold_raw"] == 0
        assert all(request["step"] != transport.ACTION_NATIVE for request in driver.requests)
        observations.append({"route": route, "expenses_raw": expenses, "selected_plan": selected,
                             "request_steps": [request["step"] for request in driver.requests]})
    output = Path(os.environ.get("XAR_G2_FORMAL_CASH_OUTPUT_DIR", str(tmp_path)))
    output.mkdir(parents=True, exist_ok=True)
    (output / "FORMAL-CASH-DECISION-OBSERVATIONS.json").write_text(
        json.dumps({"unique_cases": 1, "fixture_provenance": "controlled whole wire and real formal decision; no CK3/SDK/process query", "observations": observations}, indent=2),
        encoding="utf-8",
    )
