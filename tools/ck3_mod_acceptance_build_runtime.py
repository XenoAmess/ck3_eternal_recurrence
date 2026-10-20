"""Build a shared acceptance runtime from exact committed source and a qualified native production build."""
from __future__ import annotations
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
BOM = b"\xef\xbb\xbf"
HOST_RELATIVE = "ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py"
SDK_PREFIX = "ck3_autonomous_player/src/"
NATIVE_PREFIX = "ck3_autonomous_player/native_bridge/"
PROFILE_EXPANSION_RELATIVE = "tools/ck3_mod_acceptance_native_profile_expansions.json"
TEST_PREFIX = "ck3_autonomous_player/tests/"
CRITICAL_TRANSPORTS = frozenset({
    "player_pilgrimage_planner_private_transport.py", "player_pilgrimage_activities_private_transport.py",
    "native_driver.py", "mcp_server.py", "nonwar_private_build.py", "version_identity.py",
    "activity_feast_stage5_start_private_transport.py", "driver.py", "exact_clock_failure_diagnostic_v1.py",
})
EXTRA_CAPABILITIES = {
    "ck3_inspect_gui_window_tree_v1": [],
    "ck3_open_ingame_decisions_v1": ["XAR_CK3_ENABLE_INGAME_DECISIONS_OPEN_PRIVATE_V1"],
    "ck3_query_ingame_decision_item_v1": [],
    "ck3_query_player_holy_site_v1": ["XAR_CK3_ENABLE_G2_PLAYER_HOLY_SITE_CREATION_CONTEXT_PRIVATE_QUERY_V1"],
    "ck3_query_player_rite_governance_v1": ["XAR_CK3_ENABLE_G2_PLAYER_RITE_GOVERNANCE_PRIVATE_QUERY_V1"],
    "ck3_select_ingame_decision_item_v1": ["XAR_CK3_ENABLE_INGAME_DECISION_ITEM_ACTIONS_PRIVATE_V1", "XAR_CK3_ENABLE_INGAME_DECISION_OUTCOME_PRIVATE_V1"],
    "ck3_confirm_ingame_decision_outcome_v1": ["XAR_CK3_ENABLE_INGAME_DECISION_ITEM_ACTIONS_PRIVATE_V1", "XAR_CK3_ENABLE_INGAME_DECISION_OUTCOME_PRIVATE_V1"],
    "ck3_query_player_artifact_personal_use_v1": ["XAR_CK3_ENABLE_G2_PLAYER_ARTIFACT_PERSONAL_USE_READONLY_V1"],
    "ck3_submit_player_artifact_personal_use_v1": ["XAR_CK3_ENABLE_ARTIFACT_PERSONAL_USE_PRIVATE_V1"],
    "ck3_query_player_artifact_personal_use_action_post_v1": ["XAR_CK3_ENABLE_ARTIFACT_PERSONAL_USE_PRIVATE_V1"],
    "ck3_query_player_ghw_permissions_v1": ["XAR_CK3_ENABLE_G2_PLAYER_GHW_PERMISSIONS_READONLY_V1"],
    "ck3_query_character_skill_effects_v1": ["XAR_CK3_ENABLE_CHARACTER_SKILL_EFFECTS12004_PRIVATE_QUERY_V1"],
    "ck3_open_player_inventory_window_v1": ["XAR_CK3_ENABLE_PLAYER_INVENTORY_WINDOW_OPEN_PRIVATE_V1"],
    "ck3_query_player_inventory_window_open_post_v1": ["XAR_CK3_ENABLE_PLAYER_INVENTORY_WINDOW_OPEN_PRIVATE_V1"],
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
REGISTRATION_READ_ONLY_FLAGS = {
    "ck3_query_player_holy_site_creation_context_v1": "allow_private_player_holy_site_creation_context_query",
    "ck3_query_player_holy_site_relic_action_context_v1": "allow_private_player_holy_site_relic_action_context_query",
    "ck3_query_player_holy_site_relic_permissions_v1": "allow_private_player_holy_site_relic_permissions_query",
    "ck3_query_player_holy_site_relic_context_v1": "allow_private_player_holy_site_relic_context_query",
    "ck3_query_player_holy_site_v1": "allow_private_player_holy_site_query",
    "ck3_query_player_artifact_personal_use_v1": "allow_private_player_artifact_personal_use_query",
    "ck3_query_player_ghw_permissions_v1": "allow_private_player_ghw_permissions_query",
    "ck3_query_character_skill_effects_v1": "allow_private_character_skill_effects_query",
}
REGISTRATION_ACTION_FLAGS = {
    "opt_in_player_pilgrimage_execution": "allow_private_player_pilgrimage_execution",
    "opt_in_holy_site_creation_ui": "allow_private_player_holy_site_creation_ui",
    "opt_in_holy_site_creation_create_once": "allow_private_player_holy_site_creation_create_once",
    "opt_in_holy_site_relic_actions": "allow_private_holy_site_relic_actions",
    "opt_in_player_artifact_personal_use_actions": "allow_private_player_artifact_personal_use_actions",
    "opt_in_player_inventory_window_open": "allow_private_player_inventory_window_open",
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

    driver = RegistrationOnlyDriver()
    for tool, name in REGISTRATION_READ_ONLY_FLAGS.items():
        setattr(driver, name, tool in driver.case_declared_read_only_mcp_tools)
    for key, name in REGISTRATION_ACTION_FLAGS.items():
        setattr(driver, name, case.get(key) is True)
    return driver


def require(value, message):
    if not value:
        raise ValueError(message)


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


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def classify(path):
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


def qualify(chain, path, commit, root, changed_paths, machine):
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
    relevant = [p for p in changed_paths if chain in classify(p)]
    if chain == "pilgrimage_wire_seam":
        critical_paths = {SDK_PREFIX + "xar_autoplayer/bridge/" + name for name in CRITICAL_TRANSPORTS}
        require(critical_paths <= set(indexed), "Current SDK seam receipt must pin all eight actual critical SDK files")
        # Clock implementation pins belong to its actual focused clock suite;
        # the companion SDK tests validate the unchanged wire/Driver/MCP chain.
        relevant = [path for path in relevant if path in critical_paths]
    require(all(path in indexed for path in relevant), "Receipt is missing a changed-chain source pin: " + chain)
    return pin(path)


def apply_delta(delta_path, runtime_path, manifest, source, root, commit):
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
    files = dict(source["files"])
    required = set()
    for row in changes:
        relative = row["path"]
        required.update(classify(relative))
        require(row["before"] == files.get(relative), "Before raw signature differs from frozen global index: " + relative)
        current = (root / relative).resolve()
        require(current.is_relative_to(root), "Changed source escaped Root")
        after = {k: pin(current)[k] for k in ("bytes", "sha256")} if current.is_file() else None
        require(after == row["after"], "Current changed source differs from frozen delta: " + relative)
        require(after is not None or row["before"] is None,
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
             "start-unknown.json", "post-pending.json", "post-full-generation.json", "quote-unavailable.json"}
    require(len(packets) == 8 and {Path(row["path"]).name for row in packets} == names,
            "All eight actual production-serializer output packets are required")
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


def profile_expansion_contract(value, refs, root, commit, machine, old_profile, profile):
    """A flag change needs a source-reviewed contract plus exact actual receipts."""
    if profile.get("flags") == old_profile.get("flags"):
        return None
    require(value.get("profile_expansion"),
            "This public native refresh preserves the prior reviewed full feature profile; profile expansion needs separate review")
    ref = checked(value["profile_expansion"])
    actual = read(ref["path"])
    require(actual.get("schema") == "ck3-native-profile-expansion-v1"
            and actual.get("machine_id") == machine and actual.get("source_commit") == value["source_commit"]
            and actual.get("actual_live_business_qualified") is False,
            "Profile expansion must bind the actual final native compile commit and machine")
    contract_ref = checked(actual["contract"])
    contract_path = (root / PROFILE_EXPANSION_RELATIVE).resolve()
    require(Path(contract_ref["path"]).resolve() == contract_path,
            "Profile expansion contract must be the common committed source contract")
    committed = subprocess.run(["git", "show", value["source_commit"] + ":" + PROFILE_EXPANSION_RELATIVE],
                               cwd=root, capture_output=True, check=True).stdout
    require(sig(committed) == {k: contract_ref[k] for k in ("bytes", "sha256")},
            "Profile expansion contract differs from the actual native compile commit")
    contract = read(contract_path)
    require(contract.get("schema") == "ck3-native-profile-expansion-contract-v1"
            and actual.get("contract_id") == contract.get("contract_id"), "Reviewed profile expansion contract identity differs")
    checked(actual["previous_profile"])
    require(read(actual["previous_profile"]["path"]) == old_profile
            and old_profile.get("flags") == contract.get("before_flags"), "Profile expansion prior profile differs")
    for name in ("profile", "snapshot", "configured_scope", "production_freeze"):
        require(actual.get(name) == refs[name], "Profile expansion actual pin differs: " + name)
    require(actual.get("fixture_results") == value.get("fixture_results"),
            "Profile expansion finite execution pins differ")
    expected = dict(old_profile["flags"])
    changes = contract.get("flag_changes", {})
    require(changes, "Empty profile expansion cannot authorize changed flags")
    for name, change in changes.items():
        before = change["before"]
        require((name not in expected) if before is None else expected.get(name) == before,
                "Reviewed profile expansion prior flag differs: " + name)
        expected[name] = change["after"]
    require(profile.get("flags") == expected, "Profile expansion changes flags outside the reviewed exact delta")
    return {"ref": ref, "actual": actual, "contract": contract}


def profile_expansion_scope(expansion, production, targets, snapshot_root, indexed, fixtures):
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
        require({targets[key]["name"] for key in closure} == set(row["dependency_targets"]),
                "Expanded profile fixture dependency closure differs: " + name)
        bodies.update(relative for relative, _ in sources)
        bodies.update(contract.get("fixture_included_bodies", {}).get(name, []))
    expected = {relative: indexed[relative] for relative in sorted(bodies)}
    require(expansion["actual"].get("fixture_source_bindings") == expected,
            "Expanded profile finite direct/included body pins differ from actual frozen source")


def qualify_native(path, root, commit, machine, previous_dll, previous_manifest):
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
    expansion = profile_expansion_contract(value, refs, root, commit, machine, old_profile, profile)
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
    require(Path(snapshot["Root_native_source_base"]).resolve() == native_root, "Snapshot is from another Root native tree")
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=root,
                            capture_output=True, text=True, check=True).stdout
    require(head == commit and not status.strip(), "Actual current Root must be clean at the exact qualified commit")
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", native_commit, commit], cwd=root, capture_output=True)
    require(ancestor.returncode == 0, "Native compile commit must be a proven ancestor of current Root; native bytes are checked independently")
    tracked_raw = subprocess.run(["git", "ls-files", "-z", "--", NATIVE_PREFIX], cwd=root,
                                 capture_output=True, check=True).stdout.decode("utf-8")
    tracked = {name[len(NATIVE_PREFIX):] for name in tracked_raw.split("\0") if name}
    declared_root = {row["native_relative"] for row in rows if "source" not in row}
    require(tracked == declared_root, "Frozen native manifest omitted or added current Root tracked inputs")
    snapshot_root = Path(snapshot["snapshot_native_base"]).resolve()
    indexed = {}
    for row in rows:
        relative = safe_relative(row["native_relative"])
        require(relative not in indexed, "Duplicate frozen native source")
        current_snapshot = checked({"path": str(snapshot_root / relative), "bytes": row["bytes"], "sha256": row["sha256"]})
        original = row.get("original_source_pin")
        if original:
            require(relative == "CMakeLists.txt", "Only a separately identified test-registration CMake derivative is allowed")
            require(Path(original["path"]).resolve() == native_root / relative, "Original CMake source belongs to another tree")
            checked(original)
        elif "source" not in row:
            original = {"path": str(native_root / relative), "bytes": row["bytes"], "sha256": row["sha256"]}
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
    profile_expansion_scope(expansion, production, actual_targets, snapshot_root, indexed, fixtures)
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
            "execution_wire": execution_wire, "profile_expansion": expansion["ref"] if expansion else None}


