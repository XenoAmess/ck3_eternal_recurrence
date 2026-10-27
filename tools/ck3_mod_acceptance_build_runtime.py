"""Build a shared acceptance runtime from exact committed source and a qualified native production build."""
from __future__ import annotations
import argparse
import ast
from collections.abc import Mapping
from datetime import datetime, timezone
from dataclasses import dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
from typing import Literal, TypedDict

import build_native_configured_successor as native_successor
from ck3_mod_acceptance_background_types import (
    WireEvidenceCodec, wire_evidence_codec, FilePin, JsonObject, json_object, text_field,
    checked_host_support_pin, HostRunningDateProjectionV1, project_running_date_host,
    validate_host_running_date_projection, RUNNING_DATE_SUPPORT_RELATIVE, RUNNING_DATE_SUPPORT_FILENAME,
)

HERE = Path(__file__).resolve().parent
BOM = b"\xef\xbb\xbf"
HOST_RELATIVE = "ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py"
SDK_PREFIX = "ck3_autonomous_player/src/"
GENERIC_DECISION_CONTRACTS: frozenset[str] = frozenset({
    SDK_PREFIX + "xar_autoplayer/bridge/ingame_decision_item_action_contract.py",
    SDK_PREFIX + "xar_autoplayer/bridge/ingame_decisions_open_contract.py",
})
NATIVE_PREFIX = "ck3_autonomous_player/native_bridge/"
PROFILE_EXPANSION_RELATIVE = "tools/ck3_mod_acceptance_native_profile_expansions.json"
TEST_PREFIX = "ck3_autonomous_player/tests/"


@dataclass(frozen=True)
class StockReadOnlyCapabilityRule:
    native_sources: tuple[str, ...]
    sdk_sources: tuple[str, ...]
    required_flags: tuple[str, ...] = ()


_FRONTEND_NATIVE_SOURCES = (
    "src/bridge.cpp", "src/ck3_12004_adapter.cpp", "src/frontend_gui_route_v1.cpp",
    "src/frontend_gui_result_v1.cpp",
)
_FRONTEND_SDK_SOURCES = (
    "xar_autoplayer/bridge/mcp_server.py", "xar_autoplayer/bridge/service.py",
    "xar_autoplayer/bridge/native_driver.py", "xar_autoplayer/bridge/frontend_gui_route_contract.py",
)
_FRONTEND_QUERY_FLAGS = (
    "XAR_CK3_ENABLE_FEUDAL_1066_BOOKMARK_MODEL_PRIVATE_V1",
    "XAR_CK3_ENABLE_FEUDAL_1066_SELECTED_BOOKMARK_START_PRIVATE_V1",
)
STOCK_READ_ONLY_CAPABILITIES: dict[str, StockReadOnlyCapabilityRule] = {
    "ck3_query_frontend_gui_route_v1": StockReadOnlyCapabilityRule(
        _FRONTEND_NATIVE_SOURCES, _FRONTEND_SDK_SOURCES, _FRONTEND_QUERY_FLAGS),
    "ck3_inspect_frontend_gui_tree_v1": StockReadOnlyCapabilityRule(
        _FRONTEND_NATIVE_SOURCES, _FRONTEND_SDK_SOURCES, _FRONTEND_QUERY_FLAGS),
    "ck3_migration_pipe_diagnostics": StockReadOnlyCapabilityRule(
        ("src/bridge.cpp",), ("xar_autoplayer/bridge/native_driver.py",)),
    "ck3_query_engine_diagnostics_v1": StockReadOnlyCapabilityRule(
        (), ("xar_autoplayer/bridge/mcp_server.py", "xar_autoplayer/ck3_runtime_diagnostics.py")),
    "ck3_query_engine_log_literals_v1": StockReadOnlyCapabilityRule(
        (), ("xar_autoplayer/bridge/mcp_server.py", "xar_autoplayer/ck3_runtime_diagnostics.py")),
}
CRITICAL_TRANSPORTS = frozenset({
    "player_pilgrimage_planner_private_transport.py", "player_pilgrimage_activities_private_transport.py",
    "native_driver.py", "mcp_server.py", "nonwar_private_build.py", "version_identity.py",
    "activity_feast_stage5_start_private_transport.py", "driver.py", "exact_clock_failure_diagnostic_v1.py",
})
EXTRA_CAPABILITIES: dict[str, list[str]] = {
    "ck3_save_checkpoint": [],  # Existing native save primitive; no new feature flag or live credit.
    "ck3_execute_step": [],  # Existing generic SDK endpoint; Case policy still constrains actions.
    "ck3_open_character_window_v1": ["XAR_ENABLE_RELIGION_UI12004_PRESENTATION"],
    "ck3_open_faith_window_v1": ["XAR_ENABLE_RELIGION_UI12004_PRESENTATION"],
    "ck3_present_faith_power_ui_v1": ["XAR_ENABLE_RELIGION_UI12004_PRESENTATION"],
    "ck3_query_faith_power_ui_v1": ["XAR_ENABLE_RELIGION_UI12004_PRESENTATION"],
    "ck3_query_faith_power_tooltip_v1": ["XAR_ENABLE_RELIGION_UI12004_PRESENTATION"],
    "ck3_open_holy_site_decision_v1": [],
    "ck3_confirm_holy_site_decision_v1": [],
    "ck3_query_player_holy_site_decision_detail_v1": [],
    "ck3_query_player_holy_site_decision_cooldown_v1": [],
    "ck3_inspect_gui_window_tree_v1": [],
    "ck3_query_scripted_widget_controls_v1": [],
    "ck3_activate_scripted_widget_control_v1": [],
    "ck3_query_player_rite_creation_action_context_v1": ["XAR_ENABLE_RITE_CREATION_ACTIONS12004"],
    "ck3_execute_player_rite_creation_action_v1": ["XAR_ENABLE_RITE_CREATION_ACTIONS12004"],
    "ck3_collect_player_rite_creation_action_result_v1": ["XAR_ENABLE_RITE_CREATION_ACTIONS12004"],
    "ck3_verify_player_rite_creation_action_completed_v1": ["XAR_ENABLE_RITE_CREATION_ACTIONS12004"],
    "ck3_open_ingame_decisions_v1": ["XAR_CK3_ENABLE_INGAME_DECISIONS_OPEN_PRIVATE_V1"],
    "ck3_query_ingame_decision_item_v1": [],
    "ck3_query_player_holy_site_v1": ["XAR_CK3_ENABLE_G2_PLAYER_HOLY_SITE_CREATION_CONTEXT_PRIVATE_QUERY_V1"],
    "ck3_query_player_rite_governance_v1": ["XAR_CK3_ENABLE_G2_PLAYER_RITE_GOVERNANCE_PRIVATE_QUERY_V1"],
    "ck3_query_player_religion_doctrines_v1": ["XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINES_PRIVATE_QUERY_V1"],
    "ck3_query_player_religion_tenets_v1": ["XAR_CK3_ENABLE_G2_PLAYER_RELIGION_TENETS_PRIVATE_QUERY_V1"],
    "ck3_query_player_rite_members_v1": ["XAR_CK3_ENABLE_G2_PLAYER_RITE_MEMBERS_PRIVATE_QUERY_V1"],
    "ck3_query_player_prisoner_collection_private_v1": [
        "XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1",
        "XAR_CK3_ENABLE_G2_PRISONER_RELEASE_PREVIEW_PRIVATE_V1",
    ],
    "ck3_select_ingame_decision_item_v1": ["XAR_CK3_ENABLE_INGAME_DECISION_ITEM_ACTIONS_PRIVATE_V1", "XAR_CK3_ENABLE_INGAME_DECISION_OUTCOME_PRIVATE_V1"],
    "ck3_confirm_ingame_decision_outcome_v1": ["XAR_CK3_ENABLE_INGAME_DECISION_ITEM_ACTIONS_PRIVATE_V1", "XAR_CK3_ENABLE_INGAME_DECISION_OUTCOME_PRIVATE_V1"],
    "ck3_query_player_artifact_personal_use_v1": ["XAR_CK3_ENABLE_G2_PLAYER_ARTIFACT_PERSONAL_USE_READONLY_V1"],
    "ck3_submit_player_artifact_personal_use_v1": ["XAR_CK3_ENABLE_ARTIFACT_PERSONAL_USE_PRIVATE_V1"],
    "ck3_query_player_artifact_personal_use_action_post_v1": ["XAR_CK3_ENABLE_ARTIFACT_PERSONAL_USE_PRIVATE_V1"],
    "ck3_query_player_ghw_permissions_v1": ["XAR_CK3_ENABLE_G2_PLAYER_GHW_PERMISSIONS_READONLY_V1"],
    "ck3_query_character_skill_effects_v1": ["XAR_CK3_ENABLE_CHARACTER_SKILL_EFFECTS12004_PRIVATE_QUERY_V1"],
    "ck3_query_character_knight_effectiveness_v1": ["XAR_CK3_ENABLE_CHARACTER_SKILL_EFFECTS12004_PRIVATE_QUERY_V1"],
    "ck3_open_player_inventory_window_v1": ["XAR_CK3_ENABLE_PLAYER_INVENTORY_WINDOW_OPEN_PRIVATE_V1"],
    "ck3_query_player_inventory_window_open_post_v1": ["XAR_CK3_ENABLE_PLAYER_INVENTORY_WINDOW_OPEN_PRIVATE_V1"],
    "ck3_query_player_inventory_window_close_v1": ["XAR_CK3_ENABLE_PLAYER_INVENTORY_WINDOW_OPEN_PRIVATE_V1"],
    "ck3_close_player_inventory_window_v1": ["XAR_CK3_ENABLE_PLAYER_INVENTORY_WINDOW_OPEN_PRIVATE_V1"],
    "ck3_query_player_inventory_window_close_post_v1": ["XAR_CK3_ENABLE_PLAYER_INVENTORY_WINDOW_OPEN_PRIVATE_V1"],
    "ck3_query_ingame_ui_window_v1": [],
    "ck3_open_holy_site_window_v1": [],
    "ck3_query_player_holy_site_creation_context_v1": ["XAR_CK3_ENABLE_G2_PLAYER_HOLY_SITE_CREATION_CONTEXT_PRIVATE_QUERY_V1"],
    "ck3_query_player_holy_site_relic_action_context_v1": [],
    "ck3_query_player_holy_site_relic_context_v1": [],
    "ck3_query_player_holy_site_relic_permissions_v1": [],
    "ck3_open_holy_site_creation_window_v1": ["XAR_ENABLE_HOLY_SITE_CREATION_UI12004"],
    "ck3_select_holy_site_creation_type_v1": ["XAR_ENABLE_HOLY_SITE_CREATION_UI12004"],
    "ck3_select_holy_site_creation_barony_v1": ["XAR_ENABLE_HOLY_SITE_CREATION_UI12004"],
    "ck3_set_holy_site_creation_artifact_selection_v1": ["XAR_ENABLE_HOLY_SITE_CREATION_UI12004"],
    "ck3_select_holy_site_relic_artifact_v1": ["XAR_ENABLE_HOLY_SITE_RELIC_TYPED_UI12004"],
    "ck3_set_holy_site_relic_slot_selection_v1": ["XAR_ENABLE_HOLY_SITE_RELIC_TYPED_UI12004"],
    "ck3_enshrine_holy_site_relic_v1": ["XAR_ENABLE_HOLY_SITE_RELIC_TYPED_UI12004", "XAR_ENABLE_HOLY_SITE_RELIC_BUTTON_ACTION12004"],
    "ck3_remove_holy_site_relic_v1": ["XAR_ENABLE_HOLY_SITE_RELIC_TYPED_UI12004", "XAR_ENABLE_HOLY_SITE_RELIC_BUTTON_ACTION12004"],
}
REGISTRATION_READ_ONLY_FLAGS: dict[str, str] = {
    "ck3_query_player_prisoner_collection_private_v1": "allow_private_prisoner_collection_query",
    "ck3_query_player_rite_members_v1": "allow_private_player_rite_members_query",
    "ck3_query_player_religion_doctrines_v1": "allow_private_player_religion_doctrines_query",
    "ck3_query_player_religion_tenets_v1": "allow_private_player_religion_tenets_query",
    "ck3_query_player_religion_reform_context_v1": "allow_private_player_religion_reform_context_query",
    "ck3_query_player_religion_draft_groups_v1": "allow_private_player_religion_draft_groups_query",
    "ck3_query_player_religion_draft_doctrine_choices_v1": "allow_private_player_religion_draft_doctrine_choices_query",
    "ck3_query_player_religion_draft_resource_costs_v1": "allow_private_player_religion_draft_resource_costs_query",
    "ck3_query_player_holy_site_creation_context_v1": "allow_private_player_holy_site_creation_context_query",
    "ck3_query_player_holy_site_relic_action_context_v1": "allow_private_player_holy_site_relic_action_context_query",
    "ck3_query_player_holy_site_relic_permissions_v1": "allow_private_player_holy_site_relic_permissions_query",
    "ck3_query_player_holy_site_relic_context_v1": "allow_private_player_holy_site_relic_context_query",
    "ck3_query_player_holy_site_v1": "allow_private_player_holy_site_query",
    "ck3_query_player_artifact_personal_use_v1": "allow_private_player_artifact_personal_use_query",
    "ck3_query_player_ghw_permissions_v1": "allow_private_player_ghw_permissions_query",
    "ck3_query_character_skill_effects_v1": "allow_private_character_skill_effects_query",
    "ck3_query_character_knight_effectiveness_v1": "allow_private_character_knight_effectiveness_query",
}
REGISTRATION_ACTION_FLAGS = {
    "opt_in_player_pilgrimage_execution": "allow_private_player_pilgrimage_execution",
    "opt_in_holy_site_creation_ui": "allow_private_player_holy_site_creation_ui",
    "opt_in_holy_site_creation_create_once": "allow_private_player_holy_site_creation_create_once",
    "opt_in_holy_site_relic_actions": "allow_private_holy_site_relic_actions",
    "opt_in_player_artifact_personal_use_actions": "allow_private_player_artifact_personal_use_actions",
    "opt_in_player_inventory_window_open": "allow_private_player_inventory_window_open",
    "opt_in_player_inventory_window_close": "allow_private_player_inventory_window_close",
    "opt_in_player_rite_creation_actions": "allow_private_player_rite_creation_actions",
}


def registration_driver(case):
    """Mirror existing public case/host permissions for factory listing only."""
    class RegistrationOnlyDriver:
        case_declared_read_only_mcp_tools = set(case.get("opt_in_read_only_mcp_tools", []))

        def capabilities(self):
            return {}

        def take_snapshot(self):
            raise RuntimeError("registration-only validation must never take a game snapshot")

        def execute_step(self, step: str, *, expected_revision: int | None = None) -> dict[str, object]:
            raise RuntimeError("registration-only validation must never submit a game action")

        def wait_for_change(self, after_revision: int, *, timeout_seconds: float) -> dict[str, object]:
            raise RuntimeError("registration-only validation must never wait on a game")

    driver = RegistrationOnlyDriver()
    driver.allow_private_holy_site_adoption_detail_query = bool({
        "ck3_query_player_holy_site_adoption_detail_v1",
        "ck3_query_player_holy_site_decision_detail_v1",
        "ck3_query_player_holy_site_decision_cooldown_v1",
    } & driver.case_declared_read_only_mcp_tools)
    for tool, name in REGISTRATION_READ_ONLY_FLAGS.items():
        setattr(driver, name, tool in driver.case_declared_read_only_mcp_tools)
    for key, name in REGISTRATION_ACTION_FLAGS.items():
        setattr(driver, name, case.get(key) is True)
    return driver


