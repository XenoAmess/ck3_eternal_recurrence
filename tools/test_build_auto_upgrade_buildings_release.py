#!/usr/bin/env python3
"""Unit tests for the Auto Upgrade Buildings release builder."""

from __future__ import annotations

import json
import copy
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

import build_auto_upgrade_buildings_release as release
import auto_upgrade_buildings_data as data


REVISION = "a" * 40


class BuildAutoUpgradeBuildingsReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="auto-upgrade-builder-test-")
        self.root = Path(self.temp.name)
        self.source = self.root / release.PRODUCT_ID
        shutil.copytree(release.DEFAULT_SOURCE, self.source)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def build(self):
        return release.build_release(
            self.source, self.root / "dist" / release.PRODUCT_ID, REVISION
        )

    def test_exact_inventory_and_readme_exclusion(self) -> None:
        staging, _, archive, manifest = self.build()
        expected = sorted(release.RUNTIME_FILES)
        self.assertEqual([item["path"] for item in manifest["files"]], expected)
        self.assertFalse((staging / "README.md").exists())
        with zipfile.ZipFile(archive) as zipped:
            self.assertEqual(
                zipped.namelist(),
                [f"{release.PRODUCT_ID}/{relative}" for relative in expected],
            )

    def test_repeated_build_is_byte_identical(self) -> None:
        first = self.build()
        first_manifest = first[1].read_bytes()
        first_zip = first[2].read_bytes()
        second = self.build()
        self.assertEqual(second[1].read_bytes(), first_manifest)
        self.assertEqual(second[2].read_bytes(), first_zip)

    def test_missing_and_extra_files_fail_closed(self) -> None:
        (self.source / "events/auto_build.txt").unlink()
        (self.source / "unexpected.txt").write_text("x", encoding="utf-8")
        errors = release.source_errors(self.source)
        self.assertTrue(any("missing runtime file" in error for error in errors))
        self.assertTrue(any("outside allowlist" in error for error in errors))

    def test_old_faith_gate_cannot_enter_release(self) -> None:
        path = self.source / "common/scripted_triggers/aub_building_triggers.txt"
        text = path.read_text(encoding="utf-8-sig")
        self.assertIn("rite_has_parameter = sky_burials_active", text)
        path.write_text(
            text.replace("rite_has_parameter = sky_burials_active", "has_doctrine_parameter = sky_burials_active", 1),
            encoding="utf-8-sig",
        )
        with self.assertRaisesRegex(ValueError, "reviewed building contract"):
            self.build()

    def test_changed_generated_charge_cannot_enter_release(self) -> None:
        path = self.source / "common/scripted_effects/build_scripted_effect.txt"
        text = path.read_text(encoding="utf-8-sig")
        self.assertIn("remove_short_term_gold = $GOLD$", text)
        path.write_text(
            text.replace("remove_short_term_gold = $GOLD$", "remove_short_term_gold = 0", 1),
            encoding="utf-8-sig",
        )
        with self.assertRaisesRegex(ValueError, "reviewed building contract"):
            self.build()

    def test_canonical_workshop_identity_is_rejected(self) -> None:
        descriptor = self.source / "descriptor.mod"
        descriptor.write_text(
            descriptor.read_text(encoding="utf-8")
            + f'remote_file_id="{release.UPSTREAM_WORKSHOP_ITEM_ID}"\n',
            encoding="utf-8",
        )
        errors = release.source_errors(self.source)
        self.assertTrue(any("remote_file_id" in error for error in errors))
        self.assertTrue(any("Workshop identity" in error for error in errors))

    def test_manifest_identity(self) -> None:
        _, manifest_path, _, manifest = self.build()
        loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(loaded, manifest)
        self.assertEqual(loaded["product_id"], release.PRODUCT_ID)
        self.assertEqual(loaded["mod_version"], "4.0.3")
        self.assertIsNone(loaded["git_tag"])
        self.assertIsNone(loaded["workshop_item_id"])

    def test_workshop_identity_rejects_upstream_item(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not reuse"):
            release.build_release(
                self.source,
                self.root / "upstream-id",
                REVISION,
                release.UPSTREAM_WORKSHOP_ITEM_ID,
            )

    def test_workshop_cache_accepts_exact_or_launcher_injected_descriptor(self) -> None:
        item_id = "4000000000"
        staging, manifest_path, _, manifest = release.build_release(
            self.source,
            self.root / "canonical" / release.PRODUCT_ID,
            REVISION,
            item_id,
            git_tag=release.product_tag("4.0.3"),
        )
        self.assertEqual(manifest["workshop_item_id"], item_id)
        cache = self.root / "cache"
        shutil.copytree(staging, cache)
        self.assertEqual(
            release.verify_manifest(cache, manifest_path, workshop_cache=True),
            len(release.RUNTIME_FILES),
        )
        descriptor = cache / "descriptor.mod"
        descriptor.write_bytes(
            descriptor.read_bytes().rstrip(b"\r\n")
            + f'\nremote_file_id="{item_id}"'.encode("ascii")
        )
        self.assertEqual(
            release.verify_manifest(cache, manifest_path, workshop_cache=True),
            len(release.RUNTIME_FILES),
        )
        descriptor.write_bytes(descriptor.read_bytes() + b'\nremote_file_id="4000000001"')
        with self.assertRaisesRegex(ValueError, "descriptor.mod"):
            release.verify_manifest(cache, manifest_path, workshop_cache=True)


class BuildingSnapshotContractTests(unittest.TestCase):
    def test_same_counts_cannot_hide_a_changed_price(self) -> None:
        payload = copy.deepcopy(data.SNAPSHOT_DATA)
        payload["included_edges"][0]["resources"]["gold"] = "1"
        with self.assertRaisesRegex(ValueError, "policy contract"):
            data.validate_snapshot_contract(payload)

    def test_same_counts_cannot_hide_a_weakened_gate(self) -> None:
        payload = copy.deepcopy(data.SNAPSHOT_DATA)
        edge = next(e for e in payload["included_edges"] if e["target"] == "charnel_grounds_02")
        edge["gates"]["can_construct_potential"] = "always = yes"
        with self.assertRaisesRegex(ValueError, "gate contract"):
            data.validate_snapshot_contract(payload)

    def test_no_new_church_or_great_project_edges(self) -> None:
        old = json.loads((data.ROOT / "tools/auto_upgrade_buildings_1_19_0_6.json").read_text(encoding="utf-8"))
        self.assertEqual(
            [{key:value for key,value in e.items() if key != "gates"} for e in data.SNAPSHOT_DATA["included_edges"]],
            [{key:value for key,value in e.items() if key != "gates"} for e in old["included_edges"]],
        )
        self.assertEqual(data.SNAPSHOT_DATA["excluded_edges"], old["excluded_edges"])

    def test_reviewed_rite_and_temple_citadel_changes(self) -> None:
        edges = {e.target: e for e in data.EDGES}
        for target in ("charnel_grounds_02", "charnel_grounds_03"):
            gates = "\n".join(dict(edges[target].gates).values())
            self.assertIn("rite_has_parameter = sky_burials_active", gates)
            self.assertNotIn("has_doctrine_parameter", gates)
        gates = "\n".join(dict(edges["megalith_02"].gates).values())
        self.assertIn("scope:holder.rite", gates)
        self.assertIn("has_building_or_higher = temple_citadel_01", gates)
        self.assertIn("has_holding_type = temple_citadel_holding", dict(edges["monastic_schools_02"].gates)["can_construct_potential"])
        self.assertIn("rite_has_doctrine = special_doctrine_is_eastern_christian_faith", dict(edges["meteora_02"].gates)["is_enabled"])
        self.assertIn("faith = faith:manichaean_faith", dict(edges["palace_of_ctesiphon_02"].gates)["can_construct"])

    def test_dlc_and_final_scriptorium_qualification_are_preserved(self) -> None:
        edges = {e.target: e for e in data.EDGES}
        for prefix in ("citadel_shrine", "sacred_pool", "vihara_halls"):
            for level in range(3, 9):
                gates = dict(edges[f"{prefix}_{level:02}"].gates)
                self.assertEqual(gates["can_construct_potential"], 'has_dlc = "All Under Heaven"')
                self.assertNotIn("has_dlc", gates["can_construct"])
        gate = dict(edges["scriptorium_08"].gates)["can_construct"]
        self.assertIn("has_building_or_higher = temple_04", gate)
        self.assertIn("has_building_or_higher = temple_citadel_04", gate)
        self.assertNotIn("has_building_or_higher = temple_03", gate)
        self.assertIn("has_dlc_feature = legends", gate)


if __name__ == "__main__":
    unittest.main()