def project_host(root, old_host, old_runtime, new_runtime, source_files):
    canonical_raw = (root / HOST_RELATIVE).read_bytes()
    require(sig(canonical_raw) == source_files[HOST_RELATIVE], "Actual global host differs from the selected source index")
    canonical = canonical_raw.removeprefix(BOM).decode("utf-8")
    previous = old_host.read_text(encoding="utf-8-sig")
    marker = "# Explicit static normal-exit binding projection; ordinary shared host remains above."
    require(previous.count(marker) == 1, "Existing shared normal-exit projection boundary differs")
    tail = previous[previous.index(marker):]
    assignments = [node.value for node in ast.walk(ast.parse(tail)) if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == "_runtime_path" for target in node.targets)]
    require(len(assignments) == 1 and isinstance(assignments[0], ast.Call)
            and isinstance(assignments[0].func, ast.Name) and assignments[0].func.id == "Path"
            and len(assignments[0].args) == 1 and isinstance(assignments[0].args[0], ast.Constant)
            and isinstance(assignments[0].args[0].value, str), "Unique literal existing runtime binding required")
    bound_path = Path(assignments[0].args[0].value).resolve()
    bound_runtime, selected_runtime = read(bound_path), read(old_runtime)
    bound_manifest = read(checked(bound_runtime["manifest"])["path"])
    selected_manifest = read(checked(selected_runtime["manifest"])["path"])
    require(all(bound_manifest[key] == selected_manifest[key] for key in
                ("host", "source_root", "source_index", "native_source_index", "native", "game")),
            "A recording clone must retain the existing actual global source/native host binding")
    old_binding = "Path(" + repr(str(bound_path)) + ")"
    require(tail.count(old_binding) == 1, "Unique previous runtime projection path differs")
    tail = tail.replace(old_binding, "Path(" + repr(str(new_runtime)) + ")", 1)
    sentinel = 'if __name__ == "__main__":\n    raise SystemExit(main())'
    require(canonical.count(sentinel) == 1, "Actual shared host entry boundary differs")
    result = canonical.replace(sentinel, "", 1).rstrip() + "\n\n" + tail
    ast.parse(result)
    return BOM + result.encode("utf-8")


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