def require(value: object, message: str) -> None:
    if not value:
        raise ValueError(message)


def stock_read_only_source_evidence(tool: str, root: Path, snapshot: Path,
        native_files: Mapping[str, object], source_files: Mapping[str, object],
        profile_flags: Mapping[str, object]) -> dict[str, FilePin]:
    """Prove existing stock providers, without asserting an actual query or cache load."""
    require(tool in STOCK_READ_ONLY_CAPABILITIES, "Unreviewed stock read-only capability: " + tool)
    rule = STOCK_READ_ONLY_CAPABILITIES[tool]
    for flag in rule.required_flags:
        require(profile_flags.get(flag) == "ON", "Qualified profile lacks required stock query flag: " + flag)
    evidence: dict[str, FilePin] = {}
    for relative in rule.native_sources:
        key = NATIVE_PREFIX + relative
        path = snapshot / relative
        require(key in native_files and path.is_file() and native_files[key] == sig(path.read_bytes()),
                "Stock query provider is not an exact qualified production TU: " + key)
        evidence[key] = pin(path)
    for relative in rule.sdk_sources:
        key = SDK_PREFIX + relative
        path = root / key
        require(key in source_files and path.is_file() and source_files[key] == sig(path.read_bytes()),
                "Stock query SDK provider is outside the exact source index: " + key)
        evidence[key] = pin(path)
    if tool == "ck3_migration_pipe_diagnostics":
        path = root / HOST_RELATIVE
        require(source_files.get(HOST_RELATIVE) == sig(path.read_bytes()),
                "Stock pipe diagnostics host is outside the exact source index")
        evidence[HOST_RELATIVE] = pin(path)
    return evidence


