from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.frontend_gui_route_contract import (
    QUERY_FRONTEND_GUI_ROUTE_V1_CAPABILITY,
)
from xar_autoplayer.bridge.service import GameplayBridgeService


def _route() -> dict[str, object]:
    return {
        "schema": "ck3-frontend-gui-route-v1",
        "schema_version": 1,
        "route": "coat_of_arms_designer",
        "accepted": True,
        "backend_id": "native-headless",
    }


def _tree() -> dict[str, object]:
    return {
        "schema": "ck3-frontend-coat-of-arms-tree-inspection-v1",
        "schema_version": 1,
        "status": "available",
        "root_available": True,
        "scope_root_name": "coat_of_arms_page",
    }


class _FramebufferDriver:
    def capabilities(self) -> dict[str, object]:
        return {
            "backend_id": "native-headless",
            "mode": "native-headless",
            "source": "injected-dll-named-pipe",
            "visual_fallback": False,
            "snapshot": True,
            "bridge_capabilities": [QUERY_FRONTEND_GUI_ROUTE_V1_CAPABILITY],
            "diagnostics": {
                "connected": True,
                "bridge_pid": 1234,
                "connection_generation": 7,
                "hello": {
                    "pid": 1234,
                    "connection_generation": 7,
                    "game_adapter_id": "ck3-1.19.0.6-msvc-x64",
                    "game_adapter_status": "ready",
                    "expected_ck3_version": "1.19.0.6",
                    "expected_ck3_sha256": (
                        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
                    ),
                    "ck3_build_match": True,
                    "capabilities": [QUERY_FRONTEND_GUI_ROUTE_V1_CAPABILITY],
                },
            },
        }


