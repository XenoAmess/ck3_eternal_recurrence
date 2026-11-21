"""Generate isolated scripted-war scenarios; never launch CK3 or edit production."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
import hashlib
import io
import json
from pathlib import Path
import sys
from typing import Literal, NotRequired, TypedDict

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
    eligibility_failure_probe: NotRequired[Literal["READONLY-STATE-AND-ON-FAILURE"]]
    event_target_context: NotRequired[Literal["CLEAR-INHERITED-TARGET-BEFORE-NATIVE"]]


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


def check(condition: str, marker: str, failure_diagnostic: str = "") -> str:
    failed = (failure_diagnostic.rstrip() + " " if failure_diagnostic else "") + fail(marker)
    return f'''if = {{
        limit = {{ NOT = {{ has_variable = djct_failed }} }}
        if = {{
            limit = {{ {condition} }}
            debug_log = "DJCT: TEST PASS {marker}"
            change_variable = {{ name = djct_pass_count add = 1 }}
        }}
        else = {{ {failed} }}
    }}'''


def generated_files(tier: Tier = "all", *, diagnose_eligibility: bool = False,
                    clear_inherited_target: bool = False) -> dict[str, bytes]:
    tier = reviewed_tier(tier)
    if type(diagnose_eligibility) is not bool:
        raise ValueError("diagnose_eligibility must be a bool")
    if type(clear_inherited_target) is not bool:
        raise ValueError("clear_inherited_target must be a bool")
    if clear_inherited_target and not diagnose_eligibility:
        raise ValueError("clear_inherited_target requires explicit eligibility diagnosis")
    selected = [row for row in TIERS if tier == "all" or row[0] == tier]
    first_stage = 10 + next(index for index, row in enumerate(TIERS) if row == selected[0]) * 30
    max_days = 48 if tier == "all" else 18
    nominal_days = 46 if tier == "all" else 16
    deadline = date(1066, 9, 15) + timedelta(days=max_days)
    latest_date = f"{deadline.year}.{deadline.month}.{deadline.day}"
    files: dict[str, bytes] = {}
    # Capua is always an actual consumer: it owns the outside Vannes control.
    # Other holders exist only for the selected tier's original predicates.
    needed_holders = {"djct_capua_holder", *(holder for row in selected for holder in row[4:6])}
    holder_pairs = (("djct_capua_holder", "c_capua"), ("djct_napoli_holder", "c_napoli"),
                    ("djct_roma_holder", "c_roma"), ("djct_firenze_holder", "c_firenze"))
    holder_setup = "\n            ".join(f"set_variable = {{ name = {holder} value = title:{county}.holder }}" for holder, county in holder_pairs if holder in needed_holders)
    holder_guards = " ".join(f"exists = title:{county}.holder" for holder, county in holder_pairs if holder in needed_holders)
    napoli_initial = '''if = {
                limit = { var:djct_napoli_holder = { is_independent_ruler = yes } }
                set_variable = { name = djct_napoli_originally_independent value = 1 }
                debug_log = "DJCT: PREP READBACK initial_napoli_independent TRUE"
            }
            else = { debug_log = "DJCT: PREP READBACK initial_napoli_independent FALSE" }''' if "djct_napoli_holder" in needed_holders else ""

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
            limit = {{ djct_can_continue_trigger = yes {holder_guards} title:c_apulia.holder = root }}
            debug_log = "{BEGIN_MARKER}"
            {holder_setup}
            set_variable = {{ name = djct_owned_holder value = title:c_apulia.holder }}
            {napoli_initial}
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
            state_probe = f"djct_probe_{label}_state_effect = yes\n            " if diagnose_eligibility else ""
            failure_probe = f"djct_probe_{label}_failure_effect = yes " if diagnose_eligibility else ""
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
            debug_log = "DJCT: PREP READBACK {label}_owners_realms_stress_zero_wait_expired_resources_no_truce TRUE"
            debug_log = "DJCT: DIAGNOSTIC {label}_player_to_primary_truce_after FALSE"
            {state_probe}{check(f'var:djct_case_primary = {{ NOT = {{ can_declare_war = {{ defender = root casus_belli = {cb} target_titles = {{ title:{goal} }} }} }} }}', label+'_ai_unavailable')}
            {check('var:djct_case_primary.top_liege != var:djct_case_secondary.top_liege', label+'_distinct_realms')}
            {check(f'can_declare_war = {{ defender = var:djct_case_primary.top_liege casus_belli = {cb} target_titles = {{ title:{goal} }} }}', label+'_native_eligibility', f'djct_probe_{label}_failure_effect = yes' if diagnose_eligibility else '')}
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
        else = {{ {state_probe}{failure_probe}{fail(label+'_prepared_readback')} }}
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
    if diagnose_eligibility:
        add("common/scripted_effects/djct_eligibility_probes.txt", eligibility_probe_effects(tier, clear_inherited_target=clear_inherited_target))
        contract["eligibility_failure_probe"] = "READONLY-STATE-AND-ON-FAILURE"
    if clear_inherited_target:
        contract["event_target_context"] = "CLEAR-INHERITED-TARGET-BEFORE-NATIVE"
    files["fixture-contract.json"] = (json.dumps(contract, ensure_ascii=False, indent=2) + "\n").encode()
    return files


# Exact current stock government IDs, source-pinned in the a05 diagnostic review.
# A complete truth vector names the actual matching government without a guessed
# Native getter. A custom/unmatched government remains explicitly unresolved.
PROBE_GOVERNMENTS = ("feudal_government", "republic_government", "clan_government", "tribal_government", "wanua_government", "mercenary_government", "holy_order_government", "monastic_holy_order_government", "administrative_government", "landless_adventurer_government", "nomad_government", "herder_government", "celestial_government", "mandala_government", "steppe_admin_government", "meritocratic_government", "merchant_government", "japan_administrative_government", "japan_feudal_government", "theocracy_government", "ecclesiastical_government")


def probe_boolean(condition: str, label: str) -> str:
    return f'if = {{ limit = {{ {condition} }} debug_log = "DJCT: PROBE {label} TRUE" }} else = {{ debug_log = "DJCT: PROBE {label} FALSE" }}'


def eligibility_probe_effects(tier: Tier, *, clear_inherited_target: bool = False) -> str:
    """Finite readbacks; optional target-only evaluated-context normalization.

    No government, titles, money, truce, days or production predicates change.
    Only fixture-owned prefixed temporary aliases are introduced. The optional
    clear is disclosed separately from the read-only probe contract.
    """
    tier = reviewed_tier(tier)
    effects = ["# Optional read-only eligibility diagnosis; no TEST PASS credit."]
    roles = (("root", "root"), ("primary_original", "root.var:djct_case_primary"), ("primary_top", "root.var:djct_case_primary.top_liege"), ("secondary_original", "root.var:djct_case_secondary"), ("secondary_top", "root.var:djct_case_secondary.top_liege"))
    for name, goal, *_ in TIERS:
        if tier != "all" and tier != name:
            continue
        for outcome in OUTCOMES:
            label = name + "_" + outcome
            state = [f'debug_log = "DJCT: PROBE {label}_state_begin"', 'debug_log_date = yes']
            for role, scope in roles:
                state.append(probe_boolean('exists = ' + scope, label + '_' + role + '_exists'))
                observations = [(f'has_government = {government}', label + '_' + role + '_government_' + government) for government in PROBE_GOVERNMENTS]
                observations += [(predicate, label + '_' + role + '_' + key) for key, predicate in (
                    ('is_landed', 'is_landed = yes'), ('independent', 'is_independent_ruler = yes'),
                    ('is_playable', 'is_playable_character = yes'),
                    ('primary_title_landless', 'exists = primary_title primary_title ?= { is_landless_type_title = yes }'),
                    ('adventurer_flag', 'government_has_flag = government_is_landless_adventurer'),
                    ('merchant_flag', 'government_has_flag = government_is_merchant'))]
                body = '\n'.join(probe_boolean(predicate, key) for predicate, key in observations)
                state.append(f'if = {{ limit = {{ exists = {scope} }} {scope} = {{ {body} }} }} else = {{ debug_log = "DJCT: PROBE {label}_{role}_MISSING" }}')
            conditions = (
                ('root_raised_armies', 'has_raised_armies = yes'), ('root_in_debt', 'is_in_debt = yes'),
                ('root_government_allows_raised_troops', 'government_has_flag = can_start_war_with_raised_troops'),
                ('root_in_activity', 'is_in_activity = yes'), ('root_imprisoned', 'is_imprisoned = yes'),
                ('root_incapable', 'is_incapable = yes'), ('root_sworn_peace', 'has_character_flag = sworn_peace'),
                ('root_owns_goal', f'has_title = title:{goal}'),
                ('goal_expected_tier', f'title:{goal} = {{ tier = tier_{name} }}'),
                ('goal_landless_type', f'title:{goal} = {{ is_landless_type_title = yes }}'),
                ('root_in_range_primary', 'in_diplomatic_range = root.var:djct_case_primary.top_liege'),
                ('root_can_attack_hierarchy_primary', 'can_attack_in_hierarchy = root.var:djct_case_primary.top_liege'),
                ('root_allied_in_war_primary', 'is_allied_in_war = root.var:djct_case_primary.top_liege'),
                ('root_at_war_primary', 'is_at_war_with = root.var:djct_case_primary.top_liege'),
                ('root_truce_primary_top', 'has_truce = root.var:djct_case_primary.top_liege'),
                ('primary_top_truce_root', 'root.var:djct_case_primary.top_liege = { has_truce = root }'),
                ('root_rival_original_primary', 'has_relation_rival = root.var:djct_case_primary'),
                ('root_rival_original_secondary', 'has_relation_rival = root.var:djct_case_secondary'),
                ('primary_equals_its_top', 'var:djct_case_primary = var:djct_case_primary.top_liege'),
                ('secondary_equals_its_top', 'var:djct_case_secondary = var:djct_case_secondary.top_liege'),
                ('goal_has_primary_realm_county', f'title:{goal} = {{ any_de_jure_county = {{ exists = holder holder ?= {{ top_liege = root.var:djct_case_primary.top_liege }} }} }}'),
                ('goal_has_secondary_realm_county', f'title:{goal} = {{ any_de_jure_county = {{ exists = holder holder ?= {{ top_liege = root.var:djct_case_secondary.top_liege }} }} }}'),
                ('goal_holder_exists', f'exists = title:{goal}.holder'),
            )
            condition_body = '\n'.join(probe_boolean(predicate, label + '_' + key) for key, predicate in conditions)
            state.append(f'if = {{ limit = {{ exists = root.var:djct_case_primary.top_liege exists = root.var:djct_case_secondary.top_liege }} {condition_body} }} else = {{ debug_log = "DJCT: PROBE {label}_missing_top_blocks_pair_predicates" }}')
            # Save incoming identities before any new can_declare_war query.
            # One Root dump includes all prefixed role IDs and the incoming
            # target's real engine type; do not invent a generic type getter.
            context_roles = (*roles, ('goal', 'title:' + goal),
                ('root_capital', 'root.capital_province'),
                ('primary_capital', 'root.var:djct_case_primary.top_liege.capital_province'),
                ('incoming_target', 'scope:target'), ('incoming_adventurer', 'scope:adventurer'))
            for role, scope in context_roles:
                state.append(f'if = {{ limit = {{ exists = {scope} }} {scope} = {{ save_temporary_scope_as = djct_probe_frame_{role} }} }}')
            identities = ' '.join(f'scope:djct_probe_frame_{role} = {scope}' for role, scope in roles)
            identities += f' scope:djct_probe_frame_goal = title:{goal}'
            predicate = f'can_declare_war = {{ defender = root.var:djct_case_primary.top_liege casus_belli = {name}_de_jure_greatwar target_titles = {{ title:{goal} }} }}'
            state += [probe_boolean('exists = scope:target', label + '_context_incoming_target_exists'),
                'if = { limit = { exists = scope:target } '
                + probe_boolean(f'scope:target = title:{goal}', label + '_context_incoming_target_matches_goal')
                + f' }} else = {{ debug_log = "DJCT: PROBE {label}_context_incoming_target_matches_goal FALSE" }}',
                probe_boolean(identities, label + '_context_identity_before_clear'),
                probe_boolean(predicate, label + '_context_native_before_clear')]
            first_name = next(row[0] for row in TIERS if tier == 'all' or row[0] == tier)
            dump_condition = 'always = yes' if name == first_name and outcome == 'attacker' else f'NOT = {{ {predicate} }}'
            state.append(f'if = {{ limit = {{ {dump_condition} }} debug_log = "DJCT: PROBE {label}_incoming_context_single_root_dump" debug_log_scopes = yes }}')
            if clear_inherited_target:
                state += [f'debug_log = "DJCT: PROBE {label}_context_clear_target_only"',
                    'clear_saved_scope = target',
                    probe_boolean('exists = scope:target', label + '_context_target_exists_after_clear'),
                    probe_boolean(identities, label + '_context_identity_after_clear'),
                    f'if = {{ limit = {{ {identities} NOT = {{ exists = scope:target }} }} debug_log_date = yes '
                    + probe_boolean(predicate, label + '_context_native_after_clear') + '\n'
                    + probe_boolean('exists = scope:target', label + '_context_target_exists_after_native_query') + '\n'
                    + probe_boolean(identities, label + '_context_identity_after_native_query') + '\n'
                    + f'if = {{ limit = {{ NOT = {{ {identities} }} }} {fail(label + "_context_identity_changed_after_native_query")} }} '
                    + f'}} else = {{ {fail(label + "_context_identity_or_target_not_cleared")} }}']
            state += [f'debug_log = "DJCT: PROBE {label}_state_end"']
            body = '\n'.join(state)
            effects.append(f'djct_probe_{label}_state_effect = {{ if = {{ limit = {{ has_variable = djct_case_primary has_variable = djct_case_secondary }} {body} }} else = {{ debug_log = "DJCT: PROBE {label}_state_missing_holder_variables" }} }}')

            details = [f'debug_log = "DJCT: PROBE {label}_original_gate_failed_detail_begin"', 'debug_log_date = yes']
            # The state probe already captured one Root context with every role.
            # Repeating debug_log_scopes per holder copied the same global saved
            # targets eight times and did not add independent identity evidence.
            # scope:adventurer belongs to the stock letter/event context. It may
            # already be unavailable; never assign it from a guessed old holder.
            details.append(probe_boolean('exists = scope:adventurer', label + '_ambient_adventurer_exists'))
            links = [probe_boolean(f'scope:adventurer = {scope}', label + '_ambient_adventurer_matches_' + role) for role, scope in roles[1:]]
            details.append('if = { limit = { exists = scope:adventurer } ' + '\n'.join(links) + ' }')
            gated_details: list[str] = []
            for control_tier, control_goal, *_ in TIERS:
                predicate = f'can_declare_war = {{ defender = root.var:djct_case_primary.top_liege casus_belli = {control_tier}_de_jure_greatwar target_titles = {{ title:{control_goal} }} }}'
                gated_details.append(probe_boolean(predicate, label + '_control_' + control_tier + '_native_pre_alias'))
                gated_details.append(probe_boolean(f'has_title = title:{control_goal}', label + '_root_owns_' + control_goal))
            # Stock group/UI helpers require reserved actor/defender scopes.
            # A fixture cannot safely fabricate or overwrite these, especially
            # the permanent Dynasty-valued target actually observed in R2.
            gated_details.append(f'debug_log = "DJCT: PROBE {label}_stock_UI_group_helpers_omitted_unbound_reserved_scopes"')
            gated_body = '\n'.join(gated_details)
            details.append(f'if = {{ limit = {{ exists = root.var:djct_case_primary.top_liege }} {gated_body} }} else = {{ debug_log = "DJCT: PROBE {label}_missing_primary_top_no_native_control" }}')
            details.append(f'debug_log = "DJCT: PROBE {label}_failed_detail_end_not_a_repair"')
            body = '\n'.join(details)
            effects.append(f'djct_probe_{label}_failure_effect = {{ if = {{ limit = {{ has_variable = djct_case_primary has_variable = djct_case_secondary }} {body} }} else = {{ debug_log = "DJCT: PROBE {label}_failure_missing_holder_variables" }} }}')
    return '\n'.join(effects)


GUI_BASE_VALUES = ("djcg_phase", "djcg_tier", "djcg_date", "djcg_before_gold", "djcg_before_prestige", "djcg_before_piety", "djcg_after_gold", "djcg_after_prestige", "djcg_after_piety", "djcg_same_faith", "djcg_peace_of_god", "djcg_expected_extra_piety")
GUI_RELOAD_VALUES = ("djcg_reload_date", "djcg_reload_gold", "djcg_reload_prestige", "djcg_reload_piety")
GUI_REFERENCES = ("djcg_primary", "djcg_secondary", "djcg_goal", "djcg_war")
GUI_STANDALONE_VALUES = ("djcg_standalone", "djcg_setup_prestige", "djcg_setup_piety")
GUI_STANDALONE_BASE_VALUES = tuple(key for key in GUI_BASE_VALUES if key != "djcg_date")
GUI_STANDALONE_RELOAD_VALUES = tuple(key for key in GUI_RELOAD_VALUES if key != "djcg_reload_date")
GUI_STANDALONE_REFERENCES = ("djcg_setup_goal", "djcg_setup_capua_title", "djcg_setup_napoli_title", "djcg_setup_primary", "djcg_setup_secondary")
GUI_STANDALONE_SCHEMA = "djc.gui-ordinary-standalone-save.v2"
GUI_PHYSICAL_SCHEMA = "djc.physical-ordinary-s0-s1.v1"
GUI_PHYSICAL_SETUP_VALUES = ("djcg_standalone", "djcg_tier", "djcg_physical", "djcg_setup_gold", "djcg_setup_prestige", "djcg_setup_piety", "djcg_same_faith", "djcg_peace_of_god", "djcg_expected_extra_piety")
GUI_PHYSICAL_AFTER_VALUES = ("djcg_physical_captured", "djcg_war_count", "djcg_after_gold", "djcg_after_prestige", "djcg_after_piety")
GUI_PHYSICAL_AFTER_REFS = ("djcg_war", "djcg_actual_goal", "djcg_actual_attacker", "djcg_actual_primary", "djcg_actual_secondary")


def gui_observer_files(tier: Tier) -> dict[str, bytes]:
    """Companion only: never declare, settle, pay, save or load on the player's behalf."""
    tier = reviewed_tier(tier)
    if tier == "all":
        raise ValueError("GUI observer needs a single completed fresh tier")
    tier_index, row = next((index, row) for index, row in enumerate(TIERS) if row[0] == tier)
    _, goal, county_a, county_b, holder_a, holder_b = row
    cb = tier + "_de_jure_greatwar"
    files: dict[str, bytes] = {}

    def add(relative: str, text: str) -> None:
        text = text.strip() + "\n"
        if relative.endswith(".txt"):
            parse_clausewitz(text)
        files[relative] = text.encode("utf-8-sig")

    add("common/scripted_triggers/djcg_observer_triggers.txt", f'''
djcg_actor_trigger = {{
    this = character:1128 is_alive = yes is_ai = no
    var:djct_finished = 1 var:djct_pass_count = 24
    NOT = {{ has_variable = djct_failed }} NOT = {{ has_variable = djcg_failed }}
    current_date <= 1066.10.3
}}
djcg_real_gui_war_trigger = {{
    var:djcg_war = {{
        using_cb = {cb} is_attacker = root
        is_defender = root.var:djcg_primary is_defender = root.var:djcg_secondary
        has_variable = djc_goal_title var:djc_goal_title = title:{goal}
    }}
}}
''')
    add("common/scripted_effects/djcg_observer_effects.txt", f'''
# Only fixture variables change after the before snapshot. No start/end_war,
# resource payment/refill, date writes, save/load or production flag writes.
djcg_stop_effect = {{
    if = {{
        limit = {{ NOT = {{ has_variable = djcg_failed }} }}
        set_variable = {{ name = djcg_failed value = 1 }}
        debug_log = "DJCG: OBSERVE FAIL stopped"
        trigger_event = djcg.900
    }}
}}
djcg_prepare_gui_effect = {{
    if = {{
        limit = {{
            djcg_actor_trigger = yes NOT = {{ has_variable = djcg_phase }}
            title:{county_a}.holder = var:{holder_a} title:{county_b}.holder = var:{holder_b}
            var:{holder_a}.top_liege != root var:{holder_b}.top_liege != root
            var:{holder_a}.top_liege != var:{holder_b}.top_liege
            NOT = {{ any_character_war = {{ using_cb = {cb} is_attacker = root }} }}
        }}
        set_variable = {{ name = djcg_primary value = var:{holder_a}.top_liege }}
        set_variable = {{ name = djcg_secondary value = var:{holder_b}.top_liege }}
        # Explicit fixture preparation before any balance snapshot: only the
        # truce created by the just-completed scripted tier is cancelled.
        if = {{ limit = {{ has_truce = var:djcg_primary }} cancel_truce_one_way = var:djcg_primary }}
        if = {{
            limit = {{ NOT = {{ has_truce = var:djcg_primary }} can_declare_war = {{ defender = var:djcg_primary casus_belli = {cb} target_titles = {{ title:{goal} }} }} }}
            set_variable = {{ name = djcg_phase value = 1 }}
            set_variable = {{ name = djcg_tier value = {tier_index+1} }}
            set_variable = {{ name = djcg_goal value = title:{goal} }}
            set_variable = {{ name = djcg_date value = current_date }}
            set_variable = {{ name = djcg_before_gold value = gold }}
            set_variable = {{ name = djcg_before_prestige value = prestige }}
            set_variable = {{ name = djcg_before_piety value = piety }}
            set_variable = {{ name = djcg_same_faith value = 0 }}
            set_variable = {{ name = djcg_peace_of_god value = 0 }}
            set_variable = {{ name = djcg_expected_extra_piety value = 0 }}
            if = {{ limit = {{ var:djcg_primary = {{ faith = root.faith }} }} set_variable = {{ name = djcg_same_faith value = 1 }} }}
            if = {{ limit = {{ root.rite ?= {{ rite_has_parameter = tenet_peace_of_god_same_faith_war_piety_penalty }} }} set_variable = {{ name = djcg_peace_of_god value = 1 }} }}
            if = {{ limit = {{ var:djcg_same_faith = 1 var:djcg_peace_of_god = 1 }} set_variable = {{ name = djcg_expected_extra_piety value = medium_piety_value }} }}
            debug_log = "DJCG: OBSERVE prepared_native_eligible_before_resources_and_extra_condition"
            trigger_event = djcg.100
        }}
        else = {{ djcg_stop_effect = yes }}
    }}
    else = {{ djcg_stop_effect = yes }}
}}
djcg_observe_declaration_effect = {{
    if = {{
        limit = {{ djcg_actor_trigger = yes var:djcg_phase = 1 current_date = var:djcg_date }}
        set_variable = {{ name = djcg_count value = 0 }}
        every_character_war = {{
            limit = {{ using_cb = {cb} is_attacker = root }}
            save_scope_as = djcg_actual_war
            root = {{ change_variable = {{ name = djcg_count add = 1 }} }}
        }}
        if = {{
            limit = {{ var:djcg_count = 1 exists = scope:djcg_actual_war }}
            set_variable = {{ name = djcg_war value = scope:djcg_actual_war }}
            if = {{
                limit = {{ djcg_real_gui_war_trigger = yes }}
                set_variable = {{ name = djcg_after_gold value = gold }}
                set_variable = {{ name = djcg_after_prestige value = prestige }}
                set_variable = {{ name = djcg_after_piety value = piety }}
                set_variable = {{ name = djcg_phase value = 2 }}
                debug_log = "DJCG: OBSERVE actual_war_target_participants_after_resources"
                trigger_event = djcg.110
            }}
            else = {{ djcg_stop_effect = yes }}
        }}
        else = {{ djcg_stop_effect = yes }}
    }}
    else = {{ djcg_stop_effect = yes }}
}}
djcg_observe_reload_effect = {{
    if = {{
        limit = {{
            djcg_actor_trigger = yes var:djcg_phase = 2 current_date = var:djcg_date
            gold = var:djcg_after_gold prestige = var:djcg_after_prestige piety = var:djcg_after_piety
            has_variable = djcg_war djcg_real_gui_war_trigger = yes
        }}
        set_variable = {{ name = djcg_reload_date value = current_date }}
        set_variable = {{ name = djcg_reload_gold value = gold }}
        set_variable = {{ name = djcg_reload_prestige value = prestige }}
        set_variable = {{ name = djcg_reload_piety value = piety }}
        set_variable = {{ name = djcg_phase value = 3 }}
        debug_log = "DJCG: OBSERVE persisted_actor_date_resources_war_after_operator_load"
        trigger_event = djcg.120
    }}
    else = {{ djcg_stop_effect = yes }}
}}
''')
    decisions = []
    for name, condition, effect in (
        ("prepare", "NOT = { has_variable = djcg_phase }", "djcg_prepare_gui_effect"),
        ("declaration", "var:djcg_phase = 1", "djcg_observe_declaration_effect"),
        ("reload", "var:djcg_phase = 2", "djcg_observe_reload_effect"),
    ):
        decisions.append(f'''
djcg_{name}_decision = {{
    picture = {{ reference = "gfx/interface/illustrations/decisions/decision_realm.dds" }}
    decision_group_type = realm
    ai_check_interval = 0
    desc = djcg_{name}_decision_desc
    selection_tooltip = djcg_observer_tooltip
    confirm_text = djcg_observer_confirm
    is_shown = {{ this = character:1128 is_ai = no var:djct_finished = 1 NOT = {{ has_variable = djcg_failed }} {condition} }}
    is_valid = {{ always = yes }}
    effect = {{ hidden_effect = {{ {effect} = yes }} }}
    ai_potential = {{ always = no }}
    ai_will_do = {{ base = 0 }}
}}
''')
    add("common/decisions/djcg_observers.txt", "\n".join(decisions))
    events = ['namespace = djcg']
    for number, stage in ((100, "ready"), (110, "save"), (120, "reload"), (900, "failed")):
        events.append(f'''djcg.{number} = {{
    type = character_event
    theme = realm
    title = djcg_{stage}_title
    desc = djcg_{stage}_desc
    option = {{ name = djcg_keep_paused }}
}}''')
    add("events/djcg_observer_events.txt", "\n".join(events))
    texts = {
        'djcg_prepare_decision': 'DJC observer: prepare ordinary GUI declaration',
        'djcg_prepare_decision_desc': 'After this tier really finishes, cancel only its directed fixture truce, read actual native eligibility and capture before balances. No war is declared or paid by this decision.',
        'djcg_declaration_decision': 'DJC observer: read actual GUI declaration result',
        'djcg_declaration_decision_desc': 'Use only after the actual ordinary Declare War GUI action, while the same date stays paused. Read the real war, production goal, participants and after balances. No war/payment is created.',
        'djcg_reload_decision': 'DJC observer: read state after actual Load Game',
        'djcg_reload_decision_desc': 'Use only after physically saving the phase2 war and actually loading that same file. This observer cannot prove that Load occurred; retain separate GUI action and both physical ZIP saves.',
        'djcg_observer_tooltip': 'Fixture observations only; ordinary GUI actions and physical Save/Load remain independent evidence.',
        'djcg_observer_confirm': 'Observe; keep the calendar paused',
        'djcg_ready_title': 'DJC ready for ordinary GUI declaration',
        'djcg_ready_desc': f'Same completed {tier} world. Keep paused. Close this known window, select the real {cb} / {goal} declaration against the primary defender, capture preview and confirm through the ordinary GUI. Then select the declaration observer. Do not advance a natural day.',
        'djcg_save_title': 'DJC observed real war; now Save then Load',
        'djcg_save_desc': 'Actual war and after balances are captured in phase2. Close while paused. Save a new physical file S1, retain its exact bytes/hash, and actually Load S1. Read back map/date/paused/player/war. Then select the reload observer and Save a separate physical S2. No script Save/Load or war settlement occurs.',
        'djcg_reload_title': 'DJC post-load observation captured',
        'djcg_reload_desc': 'Phase3 read actual persisted resources, date, goal and participants. Keep paused, close and Save a distinct S2. The offline consumer compares S1/S2 plus real GUI records. This window alone is not proof of reload, fees or whole-product acceptance.',
        'djcg_failed_title': 'DJC observer stopped',
        'djcg_failed_desc': 'Actor/phase/date/native eligibility/actual war/resources did not match. No successor, repair, war, payment or Save/Load is performed. Preserve failure and keep paused.',
        'djcg_keep_paused': 'Close and keep paused',
    }
    for language in ("english", "simp_chinese"):
        localized = dict(texts)
        if language == "simp_chinese":
            localized.update(djcg_prepare_decision="法理征服观察：准备普通界面宣战", djcg_declaration_decision="法理征服观察：读取真实界面宣战后态", djcg_reload_decision="法理征服观察：读取实际载入后态", djcg_ready_title="已准备普通界面宣战，保持暂停", djcg_save_title="已读取真实战争，请物理保存并载入", djcg_reload_title="已读取载入后态，请另存S2", djcg_failed_title="法理征服观察已停止", djcg_keep_paused="关闭并保持暂停")
        add(f"localization/{language}/djcg_l_{language}.yml", 'l_' + language + ':\n' + '\n'.join(f' {key}:0 "{value}"' for key, value in localized.items()))
    contract = {
        "schema": "djc.gui-ordinary-save.v1", "tier": tier, "tier_value": tier_index+1,
        "player_history_id": 1128, "casus_belli": cb, "goal": goal,
        "base_value_variables": list(GUI_BASE_VALUES), "reload_value_variables": list(GUI_RELOAD_VALUES), "reference_variables": list(GUI_REFERENCES),
        "ordinary_gui_required": True, "same_completed_matrix_world_required": True,
        "same_paused_date_required": True, "max_extra_natural_days": 0,
        "save_before_reload_phase": 2, "save_after_reload_phase": 3,
        "native_qualification": "NOT_GRANTED", "live": "NOT_RUN",
        "boundary": "Observer does not declare/settle/pay/Save/Load. Only before-snapshot preparation cancels the directed fixture truce. Physical ZIP saved values plus distinct real GUI declaration/load and preview evidence are mandatory. Observer phase3 is not proof of actual Load by itself.",
    }
    files["gui-observer-contract.json"] = (json.dumps(contract, ensure_ascii=False, indent=2) + '\n').encode()
    return files