async def registered_runtime_tool_names(case: JsonObject, host_path: Path, profile_dir: Path) -> set[str]:
    """List the real SDK plus its existing canonical-host read-only registration."""
    from xar_autoplayer.bridge.mcp_server import create_server
    driver = registration_driver(case)
    server = create_server(driver, profile_dir=profile_dir)
    tools = case.get("required_mcp_tools", [])
    require(isinstance(tools, list), "Required MCP tools must be a JSON list")
    if isinstance(tools, list) and "ck3_migration_pipe_diagnostics" in tools:
        tree = ast.parse(host_path.read_text(encoding="utf-8-sig"))
        owners = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "native_server"]
        require(len(owners) == 1, "Canonical native-server registration owner missing")
        functions = [node for node in owners[0].body if isinstance(node, ast.FunctionDef)
                     and node.name == "ck3_migration_pipe_diagnostics"]
        expected = ast.parse('''@server.tool()
def ck3_migration_pipe_diagnostics() -> dict[str, object]:
    """Inspect this harness's pipe, native hello, heartbeat and mailbox."""
    return {"pipe": driver.pipe_name, "transport_error": driver.endpoint.transport_error(),
            "diagnostics": driver.diagnostics()}
''').body[0]
        require(len(functions) == 1 and ast.dump(functions[0]) == ast.dump(expected),
                "Canonical pipe diagnostics registration differs from the reviewed read-only provider")
        # Execute only this exact existing declaration. Its body is never invoked.
        statements: list[ast.stmt] = [*functions]
        exec(compile(ast.Module(body=statements, type_ignores=[]), str(host_path), "exec"),
             {"server": server, "driver": driver})
    return {row.name for row in await server.list_tools()}


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sig(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def pin(path):
    path = Path(path).resolve()
    return {"path": str(path), **sig(path.read_bytes())}


def checked(row):
    actual = pin(row["path"])
    require(all(actual[k] == row[k] for k in ("bytes", "sha256")), "Exact input changed: " + row["path"])
    return actual


def encoded(value):
    return (json.dumps(value, separators=(",", ":"), ensure_ascii=True) + "\n").encode()


def validate_metadata_bound(output: Mapping[str, bytes], *, limit_bytes: int,
                            reserve_bytes: int) -> None:
    """Check the complete serialized package before creating its directory."""
    if type(limit_bytes) is not int or type(reserve_bytes) is not int:
        raise ValueError("Metadata budget requires exact integer byte counts")
    if limit_bytes <= 0 or reserve_bytes < 0:
        raise ValueError("Metadata budget requires a positive limit and nonnegative reserve")
    if sum(map(len, output.values())) + reserve_bytes > limit_bytes:
        raise ValueError("Complete serialized metadata exceeds its admitted byte limit")


def write_bounded_metadata(destination: Path, output: Mapping[str, bytes], *,
                           limit_bytes: int, reserve_bytes: int) -> None:
    """Write every original serialized byte after one finite capacity check."""
    validate_metadata_bound(output, limit_bytes=limit_bytes, reserve_bytes=reserve_bytes)
    destination.mkdir(parents=False)
    for name, raw in output.items():
        with (destination / name).open("xb") as stream:
            stream.write(raw)


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def classify(path: str) -> set[str]:
    """Categories determine actual required qualification, never automatic credit."""
    require("\\" not in path and not path.startswith("/") and ":" not in path
            and all(v not in {"", ".", ".."} for v in path.split("/")), "Unsafe changed path")
    name = path.rsplit("/", 1)[-1]
    if path.startswith(("tools/g2_saved_campaign/", "_runtime/", "tools/ck3_obs_")):
        return set()  # version corpus only; actual selected dependency check below
    if path == HOST_RELATIVE:
        return {"shared_host"}
    if path.startswith(NATIVE_PREFIX):
        # Even BOM-only C++/headers/CMake changes are visible changes. A fresh
        # global qualified native base, rather than a Python compatibility claim,
        # must absorb them before this lightweight builder is used.
        if not path.endswith((".py", ".md")):
            return {"new_native_base_required"}
        if path.endswith(".md"):
            return set()
        return {"shared_host"}
    if path.startswith(SDK_PREFIX):
        if path in GENERIC_DECISION_CONTRACTS:
            return {"shared_sdk_delta"}
        if name in CRITICAL_TRANSPORTS:
            return {"pilgrimage_wire_seam"}
        if any(value in name for value in ("exact_day", "speed_configuration", "application_main_clock")):
            return {"exact_day_clock", "pilgrimage_wire_seam"}
        if any(value in name for value in ("ingame_decision", "rite_governance", "religion_context", "holy_site")):
            return {"hof_terms_confirm_seam"}
        return {"shared_sdk_delta"}
    if path.startswith("tools/ck3_mod_acceptance_cases/"):
        chains = {"case_hooks"}
        if any(value in name for value in ("journey", "event", "health", "interrupt")):
            chains.add("event_policy")
        return chains
    if name.startswith("test_") or path.startswith(TEST_PREFIX):
        return {"changed_tests"}
    if path.startswith("tools/") and name.startswith(("ck3_mod_acceptance", "build_normal_exit", "fixture_engine")):
        return {"public_control"}
    if name == "recorder_job.py":
        return {"recording_control"}
    if path.startswith(("docs/", "promo/")) or Path(name).suffix in {".md", ".bbcode"}:
        return set()
    return {"other_source_delta"}


def load_base(runtime_path):
    runtime = read(runtime_path)
    require(runtime["schema"] == "ck3-mod-acceptance-runtime-v1", "Shared runtime schema required")
    manifest = read(checked(runtime["manifest"])["path"])
    require(manifest["schema"] == "ck3-mod-acceptance-shared-runtime-v1", "Shared manifest schema required")
    refs = {}
    for name in ("host", "source_index", "native_source_index"):
        row = manifest[name]
        refs[name] = {"path": runtime["paths"][row["path_key"]], "bytes": row["bytes"], "sha256": row["sha256"]}
        checked(refs[name])
    for name in ("dll", "injector"):
        row = manifest["native"][name]
        refs[name] = {"path": runtime["paths"][row["path_key"]], "bytes": row["bytes"], "sha256": row["sha256"]}
        checked(refs[name])
    source = read(refs["source_index"]["path"])
    native = read(refs["native_source_index"]["path"])
    require(source.get("schema") == "ck3-common-source-index-v1" and isinstance(source.get("files"), dict)
            and native.get("schema") == "ck3-common-native-source-index-v1" and isinstance(native.get("files"), dict),
            "Frozen common source-index contracts required")
    return runtime, manifest, refs, source


def qualify(chain, path, commit, root, changed_paths, machine, archive_context=None):
    value = read(path)
    require(value.get("machine_id") == machine and value.get("source_commit") == commit,
            "Actual changed-chain receipt must bind this new Root commit: " + chain)
    exit_keys = [k for k in ("exit_code", "original_wait_returncode") if k in value]
    require(exit_keys and all(type(value[k]) is int and value[k] == 0 for k in exit_keys),
            "Actual zero exit required: " + chain)
    require(value.get("result") == "PASS" and type(value.get("skipped")) is int and value["skipped"] == 0,
            "Explicit PASS and zero skipped required: " + chain)
    if chain == "pilgrimage_wire_seam":
        groups = value.get("test_groups")
        require(isinstance(groups, list) and len(groups) == 3 and all(type(n) is int for n in groups)
                and groups[0] >= 20 and groups[1] == 11 and groups[2] == 6
                and value.get("tests_run") == sum(groups)
                and value.get("wrong_SDK_imports") == [] and value.get("source_or_wire_changed_during_test") == [],
                "Actual current-Root portable+11+6 seam receipt required; added portable tests are not a failure")
        rows = value.get("critical_source_pins", [])
    else:
        require(chain in value.get("covered_chains", []), "Receipt does not cover the changed chain: " + chain)
        require(type(value.get("tests_run")) is int and value["tests_run"] > 0, "Actual finite tests required")
        rows = value.get("source_pins", [])
    indexed = {}
    for row in rows:
        checked(row)
        path_value = Path(row["path"]).resolve()
        if path_value.is_relative_to(root):
            indexed[path_value.relative_to(root).as_posix()] = row
    retired = archive_context.retired_paths(root, commit) if archive_context else frozenset()
    relevant = [p for p in changed_paths if p not in retired and chain in classify(p)]
    if chain == "pilgrimage_wire_seam":
        critical_paths = {SDK_PREFIX + "xar_autoplayer/bridge/" + name for name in CRITICAL_TRANSPORTS}
        require(critical_paths <= set(indexed), "Current SDK seam receipt must pin all eight actual critical SDK files")
        # Clock implementation pins belong to its actual focused clock suite;
        # the companion SDK tests validate the unchanged wire/Driver/MCP chain.
        relevant = [path for path in relevant if path in critical_paths]
    require(all(path in indexed for path in relevant), "Receipt is missing a changed-chain source pin: " + chain)
    return pin(path)


def apply_delta(delta_path, runtime_path, manifest, source, root, commit, archive_context=None):
    value = read(delta_path)
    require(value.get("schema") in {"ck3-shared-source-delta-v1", "faith-next-shared-source-delta-v1"}
            and value.get("machine_id") == manifest["machine_id"]
            and value.get("base_source_commit") == manifest["source_commit"]
            and value.get("source_commit") == commit
            and value.get("complete_changed_paths_declared_by_Root") is True, "Exact complete Root source delta required")
    checked(value["base_runtime"])
    require(Path(value["base_runtime"]["path"]).resolve() == runtime_path.resolve(), "Delta belongs to another base runtime")
    checked(value["Root_diff_receipt"])
    checked(value["Root_diff_paths"])
    root_receipt = read(value["Root_diff_receipt"]["path"])
    require(root_receipt.get("machine_id") == manifest["machine_id"]
            and root_receipt.get("base_commit") == manifest["source_commit"] and root_receipt.get("source_commit") == commit
            and root_receipt.get("complete_changed_paths") is True and root_receipt.get("working_tree_clean") is True
            and root_receipt.get("untracked_runtime_source_inputs_checked") is True
            and root_receipt.get("observed_at_utc") and isinstance(root_receipt.get("argv"), list)
            and manifest["source_commit"] in root_receipt["argv"] and commit in root_receipt["argv"]
            and type(root_receipt.get("exit_code")) is int and root_receipt["exit_code"] == 0
            and root_receipt.get("paths_sha256") == value["Root_diff_paths"]["sha256"], "Root complete committed diff evidence differs")
    require(all(type(root_receipt[key]) is int and root_receipt[key] == 0
                for key in ("exit_code", "original_wait_returncode") if key in root_receipt),
            "Contradictory Root complete-diff exit codes")
    actual_names = Path(value["Root_diff_paths"]["path"]).read_text(encoding="utf-8-sig").splitlines()
    changes = value["changes"]
    require(sorted(actual_names) == sorted(row["path"] for row in changes)
            and len(changes) == len({row["path"] for row in changes}), "Delta omitted or duplicated actual Root diff paths")
    require(("archive_relocations" in value) == (archive_context is not None),
            "Optional archive contract requires its validated shared context")
    retired = archive_context.retired_paths(root, commit, delta_path) if archive_context else frozenset()
    files = dict(source["files"])
    required = set()
    for row in changes:
        relative = row["path"]
        if relative not in retired:
            required.update(classify(relative))
        require(row["before"] == files.get(relative), "Before raw signature differs from frozen global index: " + relative)
        current = (root / relative).resolve()
        require(current.is_relative_to(root), "Changed source escaped Root")
        after = {k: pin(current)[k] for k in ("bytes", "sha256")} if current.is_file() else None
        require(after == row["after"], "Current changed source differs from frozen delta: " + relative)
        require(after is not None or row["before"] is None or relative in retired,
                "Removing an indexed implementation requires a separately qualified full shared base; deletion is outside this lightweight contract")
        if after is None:
            files.pop(relative, None)
        elif relative.endswith(".py") and (relative.startswith((SDK_PREFIX, "tools/")) or relative == HOST_RELATIVE or relative.endswith("recorder_job.py")):
            files[relative] = after
    required.discard("changed_tests")
    return files, required, [row["path"] for row in changes]


FORBIDDEN_OLD_FLAGS = (
    "XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_STAGE5_START_PRIVATE_V1",
    "XAR_CK3_ENABLE_G2_ACTIVITY_COST_SLOT12_PASSIVE_PRIVATE_V1",
    "XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_FEAST_FULL_COST_PRIVATE_V1",
    "XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_GOLD_COST_PRIVATE_V1",
    "XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_CANSTART_PRIVATE_V1",
)


def safe_relative(value):
    require(isinstance(value, str) and value and "\\" not in value and ":" not in value
            and not value.startswith("/") and all(p not in {"", ".", ".."} for p in value.split("/")),
            "Safe native relative path required")
    return value


def zero_execution(ref, machine, executable=None):
    checked(ref)
    result = read(ref["path"])
    require(result.get("machine_id") == machine, "Actual execution machine differs")
    require(type(result.get("original_wait_returncode")) is int and result["original_wait_returncode"] == 0
            and result.get("stopped_reason") is None and result.get("started_at_utc")
            and result.get("finished_at_utc"), "Actual original finite Popen.wait zero required")
    require(result.get("game_started_or_attached") is False
            and result.get("actual_live_business_qualified") is False, "Offline build/fixture scope required")
    checked(result["log"])
    if executable:
        argv = result.get("argv")
        require(isinstance(argv, list) and argv and all(isinstance(arg, str) and arg for arg in argv)
                and argv[0] == executable["path"], "Fixture execution does not bind exact executable")
    return result


def previous_profile(manifest, previous_dll):
    found = []
    for cap in manifest.get("capabilities", {}).values():
        ref = cap.get("actual_production_freeze") or cap.get("actual_B5_production_freeze")
        if not ref or ref in found:
            continue
        checked(ref)
        freeze = read(ref["path"])
        require((freeze.get("published_dll") or freeze.get("published_DLL")) == previous_dll,
                "Previous global production freeze DLL differs")
        checked(freeze["profile"])
        found.append(ref)
    require(found, "Previous global compiled profile identity is missing")
    profiles = [read(read(ref["path"])["profile"]["path"]) for ref in found]
    require(all(row["flags"] == profiles[0]["flags"] for row in profiles), "Previous global profiles conflict")
    return profiles[0]


def qualified_execution_packets(ref, fixtures, snapshot_root, machine):
    checked(ref)
    value = read(ref["path"])
    require(value.get("machine_id") == machine and value.get("actual_live_business_qualified") is False,
            "Machine-bound actual owned serializer outputs required")
    for name in ("source", "executable", "execution", "provenance"):
        checked(value[name])
    require(Path(value["source"]["path"]).resolve().is_relative_to(snapshot_root),
            "Execution serializer fixture source is outside the actual frozen native snapshot")
    matching = [row for row in fixtures if row["executable"] == value["executable"] and row["execution"] == value["execution"]]
    require(len(matching) == 1, "Execution wire emitter differs from actual qualified finite fixture")
    execution = zero_execution(value["execution"], machine, value["executable"])
    packets = value.get("packets", [])
    names = {"read.json", "can-select-false.json", "quote-dynamic-index.json", "start-pending.json",
             "start-unknown.json", "post-pending.json", "post-full-generation.json", "quote-unavailable.json",
             "hajj-read.json", "hajj-quote.json", "hajj-start.json",
             "worldly-read.json", "worldly-quote.json", "worldly-start.json"}
    require(len(packets) == len(names) and {Path(row["path"]).name for row in packets} == names,
            "All fourteen actual production-serializer output packets are required")
    folder = Path(value["provenance"]["path"]).resolve().parent
    require(Path(value["provenance"]["path"]).name == "PROVENANCE.json"
            and len(execution["argv"]) == 2 and Path(execution["argv"][1]).resolve() == folder,
            "Actual finite emitter must have used this unique output directory")
    expected = {Path(value["provenance"]["path"]).resolve()}
    for row in packets:
        checked(row)
        packet_path = Path(row["path"]).resolve()
        require(packet_path.parent == folder and isinstance(read(packet_path), dict), "Exact JSON object packet required")
        expected.add(packet_path)
    require(set(folder.iterdir()) == expected, "Wire output directory contains omitted or unexpected files")
    provenance = read(value["provenance"]["path"])
    require(provenance.get("owned_result_dtos") is True and provenance.get("game_queried") is False
            and provenance.get("native_runtime_qualified") is False, "Owned result DTO output cannot imply live qualification")
    return {"ref": ref, "folder": str(folder)}


def select_profile_expansion_contract(registry, contract_id=None):
    """Keep the original single-contract format and select explicit later versions."""
    if contract_id is None:
        contract_id = "ck3-12004-five-gate-native-profile-v1"
    if registry.get("contract_id") == contract_id:
        contract = {key: value for key, value in registry.items() if key != "additional_contracts"}
    else:
        contract = registry.get("additional_contracts", {}).get(contract_id)
    require(isinstance(contract, dict)
            and contract.get("schema") == "ck3-native-profile-expansion-contract-v1"
            and contract.get("contract_id") == contract_id,
            "Unknown reviewed profile expansion contract: " + str(contract_id))
    return contract


def profile_expansion_contract(value, refs, root, commit, machine, old_profile, profile, *, require_current_contract_pin=False):
    """A flag change needs a source-reviewed contract plus exact actual receipts."""
    if profile.get("flags") == old_profile.get("flags") and not value.get("profile_expansion"):
        return None
    require(value.get("profile_expansion"),
            "This public native refresh preserves the prior reviewed full feature profile; profile expansion needs separate review")
    ref = checked(value["profile_expansion"])
    actual = read(ref["path"])
    require(actual.get("schema") == "ck3-native-profile-expansion-v1"
            and actual.get("machine_id") == machine and actual.get("source_commit") == value["source_commit"]
            and actual.get("actual_live_business_qualified") is False,
            "Profile expansion must bind the actual final native compile commit and machine")
    contract_ref = actual["contract"]
    if require_current_contract_pin:
        checked(contract_ref)
    contract_path = (root / PROFILE_EXPANSION_RELATIVE).resolve()
    require(Path(contract_ref["path"]).resolve() == contract_path,
            "Profile expansion contract must be the common committed source contract")
    committed = subprocess.run(["git", "-c", "core.longpaths=true", "show", value["source_commit"] + ":" + PROFILE_EXPANSION_RELATIVE],
                               cwd=root, capture_output=True, check=True).stdout
    require(sig(committed) == {k: contract_ref[k] for k in ("bytes", "sha256")},
            "Profile expansion contract differs from the actual native compile commit")
    # A later registry append must not invalidate the original compile commit's pin.
    contract = select_profile_expansion_contract(json.loads(committed.decode("utf-8-sig")), actual.get("contract_id"))
    checked(actual["previous_profile"])
    reviewed_before = read(actual["previous_profile"]["path"])
    require(reviewed_before.get("flags") == contract.get("before_flags")
            and (reviewed_before == old_profile or old_profile.get("flags") == profile.get("flags")),
            "Profile expansion prior profile differs")
    for name in ("profile", "snapshot", "configured_scope", "production_freeze"):
        require(actual.get(name) == refs[name], "Profile expansion actual pin differs: " + name)
    require(actual.get("fixture_results") == value.get("fixture_results"),
            "Profile expansion finite execution pins differ")
    expected = dict(reviewed_before["flags"])
    changes = contract.get("flag_changes", {})
    require(changes, "Empty profile expansion cannot authorize changed flags")
    for name, change in changes.items():
        before = change["before"]
        require((name not in expected) if before is None else expected.get(name) == before,
                "Reviewed profile expansion prior flag differs: " + name)
        expected[name] = change["after"]
    require(profile.get("flags") == expected, "Profile expansion changes flags outside the reviewed exact delta")
    return {"ref": ref, "actual": actual, "contract": contract}


def profile_expansion_scope(expansion, production, targets, snapshot_root, indexed, fixtures, fixture_link_owners=None):
    """Read actual File API bodies/macros; planned counts alone grant no credit."""
    if expansion is None:
        return
    contract = expansion["contract"]
    names = {row["name"]: key for key, row in targets.items()}

    def compiled(target):
        result = []
        for src in target.get("sources", []):
            if src.get("compileGroupIndex") is None:
                continue
            path = Path(src["path"])
            path = path.resolve() if path.is_absolute() else (snapshot_root / path).resolve()
            require(path.is_relative_to(snapshot_root), "Expanded profile TU escapes the frozen snapshot")
            relative = path.relative_to(snapshot_root).as_posix()
            require(relative in indexed, "Expanded profile TU is missing its actual source pin")
            groups = target.get("compileGroups", [])
            index = src["compileGroupIndex"]
            require(type(index) is int and 0 <= index < len(groups), "Expanded profile TU compile group is missing")
            defines = {row["define"] for row in groups[index].get("defines", [])}
            result.append((relative, defines))
        return result

    actual_sources = {row["name"]: [relative for relative, _ in compiled(row)] for row in production.values()}
    require({key: len(rows) for key, rows in actual_sources.items()} == contract["production_TUs"],
            "Expanded profile production TU counts differ from reviewed contract")
    require({key: sorted(rows) for key, rows in actual_sources.items()}
            == {key: sorted(rows) for key, rows in contract["production_source_lists"].items()},
            "Expanded profile production source bodies differ from reviewed contract")
    for row in contract["production_macro_contracts"]:
        matches = [defines for relative, defines in compiled(targets[names[row["target"]]])
                   if relative == row["native_relative"]]
        require(len(matches) == 1 and set(row["present"]) <= matches[0]
                and not (set(row["absent"]) & {value.split("=", 1)[0] for value in matches[0]}),
                "Expanded profile per-TU present/absent macros differ: " + row["native_relative"])
    contracts = {row["target"]: row for row in contract["fixture_contracts"]}
    require(set(contracts) == {row["target"] for row in fixtures} == set(contract["fixture_sources"]),
            "Expanded profile exact reviewed finite target set differs")
    bodies = set()
    for name, row in contracts.items():
        target = targets[names[name]]
        sources = compiled(target)
        require(len(sources) == row["translation_units"]
                and sorted(relative for relative, _ in sources) == sorted(contract["fixture_sources"][name]),
                "Expanded profile fixture source bodies differ: " + name)
        for _, defines in sources:
            require(set(row.get("required_defines", [])) <= defines
                    and not (set(row.get("forbidden_defines", [])) & defines),
                    "Expanded profile fixture compile definitions differ: " + name)
        pending, closure = [names[name]], set()
        while pending:
            key = pending.pop()
            if key in closure:
                continue
            closure.add(key)
            pending.extend(dep["id"] for dep in targets[key].get("dependencies", []) if dep["id"] in targets)
        expected_closure = set(row["dependency_targets"]) | (fixture_link_owners or {}).get(name, set())
        require({targets[key]["name"] for key in closure} == expected_closure,
                "Expanded profile fixture dependency closure differs: " + name)
        bodies.update(relative for relative, _ in sources)
        bodies.update(contract.get("fixture_included_bodies", {}).get(name, []))
    expected = {relative: indexed[relative] for relative in sorted(bodies)}
    require(expansion["actual"].get("fixture_source_bindings") == expected,
            "Expanded profile finite direct/included body pins differ from actual frozen source")


def fixture_object_inputs(target_value: object, snapshot_root: Path, build_root: Path) -> set[Path]:
    """External objects are File API sources or explicit raw linker inputs."""
    target = native_successor.obj(target_value)
    found: set[Path] = set()

    def add(value: object, relative_root: Path) -> None:
        path = Path(native_successor.string(value))
        if path.suffix.lower() in {".obj", ".o"}:
            found.add(path.resolve() if path.is_absolute() else (relative_root / path).resolve())

    for raw in native_successor.arr(target.get("sources", [])):
        source = native_successor.obj(raw)
        if source.get("compileGroupIndex") is None:
            add(source["path"], snapshot_root)
    for raw in native_successor.arr(native_successor.obj(target.get("link", {})).get("commandFragments", [])):
        fragment = native_successor.obj(raw)
        for word in shlex.split(native_successor.string(fragment["fragment"]), posix=False):
            add(word.strip('"'), build_root)
    return found


class FixtureLinkSupportResult(TypedDict):
    ref: native_successor.Pin
    fixture_production_targets: dict[str, set[str]]


def qualified_configured_fixture_links(
    support_value: object, ref: native_successor.Pin, machine: str, native_commit: str,
    scope_value: object, indexed_value: object, production_value: object,
    targets_value: object, fixtures_value: object, model_value: object,
    snapshot_root: Path, build_root: Path, reply: Path,
    actual_inputs: dict[str, set[Path]],
    noncompiled_replay: object = None,
) -> FixtureLinkSupportResult:
    """Validate configured-to-physical objects against original production and link evidence."""
    support = native_successor.obj(support_value)
    scope = native_successor.obj(scope_value)
    indexed = native_successor.obj(indexed_value)
    production = native_successor.obj(production_value)
    targets = native_successor.obj(targets_value)
    model = native_successor.obj(model_value)
    fixtures = [native_successor.obj(item) for item in native_successor.arr(fixtures_value)]
    declared = native_successor.obj(support.get("fixtures"))
    file_api = native_successor.obj(support.get("fixture_file_api"))
    links = native_successor.obj(support.get("actual_links"))
    expected_names = set(actual_inputs)
    native_successor.require(set(declared) == set(file_api) == set(links) == expected_names,
                             "Fixture raw-object target set differs from actual File API")
    entries = native_successor.obj(native_successor.arr(model["configurations"])[0])
    target_files = {native_successor.string(row["id"]): reply / safe_fixture_relative(row["jsonFile"])
                    for raw in native_successor.arr(entries["targets"])
                    for row in [native_successor.obj(raw)]}
    named = {native_successor.string(native_successor.obj(target)["name"]): key
             for key, target in targets.items()}
    commands_ref = native_successor.checked(scope["compile_commands"])
    commands_raw: object = json.loads(Path(commands_ref["path"]).read_text(encoding="utf-8-sig"))
    commands = [native_successor.obj(row) for row in native_successor.arr(commands_raw)]
    all_paths = set().union(*actual_inputs.values())
    objects: list[native_successor.FixtureProductionObjectBinding] = []
    physical: dict[Path, native_successor.Pin] = {}
    owners: dict[Path, str] = {}
    production_names = {native_successor.string(native_successor.obj(row)["name"]): native_successor.obj(row)
                        for row in production.values()}
    for raw in native_successor.arr(support.get("objects")):
        row = native_successor.obj(raw)
        native_successor.require(set(row) == {"configured_object", "object", "production_target", "native_relative",
                                             "source", "configured_compile_command_index"},
                                 "Exact configured fixture object fields required")
        configured = native_successor.string(row["configured_object"])
        path = Path(configured)
        native_successor.require(path.is_absolute() and path == path.resolve() and path in all_paths and path not in physical,
                                 "Fixture support configured set has omitted, duplicate or unlinked objects")
        name = native_successor.string(row["production_target"])
        relative = safe_fixture_relative(row["native_relative"])
        native_successor.require(name in production_names and path.is_relative_to(build_root / "CMakeFiles" / (name + ".dir")),
                                 "Fixture support object is not an actual selected production target output")
        source = native_successor.checked(row["source"])
        native_successor.require(relative in indexed and source == indexed[relative],
                                 "Fixture support source pin differs from actual frozen source")
        compiled = set()
        for source_value in native_successor.arr(production_names[name].get("sources", [])):
            source_row = native_successor.obj(source_value)
            if source_row.get("compileGroupIndex") is not None:
                source_path = Path(native_successor.string(source_row["path"]))
                compiled.add(source_path.resolve() if source_path.is_absolute() else (snapshot_root / source_path).resolve())
        native_successor.require(Path(source["path"]).resolve() in compiled,
                                 "Fixture support body is not compiled in its selected production target")
        command_index = native_successor.integer(row["configured_compile_command_index"])
        native_successor.require(command_index < len(commands), "Configured fixture compile-command index is out of range")
        command = commands[command_index]
        native_successor.require(Path(native_successor.string(command["directory"])).resolve() == build_root
            and Path(native_successor.string(command["file"])).resolve() == Path(source["path"]).resolve()
            and Path(native_successor.string(command["output"])).resolve() == path,
            "Fixture support object/source/compile command differs from actual production compilation")
        actual = native_successor.checked(row["object"])
        native_successor.require(actual not in physical.values(), "Fixture physical objects must have distinct identities")
        physical[path], owners[path] = actual, name
        objects.append({"configured_object": configured, "object": actual, "production_target": name,
                        "native_relative": relative, "source": source, "configured_compile_command_index": command_index})
    native_successor.require(set(physical) == all_paths,
                             "Fixture support configured set has omitted, duplicate or unlinked objects")
    config = native_successor.read(Path(native_successor.checked(support["producer_config"])["path"]))
    native_successor.require(config.get("source_commit") == native_commit and config.get("machine_id") == machine,
                             "Fixture production config identity differs")
    proof = native_successor.verified_fixture_object_bindings(config, sorted(str(path) for path in all_paths),
        noncompiled_replay=noncompiled_replay)
    native_successor.require(objects == proof.objects, "Fixture objects differ from verified original production bindings")
    for field, expected in (("production_plan", proof.production_plan),
                            ("incremental_production_result", proof.incremental_production_result),
                            ("baseline_compile_commands", proof.baseline_compile_commands),
                            ("original_dependencies", proof.original_dependencies)):
        native_successor.require(native_successor.checked(support[field]) == expected,
                                 "Fixture production provenance differs: " + field)
    parser_module = native_successor.load_shared(HERE / "build_native_flag_successor.py", "fixture_link_windows_arguments")
    arguments: object = getattr(parser_module, "windows_args", None)
    if not isinstance(arguments, native_successor.WindowsArguments):
        raise ValueError("Shared Windows linker argument parser unavailable")
    for name, paths in actual_inputs.items():
        key = named[name]
        native_successor.require(native_successor.checked(file_api[name]) == native_successor.pin(target_files[key]),
                                 "Fixture raw-object link File API pin differs: " + name)
        pins = [native_successor.checked(item) for item in native_successor.arr(declared[name])]
        expected_pins = [physical[path] for path in sorted(paths)]
        native_successor.require(pins == expected_pins, "Fixture raw-object links differ from actual File API: " + name)
        fixture = next(row for row in fixtures if row["target"] == name)
        executable = native_successor.checked(fixture["executable"])
        execution = native_successor.read(Path(native_successor.checked(links[name])["path"]))
        native_successor.require(execution.get("machine_id") == machine and execution.get("source_commit") == native_commit
            and type(execution.get("original_wait_returncode")) is int and execution["original_wait_returncode"] == 0
            and execution.get("stopped_reason") is None and bool(execution.get("started_at_utc"))
            and bool(execution.get("finished_at_utc")) and execution.get("game_started_or_attached") is False
            and execution.get("actual_live_business_qualified") is False,
            "Actual original finite fixture link Popen.wait zero required")
        native_successor.checked(execution["log"])
        response = [native_successor.checked(item) for item in native_successor.arr(execution["response_files"])]
        argv = native_successor.strings(execution["argv"])
        native_successor.require(len(response) == 1 and len(argv) == 2 and Path(argv[0]).is_absolute()
            and Path(argv[0]).name.lower() in {"link.exe", "lld-link.exe"}
            and argv[1] == "@" + response[0]["path"]
            and Path(native_successor.string(execution["cwd"])).resolve() == build_root,
            "Actual fixture link must bind its exact linker response file and build directory")
        words = arguments(Path(response[0]["path"]).read_text(encoding="utf-8"))
        native_successor.require(not any(word.startswith("@") for word in words), "Nested fixture linker response files are unsupported")
        linked = [Path(word).resolve() for word in words if Path(word).suffix.lower() in {".obj", ".o"}]
        target = native_successor.obj(targets[key])
        own_sources = set()
        for raw in native_successor.arr(target.get("sources", [])):
            source_row = native_successor.obj(raw)
            if source_row.get("compileGroupIndex") is not None:
                item = Path(native_successor.string(source_row["path"]))
                own_sources.add(item.resolve() if item.is_absolute() else (snapshot_root / item).resolve())
        own = {Path(native_successor.string(command["output"])).resolve() for command in commands
               if Path(native_successor.string(command["file"])).resolve() in own_sources
               and Path(native_successor.string(command["output"])).resolve().is_relative_to(build_root / "CMakeFiles" / (name + ".dir"))}
        for item in own:
            native_successor.pin(item)
        expected_objects = {Path(physical[path]["path"]) for path in paths} | own
        destinations = [Path(word[5:]).resolve() for word in words if word.upper().startswith("/OUT:")]
        native_successor.require(len(linked) == len(set(linked)) and set(linked) == expected_objects
            and destinations == [Path(executable["path"])], "Actual fixture RSP object map or configured EXE differs")
    return {"ref": ref, "fixture_production_targets": {name: {owners[path] for path in paths}
                                                       for name, paths in actual_inputs.items()}}


def safe_fixture_relative(value: object) -> str:
    """Parse a source/File API relative path without accepting traversal or aliases."""
    text = native_successor.string(value)
    native_successor.require("\\" not in text and ":" not in text and not text.startswith("/")
        and all(part not in {"", ".", ".."} for part in text.split("/")), "Safe native relative path required")
    return text


def qualified_fixture_link_support(
    value_input: object, refs_input: object, machine: str, scope_input: object,
    snapshot_root: Path, build_root: Path, indexed_input: object, production_input: object,
    targets_input: object, fixtures_input: object, reply: Path, model_input: object,
    noncompiled_replay: object = None,
) -> FixtureLinkSupportResult | None:
    value, refs = native_successor.obj(value_input), native_successor.obj(refs_input)
    scope, indexed = native_successor.obj(scope_input), native_successor.obj(indexed_input)
    production, targets = native_successor.obj(production_input), native_successor.obj(targets_input)
    model = native_successor.obj(model_input)
    fixtures = [native_successor.obj(row) for row in native_successor.arr(fixtures_input)]
    names = {native_successor.string(native_successor.obj(target)["name"]): key for key, target in targets.items()}
    actual_inputs = {native_successor.string(row["target"]): fixture_object_inputs(
        targets[names[native_successor.string(row["target"])]], snapshot_root, build_root) for row in fixtures}
    actual_inputs = {name: paths for name, paths in actual_inputs.items() if paths}
    ref = value.get("fixture_link_support")
    if not actual_inputs and not ref:
        return None
    native_successor.require(ref and actual_inputs, "Actual external fixture objects need their exact source-bound link-support receipt")
    ref = native_successor.checked(ref)
    support = native_successor.read(Path(ref["path"]))
    native_successor.require(support.get("schema") in ("ck3-fixture-production-object-link-support-v1", "ck3-fixture-production-object-link-support-v2")
            and support.get("machine_id") == machine and support.get("source_commit") == value["source_commit"]
            and support.get("actual_live_business_qualified") is False,
            "Fixture link support must bind this actual native compile source and machine")
    native_successor.require(support.get("configured_scope") == refs["configured_scope"]
            and support.get("production_freeze") == refs["production_freeze"]
            and support.get("fixture_results") == fixtures,
            "Fixture link support actual scope/freeze/finite execution pins differ")
    if support["schema"] == "ck3-fixture-production-object-link-support-v2":
        return qualified_configured_fixture_links(support, ref, machine, native_successor.string(value["source_commit"]),
            scope, indexed, production, targets, fixtures, model, snapshot_root, build_root, reply, actual_inputs,
            noncompiled_replay)
    declared = native_successor.obj(support.get("fixtures", {}))
    file_api = native_successor.obj(support.get("fixture_file_api", {}))
    native_successor.require(set(declared) == set(file_api) == set(actual_inputs), "Fixture raw-object target set differs from actual File API")
    configuration = native_successor.obj(native_successor.arr(model["configurations"])[0])
    target_files = {native_successor.string(row["id"]): reply / safe_fixture_relative(row["jsonFile"])
                    for raw in native_successor.arr(configuration["targets"]) for row in [native_successor.obj(raw)]}
    for name, paths in actual_inputs.items():
        native_successor.require(native_successor.checked(file_api[name]) == native_successor.pin(target_files[names[name]]),
                "Fixture raw-object link File API pin differs: " + name)
        declared_rows = [native_successor.parse_pin(row) for row in native_successor.arr(declared[name])]
        native_successor.require(len(declared_rows) == len(paths)
                and {Path(row["path"]).resolve() for row in declared_rows} == paths,
                "Fixture raw-object links differ from actual File API: " + name)
    objects = [native_successor.obj(row) for row in native_successor.arr(support.get("objects", []))]
    all_paths = set().union(*actual_inputs.values())
    native_successor.require(len(objects) == len(all_paths)
            and {Path(native_successor.parse_pin(row["object"])["path"]).resolve() for row in objects} == all_paths,
            "Fixture support object set has omitted, duplicate or unlinked objects")
    command_ref = native_successor.checked(scope["compile_commands"])
    commands_value: object = json.loads(Path(command_ref["path"]).read_text(encoding="utf-8-sig"))
    commands = native_successor.arr(commands_value)
    production_names = {native_successor.string(native_successor.obj(target)["name"]): native_successor.obj(target)
                        for target in production.values()}
    checked_objects: dict[Path, native_successor.Pin] = {}
    for row in objects:
        expected_object = native_successor.parse_pin(row["object"])
        obj = native_successor.pin(Path(expected_object["path"]))
        native_successor.require(obj == expected_object, "Exact input changed: " + expected_object["path"])
        path = Path(obj["path"]).resolve()
        name, relative = native_successor.string(row["production_target"]), safe_fixture_relative(row["native_relative"])
        native_successor.require(name in production_names and path.is_relative_to(build_root / "CMakeFiles" / (name + ".dir")),
                "Fixture support object is not an actual selected production target output")
        source = native_successor.checked(row["source"])
        native_successor.require(relative in indexed and source == indexed[relative], "Fixture support source pin differs from actual frozen source")
        compiled: set[Path] = set()
        for item_value in native_successor.arr(production_names[name].get("sources", [])):
            item = native_successor.obj(item_value)
            if item.get("compileGroupIndex") is not None:
                item_path = Path(native_successor.string(item["path"]))
                compiled.add(item_path.resolve() if item_path.is_absolute() else (snapshot_root / item_path).resolve())
        native_successor.require(Path(source["path"]).resolve() in compiled, "Fixture support body is not compiled in its selected production target")
        command = native_successor.obj(row["actual_compile_command"])
        native_successor.require(command in commands and Path(native_successor.string(command["directory"])).resolve() == build_root
                and Path(native_successor.string(command["file"])).resolve() == Path(source["path"]).resolve()
                and Path(native_successor.string(command["output"])).resolve() == path,
                "Fixture support object/source/compile command differs from actual production compilation")
        checked_objects[path] = obj
    for rows in declared.values():
        native_successor.require(all(row == checked_objects[Path(row["path"]).resolve()]
            for raw in native_successor.arr(rows) for row in [native_successor.parse_pin(raw)]),
                "Fixture support target object pins differ from the actual hashed object set")
    owners = {Path(native_successor.parse_pin(row["object"])["path"]).resolve(): native_successor.string(row["production_target"])
              for row in objects}
    return {"ref": ref, "fixture_production_targets": {
        name: {owners[path] for path in paths} for name, paths in actual_inputs.items()}}


def qualify_native(path, root, commit, machine, previous_dll, previous_manifest, native_source_checkout_binding=None, native_shared_python_host_delta=None):
    value = read(path)
    native_commit = value.get("source_commit", "")
    require(value.get("schema") == "ck3-qualified-native-build-v1" and value.get("machine_id") == machine
            and re.fullmatch("[0-9a-f]{40}", native_commit) and value.get("actual_live_business_qualified") is False,
            "Exact current committed qualified-native-build receipt required")
    refs = {name: checked(value[name]) for name in (
        "delivery", "snapshot", "profile", "configured_scope", "source_verification", "production_freeze",
        "original_dll", "published_dll", "production_build_receipt", "defender_binding")}
    delivery = read(refs["delivery"]["path"])
    require(delivery.get("machine_id") == machine and delivery.get("actual_live_business_qualified") is False
            and delivery.get("all_original_build_and_fixture_Popen_waits_recorded") is True,
            "Original completed build/fixture delivery is required")
    for source_key, key in (("snapshot", "snapshot"), ("profile", "profile"), ("scope", "configured_scope"),
                            ("source_verification", "source_verification"), ("production_freeze", "production_freeze"),
                            ("published_dll", "published_dll"), ("Defender_settings_verified", "defender_binding")):
        require(delivery.get(source_key) == refs[key], "Original delivery pin differs: " + source_key)
    freeze = read(refs["production_freeze"]["path"])
    require(freeze.get("machine_id") == machine and freeze.get("root_commit") == native_commit
            and freeze.get("no_fixture_target_in_production_dependency_closure") is True
            and freeze.get("repository_default_flags_changed") is False
            and freeze.get("game_started_or_attached") is False, "Actual unchanged-default production freeze required")
    for source_key, key in (("original_DLL", "original_dll"), ("published_DLL", "published_dll"),
                            ("build_execution", "production_build_receipt"), ("source_manifest", "snapshot"),
                            ("source_verification", "source_verification"), ("profile", "profile"), ("scope", "configured_scope")):
        require(freeze.get(source_key) == refs[key], "Production freeze pin differs: " + source_key)
    require(all(refs["original_dll"][k] == refs["published_dll"][k] for k in ("bytes", "sha256")),
            "Published production DLL differs from actual build output")
    zero_execution(refs["production_build_receipt"], machine)
    profile = read(refs["profile"]["path"])
    old_profile = previous_profile(previous_manifest, previous_dll)
    require(profile.get("machine_id") == machine and profile.get("repository_default_flags_changed") is False,
            "Actual machine-bound profile preserving repository defaults required")
    require(all(profile["flags"].get(flag) == "OFF" for flag in FORBIDDEN_OLD_FLAGS),
            "Old feast Start and unqualified cost helpers must stay OFF")
    for name in ("profile", "cmake"):
        if name in profile:
            checked(profile[name])
    snapshot = read(refs["snapshot"]["path"])
    verification = read(refs["source_verification"]["path"])
    require(snapshot.get("machine_id") == machine and snapshot.get("root_commit") == native_commit
            and verification.get("machine_id") == machine and verification.get("root_commit") == native_commit
            and verification.get("source_manifest") == refs["snapshot"], "Exact source verification identity differs")
    rows = snapshot.get("files", [])
    require(rows and snapshot.get("source_count") == len(rows)
            and verification.get("all_snapshot_files_exactly_verified") == len(rows)
            and verification.get("all_original_inputs_still_exactly_verified") == len(rows),
            "Complete frozen source verification required")
    native_root = (root / NATIVE_PREFIX).resolve()
    source_checkout = module(HERE / "ck3_mod_acceptance_native_source_binding.py",
                             "ck3_native_source_binding").qualified_native_source_checkout(
        native_source_checkout_binding, root=root, runtime_commit=commit, native_commit=native_commit,
        machine=machine, qualified_native_ref=pin(path), qualification=value,
        snapshot_ref=refs["snapshot"], snapshot=snapshot,
        native_shared_python_host_delta=native_shared_python_host_delta)
    if native_shared_python_host_delta is not None:
        require(classify(HOST_RELATIVE) == {"shared_host"}, "Canonical Python-host classification changed")
        qualify("shared_host", Path(source_checkout["shared_host_qualification"]["path"]),
                commit, root, [HOST_RELATIVE], machine)
    compile_native_root = source_checkout["native_source_base"]
    compile_repo = compile_native_root.parent.parent
    require((compile_repo / NATIVE_PREFIX).resolve() == compile_native_root,
            "Verified Native source root has an unexpected repository structure")
    expansion = profile_expansion_contract(value, refs, compile_repo, commit, machine, old_profile, profile,
                                           require_current_contract_pin=source_checkout["binding_ref"] is not None)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=root,
                            capture_output=True, text=True, check=True).stdout
    require(head == commit and not status.strip(), "Actual current Root must be clean at the exact qualified commit")
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", native_commit, commit], cwd=root, capture_output=True)
    require(ancestor.returncode == 0 or (
                ancestor.returncode == 1
                and source_checkout.get("native_compile_commit_is_ancestor") is False
                and (source_checkout.get("nonancestor_exact_tree_binding") is not None
                     and source_checkout["nonancestor_exact_tree_binding"] == source_checkout["binding_ref"]
                     or source_checkout.get("nonancestor_research_delta_binding") is not None
                     and source_checkout["nonancestor_research_delta_binding"] == source_checkout["binding_ref"])),
            "Native compile commit must be a proven ancestor or have a verified explicit exact-tree nonancestor binding")
    tracked_raw = subprocess.run(["git", "ls-files", "-z", "--", NATIVE_PREFIX], cwd=root,
                                 capture_output=True, check=True).stdout.decode("utf-8")
    tracked = {name[len(NATIVE_PREFIX):] for name in tracked_raw.split("\0") if name}
    declared_root = {row["native_relative"] for row in rows if "source" not in row}
    added_research = set(source_checkout.get("added_runtime_research_paths", ()))
    require(tracked == declared_root | added_research,
            "Frozen native manifest omitted or added current Root tracked inputs")
    snapshot_root = Path(snapshot["snapshot_native_base"]).resolve()
    indexed = {}
    for row in rows:
        relative = safe_relative(row["native_relative"])
        require(relative not in indexed, "Duplicate frozen native source")
        snapshot_input = {"path": str(snapshot_root / relative), "bytes": row["bytes"], "sha256": row["sha256"]}
        if relative == HOST_RELATIVE.removeprefix(NATIVE_PREFIX) and source_checkout.get("original_shared_host_blob"):
            snapshot_input = source_checkout["original_shared_host_blob"]
            require({key: snapshot_input[key] for key in ("bytes", "sha256")}
                    == {key: row[key] for key in ("bytes", "sha256")},
                    "Preserved original shared-host blob differs from the original Native snapshot")
        if relative == "cmake/player_pilgrimage_traits_12004.cmake" and source_checkout.get("original_fixture_cmake_blob"):
            snapshot_input = source_checkout["original_fixture_cmake_blob"]
            require({key: snapshot_input[key] for key in ("bytes", "sha256")}
                    == {key: row[key] for key in ("bytes", "sha256")},
                    "Preserved fixture CMake blob differs from the original Native snapshot")
        if relative == "CMakeLists.txt" and source_checkout.get("original_inactive_cmake_blob"):
            snapshot_input = source_checkout["original_inactive_cmake_blob"]
            require({key: snapshot_input[key] for key in ("bytes", "sha256")}
                    == {key: row[key] for key in ("bytes", "sha256")},
                    "Preserved inactive CMake blob differs from the original Native snapshot")
        if relative in source_checkout.get("original_research_blobs", {}):
            require(relative in (native_successor.NONCOMPILED_CONSUMER_RELATIVE,
                                 native_successor.HOST_TEST_COMPANION_RELATIVE),
                    "Only the reviewed refill consumer and host test may preserve non-host before blobs")
            snapshot_input = source_checkout["original_research_blobs"][relative]
            require({key: snapshot_input[key] for key in ("bytes", "sha256")}
                    == {key: row[key] for key in ("bytes", "sha256")},
                    "Preserved refill consumer blob differs from the original Native snapshot")
        current_snapshot = checked(snapshot_input)
        original = row.get("original_source_pin")
        if original:
            require(relative == "CMakeLists.txt", "Only a separately identified test-registration CMake derivative is allowed")
            require(Path(original["path"]).resolve() == compile_native_root / relative, "Original CMake source belongs to another tree")
            checked(original)
        elif "source" not in row:
            original = {"path": str(native_root / relative), "bytes": row["bytes"], "sha256": row["sha256"]}
            if relative == HOST_RELATIVE.removeprefix(NATIVE_PREFIX) and source_checkout.get("runtime_shared_host_pin"):
                original = source_checkout["runtime_shared_host_pin"]
                require(Path(original["path"]).resolve() == root / HOST_RELATIVE,
                        "Verified shared-host runtime pin is from another source path")
            if relative == "cmake/player_pilgrimage_traits_12004.cmake" and source_checkout.get("runtime_fixture_cmake_pin"):
                original = source_checkout["runtime_fixture_cmake_pin"]
                require(Path(original["path"]).resolve() == native_root / relative,
                        "Verified fixture CMake runtime pin is from another source path")
            if relative == "CMakeLists.txt" and source_checkout.get("runtime_inactive_cmake_pin"):
                original = source_checkout["runtime_inactive_cmake_pin"]
                require(Path(original["path"]).resolve() == native_root / relative,
                        "Verified inactive CMake runtime pin is from another source path")
            if relative in source_checkout.get("runtime_research_pins", {}):
                original = source_checkout["runtime_research_pins"][relative]
                require(Path(original["path"]).resolve() == native_root / relative,
                        "Verified runtime research pin is from another source path")
            checked(original)
        else:
            checked({"path": row["source"], "bytes": row["bytes"], "sha256": row["sha256"]})
        indexed[relative] = current_snapshot
    scope = read(refs["configured_scope"]["path"])
    require(scope.get("machine_id") == machine and scope.get("snapshot") == refs["snapshot"]
            and scope.get("no_fixture_in_production") is True, "Exact production File API scope required")
    checked(scope["codemodel"])
    checked(scope["index"])
    checked(scope["compile_commands"])
    reply = Path(scope["codemodel"]["path"]).parent
    model = read(scope["codemodel"]["path"])
    require(Path(model["paths"]["source"]).resolve() == snapshot_root, "File API selected another source snapshot")
    build_root = Path(model["paths"]["build"]).resolve()
    actual_targets = {row["id"]: read(reply / safe_relative(row["jsonFile"]))
                      for row in model["configurations"][0]["targets"]}
    names = {row["name"]: key for key, row in actual_targets.items()}
    require("xar_ck3_bridge" in names, "Actual shared production DLL target is missing")
    artifact_paths = lambda target: {(build_root / item["path"]).resolve() for item in target.get("artifacts", [])}
    require(Path(refs["original_dll"]["path"]).resolve() in artifact_paths(actual_targets[names["xar_ck3_bridge"]]),
            "Selected original DLL is not the actual File API production artifact")
    pending, production = [names["xar_ck3_bridge"]], {}
    while pending:
        target_id = pending.pop()
        if target_id in production:
            continue
        target = actual_targets[target_id]
        production[target_id] = target
        pending.extend(dep["id"] for dep in target.get("dependencies", []) if dep["id"] in actual_targets)
    require(not any("fixture" in row["name"].lower() for row in production.values()), "Fixture dependency entered production DLL")
    counts = {row["name"]: sum(src.get("compileGroupIndex") is not None for src in row.get("sources", []))
              for row in production.values()}
    require(counts == scope.get("production_TUs"), "Recorded production TU closure differs from actual File API")
    declared = {row["name"]: row for row in scope["targets"]}
    native_files = {}
    for target in production.values():
        require(target["name"] in declared, "Production target missing from original frozen scope")
        for key in ("type", "sources", "compileGroups", "artifacts"):
            require(declared[target["name"]].get(key, []) == target.get(key, []), "Actual File API production target changed: " + key)
        for src in target.get("sources", []):
            if src.get("compileGroupIndex") is None:
                continue
            source_path = Path(src["path"])
            resolved = source_path.resolve() if source_path.is_absolute() else (snapshot_root / source_path).resolve()
            require(resolved.is_relative_to(snapshot_root), "Production TU escapes frozen native source")
            relative = resolved.relative_to(snapshot_root).as_posix()
            require(relative in indexed and "source" not in next(row for row in rows if row["native_relative"] == relative),
                    "External baseline or unpinned source entered production DLL")
            native_files[NATIVE_PREFIX + relative] = {k: indexed[relative][k] for k in ("bytes", "sha256")}
    fixtures = value.get("fixture_results", [])
    requested = scope.get("requested_EXEs", [])
    require(fixtures and len(fixtures) == len(requested) == len(set(requested))
            and {row["target"] for row in fixtures} == set(requested), "Exact configured finite fixture set required")
    expected_delivery = [{"name": row["target"], "execution": row["execution"], "exe": row["executable"]} for row in fixtures]
    require(delivery.get("finite_tests") == expected_delivery, "Original delivery fixture pins differ")
    for row in fixtures:
        checked(row["executable"])
        require(row["target"] in names and row["target"] not in counts, "Finite test must be separate from production")
        require(Path(row["executable"]["path"]).resolve() in artifact_paths(actual_targets[names[row["target"]]]),
                "Fixture executable is not its actual configured artifact")
        zero_execution(row["execution"], machine, row["executable"])
    link_support = qualified_fixture_link_support(value, refs, machine, scope, snapshot_root, build_root,
        indexed, production, actual_targets, fixtures, reply, model, source_checkout.get("noncompiled_replay"))
    profile_expansion_scope(expansion, production, actual_targets, snapshot_root, indexed, fixtures,
                            link_support["fixture_production_targets"] if link_support else None)
    binding = read(refs["defender_binding"]["path"])
    require(binding.get("machine_id") == machine and binding.get("status") == "verified"
            and binding.get("exact_executable_count") == len(fixtures), "Actual exact Defender setting readback required")
    checked(binding["manifest"])
    checked(binding["receipt"])
    defender_manifest, defender = read(binding["manifest"]["path"]), read(binding["receipt"]["path"])
    expected_exes = {row["executable"]["path"]: row["executable"] for row in fixtures}
    semantic_manifest_sha = hashlib.sha256(json.dumps(defender_manifest, sort_keys=True).encode()).hexdigest()
    require(defender.get("status") == "verified" and defender.get("admin_token") is True
            and defender.get("manifest_sha256") == semantic_manifest_sha
            and defender.get("missing_requested_paths") == []
            and set(defender.get("verified_requested_paths", [])) == set(expected_exes),
            "Administrative Defender readback does not prove every exact fixture path")
    require(len(defender_manifest.get("files", [])) == len(expected_exes), "Defender manifest file set differs")
    for row in defender_manifest["files"]:
        require(row["path"] in expected_exes and row["size"] == expected_exes[row["path"]]["bytes"]
                and row["sha256"] == expected_exes[row["path"]]["sha256"], "Defender EXE source pin differs")
    execution_wire = None
    if profile["flags"].get("XAR_CK3_ENABLE_G2_PLAYER_PILGRIMAGE_EXECUTION_PRIVATE_V1") == "ON":
        require(value.get("execution_wire_packets"), "New qualified pilgrimage execution profile needs its actual new serializer packets")
        execution_wire = qualified_execution_packets(value["execution_wire_packets"], fixtures, snapshot_root, machine)
        wire = read(execution_wire["ref"]["path"])
        finite = next(row for row in fixtures if row["executable"] == wire["executable"])
        target = actual_targets[names[finite["target"]]]
        compiled = set()
        for src in target.get("sources", []):
            if src.get("compileGroupIndex") is not None:
                item = Path(src["path"])
                compiled.add(item.resolve() if item.is_absolute() else (snapshot_root / item).resolve())
        require(Path(wire["source"]["path"]).resolve() in compiled,
                "Wire emitter source is not an actual compiled source of its qualified finite fixture")
    return {"qualification_ref": pin(path), "profile_ref": refs["profile"], "freeze_ref": refs["production_freeze"],
            "profile": profile, "old_profile": old_profile, "dll": refs["published_dll"],
            "native_files": native_files, "snapshot_root": str(snapshot_root), "compile_commit": native_commit,
            "execution_wire": execution_wire, "profile_expansion": expansion["ref"] if expansion else None,
            "fixture_link_support": link_support["ref"] if link_support else None,
            "source_checkout_binding": source_checkout["binding_ref"],
            "shared_python_host_delta": source_checkout.get("shared_python_host_delta"),
            "shared_host_qualification": source_checkout.get("shared_host_qualification"),
            "nonancestor_exact_tree_binding": source_checkout.get("nonancestor_exact_tree_binding"),
            "native_compile_commit_is_ancestor": ancestor.returncode == 0,
            "nonancestor_research_delta_binding": source_checkout.get("nonancestor_research_delta_binding"),
            "full_native_tree_equal": source_checkout.get("full_native_tree_equal"),
            "compiled_inputs_equal": source_checkout.get("compiled_inputs_equal"),
            "research_delta": source_checkout.get("research_delta")}


