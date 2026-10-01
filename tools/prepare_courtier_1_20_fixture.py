#!/usr/bin/env python3
"""Prepare isolated production mounts and UI-observed fixtures; never launch CK3."""
from __future__ import annotations
import argparse
import codecs
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import build_release as main_builder
import build_vivhite_release as vivhite_builder
from fixture_engine_prepare import BUILD, EXE_SHA256, VERSION, checked_output

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "tools/fixtures/vivhite_acceptance"
SCENARIOS = ("main-ui", "vivhite-ui", "dual-original-first", "dual-vivhite-first", "main-writer", "main-reader")
STANDALONE_MARKERS = ["ERVA: TEST BEGIN standalone", "ERVA: TEST PASS ai_fixture_ready", "ERVA: TEST PASS ai_guard", "ERVA: TEST PASS cancel_zero_side_effect", "ERVA: TEST PASS insufficient_119_blocked", "ERVA: TEST PASS default_120_one_delivery_one_charge", "ERVA: TEST PASS selected_faith_aluk", "ERVA: TEST PASS custom_348_ready", "ERVA: TEST PASS custom_configuration_retained", "ERVA: TEST PASS custom_configuration_reopened", "ERVA: TEST PASS custom_348_one_delivery_one_charge", "ERVA: TEST DONE standalone"]
DUAL_MARKERS = ["ERVA: TEST BEGIN dual", "ERVA: TEST PASS ai_fixture_ready", "ERVA: TEST PASS ai_guard", "ERVA: TEST PASS ervc_custom_348_staged", "ERVA: TEST PASS ervc_configuration_retained", "ERVA: TEST PASS xar_default_isolated_from_ervc", "ERVA: TEST PASS xar_configuration_retained", "ERVA: TEST PASS ervc_state_retained_after_xar", "ERVA: TEST PASS ervc_348_one_delivery_one_charge", "ERVA: TEST PASS xar_state_retained_after_ervc", "ERVA: TEST PASS xar_120_one_delivery_one_charge", "ERVA: TEST DONE dual"]