def ordinary_gui_files(*, saved_entry_bridge: bool = False) -> dict[str, bytes]:
    """Fresh-source ducal setup/observation only; never run the matrix generator."""
    files = gui_observer_files("duchy")
    if type(saved_entry_bridge) is not bool:
        raise ValueError("saved_entry_bridge must be bool")

    def replace(relative: str, old: str, new: str) -> None:
        text = files[relative].decode("utf-8-sig")
        if text.count(old) != 1:
            raise ValueError(f"standalone observer anchor moved: {relative}")
        text = text.replace(old, new, 1)
        if relative.endswith(".txt"):
            parse_clausewitz(text)
        files[relative] = text.encode("utf-8-sig")

    triggers = "common/scripted_triggers/djcg_observer_triggers.txt"
    replace(triggers, "var:djct_finished = 1 var:djct_pass_count = 24", "var:djcg_standalone = 1")
    replace(triggers, "NOT = { has_variable = djct_failed } NOT = { has_variable = djcg_failed }", "NOT = { has_variable = djcg_failed }")
    replace(triggers, "current_date <= 1066.10.3", "current_date = 1066.9.15")
    effects = "common/scripted_effects/djcg_observer_effects.txt"
    replace(effects, "# Only fixture variables change after the before snapshot.", "# Standalone: the explicit once-only setup precedes every business snapshot.\n# Only fixture variables change after the before snapshot.")
    replace(effects, "djcg_actor_trigger = yes NOT = { has_variable = djcg_phase }", "djcg_actor_trigger = yes NOT = { has_variable = djcg_phase }\n            current_date = var:djcg_setup_date\n            prestige = var:djcg_setup_prestige piety = var:djcg_setup_piety\n            var:djcg_setup_goal = title:d_capua\n            var:djcg_setup_capua_title = title:c_capua var:djcg_setup_napoli_title = title:c_napoli\n            var:djcg_setup_primary = var:djcg_capua_holder.top_liege\n            var:djcg_setup_secondary = var:djcg_napoli_holder.top_liege")
    old_truce = """# Explicit fixture preparation before any balance snapshot: only the
        # truce created by the just-completed scripted tier is cancelled.
        if = { limit = { has_truce = var:djcg_primary } cancel_truce_one_way = var:djcg_primary }"""
    replace(effects, old_truce, """# Fixture evaluated-context hygiene only; never cancel a real truce.
        # The original declaration gate is evaluated with no inherited target.
        clear_saved_scope = target""")
    decisions = "common/decisions/djcg_observers.txt"
    text = files[decisions].decode("utf-8-sig")
    if text.count("var:djct_finished = 1") != 3:
        raise ValueError("standalone decision actor anchors moved")
    text = text.replace("var:djct_finished = 1", "var:djcg_standalone = 1")
    parse_clausewitz(text)
    files[decisions] = text.encode("utf-8-sig")
    for relative in (triggers, effects):
        text = files[relative].decode("utf-8-sig")
        text = text.replace("djct_capua_holder", "djcg_capua_holder").replace("djct_napoli_holder", "djcg_napoli_holder")
        parse_clausewitz(text)
        files[relative] = text.encode("utf-8-sig")
    # current_date is a date-literal operand in this engine, not a variable
    # comparison. The zero-day contract remains literal15 at every live gate;
    # the external consumer checks the actual two physical Save root dates.
    text = files[effects].decode("utf-8-sig")
    if text.count("current_date = var:djcg_setup_date") != 1 or text.count("current_date = var:djcg_date") != 2:
        raise ValueError("reviewed unsupported date operand anchors moved")
    text = text.replace("current_date = var:djcg_setup_date", "current_date = 1066.9.15").replace("current_date = var:djcg_date", "current_date = 1066.9.15")
    text = text.replace("set_variable = { name = djcg_date value = current_date }", "").replace("set_variable = { name = djcg_reload_date value = current_date }", "")
    text = text.replace("set_variable = { name = djcg_tier value = 1 }", "")
    text = text.replace("limit = { djcg_actor_trigger = yes var:djcg_phase = 1 current_date = 1066.9.15 }", "limit = { djcg_actor_trigger = yes var:djcg_phase = 1 current_date = 1066.9.15\n            gold = var:djcg_before_gold prestige <= var:djcg_before_prestige piety <= var:djcg_before_piety }")
    parse_clausewitz(text)
    files[effects] = text.encode("utf-8-sig")
    replace(triggers, "var:djcg_standalone = 1", "var:djcg_standalone = 1 var:djcg_tier = 1")
    replace(triggers, "var:djc_goal_title = title:d_capua", "var:djc_goal_title = root.var:djcg_goal")
    snapshot = '''
djcg_final_snapshot_trigger = {
    djcg_actor_trigger = yes var:djcg_phase = 3
    djcg_real_gui_war_trigger = yes
    gold = var:djcg_reload_gold prestige = var:djcg_reload_prestige piety = var:djcg_reload_piety
    var:djcg_reload_gold = var:djcg_after_gold
    var:djcg_reload_prestige = var:djcg_after_prestige
    var:djcg_reload_piety = var:djcg_after_piety
    OR = {
        AND = { var:djcg_same_faith = 1 var:djcg_peace_of_god = 1 var:djcg_expected_extra_piety = medium_piety_value }
        AND = { OR = { var:djcg_same_faith = 0 var:djcg_peace_of_god = 0 } var:djcg_expected_extra_piety = 0 }
    }
}
'''
    files[triggers] += snapshot.encode("utf-8")
    setup = '''
djcg.1 = {
    type = character_event
    theme = realm
    title = djcg_setup_title
    desc = djcg_setup_desc
    immediate = {
        if = {
            limit = {
                this = character:1128 is_alive = yes is_ai = no
                current_date = 1066.9.15
                NOT = { has_variable = djcg_standalone }
                NOT = { has_variable = djcg_phase }
                NOT = { has_variable = djcg_failed }
                title:c_apulia.holder = root
                exists = title:c_capua.holder exists = title:c_napoli.holder
                title:c_capua.holder.top_liege != root
                title:c_napoli.holder.top_liege != root
                title:c_capua.holder.top_liege != title:c_napoli.holder.top_liege
                title:c_napoli.holder = { is_independent_ruler = yes }
                NOT = { any_character_war = { using_cb = duchy_de_jure_greatwar is_attacker = root } }
            }
            # Explicit qualification input only, before the business before-balance.
            # This one event never writes a matrix/production success or starts war.
            add_prestige = 100000
            add_piety = 100000
            add_prestige_level = 5
            set_variable = { name = djcg_standalone value = 1 }
            set_variable = { name = djcg_tier value = 1 }
            set_variable = { name = djcg_setup_prestige value = prestige }
            set_variable = { name = djcg_setup_piety value = piety }
            set_variable = { name = djcg_setup_goal value = title:d_capua }
            set_variable = { name = djcg_setup_capua_title value = title:c_capua }
            set_variable = { name = djcg_setup_napoli_title value = title:c_napoli }
            set_variable = { name = djcg_setup_primary value = title:c_capua.holder.top_liege }
            set_variable = { name = djcg_setup_secondary value = title:c_napoli.holder.top_liege }
            set_variable = { name = djcg_capua_holder value = title:c_capua.holder }
            set_variable = { name = djcg_napoli_holder value = title:c_napoli.holder }
            debug_log = "DJCG: SETUP standalone_resources_before_business_observation"
        }
        else = { djcg_stop_effect = yes }
    }
    option = { name = djcg_keep_paused }
}
'''
    events = "events/djcg_observer_events.txt"
    text = files[events].decode("utf-8-sig") + setup
    start, end = text.index("djcg.120 ="), text.index("djcg.900 =")
    section = text[start:end]
    if section.count("option = { name = djcg_keep_paused }") != 1:
        raise ValueError("known reload confirmation option moved")
    text = text[:start] + section.replace("option = { name = djcg_keep_paused }", "option = { name = djcg_keep_paused trigger = { djcg_final_snapshot_trigger = yes } }") + text[end:]
    parse_clausewitz(text)
    files[events] = text.encode("utf-8-sig")
    for language in ("english", "simp_chinese"):
        relative = f"localization/{language}/djcg_l_{language}.yml"
        text = files[relative].decode("utf-8-sig")
        text = text.replace("Same completed duchy world.", "This standalone fresh-source world.")
        text = text.replace("Same completed", "Standalone")
        text = text.replace("After this tier really finishes, cancel only its directed fixture truce, read actual native eligibility and capture before balances. No war is declared or paid by this decision.",
                            "Standalone setup must already be observed. Read actual native eligibility and before balances without cancelling a real truce. This observer never declares or pays for war.")
        if language == "simp_chinese":
            text += ' djcg_setup_title:0 "DJC：普通公国宣战准备"\n djcg_setup_desc:0 "已执行一次明确的测试资源准备。保持暂停与零新增日；本场没有矩阵完成或战争成功资格。只通过原生普通界面宣战，随后读取真实战争与扣费。"\n'
        else:
            text += ' djcg_setup_title:0 "DJC: standalone ordinary ducal setup"\n djcg_setup_desc:0 "Explicit test resources were prepared once. Stay paused on the original date. No matrix or war success is granted; use the actual ordinary native declaration UI, then observe the real war and costs."\n'
        files[relative] = text.encode("utf-8-sig")
    descriptor = f'name="DJC standalone ordinary GUI observer"\nversion="fixture-only"\nsupported_version="{SUPPORTED_VERSION}"\n'
    files["descriptor.mod"] = descriptor.encode()
    if saved_entry_bridge:
        bridge = '''djcg_saved_entry_gui = {
    scope = character
    is_shown = { this = character:1128 is_ai = no is_alive = yes current_date = 1066.9.15 NOT = { has_character_flag = djcg_saved_entry_dispatched } NOT = { has_variable = djcg_standalone } }
    effect = {
        if = {
            limit = { this = character:1128 is_ai = no is_alive = yes current_date = 1066.9.15 NOT = { has_character_flag = djcg_saved_entry_dispatched } NOT = { has_variable = djcg_standalone } }
            add_character_flag = djcg_saved_entry_dispatched
            trigger_event = djcg.1
        }
    }
}
'''
        parse_clausewitz(bridge)
        files["common/scripted_guis/djcg_saved_entry_guis.txt"] = bridge.encode("utf-8-sig")
        files["gui/djcg_saved_entry_bridge.gui"] = '''window = {
    name = "djcg_saved_entry_bridge_window"
    size = { 1 1 }
    layer = tutorial
    position = { 0 0 }
    visible = "[GetPlayer.IsValid]"
    alwaystransparent = yes
    state = { name = _show using = Animation_FadeIn_Quick }
    state = { name = _hide using = Animation_FadeOut_Quick }
    state = {
        name = "djcg_saved_entry_bootstrap"
        trigger_when = "[GetScriptedGui('djcg_saved_entry_gui').IsShown( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
        on_start = "[GetScriptedGui('djcg_saved_entry_gui').Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
    }
}
'''.encode("utf-8-sig")
        files["gui/scripted_widgets/djcg_saved_entry_widgets.txt"] = b"\xef\xbb\xbfgui/djcg_saved_entry_bridge.gui = djcg_saved_entry_bridge_window\n"
    definition = json.loads(files["gui-observer-contract.json"])
    definition.update(schema=GUI_STANDALONE_SCHEMA, same_completed_matrix_world_required=False,
                      standalone_setup_required=True, initial_source_save_required=True,
                      fresh_start_date="1066.9.15", setup_event="djcg.1",
                      standalone_value_variables=list(GUI_STANDALONE_VALUES),
                      standalone_reference_variables=list(GUI_STANDALONE_REFERENCES),
                      base_value_variables=list(GUI_STANDALONE_BASE_VALUES), reload_value_variables=list(GUI_STANDALONE_RELOAD_VALUES),
                      physical_calendar_required="literal15-and-both-physical-save-root-dates",
                      saved_entry_bridge=saved_entry_bridge,
                      setup_resources={"prestige": 100000, "piety": 100000, "prestige_level": 5},
                      fixture_context_clear="target-only-before-native", matrix_pass_credit=False,
                      boundary="Standalone source setup only. Never starts/ends war, cancels truce or marks a matrix complete. Native ordinary UI and actual new war/cost/physical cold Load evidence are independent; no capability qualification.")
    files["gui-observer-contract.json"] = (json.dumps(definition, ensure_ascii=False, indent=2) + "\n").encode()
    return files


