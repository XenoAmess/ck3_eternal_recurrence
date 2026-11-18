#!/usr/bin/env python3
"""Unit tests for the Auto Upgrade Buildings release builder."""

from __future__ import annotations

import json
import copy
import contextlib
import io
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import build_auto_upgrade_buildings_release as release
import auto_upgrade_buildings_data as data
import extract_auto_upgrade_buildings as extractor
import validate_auto_upgrade_buildings_static as validator


REVISION = "a" * 40


class BuildAutoUpgradeBuildingsReleaseTests(unittest.TestCase):
    def test_validator_reads_payment_definition_after_earlier_call(self) -> None:
        effects = "\n".join(raw.decode("utf-8-sig")
                            for path, raw in sorted(release.generator.generated_outputs().items())
                            if path.parent.name == "scripted_effects")
        payment = validator.extract_block(effects, "aub_pay_gold_building_cost_effect", top_level=True)
        self.assertIsNotNone(payment)
        self.assertIn("has_character_flag = aub_funding_treasury_only", payment or "")
        self.assertIn("has_character_flag = aub_funding_personal_only", payment or "")
        self.assertEqual((payment or "").count("change_variable = { name = aub_upgrades_this_scan add = 1 }"), 1)

    def test_split_runtime_preserves_every_original_definition_once(self) -> None:
        for directory, original in (
            ("scripted_effects", release.generator.render_effects()),
            ("scripted_triggers", release.generator.render_triggers()),
        ):
            expected = {entry.key: entry for entry in extractor.parse_clausewitz(original).entries}
            actual: dict[str, extractor.Entry] = {}
            for path, raw in release.generator.generated_outputs().items():
                if path.parent.name != directory:
                    continue
                entries = extractor.parse_clausewitz(raw.decode("utf-8-sig")).entries
                self.assertGreaterEqual(len(entries), 1)
                self.assertLessEqual(len(entries), 10)
                for entry in entries:
                    self.assertNotIn(entry.key, actual)
                    actual[entry.key] = entry
            self.assertEqual(actual, expected)

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

    def test_weakened_native_construction_gate_cannot_enter_release(self) -> None:
        path = next(self.source / relative for relative in sorted(release.RUNTIME_FILES)
                    if relative.startswith("common/scripted_triggers/") and
                    "can_start_building_construction_for_owner = charnel_grounds_02" in
                    (self.source / relative).read_text(encoding="utf-8-sig"))
        text = path.read_text(encoding="utf-8-sig")
        self.assertIn("can_start_building_construction_for_owner = charnel_grounds_02", text)
        path.write_text(
            text.replace("can_start_building_construction_for_owner = charnel_grounds_02", "always = yes", 1),
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
        self.assertEqual(loaded["mod_version"], "4.0.4")
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
            git_tag=release.product_tag("4.0.4"),
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


class FlorinBuildingExtractionTests(unittest.TestCase):
    def game(self, root: Path) -> Path:
        files = {
            "common/buildings/holding_buildings/castles.txt":
                "castle_01 = { next_building = castle_02 }\n"
                "castle_02 = { cost_gold = 200 district_level_requirement = 2 can_construct = { always = yes } }\n",
            "common/buildings/projects/projects.txt":
                "project_01 = { next_building = project_02 great_project_type = project_kind }\n"
                "project_02 = { next_building = project_03 }\nproject_03 = { }\n",
            "common/buildings/_buildings.info": "test schema\n",
            "common/holdings/holdings.txt": "castle_holding = { primary_district = castle_district }\n",
            "common/districts/holdings.txt": "castle_district = { primary_building = castle_01 type = holding }\n",
        }
        for name, body in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        return root

    def test_recursive_graph_district_primary_and_entire_project_exclusion(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            game = self.game(Path(temporary))
            snapshot = extractor.build_snapshot(game, game_version="1.21.0")
            self.assertEqual(snapshot["building_definition_count"], 5)
            self.assertEqual(snapshot["included_edge_count"], 1)
            self.assertEqual(snapshot["excluded_edge_count"], 2)
            self.assertEqual(snapshot["primary_building_roots"], {"castle_01": "castle_holding"})
            self.assertIn("common/districts/holdings.txt", snapshot["input_sha256"])
            self.assertEqual(snapshot["included_edges"][0]["resources"], {"gold": "200"})
            self.assertEqual(snapshot["included_edges"][0]["gates"], {"can_construct": "always = yes"})
            self.assertEqual(snapshot["included_edges"][0]["district_level_requirement"], {"kind": "scalar", "value": "2"})

    def test_missing_or_ambiguous_primary_district_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            game = self.game(Path(temporary))
            path = game / "common/holdings/holdings.txt"
            path.write_text("castle_holding = { primary_district = missing }", encoding="utf-8")
            with self.assertRaisesRegex(extractor.ExtractionError, "unknown primary district"):
                extractor.read_primary_buildings(game)
            path.write_text("castle_holding = { primary_district = castle_district primary_building = castle_01 }", encoding="utf-8")
            with self.assertRaisesRegex(extractor.ExtractionError, "both primary building and district"):
                extractor.read_primary_buildings(game)

    def test_duplicate_definition_in_subdirectory_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            game = self.game(Path(temporary))
            (game / "common/buildings/duplicate.txt").write_text("castle_01 = { }", encoding="utf-8")
            with self.assertRaisesRegex(extractor.ExtractionError, "duplicate vanilla building definition"):
                extractor.read_buildings(game)

    def test_legacy_direct_primary_building_remains_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            game = self.game(Path(temporary))
            (game / "common/holdings/holdings.txt").write_text("castle_holding = { primary_building = castle_01 }", encoding="utf-8")
            roots, _ = extractor.read_primary_buildings(game)
            self.assertEqual(roots, {"castle_01": "castle_holding"})

    def test_florin_sources_cannot_be_mislabeled_as_legacy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            game = self.game(Path(temporary))
            with self.assertRaisesRegex(extractor.ExtractionError, "explicitly selected game version"):
                extractor.build_snapshot(game)

    def test_district_requirement_preserves_complete_script_value(self) -> None:
        parsed = extractor.parse_clausewitz('district_level_requirement = { value = 2 if = { limit = { always = yes } add = 1 } }')
        projected = extractor.script_value_projection(parsed, "district_level_requirement")
        self.assertIsNotNone(projected)
        self.assertEqual(projected["kind"], "block")
        self.assertEqual(extractor.parse_clausewitz(projected["body"]), parsed.entries[0].value)
        with self.assertRaisesRegex(extractor.ExtractionError, "must be one script value"):
            extractor.script_value_projection(extractor.parse_clausewitz('level = 1 level = 2'), 'level')

    def test_florin_cli_cannot_overwrite_the_historical_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            game = self.game(Path(temporary))
            historical = game / "historical.json"
            historical.write_bytes(b"historical content")
            args = ["--game-root", str(game), "--game-version", "1.21.0"]
            with patch.object(extractor, "OUTPUT", historical), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(extractor.main(args), 1)
                self.assertEqual(extractor.main([*args, "--output", str(historical)]), 1)
            self.assertEqual(historical.read_bytes(), b"historical content")


class BuildingSnapshotContractTests(unittest.TestCase):
    def test_district_levels_and_json_types_cannot_bypass_contract(self) -> None:
        payload = copy.deepcopy(data.SNAPSHOT_DATA)
        edge = next(e for e in payload["included_edges"] if e["district_level_requirement"] is not None)
        edge["district_level_requirement"] = None
        with self.assertRaisesRegex(ValueError, "policy contract"):
            data.validate_snapshot_contract(payload)
        for wrong in (1, 1.0, "true", None):
            with self.assertRaises(ValueError):
                data._boolean(wrong, "primary_building")
        with self.assertRaises(ValueError):
            data._requirement({"kind": "scalar", "value": True})
        with self.assertRaises(ValueError):
            data._requirement({"kind": "scalar", "value": "2", "body": "2"})

    def test_district_delegation_uses_complete_engine_eligibility(self) -> None:
        parsed = extractor.parse_clausewitz(release.generator.render_triggers())
        definitions = {e.key: e.value for e in parsed.entries}
        for edge in data.EDGES:
            self.assertEqual(definitions[release.generator.trigger_name(edge)],
                             extractor.parse_clausewitz(f"can_start_building_construction_for_owner = {edge.target}"))
        effects = release.generator.render_effects()
        province = validator.extract_block(effects, "aub_upgrade_all_supported_buildings_effect", top_level=True)
        self.assertEqual((province or "").count("every_built_buildings = {"), 1)
        self.assertEqual((province or "").count("is_primary_building = yes"), 1)
        self.assertEqual((province or "").count("building_district = {"), 1)
        self.assertEqual((province or "").count("aub_upgrade_supported_district_buildings_effect = yes"), 1)
        self.assertNotIn("remove_building", effects)
        self.assertNotIn("add_special_building", effects)
        for chain in data.CHAINS:
            body = "\n".join(release.generator.render_chain(chain))
            for edge in chain.edges:
                self.assertIn(f"upgrade_building_effect = {edge.source}", body)
                self.assertIn(f"limit = {{ has_building = {edge.target} }}", body)

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

    def test_historical_policy_unchanged_and_florin_great_projects_excluded(self) -> None:
        old = json.loads((data.ROOT / "tools/auto_upgrade_buildings_1_19_0_6.json").read_text(encoding="utf-8"))
        historical = json.loads((data.ROOT / "tools/auto_upgrade_buildings_1_20_0_2.json").read_text(encoding="utf-8"))
        self.assertEqual(
            [{key:value for key,value in e.items() if key != "gates"} for e in historical["included_edges"]],
            [{key:value for key,value in e.items() if key != "gates"} for e in old["included_edges"]],
        )
        self.assertEqual(historical["excluded_edges"], old["excluded_edges"])
        self.assertEqual({edge.chain_root for edge in data.EXCLUDED_EDGES}, data.EXPECTED_EXCLUDED_CHAIN_ROOTS)
        self.assertFalse(set(edge.chain_root for edge in data.EXCLUDED_EDGES) & set(chain.root for chain in data.CHAINS))

    def test_historical_reviewed_rite_and_temple_citadel_changes(self) -> None:
        historical = json.loads((data.ROOT / "tools/auto_upgrade_buildings_1_20_0_2.json").read_text(encoding="utf-8"))
        edges = {e["target"]: e["gates"] for e in historical["included_edges"]}
        for target in ("charnel_grounds_02", "charnel_grounds_03"):
            gates = "\n".join(edges[target].values())
            self.assertIn("rite_has_parameter = sky_burials_active", gates)
            self.assertNotIn("has_doctrine_parameter", gates)
        gates = "\n".join(edges["megalith_02"].values())
        self.assertIn("scope:holder.rite", gates)
        self.assertIn("has_building_or_higher = temple_citadel_01", gates)
        self.assertIn("has_holding_type = temple_citadel_holding", edges["monastic_schools_02"]["can_construct_potential"])
        self.assertIn("rite_has_doctrine = special_doctrine_is_eastern_christian_faith", edges["meteora_02"]["is_enabled"])
        self.assertIn("faith = faith:manichaean_faith", edges["palace_of_ctesiphon_02"]["can_construct"])

    def test_historical_dlc_and_final_scriptorium_qualification_are_preserved(self) -> None:
        historical = json.loads((data.ROOT / "tools/auto_upgrade_buildings_1_20_0_2.json").read_text(encoding="utf-8"))
        edges = {e["target"]: e["gates"] for e in historical["included_edges"]}
        for prefix in ("citadel_shrine", "sacred_pool", "vihara_halls"):
            for level in range(3, 9):
                gates = edges[f"{prefix}_{level:02}"]
                self.assertEqual(gates["can_construct_potential"], 'has_dlc = "All Under Heaven"')
                self.assertNotIn("has_dlc", gates["can_construct"])
        gate = edges["scriptorium_08"]["can_construct"]
        self.assertIn("has_building_or_higher = temple_04", gate)
        self.assertIn("has_building_or_higher = temple_citadel_04", gate)
        self.assertNotIn("has_building_or_higher = temple_03", gate)
        self.assertIn("has_dlc_feature = legends", gate)

    def test_florin_renamed_chains_and_rite_qualification(self) -> None:
        edges = {edge.target: edge for edge in data.EDGES}
        for prefix, top_level in (("temple_citadel_shrine", 4), ("sacred_pool", 5), ("temple_viharas", 5), ("scriptorium", 5)):
            for level in range(2, top_level + 1):
                self.assertEqual(edges[f"{prefix}_{level}"].district_level_requirement,
                                 {"kind": "scalar", "value": str(min(level, 4))})
        for target in ("charnel_grounds_02", "charnel_grounds_03"):
            self.assertIn("rite_has_parameter = sky_burials_active", dict(edges[target].gates)["can_construct_potential"])
        self.assertIn("scope:holder.rite", dict(edges["megalith_2"].gates)["can_construct_potential"])
        self.assertIn("rite_has_doctrine = special_doctrine_is_eastern_christian_faith", dict(edges["meteora_02"].gates)["is_enabled"])
        self.assertIn("faith = faith:manichaean_faith", dict(edges["palace_of_ctesiphon_02"].gates)["can_construct"])


if __name__ == "__main__":
    unittest.main()
