"""Check exact engine selection and metadata used by disposable fixtures."""
import importlib.util
import hashlib
import os
import json
import re
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

import fixture_engine_prepare as prep
import prepare_aub_1_20_fixture as aub
import extract_auto_upgrade_buildings as parser


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
                     if build.game_version.startswith(("1.20.", "1.21.")))
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


class AubFlorinProbePreparationTests(unittest.TestCase):
    def assertion_limits(self, block: parser.Block) -> dict[str, parser.Block]:
        found: dict[str, parser.Block] = {}
        for entry in block.entries:
            if not isinstance(entry.value, parser.Block):
                continue
            if entry.key in {"if", "else_if"}:
                limits = [item.value for item in entry.value.entries
                          if item.key == "limit" and isinstance(item.value, parser.Block)]
                for item in entry.value.entries:
                    if item.key == "debug_log" and isinstance(item.value, str) and item.value.startswith('"AUBT: TEST PASS '):
                        self.assertEqual(len(limits), 1)
                        found[item.value[1:-1]] = limits[0]
            nested = self.assertion_limits(entry.value)
            self.assertFalse(set(found) & set(nested))
            found.update(nested)
        return found

    def identity(self) -> dict[str, str]:
        build = next(build for build in native_builds() if build.game_version == "1.21.0")
        return {"game_version": build.game_version, "steam_build_id": "31415926",
                "exe_sha256": build.executable_sha256.lower()}

    def test_actual_producer_and_case_keep_probe_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, \
                patch.object(prep, "engine_identity", return_value=self.identity()), \
                patch.object(aub, "engine_identity", return_value=self.identity()):
            output = Path(temporary) / "probe"
            self.assertEqual(aub.prepare_probe(REPO, output), output)
            receipt = json.loads(output.with_suffix(".prepare.json").read_text(encoding="utf-8"))
            case = json.loads((REPO / "tools/ck3_mod_acceptance_cases/aub_florin_probe.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["required_markers"], case["required_markers"])
            self.assertIs(receipt["full_product_pass_from_cell"], False)
            self.assertEqual(receipt["runtime_status"], "NOT_RUN")
            script = (output / "events/aubf_events.txt").read_text(encoding="utf-8-sig")
            self.assertEqual(len(parser.parse_clausewitz(script).entries), 2)
            for marker in case["required_markers"]:
                self.assertEqual(script.count('"' + marker + '"'), 1)
            for path in output.rglob("*.txt"):
                self.assertTrue(path.read_bytes().startswith(b"\xef\xbb\xbf"))

    def test_legacy_full_matrix_is_rejected_on_florin_before_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, \
                patch.object(prep, "engine_identity", return_value=self.identity()), \
                patch.object(aub, "engine_identity", return_value=self.identity()):
            output = Path(temporary) / "legacy"
            with self.assertRaisesRegex(ValueError, "not migrated"):
                aub.prepare(REPO, output)
            self.assertFalse(output.exists())

    def test_probe_is_rejected_on_legacy_before_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, \
                patch.object(prep, "engine_identity", return_value={"game_version": "1.20.0.4"}), \
                patch.object(aub, "engine_identity", return_value={"game_version": "1.20.0.4"}):
            output = Path(temporary) / "wrong-engine"
            with self.assertRaisesRegex(ValueError, "requires exact"):
                aub.prepare_probe(REPO, output)
            self.assertFalse(output.exists())

    def test_money_scene_keeps_all_seventeen_original_assertion_conditions(self) -> None:
        old = (REPO / "tools/fixtures/auto_upgrade_buildings_acceptance/events/aubt_events.txt").read_text(encoding="utf-8-sig")
        folder = REPO / "tools/fixtures/auto_upgrade_buildings_florin_money"
        modern = "\n".join(p.read_text(encoding="utf-8-sig") for p in sorted((folder / "events").glob("*.txt")))
        self.assertNotIn("core_only_default_policy_seeded", modern)
        normalized = re.sub(r"\bcastle_garrison_([1-5])\b", lambda m: f"barracks_{int(m[1]):02}", modern)
        before = self.assertion_limits(parser.parse_clausewitz(old))
        after = self.assertion_limits(parser.parse_clausewitz(normalized))
        review = json.loads((REPO / "tools/ck3_mod_acceptance_cases/aub_florin_money_review.json").read_text(encoding="utf-8"))
        self.assertEqual(set(after), set(review["preserved_markers"]))
        self.assertEqual(len(after), 17)
        for marker, condition in after.items():
            self.assertEqual(condition, before[marker], marker)

    def test_actual_money_producer_and_case_keep_incomplete_product_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, \
                patch.object(prep, "engine_identity", return_value=self.identity()), \
                patch.object(aub, "engine_identity", return_value=self.identity()):
            output = Path(temporary) / "money"
            self.assertEqual(aub.prepare_money(REPO, output), output)
            receipt = json.loads(output.with_suffix(".prepare.json").read_text(encoding="utf-8"))
            case = json.loads((REPO / "tools/ck3_mod_acceptance_cases/aub_florin_money.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["required_markers"], case["required_markers"])
            self.assertIs(receipt["full_product_pass_from_cell"], False)
            self.assertEqual(receipt["runtime_status"], "NOT_RUN")
            combined = "\n".join(p.read_text(encoding="utf-8-sig") for p in output.rglob("*.txt"))
            self.assertNotIn("has_ongoing_construction", combined)
            self.assertNotIn("barracks_", combined)
            for marker in case["required_markers"]:
                self.assertEqual(combined.count('"' + marker + '"'), 1, marker)
            self.assertIn("Original quota/main/special/tribal/Mandala/negative-gate/succession", receipt["scope"])

    def test_florin_money_rejects_invalid_event_ids_before_writes(self) -> None:
        for invalid in ("aubt.0", "aubt.10000"):
            for target in ("events/aubf_money_00.txt", "common/decisions/aubf_money_decisions.txt"):
                with self.subTest(invalid=invalid, target=target), tempfile.TemporaryDirectory() as temporary, \
                        patch.object(prep, "engine_identity", return_value=self.identity()), \
                        patch.object(aub, "engine_identity", return_value=self.identity()):
                    base = Path(temporary)
                    repo = base / "repo"
                    relative = Path("tools/fixtures/auto_upgrade_buildings_florin_money")
                    shutil.copytree(REPO / relative, repo / relative)
                    contracts = repo / "tools/ck3_mod_acceptance_cases"
                    contracts.mkdir(parents=True)
                    shutil.copyfile(REPO / "tools/ck3_mod_acceptance_cases/aub_florin_money.json", contracts / "aub_florin_money.json")
                    path = repo / relative / target
                    path.write_text(path.read_text(encoding="utf-8-sig").replace("aubt.900", invalid), encoding="utf-8-sig")
                    output = base / "output"
                    with self.assertRaisesRegex(ValueError, "Invalid Florin event ID"):
                        aub.prepare_money(repo, output)
                    self.assertFalse(output.exists())
                    self.assertFalse(output.with_suffix(".prepare.json").exists())

    def test_florin_money_rejects_missing_visible_event_theme_before_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, \
                patch.object(prep, "engine_identity", return_value=self.identity()), \
                patch.object(aub, "engine_identity", return_value=self.identity()):
            base = Path(temporary)
            repo = base / "repo"
            relative = Path("tools/fixtures/auto_upgrade_buildings_florin_money")
            shutil.copytree(REPO / relative, repo / relative)
            contracts = repo / "tools/ck3_mod_acceptance_cases"
            contracts.mkdir(parents=True)
            shutil.copyfile(REPO / "tools/ck3_mod_acceptance_cases/aub_florin_money.json", contracts / "aub_florin_money.json")
            path = repo / relative / "events/aubf_money_01.txt"
            original = path.read_text(encoding="utf-8-sig")
            self.assertEqual(original.count("theme = realm"), 1)
            path.write_text(original.replace("theme = realm", ""), encoding="utf-8-sig")
            output = base / "output"
            with self.assertRaisesRegex(ValueError, "requires a theme: aubt.800"):
                aub.prepare_money(repo, output)
            self.assertFalse(output.exists())
            self.assertFalse(output.with_suffix(".prepare.json").exists())

    def test_actual_ordinary_producer_preserves_partial_six_cell_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, \
                patch.object(prep, "engine_identity", return_value=self.identity()), \
                patch.object(aub, "engine_identity", return_value=self.identity()):
            output = Path(temporary) / "ordinary"
            self.assertEqual(aub.prepare_ordinary(REPO, output), output)
            receipt = json.loads(output.with_suffix(".prepare.json").read_text(encoding="utf-8"))
            case = json.loads((REPO / "tools/ck3_mod_acceptance_cases/aub_florin_ordinary.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["required_markers"], case["required_markers"])
            self.assertIs(receipt["full_product_pass_from_cell"], False)
            self.assertEqual(receipt["runtime_status"], "NOT_RUN")
            combined = "\n".join(p.read_text(encoding="utf-8-sig") for p in output.rglob("*.txt"))
            passes = [m for m in case["required_markers"] if m.startswith("AUBT: TEST PASS ")]
            self.assertEqual(len(passes), 6)
            original = self.assertion_limits(parser.parse_clausewitz((REPO / "tools/fixtures/auto_upgrade_buildings_acceptance/events/aubt_events.txt").read_text(encoding="utf-8-sig")))
            self.assertTrue(set(passes).issubset(original))
            for marker in case["required_markers"]:
                self.assertEqual(combined.count('"' + marker + '"'), 1, marker)

    def test_actual_mandala_producer_emits_exact_sources_and_partial_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, \
                patch.object(prep, "engine_identity", return_value=self.identity()), \
                patch.object(aub, "engine_identity", return_value=self.identity()):
            output = Path(temporary) / "mandala"
            self.assertEqual(aub.prepare_mandala(REPO, output), output)
            receipt = json.loads(output.with_suffix(".prepare.json").read_text(encoding="utf-8"))
            case = json.loads((REPO / "tools/ck3_mod_acceptance_cases/aub_florin_mandala.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["required_markers"], case["required_markers"])
            self.assertEqual(receipt["mode"], "florin-four-mandala-production-edges")
            self.assertEqual(receipt["runtime_status"], "NOT_RUN")
            self.assertIs(receipt["full_product_pass_from_cell"], False)
            self.assertIs(receipt["native_abi_loaded"], False)
            self.assertIs(receipt["gui_callbacks_mounted"], False)
            self.assertEqual(case["maximum_natural_days"], 2)
            source = REPO / "tools/fixtures/auto_upgrade_buildings_florin_mandala"
            relative_files = {p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file()}
            self.assertEqual(set(receipt["source_file_sha256"]), relative_files)
            self.assertEqual(set(receipt["prepared_file_sha256"]), relative_files)
            for relative in relative_files:
                self.assertEqual((output / relative).read_bytes(), (source / relative).read_bytes())
                if Path(relative).suffix in {".txt", ".yml"}:
                    self.assertTrue((output / relative).read_bytes().startswith(b"\xef\xbb\xbf"))
            self.assertFalse((output / "descriptor.mod").read_bytes().startswith(b"\xef\xbb\xbf"))
            combined = "\n".join(p.read_text(encoding="utf-8-sig") for p in output.rglob("*.txt"))
            for marker in case["required_markers"]:
                self.assertEqual(combined.count('"' + marker + '"'), 1, marker)
            historical = self.assertion_limits(parser.parse_clausewitz((REPO / "tools/fixtures/auto_upgrade_buildings_acceptance/events/aubt_events.txt").read_text(encoding="utf-8-sig")))
            representatives = {m for m in case["required_markers"] if m.startswith("AUBT: TEST PASS ")}
            self.assertEqual(len(representatives), 4)
            self.assertTrue(representatives.issubset(historical))
            self.assertIn("terminal-edge representative", receipt["rules"])
            self.assertIn("different-tier representatives", case["scope"])

    def test_actual_holdings_producer_and_case_keep_four_partial_cells(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, \
                patch.object(prep, "engine_identity", return_value=self.identity()), \
                patch.object(aub, "engine_identity", return_value=self.identity()):
            output = Path(temporary) / "holdings"
            self.assertEqual(aub.prepare_holdings(REPO, output), output)
            receipt = json.loads(output.with_suffix(".prepare.json").read_text(encoding="utf-8"))
            case = json.loads((REPO / "tools/ck3_mod_acceptance_cases/aub_florin_holdings.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["required_markers"], case["required_markers"])
            self.assertIs(receipt["full_product_pass_from_cell"], False)
            self.assertEqual(receipt["runtime_status"], "NOT_RUN")
            combined = "\n".join(p.read_text(encoding="utf-8-sig") for p in output.rglob("*.txt"))
            representatives = {m for m in case["required_markers"] if m.startswith("AUBT: TEST PASS ")}
            historical = self.assertion_limits(parser.parse_clausewitz((REPO / "tools/fixtures/auto_upgrade_buildings_acceptance/events/aubt_events.txt").read_text(encoding="utf-8-sig")))
            self.assertEqual(len(representatives), 4)
            self.assertTrue(representatives.issubset(historical))
            for marker in case["required_markers"]:
                self.assertEqual(combined.count('"' + marker + '"'), 1, marker)
            for relative, expected in receipt["prepared_file_sha256"].items():
                self.assertEqual(hashlib.sha256((output / relative).read_bytes()).hexdigest(), expected)

    def test_mandala_rejects_legacy_engine_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, \
                patch.object(prep, "engine_identity", return_value={"game_version": "1.20.0.4"}), \
                patch.object(aub, "engine_identity", return_value={"game_version": "1.20.0.4"}):
            output = Path(temporary) / "mandala"
            with self.assertRaisesRegex(ValueError, "requires exact"):
                aub.prepare_mandala(REPO, output)
            self.assertFalse(output.exists())
            self.assertFalse(output.with_suffix(".prepare.json").exists())

    def test_florin_reference_rejects_missing_scalar_event_id(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            actions = source / "common/on_action"
            actions.mkdir(parents=True)
            (actions / "missing.txt").write_text(
                "on_game_start_after_lobby = { effect = { trigger_event = { id } } }",
                encoding="utf-8-sig")
            with self.assertRaisesRegex(ValueError, "event ID: missing scalar"):
                aub._validate_florin_event_ids(source)

    def test_mandala_rejects_mismatched_or_ambiguous_case_before_writing(self) -> None:
        for defect in ("wrong-product", "duplicate-marker"):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as temporary, \
                    patch.object(prep, "engine_identity", return_value=self.identity()), \
                    patch.object(aub, "engine_identity", return_value=self.identity()):
                base = Path(temporary)
                repo = base / "repo"
                relative = Path("tools/fixtures/auto_upgrade_buildings_florin_mandala")
                shutil.copytree(REPO / relative, repo / relative)
                contracts = repo / "tools/ck3_mod_acceptance_cases"
                contracts.mkdir(parents=True)
                case = json.loads((REPO / "tools/ck3_mod_acceptance_cases/aub_florin_mandala.json").read_text(encoding="utf-8"))
                if defect == "wrong-product":
                    case["product"] = "other-product"
                    message = "case identity differs"
                else:
                    case["required_markers"].append(case["required_markers"][0])
                    message = "markers must be unique"
                (contracts / "aub_florin_mandala.json").write_text(json.dumps(case), encoding="utf-8")
                output = base / "output"
                with self.assertRaisesRegex(ValueError, message):
                    aub.prepare_mandala(repo, output)
                self.assertFalse(output.exists())
                self.assertFalse(output.with_suffix(".prepare.json").exists())


if __name__ == "__main__":
    unittest.main()
