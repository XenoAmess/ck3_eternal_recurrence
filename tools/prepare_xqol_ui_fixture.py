"""Prepare the original Song UI scene without replaying QOL core matrices."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import fixture_engine_prepare as prep

MARKERS = {
    'begin': 'ZQAUITAIL: SCOPE BEGIN actual_song_actor',
    'pass': 'ZQAUITAIL: SCOPE PASS actual_song_actor',
    'end': 'ZQAUITAIL: SCOPE END actual_song_actor',
    'fail': 'ZQAUITAIL: TEST FAIL actual_song_actor',
}


def project():
    # The historical reference is an engine scope selector. The full current
    # CharacterID is read from the framed dump and native snapshot on each run.
    startup = '''on_game_start_after_lobby = { on_actions = { zqauitail_start } }
zqauitail_start = {
    effect = {
        # set_player_character requires the actual current player scope.
        random_player = {
        if = {
            limit = {
                exists = character:han_8052
                character:han_8052 = {
                    is_alive = yes is_ai = yes is_ruler = yes
                    has_title = title:h_china
                    is_independent_ruler = yes
                    has_government = celestial_government
                }
            }
            character:han_8052 = { save_scope_as = xqol_startup_actor }
            set_player_character = scope:xqol_startup_actor
            scope:xqol_startup_actor = {
                set_player_character = scope:xqol_startup_actor
                debug_log = "ZQAUITAIL: SCOPE BEGIN actual_song_actor"
                debug_log_scopes = yes
                if = {
                    limit = {
                        is_ai = no is_alive = yes is_ruler = yes
                        has_title = title:h_china
                        is_independent_ruler = yes
                        has_government = celestial_government
                    }
                    debug_log = "ZQAUITAIL: SCOPE PASS actual_song_actor"
                }
                else = { debug_log = "ZQAUITAIL: TEST FAIL actual_song_actor" }
                debug_log = "ZQAUITAIL: SCOPE END actual_song_actor"
            }
        }
        else = { debug_log = "ZQAUITAIL: TEST FAIL original_song_preconditions" }
        }
    }
}
'''
    return {
        'descriptor.mod': 'name="QOL original Song UI scene"\nversion="1"\ntags={ "Testing" }\n',
        'common/on_action/zqauitail_on_actions.txt': startup,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    repo, output = prep.checked_output(args.repo, args.output)
    payloads = project()
    for relative, text in payloads.items():
        prep.write_script(output, relative, text)
    receipt = {'schema': 'ck3-xqol-original-ui-scene-projection-v1',
               'engine_identity': prep.engine_identity(repo), 'fixture_files': list(payloads),
               'runtime_status': 'NOT_RUN', 'business_pass': False,
               'does_not_run': ['defense23', 'reverse', 'final6', 'guard_assertions'],
               'does_not_set': ['government', 'opinion', 'obedience', 'blood_brother',
                                'production_toggle', 'faith', 'pending', 'slider']}
    (output/'projection-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
