"""No-launch regression for R0107's old DLL and forged build provenance."""

import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "ck3_autonomous_player" / "src"))

from capture_session import (  # noqa: E402
    A04_UI_TARGETS, BATTLE_CONTROL_PAIR_SCHEMA, BATTLE_CONTROL_WIRE_MARKERS,
    identity, validate_d11_battle_control_pair,
)
from xar_autoplayer.bridge import battle_control_contract  # noqa: E402


NATIVE = REPO / "ck3_autonomous_player" / "native_bridge"
SERIALIZER = NATIVE / "src" / "battle_control_snapshot_v1_mailbox.cpp"
HELPER = NATIVE / "tools" / "build_fresh.py"
TEST_NAME = "xar_ck3_native_bridge_battle_control_snapshot_v1_mailbox"
OLD_DLL = Path(
    "D:/wai/ck3_autonomous_player/native_bridge/"
    "build-fresh-20260927T025104Z-572e2125/xar_ck3_bridge.dll"
)
OLD_SHA = "1CC2AE965CD0EE897F918D50AF038F3DA874354DA7F3A57D2710B7BCCF44366F"


def fingerprint() -> str:
    return runpy.run_path(str(HELPER))["native_bridge_source_fingerprint"](NATIVE)


def write_json(path: Path, value: object) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def checkpoint() -> dict:
    return {"save": {"sha256": A04_UI_TARGETS["e2-06-d11"]["save"][2]}}


