from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from ck3_autonomous_player.native_bridge.research.prepare_coat_of_arms_vfs_fixture import (
    FIRST_SOURCE,
    PATTERN_DIRECTORY,
    SECOND_SOURCE,
    prepare_fixture,
)


class PrepareCoatOfArmsVfsFixtureTests(unittest.TestCase):
    def test_builds_two_ordered_mods_with_shared_and_unique_byte_twins(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base_profile = root / "base-profile"
            base_profile.mkdir()
            (base_profile / "pdx_settings.txt").write_text(
                "language=l_english\n", encoding="utf-8"
            )
            patterns = root / "game" / PATTERN_DIRECTORY
            patterns.mkdir(parents=True)
            (patterns / FIRST_SOURCE).write_bytes(b"DDS first fixture")
            (patterns / SECOND_SOURCE).write_bytes(b"DDS second fixture")
            output = root / "fixture"

            receipt = prepare_fixture(base_profile, root / "game", output)

            load = json.loads((output / "dlc_load.json").read_text(encoding="utf-8"))
            self.assertEqual(
                load["enabled_mods"],
                ["mod/coa_vfs_fixture_first.mod", "mod/coa_vfs_fixture_second.mod"],
            )
            self.assertEqual(receipt["enabled_mods"], load["enabled_mods"])
            first = receipt["mods"][0]
            second = receipt["mods"][1]
            self.assertEqual(first["source_dds_sha256"], first["shared_dds_sha256"])
            self.assertEqual(first["source_dds_sha256"], first["reference_dds_sha256"])
            self.assertEqual(second["source_dds_sha256"], second["shared_dds_sha256"])
            self.assertEqual(second["source_dds_sha256"], second["reference_dds_sha256"])
            self.assertNotEqual(first["source_dds_sha256"], second["source_dds_sha256"])
            self.assertIn(
                "pattern_xar_vfs_shared.dds",
                Path(first["manifest_path"]).read_text(encoding="utf-8"),
            )
            with self.assertRaises(FileExistsError):
                prepare_fixture(base_profile, root / "game", output)


if __name__ == "__main__":
    unittest.main()
