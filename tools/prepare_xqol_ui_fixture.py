"""Prepare a controlled zero-recipient Song UI scene, not a conversion replay."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import fixture_engine_prepare as prep
from prepare_xqol_1_20_fixture import saved_entry_files

MARKERS = {
    'begin': 'ZQAUITAIL: SCOPE BEGIN actual_song_actor',
    'pass': 'ZQAUITAIL: SCOPE PASS actual_song_actor',
    'end': 'ZQAUITAIL: SCOPE END actual_song_actor',
    'fail': 'ZQAUITAIL: TEST FAIL actual_song_actor',
}

FIXTURE_PREPARATION = {
    'id': 'song-ui-zero-recipient-faith-seed-v1',
    'phase': 'startup_before_scope_markers_and_ui',
    'ai_recipient_domains': ['courtier', 'vassal_or_below', 'tributary'],
    'recipient_faith': 'scope:xqol_startup_actor.faith',
    'actor_own_faith_unchanged': True,
    'titles_and_government_unchanged': True,
    'ui_phase_forbids': ['setfaith', 'clear_pending', 'candidate_flag_override'],
}


def project(*, saved_entry_bridge: bool = False) -> dict[str, str]:
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
                # ZQAUITAIL_RECIPIENT_SEED_BEGIN song-ui-zero-recipient-faith-seed-v1
                # Fixture-only preparation; the actor's own faith is unchanged.
                every_courtier = {
                    limit = { is_ai = yes }
                    set_character_faith = scope:xqol_startup_actor.faith
                }
                every_vassal_or_below = {
                    limit = { is_ai = yes }
                    set_character_faith = scope:xqol_startup_actor.faith
                }
                every_tributary = {
                    limit = { is_ai = yes }
                    set_character_faith = scope:xqol_startup_actor.faith
                }
                # ZQAUITAIL_RECIPIENT_SEED_END song-ui-zero-recipient-faith-seed-v1
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
    files = {
        'descriptor.mod': 'name="QOL controlled zero-recipient Song UI scene"\nversion="2"\ntags={ "Testing" }\n',
        'common/on_action/zqauitail_on_actions.txt': startup,
    }
    if saved_entry_bridge:
        # Use the original human scope body without re-selecting a random player.
        # The bridge is rooted at the actual GetPlayer (Robert1128), and the
        # original Song preconditions, one switch and recipient seed remain.
        player = prep.balanced_excerpt(startup, r"^        random_player\s*=\s*\{")
        body = player[player.index("{") + 1:player.rfind("}")]
        files['common/on_action/zqauitail_on_actions.txt'] = (
            '# Saved-only fixture: the guarded scripted widget owns startup.\n')
        files.update(saved_entry_files(ui_start_body=body))
    return files


def projection_receipt(engine_identity: dict[str, str], payloads: dict[str, str], *,
                       saved_entry_bridge: bool = False) -> dict[str, object]:
    receipt: dict[str, object] = {'schema': 'ck3-xqol-controlled-zero-recipient-ui-scene-projection-v1',
            'engine_identity': engine_identity, 'fixture_files': list(payloads),
            'fixture_preparation': FIXTURE_PREPARATION,
            'runtime_status': 'NOT_RUN', 'business_pass': False,
            'does_not_run': ['defense23', 'reverse', 'final6', 'guard_assertions'],
            'does_not_set': ['government', 'opinion', 'obedience', 'blood_brother',
                             'production_toggle', 'pending', 'slider', 'candidate_flags']}
    if saved_entry_bridge:
        receipt.update({'saved_entry_bridge': True,
                        'entry': 'GetPlayer-bound Saved scripted widget -> original Song scope preparation',
                        'saved_entry_actor_history_id': '1128', 'saved_entry_date': '1066.9.15',
                        'saved_entry_once_flag': 'zqauitail_saved_entry_dispatched',
                        'startup_observed': 'NOT_RUN', 'source_save_mutated': False})
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--saved-entry-bridge', action='store_true',
                        help='Use the guarded Robert1128/.15 Saved bootstrap instead of the new-game hook')
    args = parser.parse_args()
    repo, output = prep.checked_output(args.repo, args.output)
    payloads = project(saved_entry_bridge=args.saved_entry_bridge)
    for relative, text in payloads.items():
        prep.write_script(output, relative, text)
    receipt = projection_receipt(prep.engine_identity(repo), payloads,
                                 saved_entry_bridge=args.saved_entry_bridge)
    (output/'projection-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