class RegistrationFactoryProjectionV1(TypedDict):
    parent: FilePin
    current_factory: FilePin
    projected: FilePin
    binding: Literal['existing_same_service_builder_to_current_global_factory']


def _registration_host_closure(previous_host: str, runtime: JsonObject) -> tuple[list[ast.stmt], FilePin] | None:
    """Recognize only the legacy imports or this producer's exact pinned loader."""
    servers = [node for node in ast.parse(previous_host).body
               if isinstance(node, ast.FunctionDef) and node.name == 'native_server']
    modules = {'registration_bootstrap', 'progress_driver', 'registration_mcp',
               'progress_contract', 'progress_boundary'}
    names = {'bind_registration', 'ProgressDailyDriver', '_SharedRegistrationPin',
             '_load_shared_registration', '_shared_registration', 'create_server'}
    selected: list[ast.stmt] = [node for server in servers for node in server.body
        if (isinstance(node, ast.ImportFrom) and node.module in modules)
        or (isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id in names
                                               for target in node.targets))
        or (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name) and node.value.func.id == 'bind_registration')]
    if not selected:
        return None
    if len(servers) != 1:
        raise ValueError('Existing global registration native server must be unique')
    prefix = ('from registration_bootstrap import bind_registration\n'
              'bind_registration()\nfrom progress_driver import ProgressDailyDriver\n')
    legacy = ast.parse(prefix + 'from registration_mcp import create_server\n').body
    embedded: FilePin | None = None
    if [ast.dump(node) for node in selected] != [ast.dump(node) for node in legacy]:
        loaders = [node for node in selected if isinstance(node, ast.Assign)
                   and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                   and node.targets[0].id == '_shared_registration']
        if len(loaders) != 1:
            raise ValueError('Existing global registration provider closure is incomplete')
        call = loaders[0].value
        if (not isinstance(call, ast.Call) or len(call.args) != 2
                or not isinstance(call.args[0], ast.Call) or len(call.args[0].args) != 1):
            raise ValueError('Unknown existing pinned registration loader')
        try:
            literal: object = ast.literal_eval(call.args[0].args[0])
        except (ValueError, TypeError) as error:
            raise ValueError('Literal existing registration source pin required') from error
        embedded = checked_host_support_pin(literal)
        projected = ast.parse(prefix
            + 'from progress_contract import Pin as _SharedRegistrationPin\n'
            + 'from progress_boundary import load_module as _load_shared_registration\n'
            + f'_shared_registration = _load_shared_registration(_SharedRegistrationPin.parse({dict(embedded)!r}), '
            + "'xar_autoplayer.bridge.selected_r05_registration_factory_v1')\n"
            + 'create_server = _shared_registration.create_server\n').body
        if [ast.dump(node) for node in selected] != [ast.dump(node) for node in projected]:
            raise ValueError('Unknown existing pinned registration closure')
    search = json_object(runtime.get('runtime_environment')).get('PYTHONPATH')
    if not isinstance(search, list) or any(not isinstance(item, str) for item in search):
        raise ValueError('Existing global registration requires explicit string import roots')
    if embedded is None:
        candidates = [(Path(item) / 'registration_mcp.py').resolve()
                      for item in search if isinstance(item, str)]
        parent = next((path for path in candidates if path.is_file()), None)
        if parent is None:
            raise ValueError('Existing global registration provider is unavailable')
    else:
        parent = Path(embedded['path']).resolve()
    references: list[FilePin] = []
    for value in json_object(runtime.get('allocator_overlay')).values():
        if isinstance(value, dict):
            declared = value.get('path')
            if isinstance(declared, str) and Path(declared).resolve() == parent:
                references.append(checked_host_support_pin(value))
    if len(references) != 1 or embedded is not None and references[0] != embedded:
        raise ValueError('The selected existing registration provider must have one exact parent source pin')
    return selected[:3], references[0]


