"""Prepare XCCC scripted entry plus real production event choice for CK3 1.20."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from fixture_engine_prepare import checked_output, copy_files, decision_effect, finish_receipt, replace_once, required_markers, write_script

ON_ACTION = '''on_game_start_after_lobby = {
    on_actions = { xca120_start }
}

xca120_start = {
    effect = { random_player = { trigger_event = { id = xca120.1 } } }
}
'''
EVENTS = '''namespace = xca120

xca120.1 = {
    type = character_event
    hidden = yes
    immediate = {
        debug_log = "XCA120: TEST BEGIN engine_startup"
        add_character_flag = xca_initialize_pending
        xca_initialize_effect = yes
        character:han_8052 = { trigger_event = { id = xca120.2 days = 1 } }
    }
}

xca120.2 = {
    type = character_event
    hidden = yes
    immediate = {
        xca_setup_effect = yes
        if = {
            limit = { exists = scope:xca_official }
            scope:xca_official = { trigger_event = { id = xca120.3 days = 1 } }
        }
        else = { debug_log = "XCA120: TEST FAIL official_target_unavailable" }
    }
}

xca120.3 = {
    type = character_event
    hidden = yes
    immediate = {
        if = {
            limit = {
                is_ai = no
                is_landed = yes
                is_independent_ruler = no
                government_has_flag = government_has_merit
                has_tgp_dlc_trigger = yes
                is_capable_adult = yes
                is_imprisoned = no
                is_at_war = no
                NOT = { has_character_flag = xccc_never_corrupt }
                has_character_flag = xca_verify_policy_pending
            }
            # Fixture supplies a clean choice prestate; the actual product event
            # must apply the selected trait. No PASS postcondition is supplied.
            remove_trait = xccc_corruption_1
            remove_trait = xccc_corruption_2
            remove_trait = xccc_corruption_3
            remove_trait = xccc_corruption_4
            debug_log = "XCA120: TEST PASS production_decision_eligibility"
            debug_log = "XCA120: TEST READY production_corruption_event"
__PRODUCTION_EFFECT__
            set_variable = { name = xca120_choice_wait value = 0 }
            trigger_event = { id = xca120.4 days = 1 }
        }
        else = { debug_log = "XCA120: TEST FAIL production_decision_eligibility" }
    }
}

xca120.4 = {
    type = character_event
    hidden = yes
    immediate = {
        if = {
            limit = { has_character_flag = xca_verify_policy_pending has_trait = xccc_corruption_4 }
            xca_verify_policy_effect = yes
        }
        else_if = {
            limit = { has_character_flag = xca_verify_policy_pending var:xca120_choice_wait < 10 }
            change_variable = { name = xca120_choice_wait add = 1 }
            trigger_event = { id = xca120.4 days = 1 }
        }
        else = { debug_log = "XCA120: TEST FAIL production_choice_timeout" }
    }
}
'''

SAVED_GUARD = '''this = character:1128
        is_ai = no
        is_alive = yes
        current_date = 1066.9.15
        NOT = { has_character_flag = xca120_saved_entry_dispatched }
        NOT = { has_character_flag = xca_fixture_initialized }
        NOT = { has_character_flag = xca_initialize_pending }
        character:han_8052 = {
            NOT = { has_character_flag = xca120_saved_entry_dispatched }
            NOT = { has_character_flag = xca_fixture_initialized }
            NOT = { has_character_flag = xca_setup_pending }
        }'''


def saved_entry_files() -> dict[str, str]:
    """Bootstrap only the original entry; setup and production choice stay original."""
    return {
        'common/scripted_guis/xca120_saved_entry_guis.txt': f'''xca120_saved_entry_gui = {{
    scope = character
    is_shown = {{ {SAVED_GUARD} }}
    effect = {{
        if = {{
            limit = {{ {SAVED_GUARD} }}
            add_character_flag = xca120_saved_entry_dispatched
            character:han_8052 = {{ add_character_flag = xca120_saved_entry_dispatched }}
            trigger_event = {{ id = xca120.1 }}
        }}
    }}
}}
''',
        'gui/xca120_saved_entry_bridge.gui': '''window = {
    name = "xca120_saved_entry_bridge_window"
    size = { 1 1 }
    layer = tutorial
    position = { 0 0 }
    visible = "[GetPlayer.IsValid]"
    alwaystransparent = yes
    state = {
        name = "xca120_saved_entry_bootstrap"
        trigger_when = "[GetScriptedGui('xca120_saved_entry_gui').IsShown( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
        on_start = "[GetScriptedGui('xca120_saved_entry_gui').Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
    }
}
''',
        'gui/scripted_widgets/xca120_saved_entry_widgets.txt':
            'gui/xca120_saved_entry_bridge.gui = xca120_saved_entry_bridge_window\n',
    }



ROLE_WITNESS_RELATIVE = 'common/scripted_guis/xca120_actor_transition_witnesses.txt'
SELECTED_OFFICIAL_WITNESS = 'xca120_witness_selected_official'
ROLE_WITNESS_KEYS = (
    'xca120_current_song_actor_witness_gui',
    'xca120_current_official_actor_witness_gui',
)


def project_selected_official_witness(effects: str) -> str:
    """Record only the already selected original scope, on Song before the existing switch."""
    if SELECTED_OFFICIAL_WITNESS in effects:
        raise ValueError('Selected-official witness is already projected')
    anchor = '\t\t\tset_player_character = scope:xca_official\n'
    record = ('\t\t\t# Fixture-only observation; original ordered_vassal selection is unchanged.\n'
              '\t\t\tset_variable = { name = xca120_witness_selected_official value = scope:xca_official }\n')
    return replace_once(effects, anchor, record + anchor)


def readonly_role_witness_files() -> dict[str, str]:
    """Fixed IsShown predicates only; no Execute or permission granted by this fixture."""
    return {ROLE_WITNESS_RELATIVE: """# FIXTURE ONLY: current player Root must be independently bound by Native.
