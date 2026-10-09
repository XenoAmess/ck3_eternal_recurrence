"""Project the two original QOL guard assertions, without the other matrices."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re

import fixture_engine_prepare as prep

ORIGINAL = 'tools/fixtures/xqol_acceptance/common/scripted_effects/zqa_effects.txt'
ENABLED = 'ZQA: TEST PASS transfer_guard_enabled_and_preexisting_preserved'
DISABLED = 'ZQA: TEST PASS transfer_guard_disabled_and_preexisting_preserved'
SCOPE = {
    'begin': 'ZQAGUARD: SCOPE BEGIN actual_song_actor',
    'pass': 'ZQAGUARD: SCOPE PASS actual_song_actor',
    'end': 'ZQAGUARD: SCOPE END actual_song_actor',
    'fail': 'ZQAGUARD: TEST FAIL actual_song_actor',
}


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def between(text, start, end):
    if text.count(start) != 1:
        raise ValueError('Original guard projection anchor changed')
    first = text.index(start)
    last = text.find(end, first)
    if last < 0:
        raise ValueError('Original guard projection terminator missing')
    return text[first:last]


def original_assertion(effect, marker):
    """Keep the original whole if/else, including its original FAIL branch."""
    result = between(effect, '\tif = {\n\t\tlimit = {\n\t\t\t' + (
        'exists = scope:zqa_preexisting_guard_subject' if marker == ENABLED else 'any_vassal = {'),
        '\n\n\trandom_vassal = {' if marker == ENABLED else '\n\tevery_vassal_or_below = {')
    if result.count(marker) != 1 or result.count(marker.replace('TEST PASS', 'TEST FAIL')) != 1:
        raise ValueError('Original guard assertion/FAIL branch changed')
    return result


def project(repo):
    source = Path(repo) / ORIGINAL
    raw = source.read_bytes()
    text = raw.decode('utf-8-sig').replace('\r\n', '\n')
    init = prep.balanced_excerpt(text, r'^zqa_initialize_effect\s*=\s*\{')
    enabled = prep.balanced_excerpt(text, r'^zqa_run_enabled_matrix_effect\s*=\s*\{')
    disabled = prep.balanced_excerpt(text, r'^zqa_verify_disabled_matrix_effect\s*=\s*\{')
    # These are exact original subject blocks, including the original exclusions.
    subject_start = '\t\t\t\trandom_vassal = {\n\t\t\t\t\tlimit = { is_landed = yes }\n\t\t\t\t\tadd_character_flag = zqa_preexisting_guard_subject'
    subjects = between(init, subject_start, '\n\t\t\t}\n\t\t\tif = {')
    owned_start = '\trandom_vassal = {\n\t\tlimit = {\n\t\t\tis_landed = yes\n\t\t\thas_character_flag = zqa_preexisting_guard_subject'
    owned = between(enabled, owned_start, '\tif = {\n\t\tlimit = {\n\t\t\texists = scope:zqa_preexisting_guard_subject')
    on_check = original_assertion(enabled, ENABLED)
    # Anchor after the unrelated heir assertion, rather than the first any_vassal.
    off_start = '\tif = {\n\t\tlimit = {\n\t\t\tany_vassal = {\n\t\t\t\thas_character_flag = zqa_owned_guard_subject'
    off_check = between(disabled, off_start, '\n\tevery_vassal_or_below = {')
    if off_check.count(DISABLED) != 1 or off_check.count(DISABLED.replace('TEST PASS', 'TEST FAIL')) != 1:
        raise ValueError('Original disabled guard assertion/FAIL branch changed')
    projections = []
    production = []
    for short in ('enable', 'disable'):
        decision = f'xqol_{short}_no_vassal_transfers_decision'
        body, proof = prep.decision_effect(Path(repo), 'mod_xenoamess_quality_of_life',
                                         'common/decisions/xqol_decisions.txt', decision)
        production.append(f'zqag_{short}_production_effect = {{\n{body}\n}}\n')
        projections.append(proof)
    setup = '''zqag_setup_subjects_effect = {
    if = {
        limit = { NOT = { has_character_flag = zqag_subjects_initialized } }
        add_character_flag = zqag_subjects_initialized
ORIGINAL_SUBJECTS
        debug_log = "ZQAGUARD: TEST BEGIN focused_guards"
        trigger_event = { id = zqag.1 days = 1 }
    }
}
'''.replace('ORIGINAL_SUBJECTS', subjects)
    observe = '''zqag_dump_original_subjects_effect = {
    debug_log_scopes = yes
    every_vassal = {
        limit = { has_character_flag = zqa_preexisting_guard_subject }
        debug_log = "ZQAGUARD: SUBJECT preexisting BEGIN"
        debug_log_scopes = yes
        debug_log = "ZQAGUARD: SUBJECT preexisting END"
    }
    every_vassal = {
        limit = { has_character_flag = zqa_owned_guard_subject }
        debug_log = "ZQAGUARD: SUBJECT owned BEGIN"
        debug_log_scopes = yes
        debug_log = "ZQAGUARD: SUBJECT owned END"
    }
}
'''
    first = '''zqag.1 = {
    type = character_event
    hidden = yes
    immediate = {
        if = {
            limit = { is_ai = no xqol_supported_player_trigger = yes has_character_flag = zqag_subjects_initialized NOT = { has_character_flag = zqag_enabled_once } }
            add_character_flag = zqag_enabled_once
            zqag_enable_production_effect = yes
ORIGINAL_OWNED
            debug_log = "ZQAGUARD: OBSERVED enabled SUBJECTS BEGIN"
            zqag_dump_original_subjects_effect = yes
            debug_log = "ZQAGUARD: OBSERVED enabled SUBJECTS END"
ORIGINAL_ENABLED
            trigger_event = { id = zqag.2 days = 1 }
        }
        else = { debug_log = "ZQAGUARD: TEST FAIL enabled_once_preconditions" }
    }
}
'''.replace('ORIGINAL_OWNED', owned).replace('ORIGINAL_ENABLED', on_check)
    second = '''zqag.2 = {
    type = character_event
    hidden = yes
    immediate = {
        if = {
            limit = { is_ai = no xqol_supported_player_trigger = yes has_character_flag = zqag_enabled_once NOT = { has_character_flag = zqag_disabled_once } }
            add_character_flag = zqag_disabled_once
            zqag_disable_production_effect = yes
            debug_log = "ZQAGUARD: OBSERVED disabled SUBJECTS BEGIN"
            zqag_dump_original_subjects_effect = yes
            debug_log = "ZQAGUARD: OBSERVED disabled SUBJECTS END"
ORIGINAL_DISABLED
            debug_log = "ZQAGUARD: TEST DONE focused_guards"
        }
        else = { debug_log = "ZQAGUARD: TEST FAIL disabled_once_preconditions" }
    }
}
'''.replace('ORIGINAL_DISABLED', off_check)
    startup = '''on_game_start_after_lobby = { on_actions = { zqag_start } }
zqag_start = {
    effect = {
        if = {
            limit = {
                exists = character:han_8052
                character:han_8052 = {
                    is_alive = yes is_ai = yes is_ruler = yes has_title = title:h_china
                    is_independent_ruler = yes has_government = celestial_government
                    any_vassal = { count >= 4 is_landed = yes }
                }
            }
            character:han_8052 = { save_scope_as = xqol_startup_actor }
            set_player_character = scope:xqol_startup_actor
            scope:xqol_startup_actor = {
                set_player_character = scope:xqol_startup_actor
                debug_log = "ZQAGUARD: SCOPE BEGIN actual_song_actor"
                debug_log_scopes = yes
                if = {
                    limit = { is_ai = no is_alive = yes is_ruler = yes has_title = title:h_china is_independent_ruler = yes has_government = celestial_government }
                    debug_log = "ZQAGUARD: SCOPE PASS actual_song_actor"
                }
                else = { debug_log = "ZQAGUARD: TEST FAIL actual_song_actor" }
                debug_log = "ZQAGUARD: SCOPE END actual_song_actor"
                zqag_setup_subjects_effect = yes
            }
        }
        else = { debug_log = "ZQAGUARD: TEST FAIL original_song_preconditions" }
    }
}
'''
    payloads = {
        'descriptor.mod': 'name="QOL original guard assertions (focused fixture)"\nversion="1"\ntags={ "Testing" }\n',
        'common/on_action/zqag_on_actions.txt': startup,
        'common/scripted_effects/zqag_effects.txt': setup + observe + '\n'.join(production),
        'events/zqag_events.txt': 'namespace = zqag\n' + first + second,
    }
    return payloads, {
        'source': {'path': ORIGINAL, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()},
        'original_projection_sha256': {name: digest(value) for name, value in {
            'subjects': subjects, 'owned_subject_selection': owned,
            'enabled_if_else': on_check, 'disabled_if_else': off_check}.items()},
        'production_decision_effects': projections,
        'assertions': [ENABLED, DISABLED], 'maximum_natural_days': 2,
        'does_not_run': ['defense23', 'reverse', 'death', 'appointment_matrix', 'payment', 'conversion', 'ransom'],
        'fixture_subjects_are_original_seeded_samples_not_claimed_natural_external_subjects': True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    repo, output = prep.checked_output(args.repo, args.output)
    payloads, receipt = project(repo)
    for relative, text in payloads.items():
        prep.write_script(output, relative, text)
    receipt.update(engine_identity=prep.engine_identity(repo), runtime_status='NOT_RUN',
                   formal_product_unchanged=True, native_or_game_actions=False)
    (output / 'projection-receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
