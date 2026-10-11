"""Prepare a self-only original Confucian setup; never a business PASS fixture."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SETUP = '''# GENERATED FILE by tools/prepare_lyd_vanilla_feedback_fixture.py
on_game_start_after_lobby = { on_actions = { lyd_feedback_setup } }
lyd_feedback_setup = {
    effect = {
        random_player = {
            if = {
                limit = { is_ai = no NOT = { has_character_flag = lyd_feedback_setup_done } }
                set_character_rite = rite:jingxue
                add_character_flag = lyd_feedback_setup_done
                debug_log = "LYD_FEEDBACK: SELF_JINGXUE_SETUP_APPLIED"
            }
        }
    }
}
'''


def generate(output: Path, identity: dict) -> dict:
    """Pure small fixture emission; callers own exact engine qualification."""
    if output.exists():
        raise ValueError('Fresh fixture output required')
    output.mkdir(parents=True)
    files = {
        'descriptor.mod': 'name="LYD original Confucian feedback setup"\nversion="1"\nsupported_version="1.20.*"\n',
        'common/on_action/lyd_feedback_setup.txt': SETUP,
    }
    refs = []
    for relative, text in files.items():
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = text.encode('utf-8-sig')
        target.write_bytes(raw)
        refs.append({'relative_path': relative, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    receipt = {
        'schema': 'lyd-vanilla-feedback-setup-v1', 'engine_identity': identity,
        'fixture_files': refs, 'required_markers': ['LYD_FEEDBACK: SELF_JINGXUE_SETUP_APPLIED'],
        'setup_scope': 'sole selected human player; Robert 29829 is verified by public admission and GUI readback',
        'setup_changes': ['self character rite to original jingxue', 'self idempotence flag'],
        'fixture_flag_is_business_proof': False, 'business_pass': False,
        'faith_main_rite_or_NPC_or_title_changes': False,
    }
    with (output / 'setup-receipt.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    import fixture_engine_prepare as prep
    repo, output = args.repo.resolve(), args.output.resolve()
    if output == repo or repo in output.parents:
        raise ValueError('Fixture output must be outside repository')
    # Shared prepare installs its selected exact-build implementation here.
    identity = prep.engine_identity(repo)
    receipt = generate(output, identity)
    print(json.dumps({'status': 'SETUP_EMITTED_NOT_RUN', 'output': str(output),
                      'engine_identity': receipt['engine_identity'], 'business_pass': False}))


if __name__ == '__main__':
    main()
