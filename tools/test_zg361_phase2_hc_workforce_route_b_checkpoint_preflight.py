#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import zg361_phase2_hc_workforce_route_b_checkpoint_preflight as preflight  # noqa: E402


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


class RouteBCheckpointPreflightTests(unittest.TestCase):
    def test_green_is_explicitly_no_launch_and_live_pending(self) -> None:
        report = preflight.build_preflight()
        self.assertEqual("GREEN", report["result"])
        self.assertEqual("static-ready-live-pending", report["readiness"])
        self.assertTrue(all(report["checks"].values()))
        self.assertFalse(report["live_gate"]["ready"])
        self.assertTrue(
            all(value is False for value in report["no_launch_boundary"].values())
        )

    def test_contract_cannot_claim_numeric_cycle_case_before_provider(self) -> None:
        contract = json.loads(
            preflight.CONTRACT_PATH.read_text(encoding="utf-8")
        )
        altered = copy.deepcopy(contract)
        altered["case_identity_contract"]["cycle_case_available_before_action"] = True
        with tempfile.TemporaryDirectory(prefix="zg361-b4-route-b-preflight-") as name:
            path = Path(name) / "contract.json"
            write_json(path, altered)
            report = preflight.build_preflight(path)
        self.assertEqual("RED", report["result"])
        self.assertFalse(report["checks"]["contract_is_strict_and_live_pending"])
        self.assertFalse(report["no_launch_boundary"]["checkpoint_captured"])
        self.assertFalse(report["no_launch_boundary"]["postcondition_observed"])

    def test_missing_concrete_restore_method_is_red(self) -> None:
        with mock.patch.object(
            preflight.GameplayBridgeService, "restore_checkpoint", None
        ):
            report = preflight.build_preflight()
        self.assertEqual("RED", report["result"])
        self.assertFalse(
            report["checks"]["concrete_service_surface_matches_protocol"]
        )

    def test_cli_writes_green_report_without_launch(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zg361-b4-route-b-preflight-") as name:
            output = Path(name) / "preflight.json"
            completed = subprocess.run(
                [sys.executable, str(preflight.__file__), "--output", str(output)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        self.assertEqual("GREEN", report["result"])
        self.assertFalse(report["no_launch_boundary"]["ck3_started"])
        self.assertFalse(report["no_launch_boundary"]["checkpoint_restored"])

    def test_plumbing_has_no_launcher_surface(self) -> None:
        source = preflight.MODULE_PATH.read_text(encoding="utf-8")
        for forbidden in (
            "import subprocess",
            "from subprocess",
            "Start-Process",
            "ck3.exe",
            "GameplayBridgeService(",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