xca120_current_song_actor_witness_gui = {
    scope = character
    is_shown = {
        this = character:han_8052
        is_ai = no
        is_alive = yes
        is_landed = yes
        is_independent_ruler = yes
        has_title = title:h_china
        government_has_flag = government_is_celestial
        government_allows = barter
        has_character_flag = xca_setup_pending
    }
}
xca120_current_official_actor_witness_gui = {
    scope = character
    is_shown = {
        is_ai = no
        is_alive = yes
        is_landed = yes
        is_independent_ruler = no
        government_has_flag = government_has_merit
        NOT = { this = character:han_8052 }
        trigger_if = {
            limit = { exists = character:han_8052 }
            character:han_8052 = {
                trigger_if = {
                    limit = { has_variable = xca120_witness_selected_official }
                    var:xca120_witness_selected_official = root
                }
                trigger_else = { always = no }
            }
        }
        trigger_else = { always = no }
    }
}
"""}

def prepare(repo: Path, output: Path, saved_entry_bridge: bool = False, readonly_role_witnesses: bool = False, readonly_business_observations: bool = False) -> dict:
    if type(saved_entry_bridge) is not bool:
        raise ValueError('saved_entry_bridge must be a strict boolean')
    if type(readonly_role_witnesses) is not bool:
        raise ValueError('readonly_role_witnesses must be a strict boolean')
    if type(readonly_business_observations) is not bool or (readonly_business_observations and not readonly_role_witnesses):
        raise ValueError("Business observations require the actual original selected-role observer")
    repo, output = checked_output(repo, output)
    source = repo / "tools/fixtures/celestial_commerce_corruption_acceptance"
    files = sorted(path for path in source.rglob("*") if path.is_file()
                   and (path.name == "descriptor.mod" or path.relative_to(source).parts[0] == "localization"
                        or path.relative_to(source).parts[:2] == ("common", "scripted_effects")))
    copy_files(source, output, files)
    effects = (source / "common/scripted_effects/xca_effects.txt").read_text(encoding="utf-8-sig")
    old = "XCA: TEST PASS production_decision_event_round_trip"
    new = "XCA: TEST PASS scripted_decision_effect_event_result"
    effects = replace_once(effects, old, new)
    if readonly_role_witnesses:
        effects = project_selected_official_witness(effects)
    write_script(output, "common/scripted_effects/xca_effects.txt", effects)
    body, provenance = decision_effect(repo, "mod_celestial_commerce_corruption",
                                       "common/decisions/xccc_corruption_decision.txt", "xccc_corruption_policy_decision")
    if saved_entry_bridge:
        for relative, text in saved_entry_files().items():
            write_script(output, relative, text)
    else:
        write_script(output, "common/on_action/xca120_on_actions.txt", ON_ACTION)
    write_script(output, "events/xca120_events.txt", EVENTS.replace("__PRODUCTION_EFFECT__", "\n".join("            " + line for line in body.splitlines())))
    if readonly_role_witnesses:
        for relative, value in readonly_role_witness_files().items():
            write_script(output, relative, value)
    if readonly_business_observations:
        write_script(output, "common/scripted_guis/xca120_business_observations.txt", 'xca120_observe_corruption_1_gui = {\n    scope = character\n    is_shown = { is_ai = no\n        is_alive = yes\n        trigger_if = {\n            limit = { exists = character:han_8052 }\n            character:han_8052 = {\n                trigger_if = {\n                    limit = { has_variable = xca120_witness_selected_official }\n                    var:xca120_witness_selected_official = root\n                }\n                trigger_else = { always = no }\n            }\n        }\n        trigger_else = { always = no }\n        has_trait = xccc_corruption_1\n    }\n}\n\nxca120_observe_corruption_2_gui = {\n    scope = character\n    is_shown = { is_ai = no\n        is_alive = yes\n        trigger_if = {\n            limit = { exists = character:han_8052 }\n            character:han_8052 = {\n                trigger_if = {\n                    limit = { has_variable = xca120_witness_selected_official }\n                    var:xca120_witness_selected_official = root\n                }\n                trigger_else = { always = no }\n            }\n        }\n        trigger_else = { always = no }\n        has_trait = xccc_corruption_2\n    }\n}\n\nxca120_observe_corruption_3_gui = {\n    scope = character\n    is_shown = { is_ai = no\n        is_alive = yes\n        trigger_if = {\n            limit = { exists = character:han_8052 }\n            character:han_8052 = {\n                trigger_if = {\n                    limit = { has_variable = xca120_witness_selected_official }\n                    var:xca120_witness_selected_official = root\n                }\n                trigger_else = { always = no }\n            }\n        }\n        trigger_else = { always = no }\n        has_trait = xccc_corruption_3\n    }\n}\n\nxca120_observe_corruption_4_gui = {\n    scope = character\n    is_shown = { is_ai = no\n        is_alive = yes\n        trigger_if = {\n            limit = { exists = character:han_8052 }\n            character:han_8052 = {\n                trigger_if = {\n                    limit = { has_variable = xca120_witness_selected_official }\n                    var:xca120_witness_selected_official = root\n                }\n                trigger_else = { always = no }\n            }\n        }\n        trigger_else = { always = no }\n        has_trait = xccc_corruption_4\n    }\n}\n\nxca120_observe_tax_variable_gui = {\n    scope = character\n    is_shown = { is_ai = no\n        is_alive = yes\n        trigger_if = {\n            limit = { exists = character:han_8052 }\n            character:han_8052 = {\n                trigger_if = {\n                    limit = { has_variable = xca120_witness_selected_official }\n                    var:xca120_witness_selected_official = root\n                }\n                trigger_else = { always = no }\n            }\n        }\n        trigger_else = { always = no }\n        has_variable = xca_tax_after_tier_four\n    }\n}\n\nxca120_observe_tax_half_gui = {\n    scope = character\n    is_shown = { is_ai = no\n        is_alive = yes\n        trigger_if = {\n            limit = { exists = character:han_8052 }\n            character:han_8052 = {\n                trigger_if = {\n                    limit = { has_variable = xca120_witness_selected_official }\n                    var:xca120_witness_selected_official = root\n                }\n                trigger_else = { always = no }\n            }\n        }\n        trigger_else = { always = no }\n        has_variable = xca_tax_after_tier_four\n        trigger_if = { limit = { has_variable = xca_tax_after_tier_four } var:xca_tax_after_tier_four = 0.50 }\n        trigger_else = { always = no }\n    }\n}\n')
    markers = [new if marker == old else marker for marker in required_markers(repo / "tools/run_celestial_commerce_corruption_acceptance.py")]
    entry_metadata: dict[str, object] = {}
    if saved_entry_bridge:
        entry_metadata = {
            'entry': 'Saved GetPlayer bridge -> original xca120.1/2/3/4; original Song/official switches and real production option remain',
            'saved_entry': {
                'actor_history_id': 1128, 'required_source_game_date': '1066.9.15',
                'runtime_actor_id': 'NOT_INFERRED_FROM_HISTORY_ID',
                'source_save_binding': 'REQUIRED_BY_PUBLIC_SAVED_PREPARATION',
                'requires_human_alive_unstarted_actor': True,
                'paired_once_flag': 'xca120_saved_entry_dispatched', 'paired_target': 'character:han_8052',
                'new_game_on_action_included': False, 'original_events_and_setup': 'UNCHANGED',
                'saved_bootstrap_gui_mounted': True, 'original_business_gui_callbacks_mounted': False,
                'runtime_status': 'NOT_RUN',
            },
        }
    if readonly_role_witnesses:
        entry_metadata['readonly_role_witnesses'] = {
            'schema': 'xca120.fixed-actor-role-witnesses.v1',
            'fixed_keys': list(ROLE_WITNESS_KEYS),
            'relative': ROLE_WITNESS_RELATIVE,
            'selected_scope_record': 'Original Song scope records scope:xca_official immediately before the existing set_player_character',
            'variable': SELECTED_OFFICIAL_WITNESS,
            'selection_and_player_switch_changed': False,
            'events_markers_calendar_and_production_effects_changed': False,
            'Native_permission_or_actual_role_observed': False,
            'runtime_status': 'NOT_RUN',
        }
        if saved_entry_bridge:
            entry_metadata['saved_entry']['original_events_and_setup'] = 'ORIGINAL_BEHAVIOR_WITH_EXPLICIT_SELECTED_SCOPE_OBSERVER'
    return finish_receipt(repo, source, output, files, {
        "product": "mod_celestial_commerce_corruption", "mode": "scripted-decision-entry-real-event-choice",
        "entry": "post-lobby -> xca_initialize_effect -> Song at D1 xca_setup_effect -> official at D2 production decision effect -> actual xccc.1001 option -> original verifier",
        "required_markers": ["XCA120: TEST BEGIN engine_startup", "XCA120: TEST PASS production_decision_eligibility", "XCA120: TEST READY production_corruption_event", *markers],
        "rules": "vanilla declared defaults; 1066 ordinary player outside Song; Song han_8052 initially AI; TGP runtime DLC required",
        "production_decision_effect": provenance,
        "production_builder": "tools/build_celestial_commerce_corruption_release.py",
        "production_government_contract": "Use current exact 1.20 full celestial government + sole barter=yes; obligations unchanged. Existing static contract remains authoritative, not rewritten by fixture.",
        "real_choice": "Inspect actual xccc.1001 instance and enabled option named xccc.1001.d (fourth tier); select via UI or existing native event-option tool. Advance one day for original trait + 0.75-0.25=0.50 verification.",
        "marker_policy": "Each required marker once; no XCA or XCA120 TEST FAIL. Eligibility failure is a fixture precondition until actual state is audited.",
        "ui_not_executed_by_fixture": ["production decision opening/confirm", "three-year decision cooldown", "all other tax-tier UI choices"],
        "player_switch_policy": "Actual scripted player changes may be observed as played_character_changed terminal by native one-life driver; preserve production policy.",
        **entry_metadata,
    })

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument('--saved-entry-bridge', action='store_true',
                        help='explicit Robert1128/1066.9.15 Saved bootstrap; original CCC setup and choice required')
    parser.add_argument('--readonly-business-observations', action='store_true')
    parser.add_argument('--readonly-role-witnesses', action='store_true',
                        help='explicit fixture-only original Song/selected official readonly role observations; no gameplay or Native permission')
    args = parser.parse_args()
    receipt = prepare(args.repo, args.output, args.saved_entry_bridge, args.readonly_role_witnesses, args.readonly_business_observations)
    print(json.dumps({"prepared_fixture": receipt["prepared_fixture"], "runtime_status": "NOT_RUN"}))

if __name__ == "__main__":
    main()
