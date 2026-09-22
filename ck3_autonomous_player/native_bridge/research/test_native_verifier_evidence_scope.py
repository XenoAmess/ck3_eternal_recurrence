"""Focused subprocess checks for verifier scope and normal/-O rejection parity.

The optional --exact-exe path adds read-only checks against a local frozen EXE.
No test starts or attaches to CK3; ordinary repository tests need no game files.
Use the same interpreter environment as the building verifier (pefile required).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
NATIVE_ROOT = HERE.parent
BUILDING = HERE / "verify_player_world_building_definition_source_v1.py"
MARRIAGE = HERE / "verify_marriage_matchmaking_observer_v1.py"
MARRIAGE_ABI = "marriage_matchmaking_observer_v1_abi.json"
MARRIAGE_CONTRACT = "fixtures/marriage_matchmaking_observer_v1_source_contract.json"
EXACT_EXE: Path | None = None


class VerifierEvidenceScopeTests(unittest.TestCase):
    def _run(self, arguments: list[str], optimized: bool) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, *(["-O"] if optimized else []), *arguments],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )

    def _rejected(self, result: subprocess.CompletedProcess[str], reason: str) -> None:
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(f"RED: {reason}", result.stderr)
        self.assertNotIn("GREEN", result.stdout)
        self.assertNotIn("EVIDENCE_SCOPE ", result.stdout)

    def _scope(self, result: subprocess.CompletedProcess[str]) -> dict[str, object]:
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = [line.removeprefix("EVIDENCE_SCOPE ")
                for line in result.stdout.splitlines() if line.startswith("EVIDENCE_SCOPE ")]
        self.assertEqual(len(rows), 1, result.stdout)
        scope = json.loads(rows[0])
        self.assertIs(scope["game_process_started"], False)
        self.assertIn("live-behavior", scope["not_verified"])
        self.assertIn("complete-decision-semantics", scope["not_verified"])
        return scope

    def _marriage_fixture(self, root: Path) -> None:
        contract = json.loads((HERE / MARRIAGE_CONTRACT).read_text(encoding="utf-8"))
        files = [*contract["files"].values(), f"research/{MARRIAGE_ABI}",
                 f"research/{MARRIAGE_CONTRACT}"]
        for relative in files:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(NATIVE_ROOT / relative, target)

    def test_building_rejects_wrong_executable_hash_before_pe_parsing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            wrong_exe = Path(temporary) / "wrong-executable.bin"
            wrong_exe.write_bytes(b"not the frozen CK3 executable")
            for optimized in (False, True):
                with self.subTest(optimized=optimized):
                    result = self._run([str(BUILDING), "--exe", str(wrong_exe)], optimized)
                    self._rejected(result, "executable SHA-256 mismatch")

    def test_building_rejects_invalid_or_truncated_instruction_encodings(self) -> None:
        probe = """
import sys
sys.path.insert(0, sys.argv[1])
import verify_player_world_building_definition_source_v1 as verifier
class FixturePe:
    def get_data(self, source, size):
        return bytes.fromhex(sys.argv[3])
getattr(verifier, sys.argv[2])(FixturePe(), 0x1000)
"""
        cases = (
            ("call_target", "e900000000", "not a complete direct stock call"),
            ("call_target", "e8", "not a complete direct stock call"),
            ("rip_target", "48890500000000", "not a complete RIP-relative MOV/LEA"),
            ("rip_target", "488b", "not a complete RIP-relative MOV/LEA"),
            ("rip_target", "488b0000000000", "not a RIP-relative operand"),
        )
        for optimized in (False, True):
            for helper, encoded, reason in cases:
                with self.subTest(optimized=optimized, helper=helper, encoded=encoded):
                    result = self._run(["-c", probe, str(HERE), helper, encoded], optimized)
                    self._rejected(result, reason)

    def test_marriage_success_reports_only_repository_checks(self) -> None:
        for optimized in (False, True):
            with self.subTest(optimized=optimized):
                result = self._run([str(MARRIAGE), "--native-root", str(NATIVE_ROOT)], optimized)
                self.assertIn("GREEN: marriage-matchmaking-observer-v1 source contract", result.stdout)
                scope = self._scope(result)
                self.assertEqual(scope["evidence_scope"], "repository-contract")
                self.assertIn("required-source-tokens", scope["verified"])
                self.assertIn("executable-bytes", scope["not_verified"])

    def test_marriage_rejects_missing_source_token(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            native_root = Path(temporary)
            self._marriage_fixture(native_root)
            contract = json.loads((HERE / MARRIAGE_CONTRACT).read_text(encoding="utf-8"))
            (native_root / contract["files"]["header"]).write_text("", encoding="utf-8")
            for optimized in (False, True):
                with self.subTest(optimized=optimized):
                    result = self._run([str(MARRIAGE), "--native-root", str(native_root)], optimized)
                    self._rejected(result, "header token missing")

    def test_marriage_rejects_changed_ranked_row_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            native_root = Path(temporary)
            self._marriage_fixture(native_root)
            abi_path = native_root / "research" / MARRIAGE_ABI
            abi = json.loads(abi_path.read_text(encoding="utf-8"))
            abi["ranked_row_layout"]["stride_bytes"] = 17
            abi_path.write_text(json.dumps(abi), encoding="utf-8")
            for optimized in (False, True):
                with self.subTest(optimized=optimized):
                    result = self._run([str(MARRIAGE), "--native-root", str(native_root)], optimized)
                    self._rejected(result, "ranked row stride drifted")

    def test_exact_building_success_reports_static_chain_scope(self) -> None:
        if EXACT_EXE is None:
            self.skipTest("pass --exact-exe for the local read-only static-chain check")
        for optimized in (False, True):
            with self.subTest(optimized=optimized):
                result = self._run([str(BUILDING), "--exe", str(EXACT_EXE)], optimized)
                self.assertIn("GREEN exact CBuildingType manager vector/player final-legality source", result.stdout)
                scope = self._scope(result)
                self.assertEqual(scope["evidence_scope"], "exact-build-static-chain")
                self.assertIn("executable-and-span-bytes", scope["verified"])
                self.assertIn("RTTI-type-chain", scope["verified"])

    def test_exact_building_rejects_changed_span_contract(self) -> None:
        if EXACT_EXE is None:
            self.skipTest("pass --exact-exe for the local span rejection check")
        probe = """
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import verify_player_world_building_definition_source_v1 as verifier
verifier.ABI = Path(sys.argv[2])
verifier.verify(Path(sys.argv[3]))
"""
        with tempfile.TemporaryDirectory() as temporary:
            abi = json.loads(BUILDING.with_name("player_world_building_definition_source_v1_abi.json")
                             .read_text(encoding="utf-8"))
            abi["exact_regions"][0]["sha256"] = "0" * 64
            changed = Path(temporary) / "changed-span-contract.json"
            changed.write_text(json.dumps(abi), encoding="utf-8")
            for optimized in (False, True):
                with self.subTest(optimized=optimized):
                    result = self._run(["-c", probe, str(HERE), str(changed), str(EXACT_EXE)], optimized)
                    self._rejected(result, "source span")
                    self.assertIn("SHA-256 mismatch", result.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exact-exe", type=Path)
    arguments, remaining = parser.parse_known_args()
    EXACT_EXE = arguments.exact_exe
    unittest.main(argv=[sys.argv[0], *remaining])
