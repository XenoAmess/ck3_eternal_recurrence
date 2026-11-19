"""Generate isolated scripted-war scenarios; never launch CK3 or edit production."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
import hashlib
import io
import json
from pathlib import Path
import sys
from typing import Literal, TypedDict

from product import ROOT, SUPPORTED_VERSION
sys.path.insert(0, str(ROOT / "tools"))
from extract_auto_upgrade_buildings import parse_clausewitz

Tier = Literal["all", "duchy", "kingdom", "empire"]
TIERS = (
    ("duchy", "d_capua", "c_capua", "c_napoli", "djct_capua_holder", "djct_napoli_holder"),
    ("kingdom", "k_sicily", "c_capua", "c_napoli", "djct_capua_holder", "djct_napoli_holder"),
    ("empire", "e_italy", "c_roma", "c_firenze", "djct_roma_holder", "djct_firenze_holder"),
)
OUTCOMES = ("attacker", "white_peace", "defender")
MARKER_SUFFIXES = ("ai_unavailable", "distinct_realms", "native_eligibility", "native_participants", "native_goal", "county_ownership", "war_ended", "outside_and_owned_unchanged")
BEGIN_MARKER = "DJCT: TEST BEGIN scripted-war-1128"
DONE_MARKER = "DJCT: TEST DONE scripted-war-1128"
CLAIMS_EXCLUDED = ("native declare-war UI", "normal declaration cost debit", "native peace entry", "production persisted truce duration", "automatic army behavior", "save/reload", "concurrent-war regression", "low prestige/resource GUI boundaries", "whole-product acceptance")


class FixtureContract(TypedDict):
    schema: Literal["djc.external-acceptance.v2"]
    player_history_id: Literal[1128]
    layer: str
    tier: Tier
    markers: list[str]
    claims_excluded: list[str]
    fixture_isolation: str
    requires_done_marker: str
    fresh_start_date: str
    nominal_completion_natural_day: int
    max_natural_days: int
    latest_date: str
    completion_event: str
    failure_event: str
    watchdog_event: str
    pause_boundary: str
    live: Literal["NOT_RUN"]


def reviewed_tier(value: object) -> Tier:
    if type(value) is str:
        if value == "all":
            return "all"
        if value == "duchy":
            return "duchy"
        if value == "kingdom":
            return "kingdom"
        if value == "empire":
            return "empire"
    raise ValueError("tier must be all, duchy, kingdom or empire")


def expected_markers(tier: Tier = "all") -> list[str]:
    reviewed_tier(tier)
    return [f"{name}_{outcome}_{suffix}" for name, *_ in TIERS if tier == "all" or name == tier
            for outcome in OUTCOMES for suffix in MARKER_SUFFIXES]


def fail(marker: str) -> str:
    return f'debug_log = "DJCT: TEST FAIL {marker}"\n        djct_stop_effect = yes'


def check(condition: str, marker: str) -> str:
    return f'''if = {{
        limit = {{ NOT = {{ has_variable = djct_failed }} }}
        if = {{
            limit = {{ {condition} }}
            debug_log = "DJCT: TEST PASS {marker}"
            change_variable = {{ name = djct_pass_count add = 1 }}
        }}
        else = {{ {fail(marker)} }}
    }}'''


def generated_files(tier: Tier = "all") -> dict[str, bytes]:
    tier = reviewed_tier(tier)
    selected = [row for row in TIERS if tier == "all" or row[0] == tier]
    first_stage = 10 + next(index for index, row in enumerate(TIERS) if row == selected[0]) * 30
    max_days = 48 if tier == "all" else 18
    nominal_days = 46 if tier == "all" else 16
    deadline = date(1066, 9, 15) + timedelta(days=max_days)
    latest_date = f"{deadline.year}.{deadline.month}.{deadline.day}"
    files: dict[str, bytes] = {}

    def add(relative: str, value: str, *, bom: bool = True) -> None:
        value = value.strip() + "\n"
        if relative.endswith(".txt"):
            parse_clausewitz(value)
        files[relative] = value.encode("utf-8-sig" if bom else "utf-8")

    add("descriptor.mod", f'version="1.0.1"\nname="De Jure Conquest external acceptance fixture ({tier})"\nsupported_version="{SUPPORTED_VERSION}"', bom=False)
    add("common/scripted_effects/djct_fixture_effects.txt", '''
# Fixture-only stop. No production flags, queued stock events or wars are cleared.
djct_stop_effect = {
    if = {
        limit = { NOT = { has_variable = djct_failed } }
        set_variable = { name = djct_failed value = 1 }
        random_player = { trigger_event = djct.900 }
    }
}
''')
    add("common/scripted_triggers/djct_fixture_triggers.txt", f'''
djct_can_continue_trigger = {{
    this = character:1128
    is_alive = yes
    is_ai = no
    NOT = {{ has_variable = djct_failed }}
    NOT = {{ has_variable = djct_finished }}
    current_date <= {latest_date}
}}
''')
    add("common/on_action/djct_on_actions.txt", f'''
# GENERATED FILE. Fresh external single-player 1066-09-15 only.
on_game_start_after_lobby = {{ on_actions = {{ djct_initialize }} }}
djct_initialize = {{
    effect = {{
        every_player = {{
            if = {{
                limit = {{ this = character:1128 is_ai = no is_alive = yes current_date = 1066.9.15 NOT = {{ has_variable = djct_started }} }}
                set_variable = {{ name = djct_started value = 1 }}
                set_variable = {{ name = djct_pass_count value = 0 }}
                trigger_event = {{ id = djct.1 days = 1 }}
                trigger_event = {{ id = djct.901 days = {max_days} }}
            }}
            else = {{ {fail('wrong_player_or_fresh_date_entry')} }}
        }}
    }}
}}
''')
    add("events/djct_init.txt", f'''
namespace = djct
djct.1 = {{
    type = character_event
    hidden = yes
    immediate = {{
        if = {{
            limit = {{ djct_can_continue_trigger = yes exists = title:c_capua.holder exists = title:c_napoli.holder exists = title:c_roma.holder exists = title:c_firenze.holder title:c_apulia.holder = root }}
            debug_log = "{BEGIN_MARKER}"
            set_variable = {{ name = djct_capua_holder value = title:c_capua.holder }}
            set_variable = {{ name = djct_napoli_holder value = title:c_napoli.holder }}
            set_variable = {{ name = djct_roma_holder value = title:c_roma.holder }}
            set_variable = {{ name = djct_firenze_holder value = title:c_firenze.holder }}
            set_variable = {{ name = djct_owned_holder value = title:c_apulia.holder }}
            if = {{
                limit = {{ var:djct_napoli_holder = {{ is_independent_ruler = yes }} }}
                set_variable = {{ name = djct_napoli_originally_independent value = 1 }}
                debug_log = "DJCT: PREP READBACK initial_napoli_independent TRUE"
            }}
            else = {{ debug_log = "DJCT: PREP READBACK initial_napoli_independent FALSE" }}
            create_title_and_vassal_change = {{ type = granted save_scope_as = djct_setup_change }}
            title:c_vannes = {{ change_title_holder = {{ holder = root.var:djct_capua_holder change = scope:djct_setup_change take_baronies = yes }} }}
            resolve_title_and_vassal_change = scope:djct_setup_change
            set_variable = {{ name = djct_stage value = {first_stage} }}
            set_variable = {{ name = djct_phase value = 0 }}
            trigger_event = {{ id = djct.{first_stage} days = 1 }}
        }}
        else = {{ {fail('initial_actor_or_titles')} }}
    }}
}}
''')
    for global_index, (name, goal, county_a, county_b, holder_a, holder_b) in enumerate(TIERS):
        if tier != "all" and name != tier:
            continue
        events = ["# GENERATED FILE: fixture only; never upload.\nnamespace = djct"]
        for outcome_index, outcome in enumerate(OUTCOMES):
            stage = 10 + global_index * 30 + outcome_index * 10
            cb = f"{name}_de_jure_greatwar"
            label = f"{name}_{outcome}"
            napoli = ''
            napoli_ready = ''
            if county_b == "c_napoli":
                napoli = '''
        # Only the historically independent Naples holder may be restored.
        # Other title holders, including HRE vassals, are never liberated.
        if = {
            limit = { var:djct_napoli_originally_independent = 1 var:djct_napoli_holder = { top_liege = root } }
            create_title_and_vassal_change = { type = independency save_scope_as = djct_napoli_independence add_claim_on_loss = no }
            var:djct_napoli_holder = { becomes_independent = { change = scope:djct_napoli_independence } }
            resolve_title_and_vassal_change = scope:djct_napoli_independence
        }
'''
                napoli_ready = 'var:djct_napoli_originally_independent = 1 var:djct_napoli_holder = { is_independent_ruler = yes }'
            events.append(f'''
djct.{stage} = {{
    type = character_event
    hidden = yes
    immediate = {{
        if = {{
            limit = {{ djct_can_continue_trigger = yes var:djct_stage = {stage} var:djct_phase = 0 }}
            add_prestige = 100000
            add_piety = 100000
            add_prestige_level = 5
            add_stress = -1000
            set_variable = {{ name = djct_case_primary value = root.var:{holder_a} }}
            set_variable = {{ name = djct_case_secondary value = root.var:{holder_b} }}
            create_title_and_vassal_change = {{ type = granted save_scope_as = djct_reset_change }}
            title:{county_a} = {{ change_title_holder = {{ holder = root.var:{holder_a} change = scope:djct_reset_change take_baronies = yes }} }}
            title:{county_b} = {{ change_title_holder = {{ holder = root.var:{holder_b} change = scope:djct_reset_change take_baronies = yes }} }}
            resolve_title_and_vassal_change = scope:djct_reset_change
            {napoli}
            var:djct_case_primary = {{ add_prestige = 100000 add_piety = 100000 add_prestige_level = 5 }}
            if = {{
                limit = {{ has_truce = var:djct_case_primary.top_liege }}
                debug_log = "DJCT: DIAGNOSTIC {label}_player_to_primary_truce_before TRUE"
                cancel_truce_one_way = var:djct_case_primary.top_liege
            }}
            else = {{ debug_log = "DJCT: DIAGNOSTIC {label}_player_to_primary_truce_before FALSE" }}
            set_variable = {{ name = djct_reset_date value = current_date }}
            add_character_flag = {{ flag = djct_reset_wait days = 2 }}
            set_variable = {{ name = djct_phase value = 1 }}
            debug_log = "DJCT: PREP {label}_reset_then_wait_two_natural_days"
            trigger_event = {{ id = djct.{stage+3} days = 2 }}
        }}
        else = {{ {fail(label+'_prepare_actor_phase_or_deadline')} }}
    }}
}}

djct.{stage+3} = {{
    type = character_event
    hidden = yes
    immediate = {{
        if = {{
            limit = {{
                djct_can_continue_trigger = yes var:djct_stage = {stage} var:djct_phase = 1
                NOT = {{ has_character_flag = djct_reset_wait }} stress = 0
                title:{county_a}.holder = var:{holder_a} title:{county_b}.holder = var:{holder_b}
                var:djct_case_primary = {{ is_alive = yes is_ai = yes }}
                var:djct_case_secondary = {{ is_alive = yes }}
                var:djct_case_primary.top_liege != root var:djct_case_secondary.top_liege != root
                NOT = {{ has_truce = var:djct_case_primary.top_liege }}
                prestige >= 100000 piety >= 100000 prestige_level >= 4
                NOT = {{ any_character_war = {{ using_cb = {cb} is_attacker = root }} }}
                title:c_vannes.holder = var:djct_capua_holder title:c_apulia.holder = var:djct_owned_holder
                {napoli_ready}
            }}
            set_variable = {{ name = djct_ready_date value = current_date }}
            debug_log = "DJCT: PREP READBACK {label}_owners_realms_stress_zero_wait_expired_resources_no_truce TRUE"
            debug_log = "DJCT: DIAGNOSTIC {label}_player_to_primary_truce_after FALSE"
            {check(f'var:djct_case_primary = {{ NOT = {{ can_declare_war = {{ defender = root casus_belli = {cb} target_titles = {{ title:{goal} }} }} }} }}', label+'_ai_unavailable')}
            {check('var:djct_case_primary.top_liege != var:djct_case_secondary.top_liege', label+'_distinct_realms')}
            {check(f'can_declare_war = {{ defender = var:djct_case_primary.top_liege casus_belli = {cb} target_titles = {{ title:{goal} }} }}', label+'_native_eligibility')}
            if = {{
                limit = {{ NOT = {{ has_variable = djct_failed }} }}
                start_war = {{ cb = {cb} target = var:djct_case_primary.top_liege target_title = title:{goal} }}
                set_variable = {{ name = djct_created_count value = 0 }}
                every_character_war = {{
                    limit = {{ using_cb = {cb} is_attacker = root }}
                    save_scope_as = djct_created_war
                    root = {{ change_variable = {{ name = djct_created_count add = 1 }} }}
                }}
                if = {{
                    limit = {{ var:djct_created_count = 1 exists = scope:djct_created_war }}
                    set_variable = {{ name = djct_current_war value = scope:djct_created_war }}
                    set_variable = {{ name = djct_phase value = 2 }}
                    trigger_event = {{ id = djct.{stage+1} days = 1 }}
                }}
                else = {{ {fail(label+'_war_created')} }}
            }}
        }}
        else = {{ {fail(label+'_prepared_readback')} }}
    }}
}}

djct.{stage+1} = {{
    type = character_event
    hidden = yes
    immediate = {{
        if = {{
            limit = {{ djct_can_continue_trigger = yes var:djct_stage = {stage} var:djct_phase = 2 has_variable = djct_current_war }}
            {check(f'var:djct_current_war = {{ using_cb = {cb} is_attacker = root is_defender = root.var:djct_case_primary.top_liege is_defender = root.var:djct_case_secondary.top_liege }}', label+'_native_participants')}
            {check(f'var:djct_current_war = {{ trigger_if = {{ limit = {{ has_variable = djc_goal_title }} var:djc_goal_title = title:{goal} }} trigger_else = {{ always = no }} }}', label+'_native_goal')}
            if = {{
                limit = {{ NOT = {{ has_variable = djct_failed }} }}
                var:djct_current_war = {{ end_war = {outcome} }}
                remove_variable = djct_current_war
                set_variable = {{ name = djct_phase value = 3 }}
                trigger_event = {{ id = djct.{stage+2} days = 1 }}
            }}
        }}
        else = {{ {fail(label+'_lost_war_scope_or_phase')} }}
    }}
}}
''')
            ownership = f'title:{county_a}.holder = root title:{county_b}.holder = root' if outcome == 'attacker' else f'title:{county_a}.holder = var:{holder_a} title:{county_b}.holder = var:{holder_b}'
            last = name == selected[-1][0] and outcome_index == 2
            finish = f'''if = {{
                limit = {{ var:djct_pass_count = {len(expected_markers(tier))} }}
                set_variable = {{ name = djct_finished value = 1 }}
                trigger_event = djct.800
            }}
            else = {{ {fail('final_marker_count')} }}''' if last else f'''set_variable = {{ name = djct_stage value = {stage+10} }}
            set_variable = {{ name = djct_phase value = 0 }}
            trigger_event = {{ id = djct.{stage+10} days = 1 }}'''
            events.append(f'''
djct.{stage+2} = {{
    type = character_event
    hidden = yes
    immediate = {{
        if = {{
            limit = {{ djct_can_continue_trigger = yes var:djct_stage = {stage} var:djct_phase = 3 }}
            {check(ownership, label+'_county_ownership')}
            {check(f'NOT = {{ any_character_war = {{ using_cb = {cb} is_attacker = root }} }}', label+'_war_ended')}
            {check('title:c_vannes.holder = var:djct_capua_holder title:c_apulia.holder = var:djct_owned_holder', label+'_outside_and_owned_unchanged')}
            if = {{
                limit = {{ NOT = {{ has_variable = djct_failed }} }}
                {finish}
            }}
        }}
        else = {{ {fail(label+'_result_actor_phase_or_deadline')} }}
    }}
}}
''')
        add(f"events/djct_{name}.txt", "\n".join(events))
    add("events/djct_terminal.txt", f'''
namespace = djct
# Known single-player visible Realm windows request the ordinary event pause.
# Actual date/window/paused status must be observed; no unknown pause API is used.
djct.800 = {{
    type = character_event
    theme = realm
    title = djct_done_title
    desc = djct_done_desc
    immediate = {{ debug_log = "{DONE_MARKER}" }}
    option = {{ name = djct_keep_paused }}
}}
djct.900 = {{
    type = character_event
    theme = realm
    title = djct_failed_title
    desc = djct_failed_desc
    immediate = {{ debug_log = "DJCT: TEST STOP failed_no_successor" }}
    option = {{ name = djct_keep_paused }}
}}
djct.901 = {{
    type = character_event
    hidden = yes
    immediate = {{
        if = {{
            limit = {{ NOT = {{ has_variable = djct_finished }} NOT = {{ has_variable = djct_failed }} }}
            {fail('natural_day_bound')}
        }}
    }}
}}
''')
    for language, done, failed, close in (
        ("english", "DJC scripted matrix finished; inspect exact markers", "DJC fixture stopped; preserve failure", "Close and keep the calendar paused"),
        ("simp_chinese", "法理征服脚本矩阵已结束，请核对实际标记", "法理征服夹具已停止，请保留失败", "关闭并保持日历暂停"),
    ):
        description = f"Fixture {tier}: scripted production-CB checks only. Maximum {max_days} natural days from 1066-09-15. Actual pause/date, logs, runtime identity and exit remain mandatory. Native GUI payment, peace, death, Save/Load and full product acceptance are NOT_RUN. Do not choose an unknown stock event or advance after this window."
        add(f"localization/{language}/djct_l_{language}.yml", f'l_{language}:\n djct_done_title:0 "{done}"\n djct_done_desc:0 "{description}"\n djct_failed_title:0 "{failed}"\n djct_failed_desc:0 "{description} No successor business event is queued after failure. Retain the exact failure marker."\n djct_keep_paused:0 "{close}"')
    contract: FixtureContract = {
        "schema": "djc.external-acceptance.v2", "player_history_id": 1128,
        "layer": "scripted-war-production-CB", "tier": tier, "markers": expected_markers(tier),
        "claims_excluded": list(CLAIMS_EXCLUDED),
        "fixture_isolation": "restore original target county holders; restore only originally independent Naples if it became the player's vassal; refill resources; reset stress and require actual stress=0; cancel only player-to-primary truce; wait two real days and require timed flag expiry, exact owners/top lieges, funds, no truce, then real can_declare_war. No forced start after any failure.",
        "requires_done_marker": DONE_MARKER, "fresh_start_date": "1066.9.15",
        "nominal_completion_natural_day": nominal_days, "max_natural_days": max_days,
        "latest_date": latest_date, "completion_event": "djct.800", "failure_event": "djct.900", "watchdog_event": "djct.901",
        "pause_boundary": "Known visible character_event/theme=realm requests ordinary single-player event pause at completion/failure. Actual paused date/window readback is mandatory; no new Native API is assumed. Default all exceeds Robert event day35: prefer three fresh tier runs with day18 bounds.",
        "live": "NOT_RUN",
    }
    files["fixture-contract.json"] = (json.dumps(contract, ensure_ascii=False, indent=2) + "\n").encode()
    return files


def main() -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--tier", choices=("all", "duchy", "kingdom", "empire"), default="all")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("fixture output already exists; use a fresh attempt")
    files = generated_files(reviewed_tier(args.tier))
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
