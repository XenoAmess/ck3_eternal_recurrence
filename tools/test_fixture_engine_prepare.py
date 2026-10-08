"""Check exact engine selection and metadata used by disposable fixtures."""
import importlib.util
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

import fixture_engine_prepare as prep


REPO = Path(__file__).resolve().parents[1]
REGISTRY = Path("ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py")
STEAM_PARSER = Path("ck3_autonomous_player/src/xar_autoplayer/steam_workshop_status.py")


def native_builds():
    """Use the production registry; do not maintain a second version/SHA map."""
    name = "_fixture_engine_test_native_registry"
    spec = importlib.util.spec_from_file_location(name, REPO / REGISTRY)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
        return tuple(build for build in module.NATIVE_BUILD_IDENTITIES
                     if build.game_version.startswith("1.20."))
    finally:
        sys.modules.pop(name, None)


def complete_fixture(base):
    """Supply both source dependencies and explicit mock Steam metadata."""
    repo = base / "repo"
    for relative in (REGISTRY, STEAM_PARSER):
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / relative, target)
    game = repo / "Crusader Kings III"
    game.mkdir()
    manifest = base / "appmanifest_1158310.acf"
    manifest.write_text('"AppState" { "appid" "1158310" "buildid" "31415926" }\n',
                        encoding="utf-8")
    environment = {"XAR_CK3_GAME_DIR": str(game),
                   "XAR_CK3_STEAM_MANIFEST": str(manifest)}
    return repo, environment


class EngineIdentityTests(unittest.TestCase):
    def test_each_reviewed_executable_keeps_its_own_identity(self):
        builds = native_builds()
        self.assertTrue(builds)
        with tempfile.TemporaryDirectory() as temporary:
            repo, environment = complete_fixture(Path(temporary))
            for build in builds:
                sha = build.executable_sha256.lower()
                with self.subTest(version=build.game_version), \
                        patch.dict(os.environ, environment, clear=True), \
                        patch.object(prep, "digest", return_value=sha):
                    identity = prep.engine_identity(repo)
                    self.assertEqual(identity, {
                        "game_version": build.game_version,
                        "steam_build_id": "31415926", "exe_sha256": sha,
                    })

    def test_unknown_executable_is_rejected_before_output_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            repo, environment = complete_fixture(base)
            output = base / "output"
            with patch.dict(os.environ, environment, clear=True), \
                    patch.object(prep, "digest", return_value="0" * 64):
                with self.assertRaisesRegex(ValueError, "installed EXE differs"):
                    prep.checked_output(repo, output)
            self.assertFalse(output.exists())
            self.assertFalse(output.with_suffix(".prepare.json").exists())

    def test_common_receipt_uses_the_actual_engine_and_retains_not_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            repo, environment = complete_fixture(base)
            source = base / "source"
            source.mkdir()
            for build in native_builds():
                output = base / build.game_version
                output.mkdir()
                sha = build.executable_sha256.lower()
                with patch.dict(os.environ, environment, clear=True), \
                        patch.object(prep, "digest", return_value=sha):
                    receipt = prep.finish_receipt(repo, source, output, [], {})
                self.assertEqual(receipt["game_version"], build.game_version)
                self.assertEqual(receipt["steam_build_id"], "31415926")
                self.assertEqual(receipt["exe_sha256"], sha)
                self.assertEqual(receipt["runtime_status"], "NOT_RUN")
                self.assertFalse(receipt["native_abi_loaded"])
                self.assertFalse(receipt["gui_callbacks_mounted"])


if __name__ == "__main__":
    unittest.main()
