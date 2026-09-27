"""No-CK3 preflight and fail-closed tests for the War31 probe driver."""

from __future__ import annotations

import hashlib
import importlib.util
import copy
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
    for label in ("game_exe", "bridge_dll", "checkpoint", "sidecar", "probe"):
        paths[label] = directory / label
        paths[label].write_bytes(label.encode())
    old_binding = {"lifecycle": "ordinary_campaign_succession", "xar_enabled": "xar_off",
                   "environment_sha256": "old-environment"}
    new_binding = {**old_binding, "environment_sha256": "new-environment"}
    paths["sidecar"].write_text(json.dumps({"environment_sha256": "new-environment"}),
                                encoding="utf-8")
    history = [{"index": index, "command": "query", "ok": True}
               for index in range(1, 2134)]
    history.append({"index": 2134, "command": "save-checkpoint", "ok": True,
                    "result": {"checkpoint": {"succession_lifecycle": old_binding}}})
    source = {"format_version": 2, "pipe_name": "test-pipe", "episode_character_id": 29829,
              "episode_run_id": "native-29829-2bc2d599f7f9",
              "succession_lifecycle": old_binding, "command_history": history,
              "last_checkpoint": {"history_index": 2134, "date_raw": 53215920,
                                  "sha256": "1AF4055F978AF60267FB3A0D8658224047CD6BFDA884C66886A13B74EE34A90A",
                                  "succession_lifecycle": old_binding}}
    rebound = copy.deepcopy(source)
    rebound["succession_lifecycle"] = new_binding
    rebound["last_checkpoint"]["succession_lifecycle"] = new_binding
    rebound["command_history"][2133]["result"]["checkpoint"]["succession_lifecycle"] = new_binding
    paths["source_driver_state"] = directory / "source-driver-state.json"
    paths["driver_state"] = directory / "derived-driver-state.json"
    paths["source_driver_state"].write_text(json.dumps(source), encoding="utf-8")
    paths["driver_state"].write_text(json.dumps(rebound), encoding="utf-8")
    paths["rebind_receipt"] = directory / "rebind-receipt.json"
    paths["rebind_receipt"].write_text(json.dumps({
        "schema": "xar.ck3.ordinary-seed-rebind/v1", "status": "rebound", "ok": True,
        "pipe_name": "test-pipe",
        "environment": {"source_sha256": "old-environment",
                        "target_sha256": "new-environment"},
        "driver_state": {"source_sha256": "1DE61CF0AC47EDD1D63FE1F3D77668D5F499EA6CA06B90BC83B068CF35F16336",
                         "target_sha256": digest(paths["driver_state"])},
        "save": {"bytes_unchanged": True,
                 "source": {"sha256": source["last_checkpoint"]["sha256"]},
                 "target": {"sha256": source["last_checkpoint"]["sha256"]}},
    }), encoding="utf-8")
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
        "bridge_dll_sha256": "C36ECCEB67A0DCA7C8C1C6C855A5036771B46617E9F1BF5F4185D965C1951BCE",
        "checkpoint_sha256": source["last_checkpoint"]["sha256"],
        "source_driver_state_sha256": "1DE61CF0AC47EDD1D63FE1F3D77668D5F499EA6CA06B90BC83B068CF35F16336",
    }
    for label, key in (("driver_state", "driver_state_sha256"),
                       ("rebind_receipt", "rebind_receipt_sha256"),
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

            def fake_frozen_hash(path):
                frozen = {args.game_exe: "ck3_exe_sha256",
                          args.bridge_dll: "bridge_dll_sha256",
                          args.checkpoint: "checkpoint_sha256",
                          args.source_driver_state: "source_driver_state_sha256"}
                return manifest[frozen[path]] if path in frozen else actual_hash(path)

            with patch.object(driver, "_sha256", side_effect=fake_frozen_hash):
                checked, assets = driver.preflight_assets(args)
                self.assertEqual(checked, manifest)
                self.assertEqual(len(assets), 9)
                receipt = json.loads(args.authorization_receipt.read_text(encoding="utf-8"))
                receipt["authorization_status"] = "pending"
                args.authorization_receipt.write_text(json.dumps(receipt), encoding="utf-8")
                manifest["authorization_receipt_sha256"] = digest(args.authorization_receipt)
                args.manifest.write_text(json.dumps(manifest), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "authorization receipt"):
                    driver.preflight_assets(args)

    def test_frozen_source_fields_fail_closed(self):
        driver = load_driver()
        with TemporaryDirectory() as temporary:
            args, manifest = fixture(Path(temporary))
            for field, replacement in (
                ("checkpoint_sha256", "0" * 64),
                ("source_driver_state_sha256", "0" * 64),
                ("bridge_dll_sha256", "0" * 64),
                ("date_raw", 53215944),
            ):
                changed = dict(manifest)
                changed[field] = replacement
                args.manifest.write_text(json.dumps(changed), encoding="utf-8")
                with self.subTest(field=field), self.assertRaisesRegex(ValueError, field):
                    driver.preflight_assets(args)

    def test_derived_driver_must_only_change_lifecycle_anchors(self):
        driver = load_driver()
        with TemporaryDirectory() as temporary:
            args, manifest = fixture(Path(temporary))
            derived = json.loads(args.driver_state.read_text(encoding="utf-8"))
            derived["pipe_name"] = "different-pipe"
            args.driver_state.write_text(json.dumps(derived), encoding="utf-8")
            manifest["driver_state_sha256"] = digest(args.driver_state)
            receipt = json.loads(args.rebind_receipt.read_text(encoding="utf-8"))
            receipt["driver_state"]["target_sha256"] = manifest["driver_state_sha256"]
            args.rebind_receipt.write_text(json.dumps(receipt), encoding="utf-8")
            manifest["rebind_receipt_sha256"] = digest(args.rebind_receipt)
            args.manifest.write_text(json.dumps(manifest), encoding="utf-8")
            actual_hash = driver._sha256

            def fake_frozen_hash(path):
                frozen = {args.game_exe: "ck3_exe_sha256",
                          args.bridge_dll: "bridge_dll_sha256",
                          args.checkpoint: "checkpoint_sha256",
                          args.source_driver_state: "source_driver_state_sha256"}
                return manifest[frozen[path]] if path in frozen else actual_hash(path)

            with patch.object(driver, "_sha256", side_effect=fake_frozen_hash):
                with self.assertRaisesRegex(ValueError, "bridge pipe"):
                    driver.preflight_assets(args)

    def test_old_environment_sidecar_is_rejected(self):
        driver = load_driver()
        with TemporaryDirectory() as temporary:
            args, manifest = fixture(Path(temporary))
            args.sidecar.write_text(json.dumps({"environment_sha256": "old-environment"}),
                                    encoding="utf-8")
            manifest["sidecar_sha256"] = digest(args.sidecar)
            args.manifest.write_text(json.dumps(manifest), encoding="utf-8")
            actual_hash = driver._sha256

            def fake_frozen_hash(path):
                frozen = {args.game_exe: "ck3_exe_sha256",
                          args.bridge_dll: "bridge_dll_sha256",
                          args.checkpoint: "checkpoint_sha256",
                          args.source_driver_state: "source_driver_state_sha256"}
                return manifest[frozen[path]] if path in frozen else actual_hash(path)

            with patch.object(driver, "_sha256", side_effect=fake_frozen_hash):
                with self.assertRaisesRegex(ValueError, "newly prepared environment"):
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
