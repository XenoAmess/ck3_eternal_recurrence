from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
HELPER = REPO_ROOT / "tools" / "run_one_generation_canary.ps1"
PIPE = r"\\.\pipe\xar_ck3_restore_exact2_7aff1d0"


class OneGenerationCanaryHelperTests(unittest.TestCase):
    def test_static_contract_keeps_the_handoff_strict_and_non_destructive(
        self,
    ) -> None:
        source = HELPER.read_text(encoding="utf-8")
        self.assertIn("fresh canary target already exists; refusing overwrite", source)
        self.assertIn("/E /COPY:DAT /DCOPY:DAT", source)
        self.assertNotIn("/MIR", source)
        self.assertNotIn("/PURGE", source)
        self.assertIn("WinSta0\\Default", source)
        self.assertNotIn("CodexSandbox", source)
        self.assertIn("native-one-generation", source)
        self.assertIn('"--max-turns", "20"', source)
        self.assertIn('[double]$TimeoutSeconds = 21600', source)
        self.assertGreaterEqual(source.count('"--bridge-mode", "disabled"'), 2)
        self.assertIn("bounded_incomplete (expected canary result)", source)
        self.assertIn("run_bound_exhausted", source)
        self.assertIn("Test-ArtifactBinding", source)
        self.assertIn("stdout_report_matches_persisted", source)
        self.assertIn("post_canary_ck3_process_count", source)
        self.assertIn('[ValidateSet("legacy", "claim-cb-white-peace")]', source)
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

    @unittest.skipUnless(os.name == "nt", "PowerShell handoff targets Windows")
    def test_dry_run_validates_fixture_without_creating_target(self) -> None:
        powershell = shutil.which("powershell.exe")
        self.assertIsNotNone(powershell)
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
                    powershell,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(HELPER),
                    "-RepoRoot",
                    str(REPO_ROOT),
                    "-SourceState",
                    str(source_state),
                    "-TargetState",
                    str(target),
                    "-GameDir",
                    str(game_dir),
                    "-PythonPath",
                    sys.executable,
                    "-BridgeDll",
                    str(dll),
                    "-BridgeInjector",
                    str(injector),
                    "-ExpectedCheckpointSize",
                    str(checkpoint.stat().st_size),
                    "-ExpectedCheckpointSha256",
                    self._sha256(checkpoint),
                    "-ExpectedDriverStateSha256",
                    self._sha256(driver_state),
                    "-ExpectedBridgeDllSha256",
                    self._sha256(dll),
                    "-ExpectedBridgeInjectorSha256",
                    self._sha256(injector),
                    "-SkipRepositoryCheck",
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

    @unittest.skipUnless(os.name == "nt", "PowerShell handoff targets Windows")
    def test_claim_white_peace_profile_dry_run_records_identity_without_target(
        self,
    ) -> None:
        powershell = shutil.which("powershell.exe")
        self.assertIsNotNone(powershell)
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
                    powershell,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(HELPER),
                    "-Profile",
                    "claim-cb-white-peace",
                    "-RepoRoot",
                    str(fixture_repo),
                    "-SourceState",
                    str(source_state),
                    "-TargetState",
                    str(target),
                    "-GameDir",
                    str(game_dir),
                    "-PythonPath",
                    sys.executable,
                    "-ExpectedRepoRevision",
                    "a" * 40,
                    "-ExpectedCheckpointSize",
                    str(checkpoint.stat().st_size),
                    "-ExpectedCheckpointSha256",
                    self._sha256(checkpoint),
                    "-ExpectedDriverStateSha256",
                    self._sha256(driver_state),
                    "-ExpectedBridgeDllSha256",
                    self._sha256(dll),
                    "-ExpectedBridgeInjectorSha256",
                    self._sha256(injector),
                    "-SkipRepositoryCheck",
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

    @unittest.skipUnless(os.name == "nt", "PowerShell handoff targets Windows")
    def test_existing_target_is_rejected_without_mutation(self) -> None:
        powershell = shutil.which("powershell.exe")
        self.assertIsNotNone(powershell)
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
                    powershell,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(HELPER),
                    "-RepoRoot",
                    str(REPO_ROOT),
                    "-SourceState",
                    str(source_state),
                    "-TargetState",
                    str(target),
                    "-GameDir",
                    str(game_dir),
                    "-PythonPath",
                    sys.executable,
                    "-BridgeDll",
                    str(dll),
                    "-BridgeInjector",
                    str(injector),
                    "-ExpectedCheckpointSize",
                    str(checkpoint.stat().st_size),
                    "-ExpectedCheckpointSha256",
                    self._sha256(checkpoint),
                    "-ExpectedDriverStateSha256",
                    self._sha256(driver_state),
                    "-ExpectedBridgeDllSha256",
                    self._sha256(dll),
                    "-ExpectedBridgeInjectorSha256",
                    self._sha256(injector),
                    "-SkipRepositoryCheck",
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

    @unittest.skipUnless(os.name == "nt", "PowerShell handoff targets Windows")
    def test_artifact_binding_accepts_exact_sidecar_and_rejects_escape(self) -> None:
        powershell = shutil.which("powershell.exe")
        self.assertIsNotNone(powershell)
        with tempfile.TemporaryDirectory(prefix="xar-canary-artifact-") as temporary:
            root = Path(temporary)
            source_state, checkpoint = self._make_source_state(root)
            driver_state = source_state / "native-session" / "driver-state.json"
            game_dir = self._make_game_dir(root)
            dll = root / "xar_ck3_bridge.dll"
            injector = root / "xar_ck3_bridge_injector.exe"
            dll.write_bytes(b"fixture dll")
            injector.write_bytes(b"fixture injector")
            run_dir = root / "artifact-run"
            run_dir.mkdir()
            sidecar = run_dir / "first-blocker.json"
            sidecar.write_text('{"kind":"run_bound_exhausted"}\n', encoding="utf-8")
            outside = root / "outside.json"
            outside.write_text("{}\n", encoding="utf-8")

            environment = os.environ.copy()
            environment.update(
                {
                    "XAR_CANARY_HELPER": str(HELPER),
                    "XAR_CANARY_REPO": str(REPO_ROOT),
                    "XAR_CANARY_SOURCE": str(source_state),
                    "XAR_CANARY_TARGET": str(root / "fresh-target"),
                    "XAR_CANARY_GAME": str(game_dir),
                    "XAR_CANARY_PYTHON": sys.executable,
                    "XAR_CANARY_DLL": str(dll),
                    "XAR_CANARY_INJECTOR": str(injector),
                    "XAR_CANARY_CHECKPOINT_SIZE": str(checkpoint.stat().st_size),
                    "XAR_CANARY_CHECKPOINT_SHA": self._sha256(checkpoint),
                    "XAR_CANARY_DRIVER_SHA": self._sha256(driver_state),
                    "XAR_CANARY_DLL_SHA": self._sha256(dll),
                    "XAR_CANARY_INJECTOR_SHA": self._sha256(injector),
                    "XAR_CANARY_RUN": str(run_dir),
                    "XAR_CANARY_SIDECAR": str(sidecar),
                }
            )
            command = (
                "$null = . $env:XAR_CANARY_HELPER "
                "-RepoRoot $env:XAR_CANARY_REPO "
                "-SourceState $env:XAR_CANARY_SOURCE "
                "-TargetState $env:XAR_CANARY_TARGET "
                "-GameDir $env:XAR_CANARY_GAME "
                "-PythonPath $env:XAR_CANARY_PYTHON "
                "-BridgeDll $env:XAR_CANARY_DLL "
                "-BridgeInjector $env:XAR_CANARY_INJECTOR "
                "-ExpectedCheckpointSize $env:XAR_CANARY_CHECKPOINT_SIZE "
                "-ExpectedCheckpointSha256 $env:XAR_CANARY_CHECKPOINT_SHA "
                "-ExpectedDriverStateSha256 $env:XAR_CANARY_DRIVER_SHA "
                "-ExpectedBridgeDllSha256 $env:XAR_CANARY_DLL_SHA "
                "-ExpectedBridgeInjectorSha256 $env:XAR_CANARY_INJECTOR_SHA "
                "-SkipRepositoryCheck; "
                "$item = Get-Item -LiteralPath $env:XAR_CANARY_SIDECAR; "
                "$entry = [pscustomobject]@{path='first-blocker.json';"
                "size=[long]$item.Length;sha256=(Get-FileHash -LiteralPath "
                "$item.FullName -Algorithm SHA256).Hash}; "
                "$valid = Test-ArtifactBinding -RunDir $env:XAR_CANARY_RUN "
                "-Entry $entry -ExpectedRelativePath 'first-blocker.json' "
                "-Label 'fixture'; "
                "$escape = Test-ArtifactBinding -RunDir $env:XAR_CANARY_RUN "
                "-Entry ([pscustomobject]@{path='../outside.json';size=3;"
                "sha256=('0' * 64)}) -ExpectedRelativePath '../outside.json' "
                "-Label 'escape'; "
                "[pscustomobject]@{valid=$valid.ok;escape=$escape.ok;"
                "escape_error=$escape.error}|ConvertTo-Json -Compress"
            )
            result = subprocess.run(
                [
                    powershell,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    command,
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=environment,
            )
            payload = json.loads(result.stdout)
            self.assertTrue(payload["valid"])
            self.assertFalse(payload["escape"])
            self.assertIn("escapes the run directory", payload["escape_error"])

    @unittest.skipUnless(os.name == "nt", "PowerShell handoff targets Windows")
    def test_execute_cannot_override_the_canonical_checkpoint(self) -> None:
        powershell = shutil.which("powershell.exe")
        self.assertIsNotNone(powershell)
        result = subprocess.run(
            [
                powershell,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(HELPER),
                "-RepoRoot",
                str(REPO_ROOT),
                "-Execute",
                "-ExpectedCheckpointSize",
                "1",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("canonical production6b", result.stderr)

    @unittest.skipUnless(os.name == "nt", "PowerShell handoff targets Windows")
    def test_execute_cannot_override_the_fixed_canary_bounds(self) -> None:
        powershell = shutil.which("powershell.exe")
        self.assertIsNotNone(powershell)
        result = subprocess.run(
            [
                powershell,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(HELPER),
                "-RepoRoot",
                str(REPO_ROOT),
                "-Execute",
                "-TimeoutSeconds",
                "3600",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fixed canary bounds", result.stderr)

    @unittest.skipUnless(os.name == "nt", "PowerShell handoff targets Windows")
    def test_claim_white_peace_execute_rejects_noncanonical_identity(self) -> None:
        powershell = shutil.which("powershell.exe")
        self.assertIsNotNone(powershell)
        result = subprocess.run(
            [
                powershell,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(HELPER),
                "-Profile",
                "claim-cb-white-peace",
                "-RepoRoot",
                str(REPO_ROOT),
                "-Execute",
                "-ExpectedBridgeDllSha256",
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
