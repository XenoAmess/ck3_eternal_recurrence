#!/usr/bin/env python3

from __future__ import annotations

import unittest
from unittest import mock

import preflight_zg361_phase2_hc_workforce_route_b_capture as preflight


class RouteBCapturePreflightTests(unittest.TestCase):
    def test_preflight_is_static_green_and_never_launches_ck3(self) -> None:
        with mock.patch.object(
            preflight.runner, "start_phase2_native_session_supervisor"
        ) as start, mock.patch.object(
            preflight.runner, "launch_native_ck3"
        ) as legacy_launch, mock.patch.object(
            preflight.runner, "NativeHeadlessGameplayDriver"
        ) as driver:
            report = preflight.run_preflight()

        self.assertEqual("GREEN", report["result"])
        self.assertEqual("static-ready-live-pending", report["readiness"])
        self.assertFalse(report["ck3_started"])
        self.assertFalse(report["service_instantiated"])
        self.assertFalse(report["checkpoint_created"])
        self.assertFalse(report["registry_created"])
        self.assertFalse(report["provider_live_result_claimed"])
        self.assertFalse(report["live_gate_ready"])
        self.assertTrue(all(report["checks"].values()))
        start.assert_not_called()
        legacy_launch.assert_not_called()
        driver.assert_not_called()


if __name__ == "__main__":
    unittest.main()