def main(argv=None):
    sys.dont_write_bytecode = True
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("base-runtime", "source-delta", "scene-root", "storage-admission", "products", "case-inputs", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--qualified-native", type=Path, required=True, help="exact actual native production-build qualification")
    parser.add_argument("--task-prefix", default="ck3-acceptance-")
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--product", required=True)
    parser.add_argument("--case", required=True)
    parser.add_argument("--qualification", action="append", default=[], metavar="CHAIN=ACTUAL_RECEIPT")
    parser.add_argument("--native-profile", type=Path, help="actual qualified global native profile when new required tools need their compiled flags checked")
    parser.add_argument("--input-binder-command", type=Path, help="optional JSON argv for the independently selected public case input hook")
    args = parser.parse_args(argv)
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
    files, required, changed_paths = apply_delta(args.source_delta, args.base_runtime, manifest, source, root, args.source_commit)
    delta = read(args.source_delta)
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
    native_bundle = qualify_native(args.qualified_native, root, args.source_commit, machine, refs["dll"], manifest)
    required.discard("new_native_base_required")
    if native_bundle["execution_wire"]:
        required.add("pilgrimage_wire_seam")
    require(required <= set(receipts), "Missing actual changed-chain qualifications: " + str(sorted(required - set(receipts))))
    qualified = {chain: qualify(chain, receipts[chain], args.source_commit, root, changed_paths, machine) for chain in sorted(required)}
    if native_bundle["execution_wire"]:
        actual_sdk = read(receipts["pilgrimage_wire_seam"])
        require(actual_sdk.get("actual_execution_wire_packets") == native_bundle["execution_wire"]["ref"],
                "Current SDK seam must actually consume these new qualified native serializer outputs")
    index_only = check_index_only_changes(root, changed_paths)
    products = read(args.products)
    cases = [case for case in products["products"][args.product]["cases"] if case["id"] == args.case]
    require(len(cases) == 1, "Exactly one independent public product case required")
    case = cases[0]
    needed = set(case["required_mcp_tools"])
    needed = set(case["required_mcp_tools"])
    old_profile = native_bundle["old_profile"]
    native_profile = native_bundle["profile"]
    capabilities = {}
    for tool in sorted(set(manifest.get("capabilities", {})) | needed):
        if tool not in manifest.get("capabilities", {}):
            require(tool in EXTRA_CAPABILITIES, "Unreviewed global capability rule: " + tool)
            for flag in EXTRA_CAPABILITIES[tool]:
                require(native_profile["flags"].get(flag) == "ON", "Qualified profile lacks required flag: " + flag)
        capabilities[tool] = {"source_build_ready": True, "actual_live_qualified": False,
            "actual_global_native_profile": native_bundle["profile_ref"],
            "actual_production_freeze": native_bundle["freeze_ref"],
            "native_input_identity_evidence": native_bundle["qualification_ref"],
            "native_DLL": native_bundle["dll"],
            "scope": "exact shared production build and finite native fixtures; no live business credit"}
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
    new_manifest.update(observed_at_utc=now(), source_commit=args.source_commit, capabilities=capabilities,
                        qualification_scope="new exact qualified global production DLL; changed source chains qualified independently; live results pending")
    new_manifest["host"] = {"path_key": "host", **sig(host_raw)}
    new_manifest["source_index"] = {"path_key": "source_index", "bytes": source_ref["bytes"], "sha256": source_ref["sha256"]}
    new_manifest["native_source_index"] = {"path_key": "native_source_index", "bytes": native_ref["bytes"], "sha256": native_ref["sha256"]}
    new_manifest["native"] = {**manifest["native"], "dll": {"path_key": "dll", "bytes": native_bundle["dll"]["bytes"], "sha256": native_bundle["dll"]["sha256"]}}
    new_manifest["native_input_identity_evidence"] = native_bundle["qualification_ref"]
    new_manifest["native_compile_source_commit"] = native_bundle["compile_commit"]
    new_manifest["native_compile_working_tree_dirty"] = False
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
        "builder_program": pin(__file__),
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
    require(sum(len(raw) for raw in output.values()) + 32768 <= 1024 * 1024, "New scene runtime metadata exceeds 1MiB estimated budget")
    require(pin(args.storage_admission) == grant_pin, "Fresh grant changed during metadata generation")
    destination.mkdir(parents=False)
    for name, raw in output.items():
        with (destination / name).open("xb") as stream:
            stream.write(raw)
    entry = module(root / "tools/ck3_mod_acceptance.py", "qualified_actual_public_entry")
    selection = entry.Selection(destination / "runtime.local.json", args.products, args.product, args.case)
    adapter = selection.load_adapter()
    inputs = read(args.case_inputs).get("case_inputs", {}) if args.case_inputs.exists() else {}
    adapter.validate_contract(selection.adapter_context(inputs=inputs))
    require(set(selection.case["required_mcp_tools"]) <= set(new_manifest["capabilities"]), "Required global capability evidence missing")
    # Register the unchanged real global MCP factory against an offline facade.
    # No method other than capabilities may run; list_tools is registration only.
    import asyncio
    from xar_autoplayer.bridge.mcp_server import create_server

    async def registered_names():
        return {row.name for row in await create_server(registration_driver(selection.case)).list_tools()}

    registered = asyncio.run(registered_names())
    require(needed <= registered, "Actual global MCP factory does not register required case tools: " + str(sorted(needed - registered)))
    missing = sorted({v for v in selection.argv if v.startswith("--")} - entry.host_cli_flags(destination / "shared-host.py"))
    require(not missing, "Current global host lacks actual public Selection CLI: " + str(missing))
    require(all(v == "Saved campaign input unbound: product_inventory" for v in selection.blockers),
            "Unexpected public Selection blockers: " + str(selection.blockers))
    with (destination / "STATIC-VALIDATION.actual.json").open("xb") as stream:
        stream.write(encoded({"machine_id": machine, "observed_at_utc": now(), "source_commit": args.source_commit,
            "independent_case": args.case, "public_Selection_argv": selection.argv,
            "actual_Selection_blockers": selection.blockers, "actual_changed_chain_receipts": qualified,
            "actual_registered_required_MCP_tools": sorted(needed), "registration_scope": "offline factory list_tools only; no game or tool invocation",
            "case_private_host": False, "prepare_executed": False, "game_started": False, "allocated": False,
            "runtime": pin(destination / "runtime.local.json"), "manifest": pin(destination / "manifest.json")}))
    print(json.dumps({"runtime": pin(destination / "runtime.local.json"), "entry": pin(destination / "ENTRY-COMMANDS.json"),
                      "case": args.case, "required_qualified_chains": sorted(required), "game_started": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
