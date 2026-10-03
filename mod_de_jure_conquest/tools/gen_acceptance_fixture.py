"""Generate isolated scripted-war scenarios; never launch CK3 or edit production."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from product import ROOT
sys.path.insert(0, str(ROOT / "tools"))
from extract_auto_upgrade_buildings import parse_clausewitz

TIERS = (
    ("duchy", "d_capua", "c_capua", "c_napoli", "djct_capua_holder", "djct_napoli_holder"),
    ("kingdom", "k_sicily", "c_capua", "c_napoli", "djct_capua_holder", "djct_napoli_holder"),
    ("empire", "e_italy", "c_roma", "c_firenze", "djct_roma_holder", "djct_firenze_holder"),
)
OUTCOMES = ("attacker", "white_peace", "defender")


def check(condition: str, marker: str) -> str:
    return f'''if = {{
        limit = {{ {condition} }}
        debug_log = "DJCT: TEST PASS {marker}"
    }}
    else = {{ debug_log = "DJCT: TEST FAIL {marker}" }}'''


def generated_files() -> dict[str, bytes]:
    files = {}
    def add(relative: str, value: str, *, bom: bool = True):
        value = value.strip() + "\n"
        if relative.endswith(".txt"):
            parse_clausewitz(value)
        files[relative] = value.encode("utf-8-sig" if bom else "utf-8")
    add("descriptor.mod", 'version="1.0.0"\nname="De Jure Conquest external acceptance fixture"\nsupported_version="1.20.*"', bom=False)
    add("common/on_action/djct_on_actions.txt", '''
# GENERATED FILE: tools/gen_acceptance_fixture.py. Fixture only, never production.
on_game_start_after_lobby = { on_actions = { djct_initialize } }
djct_initialize = {
    effect = {
        every_player = {
            if = {
                limit = { this = character:1128 is_ai = no }
                trigger_event = { id = djct.1 days = 1 }
            }
            else = { debug_log = "DJCT: TEST FAIL wrong_player_entry" }
        }
    }
}
''')
    init = '''
# GENERATED FILE: external scripted-war fixture; setup is not production gameplay.
namespace = djct
djct.1 = {
    hidden = yes
    immediate = {
        debug_log = "DJCT: TEST BEGIN scripted-war-1128"
        set_variable = { name = djct_capua_holder value = title:c_capua.holder }
        set_variable = { name = djct_napoli_holder value = title:c_napoli.holder }
        set_variable = { name = djct_roma_holder value = title:c_roma.holder }
        set_variable = { name = djct_firenze_holder value = title:c_firenze.holder }
        set_variable = { name = djct_owned_holder value = title:c_apulia.holder }
        add_prestige = 100000
        add_piety = 100000
        add_prestige_level = 5
        create_title_and_vassal_change = { type = granted save_scope_as = djct_setup_change }
        title:c_vannes = {
            change_title_holder = {
                holder = root.var:djct_capua_holder
                change = scope:djct_setup_change
                take_baronies = yes
            }
        }
        resolve_title_and_vassal_change = scope:djct_setup_change
        trigger_event = { id = djct.10 days = 1 }
    }
}
'''
    add("events/djct_init.txt", init)
    markers = []
    stage = 10
    for tier_index, (tier, goal, county_a, county_b, holder_a, holder_b) in enumerate(TIERS):
        events = ["# GENERATED FILE: tools/gen_acceptance_fixture.py; never upload.\nnamespace = djct"]
        for outcome_index, outcome in enumerate(OUTCOMES):
            cb = f"{tier}_de_jure_greatwar"
            label = f"{tier}_{outcome}"
            next_stage = stage + 10
            prepare = f'''
djct.{stage} = {{
    hidden = yes
    immediate = {{
        add_prestige = 100000
        add_piety = 100000
        add_prestige_level = 5
        set_variable = {{ name = djct_case_primary value = root.var:{holder_a} }}
        set_variable = {{ name = djct_case_secondary value = root.var:{holder_b} }}
        create_title_and_vassal_change = {{ type = granted save_scope_as = djct_reset_change }}
        title:{county_a} = {{
            change_title_holder = {{ holder = root.var:{holder_a} change = scope:djct_reset_change take_baronies = yes }}
        }}
        title:{county_b} = {{
            change_title_holder = {{ holder = root.var:{holder_b} change = scope:djct_reset_change take_baronies = yes }}
        }}
        resolve_title_and_vassal_change = scope:djct_reset_change
        var:djct_case_primary = {{ add_prestige = 100000 add_piety = 100000 add_prestige_level = 5 }}
        {check(f'var:djct_case_primary = {{ NOT = {{ can_declare_war = {{ defender = root casus_belli = {cb} target_titles = {{ title:{goal} }} }} }} }}', label+'_ai_unavailable')}
        {check(f'var:djct_case_primary.top_liege != var:djct_case_secondary.top_liege', label+'_distinct_realms')}
        {check(f'can_declare_war = {{ defender = var:djct_case_primary.top_liege casus_belli = {cb} target_titles = {{ title:{goal} }} }}', label+'_native_eligibility')}
        start_war = {{ cb = {cb} target = var:djct_case_primary.top_liege target_title = title:{goal} }}
        every_character_war = {{
            limit = {{ using_cb = {cb} is_attacker = root }}
            save_scope_as = djct_created_war
        }}
        if = {{
            limit = {{ exists = scope:djct_created_war }}
            set_variable = {{ name = djct_current_war value = scope:djct_created_war }}
            trigger_event = {{ id = djct.{stage+1} days = 1 }}
        }}
        else = {{ debug_log = "DJCT: TEST FAIL {label}_war_created" }}
    }}
}}
'''
            inspect = f'''
djct.{stage+1} = {{
    hidden = yes
    immediate = {{
        if = {{
            limit = {{ has_variable = djct_current_war }}
            {check(f'var:djct_current_war = {{ using_cb = {cb} is_attacker = root is_defender = root.var:djct_case_primary.top_liege is_defender = root.var:djct_case_secondary.top_liege }}', label+'_native_participants')}
            {check(f'var:djct_current_war = {{ trigger_if = {{ limit = {{ has_variable = djc_goal_title }} var:djc_goal_title = title:{goal} }} trigger_else = {{ always = no }} }}', label+'_native_goal')}
            var:djct_current_war = {{ end_war = {outcome} }}
            remove_variable = djct_current_war
            trigger_event = {{ id = djct.{stage+2} days = 1 }}
        }}
        else = {{ debug_log = "DJCT: TEST FAIL {label}_lost_war_scope" }}
    }}
}}
'''
            ownership = f'title:{county_a}.holder = root title:{county_b}.holder = root' if outcome == 'attacker' else f'title:{county_a}.holder = var:{holder_a} title:{county_b}.holder = var:{holder_b}'
            finish = 'debug_log = "DJCT: TEST DONE scripted-war-1128"' if tier_index == 2 and outcome_index == 2 else f'trigger_event = {{ id = djct.{next_stage} days = 1 }}'
            result = f'''
djct.{stage+2} = {{
    hidden = yes
    immediate = {{
        {check(ownership, label+'_county_ownership')}
        {check(f'NOT = {{ any_character_war = {{ using_cb = {cb} is_attacker = root }} }}', label+'_war_ended')}
        {check('title:c_vannes.holder = var:djct_capua_holder title:c_apulia.holder = var:djct_owned_holder', label+'_outside_and_owned_unchanged')}
        {finish}
    }}
}}
'''
            events.extend([prepare, inspect, result])
            markers.extend(label + '_' + suffix for suffix in ['ai_unavailable', 'distinct_realms', 'native_eligibility', 'native_participants', 'native_goal', 'county_ownership', 'war_ended', 'outside_and_owned_unchanged'])
            stage += 10
        add(f"events/djct_{tier}.txt", "\n".join(events))
    files["fixture-contract.json"] = (json.dumps({
        "schema": "djc.external-acceptance.v1", "player_history_id": 1128,
        "layer": "scripted-war-production-CB", "markers": markers,
        "claims_excluded": ["native declare-war UI", "normal declaration cost debit", "automatic army behavior", "save/reload", "concurrent-war regression"],
        "requires_done_marker": "DJCT: TEST DONE scripted-war-1128",
        "live": "NOT_RUN",
    }, ensure_ascii=False, indent=2) + "\n").encode()
    return files


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("fixture output already exists; use a fresh attempt")
    files = generated_files()
    args.output.mkdir(parents=True)
    entries = []
    for relative, data in sorted(files.items()):
        path = args.output / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        entries.append({"path": relative, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    (args.output.parent / (args.output.name + ".manifest.json")).write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(files)} external fixture files at {args.output}; live NOT_RUN.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
