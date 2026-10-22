"""Initial-input producer regressions; no CK3 or AI business qualification."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import prepare_npc_fixture as npc
from acceptance_contract import pin, read
from ck3_text_projection import blocks, masked


class NpcFixtureTests(unittest.TestCase):
    def test_spec_strict_fields_types_and_json_roundtrip(self) -> None:
        for count in (0, 51):
            spec = npc.NpcFixtureSpec(count)
            self.assertEqual(npc.NpcFixtureSpec.parse(json.loads(json.dumps(spec.to_json()))), spec)
        bad: tuple[object, ...] = (
            {}, {"schema_version": 1}, {"schema_version": 1, "queue_count": 50},
            {"schema_version": True, "queue_count": 51}, {"schema_version": 1.0, "queue_count": 51},
            {"schema_version": 1, "queue_count": True}, {"schema_version": 1, "queue_count": 51.0},
            {"schema_version": 1, "queue_count": None}, {"schema_version": 1, "queue_count": []},
            {"schema_version": 1, "queue_count": 51, "claim_pass": True},
        )
        for value in bad:
            with self.subTest(value=value), self.assertRaises(ValueError):
                npc.NpcFixtureSpec.parse(value)

    def test_source_binding_rejects_drift_and_path_escape(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "common" / "source.txt"
            source.parent.mkdir()
            source.write_bytes(b"source definition\n")
            binding = npc.SourceBinding("common/source.txt", hashlib.sha256(source.read_bytes()).hexdigest())
            self.assertEqual(npc.verify_source(root, binding), pin(source))
            source.write_bytes(b"changed source\n")
            with self.assertRaisesRegex(ValueError, "source drift"):
                npc.verify_source(root, binding)
            for relative in ("../source.txt", "/source.txt", "common/../../source.txt", "C:/source.txt", "common/*.txt"):
                with self.subTest(relative=relative), self.assertRaises(ValueError):
                    npc.SourceBinding(relative, "0" * 64)

    def test_generated_initial_inputs_preserve_roles_references_and_no_ai_actions(self) -> None:
        script = npc.render_npc_effects(npc.NpcFixtureSpec())
        definitions = blocks(script)
        self.assertEqual(sum(block.key == "create_artifact" for block in definitions), 71)
        forbidden = {
            "equip_artifact_to_owner", "equip_artifact_to_owner_replace", "unequip_artifact", "destroy_artifact",
            "xalw_feed_material_effect", "xalw_suppress_effect", "xalw_appease_effect", "xalw_ai_cultivate_effect",
            "xalw_queue_ai_review_effect", "xalw_owner_monthly_effect",
            "xalw_settle_xp_effect", "xalw_train_effect", "trigger_event",
        }
        self.assertFalse(forbidden & {block.key for block in definitions})
        actions = set(re.findall(r"\b([A-Za-z0-9_]+)\s*=\s*yes\b", masked(script)))
        self.assertFalse(forbidden & actions)
        for variable in ("xalw_level", "xalw_xp_in_level", "xalw_growth_sequence", "xalw_growth_suppressed_until"):
            self.assertNotRegex(script, rf"name\s*=\s*{variable}\b")
        self.assertNotIn("PASS", script)
        self.assertEqual(script.count("xalw_awaken_artifact_effect = yes"), 4)
        for role in ("landed", "baron", "courtier", "fragile", "queue"):
            self.assertIn(f"name = xalw_npc_fixture_owner_{role} value = scope:xalw_npc_selected", script)
            self.assertIn(f"name = xalw_npc_fixture_missing_{role} value = yes", script)
        for index in range(1, 52):
            self.assertIn(f"name = xalw_npc_fixture_queue_item_{index:03d} value = scope:xalw_npc_created_item", script)
        self.assertIn("name = xalw_npc_fixture_queue_tail value = scope:xalw_npc_created_item", script)

    def test_every_finished_role_enters_only_the_normal_production_owner_lifecycle_once(self) -> None:
        for count in (0, 51):
            with self.subTest(queue_count=count):
                script = npc.render_npc_effects(npc.NpcFixtureSpec(count))
                definitions = blocks(script)
                roles = ("landed", "baron", "courtier", "fragile") + (("queue",) if count else ())
                calls = list(re.finditer(r"\bxalw_discover_owner_effect\s*=\s*yes\b", masked(script)))
                self.assertEqual(len(calls), len(roles))
                for role in roles:
                    create = next(block for block in definitions if block.key == "xalw_npc_fixture_create_" + role + "_effect")
                    body = masked(script[create.opening:create.end])
                    handoffs = list(re.finditer(r"\bxalw_discover_owner_effect\s*=\s*yes\b", body))
                    self.assertEqual(len(handoffs), 1)
                    self.assertEqual(body.count("create_artifact ="), count if role == "queue" else 5)
                    self.assertGreater(handoffs[0].start(), body.rfind("create_artifact ="))
                    self.assertGreater(handoffs[0].start(), body.rfind("NOT = { can_benefit_from_artifact"))
                    self.assertLess(handoffs[0].start(), body.index("name = xalw_npc_fixture_initial_inputs_created"))
                    ancestors = [block.key for block in blocks(body) if block.opening < handoffs[0].start() < block.end]
                    # The call executes on the selected owner, never inside the
                    # just-created artifact, conditional eligibility or input loop.
                    self.assertEqual(ancestors, [])
                    for forbidden in ("xalw_ai_cultivate_effect", "xalw_queue_ai_review_effect", "xalw_owner_monthly_effect", "xalw_train_effect", "xalw_feed_material_effect"):
                        self.assertNotIn(forbidden, body)

    def test_full_source_qualifier_checks_executable_and_pins_actual_producer(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            game = root / "game"
            game.mkdir()
            source = game / "source.txt"
            source.write_bytes(b"unit primary source\n")
            executable = root / "binaries" / "ck3.exe"
            executable.parent.mkdir()
            executable.write_bytes(b"unit executable boundary")
            binding = npc.SourceBinding("source.txt", pin(source)["sha256"])
            with patch.object(npc, "SOURCES", (binding,)), patch.object(npc, "EXPECTED_EXE_SHA", pin(executable)["sha256"]):
                result = npc.qualify_sources(game)
                self.assertEqual(result["binaries/ck3.exe"], pin(executable))
                self.assertEqual(result["product/prepare_npc_fixture.py"], pin(Path(npc.__file__)))
                self.assertEqual(result["source.txt"], pin(source))
                executable.write_bytes(b"different executable")
                with self.assertRaisesRegex(ValueError, "exact CK3"):
                    npc.qualify_sources(game)

    def test_native_eligibility_checks_do_not_fix_failed_initial_inputs(self) -> None:
        script = npc.render_npc_effects(npc.NpcFixtureSpec(0))
        self.assertEqual(script.count("NOT = { can_equip_artifact = scope:xalw_npc_created_item }"), 20)
        self.assertEqual(script.count("NOT = { can_benefit_from_artifact = scope:xalw_npc_created_item }"), 20)
        self.assertEqual(script.count("scope:xalw_npc_created_item = { is_equipped = yes }"), 20)
        self.assertEqual(script.count("name = xalw_npc_fixture_initial_eligibility_gap value = yes"), 20)
        self.assertNotIn("queue_item_", script)
        self.assertIn("highest_held_title_tier >= tier_county", script)
        self.assertIn("highest_held_title_tier = tier_barony", script)
        fragile = next(block for block in blocks(script) if block.key == "xalw_npc_fixture_create_fragile_effect")
        initial_body = script[fragile.opening:fragile.end]
        self.assertNotIn("add_gold", initial_body)
        self.assertNotIn("add_prestige", initial_body)
        self.assertIn("health >= 2", script)
        self.assertIn("health < 4", script)
        self.assertIn("gold < 20", script)
        self.assertIn("prestige < 50", script)

    def test_emitter_to_manifest_and_all_script_localization_consumers(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            evidence = root / "source-proof.txt"
            evidence.write_text("unit source qualification boundary\n", encoding="utf-8")
            for count in (0, 51):
                destination = root / f"fixture-{count}"
                with patch.object(npc, "qualify_sources", return_value={"unit-source": pin(evidence)}), \
                     patch.object(npc, "current_machine_id", return_value="unit-machine"):
                    result = npc.emit_npc_fixture(destination, game=root / "game", spec=npc.NpcFixtureSpec(count))
                persisted = read(root / f"fixture-{count}.emission.json")
                self.assertEqual(persisted, result)
                self.assertEqual(result["runtime_status"], "NOT_RUN")
                self.assertEqual(result["business_acceptance"], "NOT_ASSESSED")
                self.assertEqual(result["qualification_scope"], "exact-source-and-initial-script-only")
                self.assertEqual(len(result["roles"]), 5 if count else 4)
                self.assertEqual(len(result["queue_reference_variables"]), count)
                self.assertTrue(any("51 unchecked" in gap for gap in result["coverage_gaps"]))
                self.assertEqual(len(result["files"]), 5)
                for relative, identity in result["files"].items():
                    path = destination / relative
                    self.assertEqual(pin(path), identity)
                    self.assertTrue(path.read_bytes().startswith(b"\xef\xbb\xbf"))
                scripts = (destination / "common/scripted_effects/xalw_npc_fixture_inputs.txt").read_text(encoding="utf-8-sig")
                self.assertEqual(scripts.count("xalw_discover_owner_effect = yes"), 5 if count else 4)
                names = set(re.findall(r"\bname\s*=\s*(xalw_npc_[a-z0-9_]+_name)\b", scripts))
                self.assertEqual(len(names), 20 + count)
                for language in ("english", "simp_chinese"):
                    locale = (destination / f"localization/{language}/xalw_npc_fixture_l_{language}.yml").read_text(encoding="utf-8-sig")
                    keys = set(re.findall(r"^ ([a-z0-9_]+):0 ", locale, re.MULTILINE))
                    self.assertEqual(keys, names | {"xalw_npc_input_description"})
                bootstrap = (destination / "common/on_action/xalw_npc_fixture_bootstrap.txt").read_text(encoding="utf-8-sig")
                self.assertIn("NOT = { has_variable = xalw_npc_fixture_initialized }", bootstrap)
                self.assertIn("xalw_npc_fixture_initialize_effect = yes", bootstrap)
                blocks(bootstrap)

    def test_source_failure_and_existing_output_cannot_overwrite_or_emit(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "fresh"
            with patch.object(npc, "qualify_sources", side_effect=ValueError("unqualified exact source")), \
                 self.assertRaisesRegex(ValueError, "unqualified"):
                npc.emit_npc_fixture(destination, game=root)
            self.assertFalse(destination.exists())
            self.assertFalse((root / "fresh.emission.json").exists())
            (root / "fresh.emission.json").write_text("retained original", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "new external"):
                npc.emit_npc_fixture(destination, game=root)
            self.assertEqual((root / "fresh.emission.json").read_text(encoding="utf-8"), "retained original")
            with self.assertRaisesRegex(ValueError, "new external"):
                npc.emit_npc_fixture(npc.REPO / "_runtime" / "unacceptable-npc-fixture", game=root)


if __name__ == "__main__":
    unittest.main()