class D11BattleControlPairTest(unittest.TestCase):
    def pair(self, root: Path, dll: Path, injector: Path,
             *, junit_failure: bool = False, ctest_exit: int = 0,
             dependency_failure: bool = False, cache_release: bool = True,
             tracked_status: str = "") -> tuple[Path, Path]:
        source_sha = fingerprint()
        build_script = root / "build_release_candidate.py"
        build_script.write_text("# focused build fixture\n", encoding="utf-8")
        cmake_cache = root / "CMakeCache.txt"
        cmake_cache.write_text(
            "CMAKE_BUILD_TYPE:STRING=Release\n" if cache_release else
            "CMAKE_BUILD_TYPE:STRING=Debug\n", encoding="utf-8")
        def receipt(stem: str, value: object) -> dict:
            path = write_json(root / f"{stem}.json", value)
            return {f"{stem}_path": str(path), f"{stem}_sha256": identity(path)["sha256"]}

        source = {
            "head": subprocess.run(["git", "-C", str(NATIVE), "rev-parse", "HEAD"],
                                   capture_output=True, text=True, check=True).stdout.strip(),
            "source_fingerprint_sha256": source_sha,
            "native_bridge_fingerprint_sha256": source_sha,
            "build_fresh_helper": identity(HELPER),
            "build_script_sha256": identity(build_script)["sha256"],
            "configuration": "Release",
            "tracked_status": tracked_status,
        }
        parts = {}
        for stem in ("source_before", "source_after"):
            parts.update(receipt(stem, source))
        parts.update(receipt("configure_argv", {"argv": [
            "cmake", "-S", str(NATIVE), "-B", str(root), "-DCMAKE_BUILD_TYPE=Release",
        ]}))
        parts.update(receipt("configure_result", {"exit_code": 0}))
        parts.update(receipt("build_argv", {"argv": [
            "cmake", "--build", str(root), "--target", "xar_ck3_bridge",
            "xar_ck3_bridge_injector", "xar_ck3_battle_control_snapshot_v1_mailbox_test",
        ]}))
        parts.update(receipt("build_result", {"exit_code": 0}))
        dependency_rows = []
        for index, obj in enumerate(runpy.run_path(str(HELPER))["DEPENDENCY_OBJECTS"]):
            refs = {}
            for kind, value in (
                ("argv", {"argv": ["ninja", "-C", str(root), "-t", "deps", obj]}),
                ("result", {"exit_code": 0}),
            ):
                path = write_json(root / f"dependency-{index}-{kind}.json", value)
                refs[f"{kind}_path"] = str(path)
                refs[f"{kind}_sha256"] = identity(path)["sha256"]
            for kind, content in (
                ("stdout", "#deps 2\n" + ("wrong_header.hpp" if dependency_failure else "ck3_11906.hpp") + "\n"),
                ("stderr", ""),
            ):
                path = root / f"dependency-{index}-{kind}.txt"
                path.write_text(content, encoding="utf-8")
                refs[f"{kind}_path"] = str(path)
                refs[f"{kind}_sha256"] = identity(path)["sha256"]
            dependency_rows.append({"object": obj, **refs,
                                    "ck3_11906_header_recorded": True,
                                    "positive_dependency_count": True})
        parts.update(receipt("dependency_receipt", {
            "schema": "xar.promo.e204-native-dependency/v1",
            "source_fingerprint_sha256": source_sha,
            "objects": dependency_rows,
        }))
        junit = root / "ctest-junit.xml"
        junit.write_text(
            '<testsuite tests="1" failures="1" errors="0" skipped="0">'
            f'<testcase name="{TEST_NAME}"><failure>RED</failure></testcase></testsuite>'
            if junit_failure else
            '<testsuite tests="1" failures="0" errors="0" skipped="0">'
            f'<testcase name="{TEST_NAME}"/></testsuite>', encoding="utf-8")
        parts.update(receipt("ctest_argv", {"argv": [
            "ctest", "--test-dir", str(root), "--output-on-failure", "-R",
            f"^{TEST_NAME}$", "--output-junit", str(junit),
        ]}))
        parts.update(receipt("ctest_result", {"exit_code": ctest_exit,
                                               "returncode": ctest_exit}))
        stdout = root / "ctest-stdout.txt"
        stdout.write_text(f"1/1 Test #1: {TEST_NAME}\n100% tests passed\n", encoding="utf-8")
        parts.update({"ctest_stdout_path": str(stdout),
                      "ctest_stdout_sha256": identity(stdout)["sha256"],
                      "ctest_junit_path": str(junit),
                      "ctest_junit_sha256": identity(junit)["sha256"]})
        normal = write_json(root / "python-normal-result.json", {"exit_code": 0})
        optimized = write_json(root / "python-optimized-result.json", {"exit_code": 0})
        tests = {
            "ctest": {"result_path": parts["ctest_result_path"],
                      "result_sha256": parts["ctest_result_sha256"]},
            "python-normal": {"result_path": str(normal),
                              "result_sha256": identity(normal)["sha256"]},
            "python-optimized": {"result_path": str(optimized),
                                 "result_sha256": identity(optimized)["sha256"]},
        }
        report = write_json(root / "candidate-manifest.json", {
            "status": "STATIC_RELEASE_CANDIDATE_NO_CK3_LAUNCH",
            "build_status": "READY", "head": source["head"],
            "build_dir": str(root), "configuration": "Release",
            "cmake_cache_path": str(cmake_cache),
            "cmake_cache_sha256": identity(cmake_cache)["sha256"],
            "source_fingerprint_sha256": source_sha,
            "native_serializer_sha256": identity(SERIALIZER)["sha256"],
            "python_contracts_sha256": {
                "battle_control_contract.py": identity(Path(battle_control_contract.__file__))["sha256"]},
            "dll": identity(dll), "injector": identity(injector),
            "dll_sha256": identity(dll)["sha256"],
            "injector_sha256": identity(injector)["sha256"],
            "tests_ran": True,
            "test_scope": "current-battle-knight-mailbox-and-python-port",
            "dependency_gate": "ck3_11906.hpp-recorded",
            "build_script_sha256": identity(build_script)["sha256"],
            "ctest_name": TEST_NAME, "tests": tests, **parts,
        })
        pair = write_json(root / "pair.json", {
            "schema": BATTLE_CONTROL_PAIR_SCHEMA, "build_status": "READY",
            "build_report": {"path": str(report), "sha256": identity(report)["sha256"]},
            "source_fingerprint_sha256": source_sha,
            "native_serializer_sha256": identity(SERIALIZER)["sha256"],
            "python_contract_sha256": identity(Path(battle_control_contract.__file__))["sha256"],
            "dll_sha256": identity(dll)["sha256"],
            "injector_sha256": identity(injector)["sha256"],
            "battle_control_ctest_passed": True,
        })
        return pair, report

    @staticmethod
    def rebind_report(pair: Path, report: Path) -> None:
        value = json.loads(pair.read_text(encoding="utf-8"))
        value["build_report"]["sha256"] = identity(report)["sha256"]
        write_json(pair, value)

    def test_current_source_pair_passes_static_gate_only(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            dll, injector = root / "current.dll", root / "injector.exe"
            dll.write_bytes(b"\0".join(BATTLE_CONTROL_WIRE_MARKERS))
            injector.write_bytes(b"fixture injector")
            pair, _ = self.pair(root, dll, injector)
            result = validate_d11_battle_control_pair(checkpoint(), pair, dll, injector)
            self.assertTrue(result["wire_markers_present"])
            self.assertFalse(result["native_query_verified"])

    def test_fake_build_report_rejected_even_when_pair_hash_matches(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            dll, injector = root / "current.dll", root / "injector.exe"
            dll.write_bytes(b"\0".join(BATTLE_CONTROL_WIRE_MARKERS))
            injector.write_bytes(b"fixture injector")
            pair, report = self.pair(root, dll, injector)
            write_json(report, {"status": "READY", "ctest": "PASS"})
            self.rebind_report(pair, report)
            with self.assertRaisesRegex(RuntimeError, "lacks required provenance"):
                validate_d11_battle_control_pair(checkpoint(), pair, dll, injector)

    def test_failed_junit_and_ctest_result_rejected(self) -> None:
        for junit_failure, ctest_exit, error in (
            (True, 0, "JUnit testcase"), (False, 1, "CTest command or result"),
        ):
            with self.subTest(junit_failure=junit_failure, ctest_exit=ctest_exit):
                with tempfile.TemporaryDirectory() as folder:
                    root = Path(folder)
                    dll, injector = root / "current.dll", root / "injector.exe"
                    dll.write_bytes(b"\0".join(BATTLE_CONTROL_WIRE_MARKERS))
                    injector.write_bytes(b"fixture injector")
                    pair, _ = self.pair(root, dll, injector,
                                        junit_failure=junit_failure, ctest_exit=ctest_exit)
                    with self.assertRaisesRegex(RuntimeError, error):
                        validate_d11_battle_control_pair(checkpoint(), pair, dll, injector)

    def test_fake_dependency_receipt_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            dll, injector = root / "current.dll", root / "injector.exe"
            dll.write_bytes(b"\0".join(BATTLE_CONTROL_WIRE_MARKERS))
            injector.write_bytes(b"fixture injector")
            pair, _ = self.pair(root, dll, injector, dependency_failure=True)
            with self.assertRaisesRegex(RuntimeError, "Ninja dependency evidence"):
                validate_d11_battle_control_pair(checkpoint(), pair, dll, injector)

    def test_debug_cache_and_dirty_source_rejected(self) -> None:
        for options, error in (
            ({"cache_release": False}, "status or directory"),
            ({"tracked_status": " M native.cpp"}, "tracked source changes"),
        ):
            with self.subTest(options=options):
                with tempfile.TemporaryDirectory() as folder:
                    root = Path(folder)
                    dll, injector = root / "current.dll", root / "injector.exe"
                    dll.write_bytes(b"\0".join(BATTLE_CONTROL_WIRE_MARKERS))
                    injector.write_bytes(b"fixture injector")
                    pair, _ = self.pair(root, dll, injector, **options)
                    with self.assertRaisesRegex(RuntimeError, error):
                        validate_d11_battle_control_pair(checkpoint(), pair, dll, injector)

    def test_python_contract_from_another_checkout_rejected_even_with_same_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            dll, injector = root / "current.dll", root / "injector.exe"
            dll.write_bytes(b"\0".join(BATTLE_CONTROL_WIRE_MARKERS))
            injector.write_bytes(b"fixture injector")
            pair, _ = self.pair(root, dll, injector)
            rogue = root / "battle_control_contract.py"
            rogue.write_bytes(Path(battle_control_contract.__file__).read_bytes())
            original = battle_control_contract.__file__
            try:
                battle_control_contract.__file__ = str(rogue)
                with self.assertRaisesRegex(RuntimeError, "loaded from another checkout"):
                    validate_d11_battle_control_pair(checkpoint(), pair, dll, injector)
            finally:
                battle_control_contract.__file__ = original

    @unittest.skipUnless(OLD_DLL.is_file(), "R0107 exact old DLL is not present")
    def test_r0107_pinned_old_dll_rejected_before_launch(self) -> None:
        self.assertEqual(identity(OLD_DLL)["sha256"], OLD_SHA)
        self.assertIn(b"side_0_current_roll_points", OLD_DLL.read_bytes())
        self.assertNotIn(BATTLE_CONTROL_WIRE_MARKERS[0], OLD_DLL.read_bytes())
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            dll = root / "r0107-exact-bytes.dll"
            dll.write_bytes(OLD_DLL.read_bytes())
            self.assertEqual(identity(dll)["sha256"], OLD_SHA)
            injector = root / "injector.exe"
            injector.write_bytes(b"fixture injector")
            pair, _ = self.pair(root, dll, injector)
            with self.assertRaisesRegex(RuntimeError, "lacks current battle-control"):
                validate_d11_battle_control_pair(checkpoint(), pair, dll, injector)

    def test_d11_requires_manifest_and_other_tracks_reject_it(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "manifest is required"):
            validate_d11_battle_control_pair(checkpoint(), None, Path("missing"), Path("missing"))
        with self.assertRaisesRegex(RuntimeError, "only for the exact d11"):
            validate_d11_battle_control_pair(None, Path("unused.json"), Path("missing"), Path("missing"))


if __name__ == "__main__":
    unittest.main()
