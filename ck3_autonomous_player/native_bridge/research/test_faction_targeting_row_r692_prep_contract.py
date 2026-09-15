"""Focused no-launch contract tests for the R692 faction probe package."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
SOURCE_ROOT = REPO_ROOT / "ck3_autonomous_player" / "src"
sys.path.insert(0, str(SOURCE_ROOT))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


WRAPPER = _load("bounded_wrapper", HERE / "generate_bounded_private_probe_wrapper.py")
sys.modules["generate_bounded_private_probe_wrapper"] = WRAPPER
RUNNER = _load("faction_r692_runner", HERE / "run_faction_targeting_row_private_probe_live.py")
PREP = _load(
    "faction_r692_prep", HERE / "prepare_faction_targeting_row_probe_candidate.py"
)
BOOTSTRAP = _load(
    "faction_r692_bootstrap", REPO_ROOT / "tools" / "run_g2_faction_targeting_row_probe.py"
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _arguments(root: Path) -> list[str]:
    return [
        "--artifact-dir",
        str(root / "artifact"),
        "--state-dir",
        str(root / "state"),
        "--game-dir",
        str(root / "game"),
        "--source-save",
        str(root / "source-save" / "save.ck3"),
        "--save-name",
        "save.ck3",
        "--expected-save-sha256",
        "1" * 64,
        "--candidate-manifest",
        str(root / "candidate-manifest.json"),
        "--expected-candidate-manifest-sha256",
        "2" * 64,
        "--bridge-dll",
        str(root / "bin" / "bridge.dll"),
        "--expected-bridge-dll-sha256",
        "3" * 64,
        "--bridge-injector",
        str(root / "bin" / "injector.exe"),
        "--expected-bridge-injector-sha256",
        "4" * 64,
        "--expected-game-exe-sha256",
        "5" * 64,
        "--expected-character-id",
        "29829",
        "--pipe",
        r"\\.\pipe\xar_ck3_bridge_g2_m4_r692_faction_test",
        "--old-round",
        "R691",
        "--new-round",
        "R692",
        "--candidate-revision",
        "6" * 40,
        "--publish-timeout",
        "90",
    ]


class R692ParameterContractTest(unittest.TestCase):
    def test_generator_arguments_are_accepted_by_runner(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = RUNNER.build_parser().parse_args(_arguments(root))
            RUNNER.validate_parameter_contract(args)
        contract = PREP.verify_parameter_contract(
            HERE / "run_faction_targeting_row_private_probe_live.py"
        )
        self.assertEqual(contract["status"], "green")
        self.assertEqual(contract["missing_runner_options"], [])

    def test_round_and_revision_are_frozen(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            arguments = _arguments(Path(temporary))
            arguments[arguments.index("R692")] = "R693"
            args = RUNNER.build_parser().parse_args(arguments)
            with self.assertRaisesRegex(ValueError, "R691 -> R692"):
                RUNNER.validate_parameter_contract(args)

    def test_bootstrap_paths_are_operator_configurable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            requested = root / "portable" / "python.exe"
            candidates = BOOTSTRAP.runtime_candidates(
                requested=requested,
                workspace_root=None,
                repo_root=root,
                environment={},
            )
            self.assertEqual(candidates, [("--python", requested.resolve())])

    def test_generated_wrapper_dry_run_preserves_r692_arguments(self) -> None:
        canonical = r"\\.\pipe\xar_ck3_bridge_g2_m4_r692_faction_test"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            files = {
                "source-save/save.ck3": b"save",
                "bin/bridge.dll": b"dll",
                "bin/injector.exe": b"injector",
                "game/binaries/ck3.exe": b"exe",
                "source-repo/tools/bootstrap.py": b"raise SystemExit(99)\n",
            }
            for relative, data in files.items():
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            manifest = root / "candidate-manifest.json"
            manifest.write_text(
                json.dumps({"next_live": {"unique_pipe": canonical}}),
                encoding="utf-8",
            )
            wrapper = root / "run-r692.py"
            wrapper.write_text(
                WRAPPER.render_wrapper(
                    manifest_relative=manifest.name,
                    bootstrap_relative="source-repo/tools/bootstrap.py",
                    save_relative="source-save/save.ck3",
                    dll_relative="bin/bridge.dll",
                    injector_relative="bin/injector.exe",
                    save_name="save.ck3",
                    expected_save_sha256=_sha(root / "source-save/save.ck3"),
                    expected_dll_sha256=_sha(root / "bin/bridge.dll"),
                    expected_injector_sha256=_sha(root / "bin/injector.exe"),
                    expected_game_exe_sha256=_sha(root / "game/binaries/ck3.exe"),
                    expected_character_id=29829,
                    old_round="R691",
                    new_round="R692",
                    candidate_revision="6" * 40,
                    publish_timeout=90,
                ),
                encoding="utf-8-sig",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(wrapper),
                    "--python",
                    sys.executable,
                    "--game-dir",
                    str(root / "game"),
                    "--artifact-dir",
                    str(root / "artifact"),
                    "--state-dir",
                    str(root / "state"),
                    "--dry-run",
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["manifest_pipe"], canonical)
            self.assertEqual(payload["argument_pipe"], canonical)
            self.assertFalse(payload["ck3_launched"])


class R692TerminalContractTest(unittest.TestCase):
    @staticmethod
    def _probe(terminal: str, rows: list[dict[str, object]]) -> dict[str, object]:
        binding = {
            "paused": True,
            "proof_epoch": 42,
            "snapshot_revision": 412,
            "date_raw": 777,
            "player_character_id": 29829,
        }
        return {
            "private_build": True,
            "read_only": True,
            "advertised": False,
            "async_state": "terminal",
            "query_in_flight": False,
            "terminal_published": True,
            "last_submit_result": 1,
            "last_wait_result": 1,
            "last_reclaim_result": 1,
            "async_failure_flags": 0,
            "admission_generation": 2,
            "observer": {},
            "terminal_result": {
                "schema": "g2_faction_targeting_row_probe_v1",
                "private": True,
                "raw_pointers_persisted": False,
                "terminal": terminal,
                "unavailable_reasons": 0 if terminal != "unavailable" else 2,
                "observer_failure_flags": 0 if terminal != "unavailable" else 1,
                "published_generation": 2,
                "required_binding": binding,
                "observed_binding": dict(binding),
                "faction_count": len(rows),
                "factions": rows,
            },
        }

    def test_ready_and_known_empty_are_accepted(self) -> None:
        row = {
            "faction_id": 42,
            "target_character_id": 29829,
            "leader_character_id": 4001,
            "leader_present_in_character_members": True,
            "character_member_ids": [4001, 4002],
        }
        for terminal, rows in (("ready", [row]), ("known-empty", [])):
            probe = self._probe(terminal, rows)
            RUNNER.validate_probe_envelope(probe)
            result = RUNNER.validate_terminal_result(
                probe, expected_character_id=29829, expected_date_raw=777
            )
            self.assertEqual(result["terminal"], terminal)

    def test_typed_unavailable_remains_red(self) -> None:
        probe = self._probe("unavailable", [])
        with self.assertRaisesRegex(RuntimeError, "probe is unavailable"):
            RUNNER.validate_terminal_result(
                probe, expected_character_id=29829, expected_date_raw=777
            )


if __name__ == "__main__":
    unittest.main()
