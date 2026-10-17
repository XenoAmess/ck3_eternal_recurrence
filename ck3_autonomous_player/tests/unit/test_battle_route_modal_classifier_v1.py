"""Real Driver producer -> modal helper with synthetic Native I/O and plan.

No private queue, Service.auto_turn, live game, pipe, or business result is tested.
Run directly or through unittest discovery; --source-root supports external tests.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest


SOURCE_ROOT = Path(__file__).resolve().parents[3]
HELPER_FILE = SOURCE_ROOT / "tools/root_battle_route_modal_classifier_v1.py"
OUTCOMES = []
NEGATIVE_CHECKS = []
CUNIT_ZERO = []


def load_file(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BattleRouteModalClassifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = load_file(Path(__file__).with_name("battle_route_modal_producer_fixture.py"),
                                "battle_route_modal_producer_fixture")
        cls.fixture.configure(SOURCE_ROOT)
        cls.helper = load_file(HELPER_FILE, "battle_route_modal_classifier_under_test")

    def test_actual_native_producer_four_boundaries_and_48_rejections(self):
        for scope in ("active_battle", "committed_route"):
            for kind, state in (("active_event", "idle"), ("pending_character_interaction", "triggered")):
                label = scope + ":" + kind + ":" + state
                with self.subTest(case=label):
                    body, startup_metrics, before_metrics, _, wire = self.fixture.producer(scope, kind, state)
                    # The actual producer publishes both snapshots; the startup
                    # baseline has six fields, and predates the plan frame.
                    fields = ("snapshot_id", "revision", "native_revision", "date_raw",
                              "actor_character_id", "episode_run_id")
                    startup = {key: startup_metrics[key] for key in fields}
                    self.assertEqual(len(startup), 6)
                    self.assertLess(startup["date_raw"], before_metrics["date_raw"])
                    self.assertEqual(before_metrics["native_revision"], 11)
                    self.assertGreater(before_metrics["revision"], startup["revision"])
                    self.assertNotEqual(before_metrics["revision"], before_metrics["native_revision"])
                    commands = [frame for frame in wire if frame.get("type") == "execute_step"]
                    self.assertEqual(commands[0]["step"], "set-speed-3")
                    self.assertEqual(commands[0]["expected_revision"], 11)
                    def classify(value):
                        return self.helper.classify(value, startup, 4242,
                            self.fixture.classify_gameplay_start_binding_v1, scope)
                    credit = classify(copy.deepcopy(body))
                    self.assertEqual(credit["category"], scope + "_player_decision_interrupted_observed")
                    self.assertEqual(credit["actual_elapsed_days"], 1)
                    self.assertEqual(credit["actual_date_delta_raw"], 24)
                    self.assertTrue(credit["typed_nonmaterial_observation"])
                    self.assertTrue(credit["paired_after_metrics_still_required"])
                    for key in ("primitive_accepted", "submitted_pending", "ui_action_credit", "action_credit",
                                "business_success_inferred", "material_verified", "replay_allowed"):
                        self.assertIs(credit[key], False, key)
                    mutations = {
                        "wrong_game": lambda b: b["result"].update(bridge_pid=1),
                        "public_native_swap": lambda b: b["planning_source_frame"].update(native_revision=b["planning_source_frame"]["revision"]),
                        "wrong_boundary": lambda b: b["result"]["player_decision_boundary"].update(instance_id=999),
                        "unpaused": lambda b: b["result"].update(paused=False),
                        "failed_postcondition": lambda b: b["result"].update(progress_status="postcondition_failed"),
                        "unknown_modal": lambda b: b["result"]["player_decision_boundary"].update(kind="unknown"),
                        "UI_action": lambda b: b["result"]["actions"].append({"step": "select-event-option-1", "result": {"accepted": True}}),
                        "wrong_generation": lambda b: b["result"]["tactical_daily_sentinel"].update(generation=999),
                        "bad_tick": lambda b: b["result"]["tactical_daily_sentinel"].update(completed_daily_ticks=99),
                        "war_scope": lambda b: b["plan"]["active_wars"][0].update(war_id=99),
                    }
                    if scope == "committed_route":
                        mutations.update(
                            incomplete_hostile=lambda b: b["plan"]["contact_horizon"].update(hostile_army_ids=[]),
                            margin_weakened=lambda b: b["plan"].update(friendly_current_soldiers=1499))
                    if state == "idle":
                        mutations["cancel_missing"] = lambda b: b["result"].update(player_decision_boundary_cancel=None)
                    else:
                        mutations["triggered_canceled"] = lambda b: b["result"].update(player_decision_boundary_cancel={"generation": 42})
                    for name, mutate in mutations.items():
                        with self.subTest(case=label, rejection=name):
                            bad = copy.deepcopy(body)
                            mutate(bad)
                            with self.assertRaises((ValueError, RuntimeError)):
                                classify(bad)
                            NEGATIVE_CHECKS.append(label + ":" + name)
                    OUTCOMES.append({"case": label, "startup_field_count": len(startup),
                        "current_public_native": [before_metrics["revision"], before_metrics["native_revision"]],
                        "category": credit["category"], "actual_elapsed_days": credit["actual_elapsed_days"],
                        "business_or_UI_credit": False, "replay_allowed": False})
        self.assertEqual(len(OUTCOMES), 4)
        self.assertEqual(len(NEGATIVE_CHECKS), 48)

    def test_public_cunit_zero_actual_native_producer(self):
        body, metrics, _, _, _ = self.fixture.producer("active_battle", "active_event", "idle", army_id=0)
        startup = {key: metrics[key] for key in ("snapshot_id", "revision", "native_revision", "date_raw",
                                               "actor_character_id", "episode_run_id")}
        credit = self.helper.classify(body, startup, 4242,
            self.fixture.classify_gameplay_start_binding_v1, "active_battle")
        self.assertEqual(body["result"]["watch_army_ids"], [0])
        self.assertEqual(credit["actual_elapsed_days"], 1)
        self.assertFalse(credit["business_success_inferred"])
        CUNIT_ZERO.append({"army_id": 0, "Driver_execute_step_exercised": True,
                           "category": credit["category"], "business_or_UI_credit": False})


def main():
    global SOURCE_ROOT, HELPER_FILE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=SOURCE_ROOT)
    parser.add_argument("--helper-file", type=Path)
    parser.add_argument("--receipt", type=Path)
    args, remaining = parser.parse_known_args()
    SOURCE_ROOT = args.source_root.resolve()
    HELPER_FILE = (args.helper_file or SOURCE_ROOT / "tools/root_battle_route_modal_classifier_v1.py").resolve()
    if args.receipt and args.receipt.exists():
        parser.error("receipt already exists; choose a new output")
    program = unittest.main(argv=[sys.argv[0], *remaining], exit=False)
    if args.receipt:
        digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
        result = {"schema": "xar.modal-consumer.portable-producer-test/v1",
            "at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "SOURCE_FIXTURE_GREEN_NOT_LIVE" if program.result.wasSuccessful() else "SOURCE_FIXTURE_RED",
            "cases": OUTCOMES, "negative_checks": NEGATIVE_CHECKS, "public_cunit_zero": CUNIT_ZERO,
            "Driver_execute_step_with_only_Native_IO_fake": True, "Service_auto_turn_exercised": False,
            "formal_queue_exercised": False, "Native_Game_or_MCP_calls": 0,
            "helper_sha256": digest(HELPER_FILE),
            "Driver_sha256": digest(SOURCE_ROOT / "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py"),
            "public_native_fixture_source_sha256": digest(SOURCE_ROOT / "ck3_autonomous_player/tests/unit/test_native_bridge_driver.py")}
        with args.receipt.open("x", encoding="utf-8") as file:
            json.dump(result, file, indent=2)
            file.write("\n")
    return 0 if program.result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
