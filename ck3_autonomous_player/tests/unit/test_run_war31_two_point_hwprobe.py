"""No-CK3 preflight and fail-closed tests for the War31 probe driver."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "ck3_autonomous_player/native_bridge/research/run_war31_two_point_hwprobe.py"


def load_driver():
    spec = importlib.util.spec_from_file_location(SCRIPT.stem, SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("War31 probe driver unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def fixture(directory: Path):
    paths = {}
    for label in ("game_exe", "bridge_dll", "checkpoint", "driver_state", "sidecar", "probe"):
        paths[label] = directory / label
        paths[label].write_bytes(label.encode())
    authorization = {
        "schema": "xar.ck3.war31.single_action_authorization.v1",
        "request_id": "WAR-INPUT-R0221-WAR31-20260927",
        "war_id": 16777231,
        "episode_run_id": "native-29829-2bc2d599f7f9",
        "action_attempt_id": "synthetic-only-action",
        "approved_action_step": "surrender-war-16777231",
        "authorization_status": "authorized",
        "authorization_source": "synthetic unit test, never a real authorization",
    }
    paths["authorization_receipt"] = directory / "receipt.json"
    paths["authorization_receipt"].write_text(json.dumps(authorization), encoding="utf-8")
    manifest = {
        "schema": "xar.ck3.war31.hwprobe_manifest.v1",
        "request_id": authorization["request_id"],
        "war_id": authorization["war_id"],
        "episode_run_id": authorization["episode_run_id"],
        "approved_action_step": authorization["approved_action_step"],
        "action_attempt_id": authorization["action_attempt_id"],
        "source_evidence_status": "separately_authorized_unverified_by_probe",
        "date_raw": 53215920,
        "expected_pid": 1234,
        "expected_process_created_filetime": 100000,
        "effect_invocation_id": "synthetic-invocation",
        "frame_token": "synthetic-frame",
        "ck3_exe_sha256": "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
    }
    for label, key in (("bridge_dll", "bridge_dll_sha256"),
                       ("checkpoint", "checkpoint_sha256"),
                       ("driver_state", "driver_state_sha256"),
                       ("sidecar", "sidecar_sha256"),
                       ("probe", "sampler_sha256"),
                       ("authorization_receipt", "authorization_receipt_sha256")):
        manifest[key] = digest(paths[label])
    paths["manifest"] = directory / "manifest.json"
    paths["manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    args = SimpleNamespace(**paths, pid=1234, attempt=directory / "attempt",
                           arm=True, timeout_ms=1000)
    return args, manifest


class DriverTests(unittest.TestCase):
    def test_asset_preflight_requires_receipt_and_exact_hashes(self):
        driver = load_driver()
        with TemporaryDirectory() as temporary:
            args, manifest = fixture(Path(temporary))
            actual_hash = driver._sha256

            def fake_exe_hash(path):
                return manifest["ck3_exe_sha256"] if path == args.game_exe else actual_hash(path)

            with patch.object(driver, "_sha256", side_effect=fake_exe_hash):
                checked, assets = driver.preflight_assets(args)
                self.assertEqual(checked, manifest)
                self.assertEqual(len(assets), 7)
                receipt = json.loads(args.authorization_receipt.read_text(encoding="utf-8"))
                receipt["authorization_status"] = "pending"
                args.authorization_receipt.write_text(json.dumps(receipt), encoding="utf-8")
                manifest["authorization_receipt_sha256"] = digest(args.authorization_receipt)
                args.manifest.write_text(json.dumps(manifest), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "authorization receipt"):
                    driver.preflight_assets(args)

    def test_preflight_rejects_invalid_identity_before_any_attach(self):
        driver = load_driver()
        with TemporaryDirectory() as temporary:
            args, manifest = fixture(Path(temporary))
            manifest["expected_pid"] = 0
            args.manifest.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "expected_pid"):
                driver.preflight_assets(args)

    def test_capture_preserves_red_report_if_offline_pair_rejects(self):
        driver = load_driver()
        with TemporaryDirectory() as temporary:
            args, manifest = fixture(Path(temporary))
            class FakeProcess:
                pid = 9999
                returncode = 0

                def __init__(self, _command, **_kwargs):
                    (args.attempt / "probe-ready.json").write_text(json.dumps({
                        "schema": "xar.ck3.war31.hwprobe_ready.v1",
                        "pid": 1234, "module_base": "0x140000000",
                        "site_0": "0x2E9F746", "site_1": "0x2EC4410",
                    }), encoding="utf-8")
                    (args.attempt / "raw.ndjson").write_text("invalid\n", encoding="utf-8")

                def poll(self):
                    return None

                def wait(self, timeout):
                    return 0

            class FakeAssembler:
                @staticmethod
                def assemble(_raw, _manifest):
                    raise ValueError("synthetic malformed stream")

            identities = {"probe": {"sha256": digest(args.probe)}}
            with patch.object(driver.subprocess, "Popen", FakeProcess), \
                 patch.object(driver, "_assembler", return_value=FakeAssembler):
                result = driver.capture(args, manifest, identities,
                                        {"attached": False, "pid": 1234,
                                         "module_base": "0x140000000"})
            self.assertEqual(result, 1)
            report = json.loads((args.attempt / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "red")
            self.assertIn("offline_pair_rejected", report["reason"])
            self.assertTrue((args.attempt / "raw.ndjson").is_file())


if __name__ == "__main__":
    unittest.main()
