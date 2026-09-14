from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
HELPER = REPO_ROOT / "tools" / "run_one_generation_canary.py"
PIPE = r"\\.\pipe\xar_ck3_restore_exact2_7aff1d0"

SPEC = importlib.util.spec_from_file_location("run_one_generation_canary", HELPER)
assert SPEC is not None and SPEC.loader is not None
CANARY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CANARY)


class OneGenerationCanaryHelperTests(unittest.TestCase):
    def test_static_contract_keeps_the_handoff_strict_and_non_destructive(
        self,
    ) -> None:
        source = HELPER.read_text(encoding="utf-8")
        self.assertIn("fresh canary target already exists; refusing overwrite", source)
        self.assertIn("shutil.copytree", source)
        self.assertIn("without purge or mirror", source)
        self.assertIn("WinSta0\\Default", source)
        self.assertNotIn("CodexSandbox", source)
        self.assertIn("native-one-generation", source)
        self.assertIn('"--max-turns", "20"', source)
        self.assertIn("default=21_600", source)
        self.assertGreaterEqual(source.count('"--bridge-mode", "disabled"'), 2)
        self.assertIn("bounded_incomplete (expected canary result)", source)
        self.assertIn("run_bound_exhausted", source)
        self.assertIn("def artifact_binding", source)
        self.assertIn("stdout_report_matches_persisted", source)
        self.assertIn("post_canary_ck3_process_count", source)
        self.assertIn('"claim-cb-white-peace": {', source)
        self.assertIn("51fe8cf6cb55de5ca01db4ed215e0abff52213a6", source)
        self.assertIn(
            "12FD30A079982E3B01FAD6442574D7938E795A84A59B4EBDD53023135B04F37D",
            source,
        )
        self.assertIn(
            "A2B78F371A16A87B2A911E1E832C07A5701E2E7B3C42FA046006A41C233702DF",
            source,
        )
        self.assertIn(
            "1618840EC108F688B3EBECC6D7F8963038BA64C8D4A3E10DDE2E29E3F443B4DF",
            source,
        )
        self.assertIn(
            "F52203F2395819CCB7A37153DBD36AB9CC6F6E168F4B44D179D3979ABF939D7B",
            source,
        )
        self.assertIn(
            "8A46DE3BFBF567E34BA99E61AEFA7F59DA248C4AE89791BB74E12820B4380B99",
            source,
        )

    @unittest.skipUnless(os.name == "nt", "canary handoff targets Windows")
    def test_dry_run_validates_fixture_without_creating_target(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-canary-plan-") as temporary:
            root = Path(temporary)
            source_state, checkpoint = self._make_source_state(root)
            driver_state = source_state / "native-session" / "driver-state.json"
            game_dir = self._make_game_dir(root)
            dll = root / "xar_ck3_bridge.dll"
            injector = root / "xar_ck3_bridge_injector.exe"
            dll.write_bytes(b"fixture dll")
            injector.write_bytes(b"fixture injector")
            target = root / "fresh-target"

            result = subprocess.run(
                [
                    sys.executable,
                    str(HELPER),
                    "--repo-root",
                    str(REPO_ROOT),
                    "--source-state",
                    str(source_state),
                    "--target-state",
                    str(target),
                    "--game-dir",
                    str(game_dir),
                    "--python-path",
                    sys.executable,
                    "--bridge-dll",
                    str(dll),
                    "--bridge-injector",
                    str(injector),
                    "--expected-checkpoint-size",
                    str(checkpoint.stat().st_size),
                    "--expected-checkpoint-sha256",
                    self._sha256(checkpoint),
                    "--expected-driver-state-sha256",
                    self._sha256(driver_state),
                    "--expected-bridge-dll-sha256",
                    self._sha256(dll),
                    "--expected-bridge-injector-sha256",
                    self._sha256(injector),
                    "--skip-repository-check",
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            plan = json.loads(result.stdout)
            self.assertEqual(plan["profile"], "legacy")
            self.assertEqual(plan["mode"], "dry_run")
            self.assertEqual(plan["source_driver_state"]["pipe"], PIPE)
            self.assertEqual(plan["execute_host_required"]["user"], "xenoa")
            self.assertEqual(
                plan["execute_host_required"]["desktop"], "WinSta0\\Default"
            )
            self.assertEqual(plan["strict_canary_contract"]["max_turns"], 20)
            argv = plan["commands"]["native_one_generation"]
            self.assertEqual(argv[argv.index("--timeout") + 1], "21600")
            self.assertIn(
                "bounded_incomplete",
                plan["strict_canary_contract"]["alive_at_bound"],
            )
            self.assertFalse(target.exists())

    @unittest.skipUnless(os.name == "nt", "canary handoff targets Windows")
    def test_claim_white_peace_profile_dry_run_records_identity_without_target(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-claim-canary-plan-") as temporary:
            root = Path(temporary)
            source_state, checkpoint = self._make_source_state(root)
            driver_state = source_state / "native-session" / "driver-state.json"
            game_dir = self._make_game_dir(root)
            fixture_repo = root / "repo"
            agent = fixture_repo / "ck3_autonomous_player" / "agent.py"
            agent.parent.mkdir(parents=True)
            agent.write_text("# fixture agent\n", encoding="utf-8")
            build_dir = (
                fixture_repo
                / "ck3_autonomous_player"
                / "native_bridge"
                / "build-claim-white-peace-51fe8cf-msvc"
            )
            build_dir.mkdir(parents=True)
            dll = build_dir / "xar_ck3_bridge.dll"
            injector = build_dir / "xar_ck3_bridge_injector.exe"
            dll.write_bytes(b"fixture claim white peace dll")
            injector.write_bytes(b"fixture claim white peace injector")
            target = root / "fresh-target"
            environment = os.environ.copy()
            environment.pop("XAR_CK3_BRIDGE_DLL", None)
            environment.pop("XAR_CK3_BRIDGE_INJECTOR", None)

            result = subprocess.run(
                [
                    sys.executable,
                    str(HELPER),
                    "--profile",
                    "claim-cb-white-peace",
                    "--repo-root",
                    str(fixture_repo),
                    "--source-state",
                    str(source_state),
                    "--target-state",
                    str(target),
                    "--game-dir",
                    str(game_dir),
                    "--python-path",
                    sys.executable,
                    "--expected-repo-revision",
                    "a" * 40,
                    "--expected-checkpoint-size",
                    str(checkpoint.stat().st_size),
                    "--expected-checkpoint-sha256",
                    self._sha256(checkpoint),
                    "--expected-driver-state-sha256",
                    self._sha256(driver_state),
                    "--expected-bridge-dll-sha256",
                    self._sha256(dll),
                    "--expected-bridge-injector-sha256",
                    self._sha256(injector),
                    "--skip-repository-check",
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=environment,
            )

            plan = json.loads(result.stdout)
            self.assertEqual(plan["profile"], "claim-cb-white-peace")
            self.assertEqual(plan["mode"], "dry_run")
            self.assertEqual(plan["bridge_dll"]["path"], str(dll.resolve()))
            self.assertEqual(plan["bridge_dll"]["sha256"], self._sha256(dll))
            self.assertEqual(
                plan["bridge_injector"]["path"], str(injector.resolve())
            )
            self.assertEqual(
                plan["bridge_injector"]["sha256"], self._sha256(injector)
            )
            self.assertFalse(target.exists())

    @unittest.skipUnless(os.name == "nt", "canary handoff targets Windows")
    def test_existing_target_is_rejected_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-canary-existing-") as temporary:
            root = Path(temporary)
            source_state, checkpoint = self._make_source_state(root)
            driver_state = source_state / "native-session" / "driver-state.json"
            game_dir = self._make_game_dir(root)
            dll = root / "xar_ck3_bridge.dll"
            injector = root / "xar_ck3_bridge_injector.exe"
            dll.write_bytes(b"fixture dll")
            injector.write_bytes(b"fixture injector")
            target = root / "existing-target"
            target.mkdir()
            sentinel = target / "sentinel.txt"
            sentinel.write_text("keep", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(HELPER),
                    "--repo-root",
                    str(REPO_ROOT),
                    "--source-state",
                    str(source_state),
                    "--target-state",
                    str(target),
                    "--game-dir",
                    str(game_dir),
                    "--python-path",
                    sys.executable,
                    "--bridge-dll",
                    str(dll),
                    "--bridge-injector",
                    str(injector),
                    "--expected-checkpoint-size",
                    str(checkpoint.stat().st_size),
                    "--expected-checkpoint-sha256",
                    self._sha256(checkpoint),
                    "--expected-driver-state-sha256",
                    self._sha256(driver_state),
                    "--expected-bridge-dll-sha256",
                    self._sha256(dll),
                    "--expected-bridge-injector-sha256",
                    self._sha256(injector),
                    "--skip-repository-check",
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("refusing overwrite", result.stderr)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")
            self.assertEqual(list(target.iterdir()), [sentinel])

    def test_artifact_binding_accepts_exact_sidecar_and_rejects_escape(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-canary-artifact-") as temporary:
            root = Path(temporary)
            run_dir = root / "artifact-run"
            run_dir.mkdir()
            sidecar = run_dir / "first-blocker.json"
            sidecar.write_text('{"kind":"run_bound_exhausted"}\n', encoding="utf-8")
            outside = root / "outside.json"
            outside.write_text("{}\n", encoding="utf-8")
            valid = CANARY.artifact_binding(
                run_dir,
                {
                    "path": "first-blocker.json",
                    "size": sidecar.stat().st_size,
                    "sha256": self._sha256(sidecar),
                },
                "first-blocker.json",
                "fixture",
            )
            escape = CANARY.artifact_binding(
                run_dir,
                {"path": "../outside.json", "size": 3, "sha256": "0" * 64},
                "../outside.json",
                "escape",
            )
            self.assertTrue(valid["ok"])
            self.assertFalse(escape["ok"])
            self.assertIn("escapes the run directory", escape["error"])

    @unittest.skipUnless(os.name == "nt", "canary handoff targets Windows")
    def test_execute_cannot_override_the_canonical_checkpoint(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(HELPER),
                "--repo-root",
                str(REPO_ROOT),
                "--execute",
                "--expected-checkpoint-size",
                "1",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("canonical production6b", result.stderr)

    @unittest.skipUnless(os.name == "nt", "canary handoff targets Windows")
    def test_execute_cannot_override_the_fixed_canary_bounds(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(HELPER),
                "--repo-root",
                str(REPO_ROOT),
                "--execute",
                "--timeout-seconds",
                "3600",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fixed canary bounds", result.stderr)

    @unittest.skipUnless(os.name == "nt", "canary handoff targets Windows")
    def test_claim_white_peace_execute_rejects_noncanonical_identity(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(HELPER),
                "--profile",
                "claim-cb-white-peace",
                "--repo-root",
                str(REPO_ROOT),
                "--execute",
                "--expected-bridge-dll-sha256",
                "A2B78F371A16A87B2A911E1E832C07A5701E2E7B3C42FA046006A41C233702DF",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("'claim-cb-white-peace' profile identities", result.stderr)

    @staticmethod
    def _sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest().upper()

    @staticmethod
    def _make_source_state(root: Path) -> tuple[Path, Path]:
        source_state = root / "source-state"
        checkpoint = (
            source_state / "profile" / "save games" / "xar_checkpoint.ck3"
        )
        checkpoint.parent.mkdir(parents=True)
        checkpoint.write_bytes(b"fixture production checkpoint")
        checkpoint_sha256 = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
        checkpoint_record = {
            "status": "saved",
            "path": str(checkpoint),
            "name": "xar_checkpoint.ck3",
            "size": checkpoint.stat().st_size,
            "sha256": checkpoint_sha256,
            "date_raw": 53_177_976,
            "history_index": 402,
            "episode_character_id": 29_829,
            "episode_run_id": "native-29829-ee172aa720db",
        }
        history = [
            {"index": index, "command": "fixture", "ok": True, "result": {}}
            for index in range(1, 402)
        ]
        history.append(
            {
                "index": 402,
                "command": "save-checkpoint",
                "ok": True,
                "result": {"checkpoint": checkpoint_record},
            }
        )
        driver = {
            "format_version": 2,
            "pipe_name": PIPE,
            "episode_character_id": 29_829,
            "episode_run_id": "native-29829-ee172aa720db",
            "last_checkpoint": checkpoint_record,
            "command_history": history,
        }
        driver_path = source_state / "native-session" / "driver-state.json"
        driver_path.parent.mkdir(parents=True)
        driver_path.write_text(json.dumps(driver), encoding="utf-8")
        return source_state, checkpoint

    @staticmethod
    def _make_game_dir(root: Path) -> Path:
        game_dir = root / "game"
        executable = game_dir / "binaries" / "ck3.exe"
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b"fixture ck3")
        return game_dir


if __name__ == "__main__":
    unittest.main()
