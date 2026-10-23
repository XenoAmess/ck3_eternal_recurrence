"""Select one shared CK3 runtime, inspect a product case, or launch its frozen host.

This entry delegates Steam review, keeper custody, launch and normal cleanup to
the existing reviewed launcher and shared host. Host exit is not product signoff.
"""
from __future__ import annotations

import argparse
import ast
from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager
import hashlib
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Literal, TypedDict
import re
import subprocess
import sys

from ck3_mod_acceptance_background_types import (
    FilePin, JsonObject, file_pin, json_object, keyed_file_pin, object_field, text_field,
    wire_evidence_codec, validate_host_running_date_projection,
)
if TYPE_CHECKING:
    from ck3_mod_acceptance_runtime_inputs import RuntimeInputSources


LEGACY_THRESHOLD_ADAPTER_V1 = (35832, "863dfea6abd897a8efe2159f75717108f6b4afd8677e01fa44a6cc48b8c3e2e3")
LEGACY_THRESHOLD_CONTRACT_V1 = (2769, "3a69f4c485894043b8b91dd900f89eef5f06249b48b0f9d2ebbbc2327705ab51")
LEGACY_THRESHOLD_CHECKS_V1 = (
    "THRESHOLD-AUTOMATIC-11", "THRESHOLD-CURSE-HUNGER-PROJECTION", "TRAIN-ACTUAL-XP-WALLET", "TRAIN-ACTUAL-STRESS",
    "SUPPRESS-ACTUAL-WALLET-90-DAY", "SUPPRESS-ACTUAL-STRESS", "SUPPRESS-EQUIPMENT-PERSISTENCE", "SUPPRESS-MONTHLY-PAUSE",
)


class LegacyThresholdGuiQualificationV1(TypedDict):
    """A new verification projection; never a replacement for the retained v1 file."""
    schema: Literal["ck3-mod-acceptance-legacy-threshold-gui-qualification-v1"]
    run_id: str
    machine_id: str
    producer_result_schema: Literal["living-artifacts-threshold-case-result-v1"]
    retained_result: FilePin
    producer_adapter: FilePin
    producer_contract: FilePin
    prepared_case: FilePin
    frozen_argv: FilePin
    runtime_manifest: FilePin
    normal_close: FilePin
    verification_consumer: FilePin
    reverified_check_ids: list[str]
    original_adapter_recomputed: Literal[True]
    gui_contract_qualified: Literal[True]
    original_result_modified: Literal[False]


def _verification_file_pin_v1(value: object) -> FilePin:
    row = json_object(value)
    if set(row) != {"path", "bytes", "sha256"}:
        raise ValueError("Closed verification file Pin required")
    result = file_pin(row)
    if result["bytes"] <= 0 or not Path(result["path"]).is_absolute():
        raise ValueError("Nonempty absolute verification source required")
    return result


def _verification_read_object_v1(path: Path) -> JsonObject:
    value: object = json.loads(path.read_bytes())
    return json_object(value)


def _verification_actual_pin_v1(path: Path) -> FilePin:
    resolved = path.resolve()
    if not resolved.is_file() or path.is_symlink():
        raise ValueError("Ordinary retained verification file required")
    raw = resolved.read_bytes()
    return _verification_file_pin_v1({"path": str(resolved), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})


def _verification_checked_pin_v1(path: Path, declared: object) -> FilePin:
    expected = _verification_file_pin_v1(declared)
    actual = _verification_actual_pin_v1(path)
    if Path(expected["path"]).resolve() != Path(actual["path"]) or actual["bytes"] != expected["bytes"] or actual["sha256"] != expected["sha256"]:
        raise ValueError("Retained verification source Pin differs")
    return actual


def parse_legacy_threshold_gui_qualification_v1(value: object) -> LegacyThresholdGuiQualificationV1:
    row = json_object(value)
    if (set(row) != set(LegacyThresholdGuiQualificationV1.__required_keys__)
            or row["schema"] != "ck3-mod-acceptance-legacy-threshold-gui-qualification-v1"
            or row["producer_result_schema"] != "living-artifacts-threshold-case-result-v1"
            or row["original_adapter_recomputed"] is not True or row["gui_contract_qualified"] is not True
            or row["original_result_modified"] is not False or row["reverified_check_ids"] != list(LEGACY_THRESHOLD_CHECKS_V1)):
        raise ValueError("Closed versioned legacy GUI qualification required")
    return LegacyThresholdGuiQualificationV1(
        schema="ck3-mod-acceptance-legacy-threshold-gui-qualification-v1",
        run_id=text_field(row, "run_id"), machine_id=text_field(row, "machine_id"),
        producer_result_schema="living-artifacts-threshold-case-result-v1",
        retained_result=_verification_file_pin_v1(row["retained_result"]),
        producer_adapter=_verification_file_pin_v1(row["producer_adapter"]),
        producer_contract=_verification_file_pin_v1(row["producer_contract"]),
        prepared_case=_verification_file_pin_v1(row["prepared_case"]), frozen_argv=_verification_file_pin_v1(row["frozen_argv"]),
        runtime_manifest=_verification_file_pin_v1(row["runtime_manifest"]), normal_close=_verification_file_pin_v1(row["normal_close"]),
        verification_consumer=_verification_file_pin_v1(row["verification_consumer"]),
        reverified_check_ids=list(LEGACY_THRESHOLD_CHECKS_V1), original_adapter_recomputed=True,
        gui_contract_qualified=True, original_result_modified=False,
    )


def _legacy_threshold_gui_qualification_v1(
    result: object, *, loaded_adapter_source: object, adapter_path: Path, contract_path: Path,
    prepared_path: Path | None, context_path: Path, runtime_path: Path, products_path: Path,
    manifest_path: Path, required_pins: list[tuple[Path, object]], expected_argv: object,
    expected_environment: object, normal_close_path: Path,
) -> LegacyThresholdGuiQualificationV1 | None:
    """Called only AFTER the selected original adapter's real retained verify.

    The exact known v1 producer already re-read all seven Save/melt/native/action
    sources and recomputed eight checks. This derives its missing scoped output;
    explicit GUI false, unknown sources and other cases retain the ordinary gate.
    """
    row = json_object(result)
    if (row.get("schema") != "living-artifacts-threshold-case-result-v1"
            or row.get("product") != "living-artifacts" or row.get("case") != "threshold_suppression"
            or "gui_contract_qualified" in row):
        return None
    if (row.get("status") != "PASS" or row.get("case_contract_qualified") is not True
            or row.get("original_action_unknown") is not False or row.get("error") is not None
            or row.get("business_pass") is not False or row.get("product_release_pass") is not False
            or type(row.get("actual_natural_days")) is not int or row["actual_natural_days"] != 47
            or type(row.get("actual_saved_observations")) is not int or row["actual_saved_observations"] != 7):
        return None
    if not normal_close_path.is_file() or _verification_read_object_v1(normal_close_path).get("normal_close_qualified") is not True:
        return None
    checks = row.get("checks")
    if (not isinstance(checks, list) or len(checks) != len(LEGACY_THRESHOLD_CHECKS_V1)
            or any(json_object(check).get("case_id") != identity or json_object(check).get("status") != "PASS"
                   for check, identity in zip(checks, LEGACY_THRESHOLD_CHECKS_V1, strict=True))):
        raise ValueError("Legacy GUI qualification requires all eight original recomputed checks")
    if prepared_path is None or not isinstance(loaded_adapter_source, str) or Path(loaded_adapter_source).resolve() != adapter_path.resolve():
        raise ValueError("Actual selected legacy adapter source required")
    context = _verification_read_object_v1(context_path)
    prepared_pin = _verification_checked_pin_v1(prepared_path, context.get("prepared_case"))
    prepared = _verification_read_object_v1(prepared_path)
    frozen_ref = _verification_file_pin_v1(context.get("frozen_argv"))
    frozen_pin = _verification_checked_pin_v1(Path(frozen_ref["path"]), frozen_ref)
    frozen = _verification_read_object_v1(Path(frozen_pin["path"]))
    runtime = _verification_read_object_v1(runtime_path)
    manifest_pin = _verification_checked_pin_v1(manifest_path, runtime.get("manifest"))
    manifest = _verification_read_object_v1(manifest_path)
    run_id = text_field(row, "run_id")
    run = Path(text_field(context, "run_dir")).resolve()
    if (context.get("run_id") != run_id or run.name != run_id or context_path.resolve().parent != run
            or context.get("product") != "living-artifacts" or context.get("case") != "threshold_suppression"
            or context.get("case_inputs") != prepared.get("case_inputs") or frozen.get("run_id") != run_id
            or frozen.get("argv") != expected_argv or frozen.get("runtime_environment", {}) != expected_environment
            or prepared.get("runtime_manifest") != manifest_pin or frozen.get("runtime_manifest") != manifest_pin
            or manifest.get("machine_id") != row.get("machine_id")
            or normal_close_path.resolve() != run / "case-output/normal-close-result.json"):
        raise ValueError("Legacy verification crossed original allocation/runtime/scope")
    files = object_field(frozen, "files")
    def frozen_file(path: Path) -> FilePin:
        resolved = path.resolve()
        return _verification_checked_pin_v1(resolved, keyed_file_pin(str(resolved), files.get(str(resolved))))
    for path in (runtime_path, products_path, prepared_path, manifest_path):
        frozen_file(path)
    for path, declared in required_pins:
        actual = frozen_file(path)
        expected = json_object(declared)
        if type(expected.get("bytes")) is not int or expected.get("bytes") != actual["bytes"] or expected.get("sha256") != actual["sha256"]:
            raise ValueError("Selected original source fingerprint differs")
    adapter = frozen_file(adapter_path)
    contract = frozen_file(contract_path)
    _verification_checked_pin_v1(adapter_path, prepared.get("adapter"))
    _verification_checked_pin_v1(contract_path, prepared.get("contract"))
    if (adapter["bytes"], adapter["sha256"]) != LEGACY_THRESHOLD_ADAPTER_V1 or (contract["bytes"], contract["sha256"]) != LEGACY_THRESHOLD_CONTRACT_V1:
        raise ValueError("Unsupported legacy threshold producer identity")
    result_path = run / "case-output/living-artifacts-threshold-result.json"
    if _verification_read_object_v1(result_path) != row:
        raise ValueError("Original adapter returned a different retained result")
    return parse_legacy_threshold_gui_qualification_v1({
        "schema": "ck3-mod-acceptance-legacy-threshold-gui-qualification-v1", "run_id": run_id,
        "machine_id": text_field(row, "machine_id"), "producer_result_schema": row["schema"],
        "retained_result": _verification_actual_pin_v1(result_path), "producer_adapter": adapter, "producer_contract": contract,
        "prepared_case": prepared_pin, "frozen_argv": frozen_pin, "runtime_manifest": manifest_pin,
        "normal_close": _verification_actual_pin_v1(normal_close_path), "verification_consumer": _verification_actual_pin_v1(Path(__file__)),
        "reverified_check_ids": list(LEGACY_THRESHOLD_CHECKS_V1), "original_adapter_recomputed": True,
        "gui_contract_qualified": True, "original_result_modified": False,
    })