def guard_physical_missing_state(files: dict[str, bytes]) -> dict[str, bytes]:
    """Branch before value resolution; same-level AND is not short-circuit.

    Stock gdp_merchant_triggers161-166 uses this exact exists/trigger_if/else
    pattern for a possibly absent numeric variable. Never infer optional ?=
    fallback truth or seed an observer value just to suppress a diagnostic.
    """
    path = "common/scripted_triggers/djcg_observer_triggers.txt"
    original = files[path].decode("utf-8-sig")

    def wrapped(name: str, required: tuple[str, ...]) -> str:
        prefix = name + " = {\n"
        start = original.index(prefix) + len(prefix)
        end = original.index("\n}\n", start)
        body = original[start:end]
        checks = "\n".join("            exists = " + item for item in required)
        return (name + " = {\n    trigger_if = {\n        limit = {\n" + checks
                + "\n        }\n" + "\n".join("    " + line for line in body.splitlines())
                + "\n    }\n    trigger_else = { always = no }\n}\n")

    actor_vars = (*GUI_PHYSICAL_SETUP_VALUES, *GUI_STANDALONE_REFERENCES,
                  "djcg_capua_holder", "djcg_napoli_holder")
    guarded = wrapped("djcg_physical_actor_trigger", tuple("var:" + key for key in actor_vars))
    guarded += wrapped("djcg_physical_war_trigger", (
        "root.var:djcg_setup_primary", "root.var:djcg_setup_secondary",
        "root.var:djcg_setup_goal", "var:djc_goal_title"))
    # This predicate is evaluated continuously even before the first real war.
    # The body is the original IsShown expression; absent/partial S1 state is
    # false, and no variable lookup happens in the unselected branch.
    ready_vars = (*GUI_PHYSICAL_AFTER_VALUES, *GUI_PHYSICAL_AFTER_REFS)
    checks = "\n".join("            exists = var:" + key for key in ready_vars)
    guarded += ("djcg_physical_readback_ready_trigger = {\n    trigger_if = {\n        limit = {\n"
                + checks + "\n        }\n        djcg_physical_actor_trigger = yes\n"
                + "        var:djcg_physical_captured = 1\n    }\n    trigger_else = { always = no }\n}\n")
    parse_clausewitz(guarded)
    files[path] = guarded.encode("utf-8-sig")
    path = "common/scripted_guis/djcg_saved_entry_guis.txt"
    gui = files[path].decode("utf-8-sig")
    old = "is_shown = { djcg_physical_actor_trigger = yes var:djcg_physical_captured = 1 }"
    if gui.count(old) != 1:
        raise ValueError("reviewed continuously evaluated readback predicate moved")
    files[path] = gui.replace(old, "is_shown = { djcg_physical_readback_ready_trigger = yes }").encode("utf-8-sig")
    return files


