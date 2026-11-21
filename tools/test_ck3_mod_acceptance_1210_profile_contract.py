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



class FlorinToastRuntimeCapabilityConsumer(unittest.TestCase):
    """Reviewed capability uses the actual public source/flag consumer."""
    TOOL = "ck3_query_current_interface_toast_v1"
    NATIVE_SOURCES = (
        "src/bridge.cpp", "src/ck3_1210_adapter.cpp", "src/ck3_1210_core.cpp",
        "src/ck3_1210_full_snapshot_v1.cpp", "src/ck3_1210_ingame_ready_v1.cpp",
        "src/ck3_1210_gui_request_v1.cpp",
        "src/ck3_1210_toast_objects_v1.cpp", "src/ck3_1210_toast_objects_native_v1.cpp",
        "src/ck3_1210_toast_query_v1.cpp", "src/ck3_1210_toast_query_native_v1.cpp",
        "src/ck3_1210_toast_scope_identity_v1.cpp", "src/ck3_1210_toast_scope_identity_native_v1.cpp",
    )
    SDK_SOURCES = ("native_driver.py", "mcp_server.py", "service.py", "version_identity.py", "gui_window_tree_contract.py")

    def setUp(self) -> None:
        # Real checkout bodies in owned source indices, not a Native execution
        # or a claim that the synthesized index itself is a qualified build.
        self.native = {builder.NATIVE_PREFIX + relative: builder.sig((NATIVE / relative).read_bytes())
                       for relative in self.NATIVE_SOURCES}
        self.sdk = {builder.SDK_PREFIX + "xar_autoplayer/bridge/" + name:
                    builder.sig((ROOT / builder.SDK_PREFIX / "xar_autoplayer/bridge" / name).read_bytes())
                    for name in self.SDK_SOURCES}
        self.flags = {name: "ON" for name in (
            "XAR_CK3_ENABLE_1210_CORE_FRAME_V1", "XAR_CK3_ENABLE_1210_FULL_SNAPSHOT_V1",
            "XAR_CK3_ENABLE_1210_GUI_CONTROL_V1")}
        self.flags["XAR_CK3_ENABLE_1210_HOTFIX_26757580_BASIC_V1"] = "OFF"

    def consume(self):
        return builder.core_1210_source_evidence(self.TOOL, ROOT, NATIVE, self.native, self.sdk, self.flags)

    def test_exact_read_only_toast_rule_consumes_twelve_native_and_five_sdk_real_bodies(self) -> None:
        rule = builder.CORE_1210_CAPABILITIES[self.TOOL]
        self.assertEqual(rule.native_sources, self.NATIVE_SOURCES)
        self.assertEqual(rule.sdk_sources, self.SDK_SOURCES)
        self.assertEqual(rule.required_flags, (
            "XAR_CK3_ENABLE_1210_CORE_FRAME_V1", "XAR_CK3_ENABLE_1210_FULL_SNAPSHOT_V1",
            "XAR_CK3_ENABLE_1210_GUI_CONTROL_V1"))
        evidence = self.consume()
        self.assertEqual(set(evidence), set(self.native) | set(self.sdk))
        self.assertEqual(len(evidence), 17)
        self.assertNotIn("src/ck3_1210_gui_control_native_v1.cpp", rule.native_sources)

    def test_each_required_flag_rejects_missing_off_and_wrong_type(self) -> None:
        for flag in builder.CORE_1210_CAPABILITIES[self.TOOL].required_flags:
            for value in (None, "OFF", True, 1):
                with self.subTest(flag=flag, value=value):
                    original = self.flags.pop(flag)
                    if value is not None:
                        self.flags[flag] = value
                    with self.assertRaisesRegex(ValueError, "Core profile lacks required flag"):
                        self.consume()
                    self.flags[flag] = original

    def test_each_native_provider_requires_exact_qualified_body_and_index_entry(self) -> None:
        for relative in self.NATIVE_SOURCES:
            key = builder.NATIVE_PREFIX + relative
            original = self.native.pop(key)
            with self.subTest(relative=relative, mode="missing"), self.assertRaisesRegex(ValueError, "exact qualified production TU"):
                self.consume()
            self.native[key] = {"bytes": original["bytes"], "sha256": "0" * 64}
            with self.subTest(relative=relative, mode="substituted"), self.assertRaisesRegex(ValueError, "exact qualified production TU"):
                self.consume()
            self.native[key] = original

    def test_each_sdk_provider_requires_exact_loaded_source_index(self) -> None:
        for name in self.SDK_SOURCES:
            key = builder.SDK_PREFIX + "xar_autoplayer/bridge/" + name
            original = self.sdk.pop(key)
            with self.subTest(name=name, mode="missing"), self.assertRaisesRegex(ValueError, "outside the exact source index"):
                self.consume()
            self.sdk[key] = {"bytes": original["bytes"], "sha256": "0" * 64}
            with self.subTest(name=name, mode="substituted"), self.assertRaisesRegex(ValueError, "outside the exact source index"):
                self.consume()
            self.sdk[key] = original

    def test_unknown_toast_name_keeps_unreviewed_provider_closed(self) -> None:
        unknown = self.TOOL + "_unreviewed"
        self.assertNotIn(unknown, builder.CORE_1210_CAPABILITIES)
        with self.assertRaises(KeyError):
            builder.core_1210_source_evidence(unknown, ROOT, NATIVE, self.native, self.sdk, self.flags)

    def test_only_selected_spot_case_requires_tool_without_changing_three_day_budgets(self) -> None:
        products = builder.read(HERE / "ck3_mod_acceptance_products.json")
        cases = products["products"]["financial-markets"]["cases"]
        selected = next(row for row in cases if row["id"] == "spot")
        self.assertEqual(selected["required_mcp_tools"].count(self.TOOL), 1)
        self.assertEqual(selected["budgets"], {"command_timeout": 300, "readiness_timeout": 1800,
            "timeout": 6000, "hold_seconds": 3600, "poll_interval": 0.5})
        config = builder.read(HERE / "ck3_mod_acceptance_cases/financial_markets_spot.json")
        self.assertEqual(config["maximum_natural_days"], 3)
        self.assertEqual(config["required_startup"], [])
        self.assertTrue(all(self.TOOL not in row["required_mcp_tools"] for row in cases if row["id"] != "spot"))


