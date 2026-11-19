"""Exercise the Florin registry through the public scope consumer.

The File API objects below are owned test data. Actual CMake/CTest and live
qualification remain separate; source pins use the real checkout bodies.
"""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
NATIVE = ROOT / "ck3_autonomous_player/native_bridge"
CONTRACT_ID = "ck3-1210-financial-markets-native-profile-v1"
spec = importlib.util.spec_from_file_location(
    "florin_profile_scope_public_builder", HERE / "ck3_mod_acceptance_build_runtime.py")
if spec is None or spec.loader is None:
    raise ValueError("Public native runtime builder import is unavailable")
builder = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = builder
spec.loader.exec_module(builder)


class FlorinProfileContractConsumer(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = builder.read(HERE / "ck3_mod_acceptance_native_profile_expansions.json")
        cls.contract = builder.select_profile_expansion_contract(cls.registry, CONTRACT_ID)
        paths: set[str] = set()
        for section in ("production_source_lists", "fixture_sources", "fixture_included_bodies"):
            for bodies in cls.contract[section].values():
                paths.update(bodies)
        cls.indexed = {relative: builder.pin(NATIVE / relative) for relative in paths}

    def setUp(self) -> None:
        self.expansion = {"contract": copy.deepcopy(self.contract), "actual": {}}
        self.targets: dict[str, dict] = {}
        self.production: dict[str, dict] = {}
        macros = {(row["target"], row["native_relative"]): row["present"]
                  for row in self.contract["production_macro_contracts"]}
        for name, sources in self.contract["production_source_lists"].items():
            target = self.target(name, sources, [macros.get((name, path), []) for path in sources])
            self.production[name] = target
        self.fixtures: list[dict[str, str]] = []
        for row in self.contract["fixture_contracts"]:
            name = row["target"]
            sources = self.contract["fixture_sources"][name]
            target = self.target(name, sources, [row.get("required_defines", []) for _ in sources])
            target["dependencies"] = [{"id": dependency} for dependency in row["dependency_targets"]
                                      if dependency != name]
            self.fixtures.append({"target": name})
        bodies = {path for paths in self.contract["fixture_sources"].values() for path in paths}
        bodies.update(path for paths in self.contract["fixture_included_bodies"].values() for path in paths)
        self.expansion["actual"]["fixture_source_bindings"] = {
            path: self.indexed[path] for path in sorted(bodies)}

    def target(self, name: str, paths: list[str], defines: list[list[str]]) -> dict:
        target = {"id": name, "name": name,
                  "sources": [{"path": path, "compileGroupIndex": index}
                              for index, path in enumerate(paths)],
                  "compileGroups": [{"defines": [{"define": value} for value in values]}
                                    for values in defines], "dependencies": []}
        self.targets[name] = target
        return target

    def consume(self) -> None:
        builder.profile_expansion_scope(self.expansion, self.production, self.targets,
                                        NATIVE, self.indexed, self.fixtures)

    def source_defines(self, target_name: str, relative: str) -> list[dict[str, str]]:
        target = self.targets[target_name]
        source = next(row for row in target["sources"] if row["path"] == relative)
        return target["compileGroups"][source["compileGroupIndex"]]["defines"]

    def test_explicit_contract_preserves_legacy_default(self) -> None:
        self.assertEqual(builder.select_profile_expansion_contract(self.registry)["contract_id"],
                         "ck3-12004-five-gate-native-profile-v1")
        self.assertEqual(builder.select_profile_expansion_contract(
            self.registry, "ck3-12004-five-gate-native-profile-v5")["contract_id"],
            "ck3-12004-five-gate-native-profile-v5")
        self.assertEqual(self.contract["contract_id"], CONTRACT_ID)

    def test_exact_new_profile_keeps_unqualified_actor_and_cash_closed(self) -> None:
        before = self.contract["before_flags"]
        after = dict(before)
        for name, change in self.contract["flag_changes"].items():
            self.assertEqual(before.get(name), change["before"])
            after[name] = change["after"]
        self.assertEqual((len(before), len(after), len(self.contract["flag_changes"])), (180, 195, 51))
        florin = {name: value for name, value in after.items() if name.startswith("XAR_CK3_ENABLE_1210_")}
        self.assertEqual(sum(value == "ON" for value in florin.values()), 10)
        for leaf in ("ACTOR_FOUNDATION", "PERSONAL_CASH"):
            self.assertEqual(florin["XAR_CK3_ENABLE_1210_" + leaf + "_V1"], "OFF")

    def test_wrapper_bindings_pin_true_production_bodies(self) -> None:
        wrappers = {
            "fixtures/ck3_1210_adapter_body_v1.cpp": "src/ck3_1210_adapter.cpp",
            "fixtures/ck3_1210_full_snapshot_body_v1.cpp": "src/ck3_1210_full_snapshot_v1.cpp",
        }
        for name, sources in self.contract["fixture_sources"].items():
            for wrapper, body in wrappers.items():
                if wrapper in sources:
                    with self.subTest(fixture=name, body=body):
                        self.assertIn(body, self.contract["fixture_included_bodies"].get(name, []))
                        self.assertIn('#include "../' + body + '"',
                                      (NATIVE / wrapper).read_text(encoding="utf-8-sig"))

    def test_public_scope_accepts_complete_owned_codemodel(self) -> None:
        self.consume()

    def test_same_count_production_body_substitution_is_rejected(self) -> None:
        target = self.targets["xar_ck3_12002_runtime"]
        source = next(row for row in target["sources"] if row["path"] == "src/ck3_1210_adapter.cpp")
        source["path"] = "src/ck3_1210_core.cpp"
        with self.assertRaisesRegex(ValueError, "production source bodies differ"):
            self.consume()

    def test_missing_enabled_adapter_macro_is_rejected(self) -> None:
        definitions = self.source_defines("xar_ck3_12002_runtime", "src/ck3_1210_adapter.cpp")
        definitions.remove({"define": "XAR_CK3_ENABLE_1210_GUI_CONTROL_V1=1"})
        with self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
            self.consume()

    def test_zero_valued_closed_production_macro_is_still_rejected(self) -> None:
        self.source_defines("xar_ck3_12002_runtime", "src/ck3_1210_adapter.cpp").append(
            {"define": "XAR_CK3_ENABLE_1210_PERSONAL_CASH_V1=0"})
        with self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
            self.consume()

    def test_missing_one_of_nineteen_fixture_receipts_is_rejected(self) -> None:
        self.fixtures.pop()
        with self.assertRaisesRegex(ValueError, "exact reviewed finite target set differs"):
            self.consume()

    def test_zero_valued_full_macro_cannot_leak_into_identity_fixture(self) -> None:
        self.source_defines("xar_ck3_1210_identity_test", "fixtures/ck3_1210_adapter_body_v1.cpp").append(
            {"define": "XAR_CK3_ENABLE_1210_FULL_SNAPSHOT_V1=0"})
        with self.assertRaisesRegex(ValueError, "fixture compile definitions differ"):
            self.consume()

    def test_included_production_body_pin_cannot_be_omitted(self) -> None:
        self.expansion["actual"]["fixture_source_bindings"].pop("src/ck3_1210_adapter.cpp")
        with self.assertRaisesRegex(ValueError, "direct/included body pins differ"):
            self.consume()


class FlorinToastProfileContractConsumer(unittest.TestCase):
    """Versioned real source registry through the unchanged public scope guard."""
    CONTRACT_ID = "ck3-1210-financial-markets-native-profile-v4"
    NEW_SOURCES = (
        "src/ck3_1210_toast_objects_v1.cpp", "src/ck3_1210_toast_objects_native_v1.cpp",
        "src/ck3_1210_toast_query_v1.cpp", "src/ck3_1210_toast_query_native_v1.cpp",
        "src/ck3_1210_toast_scope_identity_v1.cpp", "src/ck3_1210_toast_scope_identity_native_v1.cpp",
    )

    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = builder.read(HERE / "ck3_mod_acceptance_native_profile_expansions.json")
        cls.contract = builder.select_profile_expansion_contract(cls.registry, cls.CONTRACT_ID)
        paths = {relative for section in ("production_source_lists", "fixture_sources", "fixture_included_bodies")
                 for bodies in cls.contract[section].values() for relative in bodies}
        cls.indexed = {relative: builder.pin(NATIVE / relative) for relative in paths}

    def setUp(self) -> None:
        FlorinProfileContractConsumer.setUp(self)

    target = FlorinProfileContractConsumer.target
    consume = FlorinProfileContractConsumer.consume
    source_defines = FlorinProfileContractConsumer.source_defines

    def test_exact_v4_scope_adds_six_runtime_bodies_and_three_owned_fixtures_with_identical_flags(self) -> None:
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v3")
        self.assertEqual(self.contract["before_flags"], prior["before_flags"])
        self.assertEqual(self.contract["flag_changes"], prior["flag_changes"])
        flags = dict(self.contract["before_flags"])
        flags.update({key: value["after"] for key, value in self.contract["flag_changes"].items()})
        self.assertEqual(len(flags), 201)
        self.assertEqual(flags["XAR_CK3_ENABLE_1210_HOTFIX_26757580_BASIC_V1"], "OFF")
        self.assertEqual(self.contract["production_TUs"], {
            "xar_ck3_bridge":268,"xar_ck3_12002_runtime":530,"xar_bridge_protocol":1})
        old = prior["production_source_lists"]["xar_ck3_12002_runtime"]
        new = self.contract["production_source_lists"]["xar_ck3_12002_runtime"]
        self.assertEqual(set(new) - set(old), set(self.NEW_SOURCES))
        self.assertEqual([relative for relative in new if relative not in self.NEW_SOURCES], old)
        self.assertEqual(len(self.fixtures), 22)
        self.assertEqual(len(prior["fixture_sources"]),19)
        self.assertEqual(builder.select_profile_expansion_contract(self.registry)["contract_id"],
                         "ck3-12004-five-gate-native-profile-v1")
        self.consume()

    def test_old_v3_cannot_authorize_new_six_translation_units(self) -> None:
        self.expansion["contract"] = builder.select_profile_expansion_contract(
            self.registry,"ck3-1210-financial-markets-native-profile-v3")
        with self.assertRaisesRegex(ValueError,"production TU counts differ"):
            self.consume()

    def test_missing_or_same_count_substituted_new_runtime_body_is_rejected(self) -> None:
        sources=self.targets["xar_ck3_12002_runtime"]["sources"]
        original=copy.deepcopy(sources)
        sources[:]=[row for row in sources if row["path"]!=self.NEW_SOURCES[0]]
        with self.assertRaisesRegex(ValueError,"production TU counts differ"):
            self.consume()
        sources[:]=original
        next(row for row in sources if row["path"]==self.NEW_SOURCES[0])["path"]="src/ck3_1210_core.cpp"
        with self.assertRaisesRegex(ValueError,"production source bodies differ"):
            self.consume()

    def test_new_tu_keeps_core_macro_and_forbids_per_source_gui_or_hotfix_permissions(self) -> None:
        definitions=self.source_defines("xar_ck3_12002_runtime",self.NEW_SOURCES[0])
        definitions.remove({"define":"XAR_CK3_ENABLE_1210_CORE_FRAME_V1=1"})
        with self.assertRaisesRegex(ValueError,"per-TU present/absent macros differ"):
            self.consume()
        definitions.append({"define":"XAR_CK3_ENABLE_1210_CORE_FRAME_V1=1"})
        for leaked in ("XAR_CK3_ENABLE_1210_GUI_CONTROL_V1=1","XAR_CK3_ENABLE_1210_HOTFIX_26757580_BASIC_V1=0"):
            with self.subTest(leaked=leaked):
                definitions.append({"define":leaked})
                with self.assertRaisesRegex(ValueError,"per-TU present/absent macros differ"):
                    self.consume()
                definitions.pop()

    def test_new_fixture_receipt_and_real_owned_header_pin_cannot_be_omitted(self) -> None:
        original=self.fixtures.pop()
        with self.assertRaisesRegex(ValueError,"exact reviewed finite target set differs"):
            self.consume()
        self.fixtures.append(original)
        self.expansion["actual"]["fixture_source_bindings"].pop("tests/toast_owned_fixture_v1.hpp")
        with self.assertRaisesRegex(ValueError,"direct/included body pins differ"):
            self.consume()


if __name__ == "__main__":
    unittest.main()
