"""Check exact engine selection and metadata used by disposable fixtures."""
from pathlib import Path
import runpy
import shutil
import tempfile
import unittest
from unittest.mock import patch

import fixture_engine_prepare as prep


REGISTRY_RELATIVE = Path("ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py")
REGISTRY_SOURCE = Path(__file__).resolve().parents[1] / REGISTRY_RELATIVE
REVIEWED_IDENTITIES = tuple(
    identity for identity in runpy.run_path(str(REGISTRY_SOURCE))["NATIVE_BUILD_IDENTITIES"]
    if identity.game_version.startswith("1.20.")
)


class EngineIdentityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.repo = self.base / "repo"
        registry = self.repo / REGISTRY_RELATIVE
        registry.parent.mkdir(parents=True)
        shutil.copyfile(REGISTRY_SOURCE, registry)
        environment = patch.dict(prep.os.environ, {
            "XAR_CK3_GAME_DIR": "", "XAR_CK3_STEAM_MANIFEST": "",
        })
        environment.start()
        self.addCleanup(environment.stop)

    def test_each_reviewed_executable_keeps_its_own_identity(self):
        for build in REVIEWED_IDENTITIES:
            sha = build.executable_sha256.lower()
            with self.subTest(version=build.game_version), patch.object(prep, "digest", return_value=sha):
                identity = prep.engine_identity(self.repo)
                self.assertEqual(identity, {
                    "game_version": build.game_version, "steam_build_id": "unknown", "exe_sha256": sha,
                })

    def test_unknown_executable_is_rejected_before_output_creation(self):
        output = self.base / "output"
        with patch.object(prep, "digest", return_value="0" * 64):
            with self.assertRaisesRegex(ValueError, "installed EXE differs"):
                prep.checked_output(self.repo, output)
        self.assertFalse(output.exists())
        self.assertFalse(output.with_suffix(".prepare.json").exists())

    def test_common_receipt_uses_the_actual_engine_and_retains_not_run(self):
        source = self.base / "source"
        source.mkdir()
        for build in REVIEWED_IDENTITIES:
            sha = build.executable_sha256.lower()
            output = self.base / build.game_version
            output.mkdir()
            with patch.object(prep, "digest", return_value=sha):
                receipt = prep.finish_receipt(self.repo, source, output, [], {})
            self.assertEqual(receipt["game_version"], build.game_version)
            self.assertEqual(receipt["steam_build_id"], "unknown")
            self.assertEqual(receipt["exe_sha256"], sha)
            self.assertEqual(receipt["runtime_status"], "NOT_RUN")
            self.assertFalse(receipt["native_abi_loaded"])
            self.assertFalse(receipt["gui_callbacks_mounted"])


if __name__ == "__main__":
    unittest.main()