def canonical_registration_projection(source_root: Path, runtime: JsonObject, previous_host: str,
                                        destination: Path) -> tuple[bytes, RegistrationFactoryProjectionV1] | None:
    closure = _registration_host_closure(previous_host, runtime)
    if closure is None:
        return None
    parent_pin = closure[1]
    parent = Path(parent_pin['path'])
    factory = source_root / 'ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py'
    factory_nodes = [node for node in ast.parse(factory.read_text(encoding='utf-8-sig')).body
                     if isinstance(node, ast.FunctionDef) and node.name == 'create_server']
    if len(factory_nodes) != 1 or not any(arg.arg == 'service_override' for arg in factory_nodes[0].args.kwonlyargs):
        raise ValueError('Current global factory must expose the checked same-service override')
    raw = parent.read_text(encoding='utf-8-sig')
    creators = [node for node in ast.parse(raw).body if isinstance(node, ast.FunctionDef) and node.name == 'create_server']
    if len(creators) != 1:
        raise ValueError('The existing global registration factory must be unique')
    creator = creators[0]
    matches = [index for index, node in enumerate(creator.body) if isinstance(node, ast.Assign)
        and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'module']
    imports = [index for index, node in enumerate(creator.body) if isinstance(node, ast.ImportFrom)
               and node.module == 'xar_autoplayer.bridge'
               and ast.dump(node) == ast.dump(ast.parse('from xar_autoplayer.bridge import mcp_server as module').body[0])]
    if len(matches) + len(imports) != 1 or creator.end_lineno is None:
        raise ValueError('The existing scoped-factory binding must be explicit and unique')
    if matches:
        original = creator.body[matches[0]]
        if not isinstance(original, ast.Assign) or not isinstance(original.value, ast.Call) or not isinstance(original.value.func, ast.Name) or original.value.func.id != 'load_module':
            raise ValueError('Unknown existing scoped-factory binding')
        creator.body[matches[0]] = ast.ImportFrom(module='xar_autoplayer.bridge',
            names=[ast.alias(name='mcp_server', asname='module')], level=0)
    else:
        builders = [node for node in ast.walk(creator) if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute) and node.func.attr == 'create_server'
                    and isinstance(node.func.value, ast.Name) and node.func.value.id in {'module', 'builder'}]
        if len(builders) != 1:
            raise ValueError('Projected registration must retain one same-service factory call')
        receiver = builders[0].func
        if isinstance(receiver, ast.Attribute) and isinstance(receiver.value, ast.Name) and receiver.value.id == 'builder':
            aliases = [node for node in creator.body
                if (isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == 'builder')
                or (isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'builder'
                                                        for target in node.targets))]
            if (len(aliases) != 1 or not isinstance(aliases[0].value, ast.Name)
                    or aliases[0].value.id != 'module'
                    or isinstance(aliases[0], ast.Assign) and len(aliases[0].targets) != 1):
                raise ValueError('Projected registration builder must bind uniquely to the selected module')
        services = [keyword.value for keyword in builders[0].keywords if keyword.arg == 'service_override']
        if len(services) != 1 or not isinstance(services[0], ast.Name):
            raise ValueError('Projected registration must retain its explicit same-service override')
        service_name = services[0].id
        parameters = {arg.arg for arg in creator.args.args + creator.args.kwonlyargs}
        local_services = [node for node in creator.body if isinstance(node, ast.Assign)
            and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == service_name and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name) and node.value.func.id == 'GameplayBridgeService'
            and len(node.value.args) == 1 and isinstance(node.value.args[0], ast.Name)
            and node.value.args[0].id == 'driver' and not node.value.keywords]
        if service_name not in parameters and len(local_services) != 1:
            raise ValueError('Projected registration same-service source is unknown')
    lines = raw.splitlines(keepends=True)
    projected = ''.join(lines[:creator.lineno - 1]) + ast.unparse(ast.fix_missing_locations(creator)) + '\n' + ''.join(lines[creator.end_lineno:])
    encoded = BOM + projected.encode('utf-8')
    evidence = RegistrationFactoryProjectionV1(parent=parent_pin, current_factory=_support_file_pin(factory),
        projected=_support_output_pin(destination, encoded), binding='existing_same_service_builder_to_current_global_factory')
    return encoded, evidence


