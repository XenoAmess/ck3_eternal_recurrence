from __future__ import annotations

import contextlib
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.environment import EnvironmentSpec, sha256_file  # noqa: E402
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.ordinary_seed_rebinder import (  # noqa: E402
    ORDINARY_SEED_REBIND_V1_SCHEMA,
    rebind_ordinary_seed_v1,
)
import xar_autoplayer.ordinary_seed_rebinder as rebinder_module  # noqa: E402


def _binding(environment_sha256: str) -> dict[str, object]:
    return {
        "schema": "xar.ck3.succession-lifecycle-binding/v1",
        "lifecycle": "ordinary_campaign_succession",
        "xar_enabled": "xar_off",
        "pact_contract": "absent_by_fresh_campaign_xar_off_contract",
        "source": "prepared-environment-manifest",
        "environment_sha256": environment_sha256,
    }


class OrdinarySeedRebinderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(
            prefix="xar-ordinary-seed-rebind-"
        )
        root = Path(self.temporary.name)
        self.spec = EnvironmentSpec(root / "target-state", root / "game")
        self.driver_path = (
            self.spec.state_dir / "native-session" / "driver-state.json"
        )
        self.save_path = (
            self.spec.profile_dir / "save games" / "xar_checkpoint.ck3"
        )
        self.driver_path.parent.mkdir(parents=True)
        self.save_path.parent.mkdir(parents=True)
        self.save_bytes = b"opaque ck3 checkpoint bytes\x00\xff" * 8
        self.save_path.write_bytes(self.save_bytes)
        self.save_sha256 = hashlib.sha256(self.save_bytes).hexdigest()
        self.pipe_name = r"\\.\pipe\ordinary-seed-rebind-test"
        self.source_environment = "a" * 64
        self.target_environment = "b" * 64
        checkpoint = {
            "name": "xar_checkpoint.ck3",
            "size": len(self.save_bytes),
            "sha256": self.save_sha256,
            "date_raw": 53_144_328,
            "history_index": 1,
            "episode_character_id": 31_853,
            "episode_run_id": "native-31853-fixture",
            "succession_lifecycle": _binding(self.source_environment),
        }
        self.source_payload = {
            "format_version": 2,
            "pipe_name": self.pipe_name,
            "bridge_pid": 42_424,
            "episode_character_id": 31_853,
            "episode_run_id": "native-31853-fixture",
            "last_checkpoint": copy.deepcopy(checkpoint),
            "command_history": [
                {
                    "index": 1,
                    "command": "save-checkpoint",
                    "ok": True,
                    "result": {
                        "checkpoint": copy.deepcopy(checkpoint),
                    },
                }
            ],
            "rollback_war_failure": None,
            "rollback_war_failures": [],
            "managed_restore_transaction": None,
            "succession_expectation": None,
            "succession_lifecycle": _binding(self.source_environment),
        }
        self._write_source(self.source_payload)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write_source(self, payload: dict[str, object]) -> None:
        self.driver_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _manifest(self, setting: str = "xar_off") -> dict[str, object]:
        return {
            "environment_sha256": self.target_environment,
            "rules": {
                "profile": [{"rule": "xar_enabled", "setting": setting}]
            },
        }

    def _run(self, manifest: dict[str, object] | None = None):
        with mock.patch.object(
            rebinder_module,
            "exclusive_state_lock",
            return_value=contextlib.nullcontext(),
        ), mock.patch.object(
            rebinder_module,
            "ck3_process_inventory",
            return_value={"processes": []},
        ), mock.patch.object(
            rebinder_module,
            "verify_profile",
            return_value=manifest or self._manifest(),
        ):
            return rebind_ordinary_seed_v1(
                self.spec,
                expected_pipe_name=self.pipe_name,
                lock_factory=rebinder_module.exclusive_state_lock,
            )

    def test_rebinds_exactly_three_lifecycle_anchors_and_preserves_save(self) -> None:
        source_driver_sha = sha256_file(self.driver_path)

        receipt = self._run()

        self.assertEqual(receipt["schema"], ORDINARY_SEED_REBIND_V1_SCHEMA)
        self.assertTrue(receipt["ok"])
        self.assertFalse(receipt["ck3_launch_attempted"])
        self.assertEqual(
            receipt["environment"],
            {
                "source_sha256": self.source_environment,
                "target_sha256": self.target_environment,
            },
        )
        self.assertEqual(
            receipt["driver_state"]["source_sha256"], source_driver_sha
        )
        self.assertEqual(
            receipt["driver_state"]["target_sha256"],
            sha256_file(self.driver_path),
        )
        self.assertEqual(self.save_path.read_bytes(), self.save_bytes)
        self.assertTrue(receipt["save"]["bytes_unchanged"])
        self.assertEqual(
            receipt["save"]["source"]["sha256"], self.save_sha256
        )
        self.assertEqual(receipt["save"]["source"], receipt["save"]["target"])
        self.assertEqual(
            receipt["post_rebind_validation"]["cold_checkpoint_validator"],
            "passed",
        )

        rebound = json.loads(self.driver_path.read_text(encoding="utf-8"))
        expected_binding = _binding(self.target_environment)
        self.assertEqual(rebound["succession_lifecycle"], expected_binding)
        self.assertEqual(
            rebound["last_checkpoint"]["succession_lifecycle"],
            expected_binding,
        )
        self.assertEqual(
            rebound["command_history"][0]["result"]["checkpoint"][
                "succession_lifecycle"
            ],
            expected_binding,
        )
        original_without_bindings = copy.deepcopy(self.source_payload)
        rebound_without_bindings = copy.deepcopy(rebound)
        for payload in (original_without_bindings, rebound_without_bindings):
            payload["succession_lifecycle"] = None
            payload["last_checkpoint"]["succession_lifecycle"] = None
            payload["command_history"][0]["result"]["checkpoint"][
                "succession_lifecycle"
            ] = None
        self.assertEqual(rebound_without_bindings, original_without_bindings)

    def test_mixed_or_missing_binding_fails_without_writing(self) -> None:
        for fault in ("mixed", "missing"):
            with self.subTest(fault=fault):
                payload = copy.deepcopy(self.source_payload)
                anchor = payload["command_history"][0]["result"]["checkpoint"]
                if fault == "mixed":
                    anchor["succession_lifecycle"] = _binding("c" * 64)
                else:
                    anchor.pop("succession_lifecycle")
                self._write_source(payload)
                before = self.driver_path.read_bytes()

                with self.assertRaises(AgentError):
                    self._run()

                self.assertEqual(self.driver_path.read_bytes(), before)
                self.assertEqual(self.save_path.read_bytes(), self.save_bytes)

    def test_xar_on_target_manifest_fails_without_writing(self) -> None:
        before = self.driver_path.read_bytes()

        with self.assertRaisesRegex(AgentError, "target prepared manifest"):
            self._run(self._manifest("xar_on"))

        self.assertEqual(self.driver_path.read_bytes(), before)

    def test_checkpoint_byte_mismatch_fails_without_writing(self) -> None:
        before = self.driver_path.read_bytes()
        self.save_path.write_bytes(b"different bytes")

        with self.assertRaisesRegex(AgentError, "save bytes differ"):
            self._run()

        self.assertEqual(self.driver_path.read_bytes(), before)

    def test_post_write_validation_failure_restores_source_driver(self) -> None:
        before = self.driver_path.read_bytes()
        real_validator = rebinder_module.validate_cold_start_checkpoint_for_pipe
        calls = 0

        def fail_second(spec, pipe_name):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise AgentError("injected post-write validator RED")
            return real_validator(spec, pipe_name)

        with mock.patch.object(
            rebinder_module,
            "validate_cold_start_checkpoint_for_pipe",
            side_effect=fail_second,
        ):
            with self.assertRaisesRegex(AgentError, "injected post-write"):
                self._run()

        self.assertEqual(self.driver_path.read_bytes(), before)
        self.assertEqual(self.save_path.read_bytes(), self.save_bytes)

    def test_running_ck3_fails_before_profile_or_artifact_mutation(self) -> None:
        before = self.driver_path.read_bytes()
        with mock.patch.object(
            rebinder_module,
            "exclusive_state_lock",
            return_value=contextlib.nullcontext(),
        ), mock.patch.object(
            rebinder_module,
            "ck3_process_inventory",
            return_value={"processes": [{"pid": 123, "name": "ck3.exe"}]},
        ), mock.patch.object(rebinder_module, "verify_profile") as profile:
            with self.assertRaisesRegex(AgentError, "zero running ck3.exe"):
                rebind_ordinary_seed_v1(
                    self.spec,
                    lock_factory=rebinder_module.exclusive_state_lock,
                )

        profile.assert_not_called()
        self.assertEqual(self.driver_path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