class FlorinOpeningDisabledProfileConsumer(unittest.TestCase):
    """Owned metadata exercises the existing guards; no Native execution credit."""
    CONTRACT_ID = "ck3-1210-financial-markets-native-profile-v5"
    OPENING_FLAG = "XAR_CK3_ENABLE_26757580_OPENING_READONLY56"
    CLOSED_SOURCES = (
        ("xar_ck3_12002_runtime", "src/ck3_1210_adapter.cpp"),
        ("xar_ck3_12002_runtime", "src/ck3_1210_personal_gold_frame_v1.cpp"),
        ("xar_ck3_bridge", "src/bridge.cpp"),
    )
    INACTIVE_SOURCES = (
        "src/ck3_1210_opening_readonly56.cpp", "src/ck3_1210_opening_frame56.cpp",
        "src/ck3_1210_opening_serialize56.cpp",
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

    def test_only_new_explicit_off_extends_actual_201_flag_baseline(self) -> None:
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v4")
        effective = dict(prior["before_flags"])
        effective.update({key: change["after"] for key, change in prior["flag_changes"].items()})
        self.assertEqual(self.contract["before_flags"], effective)
        self.assertEqual(len(effective), 201)
        self.assertNotIn(self.OPENING_FLAG, effective)
        self.assertEqual(self.contract["flag_changes"], {self.OPENING_FLAG: {"before": None, "after": "OFF"}})
        after = dict(effective, **{self.OPENING_FLAG: "OFF"})
        self.assertEqual(len(after), 202)
        self.assertEqual(after["XAR_CK3_ENABLE_1210_HOTFIX_26757580_BASIC_V1"], "OFF")
        self.assertEqual(builder.select_profile_expansion_contract(self.registry)["contract_id"],
                         "ck3-12004-five-gate-native-profile-v1")

    def test_off_scope_preserves_799_units_22_fixtures_and_real_source_pins(self) -> None:
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v4")
        self.assertEqual(self.contract["production_TUs"], {
            "xar_ck3_bridge": 268, "xar_ck3_12002_runtime": 530, "xar_bridge_protocol": 1})
        for field in ("production_source_lists", "fixture_sources", "fixture_included_bodies"):
            self.assertEqual(self.contract[field], prior[field])
        self.assertEqual(len(self.fixtures), 22)
        runtime = self.contract["production_source_lists"]["xar_ck3_12002_runtime"]
        self.assertTrue(all(relative not in runtime for relative in self.INACTIVE_SOURCES))
        for current, previous in zip(self.contract["fixture_contracts"], prior["fixture_contracts"], strict=True):
            restored = copy.deepcopy(current)
            suffix = restored["forbidden_defines"][-3:]
            self.assertEqual(suffix, [self.OPENING_FLAG, self.OPENING_FLAG + "=0", self.OPENING_FLAG + "=1"])
            del restored["forbidden_defines"][-3:]
            self.assertEqual(restored, previous)
        self.consume()

    def test_hidden_opening_define_is_rejected_on_all_three_gate_sources(self) -> None:
        for target, relative in self.CLOSED_SOURCES:
            definitions = self.source_defines(target, relative)
            for value in (self.OPENING_FLAG, self.OPENING_FLAG + "=0", self.OPENING_FLAG + "=1"):
                with self.subTest(target=target, relative=relative, define=value):
                    definitions.append({"define": value})
                    try:
                        with self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
                            self.consume()
                    finally:
                        definitions.pop()

    def test_opening_define_cannot_leak_into_old_or_toast_fixture(self) -> None:
        for target in ("xar_ck3_1210_identity_test", "xar_ck3_1210_toast_query_test"):
            relative = self.contract["fixture_sources"][target][0]
            definitions = self.source_defines(target, relative)
            for value in (self.OPENING_FLAG, self.OPENING_FLAG + "=0", self.OPENING_FLAG + "=1"):
                with self.subTest(target=target, define=value):
                    definitions.append({"define": value})
                    try:
                        with self.assertRaisesRegex(ValueError, "fixture compile definitions differ"):
                            self.consume()
                    finally:
                        definitions.pop()

    def test_off_profile_cannot_add_opening_runtime_body(self) -> None:
        relative = self.INACTIVE_SOURCES[0]
        self.indexed = dict(self.indexed)
        self.indexed[relative] = builder.pin(NATIVE / relative)
        self.targets["xar_ck3_12002_runtime"]["sources"].append({"path": relative, "compileGroupIndex": 0})
        with self.assertRaisesRegex(ValueError, "production TU counts differ"):
            self.consume()

    def consume_profile_receipt(self, *, old_flags: dict[str, str] | None = None,
                                actual_flags: dict[str, str] | None = None) -> dict:
        # The only mock is Git's immutable registry read. Every pin below is a
        # real owned JSON file; these are not CMake/build/qualification receipts.
        import json
        import tempfile
        from types import SimpleNamespace
        from unittest.mock import patch

        machine, commit = "software-profile-fixture", "a" * 40
        previous = {"schema": "ck3-native-profile-v1", "machine_id": machine,
                    "repository_default_flags_changed": False,
                    "flags": dict(self.contract["before_flags"])}
        old_profile = copy.deepcopy(previous)
        if old_flags is not None:
            old_profile["flags"] = old_flags
        profile = copy.deepcopy(previous)
        profile["flags"] = dict(self.contract["before_flags"], **{self.OPENING_FLAG: "OFF"})
        if actual_flags is not None:
            profile["flags"] = actual_flags
        registry_path = HERE / "ck3_mod_acceptance_native_profile_expansions.json"
        registry_bytes = registry_path.read_bytes()
        with tempfile.TemporaryDirectory(prefix="florin-profile-v5-") as folder:
            base = Path(folder)

            def owned(name: str, value: object) -> dict:
                path = base / name
                path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
                return builder.pin(path)

            refs = {"profile": owned("profile.json", profile)}
            for name in ("snapshot", "configured_scope", "production_freeze"):
                refs[name] = owned(name + ".json", {"software_fixture": name})
            actual = {"schema": "ck3-native-profile-expansion-v1", "machine_id": machine,
                      "source_commit": commit, "actual_live_business_qualified": False,
                      "contract": builder.pin(registry_path), "contract_id": self.CONTRACT_ID,
                      "previous_profile": owned("previous-profile.json", previous),
                      "fixture_results": [], **refs}
            value = {"source_commit": commit, "fixture_results": [],
                     "profile_expansion": owned("expansion.json", actual)}
            with patch.object(builder.subprocess, "run", return_value=SimpleNamespace(stdout=registry_bytes)) as git_read:
                result = builder.profile_expansion_contract(value, refs, ROOT, commit, machine, old_profile, profile,
                                                            require_current_contract_pin=True)
                git_read.assert_called_once_with(
                    ["git", "-c", "core.longpaths=true", "show", commit + ":" + builder.PROFILE_EXPANSION_RELATIVE],
                    cwd=ROOT, capture_output=True, check=True)
            return result

    def test_existing_receipt_guard_accepts_only_the_exact_201_to_202_delta(self) -> None:
        self.assertEqual(self.consume_profile_receipt()["contract"]["contract_id"], self.CONTRACT_ID)
        expected = dict(self.contract["before_flags"], **{self.OPENING_FLAG: "OFF"})
        for mode in ("on", "missing", "unrelated"):
            changed = dict(expected)
            if mode == "on":
                changed[self.OPENING_FLAG] = "ON"
            elif mode == "missing":
                del changed[self.OPENING_FLAG]
            else:
                changed["XAR_CK3_ENABLE_1210_HOTFIX_26757580_BASIC_V1"] = "ON"
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
                self.consume_profile_receipt(actual_flags=changed)

    def test_historical_180_flag_profile_cannot_replace_selected_201_baseline(self) -> None:
        historical = builder.select_profile_expansion_contract(
            self.registry, "ck3-1210-financial-markets-native-profile-v4")["before_flags"]
        self.assertEqual(len(historical), 180)
        with self.assertRaisesRegex(ValueError, "prior profile differs"):
            self.consume_profile_receipt(old_flags=copy.deepcopy(historical))


class FlorinSixClosedOptionsProfileConsumer(unittest.TestCase):
    """Six explicit OFF options through unchanged public guards; no Native credit."""
    CONTRACT_ID = "ck3-1210-financial-markets-native-profile-v6"
    NEW_FLAGS = (
        "XAR_CK3_ENABLE_121003_26785313_READONLY_V1",
        "XAR_CK3_ENABLE_1210_HOTFIX_26757580_PERSONAL_CASH_V2",
        "XAR_CK3_ENABLE_26757580_ARMY_FULL58",
        "XAR_CK3_ENABLE_26757580_COUNCIL_OBSERVATION67",
        "XAR_CK3_ENABLE_26757580_SAVE_MAPPED61",
        "XAR_CK3_ENABLE_26757580_WAR_IDENTITY58",
    )
    CLOSED_SOURCES = (
        ("xar_ck3_12002_runtime", "src/ck3_1210_adapter.cpp"),
        ("xar_ck3_12002_runtime", "src/ck3_1210_personal_gold_frame_v1.cpp"),
        ("xar_ck3_bridge", "src/bridge.cpp"),
    )
    NEW_RUNTIME_SOURCES = (
        "src/ck3_26757580_save_mapped61.cpp",
        "src/council_observation65.cpp",
        "src/ck3_26757580_council_frame67.cpp",
        "src/ck3_26757580_council_serialize67.cpp",
    )
    UNREVIEWED_RUNTIME_BODY = "src/ck3_121003_readonly26785313_v1.cpp"

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

    def test_exact_q23_202_flags_gain_only_six_absent_to_off_options(self) -> None:
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v5")
        effective = dict(prior["before_flags"])
        effective.update({key: change["after"] for key, change in prior["flag_changes"].items()})
        self.assertEqual(self.contract["before_flags"], effective)
        self.assertEqual(len(effective), 202)
        self.assertTrue(all(flag not in effective for flag in self.NEW_FLAGS))
        self.assertEqual(self.contract["flag_changes"], {flag: {"before": None, "after": "OFF"} for flag in self.NEW_FLAGS})
        after = dict(effective, **dict.fromkeys(self.NEW_FLAGS, "OFF"))
        self.assertEqual(len(after), 208)
        self.assertEqual(after["XAR_CK3_ENABLE_1210_HOTFIX_26757580_BASIC_V1"], "OFF")
        self.assertEqual(after["XAR_CK3_ENABLE_26757580_OPENING_READONLY56"], "OFF")
        self.assertEqual(builder.select_profile_expansion_contract(self.registry)["contract_id"],
                         "ck3-12004-five-gate-native-profile-v1")

    def test_six_off_match_actual_803_units_keep_22_fixtures_and_add_only_four_source_pins(self) -> None:
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v5")
        self.assertEqual(self.contract["production_TUs"], {
            "xar_ck3_bridge": 268, "xar_ck3_12002_runtime": 534, "xar_bridge_protocol": 1})
        for target, paths in prior["production_source_lists"].items():
            self.assertEqual(self.contract["production_source_lists"][target],
                             paths + list(self.NEW_RUNTIME_SOURCES) if target == "xar_ck3_12002_runtime" else paths)
        for field in ("fixture_sources", "fixture_included_bodies"):
            expected = copy.deepcopy(prior[field])
            if field == "fixture_sources":
                expected["xar_ck3_1210_core_control_test"].append("src/ck3_26757580_save_mapped61.cpp")
            self.assertEqual(self.contract[field], expected)
        self.assertNotIn("xar_ck3_1210_hotfix26757580_basic_test", self.contract["fixture_sources"])
        self.assertEqual(len(self.fixtures), 22)
        self.assertNotIn(self.UNREVIEWED_RUNTIME_BODY,
                         self.contract["production_source_lists"]["xar_ck3_12002_runtime"])
        additions = [spelling for flag in self.NEW_FLAGS for spelling in (flag, flag + "=0", flag + "=1")]
        for current, previous in zip(self.contract["fixture_contracts"], prior["fixture_contracts"], strict=True):
            restored = copy.deepcopy(current)
            self.assertEqual(restored["forbidden_defines"][-18:], additions)
            del restored["forbidden_defines"][-18:]
            expected = copy.deepcopy(previous)
            if current["target"] == "xar_ck3_1210_core_control_test":
                self.assertEqual(expected["translation_units"], 11)
                expected["translation_units"] = 12
            self.assertEqual(restored, expected)
        old_rows = prior["production_macro_contracts"]
        self.assertEqual(len(self.contract["production_macro_contracts"]), len(old_rows) + 4)
        for current, old in zip(self.contract["production_macro_contracts"][:len(old_rows)], old_rows, strict=True):
            restored = copy.deepcopy(current)
            self.assertEqual(restored["absent"][-6:], list(self.NEW_FLAGS))
            del restored["absent"][-6:]
            self.assertEqual(restored, old)
        for current, relative in zip(self.contract["production_macro_contracts"][-4:], self.NEW_RUNTIME_SOURCES, strict=True):
            self.assertEqual(current, {"target": "xar_ck3_12002_runtime", "native_relative": relative,
                                       "present": ["XAR_CK3_ENABLE_1210_CORE_FRAME_V1=1"],
                                       "absent": list(self.NEW_FLAGS)})
        self.consume()

    def test_core_control_provider_is_required_once_and_keeps_save_permission_absent(self) -> None:
        name, relative = "xar_ck3_1210_core_control_test", "src/ck3_26757580_save_mapped61.cpp"
        row = next(row for row in self.contract["fixture_contracts"] if row["target"] == name)
        self.assertEqual(row["translation_units"], 12)
        sources = self.targets[name]["sources"]
        original = copy.deepcopy(sources)
        self.assertEqual(sum(source["path"] == relative for source in sources), 1)
        for mode in ("missing", "duplicate"):
            with self.subTest(mode=mode):
                if mode == "missing":
                    sources[:] = [source for source in original if source["path"] != relative]
                else:
                    sources.append(copy.deepcopy(next(source for source in original if source["path"] == relative)))
                try:
                    with self.assertRaisesRegex(ValueError, "fixture source bodies differ"):
                        self.consume()
                finally:
                    sources[:] = copy.deepcopy(original)
        definitions = self.source_defines(name, relative)
        flag = "XAR_CK3_ENABLE_26757580_SAVE_MAPPED61"
        for spelling in (flag, flag + "=0", flag + "=1"):
            definitions.append({"define": spelling})
            try:
                with self.subTest(define=spelling), self.assertRaisesRegex(ValueError, "fixture compile definitions differ"):
                    self.consume()
            finally:
                definitions.pop()

    def test_same_count_four_body_substitution_or_missing_actual_new_unit_is_rejected(self) -> None:
        # Give the substituted real body its actual pin so this case reaches
        # the source-set guard rather than stopping at the missing-pin guard.
        self.indexed = dict(self.indexed)
        self.indexed[self.UNREVIEWED_RUNTIME_BODY] = builder.pin(NATIVE / self.UNREVIEWED_RUNTIME_BODY)
        sources = self.targets["xar_ck3_12002_runtime"]["sources"]
        original = copy.deepcopy(sources)
        for relative in self.NEW_RUNTIME_SOURCES:
            with self.subTest(source=relative):
                sources[:] = [row for row in original if row["path"] != relative]
                with self.assertRaisesRegex(ValueError, "production TU counts differ"):
                    self.consume()
                sources[:] = copy.deepcopy(original)
                next(row for row in sources if row["path"] == relative)["path"] = self.UNREVIEWED_RUNTIME_BODY
                with self.assertRaisesRegex(ValueError, "production source bodies differ"):
                    self.consume()
                sources[:] = copy.deepcopy(original)

    def test_new_units_keep_actual_core_macro_and_six_permissions_absent(self) -> None:
        for relative in self.NEW_RUNTIME_SOURCES:
            definitions = self.source_defines("xar_ck3_12002_runtime", relative)
            definitions.remove({"define": "XAR_CK3_ENABLE_1210_CORE_FRAME_V1=1"})
            with self.subTest(source=relative), self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
                self.consume()
            definitions.append({"define": "XAR_CK3_ENABLE_1210_CORE_FRAME_V1=1"})
            for flag in self.NEW_FLAGS:
                for spelling in (flag, flag + "=0", flag + "=1"):
                    definitions.append({"define": spelling})
                    try:
                        with self.subTest(source=relative, define=spelling), self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
                            self.consume()
                    finally:
                        definitions.pop()

    def test_each_new_macro_is_absent_on_adapter_cash_and_bridge_even_when_defined_zero(self) -> None:
        for target, relative in self.CLOSED_SOURCES:
            definitions = self.source_defines(target, relative)
            for flag in self.NEW_FLAGS:
                for spelling in (flag, flag + "=0", flag + "=1"):
                    with self.subTest(target=target, relative=relative, define=spelling):
                        definitions.append({"define": spelling})
                        try:
                            with self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
                                self.consume()
                        finally:
                            definitions.pop()

    def test_new_defines_cannot_leak_into_old_identity_or_toast_fixture(self) -> None:
        for target in ("xar_ck3_1210_identity_test", "xar_ck3_1210_toast_query_test"):
            relative = self.contract["fixture_sources"][target][0]
            definitions = self.source_defines(target, relative)
            for flag in self.NEW_FLAGS:
                for spelling in (flag, flag + "=0", flag + "=1"):
                    with self.subTest(target=target, define=spelling):
                        definitions.append({"define": spelling})
                        try:
                            with self.assertRaisesRegex(ValueError, "fixture compile definitions differ"):
                                self.consume()
                        finally:
                            definitions.pop()

    def test_off_profile_cannot_add_unreviewed_current_image_readonly_runtime_body(self) -> None:
        relative = self.UNREVIEWED_RUNTIME_BODY
        self.indexed = dict(self.indexed)
        self.indexed[relative] = builder.pin(NATIVE / relative)
        self.targets["xar_ck3_12002_runtime"]["sources"].append({"path": relative, "compileGroupIndex": 0})
        with self.assertRaisesRegex(ValueError, "production TU counts differ"):
            self.consume()

    def test_single_scope_call_resolves_each_target_source_once(self) -> None:
        from unittest.mock import patch

        # Count actual filesystem resolutions without replacing their results.
        # Normal production and macro lookups alias the same File API objects.
        for name, target in self.production.items():
            self.assertIs(target, self.targets[name])
        expected = sum(len(target["sources"]) for target in self.targets.values())
        calls: list[Path] = []
        original_resolve = builder.Path.resolve

        def counted_resolve(path: Path, strict: bool = False) -> Path:
            calls.append(path)
            return original_resolve(path, strict=strict)

        with patch.object(builder.Path, "resolve", new=counted_resolve):
            self.consume()
        self.assertEqual(len(calls), expected)
        self.assertGreater(expected, 803)  # All reviewed finite fixture TUs too.

    def test_same_named_distinct_target_cannot_reuse_production_macros(self) -> None:
        name, relative = self.CLOSED_SOURCES[0]
        # Equal name/id fields do not make these two metadata objects aliases.
        self.production[name] = copy.deepcopy(self.targets[name])
        self.assertIsNot(self.production[name], self.targets[name])
        self.assertEqual(self.production[name]["id"], self.targets[name]["id"])
        definitions = self.source_defines(name, relative)
        definitions.append({"define": self.NEW_FLAGS[0] + "=0"})
        with self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
            self.consume()

    def test_later_scope_call_rechecks_mutated_metadata_and_actual_pin(self) -> None:
        self.consume()
        name, relative = self.CLOSED_SOURCES[0]
        definitions = self.source_defines(name, relative)
        definitions.append({"define": self.NEW_FLAGS[0] + "=0"})
        try:
            with self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
                self.consume()
        finally:
            definitions.pop()
        self.indexed = dict(self.indexed)
        saved_pin = self.indexed.pop(relative)
        try:
            with self.assertRaisesRegex(ValueError, "missing its actual source pin"):
                self.consume()
        finally:
            self.indexed[relative] = saved_pin
        source = next(row for row in self.targets[name]["sources"] if row["path"] == relative)
        saved_group = source["compileGroupIndex"]
        source["compileGroupIndex"] = True
        try:
            with self.assertRaisesRegex(ValueError, "compile group is missing"):
                self.consume()
        finally:
            source["compileGroupIndex"] = saved_group
        self.consume()

    def consume_profile_receipt(self, *, old_flags: dict[str, str] | None = None,
                                actual_flags: dict[str, str] | None = None) -> dict:
        # Only Git's immutable registry read is mocked. The receipt consumer,
        # JSON serialization and file pins below are the actual public path.
        import json
        import tempfile
        from types import SimpleNamespace
        from unittest.mock import patch

        machine, commit = "software-profile-fixture", "a" * 40
        previous = {"schema": "ck3-native-profile-v1", "machine_id": machine,
                    "repository_default_flags_changed": False, "flags": dict(self.contract["before_flags"])}
        old_profile = copy.deepcopy(previous)
        if old_flags is not None:
            old_profile["flags"] = old_flags
        profile = copy.deepcopy(previous)
        profile["flags"] = dict(self.contract["before_flags"], **dict.fromkeys(self.NEW_FLAGS, "OFF"))
        if actual_flags is not None:
            profile["flags"] = actual_flags
        registry_path = HERE / "ck3_mod_acceptance_native_profile_expansions.json"
        registry_bytes = registry_path.read_bytes()
        with tempfile.TemporaryDirectory(prefix="florin-profile-v6-") as folder:
            base = Path(folder)

            def owned(name: str, value: object) -> dict:
                path = base / name
                path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
                return builder.pin(path)

            refs = {"profile": owned("profile.json", profile)}
            for name in ("snapshot", "configured_scope", "production_freeze"):
                refs[name] = owned(name + ".json", {"software_fixture": name})
            actual = {"schema": "ck3-native-profile-expansion-v1", "machine_id": machine,
                      "source_commit": commit, "actual_live_business_qualified": False,
                      "contract": builder.pin(registry_path), "contract_id": self.CONTRACT_ID,
                      "previous_profile": owned("previous-profile.json", previous), "fixture_results": [], **refs}
            value = {"source_commit": commit, "fixture_results": [],
                     "profile_expansion": owned("expansion.json", actual)}
            with patch.object(builder.subprocess, "run", return_value=SimpleNamespace(stdout=registry_bytes)) as git_read:
                result = builder.profile_expansion_contract(value, refs, ROOT, commit, machine, old_profile, profile,
                                                            require_current_contract_pin=True)
                git_read.assert_called_once_with(
                    ["git", "-c", "core.longpaths=true", "show", commit + ":" + builder.PROFILE_EXPANSION_RELATIVE],
                    cwd=ROOT, capture_output=True, check=True)
            return result

    def test_existing_receipt_guard_accepts_only_exact_202_to_208_delta(self) -> None:
        self.assertEqual(self.consume_profile_receipt()["contract"]["contract_id"], self.CONTRACT_ID)
        expected = dict(self.contract["before_flags"], **dict.fromkeys(self.NEW_FLAGS, "OFF"))
        for flag in self.NEW_FLAGS:
            for mode in ("on", "missing"):
                changed = dict(expected)
                if mode == "on":
                    changed[flag] = "ON"
                else:
                    del changed[flag]
                with self.subTest(flag=flag, mode=mode), self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
                    self.consume_profile_receipt(actual_flags=changed)
        changed = dict(expected)
        changed["XAR_CK3_ENABLE_1210_HOTFIX_26757580_BASIC_V1"] = "ON"
        with self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
            self.consume_profile_receipt(actual_flags=changed)

    def test_historical_180_or_201_flags_cannot_replace_actual_q23_202_baseline(self) -> None:
        for contract_id, count in (("ck3-1210-financial-markets-native-profile-v4", 180),
                                   ("ck3-1210-financial-markets-native-profile-v5", 201)):
            historical = builder.select_profile_expansion_contract(self.registry, contract_id)["before_flags"]
            self.assertEqual(len(historical), count)
            with self.subTest(contract=contract_id), self.assertRaisesRegex(ValueError, "prior profile differs"):
                self.consume_profile_receipt(old_flags=copy.deepcopy(historical))


class FlorinClosedCoreRouteProfileConsumer(unittest.TestCase):
    """Q25's actual208 flags plus one absent-to-OFF route; no new-version credit."""
    CONTRACT_ID = "ck3-1210-financial-markets-native-profile-v7"
    NEW_FLAGS = ("XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1",)
    CLOSED_SOURCES = FlorinSixClosedOptionsProfileConsumer.CLOSED_SOURCES
    UNREVIEWED_BODIES = ("src/ck3_121003_core_route26785313_v1.cpp", "src/ck3_121003_readonly26785313_v1.cpp")

    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = builder.read(HERE / "ck3_mod_acceptance_native_profile_expansions.json")
        cls.contract = builder.select_profile_expansion_contract(cls.registry, cls.CONTRACT_ID)
        paths = {relative for section in ("production_source_lists", "fixture_sources", "fixture_included_bodies")
                 for bodies in cls.contract[section].values() for relative in bodies}
        cls.indexed = {relative: builder.pin(NATIVE / relative) for relative in paths}

    setUp = FlorinProfileContractConsumer.setUp
    target = FlorinProfileContractConsumer.target
    consume = FlorinProfileContractConsumer.consume
    source_defines = FlorinProfileContractConsumer.source_defines
    # The existing helper calls the real receipt consumer, serializes actual
    # owned fixture files and mocks only Git's committed-registry byte read.
    consume_profile_receipt = FlorinSixClosedOptionsProfileConsumer.consume_profile_receipt

    def test_q25_208_flags_gain_only_closed_route_and_keep_exact_803_source_and_22_fixture_graph(self) -> None:
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v6")
        expected = dict(prior["before_flags"])
        expected.update({key: change["after"] for key, change in prior["flag_changes"].items()})
        self.assertEqual(self.contract["before_flags"], expected)
        self.assertEqual(len(expected), 208)
        self.assertNotIn(self.NEW_FLAGS[0], expected)
        self.assertEqual(self.contract["flag_changes"], {self.NEW_FLAGS[0]: {"before": None, "after": "OFF"}})
        self.assertEqual(len(dict(expected, **dict.fromkeys(self.NEW_FLAGS, "OFF"))), 209)
        self.assertEqual(self.contract["production_TUs"], {"xar_ck3_bridge": 268, "xar_ck3_12002_runtime": 534, "xar_bridge_protocol": 1})
        self.assertEqual(len(self.fixtures), 22)
        for field in ("production_source_lists", "fixture_sources", "fixture_included_bodies"):
            self.assertEqual(self.contract[field], prior[field])
        for row, old in zip(self.contract["production_macro_contracts"], prior["production_macro_contracts"], strict=True):
            restored = copy.deepcopy(row)
            self.assertEqual(restored["absent"].pop(), self.NEW_FLAGS[0])
            self.assertEqual(restored, old)
        for row, old in zip(self.contract["fixture_contracts"], prior["fixture_contracts"], strict=True):
            restored = copy.deepcopy(row)
            self.assertEqual(restored["forbidden_defines"][-3:], [self.NEW_FLAGS[0], self.NEW_FLAGS[0] + "=0", self.NEW_FLAGS[0] + "=1"])
            del restored["forbidden_defines"][-3:]
            self.assertEqual(restored, old)
        self.assertEqual(builder.select_profile_expansion_contract(self.registry)["contract_id"], "ck3-12004-five-gate-native-profile-v1")
        self.consume()

    def test_route_macro_even_defined_zero_is_rejected_on_checked_production_and_old_fixtures(self) -> None:
        selections = list(self.CLOSED_SOURCES)
        selections += [(name, self.contract["fixture_sources"][name][0])
                       for name in ("xar_ck3_1210_identity_test", "xar_ck3_1210_toast_query_test")]
        for name, relative in selections:
            definitions = self.source_defines(name, relative)
            message = "fixture compile definitions differ" if name.endswith("_test") else "per-TU present/absent macros differ"
            for spelling in (self.NEW_FLAGS[0], self.NEW_FLAGS[0] + "=0", self.NEW_FLAGS[0] + "=1"):
                definitions.append({"define": spelling})
                try:
                    with self.subTest(target=name, define=spelling), self.assertRaisesRegex(ValueError, message):
                        self.consume()
                finally:
                    definitions.pop()

    def test_route_and_reader_tus_cannot_enter_the_closed_production_graph_even_at_same_count(self) -> None:
        self.indexed = dict(self.indexed)
        sources = self.targets["xar_ck3_12002_runtime"]["sources"]
        original = copy.deepcopy(sources)
        for relative in self.UNREVIEWED_BODIES:
            self.assertNotIn(relative, self.contract["production_source_lists"]["xar_ck3_12002_runtime"])
            self.indexed[relative] = builder.pin(NATIVE / relative)
            sources.append({"path": relative, "compileGroupIndex": 0})
            try:
                with self.subTest(body=relative, change="added"), self.assertRaisesRegex(ValueError, "production TU counts differ"):
                    self.consume()
            finally:
                sources[:] = copy.deepcopy(original)
            sources[0]["path"] = relative
            try:
                with self.subTest(body=relative, change="same-count substitution"), self.assertRaisesRegex(ValueError, "production source bodies differ"):
                    self.consume()
            finally:
                sources[:] = copy.deepcopy(original)

    def test_actual_receipt_consumer_requires_exact_208_to_209_delta_and_rejects_old_profile_or_other_permission(self) -> None:
        self.assertEqual(self.consume_profile_receipt()["contract"]["contract_id"], self.CONTRACT_ID)
        expected = dict(self.contract["before_flags"], **dict.fromkeys(self.NEW_FLAGS, "OFF"))
        for mode in ("on", "missing", "unrelated"):
            changed = dict(expected)
            if mode == "missing":
                del changed[self.NEW_FLAGS[0]]
            else:
                changed[self.NEW_FLAGS[0] if mode == "on" else "XAR_CK3_ENABLE_121003_26785313_READONLY_V1"] = "ON"
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
                self.consume_profile_receipt(actual_flags=changed)
        historical = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v6")["before_flags"]
        self.assertEqual(len(historical), 202)
        with self.assertRaisesRegex(ValueError, "prior profile differs"):
            self.consume_profile_receipt(old_flags=copy.deepcopy(historical))


class FlorinClosedCouncilProgressProfileConsumer(unittest.TestCase):
    """Q26's actual209 flags plus closed BB3 progress; source-only expected806 TUs."""
    CONTRACT_ID = "ck3-1210-financial-markets-native-profile-v8"
    NEW_FLAGS = ("XAR_CK3_ENABLE_26757580_COUNCIL_PROGRESS70",)
    NEW_RUNTIME_SOURCES = (
        "src/council_progress70.cpp",
        "src/ck3_26757580_council_progress_frame70.cpp",
        "src/ck3_26757580_council_progress_serialize70.cpp",
    )
    CLOSED_SOURCES = FlorinSixClosedOptionsProfileConsumer.CLOSED_SOURCES + tuple(
        ("xar_ck3_12002_runtime", relative) for relative in NEW_RUNTIME_SOURCES)
    UNREVIEWED_BODIES = FlorinClosedCoreRouteProfileConsumer.UNREVIEWED_BODIES

    setUpClass = classmethod(FlorinClosedCoreRouteProfileConsumer.setUpClass.__func__)
    setUp = FlorinProfileContractConsumer.setUp
    target = FlorinProfileContractConsumer.target
    consume = FlorinProfileContractConsumer.consume
    source_defines = FlorinProfileContractConsumer.source_defines
    consume_profile_receipt = FlorinSixClosedOptionsProfileConsumer.consume_profile_receipt

    def test_q26_209_flags_gain_only_progress_off_with_three_sources_and_unchanged_22_fixtures(self) -> None:
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v7")
        expected = dict(prior["before_flags"])
        expected.update({key: change["after"] for key, change in prior["flag_changes"].items()})
        self.assertEqual(self.contract["before_flags"], expected)
        self.assertEqual(len(expected), 209)
        self.assertNotIn(self.NEW_FLAGS[0], expected)
        self.assertEqual(self.contract["flag_changes"], {self.NEW_FLAGS[0]: {"before": None, "after": "OFF"}})
        self.assertEqual(len(dict(expected, **dict.fromkeys(self.NEW_FLAGS, "OFF"))), 210)
        self.assertEqual(self.contract["production_TUs"], {"xar_ck3_bridge": 268, "xar_ck3_12002_runtime": 537, "xar_bridge_protocol": 1})
        self.assertEqual(sum(self.contract["production_TUs"].values()), 806)
        for target, sources in prior["production_source_lists"].items():
            self.assertEqual(self.contract["production_source_lists"][target],
                             sources + list(self.NEW_RUNTIME_SOURCES) if target == "xar_ck3_12002_runtime" else sources)
        self.assertEqual(len(self.fixtures), 22)
        for field in ("fixture_sources", "fixture_included_bodies"):
            self.assertEqual(self.contract[field], prior[field])
        self.assertEqual(len(self.contract["production_macro_contracts"]), len(prior["production_macro_contracts"]) + 3)
        for row, old in zip(self.contract["production_macro_contracts"][:-3], prior["production_macro_contracts"], strict=True):
            restored = copy.deepcopy(row)
            self.assertEqual(restored["absent"].pop(), self.NEW_FLAGS[0])
            self.assertEqual(restored, old)
        for row, relative in zip(self.contract["production_macro_contracts"][-3:], self.NEW_RUNTIME_SOURCES, strict=True):
            self.assertEqual(row, {"target": "xar_ck3_12002_runtime", "native_relative": relative,
                                   "present": ["XAR_CK3_ENABLE_1210_CORE_FRAME_V1=1"],
                                   "absent": prior["production_macro_contracts"][-1]["absent"] + list(self.NEW_FLAGS)})
        for row, old in zip(self.contract["fixture_contracts"], prior["fixture_contracts"], strict=True):
            restored = copy.deepcopy(row)
            self.assertEqual(restored["forbidden_defines"][-3:], [self.NEW_FLAGS[0], self.NEW_FLAGS[0] + "=0", self.NEW_FLAGS[0] + "=1"])
            del restored["forbidden_defines"][-3:]
            self.assertEqual(restored, old)
        self.assertEqual(builder.select_profile_expansion_contract(self.registry)["contract_id"], "ck3-12004-five-gate-native-profile-v1")
        self.consume()

    def test_progress_permission_even_zero_is_rejected_on_production_and_old_fixtures(self) -> None:
        selections = list(self.CLOSED_SOURCES)
        selections += [(name, self.contract["fixture_sources"][name][0]) for name in
                       ("xar_ck3_1210_identity_test", "xar_ck3_1210_toast_query_test", "xar_ck3_1210_core_control_test")]
        for name, relative in selections:
            definitions = self.source_defines(name, relative)
            message = "fixture compile definitions differ" if name.endswith("_test") else "per-TU present/absent macros differ"
            for spelling in (self.NEW_FLAGS[0], self.NEW_FLAGS[0] + "=0", self.NEW_FLAGS[0] + "=1"):
                definitions.append({"define": spelling})
                try:
                    with self.subTest(target=name, source=relative, define=spelling), self.assertRaisesRegex(ValueError, message):
                        self.consume()
                finally:
                    definitions.pop()

    def test_each_unconditional_source_requires_exact_pin_body_and_existing_core_macro(self) -> None:
        self.indexed = dict(self.indexed)
        replacement = self.UNREVIEWED_BODIES[0]
        self.indexed[replacement] = builder.pin(NATIVE / replacement)
        sources = self.targets["xar_ck3_12002_runtime"]["sources"]
        original = copy.deepcopy(sources)
        for relative in self.NEW_RUNTIME_SOURCES:
            sources[:] = [row for row in original if row["path"] != relative]
            try:
                with self.subTest(source=relative, mode="missing"), self.assertRaisesRegex(ValueError, "production TU counts differ"):
                    self.consume()
            finally:
                sources[:] = copy.deepcopy(original)
            next(row for row in sources if row["path"] == relative)["path"] = replacement
            try:
                with self.subTest(source=relative, mode="substituted"), self.assertRaisesRegex(ValueError, "production source bodies differ"):
                    self.consume()
            finally:
                sources[:] = copy.deepcopy(original)
            saved = self.indexed.pop(relative)
            try:
                with self.subTest(source=relative, mode="unpinned"), self.assertRaisesRegex(ValueError, "missing its actual source pin"):
                    self.consume()
            finally:
                self.indexed[relative] = saved
            definitions = self.source_defines("xar_ck3_12002_runtime", relative)
            core = {"define": "XAR_CK3_ENABLE_1210_CORE_FRAME_V1=1"}
            definitions.remove(core)
            try:
                with self.subTest(source=relative, mode="core absent"), self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
                    self.consume()
            finally:
                definitions.append(core)

    def test_closed_exact26785313_route_and_reader_bodies_still_cannot_enter_production(self) -> None:
        FlorinClosedCoreRouteProfileConsumer.test_route_and_reader_tus_cannot_enter_the_closed_production_graph_even_at_same_count(self)

    def test_actual_receipt_consumer_requires_exact_209_to_210_delta_and_rejects_old_profile(self) -> None:
        self.assertEqual(self.consume_profile_receipt()["contract"]["contract_id"], self.CONTRACT_ID)
        expected = dict(self.contract["before_flags"], **dict.fromkeys(self.NEW_FLAGS, "OFF"))
        for mode in ("on", "missing", "unrelated"):
            changed = dict(expected)
            if mode == "missing":
                del changed[self.NEW_FLAGS[0]]
            else:
                changed[self.NEW_FLAGS[0] if mode == "on" else "XAR_CK3_ENABLE_1210_HOTFIX_26757580_BASIC_V1"] = "ON"
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
                self.consume_profile_receipt(actual_flags=changed)
        old_q25_flags = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v7")["before_flags"]
        self.assertEqual(len(old_q25_flags), 208)
        with self.assertRaisesRegex(ValueError, "prior profile differs"):
            self.consume_profile_receipt(old_flags=copy.deepcopy(old_q25_flags))


class StockCapabilitiesMetadataConsumer(unittest.TestCase):
    """Use exact real bodies with the public stock-source validator; no Game query."""
    TOOL = "ck3_get_capabilities"
    SDK_SOURCES = ("xar_autoplayer/bridge/mcp_server.py",
                   "xar_autoplayer/bridge/service.py",
                   "xar_autoplayer/bridge/native_driver.py")

    def setUp(self) -> None:
        self.sources = {builder.SDK_PREFIX + relative:
                        builder.sig((ROOT / builder.SDK_PREFIX / relative).read_bytes())
                        for relative in self.SDK_SOURCES}
        self.sources[builder.HOST_RELATIVE] = builder.sig((ROOT / builder.HOST_RELATIVE).read_bytes())

    def consume(self) -> dict[str, object]:
        return builder.stock_read_only_source_evidence(self.TOOL, ROOT, NATIVE, {}, self.sources, {})

    def test_exact_cached_metadata_rule_requires_three_sdk_and_canonical_host_bodies(self) -> None:
        rule = builder.STOCK_READ_ONLY_CAPABILITIES[self.TOOL]
        self.assertEqual(rule.native_sources, ())
        self.assertEqual(rule.required_flags, ())
        self.assertEqual(rule.sdk_sources, self.SDK_SOURCES)
        evidence = self.consume()
        self.assertEqual(set(evidence), set(self.sources))
        self.assertEqual(len(evidence), 4)
        for relative, actual in evidence.items():
            self.assertEqual(actual, builder.pin(ROOT / relative))
        self.assertNotIn(self.TOOL, builder.CORE_1210_CAPABILITIES)

    def test_each_sdk_body_rejects_missing_or_substituted_source_index(self) -> None:
        for relative in self.SDK_SOURCES:
            key = builder.SDK_PREFIX + relative
            original = self.sources.pop(key)
            try:
                with self.subTest(source=key, mode="missing"), self.assertRaisesRegex(ValueError, "outside the exact source index"):
                    self.consume()
                self.sources[key] = {"bytes": original["bytes"], "sha256": "0" * 64}
                with self.subTest(source=key, mode="substituted"), self.assertRaisesRegex(ValueError, "outside the exact source index"):
                    self.consume()
            finally:
                self.sources[key] = original

    def test_canonical_host_rejects_missing_or_substituted_source_index(self) -> None:
        original = self.sources.pop(builder.HOST_RELATIVE)
        try:
            with self.assertRaisesRegex(ValueError, "Stock capabilities host is outside the exact source index"):
                self.consume()
            self.sources[builder.HOST_RELATIVE] = {"bytes": original["bytes"], "sha256": "0" * 64}
            with self.assertRaisesRegex(ValueError, "Stock capabilities host is outside the exact source index"):
                self.consume()
        finally:
            self.sources[builder.HOST_RELATIVE] = original

    def test_unknown_metadata_tool_does_not_borrow_the_stock_rule(self) -> None:
        unknown = self.TOOL + "_unreviewed"
        self.assertNotIn(unknown, builder.STOCK_READ_ONLY_CAPABILITIES)
        with self.assertRaisesRegex(ValueError, "Unreviewed stock read-only capability"):
            builder.stock_read_only_source_evidence(unknown, ROOT, NATIVE, {}, self.sources, {})

    def test_all_continuous14_required_tools_have_reviewed_routes_without_new_status_tool(self) -> None:
        products = builder.read(HERE / "ck3_mod_acceptance_products.json")
        selected = next(row for row in products["products"]["financial-markets"]["cases"]
                        if row["id"] == "clock-cadence-continuous14")
        expected = {self.TOOL, "ck3_take_snapshot", "ck3_take_fresh_full_snapshot_v1", "ck3_execute_step",
                    "ck3_save_checkpoint", "ck3_query_normal_exit_context_v1", "ck3_request_normal_exit_v1",
                    "ck3_observe_normal_exit_v1"}
        self.assertEqual(set(selected["required_mcp_tools"]), expected)
        self.assertEqual(len(selected["required_mcp_tools"]), len(expected))
        self.assertEqual(selected["normal_close"]["reserve_seconds"], 180)
        for tool in expected:
            with self.subTest(tool=tool):
                core = builder.CORE_1210_CAPABILITIES.get(tool)
                stock = builder.STOCK_READ_ONLY_CAPABILITIES.get(tool)
                self.assertTrue(core is not None or stock is not None and not stock.required_flags)
        self.assertEqual(expected - set(builder.CORE_1210_CAPABILITIES), {self.TOOL})
        config = builder.read(HERE / "ck3_mod_acceptance_cases/financial_markets_clock_cadence_continuous14.json")
        self.assertEqual(config["continuous14_contract"]["running_observation"], "native_date_sentinel_status_only")
        self.assertEqual(config["continuous14_contract"]["days"], 14)


class FlorinClosedObserverScopeProfileConsumer(unittest.TestCase):
    """Q29's actual210 flags plus one OFF private scope, with no new sources or capability."""
    CONTRACT_ID = "ck3-1210-financial-markets-native-profile-v9"
    NEW_FLAGS = ("XAR_CK3_ENABLE_26757580_OBSERVER_SCOPE92",)
    CLOSED_SOURCES = (
        ("xar_ck3_bridge", "src/main_thread_query_mailbox_v1.cpp"),
        ("xar_ck3_12002_runtime", "src/main_thread_query_mailbox_v1.cpp"),
        ("xar_ck3_12002_runtime", "src/ck3_12002_semantic_adapter.cpp"),
        ("xar_ck3_12002_runtime", "src/ck3_1210_adapter.cpp"),
    )

    setUpClass = classmethod(FlorinClosedCoreRouteProfileConsumer.setUpClass.__func__)
    setUp = FlorinProfileContractConsumer.setUp
    target = FlorinProfileContractConsumer.target
    consume = FlorinProfileContractConsumer.consume
    source_defines = FlorinProfileContractConsumer.source_defines
    consume_profile_receipt = FlorinSixClosedOptionsProfileConsumer.consume_profile_receipt

    def test_q29_210_flags_gain_only_scope_off_with_same_806_sources_and_22_fixtures(self) -> None:
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v8")
        expected = dict(prior["before_flags"])
        expected.update({key: change["after"] for key, change in prior["flag_changes"].items()})
        self.assertEqual(self.contract["before_flags"], expected)
        self.assertEqual(len(expected), 210)
        self.assertNotIn(self.NEW_FLAGS[0], expected)
        self.assertEqual(self.contract["flag_changes"], {self.NEW_FLAGS[0]: {"before": None, "after": "OFF"}})
        self.assertEqual(len(dict(expected, **dict.fromkeys(self.NEW_FLAGS, "OFF"))), 211)
        self.assertEqual(self.contract["production_TUs"], {"xar_ck3_bridge": 268, "xar_ck3_12002_runtime": 537, "xar_bridge_protocol": 1})
        self.assertEqual(sum(self.contract["production_TUs"].values()), 806)
        self.assertEqual(len(self.fixtures), 22)
        for field in ("production_source_lists", "fixture_sources", "fixture_included_bodies"):
            self.assertEqual(self.contract[field], prior[field])
        self.assertEqual(len(self.contract["production_macro_contracts"]), len(prior["production_macro_contracts"]) + 1)
        for row, old in zip(self.contract["production_macro_contracts"][:-1], prior["production_macro_contracts"], strict=True):
            restored = copy.deepcopy(row)
            self.assertEqual(restored["absent"].pop(), self.NEW_FLAGS[0])
            self.assertEqual(restored, old)
        semantic = copy.deepcopy(next(row for row in prior["production_macro_contracts"]
            if row["target"] == "xar_ck3_12002_runtime" and row["native_relative"] == "src/main_thread_query_mailbox_v1.cpp"))
        semantic["native_relative"] = "src/ck3_12002_semantic_adapter.cpp"
        semantic["absent"].append(self.NEW_FLAGS[0])
        self.assertEqual(self.contract["production_macro_contracts"][-1], semantic)
        for row, old in zip(self.contract["fixture_contracts"], prior["fixture_contracts"], strict=True):
            restored = copy.deepcopy(row)
            self.assertEqual(restored["forbidden_defines"][-3:], [self.NEW_FLAGS[0], self.NEW_FLAGS[0] + "=0", self.NEW_FLAGS[0] + "=1"])
            del restored["forbidden_defines"][-3:]
            self.assertEqual(restored, old)
        self.assertEqual(builder.select_profile_expansion_contract(self.registry)["contract_id"], "ck3-12004-five-gate-native-profile-v1")
        self.consume()

    def test_scope_macro_bare_zero_and_one_are_rejected_on_all_three_cmake_tus(self) -> None:
        # Mailbox is compiled into both production targets, hence four actual rows.
        for target, relative in self.CLOSED_SOURCES:
            definitions = self.source_defines(target, relative)
            for spelling in (self.NEW_FLAGS[0], self.NEW_FLAGS[0] + "=0", self.NEW_FLAGS[0] + "=1"):
                definitions.append({"define": spelling})
                try:
                    with self.subTest(target=target, source=relative, define=spelling), self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
                        self.consume()
                finally:
                    definitions.pop()

    def test_forbidden_scope_spellings_reach_real_identity_toast_and_core_fixture_consumers(self) -> None:
        # All22 rows' exact new ban is checked by the positive closure test above;
        # these three distinct compiled fixture closures exercise actual rejection.
        for target in ("xar_ck3_1210_identity_test", "xar_ck3_1210_toast_query_test", "xar_ck3_1210_core_control_test"):
            relative = self.contract["fixture_sources"][target][0]
            definitions = self.source_defines(target, relative)
            for spelling in (self.NEW_FLAGS[0], self.NEW_FLAGS[0] + "=0", self.NEW_FLAGS[0] + "=1"):
                definitions.append({"define": spelling})
                try:
                    with self.subTest(target=target, define=spelling), self.assertRaisesRegex(ValueError, "fixture compile definitions differ"):
                        self.consume()
                finally:
                    definitions.pop()

    def test_new_semantic_checked_row_requires_existing_actual_core_macro(self) -> None:
        definitions = self.source_defines("xar_ck3_12002_runtime", "src/ck3_12002_semantic_adapter.cpp")
        core = {"define": "XAR_CK3_ENABLE_1210_CORE_FRAME_V1=1"}
        definitions.remove(core)
        try:
            with self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
                self.consume()
        finally:
            definitions.append(core)

    def test_actual_receipt_consumer_requires_q29_210_before_and_rejects_unsupported_scope_on(self) -> None:
        self.assertEqual(self.consume_profile_receipt()["contract"]["contract_id"], self.CONTRACT_ID)
        expected = dict(self.contract["before_flags"], **dict.fromkeys(self.NEW_FLAGS, "OFF"))
        for mode in ("on", "missing", "unrelated"):
            changed = dict(expected)
            if mode == "missing":
                del changed[self.NEW_FLAGS[0]]
            else:
                changed[self.NEW_FLAGS[0] if mode == "on" else "XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1"] = "ON"
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
                self.consume_profile_receipt(actual_flags=changed)
        old_q26 = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v8")["before_flags"]
        self.assertEqual(len(old_q26), 209)
        with self.assertRaisesRegex(ValueError, "prior profile differs"):
            self.consume_profile_receipt(old_flags=copy.deepcopy(old_q26))
        not_absent_before = dict(self.contract["before_flags"], **dict.fromkeys(self.NEW_FLAGS, "OFF"))
        # A later byte-exact rebind may retain the original reviewed210->211 receipt.
        self.assertEqual(self.consume_profile_receipt(old_flags=not_absent_before)["contract"]["contract_id"], self.CONTRACT_ID)


class FlorinClosedGoldV2ProfileConsumer(unittest.TestCase):
    """Exact211->212 OFF profile through unchanged public receipt/scope consumers."""
    CONTRACT_ID = "ck3-1210-financial-markets-native-profile-v10"
    NEW_FLAGS = ("XAR_CK3_ENABLE_121003_26785313_PERSONAL_GOLD_V2",)
    CLOSED_SOURCES = (
        ("xar_ck3_bridge", "src/bridge.cpp"),
        ("xar_ck3_12002_runtime", "src/ck3_1210_adapter.cpp"),
        ("xar_ck3_bridge", "src/game_adapter.cpp"),
        ("xar_ck3_12002_runtime", "src/game_adapter_capabilities.cpp"),
        ("xar_ck3_bridge", "src/game_adapter_capabilities.cpp"),
    )
    setUpClass = classmethod(FlorinClosedCoreRouteProfileConsumer.setUpClass.__func__)
    setUp = FlorinProfileContractConsumer.setUp
    target = FlorinProfileContractConsumer.target
    consume = FlorinProfileContractConsumer.consume
    source_defines = FlorinProfileContractConsumer.source_defines
    consume_profile_receipt = FlorinSixClosedOptionsProfileConsumer.consume_profile_receipt

    def test_q31_211_flags_gain_only_goldv2_off_with_806_tus_and_22_fixtures(self) -> None:
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v9")
        effective = dict(prior["before_flags"])
        effective.update({key: change["after"] for key, change in prior["flag_changes"].items()})
        self.assertEqual(self.contract["before_flags"], effective)
        self.assertEqual(len(effective), 211)
        self.assertNotIn(self.NEW_FLAGS[0], effective)
        self.assertEqual(self.contract["flag_changes"], {self.NEW_FLAGS[0]: {"before": None, "after": "OFF"}})
        self.assertEqual(len(dict(effective, **dict.fromkeys(self.NEW_FLAGS, "OFF"))), 212)
        self.assertEqual(self.contract["production_TUs"], {"xar_ck3_bridge": 268, "xar_ck3_12002_runtime": 537, "xar_bridge_protocol": 1})
        self.assertEqual(len(self.fixtures), 22)
        for field in ("production_source_lists", "fixture_sources", "fixture_included_bodies"):
            self.assertEqual(self.contract[field], prior[field])
        old_rows = prior["production_macro_contracts"]
        self.assertEqual(len(self.contract["production_macro_contracts"]), len(old_rows) + 3)
        for row, old in zip(self.contract["production_macro_contracts"][:len(old_rows)], old_rows, strict=True):
            restored = copy.deepcopy(row)
            self.assertEqual(restored["absent"].pop(), self.NEW_FLAGS[0])
            self.assertEqual(restored, old)
        self.assertEqual(self.contract["production_macro_contracts"][-3:], [
            {"target": target, "native_relative": relative, "present": [], "absent": list(self.NEW_FLAGS)}
            for target, relative in self.CLOSED_SOURCES[-3:]])
        for row, old in zip(self.contract["fixture_contracts"], prior["fixture_contracts"], strict=True):
            restored = copy.deepcopy(row)
            self.assertEqual(restored["forbidden_defines"][-3:], [self.NEW_FLAGS[0], self.NEW_FLAGS[0] + "=0", self.NEW_FLAGS[0] + "=1"])
            del restored["forbidden_defines"][-3:]
            self.assertEqual(restored, old)
        self.assertEqual(builder.select_profile_expansion_contract(self.registry)["contract_id"], "ck3-12004-five-gate-native-profile-v1")
        self.consume()

    def test_goldv2_bare_zero_and_one_reject_on_exact_current_dispatch_consumers(self) -> None:
        for target, relative in self.CLOSED_SOURCES:
            definitions = self.source_defines(target, relative)
            for spelling in (self.NEW_FLAGS[0], self.NEW_FLAGS[0] + "=0", self.NEW_FLAGS[0] + "=1"):
                definitions.append({"define": spelling})
                try:
                    with self.subTest(target=target, source=relative, define=spelling), self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
                        self.consume()
                finally:
                    definitions.pop()

    def test_goldv2_permission_rejects_in_existing_identity_toast_and_core_fixtures(self) -> None:
        for target in ("xar_ck3_1210_identity_test", "xar_ck3_1210_toast_query_test", "xar_ck3_1210_core_control_test"):
            relative = self.contract["fixture_sources"][target][0]
            definitions = self.source_defines(target, relative)
            for spelling in (self.NEW_FLAGS[0], self.NEW_FLAGS[0] + "=0", self.NEW_FLAGS[0] + "=1"):
                definitions.append({"define": spelling})
                try:
                    with self.subTest(target=target, define=spelling), self.assertRaisesRegex(ValueError, "fixture compile definitions differ"):
                        self.consume()
                finally:
                    definitions.pop()

    def test_foreign_goldv2_tu_cannot_replace_a_selected_body_even_at_same_count(self) -> None:
        relative = "src/ck3_121003_personal_gold26785313_v2.cpp"
        self.indexed = dict(self.indexed)
        self.indexed[relative] = builder.pin(NATIVE / relative)
        sources = self.targets["xar_ck3_12002_runtime"]["sources"]
        original = copy.deepcopy(sources)
        next(row for row in sources if row["path"] == "src/game_adapter_capabilities.cpp")["path"] = relative
        try:
            with self.assertRaisesRegex(ValueError, "production source bodies differ"):
                self.consume()
        finally:
            sources[:] = original

    def test_actual_receipt_consumer_requires_211_before_and_only_the_new_off_flag(self) -> None:
        self.assertEqual(self.consume_profile_receipt()["contract"]["contract_id"], self.CONTRACT_ID)
        expected = dict(self.contract["before_flags"], **dict.fromkeys(self.NEW_FLAGS, "OFF"))
        for mode in ("on", "missing", "unrelated"):
            changed = dict(expected)
            if mode == "missing":
                del changed[self.NEW_FLAGS[0]]
            else:
                changed[self.NEW_FLAGS[0] if mode == "on" else "XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1"] = "ON"
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
                self.consume_profile_receipt(actual_flags=changed)
        old_q29 = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v9")["before_flags"]
        self.assertEqual(len(old_q29), 210)
        with self.assertRaisesRegex(ValueError, "prior profile differs"):
            self.consume_profile_receipt(old_flags=copy.deepcopy(old_q29))


class FlorinClosedCurrentGuiExitProfileConsumer(unittest.TestCase):
    """Q33's actual212 flags plus only three closed foreign options; no new ABI credit."""
    CONTRACT_ID = "ck3-1210-financial-markets-native-profile-v11"
    NEW_FLAGS = (
        "XAR_CK3_ENABLE_121003_26785313_GUI_ROOT_INDEX_V1",
        "XAR_CK3_ENABLE_121003_26785313_APPLICATION_EXIT_V1",
        "XAR_CK3_ENABLE_121003_26785313_GUI_WINDOW_V1",
    )
    CLOSED_SOURCES = FlorinClosedGoldV2ProfileConsumer.CLOSED_SOURCES
    FOREIGN_BODIES = (
        "src/ck3_121003_gui_root_index26785313_wire_v1.cpp",
        "src/ck3_121003_application_exit26785313_v1.cpp",
        "src/ck3_121003_gui_window26785313_wire_v1.cpp",
    )
    setUpClass = classmethod(FlorinClosedCoreRouteProfileConsumer.setUpClass.__func__)
    setUp = FlorinProfileContractConsumer.setUp
    target = FlorinProfileContractConsumer.target
    consume = FlorinProfileContractConsumer.consume
    source_defines = FlorinProfileContractConsumer.source_defines
    consume_profile_receipt = FlorinSixClosedOptionsProfileConsumer.consume_profile_receipt

    def test_actual_q33_212_gains_only_three_off_options_with_unchanged_806_and_22_scope(self) -> None:
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v10")
        effective = dict(prior["before_flags"])
        effective.update({key: change["after"] for key, change in prior["flag_changes"].items()})
        self.assertEqual(self.contract["before_flags"], effective)
        self.assertEqual(len(effective), 212)
        self.assertTrue(all(flag not in effective for flag in self.NEW_FLAGS))
        self.assertEqual(self.contract["flag_changes"], {flag: {"before": None, "after": "OFF"} for flag in self.NEW_FLAGS})
        self.assertEqual(len(dict(effective, **dict.fromkeys(self.NEW_FLAGS, "OFF"))), 215)
        self.assertEqual(self.contract["production_TUs"], {"xar_ck3_bridge": 268, "xar_ck3_12002_runtime": 537, "xar_bridge_protocol": 1})
        self.assertEqual(len(self.fixtures), 22)
        for field in ("production_source_lists", "fixture_sources", "fixture_included_bodies"):
            self.assertEqual(self.contract[field], prior[field])
        self.assertEqual(len(self.contract["production_macro_contracts"]), len(prior["production_macro_contracts"]))
        for row, old in zip(self.contract["production_macro_contracts"], prior["production_macro_contracts"], strict=True):
            restored = copy.deepcopy(row)
            self.assertEqual(restored["absent"][-3:], list(self.NEW_FLAGS))
            del restored["absent"][-3:]
            self.assertEqual(restored, old)
        forbidden = [spelling for flag in self.NEW_FLAGS for spelling in (flag, flag + "=0", flag + "=1")]
        for row, old in zip(self.contract["fixture_contracts"], prior["fixture_contracts"], strict=True):
            restored = copy.deepcopy(row)
            self.assertEqual(restored["forbidden_defines"][-9:], forbidden)
            del restored["forbidden_defines"][-9:]
            self.assertEqual(restored, old)
        self.assertEqual(builder.select_profile_expansion_contract(self.registry)["contract_id"], "ck3-12004-five-gate-native-profile-v1")
        self.consume()

    def test_each_new_macro_bare_zero_and_one_reject_on_existing_dispatch_sources(self) -> None:
        for target, relative in self.CLOSED_SOURCES:
            definitions = self.source_defines(target, relative)
            for flag in self.NEW_FLAGS:
                for spelling in (flag, flag + "=0", flag + "=1"):
                    definitions.append({"define": spelling})
                    try:
                        with self.subTest(target=target, source=relative, define=spelling), self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
                            self.consume()
                    finally:
                        definitions.pop()

    def test_each_new_macro_is_rejected_in_existing_identity_toast_and_core_fixtures(self) -> None:
        for target in ("xar_ck3_1210_identity_test", "xar_ck3_1210_toast_query_test", "xar_ck3_1210_core_control_test"):
            relative = self.contract["fixture_sources"][target][0]
            definitions = self.source_defines(target, relative)
            for flag in self.NEW_FLAGS:
                for spelling in (flag, flag + "=0", flag + "=1"):
                    definitions.append({"define": spelling})
                    try:
                        with self.subTest(target=target, define=spelling), self.assertRaisesRegex(ValueError, "fixture compile definitions differ"):
                            self.consume()
                    finally:
                        definitions.pop()

    def test_foreign_gui_or_exit_body_cannot_replace_a_selected_body_at_same_count(self) -> None:
        sources = self.targets["xar_ck3_12002_runtime"]["sources"]
        selected = next(row for row in sources if row["path"] == "src/game_adapter_capabilities.cpp")
        original = selected["path"]
        self.indexed = dict(self.indexed)
        for relative in self.FOREIGN_BODIES:
            self.indexed[relative] = builder.pin(NATIVE / relative)
            selected["path"] = relative
            try:
                with self.subTest(source=relative), self.assertRaisesRegex(ValueError, "production source bodies differ"):
                    self.consume()
            finally:
                selected["path"] = original

    def test_real_receipt_requires_actual_212_before_and_exact_three_off_flags(self) -> None:
        self.assertEqual(self.consume_profile_receipt()["contract"]["contract_id"], self.CONTRACT_ID)
        expected = dict(self.contract["before_flags"], **dict.fromkeys(self.NEW_FLAGS, "OFF"))
        for flag in self.NEW_FLAGS:
            for mode in ("on", "missing"):
                changed = dict(expected)
                if mode == "missing":
                    del changed[flag]
                else:
                    changed[flag] = "ON"
                with self.subTest(flag=flag, mode=mode), self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
                    self.consume_profile_receipt(actual_flags=changed)
        changed = dict(expected)
        changed["XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1"] = "ON"
        with self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
            self.consume_profile_receipt(actual_flags=changed)
        old211 = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v10")["before_flags"]
        self.assertEqual(len(old211), 211)
        with self.assertRaisesRegex(ValueError, "prior profile differs"):
            self.consume_profile_receipt(old_flags=copy.deepcopy(old211))
        with self.assertRaisesRegex(ValueError, "Unknown reviewed profile expansion contract"):
            builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v11-unknown")


class FlorinClosedRiteDraftProfileConsumer(unittest.TestCase):
    """Q34's actual215 flags plus one closed Rite option; no new ABI credit."""
    CONTRACT_ID = "ck3-1210-financial-markets-native-profile-v12"
    NEW_FLAGS = (
        "XAR_CK3_ENABLE_121003_26785313_RITE_DRAFT_V2",
    )
    CLOSED_SOURCES = FlorinClosedGoldV2ProfileConsumer.CLOSED_SOURCES
    FOREIGN_BODIES = (
        "src/ck3_121003_rite_draft26785313_wire_v2.cpp",
    )
    setUpClass = classmethod(FlorinClosedCoreRouteProfileConsumer.setUpClass.__func__)
    setUp = FlorinProfileContractConsumer.setUp
    target = FlorinProfileContractConsumer.target
    consume = FlorinProfileContractConsumer.consume
    source_defines = FlorinProfileContractConsumer.source_defines
    consume_profile_receipt = FlorinSixClosedOptionsProfileConsumer.consume_profile_receipt

    def test_actual_q34_215_gains_only_rite_off_with_unchanged_806_and_22_scope(self) -> None:
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v11")
        effective = dict(prior["before_flags"])
        effective.update({key: change["after"] for key, change in prior["flag_changes"].items()})
        self.assertEqual(self.contract["before_flags"], effective)
        self.assertEqual(len(effective), 215)
        self.assertTrue(all(flag not in effective for flag in self.NEW_FLAGS))
        self.assertEqual(self.contract["flag_changes"], {flag: {"before": None, "after": "OFF"} for flag in self.NEW_FLAGS})
        self.assertEqual(len(dict(effective, **dict.fromkeys(self.NEW_FLAGS, "OFF"))), 216)
        self.assertEqual(self.contract["production_TUs"], {"xar_ck3_bridge": 268, "xar_ck3_12002_runtime": 537, "xar_bridge_protocol": 1})
        self.assertEqual(len(self.fixtures), 22)
        for field in ("production_source_lists", "fixture_sources", "fixture_included_bodies"):
            self.assertEqual(self.contract[field], prior[field])
        self.assertEqual(len(self.contract["production_macro_contracts"]), len(prior["production_macro_contracts"]))
        for row, old in zip(self.contract["production_macro_contracts"], prior["production_macro_contracts"], strict=True):
            restored = copy.deepcopy(row)
            self.assertEqual(restored["absent"][-1:], list(self.NEW_FLAGS))
            del restored["absent"][-1:]
            self.assertEqual(restored, old)
        forbidden = [spelling for flag in self.NEW_FLAGS for spelling in (flag, flag + "=0", flag + "=1")]
        for row, old in zip(self.contract["fixture_contracts"], prior["fixture_contracts"], strict=True):
            restored = copy.deepcopy(row)
            self.assertEqual(restored["forbidden_defines"][-3:], forbidden)
            del restored["forbidden_defines"][-3:]
            self.assertEqual(restored, old)
        self.assertEqual(builder.select_profile_expansion_contract(self.registry)["contract_id"], "ck3-12004-five-gate-native-profile-v1")
        self.consume()

    def test_each_new_macro_bare_zero_and_one_reject_on_existing_dispatch_sources(self) -> None:
        for target, relative in self.CLOSED_SOURCES:
            definitions = self.source_defines(target, relative)
            for flag in self.NEW_FLAGS:
                for spelling in (flag, flag + "=0", flag + "=1"):
                    definitions.append({"define": spelling})
                    try:
                        with self.subTest(target=target, source=relative, define=spelling), self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
                            self.consume()
                    finally:
                        definitions.pop()

    def test_each_new_macro_is_rejected_in_existing_identity_toast_and_core_fixtures(self) -> None:
        for target in ("xar_ck3_1210_identity_test", "xar_ck3_1210_toast_query_test", "xar_ck3_1210_core_control_test"):
            relative = self.contract["fixture_sources"][target][0]
            definitions = self.source_defines(target, relative)
            for flag in self.NEW_FLAGS:
                for spelling in (flag, flag + "=0", flag + "=1"):
                    definitions.append({"define": spelling})
                    try:
                        with self.subTest(target=target, define=spelling), self.assertRaisesRegex(ValueError, "fixture compile definitions differ"):
                            self.consume()
                    finally:
                        definitions.pop()

    def test_foreign_rite_body_cannot_replace_a_selected_body_at_same_count(self) -> None:
        sources = self.targets["xar_ck3_12002_runtime"]["sources"]
        selected = next(row for row in sources if row["path"] == "src/game_adapter_capabilities.cpp")
        original = selected["path"]
        self.indexed = dict(self.indexed)
        for relative in self.FOREIGN_BODIES:
            self.indexed[relative] = builder.pin(NATIVE / relative)
            selected["path"] = relative
            try:
                with self.subTest(source=relative), self.assertRaisesRegex(ValueError, "production source bodies differ"):
                    self.consume()
            finally:
                selected["path"] = original

    def test_real_receipt_requires_actual_215_before_and_exact_rite_off(self) -> None:
        self.assertEqual(self.consume_profile_receipt()["contract"]["contract_id"], self.CONTRACT_ID)
        expected = dict(self.contract["before_flags"], **dict.fromkeys(self.NEW_FLAGS, "OFF"))
        for flag in self.NEW_FLAGS:
            for mode in ("on", "missing"):
                changed = dict(expected)
                if mode == "missing":
                    del changed[flag]
                else:
                    changed[flag] = "ON"
                with self.subTest(flag=flag, mode=mode), self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
                    self.consume_profile_receipt(actual_flags=changed)
        changed = dict(expected)
        changed["XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1"] = "ON"
        with self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
            self.consume_profile_receipt(actual_flags=changed)
        old212 = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v11")["before_flags"]
        self.assertEqual(len(old212), 212)
        with self.assertRaisesRegex(ValueError, "prior profile differs"):
            self.consume_profile_receipt(old_flags=copy.deepcopy(old212))
        with self.assertRaisesRegex(ValueError, "Unknown reviewed profile expansion contract"):
            builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v12-unknown")


class FlorinClosedCurrentResearchProfileConsumer(unittest.TestCase):
    """Actual Q36 before; source-derived OFF graph tested through public consumers."""
    CONTRACT_ID = "ck3-1210-financial-markets-native-profile-v13"
    setUpClass = classmethod(FlorinClosedCoreRouteProfileConsumer.setUpClass.__func__)
    setUp = FlorinProfileContractConsumer.setUp
    target = FlorinProfileContractConsumer.target
    consume = FlorinProfileContractConsumer.consume
    source_defines = FlorinProfileContractConsumer.source_defines
    consume_profile_receipt = FlorinSixClosedOptionsProfileConsumer.consume_profile_receipt
    NEW_FLAGS = ('XAR_CK3_ENABLE_121003_FULL111', 'XAR_CK3_ENABLE_ADMISSION_DIAG125', 'XAR_CK3_ENABLE_CURRENT_STRICT_SENTINEL131', 'XAR_CK3_ENABLE_121003_26785313_COMMAND_BINDINGS_V1', 'XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1', 'XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1', 'XAR_CK3_ENABLE_121003_26785313_DATE_POSTDAY_BINDINGS_V1', 'XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1', 'XAR_CK3_ENABLE_121003_26785313_FRONTEND_MENU_V1')
    AUX_FLAGS = ('XAR_CK3_ENABLE_121003_26785313_DOCTRINE_CATEGORY_OPEN_V1', 'XAR_CK3_ENABLE_121003_26785313_DOCTRINE_SELECT_BINDINGS_V1', 'XAR_CK3_ENABLE_121003_26785313_KNOWN_DOCTRINE_GATE_V1')
    ADDED_RUNTIME = ('src/ck3_121003_full111.cpp', 'src/ck3_121003_save_mapped111.cpp', 'src/ck3_121003_commands26785313_v1.cpp', 'src/ck3_121003_save_checkpoint26785313_v1.cpp', 'src/ck3_121003_save_checkpoint26785313_wire_v1.cpp', 'src/ck3_121003_rite_doctrine26785313_v1.cpp', 'src/ck3_121003_rite_doctrine26785313_wire_v1.cpp', 'src/ck3_121003_rite_doctrine26785313_dispatch_v1.cpp', 'src/ck3_121003_rite_edit_confirmation26785313_v1.cpp', 'src/ck3_121003_doctrine_category26785313_v1.cpp', 'src/ck3_121003_doctrine_select26785313_v1.cpp', 'src/ck3_121003_doctrine_knowledge26785313_v1.cpp', 'src/ck3_121003_date_postday26785313_v1.cpp', 'src/ck3_121003_date_worker_access26785313_v2.cpp', 'src/ck3_121003_date_advance26785313_v1.cpp', 'src/ck3_121003_date_advance26785313_wire_v1.cpp', 'src/ck3_121003_frontend_menu26785313_v1.cpp', 'src/ck3_121003_frontend_menu26785313_wire_v1.cpp', 'src/ck3_121003_frontend_menu26785313_dispatch_v1.cpp')
    ZERO = {('xar_ck3_12002_runtime', 'src/ck3_121003_commands26785313_v1.cpp'): ['XAR_CK3_ENABLE_121003_26785313_COMMAND_BINDINGS_V1'], ('xar_ck3_12002_runtime', 'src/ck3_121003_save_checkpoint26785313_v1.cpp'): ['XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1'], ('xar_ck3_12002_runtime', 'src/ck3_1210_adapter.cpp'): ['XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1'], ('xar_ck3_bridge', 'src/bridge.cpp'): ['XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1'], ('xar_ck3_bridge', 'src/game_adapter.cpp'): ['XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1'], ('xar_ck3_12002_runtime', 'src/ck3_121003_date_postday26785313_v1.cpp'): ['XAR_CK3_ENABLE_121003_26785313_DATE_POSTDAY_BINDINGS_V1'], ('xar_ck3_12002_runtime', 'src/ck3_1210_date_sentinel_v1.cpp'): ['XAR_CK3_ENABLE_121003_26785313_DATE_POSTDAY_BINDINGS_V1'], ('xar_ck3_12002_runtime', 'src/ck3_121003_doctrine_category26785313_v1.cpp'): ['XAR_CK3_ENABLE_121003_26785313_DOCTRINE_CATEGORY_OPEN_V1'], ('xar_ck3_12002_runtime', 'src/ck3_121003_doctrine_select26785313_v1.cpp'): ['XAR_CK3_ENABLE_121003_26785313_DOCTRINE_SELECT_BINDINGS_V1'], ('xar_ck3_12002_runtime', 'src/ck3_121003_doctrine_knowledge26785313_v1.cpp'): ['XAR_CK3_ENABLE_121003_26785313_KNOWN_DOCTRINE_GATE_V1']}

    def test_actual_q36_216_expands_only_nine_off_with_exact_closed_link_scope(self) -> None:
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v12")
        effective = dict(prior["before_flags"])
        effective.update({key: value["after"] for key, value in prior["flag_changes"].items()})
        self.assertEqual(self.contract["before_flags"], effective)
        self.assertEqual(len(effective), 216)
        self.assertEqual(self.contract["flag_changes"], {flag: {"before": None, "after": "OFF"} for flag in self.NEW_FLAGS})
        self.assertEqual(len(dict(effective, **dict.fromkeys(self.NEW_FLAGS, "OFF"))), 225)
        self.assertEqual(self.contract["production_TUs"], {"xar_ck3_bridge": 268, "xar_ck3_12002_runtime": 556, "xar_bridge_protocol": 1})
        self.assertEqual(self.contract["production_source_lists"]["xar_ck3_12002_runtime"], prior["production_source_lists"]["xar_ck3_12002_runtime"] + list(self.ADDED_RUNTIME))
        self.assertEqual(len(self.fixtures), 22)
        self.assertEqual(set(self.contract["fixture_sources"]), set(prior["fixture_sources"]))
        self.assertEqual(self.contract["fixture_included_bodies"], prior["fixture_included_bodies"])
        self.assertEqual(builder.select_profile_expansion_contract(self.registry)["contract_id"], "ck3-12004-five-gate-native-profile-v1")
        self.consume()

    def test_closed_dispatch_rejects_each_new_permission_bare_zero_and_one(self) -> None:
        definitions = self.source_defines("xar_ck3_12002_runtime", "src/ck3_1210_core_frame_v1.cpp")
        for flag in self.NEW_FLAGS + self.AUX_FLAGS:
            for spelling in (flag, flag + "=0", flag + "=1"):
                definitions.append({"define": spelling})
                try:
                    with self.subTest(define=spelling), self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
                        self.consume()
                finally:
                    definitions.pop()

    def test_cmake_literal_zero_is_required_and_cannot_be_bare_on_or_missing(self) -> None:
        for (target, relative), flags in self.ZERO.items():
            definitions = self.source_defines(target, relative)
            for flag in flags:
                position = next(i for i, row in enumerate(definitions) if row["define"] == flag + "=0")
                original = definitions[position]
                for replacement in (flag, flag + "=1", None):
                    definitions[position] = {"define": replacement} if replacement else {"define": "NOMINMAX"}
                    try:
                        with self.subTest(target=target, source=relative, flag=flag, replacement=replacement), self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
                            self.consume()
                    finally:
                        definitions[position] = original

    def test_new_permissions_reject_in_original_identity_and_toast_fixtures(self) -> None:
        for target in ("xar_ck3_1210_identity_test", "xar_ck3_1210_toast_query_test"):
            definitions = self.source_defines(target, self.contract["fixture_sources"][target][0])
            for flag in self.NEW_FLAGS + self.AUX_FLAGS:
                for spelling in (flag, flag + "=0", flag + "=1"):
                    definitions.append({"define": spelling})
                    try:
                        with self.subTest(target=target, define=spelling), self.assertRaisesRegex(ValueError, "fixture compile definitions differ"):
                            self.consume()
                    finally:
                        definitions.pop()

    def test_foreign_on_only_body_cannot_replace_selected_body_at_same_count(self) -> None:
        selected = next(row for row in self.targets["xar_ck3_12002_runtime"]["sources"] if row["path"] == "src/game_adapter_capabilities.cpp")
        original = selected["path"]
        self.indexed = dict(self.indexed)
        for relative in ("src/ck3_121003_readonly26785313_v1.cpp", "src/ck3_121003_core_route26785313_v1.cpp"):
            self.indexed[relative] = builder.pin(NATIVE / relative)
            selected["path"] = relative
            try:
                with self.subTest(source=relative), self.assertRaisesRegex(ValueError, "production source bodies differ"):
                    self.consume()
            finally:
                selected["path"] = original

    def test_closed_full111_fixture_link_body_is_mandatory(self) -> None:
        for target, relative in (("xar_ck3_1210_identity_test", "src/ck3_121003_full111.cpp"), ("xar_ck3_1210_core_control_test", "src/ck3_121003_save_mapped111.cpp")):
            sources = self.targets[target]["sources"]
            position = next(i for i, row in enumerate(sources) if row["path"] == relative)
            removed = sources.pop(position)
            try:
                with self.subTest(target=target, source=relative), self.assertRaisesRegex(ValueError, "fixture source bodies differ"):
                    self.consume()
            finally:
                sources.insert(position, removed)

    def test_real_receipt_requires_q36_before_and_all_nine_explicit_off(self) -> None:
        self.assertEqual(self.consume_profile_receipt()["contract"]["contract_id"], self.CONTRACT_ID)
        expected = dict(self.contract["before_flags"], **dict.fromkeys(self.NEW_FLAGS, "OFF"))
        for flag in self.NEW_FLAGS:
            for mode in ("on", "missing"):
                changed = dict(expected)
                if mode == "missing":
                    del changed[flag]
                else:
                    changed[flag] = "ON"
                with self.subTest(flag=flag, mode=mode), self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
                    self.consume_profile_receipt(actual_flags=changed)
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v12")
        with self.assertRaisesRegex(ValueError, "prior profile differs"):
            self.consume_profile_receipt(old_flags=copy.deepcopy(prior["before_flags"]))
        with self.assertRaisesRegex(ValueError, "Unknown reviewed profile expansion contract"):
            builder.select_profile_expansion_contract(self.registry, self.CONTRACT_ID + "-unknown")


class FlorinClosedGuiControlsCorrectionProfileConsumer(unittest.TestCase):
    """Actual Q36 before; source-derived OFF graph tested through public consumers."""
    CONTRACT_ID = "ck3-1210-financial-markets-native-profile-v14"
    setUpClass = classmethod(FlorinClosedCoreRouteProfileConsumer.setUpClass.__func__)
    setUp = FlorinProfileContractConsumer.setUp
    target = FlorinProfileContractConsumer.target
    consume = FlorinProfileContractConsumer.consume
    source_defines = FlorinProfileContractConsumer.source_defines
    consume_profile_receipt = FlorinSixClosedOptionsProfileConsumer.consume_profile_receipt
    NEW_FLAGS = ('XAR_CK3_ENABLE_121003_FULL111', 'XAR_CK3_ENABLE_ADMISSION_DIAG125', 'XAR_CK3_ENABLE_CURRENT_STRICT_SENTINEL131', 'XAR_CK3_ENABLE_121003_26785313_COMMAND_BINDINGS_V1', 'XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1', 'XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1', 'XAR_CK3_ENABLE_121003_26785313_DATE_POSTDAY_BINDINGS_V1', 'XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1', 'XAR_CK3_ENABLE_121003_26785313_FRONTEND_MENU_V1', 'XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2')
    AUX_FLAGS = ('XAR_CK3_ENABLE_121003_26785313_DOCTRINE_CATEGORY_OPEN_V1', 'XAR_CK3_ENABLE_121003_26785313_DOCTRINE_SELECT_BINDINGS_V1', 'XAR_CK3_ENABLE_121003_26785313_KNOWN_DOCTRINE_GATE_V1')
    ADDED_RUNTIME = ('src/ck3_121003_full111.cpp', 'src/ck3_121003_save_mapped111.cpp', 'src/ck3_121003_commands26785313_v1.cpp', 'src/ck3_121003_save_checkpoint26785313_v1.cpp', 'src/ck3_121003_save_checkpoint26785313_wire_v1.cpp', 'src/ck3_121003_rite_doctrine26785313_v1.cpp', 'src/ck3_121003_rite_doctrine26785313_wire_v1.cpp', 'src/ck3_121003_rite_doctrine26785313_dispatch_v1.cpp', 'src/ck3_121003_rite_edit_confirmation26785313_v1.cpp', 'src/ck3_121003_doctrine_category26785313_v1.cpp', 'src/ck3_121003_doctrine_select26785313_v1.cpp', 'src/ck3_121003_doctrine_knowledge26785313_v1.cpp', 'src/ck3_121003_date_postday26785313_v1.cpp', 'src/ck3_121003_date_worker_access26785313_v2.cpp', 'src/ck3_121003_date_advance26785313_v1.cpp', 'src/ck3_121003_date_advance26785313_wire_v1.cpp', 'src/ck3_121003_frontend_menu26785313_v1.cpp', 'src/ck3_121003_frontend_menu26785313_wire_v1.cpp', 'src/ck3_121003_frontend_menu26785313_dispatch_v1.cpp')
    ZERO = {('xar_ck3_12002_runtime', 'src/ck3_121003_commands26785313_v1.cpp'): ['XAR_CK3_ENABLE_121003_26785313_COMMAND_BINDINGS_V1'], ('xar_ck3_12002_runtime', 'src/ck3_121003_save_checkpoint26785313_v1.cpp'): ['XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1'], ('xar_ck3_12002_runtime', 'src/ck3_1210_adapter.cpp'): ['XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1'], ('xar_ck3_bridge', 'src/bridge.cpp'): ['XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1'], ('xar_ck3_bridge', 'src/game_adapter.cpp'): ['XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1'], ('xar_ck3_12002_runtime', 'src/ck3_121003_date_postday26785313_v1.cpp'): ['XAR_CK3_ENABLE_121003_26785313_DATE_POSTDAY_BINDINGS_V1'], ('xar_ck3_12002_runtime', 'src/ck3_1210_date_sentinel_v1.cpp'): ['XAR_CK3_ENABLE_121003_26785313_DATE_POSTDAY_BINDINGS_V1'], ('xar_ck3_12002_runtime', 'src/ck3_121003_doctrine_category26785313_v1.cpp'): ['XAR_CK3_ENABLE_121003_26785313_DOCTRINE_CATEGORY_OPEN_V1'], ('xar_ck3_12002_runtime', 'src/ck3_121003_doctrine_select26785313_v1.cpp'): ['XAR_CK3_ENABLE_121003_26785313_DOCTRINE_SELECT_BINDINGS_V1'], ('xar_ck3_12002_runtime', 'src/ck3_121003_doctrine_knowledge26785313_v1.cpp'): ['XAR_CK3_ENABLE_121003_26785313_KNOWN_DOCTRINE_GATE_V1']}

    def test_actual_q36_216_expands_only_ten_off_with_exact_closed_link_scope(self) -> None:
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v12")
        effective = dict(prior["before_flags"])
        effective.update({key: value["after"] for key, value in prior["flag_changes"].items()})
        self.assertEqual(self.contract["before_flags"], effective)
        self.assertEqual(len(effective), 216)
        self.assertEqual(self.contract["flag_changes"], {flag: {"before": None, "after": "OFF"} for flag in self.NEW_FLAGS})
        self.assertEqual(len(dict(effective, **dict.fromkeys(self.NEW_FLAGS, "OFF"))), 226)
        self.assertEqual(self.contract["production_TUs"], {"xar_ck3_bridge": 268, "xar_ck3_12002_runtime": 556, "xar_bridge_protocol": 1})
        self.assertEqual(self.contract["production_source_lists"]["xar_ck3_12002_runtime"], prior["production_source_lists"]["xar_ck3_12002_runtime"] + list(self.ADDED_RUNTIME))
        self.assertEqual(len(self.fixtures), 22)
        self.assertEqual(set(self.contract["fixture_sources"]), set(prior["fixture_sources"]))
        self.assertEqual(self.contract["fixture_included_bodies"], prior["fixture_included_bodies"])
        self.assertEqual(builder.select_profile_expansion_contract(self.registry)["contract_id"], "ck3-12004-five-gate-native-profile-v1")
        self.consume()

    def test_closed_dispatch_rejects_each_new_permission_bare_zero_and_one(self) -> None:
        definitions = self.source_defines("xar_ck3_12002_runtime", "src/ck3_1210_core_frame_v1.cpp")
        for flag in self.NEW_FLAGS + self.AUX_FLAGS:
            for spelling in (flag, flag + "=0", flag + "=1"):
                definitions.append({"define": spelling})
                try:
                    with self.subTest(define=spelling), self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
                        self.consume()
                finally:
                    definitions.pop()

    def test_cmake_literal_zero_is_required_and_cannot_be_bare_on_or_missing(self) -> None:
        for (target, relative), flags in self.ZERO.items():
            definitions = self.source_defines(target, relative)
            for flag in flags:
                position = next(i for i, row in enumerate(definitions) if row["define"] == flag + "=0")
                original = definitions[position]
                for replacement in (flag, flag + "=1", None):
                    definitions[position] = {"define": replacement} if replacement else {"define": "NOMINMAX"}
                    try:
                        with self.subTest(target=target, source=relative, flag=flag, replacement=replacement), self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
                            self.consume()
                    finally:
                        definitions[position] = original

    def test_new_permissions_reject_in_original_identity_and_toast_fixtures(self) -> None:
        for target in ("xar_ck3_1210_identity_test", "xar_ck3_1210_toast_query_test"):
            definitions = self.source_defines(target, self.contract["fixture_sources"][target][0])
            for flag in self.NEW_FLAGS + self.AUX_FLAGS:
                for spelling in (flag, flag + "=0", flag + "=1"):
                    definitions.append({"define": spelling})
                    try:
                        with self.subTest(target=target, define=spelling), self.assertRaisesRegex(ValueError, "fixture compile definitions differ"):
                            self.consume()
                    finally:
                        definitions.pop()

    def test_foreign_on_only_body_cannot_replace_selected_body_at_same_count(self) -> None:
        selected = next(row for row in self.targets["xar_ck3_12002_runtime"]["sources"] if row["path"] == "src/game_adapter_capabilities.cpp")
        original = selected["path"]
        self.indexed = dict(self.indexed)
        for relative in ("src/ck3_121003_readonly26785313_v1.cpp", "src/ck3_121003_core_route26785313_v1.cpp"):
            self.indexed[relative] = builder.pin(NATIVE / relative)
            selected["path"] = relative
            try:
                with self.subTest(source=relative), self.assertRaisesRegex(ValueError, "production source bodies differ"):
                    self.consume()
            finally:
                selected["path"] = original

    def test_closed_full111_fixture_link_body_is_mandatory(self) -> None:
        for target, relative in (("xar_ck3_1210_identity_test", "src/ck3_121003_full111.cpp"), ("xar_ck3_1210_core_control_test", "src/ck3_121003_save_mapped111.cpp")):
            sources = self.targets[target]["sources"]
            position = next(i for i, row in enumerate(sources) if row["path"] == relative)
            removed = sources.pop(position)
            try:
                with self.subTest(target=target, source=relative), self.assertRaisesRegex(ValueError, "fixture source bodies differ"):
                    self.consume()
            finally:
                sources.insert(position, removed)

    def test_real_receipt_requires_q36_before_and_all_ten_explicit_off(self) -> None:
        self.assertEqual(self.consume_profile_receipt()["contract"]["contract_id"], self.CONTRACT_ID)
        expected = dict(self.contract["before_flags"], **dict.fromkeys(self.NEW_FLAGS, "OFF"))
        for flag in self.NEW_FLAGS:
            for mode in ("on", "missing"):
                changed = dict(expected)
                if mode == "missing":
                    del changed[flag]
                else:
                    changed[flag] = "ON"
                with self.subTest(flag=flag, mode=mode), self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
                    self.consume_profile_receipt(actual_flags=changed)
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v12")
        with self.assertRaisesRegex(ValueError, "prior profile differs"):
            self.consume_profile_receipt(old_flags=copy.deepcopy(prior["before_flags"]))
        with self.assertRaisesRegex(ValueError, "Unknown reviewed profile expansion contract"):
            builder.select_profile_expansion_contract(self.registry, self.CONTRACT_ID + "-unknown")


class FlorinClosedAubFixtureProfileConsumer(unittest.TestCase):
    """R55/Q36 selected baseline; Q38 is an execution predecessor, not a runtime."""
    CONTRACT_ID = "ck3-1210-financial-markets-native-profile-v15"
    setUpClass = classmethod(FlorinClosedCoreRouteProfileConsumer.setUpClass.__func__)
    setUp = FlorinProfileContractConsumer.setUp
    target = FlorinProfileContractConsumer.target
    consume = FlorinProfileContractConsumer.consume
    source_defines = FlorinProfileContractConsumer.source_defines
    consume_profile_receipt = FlorinSixClosedOptionsProfileConsumer.consume_profile_receipt
    AUB_FLAG = "XAR_CK3_ENABLE_121003_26785313_AUB_PRIVATE_FIXTURE_V1"
    NEW_FLAGS = FlorinClosedGuiControlsCorrectionProfileConsumer.NEW_FLAGS + (AUB_FLAG,)
    ADDED_RUNTIME = (
        "src/ck3_121003_aub_private_console26785313_v1.cpp",
        "src/ck3_121003_aub_observer_fixture26785313_v1.cpp",
        "src/ck3_121003_aub_observer_fixture26785313_wire_v1.cpp",
        "src/ck3_121003_aub_observer_fixture26785313_dispatch_v1.cpp",
    )

    def test_selected_q36_216_to_eleven_off_matches_actual_cmake_and_829_graph(self) -> None:
        import re
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v14")
        self.assertEqual(self.contract["before_flags"], prior["before_flags"])
        self.assertEqual(len(self.contract["before_flags"]), 216)
        self.assertEqual(self.contract["flag_changes"], {flag: {"before": None, "after": "OFF"} for flag in self.NEW_FLAGS})
        self.assertEqual(len(dict(self.contract["before_flags"], **dict.fromkeys(self.NEW_FLAGS, "OFF"))), 227)
        cmake = (NATIVE / "cmake/current267_aub_observer_fixture_v1.cmake").read_text(encoding="utf-8-sig")
        self.assertRegex(cmake, r"option\(" + self.AUB_FLAG + r'\s+"[^"\n]*"\s+OFF\)')
        declaration = cmake.split("set(_xar_aubfix_new ", 1)[1].split(")", 1)[0]
        self.assertEqual(tuple(re.findall(r"src/[^\s)]+\.cpp", declaration)), self.ADDED_RUNTIME)
        self.assertLess(cmake.index("target_sources(xar_ck3_12002_runtime"), cmake.index(" if(" + self.AUB_FLAG + ")"))
        self.assertEqual(self.contract["production_TUs"], {"xar_ck3_bridge": 268, "xar_ck3_12002_runtime": 560, "xar_bridge_protocol": 1})
        for name in ("xar_ck3_bridge", "xar_bridge_protocol"):
            self.assertEqual(self.contract["production_source_lists"][name], prior["production_source_lists"][name])
        self.assertEqual(self.contract["production_source_lists"]["xar_ck3_12002_runtime"], prior["production_source_lists"]["xar_ck3_12002_runtime"] + list(self.ADDED_RUNTIME))
        self.assertEqual(len(self.fixtures), 22)
        for field in ("fixture_sources", "fixture_included_bodies"):
            self.assertEqual(self.contract[field], prior[field])
        for kind in ("wire", "resource", "file"):
            self.assertNotIn("xar_ck3_current_aub_observer_" + kind + "_test", self.contract["fixture_sources"])
        self.assertEqual(builder.select_profile_expansion_contract(self.registry)["contract_id"], "ck3-12004-five-gate-native-profile-v1")
        self.consume()

    def test_aub_off_requires_absent_macro_on_new_bodies_and_dispatch(self) -> None:
        selections = [("xar_ck3_12002_runtime", path) for path in self.ADDED_RUNTIME]
        selections += [("xar_ck3_12002_runtime", "src/ck3_1210_core_frame_v1.cpp"), ("xar_ck3_bridge", "src/bridge.cpp"), ("xar_ck3_bridge", "src/game_adapter.cpp")]
        for target, relative in selections:
            definitions = self.source_defines(target, relative)
            self.assertNotIn({"define": self.AUB_FLAG + "=0"}, definitions)
            for spelling in (self.AUB_FLAG, self.AUB_FLAG + "=0", self.AUB_FLAG + "=1"):
                definitions.append({"define": spelling})
                try:
                    with self.subTest(target=target, source=relative, define=spelling), self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
                        self.consume()
                finally:
                    definitions.pop()

    def test_existing_cmake_literal_zero_remains_required(self) -> None:
        for (target, relative), flags in FlorinClosedGuiControlsCorrectionProfileConsumer.ZERO.items():
            definitions = self.source_defines(target, relative)
            for flag in flags:
                position = next(i for i, row in enumerate(definitions) if row["define"] == flag + "=0")
                original = definitions[position]
                for replacement in (flag, flag + "=1", None):
                    definitions[position] = {"define": replacement} if replacement else {"define": "NOMINMAX"}
                    try:
                        with self.subTest(target=target, source=relative, flag=flag, replacement=replacement), self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
                            self.consume()
                    finally:
                        definitions[position] = original

    def test_eleven_permissions_stay_closed_in_identity_and_toast_fixtures(self) -> None:
        for target in ("xar_ck3_1210_identity_test", "xar_ck3_1210_toast_query_test"):
            definitions = self.source_defines(target, self.contract["fixture_sources"][target][0])
            for flag in self.NEW_FLAGS:
                for spelling in (flag, flag + "=0", flag + "=1"):
                    definitions.append({"define": spelling})
                    try:
                        with self.subTest(target=target, define=spelling), self.assertRaisesRegex(ValueError, "fixture compile definitions differ"):
                            self.consume()
                    finally:
                        definitions.pop()

    def test_each_new_runtime_body_is_mandatory_not_a_same_count_substitution(self) -> None:
        sources = self.targets["xar_ck3_12002_runtime"]["sources"]
        self.indexed = dict(self.indexed)
        foreign = "src/ck3_121003_core_route26785313_v1.cpp"
        self.indexed[foreign] = builder.pin(NATIVE / foreign)
        for relative in self.ADDED_RUNTIME:
            position = next(i for i, row in enumerate(sources) if row["path"] == relative)
            original = sources.pop(position)
            try:
                with self.subTest(source=relative, mode="missing"), self.assertRaisesRegex(ValueError, "production TU counts differ"):
                    self.consume()
            finally:
                sources.insert(position, original)
            original["path"] = foreign
            try:
                with self.subTest(source=relative, mode="foreign replacement"), self.assertRaisesRegex(ValueError, "production source bodies differ"):
                    self.consume()
            finally:
                original["path"] = relative

    def test_original_closed_full111_fixture_links_remain_mandatory(self) -> None:
        for target, relative in (("xar_ck3_1210_identity_test", "src/ck3_121003_full111.cpp"), ("xar_ck3_1210_core_control_test", "src/ck3_121003_save_mapped111.cpp")):
            sources = self.targets[target]["sources"]
            position = next(i for i, row in enumerate(sources) if row["path"] == relative)
            removed = sources.pop(position)
            try:
                with self.subTest(target=target, source=relative), self.assertRaisesRegex(ValueError, "fixture source bodies differ"):
                    self.consume()
            finally:
                sources.insert(position, removed)

    def test_receipt_requires_selected_q36_before_not_q38_and_all_eleven_off(self) -> None:
        self.assertEqual(self.consume_profile_receipt()["contract"]["contract_id"], self.CONTRACT_ID)
        expected = dict(self.contract["before_flags"], **dict.fromkeys(self.NEW_FLAGS, "OFF"))
        for flag in self.NEW_FLAGS:
            for mode in ("on", "missing"):
                changed = dict(expected)
                if mode == "missing":
                    del changed[flag]
                else:
                    changed[flag] = "ON"
                with self.subTest(flag=flag, mode=mode), self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
                    self.consume_profile_receipt(actual_flags=changed)
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v14")
        q38_flags = dict(prior["before_flags"], **{key: value["after"] for key, value in prior["flag_changes"].items()})
        self.assertEqual(len(q38_flags), 226)
        with self.assertRaisesRegex(ValueError, "prior profile differs"):
            self.consume_profile_receipt(old_flags=q38_flags)
        changed = dict(expected)
        changed["XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1"] = "ON"
        with self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
            self.consume_profile_receipt(actual_flags=changed)
        with self.assertRaisesRegex(ValueError, "Unknown reviewed profile expansion contract"):
            builder.select_profile_expansion_contract(self.registry, self.CONTRACT_ID + "-unknown")


class FlorinClosedDjcDeclarationsProfileConsumer(unittest.TestCase):
    """R55/Q36 selected baseline; Q38 is an execution predecessor, not a runtime."""
    CONTRACT_ID = "ck3-1210-financial-markets-native-profile-v16"
    setUpClass = classmethod(FlorinClosedCoreRouteProfileConsumer.setUpClass.__func__)
    setUp = FlorinProfileContractConsumer.setUp
    target = FlorinProfileContractConsumer.target
    consume = FlorinProfileContractConsumer.consume
    source_defines = FlorinProfileContractConsumer.source_defines
    consume_profile_receipt = FlorinSixClosedOptionsProfileConsumer.consume_profile_receipt
    DJC_FLAG = "XAR_CK3_ENABLE_121003_26785313_DJC_DECLARATIONS_V1"
    NEW_FLAGS = FlorinClosedAubFixtureProfileConsumer.NEW_FLAGS + (DJC_FLAG,)
    ADDED_RUNTIME = (
        "src/ck3_121003_djc_declarations26785313_raw_v1.cpp",
        "src/ck3_121003_djc_target_query26785313_owner_v1.cpp",
        "src/ck3_121003_djc_target_query26785313_wire_v1.cpp",
        "src/ck3_121003_djc_target_query26785313_dispatch_v1.cpp",
    )

    def test_selected_q36_216_to_twelve_off_matches_actual_cmake_and_833_graph(self) -> None:
        import re
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v15")
        self.assertEqual(self.contract["before_flags"], prior["before_flags"])
        self.assertEqual(len(self.contract["before_flags"]), 216)
        self.assertEqual(self.contract["flag_changes"], {flag: {"before": None, "after": "OFF"} for flag in self.NEW_FLAGS})
        self.assertEqual(len(dict(self.contract["before_flags"], **dict.fromkeys(self.NEW_FLAGS, "OFF"))), 228)
        cmake = (NATIVE / "cmake/current267_djc_declarations_v1.cmake").read_text(encoding="utf-8-sig")
        self.assertRegex(cmake, r"option\(" + self.DJC_FLAG + r'\s+"[^"\n]*"\s+OFF\)')
        declaration = cmake.split("set(_xar_djc_new ", 1)[1].split(")", 1)[0]
        self.assertEqual(tuple(re.findall(r"src/[^\s)]+\.cpp", declaration)), self.ADDED_RUNTIME)
        self.assertLess(cmake.index("target_sources(xar_ck3_12002_runtime"), cmake.index(" if(" + self.DJC_FLAG + ")"))
        self.assertEqual(self.contract["production_TUs"], {"xar_ck3_bridge": 268, "xar_ck3_12002_runtime": 564, "xar_bridge_protocol": 1})
        for name in ("xar_ck3_bridge", "xar_bridge_protocol"):
            self.assertEqual(self.contract["production_source_lists"][name], prior["production_source_lists"][name])
        self.assertEqual(self.contract["production_source_lists"]["xar_ck3_12002_runtime"], prior["production_source_lists"]["xar_ck3_12002_runtime"] + list(self.ADDED_RUNTIME))
        self.assertEqual(len(self.fixtures), 22)
        for field in ("fixture_sources", "fixture_included_bodies"):
            self.assertEqual(self.contract[field], prior[field])
        for kind in ("wire", "off"):
            self.assertNotIn("xar_ck3_current_djc_query_" + kind + "_test", self.contract["fixture_sources"])
        self.assertEqual(builder.select_profile_expansion_contract(self.registry)["contract_id"], "ck3-12004-five-gate-native-profile-v1")
        self.consume()

    def test_djc_off_requires_absent_macro_on_new_bodies_and_dispatch(self) -> None:
        selections = [("xar_ck3_12002_runtime", path) for path in self.ADDED_RUNTIME]
        selections += [("xar_ck3_12002_runtime", "src/ck3_1210_core_frame_v1.cpp"), ("xar_ck3_bridge", "src/bridge.cpp"), ("xar_ck3_bridge", "src/game_adapter.cpp")]
        for target, relative in selections:
            definitions = self.source_defines(target, relative)
            self.assertNotIn({"define": self.DJC_FLAG + "=0"}, definitions)
            for spelling in (self.DJC_FLAG, self.DJC_FLAG + "=0", self.DJC_FLAG + "=1"):
                definitions.append({"define": spelling})
                try:
                    with self.subTest(target=target, source=relative, define=spelling), self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
                        self.consume()
                finally:
                    definitions.pop()

    def test_existing_cmake_literal_zero_remains_required(self) -> None:
        for (target, relative), flags in FlorinClosedGuiControlsCorrectionProfileConsumer.ZERO.items():
            definitions = self.source_defines(target, relative)
            for flag in flags:
                position = next(i for i, row in enumerate(definitions) if row["define"] == flag + "=0")
                original = definitions[position]
                for replacement in (flag, flag + "=1", None):
                    definitions[position] = {"define": replacement} if replacement else {"define": "NOMINMAX"}
                    try:
                        with self.subTest(target=target, source=relative, flag=flag, replacement=replacement), self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
                            self.consume()
                    finally:
                        definitions[position] = original

    def test_twelve_permissions_stay_closed_in_identity_and_toast_fixtures(self) -> None:
        for target in ("xar_ck3_1210_identity_test", "xar_ck3_1210_toast_query_test"):
            definitions = self.source_defines(target, self.contract["fixture_sources"][target][0])
            for flag in self.NEW_FLAGS:
                for spelling in (flag, flag + "=0", flag + "=1"):
                    definitions.append({"define": spelling})
                    try:
                        with self.subTest(target=target, define=spelling), self.assertRaisesRegex(ValueError, "fixture compile definitions differ"):
                            self.consume()
                    finally:
                        definitions.pop()

    def test_each_new_runtime_body_is_mandatory_not_a_same_count_substitution(self) -> None:
        sources = self.targets["xar_ck3_12002_runtime"]["sources"]
        self.indexed = dict(self.indexed)
        foreign = "src/ck3_121003_core_route26785313_v1.cpp"
        self.indexed[foreign] = builder.pin(NATIVE / foreign)
        for relative in self.ADDED_RUNTIME:
            position = next(i for i, row in enumerate(sources) if row["path"] == relative)
            original = sources.pop(position)
            try:
                with self.subTest(source=relative, mode="missing"), self.assertRaisesRegex(ValueError, "production TU counts differ"):
                    self.consume()
            finally:
                sources.insert(position, original)
            original["path"] = foreign
            try:
                with self.subTest(source=relative, mode="foreign replacement"), self.assertRaisesRegex(ValueError, "production source bodies differ"):
                    self.consume()
            finally:
                original["path"] = relative

    def test_original_closed_full111_fixture_links_remain_mandatory(self) -> None:
        for target, relative in (("xar_ck3_1210_identity_test", "src/ck3_121003_full111.cpp"), ("xar_ck3_1210_core_control_test", "src/ck3_121003_save_mapped111.cpp")):
            sources = self.targets[target]["sources"]
            position = next(i for i, row in enumerate(sources) if row["path"] == relative)
            removed = sources.pop(position)
            try:
                with self.subTest(target=target, source=relative), self.assertRaisesRegex(ValueError, "fixture source bodies differ"):
                    self.consume()
            finally:
                sources.insert(position, removed)

    def test_receipt_requires_selected_q36_before_not_unselected_profiles_and_twelve_off(self) -> None:
        self.assertEqual(self.consume_profile_receipt()["contract"]["contract_id"], self.CONTRACT_ID)
        expected = dict(self.contract["before_flags"], **dict.fromkeys(self.NEW_FLAGS, "OFF"))
        for flag in self.NEW_FLAGS:
            for mode in ("on", "missing"):
                changed = dict(expected)
                if mode == "missing":
                    del changed[flag]
                else:
                    changed[flag] = "ON"
                with self.subTest(flag=flag, mode=mode), self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
                    self.consume_profile_receipt(actual_flags=changed)
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v14")
        q38_flags = dict(prior["before_flags"], **{key: value["after"] for key, value in prior["flag_changes"].items()})
        self.assertEqual(len(q38_flags), 226)
        with self.assertRaisesRegex(ValueError, "prior profile differs"):
            self.consume_profile_receipt(old_flags=q38_flags)
        v15 = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v15")
        unselected = dict(v15["before_flags"], **{key: value["after"] for key, value in v15["flag_changes"].items()})
        self.assertEqual(len(unselected), 227)
        with self.assertRaisesRegex(ValueError, "prior profile differs"):
            self.consume_profile_receipt(old_flags=unselected)
        changed = dict(expected)
        changed["XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1"] = "ON"
        with self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
            self.consume_profile_receipt(actual_flags=changed)
        with self.assertRaisesRegex(ValueError, "Unknown reviewed profile expansion contract"):
            builder.select_profile_expansion_contract(self.registry, self.CONTRACT_ID + "-unknown")


class FlorinClosedSuccessionProfileConsumer(unittest.TestCase):
    """Actual R56/Q39 selected baseline and passed execution predecessor; current267 stays OFF."""
    CONTRACT_ID = "ck3-1210-financial-markets-native-profile-v17"
    setUpClass = classmethod(FlorinClosedCoreRouteProfileConsumer.setUpClass.__func__)
    setUp = FlorinProfileContractConsumer.setUp
    target = FlorinProfileContractConsumer.target
    consume = FlorinProfileContractConsumer.consume
    source_defines = FlorinProfileContractConsumer.source_defines
    consume_profile_receipt = FlorinSixClosedOptionsProfileConsumer.consume_profile_receipt
    SUCCESSION_FLAG = "XAR_CK3_ENABLE_121003_26785313_SUCCESSION_CONTINUE_V1"
    ARMY_FLAG = "XAR_CK3_ENABLE_121003_OWNED_ARMY123"
    AUX_BUILD_FLAG = "XAR_CK3_BUILD_OWNED_SENTINEL142_QUALIFICATION"
    CLOSED_PERMISSIONS = FlorinClosedDjcDeclarationsProfileConsumer.NEW_FLAGS + (SUCCESSION_FLAG,ARMY_FLAG)
    NEW_FLAGS = CLOSED_PERMISSIONS + (AUX_BUILD_FLAG,)
    ADDED_RUNTIME = (
        "src/ck3_121003_succession_continue26785313_raw_v1.cpp",
        "src/ck3_121003_succession_lifecycle26785313_owner_v1.cpp",
        "src/ck3_121003_succession_lifecycle26785313_wire_v1.cpp",
        "src/ck3_121003_succession_lifecycle26785313_dispatch_v1.cpp",
    )

    def test_actual_q39_228_adds_three_off_with_four_closed_runtime_bodies(self) -> None:
        import re
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v16")
        previous_after = dict(prior["before_flags"], **{k: v["after"] for k, v in prior["flag_changes"].items()})
        self.assertEqual(self.contract["before_flags"], previous_after)
        self.assertEqual(len(self.contract["before_flags"]), 228)
        self.assertEqual(self.contract["flag_changes"], {flag: {"before": None, "after": "OFF"} for flag in (self.SUCCESSION_FLAG,self.ARMY_FLAG,self.AUX_BUILD_FLAG)})
        self.assertEqual(len(dict(self.contract["before_flags"], **dict.fromkeys(self.NEW_FLAGS, "OFF"))), 231)
        cmake = (NATIVE / "cmake/current267_succession_continue_v1.cmake").read_text(encoding="utf-8-sig")
        self.assertRegex(cmake, r"option\(" + self.SUCCESSION_FLAG + r'\s+"[^"\n]*"\s+OFF\)')
        declaration = cmake.split("set(_xar_succ_new ", 1)[1].split(")", 1)[0]
        self.assertEqual(tuple(re.findall(r"src/[^\s)]+\.cpp", declaration)), self.ADDED_RUNTIME)
        self.assertLess(cmake.index("target_sources(xar_ck3_12002_runtime"), cmake.index(" if(" + self.SUCCESSION_FLAG + ")"))
        self.assertEqual(self.contract["production_TUs"], {"xar_ck3_bridge": 268, "xar_ck3_12002_runtime": 568, "xar_bridge_protocol": 1})
        for name in ("xar_ck3_bridge", "xar_bridge_protocol"):
            self.assertEqual(self.contract["production_source_lists"][name], prior["production_source_lists"][name])
        self.assertEqual(self.contract["production_source_lists"]["xar_ck3_12002_runtime"], prior["production_source_lists"]["xar_ck3_12002_runtime"] + list(self.ADDED_RUNTIME))
        owned_cmake = (NATIVE / "cmake/current_full111.cmake").read_text(encoding="utf-8-sig")
        self.assertRegex(owned_cmake, r"option\(" + self.ARMY_FLAG + r'\s+"[^"\n]*"\s+OFF\)')
        self.assertLess(owned_cmake.index("if(" + self.ARMY_FLAG + ")"), owned_cmake.index("if(BUILD_TESTING)"))
        aux_cmake = (NATIVE / "cmake/owned_sentinel142_qualification.cmake").read_text(encoding="utf-8-sig")
        self.assertRegex(aux_cmake, r"option\(" + self.AUX_BUILD_FLAG + r'\s+"[^"\n]*"\s+OFF\)')
        self.assertLess(aux_cmake.index("return()"), aux_cmake.index("add_library("))
        self.assertEqual(len(self.fixtures), 22)
        for field in ("fixture_sources", "fixture_included_bodies"):
            self.assertEqual(self.contract[field], prior[field])
        for kind in ("wire", "off"):
            self.assertNotIn("xar_ck3_current_succession_" + kind + "_test", self.contract["fixture_sources"])
        self.assertEqual(builder.select_profile_expansion_contract(self.registry)["contract_id"], "ck3-12004-five-gate-native-profile-v1")
        self.consume()

    def test_succession_off_requires_absent_macro_on_new_bodies_and_dispatch(self) -> None:
        selections = [("xar_ck3_12002_runtime", path) for path in self.ADDED_RUNTIME]
        selections += [("xar_ck3_12002_runtime", "src/ck3_121003_full111.cpp")]
        selections += [("xar_ck3_12002_runtime", "src/ck3_1210_core_frame_v1.cpp"), ("xar_ck3_bridge", "src/bridge.cpp"), ("xar_ck3_bridge", "src/game_adapter.cpp")]
        for target, relative in selections:
            definitions = self.source_defines(target, relative)
            self.assertNotIn({"define": self.SUCCESSION_FLAG + "=0"}, definitions)
            for spelling in (self.SUCCESSION_FLAG, self.SUCCESSION_FLAG + "=0", self.SUCCESSION_FLAG + "=1", self.ARMY_FLAG, self.ARMY_FLAG + "=0", self.ARMY_FLAG + "=1"):
                definitions.append({"define": spelling})
                try:
                    with self.subTest(target=target, source=relative, define=spelling), self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
                        self.consume()
                finally:
                    definitions.pop()

    def test_existing_cmake_literal_zero_remains_required(self) -> None:
        for (target, relative), flags in FlorinClosedGuiControlsCorrectionProfileConsumer.ZERO.items():
            definitions = self.source_defines(target, relative)
            for flag in flags:
                position = next(i for i, row in enumerate(definitions) if row["define"] == flag + "=0")
                original = definitions[position]
                for replacement in (flag, flag + "=1", None):
                    definitions[position] = {"define": replacement} if replacement else {"define": "NOMINMAX"}
                    try:
                        with self.subTest(target=target, source=relative, flag=flag, replacement=replacement), self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
                            self.consume()
                    finally:
                        definitions[position] = original

    def test_fourteen_permissions_stay_closed_in_identity_and_toast_fixtures(self) -> None:
        for target in ("xar_ck3_1210_identity_test", "xar_ck3_1210_toast_query_test"):
            definitions = self.source_defines(target, self.contract["fixture_sources"][target][0])
            for flag in self.CLOSED_PERMISSIONS:
                for spelling in (flag, flag + "=0", flag + "=1"):
                    definitions.append({"define": spelling})
                    try:
                        with self.subTest(target=target, define=spelling), self.assertRaisesRegex(ValueError, "fixture compile definitions differ"):
                            self.consume()
                    finally:
                        definitions.pop()

    def test_each_new_runtime_body_is_mandatory_not_a_same_count_substitution(self) -> None:
        sources = self.targets["xar_ck3_12002_runtime"]["sources"]
        self.indexed = dict(self.indexed)
        foreign = "src/ck3_121003_core_route26785313_v1.cpp"
        self.indexed[foreign] = builder.pin(NATIVE / foreign)
        for relative in self.ADDED_RUNTIME:
            position = next(i for i, row in enumerate(sources) if row["path"] == relative)
            original = sources.pop(position)
            try:
                with self.subTest(source=relative, mode="missing"), self.assertRaisesRegex(ValueError, "production TU counts differ"):
                    self.consume()
            finally:
                sources.insert(position, original)
            original["path"] = foreign
            try:
                with self.subTest(source=relative, mode="foreign replacement"), self.assertRaisesRegex(ValueError, "production source bodies differ"):
                    self.consume()
            finally:
                original["path"] = relative

    def test_original_closed_full111_fixture_links_remain_mandatory(self) -> None:
        for target, relative in (("xar_ck3_1210_identity_test", "src/ck3_121003_full111.cpp"), ("xar_ck3_1210_core_control_test", "src/ck3_121003_save_mapped111.cpp")):
            sources = self.targets[target]["sources"]
            position = next(i for i, row in enumerate(sources) if row["path"] == relative)
            removed = sources.pop(position)
            try:
                with self.subTest(target=target, source=relative), self.assertRaisesRegex(ValueError, "fixture source bodies differ"):
                    self.consume()
            finally:
                sources.insert(position, removed)

    def test_receipt_requires_actual_q39_before_and_three_explicit_off(self) -> None:
        self.assertEqual(self.consume_profile_receipt()["contract"]["contract_id"], self.CONTRACT_ID)
        expected = dict(self.contract["before_flags"], **dict.fromkeys(self.NEW_FLAGS, "OFF"))
        for flag in self.NEW_FLAGS:
            for mode in ("on", "missing"):
                changed = dict(expected)
                if mode == "missing":
                    del changed[flag]
                else:
                    changed[flag] = "ON"
                with self.subTest(flag=flag, mode=mode), self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
                    self.consume_profile_receipt(actual_flags=changed)
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v14")
        q38_flags = dict(prior["before_flags"], **{key: value["after"] for key, value in prior["flag_changes"].items()})
        self.assertEqual(len(q38_flags), 226)
        with self.assertRaisesRegex(ValueError, "prior profile differs"):
            self.consume_profile_receipt(old_flags=q38_flags)
        v15 = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v15")
        unselected = dict(v15["before_flags"], **{key: value["after"] for key, value in v15["flag_changes"].items()})
        self.assertEqual(len(unselected), 227)
        with self.assertRaisesRegex(ValueError, "prior profile differs"):
            self.consume_profile_receipt(old_flags=unselected)
        changed = dict(expected)
        changed["XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1"] = "ON"
        with self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
            self.consume_profile_receipt(actual_flags=changed)
        v16 = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v16")
        with self.assertRaisesRegex(ValueError, "prior profile differs"):
            self.consume_profile_receipt(old_flags=v16["before_flags"])
        with self.assertRaisesRegex(ValueError, "Unknown reviewed profile expansion contract"):
            builder.select_profile_expansion_contract(self.registry, self.CONTRACT_ID + "-unknown")


class FlorinClosedDjcUiProfileConsumer(unittest.TestCase):
    """Actual R57/Q41 selected baseline and passed execution predecessor; current267 DJC UI stays OFF."""
    CONTRACT_ID = "ck3-1210-financial-markets-native-profile-v18"
    setUpClass = classmethod(FlorinClosedCoreRouteProfileConsumer.setUpClass.__func__)
    setUp = FlorinProfileContractConsumer.setUp
    target = FlorinProfileContractConsumer.target
    consume = FlorinProfileContractConsumer.consume
    source_defines = FlorinProfileContractConsumer.source_defines
    consume_profile_receipt = FlorinSixClosedOptionsProfileConsumer.consume_profile_receipt
    DJC_UI_FLAG = "XAR_CK3_ENABLE_121003_26785313_DJC_UI_V1"
    ARMY_FLAG = FlorinClosedSuccessionProfileConsumer.ARMY_FLAG
    CLOSED_PERMISSIONS = FlorinClosedSuccessionProfileConsumer.CLOSED_PERMISSIONS + (DJC_UI_FLAG,)
    NEW_FLAGS = FlorinClosedSuccessionProfileConsumer.NEW_FLAGS + (DJC_UI_FLAG,)
    ADDED_RUNTIME = ('src/ck3_121003_djc_declaration_ui26785313_raw_v1.cpp', 'src/ck3_121003_djc_declaration_ui26785313_owner_v1.cpp', 'src/ck3_121003_djc_declaration_ui26785313_wire_v1.cpp', 'src/ck3_121003_djc_declaration_ui26785313_dispatch_v1.cpp')

    def test_actual_q41_231_adds_one_off_with_four_closed_runtime_bodies(self) -> None:
        import re
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v17")
        previous_after = dict(prior["before_flags"], **{k: v["after"] for k, v in prior["flag_changes"].items()})
        self.assertEqual(self.contract["before_flags"], previous_after)
        self.assertEqual(len(self.contract["before_flags"]), 231)
        self.assertEqual(self.contract["flag_changes"], {self.DJC_UI_FLAG: {"before": None, "after": "OFF"}})
        self.assertEqual(len(dict(self.contract["before_flags"], **dict.fromkeys(self.NEW_FLAGS, "OFF"))), 232)
        cmake = (NATIVE / "cmake/current267_djc_declaration_ui_v1.cmake").read_text(encoding="utf-8-sig")
        self.assertRegex(cmake, r"option\(" + self.DJC_UI_FLAG + r'\s+"[^"\n]*"\s+OFF\)')
        declaration = cmake.split("set(_xar_ui_new ", 1)[1].split(")", 1)[0]
        self.assertEqual(tuple(re.findall(r"src/[^\s)]+\.cpp", declaration)), self.ADDED_RUNTIME)
        self.assertLess(cmake.index("target_sources(xar_ck3_12002_runtime"), cmake.index(" if(" + self.DJC_UI_FLAG + ")"))
        self.assertEqual(self.contract["production_TUs"], {"xar_ck3_bridge": 268, "xar_ck3_12002_runtime": 572, "xar_bridge_protocol": 1})
        for name in ("xar_ck3_bridge", "xar_bridge_protocol"):
            self.assertEqual(self.contract["production_source_lists"][name], prior["production_source_lists"][name])
        self.assertEqual(self.contract["production_source_lists"]["xar_ck3_12002_runtime"], prior["production_source_lists"]["xar_ck3_12002_runtime"] + list(self.ADDED_RUNTIME))
        self.assertEqual(len(self.fixtures), 22)
        for field in ("fixture_sources", "fixture_included_bodies"):
            self.assertEqual(self.contract[field], prior[field])
        for kind in ("wire", "off"):
            self.assertNotIn("xar_ck3_current_djc_ui_" + kind + "_test", self.contract["fixture_sources"])
        self.assertEqual(builder.select_profile_expansion_contract(self.registry)["contract_id"], "ck3-12004-five-gate-native-profile-v1")
        self.consume()

    def test_djc_ui_off_requires_absent_macro_on_new_bodies_and_dispatch(self) -> None:
        selections = [("xar_ck3_12002_runtime", path) for path in self.ADDED_RUNTIME]
        selections += [("xar_ck3_12002_runtime", "src/ck3_121003_full111.cpp")]
        selections += [("xar_ck3_12002_runtime", "src/ck3_1210_core_frame_v1.cpp"), ("xar_ck3_bridge", "src/bridge.cpp"), ("xar_ck3_bridge", "src/game_adapter.cpp")]
        for target, relative in selections:
            definitions = self.source_defines(target, relative)
            self.assertNotIn({"define": self.DJC_UI_FLAG + "=0"}, definitions)
            for spelling in (self.DJC_UI_FLAG, self.DJC_UI_FLAG + "=0", self.DJC_UI_FLAG + "=1", self.ARMY_FLAG, self.ARMY_FLAG + "=0", self.ARMY_FLAG + "=1"):
                definitions.append({"define": spelling})
                try:
                    with self.subTest(target=target, source=relative, define=spelling), self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
                        self.consume()
                finally:
                    definitions.pop()


    def test_existing_cmake_literal_zero_remains_required(self) -> None:
        for (target, relative), flags in FlorinClosedGuiControlsCorrectionProfileConsumer.ZERO.items():
            definitions = self.source_defines(target, relative)
            for flag in flags:
                position = next(i for i, row in enumerate(definitions) if row["define"] == flag + "=0")
                original = definitions[position]
                for replacement in (flag, flag + "=1", None):
                    definitions[position] = {"define": replacement} if replacement else {"define": "NOMINMAX"}
                    try:
                        with self.subTest(target=target, source=relative, flag=flag, replacement=replacement), self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
                            self.consume()
                    finally:
                        definitions[position] = original


    def test_fifteen_permissions_stay_closed_in_identity_and_toast_fixtures(self) -> None:
        for target in ("xar_ck3_1210_identity_test", "xar_ck3_1210_toast_query_test"):
            definitions = self.source_defines(target, self.contract["fixture_sources"][target][0])
            for flag in self.CLOSED_PERMISSIONS:
                for spelling in (flag, flag + "=0", flag + "=1"):
                    definitions.append({"define": spelling})
                    try:
                        with self.subTest(target=target, define=spelling), self.assertRaisesRegex(ValueError, "fixture compile definitions differ"):
                            self.consume()
                    finally:
                        definitions.pop()


    def test_each_new_runtime_body_is_mandatory_not_a_same_count_substitution(self) -> None:
        sources = self.targets["xar_ck3_12002_runtime"]["sources"]
        self.indexed = dict(self.indexed)
        foreign = "src/ck3_121003_core_route26785313_v1.cpp"
        self.indexed[foreign] = builder.pin(NATIVE / foreign)
        for relative in self.ADDED_RUNTIME:
            position = next(i for i, row in enumerate(sources) if row["path"] == relative)
            original = sources.pop(position)
            try:
                with self.subTest(source=relative, mode="missing"), self.assertRaisesRegex(ValueError, "production TU counts differ"):
                    self.consume()
            finally:
                sources.insert(position, original)
            original["path"] = foreign
            try:
                with self.subTest(source=relative, mode="foreign replacement"), self.assertRaisesRegex(ValueError, "production source bodies differ"):
                    self.consume()
            finally:
                original["path"] = relative


    def test_original_closed_full111_fixture_links_remain_mandatory(self) -> None:
        for target, relative in (("xar_ck3_1210_identity_test", "src/ck3_121003_full111.cpp"), ("xar_ck3_1210_core_control_test", "src/ck3_121003_save_mapped111.cpp")):
            sources = self.targets[target]["sources"]
            position = next(i for i, row in enumerate(sources) if row["path"] == relative)
            removed = sources.pop(position)
            try:
                with self.subTest(target=target, source=relative), self.assertRaisesRegex(ValueError, "fixture source bodies differ"):
                    self.consume()
            finally:
                sources.insert(position, removed)


    def test_receipt_requires_actual_q41_before_and_one_explicit_off(self) -> None:
        self.assertEqual(self.consume_profile_receipt()["contract"]["contract_id"], self.CONTRACT_ID)
        expected = dict(self.contract["before_flags"], **{self.DJC_UI_FLAG: "OFF"})
        for flag in self.NEW_FLAGS:
            for mode in ("on", "missing"):
                changed = dict(expected)
                if mode == "missing":
                    del changed[flag]
                else:
                    changed[flag] = "ON"
                with self.subTest(flag=flag, mode=mode), self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
                    self.consume_profile_receipt(actual_flags=changed)
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v17")
        self.assertEqual(len(prior["before_flags"]), 228)
        with self.assertRaisesRegex(ValueError, "prior profile differs"):
            self.consume_profile_receipt(old_flags=prior["before_flags"])
        changed = dict(expected)
        changed["XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1"] = "ON"
        with self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
            self.consume_profile_receipt(actual_flags=changed)
        changed = dict(expected)
        changed["XAR_CK3_UNREVIEWED_DJC_UI_OPTION"] = "OFF"
        with self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
            self.consume_profile_receipt(actual_flags=changed)
        with self.assertRaisesRegex(ValueError, "Unknown reviewed profile expansion contract"):
            builder.select_profile_expansion_contract(self.registry, self.CONTRACT_ID + "-unknown")

class FlorinClosedLetterProfileConsumer(unittest.TestCase):
    """Actual R57/Q41 selected baseline and passed execution predecessor; current267 DJC UI stays OFF."""
    CONTRACT_ID = "ck3-1210-financial-markets-native-profile-v19"
    setUpClass = classmethod(FlorinClosedCoreRouteProfileConsumer.setUpClass.__func__)
    setUp = FlorinProfileContractConsumer.setUp
    target = FlorinProfileContractConsumer.target
    consume = FlorinProfileContractConsumer.consume
    source_defines = FlorinProfileContractConsumer.source_defines
    consume_profile_receipt = FlorinSixClosedOptionsProfileConsumer.consume_profile_receipt
    DJC_UI_FLAG = "XAR_CK3_ENABLE_121003_26785313_DJC_UI_V1"
    LETTER_FLAG = "XAR_CK3_ENABLE_121003_26785313_LETTER_V1"
    ADDITIONAL_FLAGS = (DJC_UI_FLAG,LETTER_FLAG)
    ARMY_FLAG = FlorinClosedSuccessionProfileConsumer.ARMY_FLAG
    CLOSED_PERMISSIONS = FlorinClosedSuccessionProfileConsumer.CLOSED_PERMISSIONS + (DJC_UI_FLAG,LETTER_FLAG)
    NEW_FLAGS = FlorinClosedSuccessionProfileConsumer.NEW_FLAGS + (DJC_UI_FLAG,LETTER_FLAG)
    ADDED_RUNTIME = ('src/ck3_121003_djc_declaration_ui26785313_raw_v1.cpp', 'src/ck3_121003_djc_declaration_ui26785313_owner_v1.cpp', 'src/ck3_121003_djc_declaration_ui26785313_wire_v1.cpp', 'src/ck3_121003_djc_declaration_ui26785313_dispatch_v1.cpp', 'src/ck3_121003_letter26785313_raw_v1.cpp', 'src/ck3_121003_letter26785313_owner_v1.cpp', 'src/ck3_121003_letter26785313_wire_v1.cpp', 'src/ck3_121003_letter26785313_dispatch_v1.cpp')

    def test_actual_q41_231_adds_two_off_with_eight_closed_runtime_bodies(self) -> None:
        import re
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v17")
        previous_after = dict(prior["before_flags"], **{k: v["after"] for k, v in prior["flag_changes"].items()})
        self.assertEqual(self.contract["before_flags"], previous_after)
        self.assertEqual(len(self.contract["before_flags"]), 231)
        self.assertEqual(self.contract["flag_changes"], {flag: {"before": None, "after": "OFF"} for flag in self.ADDITIONAL_FLAGS})
        self.assertEqual(len(dict(self.contract["before_flags"], **dict.fromkeys(self.NEW_FLAGS, "OFF"))), 233)
        for flag, module, variable, expected in ((self.DJC_UI_FLAG, "current267_djc_declaration_ui_v1.cmake", "_xar_ui_new", self.ADDED_RUNTIME[:4]), (self.LETTER_FLAG, "current267_letter_v1.cmake", "_xar_letter_new", self.ADDED_RUNTIME[4:])):
            cmake = (NATIVE / "cmake" / module).read_text(encoding="utf-8-sig")
            self.assertRegex(cmake, r"option\(" + flag + r'\s+"[^"\n]*"\s+OFF\)')
            declaration = cmake.split("set(" + variable + " ", 1)[1].split(")", 1)[0]
            self.assertEqual(tuple(re.findall(r"src/[^\s)]+\.cpp", declaration)), expected)
            self.assertLess(cmake.index("target_sources(xar_ck3_12002_runtime"), cmake.index(" if(" + flag + ")"))
        self.assertEqual(self.contract["production_TUs"], {"xar_ck3_bridge": 268, "xar_ck3_12002_runtime": 576, "xar_bridge_protocol": 1})
        for name in ("xar_ck3_bridge", "xar_bridge_protocol"):
            self.assertEqual(self.contract["production_source_lists"][name], prior["production_source_lists"][name])
        self.assertEqual(self.contract["production_source_lists"]["xar_ck3_12002_runtime"], prior["production_source_lists"]["xar_ck3_12002_runtime"] + list(self.ADDED_RUNTIME))
        self.assertEqual(len(self.fixtures), 22)
        for field in ("fixture_sources", "fixture_included_bodies"):
            self.assertEqual(self.contract[field], prior[field])
        for prefix in ("xar_ck3_current_djc_ui_", "xar_ck3_current_letter_"):
            for kind in ("wire", "off"):
                self.assertNotIn(prefix + kind + "_test", self.contract["fixture_sources"])
        self.assertEqual(builder.select_profile_expansion_contract(self.registry)["contract_id"], "ck3-12004-five-gate-native-profile-v1")
        self.consume()

    def test_djc_ui_off_requires_absent_macro_on_new_bodies_and_dispatch(self) -> None:
        selections = [("xar_ck3_12002_runtime", path) for path in self.ADDED_RUNTIME]
        selections += [("xar_ck3_12002_runtime", "src/ck3_121003_full111.cpp")]
        selections += [("xar_ck3_12002_runtime", "src/ck3_1210_core_frame_v1.cpp"), ("xar_ck3_bridge", "src/bridge.cpp"), ("xar_ck3_bridge", "src/game_adapter.cpp")]
        for target, relative in selections:
            definitions = self.source_defines(target, relative)
            self.assertNotIn({"define": self.DJC_UI_FLAG + "=0"}, definitions)
            for spelling in (self.DJC_UI_FLAG, self.DJC_UI_FLAG + "=0", self.DJC_UI_FLAG + "=1", self.LETTER_FLAG, self.LETTER_FLAG + "=0", self.LETTER_FLAG + "=1", self.ARMY_FLAG, self.ARMY_FLAG + "=0", self.ARMY_FLAG + "=1"):
                definitions.append({"define": spelling})
                try:
                    with self.subTest(target=target, source=relative, define=spelling), self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
                        self.consume()
                finally:
                    definitions.pop()


    def test_existing_cmake_literal_zero_remains_required(self) -> None:
        for (target, relative), flags in FlorinClosedGuiControlsCorrectionProfileConsumer.ZERO.items():
            definitions = self.source_defines(target, relative)
            for flag in flags:
                position = next(i for i, row in enumerate(definitions) if row["define"] == flag + "=0")
                original = definitions[position]
                for replacement in (flag, flag + "=1", None):
                    definitions[position] = {"define": replacement} if replacement else {"define": "NOMINMAX"}
                    try:
                        with self.subTest(target=target, source=relative, flag=flag, replacement=replacement), self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
                            self.consume()
                    finally:
                        definitions[position] = original


    def test_sixteen_permissions_stay_closed_in_identity_and_toast_fixtures(self) -> None:
        for target in ("xar_ck3_1210_identity_test", "xar_ck3_1210_toast_query_test"):
            definitions = self.source_defines(target, self.contract["fixture_sources"][target][0])
            for flag in self.CLOSED_PERMISSIONS:
                for spelling in (flag, flag + "=0", flag + "=1"):
                    definitions.append({"define": spelling})
                    try:
                        with self.subTest(target=target, define=spelling), self.assertRaisesRegex(ValueError, "fixture compile definitions differ"):
                            self.consume()
                    finally:
                        definitions.pop()


    def test_each_new_runtime_body_is_mandatory_not_a_same_count_substitution(self) -> None:
        sources = self.targets["xar_ck3_12002_runtime"]["sources"]
        self.indexed = dict(self.indexed)
        foreign = "src/ck3_121003_core_route26785313_v1.cpp"
        self.indexed[foreign] = builder.pin(NATIVE / foreign)
        for relative in self.ADDED_RUNTIME:
            position = next(i for i, row in enumerate(sources) if row["path"] == relative)
            original = sources.pop(position)
            try:
                with self.subTest(source=relative, mode="missing"), self.assertRaisesRegex(ValueError, "production TU counts differ"):
                    self.consume()
            finally:
                sources.insert(position, original)
            original["path"] = foreign
            try:
                with self.subTest(source=relative, mode="foreign replacement"), self.assertRaisesRegex(ValueError, "production source bodies differ"):
                    self.consume()
            finally:
                original["path"] = relative


    def test_original_closed_full111_fixture_links_remain_mandatory(self) -> None:
        for target, relative in (("xar_ck3_1210_identity_test", "src/ck3_121003_full111.cpp"), ("xar_ck3_1210_core_control_test", "src/ck3_121003_save_mapped111.cpp")):
            sources = self.targets[target]["sources"]
            position = next(i for i, row in enumerate(sources) if row["path"] == relative)
            removed = sources.pop(position)
            try:
                with self.subTest(target=target, source=relative), self.assertRaisesRegex(ValueError, "fixture source bodies differ"):
                    self.consume()
            finally:
                sources.insert(position, removed)


    def test_receipt_requires_actual_q41_before_and_two_explicit_off(self) -> None:
        self.assertEqual(self.consume_profile_receipt()["contract"]["contract_id"], self.CONTRACT_ID)
        expected = dict(self.contract["before_flags"], **dict.fromkeys(self.ADDITIONAL_FLAGS, "OFF"))
        for flag in self.NEW_FLAGS:
            for mode in ("on", "missing"):
                changed = dict(expected)
                if mode == "missing":
                    del changed[flag]
                else:
                    changed[flag] = "ON"
                with self.subTest(flag=flag, mode=mode), self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
                    self.consume_profile_receipt(actual_flags=changed)
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v17")
        self.assertEqual(len(prior["before_flags"]), 228)
        with self.assertRaisesRegex(ValueError, "prior profile differs"):
            self.consume_profile_receipt(old_flags=prior["before_flags"])
        v18 = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v18")
        unexecuted_v18 = dict(v18["before_flags"], **{k: v["after"] for k, v in v18["flag_changes"].items()})
        self.assertEqual(len(unexecuted_v18), 232)
        with self.assertRaisesRegex(ValueError, "prior profile differs"):
            self.consume_profile_receipt(old_flags=unexecuted_v18)
        changed = dict(expected)
        changed["XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1"] = "ON"
        with self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
            self.consume_profile_receipt(actual_flags=changed)
        changed = dict(expected)
        changed["XAR_CK3_UNREVIEWED_DJC_UI_OPTION"] = "OFF"
        with self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
            self.consume_profile_receipt(actual_flags=changed)
        with self.assertRaisesRegex(ValueError, "Unknown reviewed profile expansion contract"):
            builder.select_profile_expansion_contract(self.registry, self.CONTRACT_ID + "-unknown")

class FlorinClosedSelectedCostProfileConsumer(unittest.TestCase):
    """Actual Q42/233 baseline, one OFF option and two closed production bodies."""
    CONTRACT_ID = "ck3-1210-financial-markets-native-profile-v20"
    setUpClass = classmethod(FlorinClosedCoreRouteProfileConsumer.setUpClass.__func__)
    setUp = FlorinProfileContractConsumer.setUp
    target = FlorinProfileContractConsumer.target
    consume = FlorinProfileContractConsumer.consume
    source_defines = FlorinProfileContractConsumer.source_defines
    consume_profile_receipt = FlorinSixClosedOptionsProfileConsumer.consume_profile_receipt
    COST_FLAG = "XAR_CK3_ENABLE_121003_26785313_DJC_COST_V1"
    CLOSED_PERMISSIONS = FlorinClosedLetterProfileConsumer.CLOSED_PERMISSIONS + (COST_FLAG,)
    NEW_FLAGS = FlorinClosedLetterProfileConsumer.NEW_FLAGS + (COST_FLAG,)
    ADDED_RUNTIME = ("src/ck3_121003_djc_selected_cost26785313_raw_v1.cpp",
                     "src/ck3_121003_djc_selected_cost26785313_wire_v1.cpp")

    def test_actual_q42_233_adds_one_off_and_two_unconditional_bodies(self) -> None:
        import re
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v19")
        previous_after = dict(prior["before_flags"], **{k: v["after"] for k, v in prior["flag_changes"].items()})
        self.assertEqual(self.contract["before_flags"], previous_after)
        self.assertEqual(len(previous_after), 233)
        self.assertEqual(self.contract["flag_changes"], {self.COST_FLAG: {"before": None, "after": "OFF"}})
        self.assertEqual(len(dict(previous_after, **{self.COST_FLAG: "OFF"})), 234)
        cmake = (NATIVE / "cmake/current267_djc_selected_cost_v1.cmake").read_text(encoding="utf-8-sig")
        self.assertRegex(cmake, r"option\(" + self.COST_FLAG + r'\s+"[^"\n]*"\s+OFF\)')
        first_sources = cmake.split("target_sources(xar_ck3_12002_runtime PRIVATE", 1)[1].split(")", 1)[0]
        self.assertEqual(tuple(re.findall(r"src/[^\s\")]+\.cpp", first_sources)), self.ADDED_RUNTIME)
        self.assertLess(cmake.index("target_sources(xar_ck3_12002_runtime"), cmake.index(" if(" + self.COST_FLAG + ")"))
        self.assertEqual(self.contract["production_TUs"], {"xar_ck3_bridge": 268, "xar_ck3_12002_runtime": 578, "xar_bridge_protocol": 1})
        self.assertEqual(self.contract["production_source_lists"]["xar_ck3_12002_runtime"],
                         prior["production_source_lists"]["xar_ck3_12002_runtime"] + list(self.ADDED_RUNTIME))
        for name in ("xar_ck3_bridge", "xar_bridge_protocol"):
            self.assertEqual(self.contract["production_source_lists"][name], prior["production_source_lists"][name])
        for key in ("fixture_sources", "fixture_included_bodies"):
            self.assertEqual(self.contract[key], prior[key])
        self.assertEqual(len(self.fixtures), 22)
        for kind in ("off", "wire"):
            self.assertNotIn("xar_ck3_current_djc_selected_cost_" + kind + "_test", self.contract["fixture_sources"])
        self.assertEqual(builder.select_profile_expansion_contract(self.registry)["contract_id"], "ck3-12004-five-gate-native-profile-v1")
        self.consume()

    def test_cost_permission_is_absent_not_defined_zero_on_selected_sources(self) -> None:
        selections = [("xar_ck3_12002_runtime", path) for path in self.ADDED_RUNTIME]
        selections += [("xar_ck3_12002_runtime", "src/ck3_121003_djc_declaration_ui26785313_owner_v1.cpp"),
                       ("xar_ck3_12002_runtime", "src/ck3_121003_djc_declaration_ui26785313_dispatch_v1.cpp"),
                       ("xar_ck3_bridge", "src/bridge.cpp"), ("xar_ck3_bridge", "src/game_adapter.cpp")]
        for target, relative in selections:
            definitions = self.source_defines(target, relative)
            for spelling in (self.COST_FLAG, self.COST_FLAG + "=0", self.COST_FLAG + "=1"):
                self.assertNotIn({"define": spelling}, definitions)
                definitions.append({"define": spelling})
                try:
                    with self.subTest(target=target, source=relative, spelling=spelling), self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
                        self.consume()
                finally:
                    definitions.pop()

    test_existing_cmake_literal_zero_remains_required = FlorinClosedLetterProfileConsumer.test_existing_cmake_literal_zero_remains_required
    test_all_closed_permissions_remain_absent_in_old_fixtures = FlorinClosedLetterProfileConsumer.test_sixteen_permissions_stay_closed_in_identity_and_toast_fixtures
    test_new_bodies_cannot_be_omitted_or_replaced = FlorinClosedLetterProfileConsumer.test_each_new_runtime_body_is_mandatory_not_a_same_count_substitution
    test_original_closed_full111_fixture_links_remain_mandatory = FlorinClosedLetterProfileConsumer.test_original_closed_full111_fixture_links_remain_mandatory

    def test_receipt_requires_exact_q42_before_and_one_explicit_off(self) -> None:
        self.assertEqual(self.consume_profile_receipt()["contract"]["contract_id"], self.CONTRACT_ID)
        expected = dict(self.contract["before_flags"], **{self.COST_FLAG: "OFF"})
        for mode in ("on", "missing"):
            flags = dict(expected)
            if mode == "on":
                flags[self.COST_FLAG] = "ON"
            else:
                del flags[self.COST_FLAG]
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
                self.consume_profile_receipt(actual_flags=flags)
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v19")
        with self.assertRaisesRegex(ValueError, "prior profile differs"):
            self.consume_profile_receipt(old_flags=prior["before_flags"])
        for flag in (FlorinClosedLetterProfileConsumer.DJC_UI_FLAG, "XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1", "XAR_CK3_UNREVIEWED_COST_OPTION"):
            flags = dict(expected)
            flags[flag] = "ON"
            with self.subTest(flag=flag), self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
                self.consume_profile_receipt(actual_flags=flags)
        with self.assertRaisesRegex(ValueError, "Unknown reviewed profile expansion contract"):
            builder.select_profile_expansion_contract(self.registry, self.CONTRACT_ID + "-unknown")


class FlorinClosedLetterSetProfileConsumer(unittest.TestCase):
    """Actual Q43/234 baseline, one OFF option and three closed production bodies."""
    CONTRACT_ID = "ck3-1210-financial-markets-native-profile-v21"
    setUpClass = classmethod(FlorinClosedCoreRouteProfileConsumer.setUpClass.__func__)
    setUp = FlorinProfileContractConsumer.setUp
    target = FlorinProfileContractConsumer.target
    consume = FlorinProfileContractConsumer.consume
    source_defines = FlorinProfileContractConsumer.source_defines
    consume_profile_receipt = FlorinSixClosedOptionsProfileConsumer.consume_profile_receipt
    LETTER_SET_FLAG = "XAR_CK3_ENABLE_121003_26785313_LETTER_SET_V1"
    CLOSED_PERMISSIONS = FlorinClosedSelectedCostProfileConsumer.CLOSED_PERMISSIONS + (LETTER_SET_FLAG,)
    NEW_FLAGS = FlorinClosedSelectedCostProfileConsumer.NEW_FLAGS + (LETTER_SET_FLAG,)
    ADDED_RUNTIME = ('src/ck3_121003_letter_set26785313_raw_v1.cpp', 'src/ck3_121003_letter_set26785313_wire_v1.cpp', 'src/ck3_121003_letter_set26785313_dispatch_v1.cpp')

    def test_actual_q43_234_adds_one_off_and_three_unconditional_bodies(self) -> None:
        import re
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v20")
        previous_after = dict(prior["before_flags"], **{k: v["after"] for k, v in prior["flag_changes"].items()})
        self.assertEqual(self.contract["before_flags"], previous_after)
        self.assertEqual(len(previous_after), 234)
        self.assertEqual(self.contract["flag_changes"], {self.LETTER_SET_FLAG: {"before": None, "after": "OFF"}})
        self.assertEqual(len(dict(previous_after, **{self.LETTER_SET_FLAG: "OFF"})), 235)
        cmake = (NATIVE / "cmake/current267_letter_set_v1.cmake").read_text(encoding="utf-8-sig")
        self.assertRegex(cmake, r"option\(" + self.LETTER_SET_FLAG + r'\s+"[^"\n]*"\s+OFF\)')
        declaration = cmake.split("set(_xar_letter_set_new ", 1)[1].split(")", 1)[0]
        self.assertEqual(tuple(re.findall(r"src/[^\s)]+\.cpp", declaration)), self.ADDED_RUNTIME)
        self.assertIn("foreach(_xar_unit IN LISTS _xar_letter_set_new)", cmake)
        self.assertIn("if(NOT XAR_CK3_ENABLE_121003_26785313_LETTER_V1)", cmake)
        self.assertLess(cmake.index("target_sources(xar_ck3_12002_runtime"), cmake.index(" if(" + self.LETTER_SET_FLAG + ")"))
        self.assertEqual(self.contract["production_TUs"], {"xar_ck3_bridge": 268, "xar_ck3_12002_runtime": 581, "xar_bridge_protocol": 1})
        self.assertEqual(self.contract["production_source_lists"]["xar_ck3_12002_runtime"],
                         prior["production_source_lists"]["xar_ck3_12002_runtime"] + list(self.ADDED_RUNTIME))
        for name in ("xar_ck3_bridge", "xar_bridge_protocol"):
            self.assertEqual(self.contract["production_source_lists"][name], prior["production_source_lists"][name])
        for key in ("fixture_sources", "fixture_included_bodies"):
            self.assertEqual(self.contract[key], prior[key])
        self.assertEqual(len(self.fixtures), 22)
        for kind in ("off", "wire"):
            self.assertNotIn("xar_ck3_current_letter_set_" + kind + "_test", self.contract["fixture_sources"])
        self.assertEqual(builder.select_profile_expansion_contract(self.registry)["contract_id"], "ck3-12004-five-gate-native-profile-v1")
        self.consume()

    def test_letter_set_permission_is_absent_not_defined_zero_on_selected_sources(self) -> None:
        selections = [("xar_ck3_12002_runtime", path) for path in self.ADDED_RUNTIME]
        selections += [("xar_ck3_12002_runtime", "src/ck3_121003_letter26785313_owner_v1.cpp"),
                       ("xar_ck3_12002_runtime", "src/ck3_121003_letter26785313_dispatch_v1.cpp"),
                       ("xar_ck3_bridge", "src/bridge.cpp"), ("xar_ck3_bridge", "src/game_adapter.cpp")]
        for target, relative in selections:
            definitions = self.source_defines(target, relative)
            for spelling in (self.LETTER_SET_FLAG, self.LETTER_SET_FLAG + "=0", self.LETTER_SET_FLAG + "=1"):
                self.assertNotIn({"define": spelling}, definitions)
                definitions.append({"define": spelling})
                try:
                    with self.subTest(target=target, source=relative, spelling=spelling), self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
                        self.consume()
                finally:
                    definitions.pop()

    test_existing_cmake_literal_zero_remains_required = FlorinClosedLetterProfileConsumer.test_existing_cmake_literal_zero_remains_required
    test_all_closed_permissions_remain_absent_in_old_fixtures = FlorinClosedLetterProfileConsumer.test_sixteen_permissions_stay_closed_in_identity_and_toast_fixtures
    test_new_bodies_cannot_be_omitted_or_replaced = FlorinClosedLetterProfileConsumer.test_each_new_runtime_body_is_mandatory_not_a_same_count_substitution
    test_original_closed_full111_fixture_links_remain_mandatory = FlorinClosedLetterProfileConsumer.test_original_closed_full111_fixture_links_remain_mandatory

    def test_receipt_requires_exact_q43_before_and_one_explicit_off(self) -> None:
        self.assertEqual(self.consume_profile_receipt()["contract"]["contract_id"], self.CONTRACT_ID)
        expected = dict(self.contract["before_flags"], **{self.LETTER_SET_FLAG: "OFF"})
        for mode in ("on", "missing"):
            flags = dict(expected)
            if mode == "on":
                flags[self.LETTER_SET_FLAG] = "ON"
            else:
                del flags[self.LETTER_SET_FLAG]
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
                self.consume_profile_receipt(actual_flags=flags)
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v20")
        with self.assertRaisesRegex(ValueError, "prior profile differs"):
            self.consume_profile_receipt(old_flags=prior["before_flags"])
        for flag in (FlorinClosedLetterProfileConsumer.DJC_UI_FLAG, "XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1", "XAR_CK3_UNREVIEWED_LETTER_SET_OPTION"):
            flags = dict(expected)
            flags[flag] = "ON"
            with self.subTest(flag=flag), self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
                self.consume_profile_receipt(actual_flags=flags)
        with self.assertRaisesRegex(ValueError, "Unknown reviewed profile expansion contract"):
            builder.select_profile_expansion_contract(self.registry, self.CONTRACT_ID + "-unknown")

class FlorinClosedFullscreenProfileConsumer(unittest.TestCase):
    """Actual Q44/235 baseline, one OFF option and four closed production bodies."""
    CONTRACT_ID = "ck3-1210-financial-markets-native-profile-v22"
    setUpClass = classmethod(FlorinClosedCoreRouteProfileConsumer.setUpClass.__func__)
    setUp = FlorinProfileContractConsumer.setUp
    target = FlorinProfileContractConsumer.target
    consume = FlorinProfileContractConsumer.consume
    source_defines = FlorinProfileContractConsumer.source_defines
    consume_profile_receipt = FlorinSixClosedOptionsProfileConsumer.consume_profile_receipt
    FULLSCREEN_FLAG = "XAR_CK3_ENABLE_121003_26785313_FULLSCREEN_EVENT_V1"
    CLOSED_PERMISSIONS = FlorinClosedLetterSetProfileConsumer.CLOSED_PERMISSIONS + (FULLSCREEN_FLAG,)
    NEW_FLAGS = FlorinClosedLetterSetProfileConsumer.NEW_FLAGS + (FULLSCREEN_FLAG,)
    ADDED_RUNTIME = ('src/ck3_121003_fullscreen_event26785313_raw_v1.cpp', 'src/ck3_121003_fullscreen_event26785313_owner_v1.cpp', 'src/ck3_121003_fullscreen_event26785313_wire_v1.cpp', 'src/ck3_121003_fullscreen_event26785313_dispatch_v1.cpp')

    def test_actual_q44_235_adds_one_off_and_four_unconditional_bodies(self) -> None:
        import re
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v21")
        previous_after = dict(prior["before_flags"], **{k: v["after"] for k, v in prior["flag_changes"].items()})
        self.assertEqual(self.contract["before_flags"], previous_after)
        self.assertEqual(len(previous_after), 235)
        self.assertEqual(self.contract["flag_changes"], {self.FULLSCREEN_FLAG: {"before": None, "after": "OFF"}})
        self.assertEqual(len(dict(previous_after, **{self.FULLSCREEN_FLAG: "OFF"})), 236)
        cmake = (NATIVE / "cmake/current267_fullscreen_event_v1.cmake").read_text(encoding="utf-8-sig")
        self.assertRegex(cmake, r"option\(" + self.FULLSCREEN_FLAG + r'\s+"[^"\n]*"\s+OFF\)')
        declaration = cmake.split("set(_xar_fullscreen_new ", 1)[1].split(")", 1)[0]
        self.assertEqual(tuple(re.findall(r"src/[^\s)]+\.cpp", declaration)), self.ADDED_RUNTIME)
        self.assertIn("foreach(_xar_unit IN LISTS _xar_fullscreen_new)", cmake)
        self.assertIn("if(NOT XAR_CK3_ENABLE_121003_26785313_LETTER_V1)", cmake)
        self.assertLess(cmake.index("target_sources(xar_ck3_12002_runtime"), cmake.index(" if(" + self.FULLSCREEN_FLAG + ")"))
        self.assertEqual(self.contract["production_TUs"], {"xar_ck3_bridge": 268, "xar_ck3_12002_runtime": 585, "xar_bridge_protocol": 1})
        self.assertEqual(self.contract["production_source_lists"]["xar_ck3_12002_runtime"],
                         prior["production_source_lists"]["xar_ck3_12002_runtime"] + list(self.ADDED_RUNTIME))
        for name in ("xar_ck3_bridge", "xar_bridge_protocol"):
            self.assertEqual(self.contract["production_source_lists"][name], prior["production_source_lists"][name])
        for key in ("fixture_sources", "fixture_included_bodies"):
            self.assertEqual(self.contract[key], prior[key])
        self.assertEqual(len(self.fixtures), 22)
        for target in ("xar_ck3_current_fullscreen_off_test", "xar_ck3_current_fullscreen_event_wire_test"):
            self.assertNotIn(target, self.contract["fixture_sources"])
        self.assertEqual(builder.select_profile_expansion_contract(self.registry)["contract_id"], "ck3-12004-five-gate-native-profile-v1")
        self.consume()

    def test_fullscreen_permission_is_absent_not_defined_zero_on_selected_sources(self) -> None:
        selections = [("xar_ck3_12002_runtime", path) for path in self.ADDED_RUNTIME]
        # READONLY is OFF: this body is not a selected production TU at all.
        self.assertNotIn("src/ck3_121003_readonly26785313_v1.cpp",
                         self.contract["production_source_lists"]["xar_ck3_12002_runtime"])
        selections += [("xar_ck3_12002_runtime", "src/ck3_121003_date_advance26785313_v1.cpp"),
                       ("xar_ck3_bridge", "src/bridge.cpp"), ("xar_ck3_bridge", "src/game_adapter.cpp")]
        for target, relative in selections:
            definitions = self.source_defines(target, relative)
            for spelling in (self.FULLSCREEN_FLAG, self.FULLSCREEN_FLAG + "=0", self.FULLSCREEN_FLAG + "=1"):
                self.assertNotIn({"define": spelling}, definitions)
                definitions.append({"define": spelling})
                try:
                    with self.subTest(target=target, source=relative, spelling=spelling), self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
                        self.consume()
                finally:
                    definitions.pop()

    test_existing_cmake_literal_zero_remains_required = FlorinClosedLetterProfileConsumer.test_existing_cmake_literal_zero_remains_required
    test_all_closed_permissions_remain_absent_in_old_fixtures = FlorinClosedLetterProfileConsumer.test_sixteen_permissions_stay_closed_in_identity_and_toast_fixtures
    test_new_bodies_cannot_be_omitted_or_replaced = FlorinClosedLetterProfileConsumer.test_each_new_runtime_body_is_mandatory_not_a_same_count_substitution
    test_original_closed_full111_fixture_links_remain_mandatory = FlorinClosedLetterProfileConsumer.test_original_closed_full111_fixture_links_remain_mandatory

    def test_receipt_requires_exact_q44_before_and_one_explicit_off(self) -> None:
        self.assertEqual(self.consume_profile_receipt()["contract"]["contract_id"], self.CONTRACT_ID)
        expected = dict(self.contract["before_flags"], **{self.FULLSCREEN_FLAG: "OFF"})
        for mode in ("on", "missing"):
            flags = dict(expected)
            if mode == "on":
                flags[self.FULLSCREEN_FLAG] = "ON"
            else:
                del flags[self.FULLSCREEN_FLAG]
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
                self.consume_profile_receipt(actual_flags=flags)
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v21")
        with self.assertRaisesRegex(ValueError, "prior profile differs"):
            self.consume_profile_receipt(old_flags=prior["before_flags"])
        for flag in (FlorinClosedLetterProfileConsumer.DJC_UI_FLAG, "XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1", "XAR_CK3_UNREVIEWED_FULLSCREEN_OPTION"):
            flags = dict(expected)
            flags[flag] = "ON"
            with self.subTest(flag=flag), self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
                self.consume_profile_receipt(actual_flags=flags)
        with self.assertRaisesRegex(ValueError, "Unknown reviewed profile expansion contract"):
            builder.select_profile_expansion_contract(self.registry, self.CONTRACT_ID + "-unknown")

class FlorinClosedCuratedAndXqolProfileConsumer(unittest.TestCase):
    """Actual Q46/236 baseline; two OFF options and eight closed runtime bodies."""
    CONTRACT_ID = "ck3-1210-financial-markets-native-profile-v23"
    setUpClass = classmethod(FlorinClosedCoreRouteProfileConsumer.setUpClass.__func__)
    setUp = FlorinProfileContractConsumer.setUp
    target = FlorinProfileContractConsumer.target
    consume = FlorinProfileContractConsumer.consume
    source_defines = FlorinProfileContractConsumer.source_defines
    consume_profile_receipt = FlorinSixClosedOptionsProfileConsumer.consume_profile_receipt
    ADDITIONAL_FLAGS = (
        "XAR_CK3_ENABLE_121003_26785313_CURATED_DECISIONS_V1",
        "XAR_CK3_ENABLE_121003_26785313_XQOL_CONVERSION_PROMPT_V1",
    )
    CLOSED_PERMISSIONS = FlorinClosedFullscreenProfileConsumer.CLOSED_PERMISSIONS + ADDITIONAL_FLAGS
    NEW_FLAGS = FlorinClosedFullscreenProfileConsumer.NEW_FLAGS + ADDITIONAL_FLAGS
    ADDED_RUNTIME = (
        "src/ck3_121003_curated_decisions26785313_raw_v1.cpp",
        "src/ck3_121003_curated_decisions26785313_wire_v1.cpp",
        "src/ck3_121003_curated_decisions26785313_owner_v1.cpp",
        "src/ck3_121003_curated_decisions26785313_dispatch_v1.cpp",
        "src/ck3_121003_xqol_conversion_prompt26785313_raw_v1.cpp",
        "src/ck3_121003_xqol_conversion_prompt26785313_wire_v1.cpp",
        "src/ck3_121003_xqol_conversion_prompt26785313_owner_v1.cpp",
        "src/ck3_121003_xqol_conversion_prompt26785313_dispatch_v1.cpp",
    )

    def test_actual_q46_236_adds_only_two_off_and_eight_unconditional_bodies(self) -> None:
        import re
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v22")
        before = dict(prior["before_flags"], **{k: v["after"] for k, v in prior["flag_changes"].items()})
        self.assertEqual(self.contract["before_flags"], before)
        self.assertEqual(len(before), 236)
        self.assertEqual(self.contract["flag_changes"], {flag: {"before": None, "after": "OFF"} for flag in self.ADDITIONAL_FLAGS})
        self.assertTrue(all(flag not in before for flag in self.ADDITIONAL_FLAGS))
        self.assertEqual(len(dict(before, **dict.fromkeys(self.ADDITIONAL_FLAGS, "OFF"))), 238)
        modules = (("current267_curated_decisions_v1.cmake", "_xar_curated_new", self.ADDITIONAL_FLAGS[0], self.ADDED_RUNTIME[:4]),
                   ("current267_xqol_prompt_v1.cmake", "_xar_xqol_new", self.ADDITIONAL_FLAGS[1], self.ADDED_RUNTIME[4:]))
        cmake_root = (NATIVE / "CMakeLists.txt").read_text(encoding="utf-8-sig")
        self.assertLess(cmake_root.index("include(cmake/" + modules[0][0] + ")"),
                        cmake_root.index("include(cmake/" + modules[1][0] + ")"))
        for name, variable, flag, bodies in modules:
            cmake = (NATIVE / "cmake" / name).read_text(encoding="utf-8-sig")
            self.assertRegex(cmake, r"option\(" + flag + r'\s+"[^"\n]*"\s+OFF\)')
            declaration = cmake.split("set(" + variable + " ", 1)[1].split(")", 1)[0]
            self.assertEqual(tuple(re.findall(r"src/[^\s)]+\.cpp", declaration)), bodies)
            self.assertIn("foreach(_xar_unit IN LISTS " + variable + ")", cmake)
            self.assertLess(cmake.index("target_sources(xar_ck3_12002_runtime"), cmake.index(" if(" + flag + ")"))
        self.assertEqual(self.contract["production_TUs"], {"xar_ck3_bridge": 268, "xar_ck3_12002_runtime": 593, "xar_bridge_protocol": 1})
        self.assertEqual(self.contract["production_source_lists"]["xar_ck3_12002_runtime"],
                         prior["production_source_lists"]["xar_ck3_12002_runtime"] + list(self.ADDED_RUNTIME))
        for target in ("xar_ck3_bridge", "xar_bridge_protocol"):
            self.assertEqual(self.contract["production_source_lists"][target], prior["production_source_lists"][target])
        for key in ("fixture_sources", "fixture_included_bodies"):
            self.assertEqual(self.contract[key], prior[key])
        self.assertEqual(len(self.fixtures), 22)
        for target in ("xar_ck3_current_curated_decisions_off_test", "xar_ck3_current_curated_decisions_wire_test",
                       "xar_ck3_current_xqol_conversion_prompt_off_test", "xar_ck3_current_xqol_prompt_wire_test"):
            self.assertNotIn(target, self.contract["fixture_sources"])
        self.assertEqual(builder.select_profile_expansion_contract(self.registry)["contract_id"], "ck3-12004-five-gate-native-profile-v1")
        self.consume()

    def test_both_new_permissions_are_absent_even_literal_zero_in_production_and_all_formal_fixtures(self) -> None:
        selections = [("xar_ck3_12002_runtime", path) for path in self.ADDED_RUNTIME]
        self.assertNotIn("src/ck3_121003_readonly26785313_v1.cpp", self.contract["production_source_lists"]["xar_ck3_12002_runtime"])
        selections += [("xar_ck3_bridge", "src/bridge.cpp"), ("xar_ck3_bridge", "src/game_adapter.cpp")]
        for target, relative in selections:
            definitions = self.source_defines(target, relative)
            for flag in self.ADDITIONAL_FLAGS:
                for spelling in (flag, flag + "=0", flag + "=1"):
                    self.assertNotIn({"define": spelling}, definitions)
                    definitions.append({"define": spelling})
                    try:
                        with self.subTest(target=target, source=relative, spelling=spelling), self.assertRaisesRegex(ValueError, "per-TU present/absent macros differ"):
                            self.consume()
                    finally:
                        definitions.pop()
        for target, paths in self.contract["fixture_sources"].items():
            definitions = self.source_defines(target, paths[0])
            for flag in self.ADDITIONAL_FLAGS:
                for spelling in (flag, flag + "=0", flag + "=1"):
                    definitions.append({"define": spelling})
                    try:
                        with self.subTest(target=target, spelling=spelling), self.assertRaisesRegex(ValueError, "fixture compile definitions differ"):
                            self.consume()
                    finally:
                        definitions.pop()

    test_existing_cmake_literal_zero_remains_required = FlorinClosedLetterProfileConsumer.test_existing_cmake_literal_zero_remains_required
    test_all_closed_permissions_remain_absent_in_old_fixtures = FlorinClosedLetterProfileConsumer.test_sixteen_permissions_stay_closed_in_identity_and_toast_fixtures
    test_new_bodies_cannot_be_omitted_or_replaced = FlorinClosedLetterProfileConsumer.test_each_new_runtime_body_is_mandatory_not_a_same_count_substitution
    test_original_closed_full111_fixture_links_remain_mandatory = FlorinClosedLetterProfileConsumer.test_original_closed_full111_fixture_links_remain_mandatory

    def test_receipt_requires_actual_q46_before_and_two_explicit_off(self) -> None:
        self.assertEqual(self.consume_profile_receipt()["contract"]["contract_id"], self.CONTRACT_ID)
        expected = dict(self.contract["before_flags"], **dict.fromkeys(self.ADDITIONAL_FLAGS, "OFF"))
        for flag in self.ADDITIONAL_FLAGS:
            for mode in ("on", "missing"):
                flags = dict(expected)
                if mode == "on":
                    flags[flag] = "ON"
                else:
                    del flags[flag]
                with self.subTest(flag=flag, mode=mode), self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
                    self.consume_profile_receipt(actual_flags=flags)
        prior = builder.select_profile_expansion_contract(self.registry, "ck3-1210-financial-markets-native-profile-v22")
        with self.assertRaisesRegex(ValueError, "prior profile differs"):
            self.consume_profile_receipt(old_flags=prior["before_flags"])
        for flag in (FlorinClosedFullscreenProfileConsumer.FULLSCREEN_FLAG, "XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1", "XAR_CK3_UNREVIEWED_CURATED_OPTION"):
            flags = dict(expected)
            flags[flag] = "ON"
            with self.subTest(flag=flag), self.assertRaisesRegex(ValueError, "outside the reviewed exact delta"):
                self.consume_profile_receipt(actual_flags=flags)
        with self.assertRaisesRegex(ValueError, "Unknown reviewed profile expansion contract"):
            builder.select_profile_expansion_contract(self.registry, self.CONTRACT_ID + "-unknown")


if __name__ == "__main__":
    unittest.main()
