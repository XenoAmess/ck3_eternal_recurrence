"""One new connected Service camera check; no desktop or Game calls."""
from copy import deepcopy
import unittest
from unittest.mock import patch

from test_war_hotspot_camera_peace_anchor_v1 import frame, observed_root
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.war_hotspot_camera import LandedProvinceIndex
from xar_autoplayer.bridge.title_map_navigation_contract import CENTER_MAP_ON_LANDED_TITLE_V1_CAPABILITY


class _Driver:
    def __init__(self, history):
        self.history = history

    def _with_internal_planning_view(self, snapshot, callback):
        return callback(snapshot, self.history)


class _CameraService(GameplayBridgeService):
    def __init__(self, snapshot, *, cached=False, cross_episode=False):
        self.frame = deepcopy(snapshot)
        self.frame.update(episode_run_id="actual-fixture-episode", diagnostics={
            "bridge_pid": 314, "connection_generation": 2})
        root = observed_root(self.frame)
        self.driver = _Driver([{"command": "query-campaign-root-context-v1",
                                "ok": True, "result": root}] if cached else [])
        self._war_hotspot_camera_index = LandedProvinceIndex(
            {12: "b_observed_capital", 34: "b_observed_battle"}, {}, ())
        self._war_hotspot_camera_index_error = None
        self.cross_episode = cross_episode
        self.root_queries = []
        self.centers = []

    def capabilities(self):
        return {"bridge_capabilities": [CENTER_MAP_ON_LANDED_TITLE_V1_CAPABILITY]}

    def snapshot(self, *, include_native_command_history=True):
        assert include_native_command_history is False
        return deepcopy(self.frame)

    def query_campaign_root_context_v1(self, *, expected_revision):
        self.root_queries.append(expected_revision)
        result = observed_root(self.frame)
        if self.cross_episode:
            self.frame["episode_run_id"] = "different-episode"
        return result

    def center_map_on_landed_title_v1(self, title_key, *, expected_revision):
        self.centers.append((title_key, expected_revision))
        return {"status": "centered", "title": {"key": title_key},
                "camera_center": {"postcondition_verified": True}}


class CameraServiceRootAnchorV1Test(unittest.TestCase):
    def test_real_service_hook_queries_reuses_and_rejects_crossed_frame(self):
        with patch("xar_autoplayer.bridge.camera_cursor_parking.park_foreground_ck3_cursor",
                   return_value={"status": "parked", "fixture_only": True}):
            for cached in (False, True):
                with self.subTest(cached=cached):
                    service = _CameraService(frame(), cached=cached)
                    result = service._follow_war_hotspot_before_turn()
                    self.assertEqual(result["hotspot"]["reason"], "player_capital")
                    self.assertEqual(service.root_queries, [] if cached else [21])
                    self.assertEqual(service.centers, [("b_observed_capital", 21)])

            war = frame()
            war["active_wars"] = [{"war_id": 9, "allied_armies": [{
                "army_id": 0, "controllable": True, "in_combat": True,
                "current_province_id": 34}]}]
            service = _CameraService(war)
            result = service._follow_war_hotspot_before_turn()
            self.assertEqual(result["hotspot"]["army_id"], 0)
            self.assertEqual(service.root_queries, [])
            self.assertEqual(service.centers, [("b_observed_battle", 21)])

            service = _CameraService(frame(), cross_episode=True)
            result = service._follow_war_hotspot_before_turn()
            self.assertEqual(result["status"], "unavailable")
            self.assertIn("crossed its observed frame", result["reason"])
            self.assertEqual(service.root_queries, [21])
            self.assertEqual(service.centers, [])

            service = _CameraService(frame())
            error = BridgeUnavailableError("native camera root unavailable")
            diagnostic = {"stage": "fixture-root-capture", "expected_revision": 21}
            error.native_command_result_frame = {"result": {"typed_query_failure_v1": diagnostic}}
            with patch.object(service, "query_campaign_root_context_v1", side_effect=error):
                result = service._follow_war_hotspot_before_turn()
            self.assertEqual(result["typed_query_failure_v1"], diagnostic)
            self.assertEqual(service.centers, [])


if __name__ == "__main__":
    unittest.main()