def _case_loaded_sdk_sources_v1(package_root: Path) -> None:
    for name, module in tuple(sys.modules.items()):
        if name == "xar_autoplayer" or name.startswith("xar_autoplayer."):
            filename = getattr(module, "__file__", None)
            if not isinstance(filename, str) or not Path(filename).resolve().is_relative_to(package_root):
                raise ValueError("Public case SDK import escaped selected runtime: " + name)


@contextmanager
def _case_sdk_imports_v1(source_root: Path, environment: object) -> Iterator[Path | None]:
    """Keep lazy case imports in the same declared SDK as the host subprocess."""
    if not isinstance(environment, dict) or any(type(key) is not str for key in environment):
        raise ValueError("Selected runtime import environment must be an object")
    if "PYTHONPATH" not in environment:
        # Existing runtimes without a declared Python environment keep their
        # SDK-free case boundary; no SDK binding is asserted for them.
        yield None
        return
    value = environment["PYTHONPATH"]
    if not isinstance(value, str) or not value or any(not part for part in value.split(os.pathsep)):
        raise ValueError("Selected runtime PYTHONPATH must contain explicit paths")
    declared = tuple(Path(part).resolve() for part in value.split(os.pathsep))
    source = source_root.resolve()
    if (source / "ck3_autonomous_player/src/xar_autoplayer").is_dir():
        source = source / "ck3_autonomous_player/src"
    package = source / "xar_autoplayer"
    if not package.is_dir() or source not in declared:
        raise ValueError("Selected runtime PYTHONPATH does not bind its frozen SDK")
    _case_loaded_sdk_sources_v1(package)
    prior = list(sys.path)
    try:
        sys.path.insert(0, str(source))
        yield source
    finally:
        try:
            _case_loaded_sdk_sources_v1(package)
        finally:
            sys.path[:] = prior


RUNTIME_SCHEMA = "ck3-mod-acceptance-runtime-v1"
MANIFEST_SCHEMA = "ck3-mod-acceptance-shared-runtime-v1"
PRODUCTS_SCHEMA = "ck3-mod-acceptance-products-v1"
CONTEXT_SCHEMA = "ck3-mod-acceptance-run-context-v1"
MINIMUM_READINESS_SECONDS = 1800
BUDGET_FLAGS = {
    "command_timeout": "--command-timeout", "readiness_timeout": "--readiness-timeout",
    "timeout": "--timeout", "poll_interval": "--poll-interval", "hold_seconds": "--hold-seconds",
}


class OrdinaryGuiCampaignStartup(TypedDict):
    mode: Literal["ordinary_gui_campaign"]
    state_dir: str


def ordinary_gui_campaign_startup(value: object) -> OrdinaryGuiCampaignStartup:
    """An isolated formal product campaign has no fixture or saved-start inputs."""
    if not isinstance(value, dict) or set(value) != {"mode", "state_dir"}:
        raise ValueError("Ordinary GUI campaign startup accepts only mode and state_dir")
    state = value["state_dir"]
    if value["mode"] != "ordinary_gui_campaign" or not isinstance(state, str) or not state.strip():
        raise ValueError("Explicit ordinary GUI campaign mode and state_dir required")
    return {"mode": "ordinary_gui_campaign", "state_dir": state}


SAVED_FLAGS = {
    "save": "--saved-campaign-save", "bytes": "--saved-campaign-save-bytes",
    "sha256": "--saved-campaign-save-sha256", "player_id": "--saved-campaign-player-id",
    "date_raw": "--saved-campaign-date-raw", "product_inventory": "--saved-campaign-product-inventory",
}
CASE_HOLY_SITE_RELIC_ACTION_MCP_TOOLS = frozenset({'ck3_set_holy_site_relic_slot_selection_v1', 'ck3_select_holy_site_relic_artifact_v1', 'ck3_remove_holy_site_relic_v1', 'ck3_enshrine_holy_site_relic_v1'})
CASE_RITE_CREATION_ACTION_MCP_TOOLS = frozenset({
    "ck3_query_player_rite_creation_action_context_v1", "ck3_execute_player_rite_creation_action_v1",
    "ck3_collect_player_rite_creation_action_result_v1",
})
CASE_PLAYER_INVENTORY_WINDOW_OPEN_MCP_TOOLS = frozenset({
    "ck3_open_player_inventory_window_v1", "ck3_query_player_inventory_window_open_post_v1",
})
CASE_PLAYER_INVENTORY_WINDOW_CLOSE_MCP_TOOLS = frozenset({
    "ck3_query_player_inventory_window_close_v1", "ck3_close_player_inventory_window_v1",
    "ck3_query_player_inventory_window_close_post_v1",
})
CASE_PLAYER_ARTIFACT_PERSONAL_USE_ACTION_MCP_TOOLS = frozenset({
    "ck3_submit_player_artifact_personal_use_v1", "ck3_query_player_artifact_personal_use_action_post_v1",
})
CASE_PLAYER_PILGRIMAGE_EXECUTION_MCP_TOOLS = frozenset({
    "ck3_query_player_pilgrimage_planner_v1", "ck3_submit_player_pilgrimage_planner_v1",
})
CASE_HOLY_SITE_CREATION_UI_MCP_TOOLS = frozenset({
    "ck3_open_holy_site_creation_window_v1", "ck3_select_holy_site_creation_type_v1",
    "ck3_select_holy_site_creation_barony_v1", "ck3_set_holy_site_creation_artifact_selection_v1",
})
CASE_READ_ONLY_MCP_TOOLS = frozenset({
    "ck3_query_campaign_root_context_v1",
    "ck3_query_player_rite_governance_v1",
    "ck3_query_player_pilgrimage_activities_v1",
    "ck3_query_faith_power_ui_v1",
    "ck3_query_faith_power_tooltip_v1",
    "ck3_query_current_title_appointment_v1",
    "ck3_query_player_religion_context_v1",
    "ck3_query_player_holy_site_creation_context_v1",
    "ck3_query_player_holy_site_relic_action_context_v1",
    "ck3_query_player_artifact_personal_use_v1",
    "ck3_query_player_ghw_permissions_v1",
    "ck3_query_character_skill_effects_v1",
    "ck3_query_character_knight_effectiveness_v1",
    "ck3_query_player_holy_site_relic_permissions_v1",
    "ck3_query_player_holy_site_relic_context_v1",
    "ck3_query_player_holy_site_v1",
    "ck3_query_player_holy_site_adoption_detail_v1",
    "ck3_query_player_holy_site_decision_detail_v1",
    "ck3_query_player_holy_site_decision_cooldown_v1",
    "ck3_query_player_religion_numeric_special_parameters_v1",
    "ck3_query_player_religion_personal_parameters_v1",
    "ck3_query_player_religion_doctrines_v1",
    "ck3_query_player_religion_tenets_v1",
    "ck3_query_player_religion_reform_context_v1",
    "ck3_query_player_religion_draft_groups_v1",
    "ck3_query_player_religion_draft_doctrine_choices_v1",
    "ck3_query_player_religion_draft_tenet_choices_v1",
    "ck3_query_player_religion_draft_resource_costs_v1",
    "ck3_query_player_religion_hostility_v1",
})
SHA = re.compile(r"^[0-9a-fA-F]{64}$")


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def path_at(value: str, base: Path) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError("Nonempty path required")
    path = Path(value)
    return (path if path.is_absolute() else base / path).resolve()


def pin(path: Path) -> dict:
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def check_pin(path: Path, expected: dict) -> dict:
    if type(expected.get("bytes")) is not int or not SHA.fullmatch(str(expected.get("sha256", ""))):
        raise ValueError(f"Exact bytes/SHA required: {path}")
    actual = pin(path)
    if actual["bytes"] != expected["bytes"] or actual["sha256"] != expected["sha256"].lower():
        raise ValueError(f"Pinned input changed: {path}")
    return actual


