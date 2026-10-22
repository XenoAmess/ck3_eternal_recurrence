"""Authored prepared packets enter the real public Selection and adapter checks.

Runtime files are the existing offline shared fixture, not CK3 qualification.
Real installed-source prepare/plan/preflight runs are retained separately.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from typing import Protocol, runtime_checkable

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parents[1]
for directory in (REPO / "tools", REPO / "ck3_autonomous_player/src", TOOLS):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from acceptance_contract import Object, array, field, integer, mapping, object_value, pin, read, text, write_once
from ck3_mod_acceptance import Selection
import test_ck3_mod_acceptance as shared_entry_fixture
import cold_persistence_acceptance_adapter as cold
import curse_representative_acceptance_adapter as curse
import suppression_timer_acceptance_adapter as timer


@runtime_checkable
class FixtureLifecycle(Protocol):
    def setUp(self) -> None: ...
    def doCleanups(self) -> bool: ...


@runtime_checkable
class AuthoredRuntime(FixtureLifecycle, Protocol):
    root: Path
    runtime: object
    manifest: object
    manifest_path: Path
    runtime_path: Path
    products_path: Path
    files: object

@runtime_checkable
class PublicConsumer(Protocol):
    def adapter_context(self) -> object: ...
    def preflight(self) -> object: ...


def authored_path(value: object) -> Path:
    if not isinstance(value, Path):
        raise AssertionError("Existing authored fixture path missing")
    return value


class PreparedContractConsumers(unittest.TestCase):
    def test_actual_selection_applies_prepared_startup_and_plan_before_all_three_adapters(self) -> None:
        for adapter in (timer, curse, cold):
            with self.subTest(case=adapter.CASE):
                fixture: object = shared_entry_fixture.SharedEntryTests()
                if not isinstance(fixture, FixtureLifecycle):
                    raise AssertionError("Existing authored runtime fixture unavailable")
                fixture.setUp()
                self.addCleanup(fixture.doCleanups)
                if not isinstance(fixture, AuthoredRuntime):
                    raise AssertionError("Existing authored runtime fields unavailable")
                runtime = mapping(fixture.runtime, "authored runtime")
                runtime["repo_root"] = str(REPO)
                fixture.runtime_path.write_text(json.dumps(runtime), encoding="utf-8")
                products = read(REPO / "tools/ck3_mod_acceptance_products.json")
                fixture.products_path.write_text(json.dumps(products), encoding="utf-8")
                product = field(field(products, "products"), "living-artifacts")
                original = next(row for row in array(field(product, "cases"), "registered cases") if field(row, "id") == adapter.CASE)
                state = fixture.root / "authored-prepared-state"
                policy = fixture.root / "authored-fixture-policy.json"
                policy.write_text("{}", encoding="utf-8")
                startup: Object = {"mode": "fixture", "state_dir": str(state), "fixture_start_policy": str(policy)}
                files = mapping(fixture.files, "authored shared files")
                if adapter.CASE == cold.CASE:
                    source = pin(authored_path(files["save"]))
                    startup = object_value({"mode": "saved_campaign", "state_dir": str(state), "saved_campaign": {
                        "save": source["path"], "bytes": source["bytes"], "sha256": source["sha256"], "player_id": 91,
                        "date_raw": 123456, "product_inventory": str(files["inventory"])}})
                # JSON packet is authored, but its startup/plan application and
                # the preflight adapter invocation are the production consumer.
                prepared = {"schema": "ck3-mod-acceptance-prepared-case-v1", "product": "living-artifacts", "case": adapter.CASE,
                    "runtime_manifest": pin(fixture.manifest_path), "case_inputs": {}, "startup": startup,
                    "initial_plan": pin(authored_path(files["initial"])),
                    "adapter": pin(TOOLS / (adapter.__name__ + ".py")), "contract": pin(TOOLS / adapter.CONTRACT_NAME)}
                packet = write_once(fixture.root / "authored-prepared-case.json", prepared)
                selected: object = Selection(fixture.runtime_path, fixture.products_path, "living-artifacts", adapter.CASE,
                    prepared_path=Path(packet["path"]))
                if not isinstance(selected, PublicConsumer):
                    raise AssertionError("Actual public prepared consumer unavailable")
                context = object_value(selected.adapter_context())
                actual_spec = field(context, "case_spec")
                self.assertNotEqual(field(actual_spec, "startup"), field(original, "startup"))
                self.assertEqual(field(actual_spec, "startup"), startup)
                adapter.validate_contract(json.loads(json.dumps(context)))
                blockers = array(field(selected.preflight(), "blockers"), "authored preflight blockers")
                self.assertFalse(any(text(value, "blocker").startswith("Case adapter:") for value in blockers), blockers)
                for spec in ({**mapping(actual_spec, "case"), "id": "wrong"},
                             {key: value for key, value in mapping(actual_spec, "case").items() if key != "required_mcp_tools"},
                             {**mapping(actual_spec, "case"), "required_mcp_tools": [False]},
                             {**mapping(actual_spec, "case"), "opt_in_read_only_mcp_tools": []}):
                    with self.assertRaises(ValueError):
                        adapter.validate_contract({**context, "case_spec": spec})
                config = mapping(field(context, "case_contract"), "case contract")
                for changed in ({**config, "schema_version": True},
                                {**config, "maximum_checkpoints": float(integer(config["maximum_checkpoints"], "Save cap", 1))},
                                {key: value for key, value in config.items() if key != "schema_version"}, {**config, "unexpected": None}):
                    with self.assertRaises(ValueError):
                        adapter.validate_contract({**context, "case_contract": changed})

    def test_curse_declares_default_registered_root_without_an_unsupported_optional_flag(self) -> None:
        standalone = read(TOOLS / "curse_representative.registry_stanza.json")
        products = read(REPO / "tools/ck3_mod_acceptance_products.json")
        cases = array(field(field(field(products, "products"), "living-artifacts"), "cases"), "public cases")
        registered = next(row for row in cases if field(row, "id") == curse.CASE)
        self.assertEqual(standalone, registered)
        self.assertIn("ck3_query_campaign_root_context_v1", array(field(registered, "required_mcp_tools"), "required"))
        self.assertNotIn("ck3_query_campaign_root_context_v1", array(field(registered, "opt_in_read_only_mcp_tools"), "optional read-only"))
        with self.assertRaises(ValueError):
            curse.validate_contract({"product": "living-artifacts", "case": curse.CASE, "case_contract": read(TOOLS / curse.CONTRACT_NAME),
                "case_spec": {**mapping(registered, "registered case"), "required_mcp_tools": [
                    tool for tool in array(field(registered, "required_mcp_tools"), "tools") if tool != "ck3_query_campaign_root_context_v1"]}})

    def test_cold_preparation_uses_selected_frozen_helper_and_sdk_in_a_fresh_process(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shared = root / "selected-runtime"
            for relative in ("tools/ck3_mod_acceptance_saved_profile_v2.py", "ck3_autonomous_player/src/xar_autoplayer/__init__.py",
                             "ck3_autonomous_player/src/xar_autoplayer/saved_campaign_profile_inventory_v2.py"):
                destination = shared / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(REPO / relative, destination)
            product = root / "authored-formal-product"
            (product / "common/on_action").mkdir(parents=True)
            (product / "descriptor.mod").write_text('name="Authored formal copy"\n', encoding="utf-8")
            (product / "common/on_action/bootstrap.txt").write_text("on_game_start_after_lobby = { }\n", encoding="utf-8")
            plain = {}
            for index, name in enumerate(("pdx_settings.txt", "tutorial.txt", "presets.txt", "player/game_rules/presets.txt")):
                source = root / f"plain-{index}.txt"
                source.write_text("authored configuration", encoding="utf-8")
                plain[name] = pin(source)
            inputs = write_once(root / "inputs.json", {"shared": str(shared), "product": str(product), "plain": plain})
            script = root / "verify-selected-source.py"
            script.write_text('''from pathlib import Path
import inspect,json,os,sys
root=Path(sys.argv[1])
value=json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
repo=Path(sys.argv[3])
sys.path[:0]=[str(repo/"tools"),str(repo/"mod_living_artifacts/tools")]
from ck3_mod_acceptance import _case_sdk_imports_v1
shared=Path(value["shared"])
sdk=shared/"ck3_autonomous_player/src"
with _case_sdk_imports_v1(shared,{"PYTHONPATH":str(sdk)}):
 import xar_autoplayer
 import cold_persistence_acceptance_adapter as cold
 context={"shared_source_root":str(shared),"state_dir":str(root/"state"),"output":str(root/"output"),
  "_selected_engine":(object(),{"game_version":"authored","exe_sha256":"a"*64})}
 profile=cold.selected_saved_preparation(context).materialize_saved_profile_v2(context,Path(value["product"]),value["plain"],source_role="formal_product")
 from xar_autoplayer.saved_campaign_profile_inventory_v2 import Inventory,parse_inventory,verify_inventory
 assert Path(inspect.getfile(Inventory)).resolve()==(sdk/"xar_autoplayer/saved_campaign_profile_inventory_v2.py").resolve()
 prepared=Path(profile["profile"])
 inventory=parse_inventory(json.loads(Path(profile["product_inventory"]["path"]).read_text(encoding="utf-8")))
 verify_inventory(inventory,profile=prepared,actual_enabled_mods=["mod/product.mod"])
 assert profile["runtime_status"]=="NOT_RUN" and profile["fixture_mounted"] is False
 print("ACTUAL_SELECTED_V2_PRODUCER_AND_CONSUMER_OK; NO_CK3")
''', encoding="utf-8")
            environment = dict(os.environ)
            environment.pop("PYTHONPATH", None)
            completed = subprocess.run([sys.executable, "-B", "-X", "utf8", str(script), str(root), inputs["path"], str(REPO)],
                cwd=root, env=environment, capture_output=True, text=True, encoding="utf-8", check=False, timeout=60)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertIn("ACTUAL_SELECTED_V2_PRODUCER_AND_CONSUMER_OK", completed.stdout)


if __name__ == "__main__":
    unittest.main()
