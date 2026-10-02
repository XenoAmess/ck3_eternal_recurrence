"""Public CUnit slot zero stays observable and executable across core contracts."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player/src"))
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, BridgeUnavailableError
from xar_autoplayer.bridge import war_contract as war
from xar_autoplayer.bridge.service import GameplayBridgeService
from test_native_bridge_driver import FakeEndpoint, _army, _hello, _snapshot, _war, _army_strength

BOOTSTRAP = ROOT / "promo/ck3_native_war_ai/episode-03-siege/tools/capture_bootstrap.py"
spec = importlib.util.spec_from_file_location("episode03_unit_zero_bootstrap", BOOTSTRAP)
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


class PublicCUnitCoreContractTests(unittest.TestCase):
    def test_strength_query_keeps_zero_carmy_with_exact_scope_and_frame(self):
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(endpoint=endpoint)
        self.addCleanup(driver.close)
        player = _army(0)
        endpoint.publish(_hello("game.state.snapshot", war.QUERY_ARMY_STRENGTHS_CAPABILITY))
        endpoint.publish(_snapshot(40, played_character={"character_id": 707, "alive": True},
            player_armies=[player], active_wars=[_war(42, allied_armies=[player])]))
        row = {**_army_strength(0, "player", [42]), "native_carmy_id": 0}
        def answer(frame):
            if frame.get("type") == "execute_step":
                endpoint.publish({"type": "command_result", "protocol_version": 1,
                    "request_id": frame["request_id"], "ok": True,
                    "result": {"step": frame["step"], "accepted": True,
                               "status": "available", "query_sequence": 7,
                               "army_strengths": [row]}})
        endpoint.send_hook = answer
        start = driver.take_snapshot()
        service = GameplayBridgeService(driver)
        result = service.query_army_strengths([0], expected_revision=start["revision"])
        self.assertEqual(result["army_strengths"][0]["native_carmy_id"], 0)
        self.assertEqual(result["army_strengths"][0]["war_ids"], [42])
        self.assertEqual(result["status"], "available")
        self.assertEqual(driver.take_snapshot()["snapshot_id"], start["snapshot_id"])
        self.assertEqual(driver.take_snapshot()["date_raw"], start["date_raw"])
        self.assertEqual(len([f for f in endpoint.frames if f.get("type") == "execute_step"]), 1)

    def test_zero_round_trips_every_basic_army_literal(self):
        for build, parse, args in (
            (war.move_army_step, war.parse_move_army_step, (0, 20)),
            (war.preview_move_army_step, war.parse_preview_move_army_step, (0, 20)),
            (war.disband_army_step, war.parse_disband_army_step, (0,)),
            (war.split_army_half_step, war.parse_split_army_half_step, (0,)),
            (war.merge_armies_step, war.parse_merge_armies_step, (0, 7)),
            (war.merge_armies_step, war.parse_merge_armies_step, (7, 0)),
        ):
            with self.subTest(build=build.__name__, args=args):
                self.assertEqual(parse(build(*args)), args if len(args) > 1 else args[0])
        self.assertIsNone(war.parse_merge_armies_step("merge-armies-0-with-0"))
        with self.assertRaises(ValueError):
            war.merge_armies_step(0, 0)

    def test_invalid_unit_types_ranges_and_grammar_still_fail(self):
        for invalid in (True, False, -1, 2**31, 0.0, "0", None):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                war.preview_move_army_step(invalid, 20)
        for token in ("-1", "00", "+0", "2147483648", "true", "０", "0 "):
            with self.subTest(token=token):
                self.assertIsNone(war.parse_preview_move_army_step(f"preview-move-army-{token}-to-20"))
                self.assertIsNone(war.parse_disband_army_step(f"disband-army-{token}"))
        for province in (0, -1, True, 2**31):
            with self.subTest(province=province), self.assertRaises(ValueError):
                war.preview_move_army_step(0, province)
        for siege in (0, False, -1):
            with self.subTest(siege=siege), self.assertRaises(ValueError):
                war.start_assault_step(siege)

    def test_route_zero_subject_and_zero_hostile_keep_exact_scope(self):
        for args in ((0, 20, (7, 8)), (7, 20, (0, 8))):
            with self.subTest(args=args):
                step = war.query_route_contact_horizon_step(*args)
                self.assertEqual(war.parse_query_route_contact_horizon_step(step), args)
        for step in ("query-route-contact-horizon-v1-0-to-20-h-1-0",
                     "query-route-contact-horizon-v1-7-to-20-h-2-0-0",
                     "query-route-contact-horizon-v1-7-to-0-h-1-0",
                     "query-route-contact-horizon-v1-7-to-20-h-1-00"):
            self.assertIsNone(war.parse_query_route_contact_horizon_step(step))

    def test_zero_sentinel_literals_keep_positive_war_province_date(self):
        step = war.committed_route_sentinel_advance_step(0, 20, 24)
        self.assertEqual(war.parse_committed_route_sentinel_advance_step(step), (0, 20, 24))
        step = war.war_objective_hold_sentinel_advance_step(1, 0, 20, 24)
        self.assertEqual(war.parse_war_objective_hold_sentinel_advance_step(step), (1, 0, 20, 24))
        self.assertIsNone(war.parse_war_objective_hold_sentinel_advance_step(step.replace("war-1", "war-0")))

    def test_actual_driver_snapshot_advertises_zero_without_filtering_owner(self):
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(endpoint=endpoint)
        self.addCleanup(driver.close)
        endpoint.publish(_hello("game.state.snapshot", war.MOVE_ARMY_CAPABILITY,
            war.PREVIEW_MOVE_ARMY_CAPABILITY, war.DISBAND_ARMY_CAPABILITY,
            war.SPLIT_ARMY_HALF_CAPABILITY, war.MERGE_ARMIES_CAPABILITY))
        endpoint.publish(_snapshot(player_armies=[_army(0, province_id=10),
            _army(7, province_id=10), _army(8, province_id=20, controllable=False)],
            active_wars=[_war(enemy_armies=[_army(8, province_id=20, controllable=False)])]))
        snapshot = driver.take_snapshot()
        self.assertEqual([a["army_id"] for a in snapshot["player_armies"]], [0, 7, 8])
        steps = driver.capabilities()["action_steps"]
        for expected in ("preview-move-army-0-to-20", "move-army-0-to-20",
                         "disband-army-0", "split-army-half-0",
                         "merge-armies-0-with-7", "merge-armies-7-with-0"):
            self.assertIn(expected, steps)
        self.assertNotIn("disband-army-8", steps)
        self.assertNotIn("merge-armies-0-with-0", steps)

    def test_root_raw_receipt_bypasses_projection_and_preserves_rejection(self):
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(endpoint=endpoint)
        self.addCleanup(driver.close)
        endpoint.publish(_hello("game.state.snapshot"))
        frame = _snapshot(player_armies=[_army(0)])
        endpoint.publish(frame)
        sent = copy.deepcopy(endpoint.frames)
        before = driver.state.public_revision()
        receipt = bootstrap.root_raw_transport_snapshot(driver, {})
        self.assertEqual(receipt["native_packet"], frame)
        self.assertTrue(receipt["semantic_packet_accepted"])
        self.assertEqual(receipt["runtime_identity"]["sys_executable"], sys.executable)
        self.assertIn("xar_autoplayer.bridge.native_driver",
                      receipt["runtime_identity"]["loaded_xar_autoplayer_modules"])
        receipt["native_packet"]["state"]["player_armies"][0]["army_id"] = 8
        self.assertEqual(driver.state.raw_transport_snapshot()["native_packet"], frame)
        rejected = copy.deepcopy(frame)
        rejected["state"]["player_armies"][0]["army_id"] = -1
        endpoint.publish(rejected)
        receipt = bootstrap.root_raw_transport_snapshot(driver, {})
        self.assertFalse(receipt["semantic_packet_accepted"])
        self.assertEqual(receipt["native_packet"], rejected)
        self.assertEqual(driver.state.public_revision(), before)
        self.assertEqual(endpoint.frames, sent)
        with self.assertRaises(ValueError):
            bootstrap.root_raw_transport_snapshot(driver, {"step": "move-army-0-to-20"})
        endpoint.error = "fixture fatal transport"
        with self.assertRaises(ValueError):
            bootstrap.root_raw_transport_snapshot(driver, {})
        endpoint.error = None
        driver.state.mark_disconnected()
        with self.assertRaises(BridgeUnavailableError):
            bootstrap.root_raw_transport_snapshot(driver, {})


if __name__ == "__main__":
    unittest.main()
