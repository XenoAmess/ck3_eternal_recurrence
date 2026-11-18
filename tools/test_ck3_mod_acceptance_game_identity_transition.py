"""Installation migration consumer tests with an authored OS hash boundary.

Only the executable hash read is replaced; the actual launcher parser, exact
SDK identity lookup, receipt pins and qualified-source tuple consumer execute.
No Game, Native DLL, injector or Steam process is started.
"""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "ck3_autonomous_player/src")]
import ck3_mod_acceptance_build_runtime as builder
from xar_autoplayer.bridge.version_identity import CK3_1210


class RuntimeGameIdentityTransitionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="authored-game-identity-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.base = self.root / "base-runtime.json"
        self.base.write_text('{"authored":"immutable base identity"}', encoding="utf-8")
        self.old_game = {"version": "1.20.0.4", "exe_sha256": "a" * 64}
        self.manifest = {"game": dict(self.old_game)}
        self.installation = self.root / "installed"
        self.exe = self.installation / "binaries/ck3.exe"
        self.exe.parent.mkdir(parents=True)
        self.exe.write_bytes(b"authored executable hash observation boundary; never executed")
        self.settings = self.installation / "launcher/launcher-settings.json"
        self.settings.parent.mkdir()
        self.write_settings()
        self.native = self.root / "qualified-native-snapshot"
        self.header = self.native / "include/xar_bridge/ck3_1210.hpp"
        self.header.parent.mkdir(parents=True)
        self.header.write_text(
            'inline constexpr char kGameVersion[] = "1.21.0";\n'
            'inline constexpr char kAdapterId[] = "ck3-1.21.0-msvc-x64";\n'
            'inline constexpr char kExecutableSha256[] = "' + CK3_1210.executable_sha256 + '";\n',
            encoding="utf-8")
        self.adapter = self.native / "src/ck3_1210_adapter.cpp"
        self.adapter.parent.mkdir()
        self.adapter.write_text('#include "xar_bridge/ck3_1210.hpp"\n'
            'descriptor{ck3_1210::kAdapterId, ck3_1210::kGameVersion, ck3_1210::kExecutableSha256};\n',
            encoding="utf-8")
        self.snapshot = self.root / "source-snapshot.json"
        self.save_snapshot()
        self.qualified = self.root / "qualified-native.json"
        self.save(self.qualified, {"snapshot": builder.pin(self.snapshot)})
        self.bundle = {"qualification_ref": builder.pin(self.qualified), "snapshot_root": str(self.native),
            "native_files": {builder.NATIVE_PREFIX + "src/ck3_1210_adapter.cpp":
                             builder.sig(self.adapter.read_bytes())}}
        self.observed_exe = {**builder.pin(self.exe), "sha256": CK3_1210.executable_sha256.lower()}
        self.value = {"schema": "ck3-runtime-game-identity-transition-v1", "machine_id": "authored-machine",
            "source_commit": "b" * 40, "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "base_runtime": builder.pin(self.base), "previous_game": dict(self.old_game),
            "qualified_native": builder.pin(self.qualified), "game_dir": str(self.installation),
            "executable": self.observed_exe, "launcher_settings": builder.pin(self.settings)}
        self.transition = self.root / "actual-installation-transition.json"
        self.real_pin = builder.pin

    @staticmethod
    def save(path: Path, value: object) -> None:
        path.write_text(json.dumps(value), encoding="utf-8")

    def write_settings(self, version: str = "1.21.0", exe_path: str = "../binaries/ck3.exe") -> None:
        self.save(self.settings, {"rawVersion": version, "exePath": exe_path})

    def save_snapshot(self) -> None:
        reference = builder.pin(self.header)
        self.save(self.snapshot, {"snapshot_native_base": str(self.native), "files": [{
            "native_relative": "include/xar_bridge/ck3_1210.hpp",
            "bytes": reference["bytes"], "sha256": reference["sha256"]}]})

    def observed_pin(self, path: Path | str) -> dict[str, object]:
        if Path(path).resolve() == self.exe:
            return dict(self.observed_exe)
        return self.real_pin(path)

    def select(self) -> builder.RuntimeGameIdentitySelection:
        self.save(self.transition, self.value)
        with patch.object(builder, "pin", side_effect=self.observed_pin):
            return builder.select_runtime_game_identity(self.transition, base_runtime=self.base,
                manifest=self.manifest, native_bundle=self.bundle, machine="authored-machine", commit="b" * 40)

    def refresh_qualified_snapshot(self) -> None:
        self.save_snapshot()
        self.save(self.qualified, {"snapshot": builder.pin(self.snapshot)})
        self.bundle["qualification_ref"] = builder.pin(self.qualified)
        self.value["qualified_native"] = builder.pin(self.qualified)

    def test_absent_transition_preserves_old_scene_without_installation_reads(self) -> None:
        original = deepcopy(self.manifest)
        with patch.object(builder, "pin", side_effect=AssertionError("old scene must remain independent")):
            selected = builder.select_runtime_game_identity(None, base_runtime=self.base,
                manifest=self.manifest, native_bundle={}, machine="authored-machine", commit="b" * 40)
        self.assertEqual(selected.game, self.old_game)
        self.assertIsNone(selected.game_directory)
        self.assertIsNone(selected.transition)
        self.assertEqual(self.manifest, original)

    def test_real_known_tuple_reaches_launcher_sdk_and_compiled_descriptor_consumers(self) -> None:
        original = deepcopy(self.manifest)
        selected = self.select()
        self.assertEqual(selected.game, {"version": CK3_1210.game_version,
            "exe_sha256": CK3_1210.executable_sha256.lower()})
        self.assertEqual(selected.game_directory, self.installation)
        self.assertEqual(selected.transition, builder.pin(self.transition))
        self.assertEqual(self.manifest, original)

    def test_machine_commit_base_and_native_qualification_cannot_cross(self) -> None:
        original = deepcopy(self.value)
        other = self.root / "foreign.json"
        self.save(other, {"foreign": True})
        for field, value in (("machine_id", "other"), ("source_commit", "c" * 40),
                             ("previous_game", {"version": "foreign", "exe_sha256": "a" * 64}),
                             ("base_runtime", builder.pin(other)), ("qualified_native", builder.pin(other))):
            with self.subTest(field=field):
                self.value = {**original, field: value}
                with self.assertRaises(ValueError):
                    self.select()

    def test_actual_launcher_version_and_executable_path_must_match(self) -> None:
        for version, path in (("1.20.0.4", "../binaries/ck3.exe"), ("1.21.0", "../binaries/other.exe")):
            with self.subTest(version=version, path=path):
                self.write_settings(version, path)
                self.value["launcher_settings"] = builder.pin(self.settings)
                with self.assertRaises(ValueError):
                    self.select()

    def test_unknown_executable_hash_cannot_be_blessed_by_receipt(self) -> None:
        self.observed_exe["sha256"] = "f" * 64
        with self.assertRaises(ValueError):
            self.select()

    def test_native_header_tuple_must_agree_even_when_its_snapshot_pin_is_valid(self) -> None:
        self.header.write_text(self.header.read_text().replace(CK3_1210.executable_sha256, "F" * 64),
                               encoding="utf-8")
        self.refresh_qualified_snapshot()
        with self.assertRaisesRegex(ValueError, "Native adapter identity"):
            self.select()

    def test_header_presence_alone_does_not_prove_compiled_adapter(self) -> None:
        self.bundle["native_files"] = {}
        with self.assertRaisesRegex(ValueError, "production translation unit"):
            self.select()

    def test_compiled_adapter_must_consume_identity_constants(self) -> None:
        self.adapter.write_text("descriptor{unrelated_version, unrelated_sha};", encoding="utf-8")
        self.bundle["native_files"] = {builder.NATIVE_PREFIX + "src/ck3_1210_adapter.cpp":
                                       builder.sig(self.adapter.read_bytes())}
        with self.assertRaisesRegex(ValueError, "descriptor"):
            self.select()


if __name__ == "__main__":
    unittest.main()
