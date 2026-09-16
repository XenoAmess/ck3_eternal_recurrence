from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from ck3_autonomous_player.native_bridge.research.prepare_coat_of_arms_vfs_fixture import (
    ARCHIVE_LATER_REFERENCE,
    ARCHIVE_SHARED,
    BASE_MOD_REFERENCE,
    BASE_ORIGINAL_REFERENCE,
    FIRST_SOURCE,
    PATTERN_DIRECTORY,
    REPLACED_EARLIER,
    REPLACE_LATER_REFERENCE,
    SECOND_SOURCE,
    SOLID_SOURCE,
    prepare_extended_fixture,
    prepare_fixture,
    prepare_replace_path_fixture,
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

    def test_builds_base_mod_and_directory_archive_precedence_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base_profile = root / "base-profile"
            base_profile.mkdir()
            (base_profile / "pdx_settings.txt").write_text(
                "language=l_english\n", encoding="utf-8"
            )
            patterns = root / "game" / PATTERN_DIRECTORY
            patterns.mkdir(parents=True)
            (patterns / FIRST_SOURCE).write_bytes(b"DDS base fixture")
            (patterns / SECOND_SOURCE).write_bytes(b"DDS override fixture")
            output = root / "fixture"

            receipt = prepare_extended_fixture(base_profile, root / "game", output)

            load = json.loads((output / "dlc_load.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["schema"], "ck3-coat-of-arms-vfs-extended-fixture-v1")
            self.assertEqual(load["enabled_mods"], receipt["enabled_mods"])
            self.assertEqual(len(load["enabled_mods"]), 3)
            self.assertEqual(
                receipt["base_vs_mod"]["base_source_sha256"],
                receipt["base_vs_mod"]["base_reference_sha256"],
            )
            self.assertEqual(
                receipt["base_vs_mod"]["mod_source_sha256"],
                receipt["base_vs_mod"]["mod_conflict_sha256"],
            )
            self.assertEqual(
                receipt["base_vs_mod"]["mod_source_sha256"],
                receipt["base_vs_mod"]["mod_reference_sha256"],
            )
            self.assertNotEqual(
                receipt["base_vs_mod"]["base_source_sha256"],
                receipt["base_vs_mod"]["mod_source_sha256"],
            )
            archive_path = output / "coa_vfs_extended_archive_later.zip"
            with zipfile.ZipFile(archive_path, "r") as archive:
                self.assertIn(
                    "gfx/coat_of_arms/patterns/" + ARCHIVE_SHARED,
                    archive.namelist(),
                )
                self.assertIn(
                    "gfx/coat_of_arms/patterns/" + ARCHIVE_LATER_REFERENCE,
                    archive.namelist(),
                )
            self.assertIn(
                f'archive="{archive_path.as_posix()}"',
                (output / "mod" / "coa_vfs_extended_archive_later.mod").read_text(
                    encoding="utf-8"
                ),
            )
            base_manifest = next(
                (output / "coa_vfs_extended_base_override").rglob("*.txt")
            ).read_text(encoding="utf-8")
            self.assertIn(BASE_ORIGINAL_REFERENCE, base_manifest)
            self.assertIn(BASE_MOD_REFERENCE, base_manifest)
            self.assertNotIn(f"{FIRST_SOURCE} =", base_manifest)
            with self.assertRaises(FileExistsError):
                prepare_extended_fixture(base_profile, root / "game", output)

    def test_builds_later_pattern_directory_replace_path_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base_profile = root / "base-profile"
            base_profile.mkdir()
            (base_profile / "pdx_settings.txt").write_text(
                "language=l_english\n", encoding="utf-8"
            )
            patterns = root / "game" / PATTERN_DIRECTORY
            patterns.mkdir(parents=True)
            (patterns / FIRST_SOURCE).write_bytes(b"DDS earlier fixture")
            (patterns / SECOND_SOURCE).write_bytes(b"DDS later fixture")
            (patterns / SOLID_SOURCE).write_bytes(b"DDS solid fixture")
            output = root / "fixture"

            receipt = prepare_replace_path_fixture(
                base_profile, root / "game", output
            )

            self.assertEqual(
                receipt["schema"], "ck3-coat-of-arms-vfs-replace-path-fixture-v1"
            )
            self.assertEqual(
                receipt["descriptors"][1]["replace_paths"],
                ["gfx/coat_of_arms/patterns"],
            )
            self.assertEqual(
                receipt["base_hidden_candidate"]["resource_name"], FIRST_SOURCE
            )
            self.assertEqual(
                receipt["base_hidden_candidate"]["source_sha256"],
                receipt["earlier"]["source_sha256"],
            )
            self.assertEqual(len(receipt["predeclared_hypotheses"]), 2)
            later_descriptor = (
                output / "mod" / "coa_vfs_replace_later.mod"
            ).read_text(encoding="utf-8")
            self.assertIn(
                'replace_path="gfx/coat_of_arms/patterns"', later_descriptor
            )
            self.assertEqual(
                receipt["earlier"]["source_sha256"],
                receipt["earlier"]["asset_sha256"],
            )
            self.assertEqual(
                receipt["later"]["source_sha256"],
                receipt["later"]["asset_sha256"],
            )
            self.assertEqual(
                receipt["later"]["solid_source_sha256"],
                receipt["later"]["solid_asset_sha256"],
            )
            self.assertNotEqual(
                receipt["earlier"]["asset_sha256"],
                receipt["later"]["asset_sha256"],
            )
            self.assertTrue(
                (
                    output
                    / "coa_vfs_replace_earlier"
                    / "gfx"
                    / "coat_of_arms"
                    / "patterns"
                    / REPLACED_EARLIER
                ).is_file()
            )
            self.assertTrue(
                (
                    output
                    / "coa_vfs_replace_later"
                    / "gfx"
                    / "coat_of_arms"
                    / "patterns"
                    / REPLACE_LATER_REFERENCE
                ).is_file()
            )
            with self.assertRaises(FileExistsError):
                prepare_replace_path_fixture(base_profile, root / "game", output)


if __name__ == "__main__":
    unittest.main()