def project_host(root: Path, old_host: Path, old_runtime: Path, new_runtime: Path,
                 source_files: Mapping[str, object], *, registration_override: FilePin | None = None) -> bytes:
    canonical_raw = (root / HOST_RELATIVE).read_bytes()
    declared_host = json_object(source_files.get(HOST_RELATIVE))
    if set(declared_host) != {'bytes', 'sha256'}:
        raise ValueError('Exact canonical host source metadata required')
    checked_host_support_pin({'path': str((root / HOST_RELATIVE).resolve()),
                              'bytes': declared_host['bytes'], 'sha256': declared_host['sha256']})
    canonical = canonical_raw.removeprefix(BOM).decode("utf-8")
    previous = old_host.read_text(encoding="utf-8-sig")
    marker = "# Explicit static normal-exit binding projection; ordinary shared host remains above."
    if marker not in previous:
        # Current shared hosts bind normal exit through the allocated managed
        # profile rather than a literal runtime tail. Preserve that authority.
        def binding_tree(text: str) -> str:
            matches = [node for node in ast.parse(text).body
                       if isinstance(node, ast.FunctionDef) and node.name == 'bind_normal_exit_managed_profile']
            require(len(matches) == 1, 'Unique managed normal-exit profile binding required')
            return ast.dump(matches[0], include_attributes=False)
        require(binding_tree(previous) == binding_tree(canonical),
                'Canonical successor changed the existing managed normal-exit binding')
        def options(text: str) -> set[str]:
            return {node.args[0].value for node in ast.walk(ast.parse(text))
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == 'add_argument' and node.args
                    and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)
                    and node.args[0].value.startswith('--')}
        require(options(previous) <= options(canonical), 'Canonical successor removed an existing public host option')
        require('saved_campaign_profile_inventory_v2' in canonical,
                'Canonical successor must consume the current role-bound saved inventory')
        closure = _registration_host_closure(previous, json_object(json.loads(old_runtime.read_bytes())))
        if closure is not None:
            # Preserve the already selected global R05 registration provider;
            # replacing the host must not silently remove its advertised tools.
            current_servers = [node for node in ast.parse(canonical).body
                               if isinstance(node, ast.FunctionDef) and node.name == 'native_server']
            if len(current_servers) != 1:
                raise ValueError('Canonical native server must be unique')
            current_server = current_servers[0]
            drivers = [node for node in current_server.body
                       if isinstance(node, ast.ClassDef) and node.name == 'RecordingDriver']
            if (len(drivers) != 1 or len(drivers[0].bases) != 1
                    or not isinstance(drivers[0].bases[0], ast.Name)
                    or drivers[0].bases[0].id != 'NativeHeadlessGameplayDriver'):
                raise ValueError('Canonical recording driver has an unknown authority')
            drivers[0].bases = [ast.Name(id='ProgressDailyDriver', ctx=ast.Load())]
            current_server.body = [node for node in current_server.body
                if not (isinstance(node, ast.ImportFrom) and node.module == 'xar_autoplayer.bridge.mcp_server')]
            if registration_override is None:
                raise ValueError('Existing global R05 tools require an explicit same-service current-factory projection')
            provider_pin = ast.Dict(keys=[ast.Constant(key) for key in ('path', 'bytes', 'sha256')],
                values=[ast.Constant(registration_override['path']), ast.Constant(registration_override['bytes']),
                        ast.Constant(registration_override['sha256'])])
            insertion: list[ast.stmt] = [*closure[0],
                ast.ImportFrom(module='progress_contract', names=[ast.alias(name='Pin', asname='_SharedRegistrationPin')], level=0),
                ast.ImportFrom(module='progress_boundary', names=[ast.alias(name='load_module', asname='_load_shared_registration')], level=0),
                ast.Assign(targets=[ast.Name(id='_shared_registration', ctx=ast.Store())],
                    value=ast.Call(func=ast.Name(id='_load_shared_registration', ctx=ast.Load()),
                        args=[ast.Call(func=ast.Attribute(value=ast.Name(id='_SharedRegistrationPin', ctx=ast.Load()), attr='parse', ctx=ast.Load()), args=[provider_pin], keywords=[]),
                              ast.Constant('xar_autoplayer.bridge.selected_r05_registration_factory_v1')], keywords=[])),
                ast.Assign(targets=[ast.Name(id='create_server', ctx=ast.Store())],
                    value=ast.Attribute(value=ast.Name(id='_shared_registration', ctx=ast.Load()), attr='create_server', ctx=ast.Load()))]
            current_server.body[1:1] = insertion
            if current_server.end_lineno is None:
                raise ValueError('Canonical native server source span unavailable')
            lines = canonical.splitlines(keepends=True)
            replacement = ast.unparse(ast.fix_missing_locations(current_server)) + '\n'
            canonical = ''.join(lines[:current_server.lineno - 1]) + replacement + ''.join(lines[current_server.end_lineno:])
            ast.parse(canonical)
        return BOM + canonical.encode('utf-8')
    require(previous.count(marker) == 1, "Existing shared normal-exit projection boundary differs")
    tail = previous[previous.index(marker):]
    tail_tree = ast.parse(tail)
    preparations = [node for node in tail_tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == '_faith_prepare_actual_normal_exit_binding']
    binding_scope = preparations[0] if len(preparations) == 1 else tail_tree
    assignments = [node.value for node in ast.walk(binding_scope) if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == "_runtime_path" for target in node.targets)]
    if (len(assignments) != 1 or not isinstance(assignments[0], ast.Call)
            or not isinstance(assignments[0].func, ast.Name) or assignments[0].func.id != "Path"
            or len(assignments[0].args) != 1 or not isinstance(assignments[0].args[0], ast.Constant)
            or not isinstance(assignments[0].args[0].value, str)):
        raise ValueError('Unique literal existing runtime binding required')
    bound_path = Path(assignments[0].args[0].value).resolve()
    bound_runtime = json_object(json.loads(bound_path.read_bytes()))
    selected_runtime = json_object(json.loads(old_runtime.read_bytes()))
    bound_manifest_pin = checked_host_support_pin(bound_runtime.get('manifest'))
    selected_manifest_pin = checked_host_support_pin(selected_runtime.get('manifest'))
    bound_manifest = json_object(json.loads(Path(bound_manifest_pin['path']).read_bytes()))
    selected_manifest = json_object(json.loads(Path(selected_manifest_pin['path']).read_bytes()))
    require(all(bound_manifest[key] == selected_manifest[key] for key in
                ("host", "source_root", "source_index", "native_source_index", "native", "game")),
            "A recording clone must retain the existing actual global source/native host binding")
    old_binding = "Path(" + repr(str(bound_path)) + ")"
    require(tail.count(old_binding) in (1, 2), "Previous runtime projection paths differ")
    tail = tail.replace(old_binding, "Path(" + repr(str(new_runtime)) + ")")
    tail_tree = ast.parse(tail)
    legacy_error = 'This selected projection derives the actual profile once; supplied replacement is forbidden'
    for node in tail_tree.body:
        if not isinstance(node, ast.FunctionDef) or node.name != 'main':
            continue
        for statement in node.body:
            if not isinstance(statement, ast.If) or not statement.body or not isinstance(statement.body[0], ast.If):
                continue
            refusal = statement.body[0]
            if (len(refusal.body) != 1 or not isinstance(refusal.body[0], ast.Raise)
                    or not isinstance(refusal.body[0].exc, ast.Call)
                    or not refusal.body[0].exc.args or not isinstance(refusal.body[0].exc.args[0], ast.Constant)
                    or refusal.body[0].exc.args[0].value != legacy_error):
                continue
            validation = ast.parse(f'''
if _args.normal_exit_managed_profile is not None or _args.normal_exit_managed_profile_sha256 is not None:
    from ck3_mod_acceptance import normal_exit_static_binding_v1
    from ck3_mod_acceptance_background_types import file_pin
    from ck3_mod_acceptance_normal_exit_profile import pin as _binding_pin
    if _args.normal_exit_managed_profile is None or not _args.normal_exit_managed_profile_sha256:
        raise ValueError('Allocated normal-exit profile requires its exact SHA-256')
    _profile_ref = _binding_pin(_args.normal_exit_managed_profile)
    if _profile_ref['sha256'] != _args.normal_exit_managed_profile_sha256.lower():
        raise ValueError('Allocated normal-exit profile bytes changed')
    _runtime_path = Path({str(new_runtime)!r})
    _runtime = json.loads(_runtime_path.read_bytes())
    _manifest_ref = file_pin(_runtime['manifest'])
    if _binding_pin(_manifest_ref['path']) != _manifest_ref:
        raise ValueError('Selected normal-exit runtime manifest changed')
    normal_exit_static_binding_v1(_profile_ref, state_dir=_args.state_dir,
        run_dir=_args.output.resolve().parent, runtime_manifest=_manifest_ref)
    bind_normal_exit_managed_profile(argparse.Namespace(), _args)
''').body[0]
            if not isinstance(validation, ast.If):
                raise ValueError('Allocated normal-exit validation branch unavailable')
            validation.orelse = statement.body[1:]
            statement.body = [validation]
    tail = marker + '\n' + ast.unparse(ast.fix_missing_locations(tail_tree)) + '\n'
    sentinel = 'if __name__ == "__main__":\n    raise SystemExit(main())'
    require(canonical.count(sentinel) == 1, "Actual shared host entry boundary differs")
    result = canonical.replace(sentinel, "", 1).rstrip() + "\n\n" + tail
    ast.parse(result)
    return BOM + result.encode("utf-8")