def write(path: Path, text: str, *, bom: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((codecs.BOM_UTF8 if bom else b"") + text.encode("utf-8"))


def strip_dual(text: str, include: bool) -> str:
    result = []
    inside = False
    for line in text.splitlines(keepends=True):
        if line.strip() == "# ERVA_DUAL_ONLY_BEGIN":
            if inside:
                raise ValueError("nested dual region")
            inside = True
        elif line.strip() == "# ERVA_DUAL_ONLY_END":
            if not inside:
                raise ValueError("unpaired dual region")
            inside = False
        elif include or not inside:
            result.append(line)
    if inside:
        raise ValueError("unclosed dual region")
    return "".join(result)


def assertion(condition: str, marker: str) -> str:
    return f'if = {{ limit = {{ {condition} }} debug_log = "CCA120: PASS {marker}" }} else = {{ debug_log = "CCA120: FAIL {marker}" }}'


def extra_ui_effects(prefix: str) -> str:
    return f'''cca120_metadata_and_migration_effect = {{
    {prefix}_cc_initialize_effect = yes
    {prefix}_cc_rebuild_trait_catalogs_effect = yes
    {prefix}_cc_rebuild_culture_faith_catalogs_effect = yes
    {assertion(f"variable_list_size = {{ name = {prefix}_cc_catalog_other value = 110 }} is_target_in_variable_list = {{ name = {prefix}_cc_catalog_other target = trait:erudite }} is_target_in_variable_list = {{ name = {prefix}_cc_catalog_other target = trait:lifestyle_scholar }} is_target_in_variable_list = {{ name = {prefix}_cc_catalog_other target = trait:herald }}", "new_trait_catalog")}
    remove_variable = {prefix}_cc_selected_rite
    {prefix}_cc_rebuild_culture_faith_catalogs_effect = yes
    {assertion(f"var:{prefix}_cc_selected_rite = root.rite", "legacy_same_faith_rite")}
    set_variable = {{ name = {prefix}_cc_selected_faith value = faith:aluk }}
    remove_variable = {prefix}_cc_selected_rite
    {prefix}_cc_rebuild_culture_faith_catalogs_effect = yes
    {assertion(f"var:{prefix}_cc_selected_rite = faith:aluk.main_rite var:{prefix}_cc_selected_rite.faith = faith:aluk", "legacy_other_faith_main_rite")}
    remove_character_flag = {prefix}_cc_v2_initialized
    {prefix}_cc_initialize_effect = yes
}}

# This seeds a legitimate retained design; it does not pretend a Rite picker exists.
cca120_prepare_branch_effect = {{
    remove_variable = cca120_branch_rite
    remove_variable = cca120_branch_faith
    random_living_character = {{
        limit = {{ exists = rite NOT = {{ rite = faith.main_rite }} }}
        save_scope_as = cca120_branch_carrier
        root = {{
            set_variable = {{ name = cca120_branch_rite value = scope:cca120_branch_carrier.rite }}
            set_variable = {{ name = cca120_branch_faith value = scope:cca120_branch_carrier.faith }}
        }}
    }}
    if = {{
        limit = {{ exists = var:cca120_branch_rite }}
        remove_character_flag = {prefix}_cc_v2_initialized
        {prefix}_cc_initialize_effect = yes
        {prefix}_cc_rebuild_trait_catalogs_effect = yes
        {prefix}_cc_rebuild_culture_faith_catalogs_effect = yes
        set_variable = {{ name = {prefix}_cc_selected_faith value = var:cca120_branch_faith }}
        set_variable = {{ name = {prefix}_cc_selected_rite value = var:cca120_branch_rite }}
        every_courtier = {{ add_character_flag = cca120_branch_baseline }}
        erva_acceptance_zero_gold_effect = yes
        add_gold = 1000
        add_character_flag = cca120_branch_ready
        debug_log = "CCA120: READY nondefault_rite_retained_design"
    }}
    else = {{ debug_log = "CCA120: SKIP no_existing_nondefault_rite" }}
}}

cca120_verify_branch_effect = {{
    set_variable = {{ name = cca120_branch_delivery_count value = 0 }}
    every_courtier = {{
        limit = {{ NOT = {{ has_character_flag = cca120_branch_baseline }} }}
        root = {{ change_variable = {{ name = cca120_branch_delivery_count add = 1 }} }}
    }}
    {assertion(f"NOT = {{ has_character_flag = {prefix}_cc_open }} gold >= 880 gold < 881 var:cca120_branch_delivery_count = 1 NOT = {{ var:cca120_branch_rite = var:cca120_branch_faith.main_rite }} var:{prefix}_cc_selected_rite = var:cca120_branch_rite any_courtier = {{ NOT = {{ has_character_flag = cca120_branch_baseline }} is_courtier_of = root culture = root.culture faith = root.var:cca120_branch_faith rite = root.var:cca120_branch_rite has_trait = education_martial_3 }}", "nondefault_rite_one_delivery_one_charge")}
}}
'''


def make_decision(key: str, effect: str, guard: str, picture: str) -> str:
    return f'''{key} = {{
    picture = {{ reference = "{picture}" }}
    decision_group_type = cca120
    ai_check_interval = 0
    is_shown = {{ is_ai = no is_alive = yes {guard} }}
    is_valid = {{ is_ai = no is_alive = yes {guard} }}
    effect = {{ {effect} }}
    ai_potential = {{ always = no }}
}}
'''


def prepare(args: argparse.Namespace) -> dict:
    _, output = checked_output(ROOT, args.output)
    if args.scenario != "main-reader" and (args.tutorial_from or args.expected_record is not None):
        raise ValueError("tutorial handoff/expected record are main-reader-only")
    if args.scenario == "main-reader" and (not args.tutorial_from or args.expected_record is None):
        raise ValueError("reader needs actual writer tutorial bytes and its observed record")
    output.mkdir(parents=True)
    content = output / "content"
    userdir = output / "userdir"
    fixture = content / "fixture"
    dual = args.scenario.startswith("dual-")
    main = args.scenario.startswith("main-")
    order = (["main", "vivhite"] if args.scenario == "dual-original-first" else
             ["vivhite", "main"] if dual else ["main"] if main else ["vivhite"])
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    for key in order:
        builder = main_builder if key == "main" else vivhite_builder
        builder.build_release(builder.DEFAULT_SOURCE, content / key, revision=revision)
    ui = args.scenario.endswith("ui") or dual
    if ui:
        for source in sorted(SOURCE.rglob("*")):
            if not source.is_file():
                continue
            target = fixture / source.relative_to(SOURCE)
            if source.suffix.lower() in {".txt", ".gui", ".yml"}:
                text = strip_dual(source.read_text(encoding="utf-8-sig"), dual)
                if main:
                    text = text.replace("ervc", "xar").replace("ERVC", "XAR")
                    if source.name == "erva_acceptance_events.txt":
                        text = text.replace("immediate = {", "immediate = {\n add_character_flag = xa_enabled", 1)
                if dual and source.name == "erva_acceptance_triggers.txt":
                    text = text.replace("\tfaith = root.var:xar_cc_selected_faith\n", "\tfaith = root.var:xar_cc_selected_faith\n\trite = root.var:xar_cc_selected_rite\n")
                write(target, text)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        p = "xar" if main else "ervc"
        setup = ("set_global_variable = { name = xa_global_record_imported value = 0 } xar_initialize_challenge_mode_effect = yes xar_enable_player_pact_effect = yes xar_initialize_run_state_effect = yes" if main else "")
        setup += f" cca120_metadata_and_migration_effect = yes add_character_flag = erva_acceptance_start_pending erva_acceptance_initialize_effect = yes"
        write(fixture / "common/scripted_effects/cca120_effects.txt", extra_ui_effects(p))
        picture = f"gfx/interface/illustrations/decisions/decision_{p}_courtier.dds"
        decisions = make_decision("cca120_prepare_branch", "cca120_prepare_branch_effect = yes", f"NOT = {{ has_character_flag = {p}_cc_open }}", picture)
        decisions += make_decision("cca120_verify_branch", "cca120_verify_branch_effect = yes", "has_character_flag = cca120_branch_ready", picture)
        write(fixture / "common/decisions/cca120_decisions.txt", decisions)
        write(fixture / "common/decision_group_types/cca120_groups.txt", "cca120 = { sort_order = 151 gui_tags = { big_button } }\n")
        for language in ("english", "simp_chinese"):
            write(fixture / f"localization/{language}/cca120_l_{language}.yml", f'''l_{language}:
 decision_group_type_cca120:0 "CK3 1.20 creator fixture"
 cca120_prepare_branch:0 "Prepare retained non-default Rite design"
 cca120_prepare_branch_desc:0 "Fixture data only. Then open the production creator and confirm through its GUI."
 cca120_prepare_branch_tooltip:0 "Prepare an existing non-default Rite design for a real production GUI purchase."
 cca120_prepare_branch_confirm:0 "Prepare"
 cca120_verify_branch:0 "Verify actual non-default Rite delivery"
 cca120_verify_branch_desc:0 "Click only after purchasing through the production creator GUI."
 cca120_verify_branch_tooltip:0 "Check the actual courtier, Rite and gold after the production GUI purchase."
 cca120_verify_branch_confirm:0 "Verify"
''')
    else:
        write(fixture / "descriptor.mod", 'name="CCA120 production persistence observer"\nversion="1"\nsupported_version="1.20.0.2"\n', bom=False)
        if args.scenario == "main-writer":
            setup = 'debug_log = "CCA120: READY real_pact_and_death_ui"'
            write(fixture / "common/on_action/cca120_death.txt", '''on_death = { on_actions = { cca120_observe_actual_death } }
cca120_observe_actual_death = { effect = { if = { limit = { has_character_flag = cca120_death_armed } debug_log = "CCA120: OBSERVED actual_player_death" } } }
''')
            write(fixture / "common/decisions/cca120_decisions.txt", make_decision("cca120_arm_death", 'add_prestige = 5000 add_character_flag = cca120_death_armed debug_log = "CCA120: READY actual_death_after_score_growth"', "has_character_flag = xa_enabled", "gfx/interface/illustrations/decisions/decision_xar_courtier.dds"))
            write(fixture / "common/decision_group_types/cca120_groups.txt", "cca120 = { sort_order = 151 gui_tags = { big_button } }\n")
            for language in ("english", "simp_chinese"):
                write(fixture / f"localization/{language}/cca120_l_{language}.yml", f'''l_{language}:
 decision_group_type_cca120:0 "CK3 1.20 persistence fixture"
 cca120_arm_death:0 "Arm actual death with score growth"
 cca120_arm_death_desc:0 "Adds prestige; does not call scoring or death effects. Use the actual engine death path afterward."
 cca120_arm_death_tooltip:0 "Add the prestige fixture and observe the next actual engine death."
 cca120_arm_death_confirm:0 "Arm"
''')
        else:
            setup = assertion(f"global_var:xa_import_consumed = 1 global_var:xa_global_record_imported = {args.expected_record} global_var:xa_inheritance_percent = 100", "actual_process_restart_import")
            tutorial = args.tutorial_from.resolve()
            if not tutorial.is_file() or tutorial == ROOT or ROOT in tutorial.parents:
                raise ValueError("reader needs an external isolated writer tutorial file")
            (userdir).mkdir(parents=True, exist_ok=True)
            shutil.copy2(tutorial, userdir / "tutorial.txt")
    write(fixture / "common/on_action/cca120_start.txt", '''on_game_start_after_lobby = { on_actions = { cca120_start } }
cca120_start = { effect = { every_player = { trigger_event = { id = cca120.1 days = 1 } } } }
''')
    write(fixture / "events/cca120_events.txt", f'''namespace = cca120
cca120.1 = {{ hidden = yes immediate = {{ if = {{ limit = {{ is_ai = no NOT = {{ has_character_flag = cca120_started }} }} add_character_flag = cca120_started debug_log = "CCA120: BEGIN {args.scenario}" {setup} }} }} }}
''')
    moddir = userdir / "mod"
    moddir.mkdir(parents=True, exist_ok=True)
    enabled = []
    for key in (*order, "fixture"):
        target = content / key
        descriptor = (target / "descriptor.mod").read_text(encoding="utf-8-sig")
        if "remote_file_id" in descriptor:
            raise ValueError("descriptor contains Workshop identity")
        write(moddir / f"cca120_{key}.mod", descriptor.rstrip() + f'\npath="{target.as_posix()}"\n', bom=False)
        enabled.append(f"mod/cca120_{key}.mod")
    write(userdir / "dlc_load.json", json.dumps({"disabled_dlcs": [], "enabled_mods": enabled}, indent=2) + "\n", bom=False)
    rules = (["erva_acceptance_dual"] if dual else ["erva_acceptance_standalone"] if ui else [])
    if "main" in order:
        rules += ["xar_on" if not ui else "xar_off", "xar_inherit_100", "xar_score_growth"]
    write(userdir / "presets.txt", 'last_applied_rules={\n' + "\n".join(f'\t"{rule}"' for rule in rules) + '\n}\n', bom=False)
    receipt = {"schema_version": 1, "scenario": args.scenario, "repository_head": revision,
               "userdir": str(userdir), "mount_order": [*order, "fixture"], "game_rule_settings": rules,
               "launch_argv": [str(ROOT / "Crusader Kings III/binaries/ck3.exe"), "-debug_mode", f"-userdir={userdir}"],
               "game_version": VERSION, "steam_build_id": BUILD,
               "expected_executable_sha256": EXE_SHA256, "runtime_status": "NOT_RUN", "native_abi_used": False,
               "preparer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "entry": "on_game_start_after_lobby -> day 1 cca120.1; UI remains operator work",
               "coverage": "fixture setup and existing UI-state observers; actual GUI clicks/death/restart are required",
               "required_markers": ([f"CCA120: BEGIN {args.scenario}", "CCA120: PASS new_trait_catalog", "CCA120: PASS legacy_same_faith_rite", "CCA120: PASS legacy_other_faith_main_rite"] + (DUAL_MARKERS if dual else STANDALONE_MARKERS) if ui else ["CCA120: BEGIN main-writer", "CCA120: READY real_pact_and_death_ui", "CCA120: READY actual_death_after_score_growth", "CCA120: OBSERVED actual_player_death", "XAR: computing score on death", "XAR: new record, writing bit", "XAR: score event fired"] if args.scenario == "main-writer" else ["CCA120: BEGIN main-reader", "CCA120: PASS actual_process_restart_import"]),
               "optional_branch_markers": ["CCA120: READY nondefault_rite_retained_design", "CCA120: PASS nondefault_rite_one_delivery_one_charge"] if ui else [],
               "branch_uncovered_marker": "CCA120: SKIP no_existing_nondefault_rite" if ui else None,
               "read_only_production_input_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCE.rglob("*") if p.is_file()},
               "prepared_file_sha256": {p.relative_to(output).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.rglob("*")) if p.is_file()}}
    if args.tutorial_from:
        receipt["tutorial_handoff"] = {"source": str(args.tutorial_from.resolve()), "sha256": hashlib.sha256(args.tutorial_from.read_bytes()).hexdigest(), "expected_record": args.expected_record, "seeded_record": False}
    (output / "prepare.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=SCENARIOS, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tutorial-from", type=Path)
    parser.add_argument("--expected-record", type=int)
    args = parser.parse_args()
    if args.expected_record is not None and args.expected_record < 0:
        parser.error("expected record must be nonnegative")
    print(json.dumps(prepare(args), indent=2))


if __name__ == "__main__":
    main()