class CoatOfArmsFramebufferServiceTests(unittest.TestCase):
    def _service(self) -> GameplayBridgeService:
        service = GameplayBridgeService(_FramebufferDriver())
        service.query_frontend_gui_route_v1 = Mock(side_effect=[_route(), _route()])
        service.inspect_frontend_coat_of_arms_tree_v1 = Mock(
            side_effect=[_tree(), _tree()]
        )
        return service

    @patch(
        "xar_autoplayer.bridge.service.capture_and_compare_coat_of_arms_framebuffer_v1"
    )
    def test_comparison_is_bound_to_stable_route_pid_and_generation(
        self, capture: Mock
    ) -> None:
        capture.return_value = {
            "schema": "ck3-coat-of-arms-framebuffer-comparison-v1",
            "bridgePid": 1234,
            "readOnly": True,
            "usesOcr": False,
            "usesKeyboard": False,
            "usesMouse": False,
        }

        result = self._service().compare_frontend_coat_of_arms_framebuffer_v1(
            "reference", "A" * 64
        )

        capture.assert_called_once_with(1234, "reference", "A" * 64)
        self.assertTrue(result["routeStable"])
        self.assertEqual(result["route"], "coat_of_arms_designer")
        self.assertEqual(result["connectionGeneration"], 7)

    @patch(
        "xar_autoplayer.bridge.service.capture_and_compare_coat_of_arms_framebuffer_v1"
    )
    def test_route_drift_fails_closed(self, capture: Mock) -> None:
        capture.return_value = {"bridgePid": 1234}
        service = self._service()
        after = _route()
        after["route"] = "ruler_designer"
        service.query_frontend_gui_route_v1 = Mock(side_effect=[_route(), after])

        with self.assertRaisesRegex(BridgeUnavailableError, "binding changed"):
            service.compare_frontend_coat_of_arms_framebuffer_v1(
                "reference", "A" * 64
            )

    @patch("xar_autoplayer.bridge.service.prepare_ck3_framebuffer_capture_v1")
    def test_foreground_preparation_is_route_and_pid_bound(
        self, prepare: Mock
    ) -> None:
        prepare.return_value = {
            "schema": "ck3-coat-of-arms-framebuffer-preparation-v1",
            "bridgePid": 1234,
            "presentationOnly": True,
            "usesOcr": False,
            "usesKeyboard": False,
            "usesMouse": False,
        }

        result = self._service().prepare_frontend_coat_of_arms_framebuffer_v1()

        prepare.assert_called_once_with(1234)
        self.assertTrue(result["routeStable"])
        self.assertEqual(result["connectionGeneration"], 7)

    def test_two_state_calibration_is_bound_to_stable_route_pid_and_generation(
        self,
    ) -> None:
        service = self._service()
        service._coat_of_arms_framebuffer_calibrations_v2 = Mock()
        service._coat_of_arms_framebuffer_calibrations_v2.begin.return_value = {
            "schema": "ck3-coat-of-arms-framebuffer-calibration-stage-v2",
            "bridgePid": 1234,
            "usesOcr": False,
            "usesKeyboard": False,
            "usesMouse": False,
        }

        result = service.calibrate_frontend_coat_of_arms_framebuffer_v2(
            "corpus", "begin"
        )

        service._coat_of_arms_framebuffer_calibrations_v2.begin.assert_called_once_with(
            1234, "corpus"
        )
        self.assertTrue(result["routeStable"])
        self.assertEqual(result["connectionGeneration"], 7)

    def test_calibrated_comparison_is_bound_to_the_same_native_process(self) -> None:
        service = self._service()
        service._coat_of_arms_framebuffer_calibrations_v2 = Mock()
        service._coat_of_arms_framebuffer_calibrations_v2.compare.return_value = {
            "schema": "ck3-coat-of-arms-framebuffer-comparison-v2",
            "bridgePid": 1234,
            "usesOcr": False,
            "usesKeyboard": False,
            "usesMouse": False,
        }

        result = service.compare_frontend_coat_of_arms_framebuffer_v2(
            "corpus", "reference", "A" * 64
        )

        service._coat_of_arms_framebuffer_calibrations_v2.compare.assert_called_once_with(
            1234, "corpus", "reference", "A" * 64
        )
        self.assertTrue(result["routeStable"])
        self.assertEqual(result["connectionGeneration"], 7)

    def test_uv_calibration_and_comparison_are_bound_to_the_same_process(self) -> None:
        service = self._service()
        service._coat_of_arms_framebuffer_calibrations_v3 = Mock()
        service._coat_of_arms_framebuffer_calibrations_v3.anchors_complete.return_value = {
            "schema": "ck3-coat-of-arms-framebuffer-calibration-v3",
            "bridgePid": 1234,
            "usesOcr": False,
            "usesKeyboard": False,
            "usesMouse": False,
        }

        calibration = service.calibrate_frontend_coat_of_arms_framebuffer_v3(
            "corpus", "anchors_complete"
        )

        service._coat_of_arms_framebuffer_calibrations_v3.anchors_complete.assert_called_once_with(
            1234, "corpus"
        )
        self.assertTrue(calibration["routeStable"])
        self.assertEqual(calibration["connectionGeneration"], 7)

        service = self._service()
        service._coat_of_arms_framebuffer_calibrations_v3 = Mock()
        service._coat_of_arms_framebuffer_calibrations_v3.compare.return_value = {
            "schema": "ck3-coat-of-arms-framebuffer-comparison-v3",
            "bridgePid": 1234,
            "usesOcr": False,
            "usesKeyboard": False,
            "usesMouse": False,
        }

        comparison = service.compare_frontend_coat_of_arms_framebuffer_v3(
            "corpus", "reference", "A" * 64
        )

        service._coat_of_arms_framebuffer_calibrations_v3.compare.assert_called_once_with(
            1234, "corpus", "reference", "A" * 64
        )
        self.assertTrue(comparison["routeStable"])
        self.assertEqual(comparison["connectionGeneration"], 7)


if __name__ == "__main__":
    unittest.main()