def build_canonical_host_successor(base_runtime: Path, source_root: Path, runtime_binding: Path,
                                    destination: Path, machine_id: str) -> FilePin:
    """Freeze the existing canonical producer; no process, SDK or live admission."""
    from ck3_live_run_id import current_machine_id
    if current_machine_id() != machine_id:
        raise ValueError('Canonical host successor requires the observed current machine')
    runtime = json_object(json.loads(base_runtime.read_bytes()))
    manifest_pin = checked_host_support_pin(runtime.get('manifest'))
    manifest = json_object(json.loads(Path(manifest_pin['path']).read_bytes()))
    if (runtime.get('schema') != 'ck3-mod-acceptance-runtime-v1'
            or manifest.get('schema') != 'ck3-mod-acceptance-shared-runtime-v1'
            or runtime.get('machine_id') != machine_id or manifest.get('machine_id') != machine_id):
        raise ValueError('Actual common parent runtime and manifest required')
    paths = json_object(runtime.get('paths'))
    host_row = json_object(manifest.get('host'))
    host_path = Path(text_field(paths, text_field(host_row, 'path_key')))
    host_pin = checked_host_support_pin({'path': str(host_path.resolve()),
                                        'bytes': host_row.get('bytes'), 'sha256': host_row.get('sha256')})
    canonical_path = source_root / HOST_RELATIVE
    canonical_pin = _support_file_pin(canonical_path)
    source_files: dict[str, object] = {HOST_RELATIVE: {'bytes': canonical_pin['bytes'], 'sha256': canonical_pin['sha256']}}
    destination = destination.resolve()
    if destination.exists() or destination.is_relative_to(source_root.resolve()):
        raise ValueError('A fresh external canonical-host successor directory is required')
    registration = canonical_registration_projection(source_root, runtime, host_path.read_text(encoding='utf-8-sig'),
                                                       destination / 'registration_mcp.py')
    raw = project_host(source_root, host_path, base_runtime, runtime_binding, source_files,
                       registration_override=registration[1]['projected'] if registration is not None else None)
    destination.mkdir(parents=True)
    if registration is not None:
        with (destination / 'registration_mcp.py').open('xb') as stream:
            stream.write(registration[0])
    target = destination / 'shared-host.py'
    with target.open('xb') as stream:
        stream.write(raw)
    receipt = destination / 'canonical-host-projection.json'
    payload = json_object({'schema': 'ck3-common-canonical-host-successor-v1',
        'machine_id': machine_id, 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'qualification': 'SOURCE_PROJECTION_ONLY_LIVE_NOT_QUALIFIED',
        'parent_runtime': _support_file_pin(base_runtime), 'parent_manifest': manifest_pin,
        'parent_host': host_pin, 'canonical_host': canonical_pin, 'producer': _support_file_pin(Path(__file__)),
        'projected_host': _support_file_pin(target), 'runtime_binding': str(runtime_binding.resolve()),
        'game_started': False, 'allocated': False, 'actual_live_qualified': False})
    if registration is not None:
        payload['registration_projection'] = json_object(registration[1])
    with receipt.open('xb') as stream:
        stream.write(_support_json(payload))
    return _support_file_pin(receipt)


