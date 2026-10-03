"""Check exact engine selection and metadata used by disposable fixtures."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import fixture_engine_prepare as prep


class EngineIdentityTests(unittest.TestCase):
    def test_each_reviewed_executable_keeps_its_own_identity(self):
        for sha, (version, build) in prep.REVIEWED_BUILDS.items():
            with self.subTest(version=version), patch.object(prep, "digest", return_value=sha):
                identity = prep.engine_identity(Path("repo"))
                self.assertEqual(identity, {
                    "game_version": version, "steam_build_id": build, "exe_sha256": sha,
                })

    def test_unknown_executable_is_rejected_before_output_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            repo, output = base / "repo", base / "output"
            repo.mkdir()
            with patch.object(prep, "digest", return_value="0" * 64):
                with self.assertRaisesRegex(ValueError, "installed EXE differs"):
                    prep.checked_output(repo, output)
            self.assertFalse(output.exists())
            self.assertFalse(output.with_suffix(".prepare.json").exists())

    def test_common_receipt_uses_the_actual_engine_and_retains_not_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            source.mkdir()
            for sha, (version, build) in prep.REVIEWED_BUILDS.items():
                output = base / version
                output.mkdir()
                with patch.object(prep, "digest", return_value=sha):
                    receipt = prep.finish_receipt(base, source, output, [], {})
                self.assertEqual(receipt["game_version"], version)
                self.assertEqual(receipt["steam_build_id"], build)
                self.assertEqual(receipt["exe_sha256"], sha)
                self.assertEqual(receipt["runtime_status"], "NOT_RUN")
                self.assertFalse(receipt["native_abi_loaded"])
                self.assertFalse(receipt["gui_callbacks_mounted"])


if __name__ == "__main__":
    unittest.main()
