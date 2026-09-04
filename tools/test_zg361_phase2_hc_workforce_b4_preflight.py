#!/usr/bin/env python3
"""Static tests for the B4 ``hc-workforce`` no-launch action contract."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import zg361_phase2_hc_workforce_b4_preflight as preflight  # noqa: E402


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def seed_fixture(root: Path) -> Path:
    save = root / "xar_checkpoint.ck3"
    save.write_bytes(b"phase-two-b4-hc-workforce-seed")
    contract = {
        "schema_version": 1,
        "kind": "zg361_phase2_paused_seed",
        "status": "ready",
        "ready": True,
        "source": {
            "absolute_save": str(save),
            "bytes": save.stat().st_size,
            "sha256": hashlib.sha256(save.read_bytes()).hexdigest(),
        },
        "provenance": {"source_git_commit": "a" * 40},
        "runtime": {
            "game_version": "1.19.0.6",
            "executable_sha256": "b" * 64,
        },
        "saved_state": {
            "date_raw": 53146920,
            "played_character_id": 29037,
            "paused_on_load": True,
            "map_ready": True,
        },
        "domain_query_matrix": {"workforce_owner_character_id": 32904},
    }
    path = root / "seed.json"
    write_json(path, contract)
    return path


class B4HCWorkforcePreflightTests(unittest.TestCase):
    def test_green_preflight_selects_real_route_b_but_keeps_live_pending(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zg361-b4-hc-workforce-") as name:
            report = preflight.build_preflight(
                seed_contract_path=seed_fixture(Path(name))
            )
        self.assertEqual("GREEN", report["result"])
        self.assertEqual("static-ready-live-pending", report["readiness"])
        self.assertEqual(
            {
                "event_definition_key": "zg361we.360",
                "route": "B",
                "native_option_index": 1,
                "option_number": 2,
            },
            {
                key: report["selected_action"][key]
                for key in (
                    "event_definition_key",
                    "route",
                    "native_option_index",
                    "option_number",
                )
            },
        )
        self.assertTrue(all(report["checks"].values()))
        self.assertTrue(report["seed_entry"]["entry_ready"])
        self.assertFalse(report["seed_entry"]["is_pre_action_checkpoint"])
        self.assertFalse(report["live_gate"]["ready"])
        self.assertIn("pre-zg361we.360", " ".join(report["live_gate"]["blockers"]))
        self.assertEqual(
            list(preflight.EXPECTED_POSTCONDITION_FACTS),
            report["selected_action"]["required_postcondition_facts"],
        )

    def test_ack_never_becomes_a_business_postcondition(self) -> None:
        contract = json.loads(preflight.CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertFalse(contract["action_cell"]["action_ack_is_business_receipt"])
        self.assertTrue(
            contract["action_cell"]["provider_observed_postcondition_required"]
        )
        with tempfile.TemporaryDirectory(prefix="zg361-b4-hc-workforce-") as name:
            root = Path(name)
            seed = seed_fixture(root)
            altered = copy.deepcopy(contract)
            altered["action_cell"]["action_ack_is_business_receipt"] = True
            contract_path = root / "bad-contract.json"
            write_json(contract_path, altered)
            report = preflight.build_preflight(
                contract_path=contract_path,
                seed_contract_path=seed,
            )
        self.assertEqual("RED", report["result"])
        self.assertFalse(report["no_launch_boundary"]["business_postcondition_claimed"])
        self.assertFalse(report["no_launch_boundary"]["action_ack_observed"])

    def test_seed_hash_drift_is_typed_red_without_launch(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zg361-b4-hc-workforce-") as name:
            root = Path(name)
            seed = seed_fixture(root)
            Path(json.loads(seed.read_text(encoding="utf-8"))["source"]["absolute_save"]).write_bytes(
                b"tampered"
            )
            report = preflight.build_preflight(seed_contract_path=seed)
        self.assertEqual("RED", report["result"])
        self.assertFalse(report["checks"]["hash_bound_current_seed_entry_ready"])
        self.assertFalse(report["no_launch_boundary"]["ck3_started_by_preflight"])

    def test_concrete_service_method_is_part_of_the_static_gate(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zg361-b4-hc-workforce-") as name:
            seed = seed_fixture(Path(name))
            with mock.patch.object(
                preflight.GameplayBridgeService,
                "query_zhongguo_workforce_collective_snapshot_v1",
                None,
            ):
                report = preflight.build_preflight(seed_contract_path=seed)
        self.assertEqual("RED", report["result"])
        self.assertFalse(report["checks"]["concrete_service_surface_complete"])

    def test_cli_writes_a_green_no_launch_report(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zg361-b4-hc-workforce-") as name:
            root = Path(name)
            seed = seed_fixture(root)
            output = root / "preflight.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(preflight.__file__),
                    "--seed-contract",
                    str(seed),
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        self.assertEqual("GREEN", report["result"])
        self.assertFalse(report["no_launch_boundary"]["service_instantiated"])
        self.assertFalse(report["no_launch_boundary"]["gameplay_action_executed"])
        self.assertFalse(report["no_launch_boundary"]["live_proof_claimed"])

    def test_preflight_source_has_no_process_or_launcher_surface(self) -> None:
        source = Path(preflight.__file__).read_text(encoding="utf-8")
        for forbidden in (
            "import subprocess",
            "from subprocess",
            "Popen(",
            "Start-Process",
            "ck3.exe",
            "GameplayBridgeService(",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