def _canonical_host_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description='Freeze the existing canonical common host without starting a game')
    for name in ('base-runtime', 'source-root', 'runtime-binding', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--machine-id', required=True)
    args = parser.parse_args(argv)
    result = build_canonical_host_successor(args.base_runtime, args.source_root, args.runtime_binding,
                                            args.output, args.machine_id)
    print(json.dumps({'receipt': result, 'game_started': False, 'allocated': False}))
    return 0


def check_index_only_changes(root, changed_paths):
    independent = [path for path in changed_paths if path.startswith(("tools/g2_saved_campaign/", "_runtime/", "tools/ck3_obs_"))]
    if not independent:
        return []
    selected = set((root / "ck3_autonomous_player/src").rglob("*.py"))
    selected.update((root / "tools").glob("ck3_mod_acceptance*.py"))
    selected.update((root / "tools/ck3_mod_acceptance_cases").glob("*.py"))
    selected.add(root / HOST_RELATIVE)
    selected = {path for path in selected if path.is_file() and path.name not in {
        "ck3_mod_acceptance_build_runtime.py", "ck3_mod_acceptance_freeze_sources.py"}}
    # The current public keeper records via FFmpeg; unrelated research and OBS
    # producers are indexed, not requalified. Existing implementation references
    # are checked as executable AST values, so explanatory comments do not count.
    tokens = ["g2_saved_campaign", "ck3_obs_"] + [path for path in independent if path.startswith("_runtime/")]
    for source in selected:
        for node in ast.walk(ast.parse(source.read_text(encoding="utf-8-sig"))):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [item.name for item in node.names] + ([node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
                require(not any(any(token in name for token in tokens) for name in names),
                        "Index-only implementation became a selected runtime import: " + str(source))
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                require(not any(token in node.value.replace("\\", "/") for token in tokens),
                        "Index-only implementation became a selected runtime executable/config reference: " + str(source))
    return independent


def wire_evidence_runtime_features(features: object, codec: object) -> dict[str, object]:
    """Select one strict shared codec without discarding existing host features."""
    if not isinstance(features, dict):
        raise ValueError("Shared host features require an object")
    result: dict[str, object] = {}
    for key, value in features.items():
        if not isinstance(key, str):
            raise ValueError("Shared host features require string keys")
        result[key] = value
    wire_evidence_codec(result["wire_evidence_codec"] if "wire_evidence_codec" in result else "plain")
    selected: WireEvidenceCodec = wire_evidence_codec(codec)
    result["wire_evidence_codec"] = selected
    return result


def _support_file_pin(path: Path) -> FilePin:
    resolved = path.resolve()
    raw = resolved.read_bytes()
    return FilePin(path=str(resolved), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def _support_output_pin(path: Path, raw: bytes) -> FilePin:
    return FilePin(path=str(path.resolve()), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def _support_json(value: JsonObject) -> bytes:
    return (json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + '\n').encode('utf-8')


@dataclass(frozen=True)
class HostSupportStorageV1:
    root: Path
    maximum: int
    minimum_free: int
    used_cap: int

    @classmethod
    def parse(cls, value: object, machine: str) -> HostSupportStorageV1:
        row = json_object(value)
        fields = {'schema', 'machine_id', 'approved_root', 'observed_at_utc', 'expires_at_utc',
                  'max_write_bytes', 'required_free_bytes', 'volume_used_cap_bytes'}
        if set(row) != fields or row['schema'] != 'ck3-shared-host-support-storage-v1' or row['machine_id'] != machine:
            raise ValueError('Exact current-machine host-support storage admission required')
        root = Path(text_field(row, 'approved_root'))
        if not root.is_absolute() or root.is_symlink():
            raise ValueError('Absolute ordinary admitted host-support root required')
        observed = datetime.fromisoformat(text_field(row, 'observed_at_utc').replace('Z', '+00:00'))
        expires = datetime.fromisoformat(text_field(row, 'expires_at_utc').replace('Z', '+00:00'))
        current = datetime.now(timezone.utc)
        if observed.tzinfo is None or expires.tzinfo is None or not observed <= current < expires:
            raise ValueError('Fresh time-bounded host-support storage admission required')
        limits: list[int] = []
        for key in ('max_write_bytes', 'required_free_bytes', 'volume_used_cap_bytes'):
            limit = row[key]
            if type(limit) is not int or not isinstance(limit, int) or limit <= 0:
                raise ValueError('Strict positive integer host-support storage limit required')
            limits.append(limit)
        return cls(root.resolve(), *limits)


def build_host_running_date_support(base_runtime: Path, source_root: Path, source_commit: str,
                                    destination: Path, storage_admission: Path, *, menu_factory: bool = False) -> FilePin:
    """Build one global immutable host/support pair, retaining the existing SDK."""
    from ck3_live_run_id import current_machine_id
    actual_machine: object = current_machine_id()
    if type(actual_machine) is not str or not isinstance(actual_machine, str):
        raise ValueError('Actual stable machine identity required')
    runtime = json_object(json.loads(base_runtime.read_bytes()))
    manifest_ref = checked_host_support_pin(runtime.get('manifest'))
    manifest = json_object(json.loads(Path(manifest_ref['path']).read_bytes()))
    if (runtime.get('schema') != 'ck3-mod-acceptance-runtime-v1'
            or manifest.get('schema') != 'ck3-mod-acceptance-shared-runtime-v1'
            or runtime.get('machine_id') != actual_machine or manifest.get('machine_id') != actual_machine):
        raise ValueError('Exact actual-machine global base runtime required')
    if 'host_support_projection' in manifest:
        raise ValueError('Host support must project the reviewed original once, never stack projections')
    paths = json_object(runtime.get('paths'))
    host_row = json_object(manifest.get('host'))
    if set(host_row) != {'path_key', 'bytes', 'sha256'}:
        raise ValueError('Exact original shared host path/pin required')
    host_path = Path(text_field(paths, text_field(host_row, 'path_key')))
    base_host = checked_host_support_pin({'path': str(host_path.resolve()),
                                         'bytes': host_row['bytes'], 'sha256': host_row['sha256']})
    if re.fullmatch('[0-9a-f]{40}', source_commit) is None:
        raise ValueError('Exact canonical helper source commit required')
    source_root = source_root.resolve()
    canonical_path = source_root / RUNNING_DATE_SUPPORT_RELATIVE
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=source_root, capture_output=True, check=True).stdout.decode().strip()
    unchanged = subprocess.run(['git', 'diff', '--exit-code', source_commit, '--', RUNNING_DATE_SUPPORT_RELATIVE],
                               cwd=source_root, capture_output=True)
    if head != source_commit or unchanged.returncode != 0:
        raise ValueError('Canonical typed helper differs from the explicit current source commit')
    git_blob = subprocess.run(['git', 'rev-parse', source_commit + ':' + RUNNING_DATE_SUPPORT_RELATIVE],
                              cwd=source_root, capture_output=True, check=True).stdout.decode().strip()
    canonical_helper = checked_host_support_pin(_support_file_pin(canonical_path))
    if type(menu_factory) is not bool:
        raise ValueError('Menu factory selection requires a literal boolean')
    canonical_menu_factory: FilePin | None = None
    if menu_factory:
        from ck3_mod_acceptance_background_types import MENU_FACTORY_SOURCE_RELATIVE
        menu_path = source_root / MENU_FACTORY_SOURCE_RELATIVE
        menu_diff = subprocess.run(['git', 'diff', '--exit-code', source_commit, '--', MENU_FACTORY_SOURCE_RELATIVE],
                                   cwd=source_root, capture_output=True)
        if menu_diff.returncode != 0:
            raise ValueError('Canonical public menu factory differs from the committed source')
        canonical_menu_factory = checked_host_support_pin(_support_file_pin(menu_path))
    helper_raw = canonical_path.read_bytes()
    for node in ast.walk(ast.parse(helper_raw.decode('utf-8-sig'))):
        if isinstance(node, ast.Import) and any(item.name != 'math' for item in node.names):
            raise ValueError('Host-support closure must remain canonical and standard-library-only')
        if isinstance(node, ast.ImportFrom) and node.module not in {'__future__', 'dataclasses', 'typing'}:
            raise ValueError('Host-support closure must not import the selected SDK or a product')
    grant_ref = _support_file_pin(storage_admission)
    storage = HostSupportStorageV1.parse(json.loads(storage_admission.read_bytes()), actual_machine)
    destination = destination.resolve()
    if (destination.exists() or not destination.is_relative_to(storage.root) or destination == storage.root
            or destination.is_relative_to(source_root) or destination.is_symlink()):
        raise ValueError('Fresh external child of the admitted global runtime root required')
    helper = _support_output_pin(destination / RUNNING_DATE_SUPPORT_FILENAME, helper_raw)
    host_raw = project_running_date_host(host_path.read_bytes(), helper, canonical_menu_factory)
    projected_host = _support_output_pin(destination / 'shared-host.py', host_raw)
    projector_path = Path(sys.modules[HostRunningDateProjectionV1.__module__].__file__ or '')
    projection = HostRunningDateProjectionV1(actual_machine, source_commit, git_blob,
        datetime.now(timezone.utc).isoformat(), base_host,
        canonical_helper, helper, projected_host, _support_file_pin(Path(__file__)), _support_file_pin(projector_path),
        canonical_menu_factory=canonical_menu_factory)
    receipt_raw = _support_json(projection.to_json())
    receipt = _support_output_pin(destination / 'host-support-projection.json', receipt_raw)
    new_manifest = json_object(manifest)
    new_manifest['host'] = {'path_key': text_field(host_row, 'path_key'),
                            'bytes': projected_host['bytes'], 'sha256': projected_host['sha256']}
    new_manifest['host_support_projection'] = json_object(receipt)
    new_manifest['observed_at_utc'] = datetime.now(timezone.utc).isoformat()
    manifest_raw = _support_json(new_manifest)
    new_runtime = json_object(runtime)
    new_paths = json_object(paths)
    new_paths[text_field(host_row, 'path_key')] = projected_host['path']
    new_paths['host_running_date_support'] = helper['path']
    new_paths['host_support_projection'] = receipt['path']
    new_runtime['paths'] = new_paths
    new_runtime['manifest'] = json_object(_support_output_pin(destination / 'manifest.json', manifest_raw))
    runtime_raw = _support_json(new_runtime)
    outputs: dict[str, bytes] = {'shared-host.py': host_raw, RUNNING_DATE_SUPPORT_FILENAME: helper_raw,
        'host-support-projection.json': receipt_raw, 'manifest.json': manifest_raw, 'runtime.local.json': runtime_raw}
    total = sum(len(raw) for raw in outputs.values())
    probe = storage.root
    while not probe.exists():
        probe = probe.parent
    capacity = shutil.disk_usage(probe)
    if (total > min(storage.maximum, 2 * 1024 * 1024) or capacity.free < storage.minimum_free
            or capacity.used + total > storage.used_cap):
        raise ValueError('Host-support materialization exceeds the admitted volume/write bounds')
    if _support_file_pin(storage_admission) != grant_ref:
        raise ValueError('Host-support storage admission changed before materialization')
    destination.mkdir(parents=True, exist_ok=False)
    for name, raw in outputs.items():
        with (destination / name).open('xb') as stream:
            stream.write(raw)
    validate_host_running_date_projection(receipt, destination / 'shared-host.py', actual_machine)
    return _support_file_pin(destination / 'runtime.local.json')


def _host_running_date_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description='Materialize the shared running-date host support without changing SDK/native/game')
    for name in ('base-runtime', 'source-root', 'output', 'storage-admission'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--menu-factory', action='store_true', help='Use the canonical stock SDK factory only for menu cache observation')
    args = parser.parse_args(argv)
    result = build_host_running_date_support(args.base_runtime, args.source_root, args.source_commit,
                                            args.output, args.storage_admission, menu_factory=args.menu_factory)
    print(json.dumps({'runtime': result, 'game_started': False, 'allocated': False}))
    return 0


def main(argv: list[str] | None = None) -> int:
    selected = sys.argv[1:] if argv is None else argv
    if selected and selected[0] == 'host-canonical-successor':
        return _canonical_host_main(selected[1:])
    if selected and selected[0] == 'host-running-date-support':
        return _host_running_date_main(selected[1:])
    sys.dont_write_bytecode = True
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("base-runtime", "source-delta", "scene-root", "storage-admission", "products", "case-inputs", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--qualified-native", type=Path, required=True, help="exact actual native production-build qualification")
    parser.add_argument("--native-source-checkout-binding", type=Path,
                        help="explicit actual equivalence receipt for a clean linked Native source worktree")
    parser.add_argument("--native-shared-python-host-delta", type=Path,
                        help="explicit reviewed canonical Python-host delta beside unchanged compiled Native inputs")
    parser.add_argument("--task-prefix", default="ck3-acceptance-")
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--product", required=True)
    parser.add_argument("--case", required=True)
    parser.add_argument("--qualification", action="append", default=[], metavar="CHAIN=ACTUAL_RECEIPT")
    parser.add_argument("--native-profile", type=Path, help="actual qualified global native profile when new required tools need their compiled flags checked")
    parser.add_argument("--input-binder-command", type=Path, help="optional JSON argv for the independently selected public case input hook")
    parser.add_argument("--wire-evidence-codec", type=wire_evidence_codec, default="plain",
                        help="Shared wire evidence codec: plain or explicit gzip-members; default plain")
    args = parser.parse_args(argv)
    codec: WireEvidenceCodec = wire_evidence_codec(args.wire_evidence_codec)
    require(re.fullmatch("[0-9a-f]{40}", args.source_commit) is not None, "Actual next Root commit required")
    runtime, manifest, refs, source = load_base(args.base_runtime)
    root = Path(runtime["repo_root"]).resolve()
    require(Path(runtime["paths"][manifest["source_root"]["path_key"]]).resolve() == root,
            "The selected global SDK/source_root must remain the actual Root repository")
    sys.path[:0] = [str(root / "tools"), str(root / "ck3_autonomous_player/src"), str(root)]
    import ck3_live_run_id
    machine = ck3_live_run_id.current_machine_id()
    require(machine == runtime["machine_id"] == manifest["machine_id"], "Current machine differs from global base")
    scene = args.scene_root.resolve()
    old_scene_roots = {Path(runtime["userdir_root"]).resolve().parent, Path(runtime["artifacts_root"]).resolve().parent}
    require(scene not in old_scene_roots and not scene.is_relative_to(Path(refs["dll"]["path"]).parent.parent),
            "The selected base/native build scene cannot be expanded; obtain a fresh scene root")
    grant_pin = pin(args.storage_admission)
    grant = read(args.storage_admission)
    current = datetime.now(timezone.utc)
    require(grant.get("machine_id") == machine and grant.get("active") is True
            and any(word in grant.get("schema", "").lower() for word in ("capture", "scene", "live"))
            and Path(grant["approved_root"]).resolve() == scene
            and datetime.fromisoformat(grant["observed_at_utc"].replace("Z", "+00:00")) <= current
            < datetime.fromisoformat(grant["expires_at_utc"].replace("Z", "+00:00")), "Actual fresh scene grant required")
    destination = args.output.resolve()
    require(destination != scene and destination.is_relative_to(scene) and not destination.exists(),
            "Generate only into a fresh child of the new scene grant; no existing B6 lane writes")
    require(not destination.is_relative_to(root), "Root source writes are forbidden")
    require(not Path(args.output).is_symlink() and not args.storage_admission.is_symlink(), "No symbolic output/admission")
    require(shutil.disk_usage(scene).free >= grant["required_free_bytes"], "Current volume no longer satisfies full fresh admission")
    delta = read(args.source_delta)
    archive_context = None
    if "archive_relocations" in delta:
        from ck3_mod_acceptance_archive_relocations import validate_archive_relocations
        archive_context = validate_archive_relocations(args.source_delta, source, root, args.source_commit,
            args.products, args.product, args.case, args.case_inputs, args.input_binder_command)
    files, required, changed_paths = apply_delta(args.source_delta, args.base_runtime, manifest, source, root, args.source_commit, archive_context)
    diff_observed = datetime.fromisoformat(read(delta["Root_diff_receipt"]["path"])["observed_at_utc"].replace("Z", "+00:00"))
    require(datetime.fromisoformat(grant["observed_at_utc"].replace("Z", "+00:00")) <= diff_observed <= current,
            "Root complete-diff observation is outside the fresh next-scene admission")
    require(checked(delta["new_scene_admission"]) == grant_pin,
            "Source delta must bind this exact fresh next-scene admission")
    for name in CRITICAL_TRANSPORTS:
        relative = SDK_PREFIX + "xar_autoplayer/bridge/" + name
        require(sig((root / relative).read_bytes()) == files[relative],
                "Actual critical SDK file drifted outside complete Root delta: " + relative)
    receipts = {}
    for item in args.qualification:
        chain, separator, path = item.partition("=")
        if chain == "sdk_pilgrimage":
            chain = "pilgrimage_wire_seam"
        require(separator and chain not in receipts, "Unique CHAIN=receipt required")
        receipts[chain] = Path(path)
    native_bundle = qualify_native(args.qualified_native, root, args.source_commit, machine, refs["dll"], manifest,
                                   getattr(args, "native_source_checkout_binding", None),
                                   getattr(args, "native_shared_python_host_delta", None))
    if native_bundle.get("shared_host_qualification") is not None:
        require("shared_host" in receipts and pin(receipts["shared_host"]) == native_bundle["shared_host_qualification"],
                "Shared-host delta must use this selected current source-chain qualification")
    required.discard("new_native_base_required")
    if native_bundle["execution_wire"]:
        required.add("pilgrimage_wire_seam")
    require(required <= set(receipts), "Missing actual changed-chain qualifications: " + str(sorted(required - set(receipts))))
    qualified = {chain: qualify(chain, receipts[chain], args.source_commit, root, changed_paths, machine, archive_context) for chain in sorted(required)}
    if native_bundle["execution_wire"]:
        actual_sdk = read(receipts["pilgrimage_wire_seam"])
        require(actual_sdk.get("actual_execution_wire_packets") == native_bundle["execution_wire"]["ref"],
                "Current SDK seam must actually consume these new qualified native serializer outputs")
    index_only = check_index_only_changes(root, changed_paths)
    entry = module(root / "tools/ck3_mod_acceptance.py", "qualified_actual_public_entry")
    # Selection owns product cases and the one globally inherited workshop_cache case.
    case = entry.Selection(args.base_runtime, args.products, args.product, args.case).case
    needed = set(case["required_mcp_tools"])
    old_profile = native_bundle["old_profile"]
    native_profile = native_bundle["profile"]
    capabilities = {}
    for tool in sorted(set(manifest.get("capabilities", {})) | needed):
        stock_evidence = None
        if tool in STOCK_READ_ONLY_CAPABILITIES:
            stock_evidence = stock_read_only_source_evidence(tool, root, Path(native_bundle["snapshot_root"]),
                                                            native_bundle["native_files"], files, native_profile["flags"])
        if tool not in manifest.get("capabilities", {}):
            require(tool in EXTRA_CAPABILITIES or stock_evidence is not None, "Unreviewed global capability rule: " + tool)
            for flag in EXTRA_CAPABILITIES.get(tool, []):
                require(native_profile["flags"].get(flag) == "ON", "Qualified profile lacks required flag: " + flag)
        capabilities[tool] = {"source_build_ready": True, "actual_live_qualified": False,
            "actual_global_native_profile": native_bundle["profile_ref"],
            "actual_production_freeze": native_bundle["freeze_ref"],
            "native_input_identity_evidence": native_bundle["qualification_ref"],
            "native_DLL": native_bundle["dll"],
            "scope": "exact shared production build and finite native fixtures; no live business credit"}
        if stock_evidence is not None:
            capabilities[tool]["stock_read_only_source_evidence"] = stock_evidence
    output = {}

    def add(name, value):
        raw = encoded(value)
        output[name] = raw
        return {"path": str(destination / name), **sig(raw)}

    host_raw = project_host(root, Path(refs["host"]["path"]), args.base_runtime,
                            destination / "runtime.local.json", files)
    output["shared-host.py"] = host_raw
    source_ref = add("source-index.json", {"schema": "ck3-common-source-index-v1", "machine_id": machine,
                    "observed_at_utc": now(), "source_commit": args.source_commit, "files": files,
                    "base_index": refs["source_index"], "exact_Root_delta": pin(args.source_delta),
                    "scope": "frozen global index plus complete committed Root source delta; unchanged bodies not rehashed by this lightweight builder"})
    native_ref = add("native-source-index.json", {"schema": "ck3-common-native-source-index-v1",
        "machine_id": machine, "observed_at_utc": now(), "source_commit": args.source_commit,
        "files": native_bundle["native_files"], "identity": native_bundle["qualification_ref"],
        "source_root": native_bundle["snapshot_root"],
        "scope": "exact unique production translation-unit source paths from actual CMake File API; test targets excluded"})
    new_manifest = dict(manifest)
    new_manifest["host_features"] = wire_evidence_runtime_features(manifest.get("host_features", {}), codec)
    new_manifest.update(observed_at_utc=now(), source_commit=args.source_commit, capabilities=capabilities,
                        qualification_scope="new exact qualified global production DLL; changed source chains qualified independently; live results pending")
    new_manifest["host"] = {"path_key": "host", **sig(host_raw)}
    new_manifest["source_index"] = {"path_key": "source_index", "bytes": source_ref["bytes"], "sha256": source_ref["sha256"]}
    new_manifest["native_source_index"] = {"path_key": "native_source_index", "bytes": native_ref["bytes"], "sha256": native_ref["sha256"]}
    new_manifest["native"] = {**manifest["native"], "dll": {"path_key": "dll", "bytes": native_bundle["dll"]["bytes"], "sha256": native_bundle["dll"]["sha256"]}}
    new_manifest["native_input_identity_evidence"] = native_bundle["qualification_ref"]
    new_manifest["native_compile_source_commit"] = native_bundle["compile_commit"]
    new_manifest["native_compile_working_tree_dirty"] = False
    new_manifest.pop("native_source_checkout_binding", None)
    new_manifest.pop("native_shared_python_host_delta", None)
    if native_bundle.get("shared_python_host_delta") is not None:
        new_manifest["native_shared_python_host_delta"] = native_bundle["shared_python_host_delta"]
    if native_bundle["source_checkout_binding"] is not None:
        new_manifest["native_source_checkout_binding"] = native_bundle["source_checkout_binding"]
    new_manifest["shared_provider_scope"] = "one public SDK/host, qualified global production DLL, independent product policy only"
    manifest_ref = add("manifest.json", new_manifest)
    new_runtime = {k: v for k, v in runtime.items() if k not in {"manifest", "paths", "recording", "graphics_cache"}}
    new_runtime.update(userdir_root=str(scene / "managed-states"), artifacts_root=str(scene / "live"), manifest=manifest_ref)
    new_runtime["paths"] = {**runtime["paths"], "host": str(destination / "shared-host.py"), "source_index": source_ref["path"], "native_source_index": native_ref["path"], "dll": native_bundle["dll"]["path"]}
    for key, relative in (("reviewed_launcher", "tools/ck3_mod_acceptance_launcher.py"),
                          ("control_queue", "tools/ck3_mod_acceptance_queue.py")):
        new_runtime[key] = pin(root / relative)
    new_runtime["allocator_overlay"] = {path.name: pin(path) for path in (root / "tools").glob("ck3_mod_acceptance*.py")}
    new_runtime["allocator_overlay"]["recorder_job"] = pin(root / "promo/ck3_native_war_ai/integration/recorder_job.py")
    for row in new_runtime["allocator_overlay"].values():
        relative = Path(row["path"]).relative_to(root).as_posix()
        require({k: row[k] for k in ("bytes", "sha256")} == files[relative],
                "Actual public control source drifted outside complete Root delta: " + relative)
    new_runtime["allocation"] = {**runtime["allocation"], "task_prefix": args.task_prefix,
                                 "screen_keeper": pin(root / "tools/ck3_mod_acceptance_keeper.py")}
    runtime_ref = add("runtime.local.json", new_runtime)
    common = [str(Path(runtime["python"])), "-B", "-X", "utf8"]
    commands = {"machine_id": machine, "observed_at_utc": now(), "commands_executed": False,
                "wire_evidence_codec": codec,
                "prepare_argv": common + [str(root / "tools/ck3_mod_acceptance.py"), "prepare", "--runtime", runtime_ref["path"],
                    "--products", str(args.products.resolve()), "--product", args.product, "--case", args.case,
                    "--case-inputs", str(args.case_inputs.resolve()), "--prepare-output", str(scene / "prepared-a01")],
                "recording": "Root clones public recorder/runtime after candidate generation and before allocation"}
    if args.input_binder_command:
        hook = read(args.input_binder_command)
        require(isinstance(hook, list) and hook and all(isinstance(v, str) for v in hook), "Independent public case binder must be JSON argv")
        commands["bind_inputs_argv"] = hook
        commands["binder_hook_source"] = pin(args.input_binder_command)
    add("ENTRY-COMMANDS.json", commands)
    add("SOURCE-BINDINGS.actual.json", {"machine_id": machine, "observed_at_utc": now(),
        "source_commit": args.source_commit, "base_runtime": pin(args.base_runtime), "base_manifest": runtime["manifest"],
        "exact_Root_delta": pin(args.source_delta), "actual_changed_chain_receipts": qualified,
        "builder_program": pin(__file__), "wire_evidence_codec": codec,
        "archive_relocations": archive_context.evidence() if archive_context else None,
        "qualified_native_build": native_bundle["qualification_ref"],
        "index_only_unselected_changes": index_only,
        "index_only_scope": "complete committed delta retained; global SDK/host/publiccase/controller AST has no imports or executable references to these independent research/CI/OBS producers; no business requalification claimed",
        "previous_native_source_index": refs["native_source_index"], "previous_native_DLL": refs["dll"],
        "new_native_source_index": native_ref, "new_native_DLL": native_bundle["dll"],
        "product_catalog": pin(args.products), "independent_case": args.case,
        "actual_global_native_profile": native_bundle["profile_ref"],
        "native_recompiled_by_this_metadata_builder": False, "unchanged_SDK_body_rehashed": False, "case_private_host": False,
        "game_started": False, "allocated": False, "public_prepare_executed": False,
        "generation_authority": "fresh Root scene grant and actual next commit; this source package did not generate any candidate when authored"})
    validate_metadata_bound(output, limit_bytes=2 * 1024 * 1024, reserve_bytes=32768)
    require(pin(args.storage_admission) == grant_pin, "Fresh grant changed during metadata generation")
    write_bounded_metadata(destination, output, limit_bytes=2 * 1024 * 1024,
                           reserve_bytes=32768)
    selection = entry.Selection(destination / "runtime.local.json", args.products, args.product, args.case)
    adapter = selection.load_adapter()
    inputs = read(args.case_inputs).get("case_inputs", {}) if args.case_inputs.exists() else {}
    if callable(getattr(adapter, "validate_contract", None)):
        with selection.case_imports():
            adapter.validate_contract(selection.adapter_context(inputs=inputs))
    require(set(selection.case["required_mcp_tools"]) <= set(new_manifest["capabilities"]), "Required global capability evidence missing")
    # Register the unchanged real global MCP factory against an offline facade.
    # No method other than capabilities may run; list_tools is registration only.
    import asyncio
    registered = asyncio.run(registered_runtime_tool_names(
        json_object(selection.case), destination / "shared-host.py", scene / "managed-states/registration-only/profile"))
    require(needed <= registered, "Actual global MCP factory does not register required case tools: " + str(sorted(needed - registered)))
    missing = sorted({v for v in selection.argv if v.startswith("--")} - entry.host_cli_flags(destination / "shared-host.py"))
    require(not missing, "Current global host lacks actual public Selection CLI: " + str(missing))
    require(all(v == "Saved campaign input unbound: product_inventory" for v in selection.blockers),
            "Unexpected public Selection blockers: " + str(selection.blockers))
    with (destination / "STATIC-VALIDATION.actual.json").open("xb") as stream:
        stream.write(encoded({"machine_id": machine, "observed_at_utc": now(), "source_commit": args.source_commit,
            "independent_case": args.case, "public_Selection_argv": selection.argv, "wire_evidence_codec": codec,
            "actual_Selection_blockers": selection.blockers, "actual_changed_chain_receipts": qualified,
            "actual_registered_required_MCP_tools": sorted(needed), "registration_scope": "offline factory list_tools only; no game or tool invocation",
            "case_private_host": False, "prepare_executed": False, "game_started": False, "allocated": False,
            "runtime": pin(destination / "runtime.local.json"), "manifest": pin(destination / "manifest.json")}))
    print(json.dumps({"runtime": pin(destination / "runtime.local.json"), "entry": pin(destination / "ENTRY-COMMANDS.json"),
                      "case": args.case, "required_qualified_chains": sorted(required), "game_started": False,
                      "wire_evidence_codec": codec}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