def physical_observer_files() -> dict[str, bytes]:
    """Automatic genuine-war observation, using the proven engine widget path."""
    files = ordinary_gui_files(saved_entry_bridge=True)
    files.pop("common/decisions/djcg_observers.txt")
    events = files["events/djcg_observer_events.txt"].decode("utf-8-sig")
    failure = events[events.index("djcg.900 ="):events.index("djcg.1 =")]
    setup = events[events.index("djcg.1 ="):]
    visible_setup = "    theme = realm\n    title = djcg_setup_title\n    desc = djcg_setup_desc\n"
    setup_option = "    option = { name = djcg_keep_paused }\n"
    if setup.count(visible_setup) != 1 or setup.count(setup_option) != 1:
        raise ValueError("reviewed standalone setup presentation moved")
    # This current-channel mode has no generic event-option action. Initial
    # qualification runs once without leaving an uncloseable business modal.
    setup = setup.replace(visible_setup, "    hidden = yes\n").replace(setup_option, "")
    capture_setup = '''set_variable = { name = djcg_physical value = 1 }
            set_variable = { name = djcg_setup_gold value = gold }
            set_variable = { name = djcg_same_faith value = 0 }
            set_variable = { name = djcg_peace_of_god value = 0 }
            set_variable = { name = djcg_expected_extra_piety value = 0 }
            if = { limit = { var:djcg_setup_primary = { faith = root.faith } } set_variable = { name = djcg_same_faith value = 1 } }
            if = { limit = { root.rite ?= { rite_has_parameter = tenet_peace_of_god_same_faith_war_piety_penalty } } set_variable = { name = djcg_peace_of_god value = 1 } }
            if = { limit = { var:djcg_same_faith = 1 var:djcg_peace_of_god = 1 } set_variable = { name = djcg_expected_extra_piety value = medium_piety_value } }
            '''
    setup = setup.replace('debug_log = "DJCG: SETUP standalone_resources_before_business_observation"', capture_setup + 'debug_log = "DJCG: SETUP standalone_resources_before_business_observation"')
    files["events/djcg_observer_events.txt"] = ("namespace = djcg\n" + failure + setup).encode("utf-8-sig")
    triggers = '''djcg_physical_actor_trigger = {
    this = character:1128 is_ai = no is_alive = yes current_date = 1066.9.15
    var:djcg_standalone = 1 var:djcg_tier = 1 var:djcg_physical = 1
    NOT = { has_variable = djcg_failed }
}
djcg_physical_war_trigger = {
    using_cb = duchy_de_jure_greatwar primary_attacker = root
    primary_defender = root.var:djcg_setup_primary
    is_defender = root.var:djcg_setup_secondary
    has_variable = djc_goal_title var:djc_goal_title = root.var:djcg_setup_goal
}
'''
    stop = files["common/scripted_effects/djcg_observer_effects.txt"].decode("utf-8-sig")
    stop = stop[:stop.index("djcg_prepare_gui_effect =")]
    effects = '''djcg_capture_physical_war_effect = {
    set_variable = { name = djcg_war_count value = 0 }
    every_character_war = {
        limit = { djcg_physical_war_trigger = yes }
        save_scope_as = djcg_physical_actual_war
        root = { change_variable = { name = djcg_war_count add = 1 } }
    }
    if = {
        limit = { var:djcg_war_count = 1 exists = scope:djcg_physical_actual_war }
        set_variable = { name = djcg_war value = scope:djcg_physical_actual_war }
        set_variable = { name = djcg_actual_goal value = scope:djcg_physical_actual_war.var:djc_goal_title }
        set_variable = { name = djcg_actual_attacker value = scope:djcg_physical_actual_war.primary_attacker }
        set_variable = { name = djcg_actual_primary value = scope:djcg_physical_actual_war.primary_defender }
        # Membership of this real secondary is checked against that exact war.
        set_variable = { name = djcg_actual_secondary value = var:djcg_setup_secondary }
        set_variable = { name = djcg_after_gold value = gold }
        set_variable = { name = djcg_after_prestige value = prestige }
        set_variable = { name = djcg_after_piety value = piety }
        set_variable = { name = djcg_physical_captured value = 1 }
        debug_log = "DJCG: PHYSICAL CAPTURE actual_war_goal_participants_resources"
    }
    else = { djcg_stop_effect = yes }
}
djcg_physical_readback_effect = {
    if = {
        limit = {
            djcg_physical_actor_trigger = yes var:djcg_physical_captured = 1 var:djcg_war_count = 1
            exists = var:djcg_war var:djcg_war = { djcg_physical_war_trigger = yes }
            var:djcg_war.primary_attacker = var:djcg_actual_attacker
            var:djcg_war.primary_defender = var:djcg_actual_primary
            var:djcg_war = { is_defender = root.var:djcg_actual_secondary }
            var:djcg_war.var:djc_goal_title = var:djcg_actual_goal
            var:djcg_actual_goal = var:djcg_setup_goal
            var:djcg_setup_capua_title = title:c_capua var:djcg_setup_napoli_title = title:c_napoli
            title:c_capua.holder = var:djcg_capua_holder title:c_napoli.holder = var:djcg_napoli_holder
            gold = var:djcg_after_gold prestige = var:djcg_after_prestige piety = var:djcg_after_piety
            gold = var:djcg_setup_gold prestige <= var:djcg_setup_prestige piety <= var:djcg_setup_piety
            OR = {
                AND = { var:djcg_same_faith = 1 var:djcg_peace_of_god = 1 var:djcg_expected_extra_piety = medium_piety_value }
                AND = { OR = { var:djcg_same_faith = 0 var:djcg_peace_of_god = 0 } var:djcg_expected_extra_piety = 0 }
            }
        }
        debug_log = "DJCG: PHYSICAL READBACK MATCH war_goal_participants_resources"
    }
    else = { debug_log = "DJCG: PHYSICAL READBACK FAIL current_war_or_resources" }
}
'''
    scripted = files["common/scripted_guis/djcg_saved_entry_guis.txt"].decode("utf-8-sig")
    scripted += '''
djcg_saved_war_capture_gui = {
    scope = character
    is_shown = { djcg_physical_actor_trigger = yes NOT = { has_character_flag = djcg_physical_capture_dispatched } any_character_war = { djcg_physical_war_trigger = yes } }
    effect = {
        if = {
            limit = { djcg_physical_actor_trigger = yes NOT = { has_character_flag = djcg_physical_capture_dispatched } any_character_war = { djcg_physical_war_trigger = yes } }
            add_character_flag = djcg_physical_capture_dispatched
            djcg_capture_physical_war_effect = yes
        }
    }
}
djcg_saved_war_readback_gui = {
    scope = character
    is_shown = { djcg_physical_actor_trigger = yes var:djcg_physical_captured = 1 }
    effect = { djcg_physical_readback_effect = yes }
}
'''
    window = files["gui/djcg_saved_entry_bridge.gui"].decode("utf-8-sig")
    at = window.rfind("}")
    states = '''    state = {
        name = "djcg_physical_war_capture"
        trigger_when = "[GetScriptedGui('djcg_saved_war_capture_gui').IsShown( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
        on_start = "[GetScriptedGui('djcg_saved_war_capture_gui').Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
    }
    state = {
        name = "djcg_physical_war_readback"
        trigger_when = "[GetScriptedGui('djcg_saved_war_readback_gui').IsShown( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
        on_start = "[GetScriptedGui('djcg_saved_war_readback_gui').Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
    }
'''
    for text in (triggers, stop + effects, scripted):parse_clausewitz(text)
    files["common/scripted_triggers/djcg_observer_triggers.txt"] = triggers.encode("utf-8-sig")
    files["common/scripted_effects/djcg_observer_effects.txt"] = (stop + effects).encode("utf-8-sig")
    files["common/scripted_guis/djcg_saved_entry_guis.txt"] = scripted.encode("utf-8-sig")
    files["gui/djcg_saved_entry_bridge.gui"] = (window[:at] + states + window[at:]).encode("utf-8-sig")
    definition = dict(schema=GUI_PHYSICAL_SCHEMA, tier="duchy", player_history_id=1128, goal="d_capua", casus_belli="duchy_de_jure_greatwar", setup_value_variables=list(GUI_PHYSICAL_SETUP_VALUES), setup_reference_variables=list(GUI_STANDALONE_REFERENCES), after_value_variables=list(GUI_PHYSICAL_AFTER_VALUES), after_reference_variables=list(GUI_PHYSICAL_AFTER_REFS), current_date="1066.9.15", maximum_natural_days=0, requires_phase_markers=False, saved_entry_bridge=True, passive_real_war_observer=True, cold_match_marker="DJCG: PHYSICAL READBACK MATCH war_goal_participants_resources", matrix_pass_credit=False, native_qualification="NOT_GRANTED", live="NOT_RUN")
    files["gui-observer-contract.json"] = (json.dumps(definition, indent=2) + "\n").encode()
    for language, title, desc, option in (
        ("english", "DJC observer stopped", "A real setup, war or resource condition failed. Stay paused; no business pass is granted.", "Keep paused"),
        ("simp_chinese", "DJC观察已停止", "真实准备、战争或资源条件未满足。保持暂停；没有业务通过资格。", "保持暂停")):
        text = f'l_{language}:\n djcg_failed_title:0 "{title}"\n djcg_failed_desc:0 "{desc}"\n djcg_keep_paused:0 "{option}"\n'
        files[f"localization/{language}/djcg_l_{language}.yml"] = text.encode("utf-8-sig")
    return guard_physical_missing_state(files)