def host_cli_flags(path: Path) -> set[str]:
    """Inspect declared argparse flags without importing or starting the host."""
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    return {
        argument.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr == "add_argument"
        for argument in node.args
        if isinstance(argument, ast.Constant) and isinstance(argument.value, str)
        and argument.value.startswith("--")
    }


class Selection:
    def __init__(self, runtime_path: Path, products_path: Path, product_key: str,
                 case_id: str, context_path: Path | None = None, prepared_path: Path | None = None):
        self.runtime_path = runtime_path.resolve()
        self.products_path = products_path.resolve()
        self.runtime = read_json(self.runtime_path)
        self.products = read_json(self.products_path)
        if self.runtime.get("schema") != RUNTIME_SCHEMA or self.products.get("schema") != PRODUCTS_SCHEMA:
            raise ValueError("Unsupported runtime/products schema")
        base = self.runtime_path.parent
        self.blockers: list[str] = []
        def configured(key, value):
            if value is None:
                self.blockers.append("Shared machine path unbound: " + key)
                return base / ("<unbound-" + key + ">")
            return path_at(value, base)
        self.paths = {key: configured(key, value) for key, value in self.runtime.get("paths", {}).items()}
        self.locations = {key: configured(key, self.runtime[key]) for key in
                          ("python", "repo_root", "game_dir", "userdir_root", "artifacts_root")}
        manifest_ref = self.runtime["manifest"]
        self.manifest_path = path_at(manifest_ref["path"], base)
        self.manifest = read_json(self.manifest_path)
        if self.manifest.get("schema") != MANIFEST_SCHEMA:
            raise ValueError("Unsupported shared runtime manifest schema")
        from ck3_mod_acceptance_graphics_cache import profile_enabled
        profile_enabled(self.manifest)
        self.product_key = product_key
        self.product = self.products["products"][product_key]
        self.shared_case_catalog = None
        if case_id == "workshop_cache":
            catalog = self.products
            if "workshop_cache_case" not in catalog:
                self.shared_case_catalog = self.locations["repo_root"] / "tools/ck3_mod_acceptance_products.json"
                catalog = read_json(self.shared_case_catalog)
                if catalog.get("schema") != PRODUCTS_SCHEMA:
                    raise ValueError("Unsupported shared cache case catalog schema")
            cases = [catalog["workshop_cache_case"]]
        else:
            cases = [case for case in self.product["cases"] if case["id"] == case_id]
        if len(cases) != 1:
            raise ValueError("Exactly one product case required")
        self.case = json.loads(json.dumps(cases[0]))
        tools = self.case.get("opt_in_read_only_mcp_tools", [])
        if (not isinstance(tools, list) or any(not isinstance(tool, str) for tool in tools)
                or len(tools) != len(set(tools)) or not set(tools) <= CASE_READ_ONLY_MCP_TOOLS
                or not set(tools) <= set(self.case.get("required_mcp_tools", []))):
            raise ValueError("Case read-only opt-in must declare unique registered required MCP tools")
        self.opt_in_read_only_mcp_tools = tools
        self.opt_in_holy_site_relic_actions = self.case.get("opt_in_holy_site_relic_actions", False)
        if type(self.opt_in_holy_site_relic_actions) is not bool:
            raise ValueError("opt_in_holy_site_relic_actions must be an explicit Boolean")
        if self.opt_in_holy_site_relic_actions and not CASE_HOLY_SITE_RELIC_ACTION_MCP_TOOLS <= set(self.case.get("required_mcp_tools", [])):
            raise ValueError("Relic action opt-in must declare all four finite action tools as required")
        self.opt_in_player_rite_creation_actions = self.case.get("opt_in_player_rite_creation_actions", False)
        if type(self.opt_in_player_rite_creation_actions) is not bool:
            raise ValueError("opt_in_player_rite_creation_actions must be an explicit Boolean")
        if self.opt_in_player_rite_creation_actions and not CASE_RITE_CREATION_ACTION_MCP_TOOLS <= set(self.case.get("required_mcp_tools", [])):
            raise ValueError("Rite action opt-in must declare query, finite action and retained collect tools as required")
        if not self.opt_in_player_rite_creation_actions and CASE_RITE_CREATION_ACTION_MCP_TOOLS & set(self.case.get("required_mcp_tools", [])):
            raise ValueError("Rite action tools require their explicit case opt-in")
        self.opt_in_player_inventory_window_open = self.case.get("opt_in_player_inventory_window_open", False)
        if type(self.opt_in_player_inventory_window_open) is not bool:
            raise ValueError("opt_in_player_inventory_window_open must be an explicit Boolean")
        if self.opt_in_player_inventory_window_open and not CASE_PLAYER_INVENTORY_WINDOW_OPEN_MCP_TOOLS <= set(self.case.get("required_mcp_tools", [])):
            raise ValueError("Inventory opening opt-in requires open and exact original-intent post tools")
        if not self.opt_in_player_inventory_window_open and CASE_PLAYER_INVENTORY_WINDOW_OPEN_MCP_TOOLS & set(self.case.get("required_mcp_tools", [])):
            raise ValueError("Inventory opening tools require their separate explicit case opt-in")
        self.opt_in_player_inventory_window_close = self.case.get("opt_in_player_inventory_window_close", False)
        if type(self.opt_in_player_inventory_window_close) is not bool:
            raise ValueError("opt_in_player_inventory_window_close must be an explicit Boolean")
        if self.opt_in_player_inventory_window_close and not CASE_PLAYER_INVENTORY_WINDOW_CLOSE_MCP_TOOLS <= set(self.case.get("required_mcp_tools", [])):
            raise ValueError("Inventory closing opt-in requires query, close and exact Close-intent post tools")
        if not self.opt_in_player_inventory_window_close and CASE_PLAYER_INVENTORY_WINDOW_CLOSE_MCP_TOOLS & set(self.case.get("required_mcp_tools", [])):
            raise ValueError("Inventory closing tools require their separate explicit case opt-in")
        self.opt_in_player_artifact_personal_use_actions = self.case.get("opt_in_player_artifact_personal_use_actions", False)
        if type(self.opt_in_player_artifact_personal_use_actions) is not bool:
            raise ValueError("opt_in_player_artifact_personal_use_actions must be an explicit Boolean")
        if self.opt_in_player_artifact_personal_use_actions and not CASE_PLAYER_ARTIFACT_PERSONAL_USE_ACTION_MCP_TOOLS <= set(self.case.get("required_mcp_tools", [])):
            raise ValueError("Personal-item action opt-in requires submit and exact original-intent post tools")
        if not self.opt_in_player_artifact_personal_use_actions and CASE_PLAYER_ARTIFACT_PERSONAL_USE_ACTION_MCP_TOOLS & set(self.case.get("required_mcp_tools", [])):
            raise ValueError("Personal-item action tools require explicit independent case opt-in")
        self.opt_in_player_pilgrimage_execution = self.case.get("opt_in_player_pilgrimage_execution", False)
        if type(self.opt_in_player_pilgrimage_execution) is not bool:
            raise ValueError("opt_in_player_pilgrimage_execution must be an explicit Boolean")
        if self.opt_in_player_pilgrimage_execution and not CASE_PLAYER_PILGRIMAGE_EXECUTION_MCP_TOOLS <= set(self.case.get("required_mcp_tools", [])):
            raise ValueError("Pilgrimage execution opt-in must declare both planner query and submit tools as required")
        if not self.opt_in_player_pilgrimage_execution and CASE_PLAYER_PILGRIMAGE_EXECUTION_MCP_TOOLS & set(self.case.get("required_mcp_tools", [])):
            raise ValueError("Pilgrimage planner tools require their explicit execution case opt-in")
        self.opt_in_holy_site_creation_ui = self.case.get("opt_in_holy_site_creation_ui", False)
        if type(self.opt_in_holy_site_creation_ui) is not bool:
            raise ValueError("opt_in_holy_site_creation_ui must be an explicit Boolean")
        if self.opt_in_holy_site_creation_ui and not CASE_HOLY_SITE_CREATION_UI_MCP_TOOLS <= set(self.case.get("required_mcp_tools", [])):
            raise ValueError("Creation UI opt-in must declare all four finite UI tools as required")
        self.opt_in_holy_site_creation_create_once = self.case.get("opt_in_holy_site_creation_create_once", False)
        if type(self.opt_in_holy_site_creation_create_once) is not bool:
            raise ValueError("opt_in_holy_site_creation_create_once must be an explicit Boolean")
        if self.opt_in_holy_site_creation_create_once and (
                self.opt_in_holy_site_creation_ui is not True
                or "ck3_create_holy_site_once_v1" not in self.case.get("required_mcp_tools", [])):
            raise ValueError("Create once Case requires both explicit opt-ins and its required action tool")
        self.prepared_path = prepared_path.resolve() if prepared_path else None
        self.prepared = read_json(self.prepared_path) if self.prepared_path else None
        if self.prepared:
            if self.prepared.get('schema') != 'ck3-mod-acceptance-prepared-case-v1' or (
                    self.prepared.get('product') != product_key or self.prepared.get('case') != case_id):
                raise ValueError('Prepared case belongs to another product/case')
            if self.prepared.get('runtime_manifest') != pin(self.manifest_path):
                raise ValueError('Prepared case selected another shared runtime')
            self.case['startup'].update(self.prepared['startup'])
            if self.prepared.get('initial_plan'):
                self.case['initial_plan'] = self.prepared['initial_plan']
        for forbidden in ("host", "source_root", "source_index", "native", "dll", "injector", "engine", "host_args", "host_features", "profile_features", "wire_evidence_codec"):
            if forbidden in self.product or forbidden in self.case:
                raise ValueError(f"Product case cannot select shared runtime: {forbidden}")
        self.context_path = context_path.resolve() if context_path else None
        self.context = read_json(self.context_path) if self.context_path else {}
        if self.context and self.context.get("schema") != CONTEXT_SCHEMA:
            raise ValueError("Unsupported actual run context schema")
        inputs=self.prepared.get('case_inputs',{}) if self.prepared else self.context.get('case_inputs',{})
        for key,value in inputs.get('budgets',{}).items():
            if key not in BUDGET_FLAGS or self.case['budgets'].get(key) is not None:
                raise ValueError('Budget latebinding can only fill a declared null field: '+key)
            if type(value) not in (int,float) or value<0 or value==0 and key!='hold_seconds':
                raise ValueError('Invalid explicit shared case budget: '+key)
            self.case['budgets'][key]=value
        if self.prepared and 'readiness_policy' in self.prepared and self.prepared['readiness_policy'] != self.readiness_policy:
            raise ValueError('Prepared readiness policy differs from the selected original budget/current user policy')
        run_id = self.context.get("run_id", "<allocated-run-id>")
        if self.context and (not isinstance(run_id, str) or not run_id or Path(run_id).name != run_id):
            raise ValueError("Actual allocated run_id required")
        if self.context:
            if self.context_path is None:
                raise ValueError('Actual allocated context requires its source path')
            self.run_dir = path_at(self.context['run_dir'], self.context_path.parent)
        else:
            self.run_dir = self.locations['artifacts_root'] / run_id
        self.values = {key: str(value) for key, value in self.locations.items()}
        self.values.update(run_id=run_id, run_dir=str(self.run_dir))
        self.runtime_environment = {}
        for key, value in self.runtime.get("runtime_environment", {}).items():
            if key == "PYTHONPATH":
                if not isinstance(value, list):
                    raise ValueError("Runtime PYTHONPATH must be explicit path strings")
                self.runtime_environment[key] = os.pathsep.join(str(path_at(item, base)) for item in value)
            elif key in ("PYTHONUTF8", "PYTHONDONTWRITEBYTECODE") and value == "1":
                self.runtime_environment[key] = value
            else:
                raise ValueError("Only shared Python import environment is configured here")
        declared_environment = self.manifest.get("entry_environment", {})
        if declared_environment:
            parts = []
            for row in declared_environment["PYTHONPATH_parts"]:
                parts.append(self.paths[row["path_key"]] if "path_key" in row else
                             self.paths[row["root_key"]] / row["relative_path"])
            shared_environment = {"PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1",
                                  "PYTHONPATH": os.pathsep.join(map(str, parts))}
            if self.runtime_environment and self.runtime_environment != shared_environment:
                raise ValueError("Machine Python environment differs from the one shared manifest")
            self.runtime_environment = shared_environment
        self.required_pins: list[tuple[Path, dict]] = [(self.manifest_path, manifest_ref)]
        if self.shared_case_catalog:
            self.required_pins.append((self.shared_case_catalog, pin(self.shared_case_catalog)))
        self.normal_quit_automation = None
        if "normal_quit_automation" in self.runtime:
            automation = self.runtime["normal_quit_automation"]
            if not isinstance(automation, dict) or set(automation) != {"helper", "matcher", "templates"}:
                raise ValueError("Normal Quit automation requires exactly helper/matcher/templates pins")
            self.normal_quit_automation = {}
            for key, row in automation.items():
                if not isinstance(row, dict):
                    raise ValueError("Normal Quit automation requires exact file pins")
                declared_path = row.get('path')
                if not isinstance(declared_path, str):
                    raise ValueError('Normal Quit automation requires an explicit file path')
                path = path_at(declared_path, base)
                self.required_pins.append((path, row))
                self.normal_quit_automation[key] = {**row, "path": str(path)}
        if self.prepared_path:
            self.required_pins.append((self.prepared_path, pin(self.prepared_path)))
        self.adapter_path: Path | None = None
        self.adapter_config: Path | None = None
        adapter = self.case.get('adapter')
        if adapter:
            if 'path' in adapter:self.adapter_path = self.case_path(adapter['path'])
            else:
                module=adapter['module']
                if not re.fullmatch(r'tools\.ck3_mod_acceptance_cases\.[a-z0-9_]+',module):
                    raise ValueError('Adapter module must name product case data below tools')
                self.adapter_path=self.locations['repo_root']/Path(*module.split('.')).with_suffix('.py')
            self.adapter_config = self.locations['repo_root']/adapter['config'] if adapter['config'].startswith('tools/') else self.case_path(adapter['config'])
        else:
            self.adapter_path = self.adapter_config = None
        self.argv = self.build_argv()

    @property
    def readiness_policy(self) -> dict:
        """Keep original product contracts while applying the future startup floor."""
        requested = self.case["budgets"]["readiness_timeout"]
        if requested is not None and (type(requested) not in (int, float) or
                                      not math.isfinite(requested) or requested <= 0):
            raise ValueError("Invalid original case budget: readiness_timeout")
        effective = max(requested, MINIMUM_READINESS_SECONDS) if requested is not None else None
        return {"schema": "ck3-mod-acceptance-readiness-policy-v1",
                "policy_id": "future-readiness-minimum-2026-10-15",
                "source": "explicit-user-instruction-2026-10-15",
                "minimum_seconds": MINIMUM_READINESS_SECONDS,
                "requested_seconds": requested, "effective_seconds": effective,
                "floor_applied": requested is not None and requested < MINIMUM_READINESS_SECONDS,
                "historical_receipts_reclassified": False}

    @property
    def effective_budgets(self) -> dict:
        budgets = dict(self.case["budgets"])
        budgets["readiness_timeout"] = self.readiness_policy["effective_seconds"]
        return budgets

    def manifest_path_key(self, row: dict) -> Path:
        key = row["path_key"]
        if key not in self.paths:
            raise ValueError(f"Shared runtime path_key missing from machine config: {key}")
        return self.paths[key]

    def shared_file(self, row: dict | None, name: str = "") -> Path:
        if row is None:
            self.blockers.append("Shared manifest pin unbound: " + name)
            return self.paths[name]
        path = self.manifest_path_key(row)
        self.required_pins.append((path, row))
        return path

    def expand(self, text: str) -> str:
        try:
            return text.format_map(self.values)
        except KeyError as error:
            raise ValueError(f"Unknown product path template: {error.args[0]}") from None

    def case_path(self, reference: str | dict) -> Path:
        text = reference["path"] if isinstance(reference, dict) else reference
        path = path_at(self.expand(text), self.products_path.parent)
        if isinstance(reference, dict):
            self.required_pins.append((path, reference))
        return path

    def build_argv(self) -> list[str]:
        host = self.shared_file(self.manifest["host"], "host")
        if 'host_support_projection' in self.manifest:
            support_pins = validate_host_running_date_projection(
                self.manifest['host_support_projection'], host, self.manifest['machine_id'])
            for reference in support_pins:
                self.required_pins.append((Path(reference['path']).resolve(), dict(reference)))
        source = self.manifest_path_key(self.manifest["source_root"])
        for name in ("source_index", "native_source_index"):
            self.shared_file(self.manifest[name], name)
        for row in self.manifest.get("imports", []):
            self.shared_file(row["index"])
        native = self.manifest["native"]
        dll, injector = self.shared_file(native["dll"]), self.shared_file(native["injector"])
        startup = self.case["startup"]
        state = self.case_path(startup["state_dir"])
        self.state_dir = state
        pipe = "\\\\.\\pipe\\ck3_mod_acceptance_" + self.values["run_id"]
        argv = [str(self.locations["python"]), "-B", "-X", "utf8", str(host),
                "--agent-source-root", str(source), "--game-dir", str(self.locations["game_dir"]),
                "--bridge-dll", str(dll), "--bridge-injector", str(injector),
                "--bridge-pipe", pipe, "--output", str(self.run_dir / "native-report.json"),
                "--state-dir", str(state), "--plan", str(self.case_path(self.case["initial_plan"])),
                "--control-plan-dir", str(self.run_dir / "controls")]
        features = self.manifest.get("host_features", {})
        if not isinstance(features, dict) or set(features) - {"succession_title_readonly", "confucian_challenger_readonly", "stock_grant_title_picker", "war_cash_queries", "saved_campaign_inject_after_load", "saved_campaign_debug_mode", "wire_evidence_codec"}:
            raise ValueError("Unknown shared host feature")
        codec = wire_evidence_codec(features["wire_evidence_codec"] if "wire_evidence_codec" in features else "plain")
        if any(type(value) is not bool for key, value in features.items() if key != "wire_evidence_codec"):
            raise ValueError("Shared host features require explicit booleans")
        if codec == "gzip-members":
            argv += ["--wire-evidence-codec", codec]
        if features.get("succession_title_readonly"):
            argv += ["--private-succession-title-readonly"]
        if features.get("confucian_challenger_readonly"):
            argv += ["--private-confucian-challenger-readonly"]
        if features.get("stock_grant_title_picker"):
            argv += ["--private-grant-title-picker"]
        if features.get("war_cash_queries"):
            argv += ["--private-war-cash-queries"]
        if features.get("saved_campaign_inject_after_load") and startup["mode"] == "saved_campaign":
            argv += ["--saved-campaign-inject-after-load"]
        if features.get("saved_campaign_debug_mode") and startup["mode"] == "saved_campaign":
            argv += ["--saved-campaign-debug-mode"]
        budgets = self.effective_budgets
        for key, flag in BUDGET_FLAGS.items():
            value = budgets[key]
            if value is None:
                self.blockers.append('Original case budget unbound: '+key)
                continue
            if type(value) not in (int, float) or value < 0 or (value == 0 and key != "hold_seconds"):
                raise ValueError(f"Invalid original case budget: {key}")
            argv += [flag, str(value)]
        if startup["mode"] == "fixture":
            argv += ["--fixture-profile", "--frontend-robert-bootstrap", "--frontend-fixture-start-policy",
                     str(self.case_path(startup["fixture_start_policy"]))]
            if startup.get("frontend_rules_plan"):
                argv += ["--frontend-rules-plan", str(self.case_path(startup["frontend_rules_plan"]))]
            if startup.get('startup_case_contract'):
                argv += ['--frontend-fixture-startup-case-contract',str(self.case_path(startup['startup_case_contract']))]
        elif startup["mode"] == "ordinary_gui_campaign":
            ordinary_gui_campaign_startup(startup)
            if self.prepared is not None:
                prepared = json_object(self.prepared)
                profile = object_field(object_field(prepared, 'preparation'), 'profile')
                reference = file_pin(profile.get('preparation'))
                self.required_pins.append((Path(reference['path']).resolve(), dict(reference)))
            argv += ["--fixture-profile", "--ordinary-gui-campaign"]
        elif startup["mode"] == "workshop_cache":
            argv += ["--fixture-profile", "--frontend-mod-load-observation"]
        elif startup["mode"] == "saved_campaign":
            argv += ['--fixture-profile']
            if startup.get('saved_campaign_startup_case_contract'):
                argv += ['--saved-campaign-startup-case-contract',
                         str(self.case_path(startup['saved_campaign_startup_case_contract']))]
            saved = dict(startup["saved_campaign"])
            for key, value in self.context.get("saved_campaign", {}).items():
                if key not in SAVED_FLAGS or saved.get(key) is not None:
                    raise ValueError(f"Saved latebinding can only fill a declared null field: {key}")
                saved[key] = value
            for key, flag in SAVED_FLAGS.items():
                value = saved.get(key)
                if value is None:
                    self.blockers.append(f"Saved campaign input unbound: {key}")
                    continue
                if key in ("save", "product_inventory"):
                    value = str(self.case_path(value))
                elif key in ("bytes", "player_id", "date_raw"):
                    if type(value) is not int or value <= 0:
                        raise ValueError(f"Positive saved integer required: {key}")
                elif not SHA.fullmatch(str(value)):
                    raise ValueError("Saved campaign exact SHA required")
                argv += [flag, str(value)]
            self.saved = saved
        else:
            raise ValueError("Unsupported fixture, saved_campaign, workshop_cache or ordinary_gui_campaign startup mode")
        if self.opt_in_player_inventory_window_open:
            argv.append("--allow-private-player-inventory-window-open")
        if self.opt_in_player_inventory_window_close:
            argv.append("--allow-private-player-inventory-window-close")
        if self.opt_in_player_artifact_personal_use_actions:
            argv.append("--allow-private-player-artifact-personal-use-actions")
        if self.opt_in_player_pilgrimage_execution:
            argv.append("--allow-private-player-pilgrimage-execution")
        if self.opt_in_player_rite_creation_actions:
            argv.append("--private-player-rite-creation-actions")
        if self.opt_in_holy_site_relic_actions:
            argv.append("--private-holy-site-relic-actions")
        if self.opt_in_holy_site_creation_create_once:
            argv.append("--private-player-holy-site-creation-create-once")
        if self.opt_in_holy_site_creation_ui:
            argv.append("--private-player-holy-site-creation-ui")
        for tool in self.opt_in_read_only_mcp_tools:
            argv += ["--case-read-only-mcp-tool", tool]
        return argv

    def describe(self) -> dict:
        return {"schema": "ck3-mod-acceptance-plan-v1", "product": self.product_key,
                "case": self.case["id"], "case_status": self.case.get("status"),
                "shared_manifest": str(self.manifest_path), "run_id": self.values["run_id"],
                "host_argv": self.argv, "required_mcp_tools": self.case.get("required_mcp_tools", []),
                "opt_in_read_only_mcp_tools": self.opt_in_read_only_mcp_tools,
                "opt_in_holy_site_relic_actions": self.opt_in_holy_site_relic_actions,
                "opt_in_player_rite_creation_actions": self.opt_in_player_rite_creation_actions,
                "opt_in_player_inventory_window_open": self.opt_in_player_inventory_window_open,
                "opt_in_player_inventory_window_close": self.opt_in_player_inventory_window_close,
                "opt_in_player_artifact_personal_use_actions": self.opt_in_player_artifact_personal_use_actions,
                "opt_in_player_pilgrimage_execution": self.opt_in_player_pilgrimage_execution,
                "rite_confirmation_expected_state_writes": ["native-session/rite-creation-actions/*.claim.json",
                    "native-session/rite-creation-actions/*.native-result.json"] if self.opt_in_player_rite_creation_actions else [],
                "opt_in_holy_site_creation_ui": self.opt_in_holy_site_creation_ui,
                "opt_in_holy_site_creation_create_once": self.opt_in_holy_site_creation_create_once,
                "creation_create_once_expected_state_writes": [
                    "native-session/holy-site-creation-create-once-intents/*.pending.json",
                    "native-session/holy-site-creation-create-once-intents/*.result.json",
                ] if self.opt_in_holy_site_creation_create_once else [],
                "runtime_environment": self.runtime_environment,
                "phases": self.case.get("phases", []), "budgets": self.case["budgets"],
                "effective_budgets": self.effective_budgets, "readiness_policy": self.readiness_policy,
                "fixture_prepare": self.case.get("fixture_prepare"),
                "adapter": self.case.get('adapter'),
                "normal_close": self.case.get("normal_close"), "gui_contract": self.case.get("gui_contract"),
                "outputs": self.case.get("outputs"), "blockers": list(self.blockers),
                "runtime_status": "NOT_RUN", "business_acceptance": "NOT_ASSESSED"}

    def recording_runtime_input_sources(self) -> RuntimeInputSources | None:
        allocation = json_object(self.runtime.get('allocation', {}))
        if allocation.get('recording') is None:
            return None
        from ck3_mod_acceptance_runtime_inputs import load_runtime_input_sources
        launcher = path_at(self.runtime['reviewed_launcher']['path'], self.runtime_path.parent)
        return load_runtime_input_sources(launcher.with_name('ck3_mod_acceptance_runtime_inputs.py'))

    def preflight(self) -> dict:
        checks = []
        errors = list(self.blockers)
        for path, expected in self.required_pins:
            try:
                checks.append(check_pin(path, expected))
            except (OSError, ValueError) as error:
                errors.append(str(error))
        try:
            sources = self.recording_runtime_input_sources()
            if sources is not None:
                for reference in (sources['helper'], sources['contract']):
                    checks.append(check_pin(Path(reference['path']), dict(reference)))
        except (OSError, ValueError, AttributeError, ImportError) as error:
            errors.append('Running input source closure: ' + str(error))
        for key in ("python", "repo_root", "game_dir", "userdir_root"):
            if not self.locations[key].exists():
                errors.append(f"Configured location missing: {key}: {self.locations[key]}")
        host = self.paths["host"] if self.manifest["host"] is None else self.manifest_path_key(self.manifest["host"])
        try:
            missing = sorted({value for value in self.argv if value.startswith("--")} - host_cli_flags(host))
            if missing:
                errors.append("Selected canonical host lacks declared CLI: " + ", ".join(missing))
        except (OSError, SyntaxError) as error:
            errors.append(str(error))
        game = self.manifest["game"]
        exe = self.locations["game_dir"] / "binaries" / "ck3.exe"
        try:
            identity = pin(exe)
            if identity["sha256"] != game["exe_sha256"].lower():
                errors.append("Actual installed game differs from the one shared manifest")
            checks.append(identity)
        except OSError as error:
            errors.append(str(error))
        for flag in ("--plan", "--frontend-fixture-start-policy", "--frontend-rules-plan",
                     "--saved-campaign-save", "--saved-campaign-product-inventory",'--frontend-fixture-startup-case-contract',
                     '--saved-campaign-startup-case-contract'):
            if flag in self.argv:
                path = Path(self.argv[self.argv.index(flag) + 1])
                if not path.is_file():
                    errors.append(f"Prepared case input missing: {flag}: {path}")
        if "--frontend-fixture-start-policy" in self.argv:
            source = self.manifest_path_key(self.manifest["source_root"])
            import_root = source / "ck3_autonomous_player" / "src"
            if not import_root.is_dir():
                import_root = source / "src"
            sys.path.insert(0, str(import_root))
            try:
                contract = importlib.import_module("xar_autoplayer.bridge.frontend_fixture_start_contract")
                contract_file = contract.__file__
                if contract_file is None or not Path(contract_file).resolve().is_relative_to(import_root.resolve()):
                    raise ValueError("Fixture validator import differs from the selected shared source")
                policy = Path(self.argv[self.argv.index("--frontend-fixture-start-policy") + 1])
                contract.validate_fixture_start_policy(read_json(policy))
            except (ImportError, OSError, ValueError) as error:
                errors.append("Selected shared fixture policy validator: " + str(error))
            finally:
                sys.path.remove(str(import_root))
        if self.prepared and 'graphics_cache' in self.prepared:
            from ck3_mod_acceptance_graphics_cache import validate_prepared_graphics
            try:
                checks.extend(validate_prepared_graphics(self))
            except (KeyError, OSError, TypeError, ValueError) as error:
                errors.append('Prepared graphics cache: ' + str(error))
        capabilities = self.manifest.get("capabilities", {})
        tool_status = {}
        for tool in self.case.get("required_mcp_tools", []):
            status = capabilities.get(tool)
            tool_status[tool] = status
            if not status or status.get("source_build_ready") is not True:
                errors.append(f"Required MCP tool has no shared build-ready evidence: {tool}")
        if self.case.get("status") != "ready":
            errors.append("Product case is explicitly blocked; preserve its pending adapter/contract")
        if self.adapter_path:
            try:
                if self.adapter_config is None:
                    raise ValueError('Selected adapter contract path is missing')
                checks.extend((check_pin(self.adapter_path,self.prepared['adapter']),check_pin(self.adapter_config,self.prepared['contract']))
                              if self.prepared else (pin(self.adapter_path),pin(self.adapter_config)))
                module = self.load_adapter()
                for name in ('prepare_case','run_case','verify_case'):
                    if not callable(getattr(module,name,None)):
                        errors.append('Actual case adapter lacks '+name)
                if callable(getattr(module,'validate_contract',None)):
                    with self.case_imports():
                        module.validate_contract(self.adapter_context())
            except (ImportError,OSError,ValueError) as error:
                errors.append('Case adapter: '+str(error))
        if '--frontend-fixture-startup-case-contract' in self.argv:
            try:
                hook_path=Path(self.argv[self.argv.index('--frontend-fixture-startup-case-contract')+1]);hook=read_json(hook_path)
                if set(hook)!={'schema','state_dir','handler','dependencies'} or hook['schema']!='ck3-frontend-fixture-startup-case-contract-v1':
                    raise ValueError('Unsupported startup-case contract')
                if Path(hook['state_dir']).resolve()!=self.state_dir.resolve() or hook['handler']['function']!='admit_startup_event':
                    raise ValueError('Startup-case handler crossed actual prepared state/function')
                for row in [hook['handler'],*hook['dependencies']]:checks.append(check_pin(Path(row['path']),row))
            except (OSError,KeyError,ValueError) as error:errors.append('Startup-case contract: '+str(error))
        if '--saved-campaign-startup-case-contract' in self.argv:
            try:
                hook_path=Path(self.argv[self.argv.index('--saved-campaign-startup-case-contract')+1]);hook=read_json(hook_path)
                dynamic_instance=hook.get('schema')=='ck3-saved-campaign-startup-case-contract-v2'
                fields={'schema','state_dir','handler','dependencies','expected'}
                if dynamic_instance:fields.add('profile_id')
                if set(hook)!=fields or hook['schema'] not in ('ck3-saved-campaign-startup-case-contract-v1','ck3-saved-campaign-startup-case-contract-v2'):
                    raise ValueError('Unsupported saved startup-case contract')
                function='qualify_prepare_event_from_save' if dynamic_instance else 'admit_saved_startup_event'
                if Path(hook['state_dir']).resolve()!=self.state_dir.resolve() or hook['handler']['function']!=function:
                    raise ValueError('Saved startup-case handler crossed actual prepared state/function')
                expected=hook['expected']
                if set(expected)!={'event_definition_key','event_instance_id','root_character_id','actor_character_id','date_raw','native_option_indices'}:
                    raise ValueError('Saved startup-case requires exact event identity fields')
                if not isinstance(expected['event_definition_key'],str) or not expected['event_definition_key']:
                    raise ValueError('Saved startup-case event definition is missing')
                integer_keys=('root_character_id','actor_character_id','date_raw') if dynamic_instance else ('event_instance_id','root_character_id','actor_character_id','date_raw')
                for key in integer_keys:
                    if type(expected[key]) is not int or expected[key]<=0 or dynamic_instance and expected[key]>2**31-1:
                        raise ValueError('Saved startup-case positive integer required: '+key)
                if dynamic_instance and (hook['profile_id']!='faith-and-power-e01-abbasid-867'
                        or expected['event_instance_id'] is not None
                        or expected['event_definition_key']!='xar_faith_h01_prepare.1'
                        or expected['date_raw']!=51394920 or expected['native_option_indices']!=[0,1]):
                    raise ValueError('Saved startup v2 requires the approved scenario and an unbound current-process event instance')
                indices=expected['native_option_indices']
                if not isinstance(indices,list) or not indices or any(type(i) is not int or i<0 for i in indices) or len(set(indices))!=len(indices):
                    raise ValueError('Saved startup-case native options must be unique nonnegative integers')
                if expected['root_character_id']!=self.saved['player_id'] or expected['actor_character_id']!=self.saved['player_id'] or expected['date_raw']!=self.saved['date_raw']:
                    raise ValueError('Saved startup-case crossed pinned actor/date')
                checks.append(pin(hook_path))
                for row in [hook['handler'],*hook['dependencies']]:checks.append(check_pin(Path(row['path']),row))
            except (OSError,KeyError,TypeError,ValueError) as error:errors.append('Saved startup-case contract: '+str(error))
        if self.context:
            try:
                if self.context_path is None:
                    raise ValueError('Allocated context source path is missing')
                frozen_ref = self.context["frozen_argv"]
                frozen_path = path_at(frozen_ref["path"], self.context_path.parent)
                checks.append(check_pin(frozen_path, frozen_ref))
                frozen = read_json(frozen_path)
                if frozen["run_id"] != self.values["run_id"] or frozen.get("argv") != self.argv:
                    errors.append("Actual allocated frozen argv differs from the one shared runtime/case selection")
                if frozen.get("runtime_environment", {}) != self.runtime_environment:
                    errors.append("Actual frozen shared Python environment differs from runtime config")
            except (KeyError, OSError, ValueError) as error:
                errors.append(str(error))
        if self.context and self.adapter_path:
            try:
                from ck3_mod_acceptance_client import resolve_operator_reviewer
                resolve_operator_reviewer(self)
            except (ImportError, KeyError, OSError, TypeError, ValueError) as error:
                errors.append("Operator reviewer: " + str(error))
        if hasattr(self, "saved") and all(self.saved.get(key) is not None for key in SAVED_FLAGS):
            try:
                checks.append(check_pin(self.case_path(self.saved["save"]), self.saved))
            except (OSError, ValueError) as error:
                errors.append(str(error))
        result = self.describe()
        result.update(status="BLOCKED" if errors else "READY_FOR_EXISTING_REVIEWED_LAUNCH",
                      blockers=errors, checked_inputs=checks, tool_status=tool_status,
                      capability_limit="Source/build evidence only; actual live tool and product gates remain mandatory")
        return result

    def case_imports(self) -> AbstractContextManager[Path | None]:
        return _case_sdk_imports_v1(self.manifest_path_key(self.manifest['source_root']), self.runtime_environment)

    def load_adapter(self) -> ModuleType:
        if not self.adapter_path:
            raise ValueError('Product case has no implemented business adapter')
        # All product modules share the public client/prepare package. Runtime
        # source, native bridge and host never come from these modules.
        repo=str(self.locations['repo_root'])
        if repo not in sys.path:sys.path.insert(0,repo)
        sys.path.insert(0,str(self.adapter_path.parent.parent))
        try:
            package=importlib.import_module('ck3_mod_acceptance_cases')
            if str(self.adapter_path.parent) not in package.__path__:
                package.__path__.append(str(self.adapter_path.parent))
            spec=importlib.util.spec_from_file_location('ck3_mod_acceptance_cases.'+self.adapter_path.stem,self.adapter_path)
            if spec is None or spec.loader is None:
                raise ValueError('Selected product case module is unavailable')
            module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module
            with self.case_imports():
                spec.loader.exec_module(module)
            return module
        finally:
            sys.path.remove(str(self.adapter_path.parent.parent))

    def r06_post_allocate_inputs(self, inputs):
        """Bind only the explicit R06 capacity hole from immutable allocation pins.

        Allocation owns the run ID. Prepared inputs and host argv remain unchanged;
        the reviewed context may add one separately pinned capacity scope afterward.
        """
        scope_ref=self.context.get('r06_post_allocate_scope')
        r06=inputs.get('r06_refill_one_day')
        if not self.context or self.context_path is None:
            return inputs,None
        if r06 is None:
            if scope_ref is not None:raise ValueError('R06 post-allocate scope cannot override another case')
            return inputs,None
        if (self.product_key!='war-episode04-r10' or self.case['id']!='r10-common-preparation'
                or inputs.get('r04_county_entry') is not None or not self.prepared_path):
            raise ValueError('R06 post-allocate scope requires its exclusive prepared public case')
        if r06.get('capacity_admission','absent') is not None:
            raise ValueError('Prepare R06 with an explicit null capacity; never predict an allocated run')
        def exact(ref,maximum=262144):
            if (not isinstance(ref,dict) or set(ref)!={'path','bytes','sha256'}
                    or type(ref['bytes']) is not int or not 0<ref['bytes']<=maximum):
                raise ValueError('Exact bounded R06 post-allocate pin required')
            path=Path(ref['path']).resolve()
            if not path.is_file() or path.stat().st_size!=ref['bytes']:
                raise ValueError('Exact bounded R06 post-allocate file changed')
            check_pin(path,ref)
            return read_json(path)
        scope=exact(scope_ref)
        fields={'schema','machine_id','run_id','run_dir','state_dir','prepared_case',
                'runtime_manifest','allocated_context','frozen_argv','capacity_admission'}
        if set(scope)!=fields or scope['schema']!='ck3-mod-acceptance-r06-post-allocate-scope-v1':
            raise ValueError('Unsupported R06 post-allocate scope')
        prepared_pin=pin(self.prepared_path);manifest_pin=pin(self.manifest_path)
        if (scope['prepared_case']!=prepared_pin or self.context.get('prepared_case')!=prepared_pin
                or scope['runtime_manifest']!=manifest_pin or self.prepared.get('runtime_manifest')!=manifest_pin):
            raise ValueError('R06 scope crossed immutable prepared case/runtime')
        if (scope['run_id']!=self.values['run_id'] or Path(scope['run_dir']).resolve()!=self.run_dir.resolve()
                or Path(scope['state_dir']).resolve()!=self.state_dir.resolve()):
            raise ValueError('R06 scope crossed actual allocation roots/run')
        if (Path(scope['allocated_context']['path']).resolve()!=self.run_dir/'allocated-context.json'
                or Path(scope['frozen_argv']['path']).resolve()!=self.run_dir/'frozen-argv.json'
                or self.context.get('frozen_argv')!=scope['frozen_argv']):
            raise ValueError('R06 scope requires the original allocated context/frozen argv')
        allocated=exact(scope['allocated_context']);frozen=exact(scope['frozen_argv'],4*1024*1024)
        if (allocated.get('schema')!=CONTEXT_SCHEMA or allocated.get('run_id')!=scope['run_id']
                or Path(allocated['run_dir']).resolve()!=self.run_dir.resolve()
                or allocated.get('prepared_case')!=prepared_pin
                or allocated.get('case_inputs')!=self.prepared['case_inputs']
                or self.context.get('case_inputs')!=allocated['case_inputs']
                or frozen.get('run_id')!=scope['run_id'] or frozen.get('runtime_manifest')!=manifest_pin
                or Path(frozen['state_dir']).resolve()!=self.state_dir.resolve() or frozen.get('argv')!=self.argv):
            raise ValueError('R06 scope changed original allocation/prepared inputs or host argv')
        machine=frozen.get('identity_allocation',{}).get('machine_id')
        cap=exact(scope['capacity_admission'])
        if (not machine or scope['machine_id']!=machine or self.manifest.get('machine_id')!=machine
                or cap.get('machine_id')!=machine or cap.get('run_id')!=scope['run_id']
                or cap.get('admitted') is not True or cap.get('budget_status')!='GREEN'
                or Path(cap['scene_root']).resolve()!=Path(r06['scene_root']).resolve()
                or Path(cap['component_roots']['profile']).resolve()!=self.state_dir.resolve()
                or Path(cap['component_roots']['driver']).resolve()!=self.run_dir.resolve()
                or cap['component_ceiling_bytes']['profile']!=r06['profile_limit_bytes']
                or cap['component_ceiling_bytes']['driver']!=r06['driver_limit_bytes']):
            raise ValueError('R06 capacity does not bind actual machine/run/roots/limits')
        from datetime import datetime,timezone
        expiry=datetime.fromisoformat(cap['quota_review_at_utc'].replace('Z','+00:00'))
        requested=datetime.fromisoformat(r06['deadline_utc'].replace('Z','+00:00'))
        hard=datetime.fromisoformat(cap['run_hard_deadline_utc'].replace('Z','+00:00'))
        if expiry.tzinfo is None or requested.tzinfo is None or hard.tzinfo is None or datetime.now(timezone.utc)>=expiry or requested>hard:
            raise ValueError('R06 post-allocate capacity expired or deadline exceeded')
        derived=json.loads(json.dumps(inputs))
        derived['r06_refill_one_day']['capacity_admission']=scope['capacity_admission']
        return derived,scope_ref

    def adapter_context(self, output=None, inputs=None):
        case_inputs = inputs if inputs is not None else self.prepared.get('case_inputs',{}) if self.prepared else self.context.get('case_inputs',{})
        case_inputs,r06_scope=self.r06_post_allocate_inputs(case_inputs)
        result={'repo_root':str(self.locations['repo_root']),'run_dir':str(self.run_dir),
            'state_dir':str(self.state_dir),'output':str(output or self.run_dir/'case-output'),
            'run_id':self.context.get('run_id'),'game_dir':str(self.locations['game_dir']),
            'product':self.product_key,'case':self.case['id'],'case_spec':self.case,
            'shared_source_root':str(self.manifest_path_key(self.manifest['source_root'])),
            'shared_game':self.manifest['game'],'case_contract':read_json(self.adapter_config),
            'product_spec':self.product,'canonical_products_path':str(self.case_path(self.products['product_inventory'])),
            'case_inputs':case_inputs,'saved_campaign':self.prepared.get('startup',{}).get('saved_campaign',{}) if self.prepared else self.context.get('saved_campaign',{}),
            'runtime_manifest':pin(self.manifest_path),'readiness_policy':self.readiness_policy,
            'opt_in_holy_site_creation_ui':self.opt_in_holy_site_creation_ui,
            'opt_in_player_inventory_window_open':self.opt_in_player_inventory_window_open,
            'opt_in_player_inventory_window_close':self.opt_in_player_inventory_window_close,
            'opt_in_player_artifact_personal_use_actions':self.opt_in_player_artifact_personal_use_actions,
            'opt_in_player_pilgrimage_execution':self.opt_in_player_pilgrimage_execution}
        if r06_scope is not None:result['r06_post_allocate_scope']=r06_scope
        return result

    def prepare(self, inputs_path: Path, output: Path) -> dict[str, object]:
        if self.context:
            raise ValueError('Preparation precedes allocation; do not rewrite allocated input')
        if self.adapter_path is None or self.adapter_config is None:
            raise ValueError('Preparation requires its selected adapter and contract paths')
        if self.case.get('status')!='ready':
            raise ValueError('Explicitly blocked product adapter cannot prepare')
        inputs=read_json(inputs_path)
        from ck3_mod_acceptance_graphics_cache import profile_enabled, prepare_graphics_cache
        if 'shader_cache_seed' in inputs and not profile_enabled(self.manifest):
            raise ValueError('Shared shader cache reuse is default OFF')
        if 'shader_cache_python_compatibility' in inputs and 'shader_cache_seed' not in inputs:
            raise ValueError('Reviewed Python compatibility requires an explicit seed')
        for key,value in inputs.get('case_inputs',{}).get('budgets',{}).items():
            if key not in BUDGET_FLAGS or self.case['budgets'].get(key) is not None:
                raise ValueError('Prepare budget latebinding can only fill declared null fields: '+key)
            if type(value) not in (int,float) or value<0 or value==0 and key!='hold_seconds':
                raise ValueError('Invalid explicit shared case budget: '+key)
            self.case['budgets'][key]=value
        if any(v is None for v in self.case['budgets'].values()):
            raise ValueError('Preparation requires explicit binding of each declared null original budget')
        output=output.resolve()
        if output.exists():raise ValueError('New preparation output required; never replay')
        state=path_at(inputs['state_dir'],inputs_path.parent)
        if state.exists():raise ValueError('Unused prepared state required')
        output.mkdir(parents=True)
        context=self.adapter_context(output,inputs.get('case_inputs',{}))
        context.update(run_dir=str(output),state_dir=str(state),run_id=None)
        context['saved_campaign']=inputs.get('saved_campaign',{})
        with self.case_imports():
            result=self.load_adapter().prepare_case(context)
        graphics=None
        if 'shader_cache_seed' in inputs:
            from types import SimpleNamespace
            graphics=prepare_graphics_cache(SimpleNamespace(manifest=self.manifest,runtime=self.runtime,state_dir=state),
                inputs['shader_cache_seed'],result,output,
                compatibility_pin=inputs.get('shader_cache_python_compatibility'))
        from ck3_mod_acceptance_prepare import write_json
        prepared={'schema':'ck3-mod-acceptance-prepared-case-v1','product':self.product_key,'case':self.case['id'],
            'runtime_manifest':pin(self.manifest_path),'case_inputs':context['case_inputs'],
            'startup':result['startup'],'initial_plan':result.get('initial_plan',self.case['initial_plan']),
            'adapter':pin(self.adapter_path),'contract':pin(self.adapter_config),'preparation':result,
            'effective_budgets':self.effective_budgets,'readiness_policy':self.readiness_policy,
            'runtime_status':'NOT_RUN','business_acceptance':'NOT_ASSESSED'}
        if graphics is not None:
            prepared['graphics_cache']=graphics
        path=output/'prepared-case.json';write_json(path,prepared)
        return {'status':'CASE_PREPARED_NOT_ALLOCATED_NOT_RUN','prepared_case':pin(path),'preparation':result,
                'effective_budgets':self.effective_budgets,'readiness_policy':self.readiness_policy}

    def verify(self) -> dict[str, object]:
        if not self.context or self.context_path is None:raise ValueError('Verify requires one actual allocated run context')
        from ck3_mod_acceptance_client import resolve_operator_reviewer
        context=self.adapter_context()
        context['operator_reviewer']=resolve_operator_reviewer(self)
        with self.case_imports():
            adapter=self.load_adapter()
            result: dict[str, object] = dict(json_object(adapter.verify_case(context)))
        closed_path=Path(context['output'])/'normal-close-result.json'
        close=read_json(closed_path) if closed_path.is_file() else None
        if result.get('schema') == 'living-artifacts-threshold-case-result-v1':
            if self.product_key != 'living-artifacts' or self.case['id'] != 'threshold_suppression':
                raise ValueError('Legacy threshold verification requires its exact selected public case')
            if self.adapter_path is None or self.adapter_config is None:
                raise ValueError('Legacy threshold adapter/contract paths are missing')
            qualification = _legacy_threshold_gui_qualification_v1(
                result, loaded_adapter_source=getattr(adapter, '__file__', None),
                adapter_path=self.adapter_path, contract_path=self.adapter_config,
                prepared_path=self.prepared_path, context_path=self.context_path,
                runtime_path=self.runtime_path, products_path=self.products_path, manifest_path=self.manifest_path,
                required_pins=[(path, reference) for path, reference in self.required_pins],
                expected_argv=self.argv, expected_environment=self.runtime_environment, normal_close_path=closed_path,
            )
            if qualification is not None:
                # Enrich this new verification output; the producer's write-once
                # retained v1 result and all original source Pins stay untouched.
                result=dict(result)
                result['gui_contract_qualified']=qualification['gui_contract_qualified']
                result['legacy_gui_qualification']=json_object(qualification)
        result.update(normal_close=close)
        result['case_acceptance_pass']=bool(result.get('case_contract_qualified') is True and
            result.get('gui_contract_qualified') is True and close and close.get('normal_close_qualified') is True)
        # A case boundary or one core cell cannot certify the whole product.
        # Preserve the adapter's explicit business applicability and credit.
        result['qualified_boundary_pass']=result['case_acceptance_pass']
        result['business_pass']=bool(result.get('business_pass') is True and
                                    result.get('business_contract_applicable',True) is True and result['case_acceptance_pass'])
        result['product_release_pass']=False
        return result

    def run(self) -> dict[str, object]:
        result = self.preflight()
        if result["blockers"]:
            raise ValueError("Preflight blocked: " + "; ".join(result["blockers"]))
        if not self.context or self.context_path is None:
            raise ValueError("Run requires actual allocated frozen argv and current reviewed launcher context")
        launcher_ref = self.runtime["reviewed_launcher"]
        launcher = path_at(launcher_ref["path"], self.runtime_path.parent)
        check_pin(launcher, launcher_ref)
        context = self.context
        for key in ("keeper_root", "steam_offline_receipt"):
            if not context.get(key):
                raise ValueError(f"Existing reviewed launcher context missing: {key}")
        argv = [str(self.locations["python"]), "-B", "-X", "utf8", str(launcher),
                "--run-root", str(self.run_dir), "--keeper-root", str(path_at(context["keeper_root"], self.context_path.parent)),
                "--steam-offline-receipt", str(path_at(context["steam_offline_receipt"], self.context_path.parent))]
        environment = dict(os.environ)
        environment.update(self.runtime_environment)
        environment.update(PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
        if self.adapter_path:
            from ck3_mod_acceptance_client import resolve_operator_reviewer
            resolve_operator_reviewer(self)
        completed = subprocess.run(argv, cwd=self.locations["repo_root"], env=environment, check=False)
        result.update(status="REVIEWED_LAUNCHER_RETURNED" if completed.returncode == 0 else "LAUNCHER_FAILED",
                      launcher_argv=argv, launcher_exit_code=completed.returncode,
                      runtime_status="LAUNCH_REQUESTED" if completed.returncode == 0 else "LAUNCH_FAILED",
                      business_acceptance="NOT_ASSESSED")
        if completed.returncode==0 and self.adapter_path:
            from ck3_mod_acceptance_client import CaseClient,write_once
            client=CaseClient(self)
            adapter=self.load_adapter()
            context=self.adapter_context(client.output)
            failure=None
            try:
                client.wait_hold()
                with self.case_imports():
                    result['case_result']=adapter.run_case(context,client)
            except BaseException as error:
                failure=type(error).__name__+': '+str(error)
                write_once(client.output/'case-error-preserved.json',{'error':failure,'run_id':self.context['run_id'],
                    'business_pass':False,'submitted_steps_never_replayed':True})
                result['case_error']=failure
            finally:
                try:
                    if client._handle is not None or client.retain_held_process(wait=True):
                        result['normal_close']=client.normal_close('business_failure_preserved' if failure else 'actual_case_evidence_recorded')
                except BaseException as error:
                    result['normal_close_error']=type(error).__name__+': '+str(error)
                    write_once(client.output/'normal-close-error-preserved.json',{'error':result['normal_close_error'],'business_pass':False})
                client.close_handle()
            result['business_acceptance']='RED_OR_INCOMPLETE' if failure else 'ACTUAL_EVIDENCE_REQUIRES_VERIFICATION'
            write_once(client.output/'entry-run-result.json',result)
        return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "prepare", "allocate", "preflight", "run", "verify"))
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--products", type=Path, required=True)
    parser.add_argument("--product", required=True)
    parser.add_argument("--case", required=True)
    parser.add_argument("--run-context", type=Path)
    parser.add_argument('--prepared-case',type=Path)
    parser.add_argument('--case-inputs',type=Path)
    parser.add_argument('--prepare-output',type=Path)
    parser.add_argument('--attempt')
    parser.add_argument('--keeper-output',type=Path)
    parser.add_argument('--previous-live',type=Path)
    parser.add_argument('--previous-keeper',type=Path)
    parser.add_argument('--previous-release',type=Path)
    parser.add_argument('--previous-failure-close',type=Path,
                        help='Explicit failed report-writer resource closure; never normal exit or business credit')
    parser.add_argument('--latest-screen-release',type=Path)
    parser.add_argument('--first-machine-bootstrap',type=Path)
    parser.add_argument('--retire-pre-identity',type=Path,
        help='allocate only: append verified first pre-identity failure retirement before the actual first ID')
    parser.add_argument('--gui-review', type=Path,
                        help='Direct review of the fresh Steam offline frame for the shared GUI-only runtime')
    args = parser.parse_args(argv)
    try:
        if args.retire_pre_identity and args.mode != 'allocate':
            raise ValueError('--retire-pre-identity is confined to the public allocate mode')
        runtime = read_json(args.runtime)
        shared_manifest = read_json(path_at(runtime['manifest']['path'], args.runtime.resolve().parent))
        if shared_manifest.get('execution_mode') == 'gui_only':
            from ck3_mod_acceptance_gui import dispatch
            result = dispatch(args)
        else:
            result = native_dispatch(args)
    except (OSError, KeyError, ValueError, TypeError) as error:
        print(json.dumps({"status": "BLOCKED", "error": str(error), "runtime_status": "NOT_RUN",
                          "business_acceptance": "NOT_ASSESSED"}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    incomplete_verify = args.mode == 'verify' and result.get('case_acceptance_pass') is not True
    incomplete_close = (args.mode == 'run' and 'normal_close' in result and
                        (not isinstance(result['normal_close'], dict) or
                         result['normal_close'].get('normal_close_qualified') is not True))
    return 2 if (result.get('status') in {'RED', 'BLOCKED'} or
                 result.get("blockers") or result.get("launcher_exit_code", 0) or
                 result.get('case_error') or result.get('normal_close_error') or
                 incomplete_verify or incomplete_close) else 0


def same_directory_control_peer(name: str) -> ModuleType:
    """Bind allocator/unrun to this entry's directory before their control calls."""
    if name not in {'ck3_mod_acceptance_allocate', 'ck3_mod_acceptance_unrun'}:
        raise ValueError('Unknown public control peer: '+name)
    entry = Path(__file__).resolve()
    expected = entry.with_name(name+'.py')
    for key, path in (('ck3_mod_acceptance', entry), (name, expected)):
        cached = sys.modules.get(key)
        if cached is not None:
            source = getattr(cached, '__file__', None)
            if not isinstance(source, str) or Path(source).resolve() != path:
                raise ValueError('Public control module directory differs: '+key)
    prior = list(sys.path)
    try:
        sys.path.insert(0, str(entry.parent))
        module = importlib.import_module(name)
    finally:
        sys.path[:] = prior
    source = getattr(module, '__file__', None)
    if not isinstance(source, str) or Path(source).resolve() != expected:
        raise ValueError('Public control module directory differs: '+name)
    return module


def native_dispatch(args: argparse.Namespace) -> dict[str, object]:
    selection = Selection(args.runtime, args.products, args.product, args.case, args.run_context,args.prepared_case)
    result: dict[str, object]
    if args.mode=='prepare':
        if not args.case_inputs or not args.prepare_output:raise ValueError('prepare requires --case-inputs and --prepare-output')
        result=selection.prepare(args.case_inputs,args.prepare_output)
    elif args.mode=='allocate':
        allocator = same_directory_control_peer('ck3_mod_acceptance_allocate')
        same_directory_control_peer('ck3_mod_acceptance_unrun')
        result=allocator.allocate_and_keep(selection,args)
    elif args.mode=='verify':result=selection.verify()
    else:result=selection.describe() if args.mode=='plan' else selection.preflight() if args.mode=='preflight' else selection.run()
    return result

if __name__ == "__main__":
    raise SystemExit(main())