def main() -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--tier", choices=("all", "duchy", "kingdom", "empire"), default="all")
    parser.add_argument("--with-gui-observer", action="store_true", help="optional same-world ordinary GUI/physical SaveLoad observer; single tier only")
    parser.add_argument("--ordinary-gui-only", action="store_true", help="standalone ducal setup/observer, no matrix or automatic warfare")
    parser.add_argument("--saved-entry-bridge", action="store_true", help="explicit standalone Saved bootstrap; own once flag, never rearm setup on S0")
    parser.add_argument("--physical-only-observer", action="store_true", help="passive actual-war observation; S0/S1 proof without external observer calls")
    parser.add_argument("--diagnose-eligibility", action="store_true", help="bounded read-only state and failed-gate diagnostics; never grants original PASS")
    parser.add_argument("--clear-inherited-target", action="store_true", help="explicit fixture-context-only clear_saved_scope=target, with same-frame pre/post diagnosis; requires --diagnose-eligibility")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("fixture output already exists; use a fresh attempt")
    tier = reviewed_tier(args.tier)
    if args.physical_only_observer and not (args.ordinary_gui_only and args.saved_entry_bridge):
        parser.error("--physical-only-observer requires explicit standalone and Saved bridge")
    if args.saved_entry_bridge and not args.ordinary_gui_only:
        parser.error("--saved-entry-bridge requires --ordinary-gui-only")
    if args.ordinary_gui_only and (tier != "duchy" or args.with_gui_observer or args.diagnose_eligibility or args.clear_inherited_target):
        parser.error("--ordinary-gui-only needs --tier duchy and excludes matrix observer/diagnosis options")
    if args.with_gui_observer and tier == "all":
        parser.error("--with-gui-observer requires one fresh --tier duchy, kingdom or empire")
    if args.clear_inherited_target and not args.diagnose_eligibility:
        parser.error("--clear-inherited-target requires --diagnose-eligibility")
    files = physical_observer_files() if args.physical_only_observer else ordinary_gui_files(saved_entry_bridge=args.saved_entry_bridge) if args.ordinary_gui_only else generated_files(
        tier, diagnose_eligibility=args.diagnose_eligibility,
        clear_inherited_target=args.clear_inherited_target)
    if args.with_gui_observer:
        # On engines that dispatch this startup hook on Load as well, an existing
        # fixture seed must remain untouched. This is not proof that a Load ran.
        hook = files["common/on_action/djct_on_actions.txt"].decode("utf-8-sig")
        old = "every_player = {\n            if = {"
        new = "every_player = {\n            if = { limit = { has_variable = djct_started } debug_log = \"DJCG: OBSERVE existing_matrix_seed_unchanged\" }\n            else_if = {"
        if hook.count(old) != 1:
            raise ValueError("reviewed matrix startup insertion point moved")
        files["common/on_action/djct_on_actions.txt"] = hook.replace(old, new).encode("utf-8-sig")
        files.update(gui_observer_files(tier))
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
