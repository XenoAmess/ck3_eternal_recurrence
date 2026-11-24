"""Source-only candidate: exact original AE2 fixture with explicit opt-in Saved setup bridge."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

SAVED_GUARD = '''this = character:1128
        is_ai = no
        is_alive = yes
        is_landed = yes
        current_date = 1066.9.15
        has_game_rule = zg361_on
        NOT = { has_character_flag = zga_ae2_saved_entry_dispatched }
        NOT = { has_character_flag = zga_ae2_setup_attempted }'''


def saved_entry_files() -> dict[str, str]:
    return {
        'common/scripted_guis/zga_ae2_saved_entry_guis.txt': f'''zga_ae2_saved_entry_gui = {{
    scope = character
    is_shown = {{ {SAVED_GUARD} }}
    effect = {{
        if = {{
            limit = {{ {SAVED_GUARD} }}
            add_character_flag = zga_ae2_saved_entry_dispatched
            zga_ae2_prepare_effect = yes
        }}
    }}
}}
''',
        'gui/zga_ae2_saved_entry_bridge.gui': '''window = {
    name = "zga_ae2_saved_entry_bridge_window"
    size = { 1 1 }
    layer = tutorial
    position = { 0 0 }
    visible = "[GetPlayer.IsValid]"
    alwaystransparent = yes
    state = {
        name = "zga_ae2_saved_entry_bootstrap"
        trigger_when = "[GetScriptedGui('zga_ae2_saved_entry_gui').IsShown( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
        on_start = "[GetScriptedGui('zga_ae2_saved_entry_gui').Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
    }
}
''',
        'gui/scripted_widgets/zga_ae2_saved_entry_widgets.txt':
            'gui/zga_ae2_saved_entry_bridge.gui = zga_ae2_saved_entry_bridge_window\n',
    }


def generate(repo: Path, output: Path, identity: dict[str, Any], *, saved_entry_bridge: bool = False) -> dict[str, Any]:
    if type(saved_entry_bridge) is not bool:
        raise ValueError('Saved bridge must be an explicit strict boolean')
    repo, output = repo.resolve(), output.resolve()
    if output == repo or repo in output.parents or output.exists():
        raise ValueError('Fresh output outside repository is required')
    version = identity.get('game_version')
    if saved_entry_bridge and (not isinstance(version, str) or re.fullmatch(r'[1-9][0-9]*(?:\.[0-9]+){2,3}', version) is None):
        raise ValueError('Exact numeric engine game_version required for opted-in Saved mode')
    source = repo / 'tools/fixtures/zg361_ae2_ui_payment'
    # This one existing finite fixture is the only copied source, never product
    # dev trees, current profiles, saves, SDK caches or another fixture.
    source_files = sorted(p for p in source.rglob('*') if p.is_file())
    if not source_files or not (source / 'descriptor.mod').is_file():
        raise ValueError('Original finite AE2 fixture is unavailable')
    files: dict[str, bytes] = {}
    source_pins = []
    for path in source_files:
        if path.is_symlink() or not path.resolve().is_relative_to(source.resolve()):
            raise ValueError('Original source file escaped the admitted fixture root')
        relative = path.relative_to(source).as_posix()
        raw = path.read_bytes()
        source_pins.append({'path': str(path), 'relative_path': relative, 'bytes': len(raw),
                            'sha256': hashlib.sha256(raw).hexdigest()})
        # Saved load invokes only original setup through the transparent bridge.
        # Its old NewGame dispatcher is not mounted simultaneously in Saved mode.
        if saved_entry_bridge and relative == 'common/on_action/zga_ae2_on_actions.txt':
            continue
        if saved_entry_bridge and relative == 'descriptor.mod':
            text = raw.decode('utf-8-sig')
            text, replaced = re.subn(r'^supported_version="[^"]+"$', f'supported_version="{version}"', text, flags=re.MULTILINE)
            if replaced != 1:
                raise ValueError('Original descriptor has no unique supported_version')
            raw = text.encode('utf-8-sig')
        files[relative] = raw
    if saved_entry_bridge:
        for relative, text in saved_entry_files().items():
            if relative in files:
                raise ValueError('Bridge collides with original fixture')
            files[relative] = text.encode('utf-8-sig')
    output.mkdir(parents=True)
    refs = []
    for relative, raw in files.items():
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as f:
            f.write(raw)
        refs.append({'relative_path': relative, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    receipt = {
        'schema': 'zg361-ae2-original-fixture-setup.v1', 'engine_identity': identity,
        'fixture_files': refs, 'source_fixture_files': source_pins,
        'saved_entry_bridge': saved_entry_bridge,
        'default_original_files_byte_preserved': not saved_entry_bridge,
        'original_effects_decisions_events_localizations_byte_preserved': True,
        'maximum_natural_days': 0, 'runtime_status': 'NOT_RUN', 'business_pass': False,
        'original_setup': 'Only unchanged zga_ae2_prepare_effect; same disclosed celestial/resources/delivered-result prerequisites. No presentation/payment/verify decision or event option is executed by the bridge.',
        'required_marker': 'ZG361AE2UI: TEST READY ae2_prepared_no_payment',
        'receipt_excluded_from_runtime_manifest': True,
        'saved_entry': None if not saved_entry_bridge else {
            'history_actor': 1128, 'required_date': '1066.9.15',
            'actual_runtime_actor': 'NOT_INFERRED_FROM_HISTORY_ID',
            'actual_source_save': 'REQUIRED_BY_PUBLIC_SAVED_PREPARATION_NOT_CHOSEN_HERE',
            'double_guard_once': 'zga_ae2_saved_entry_dispatched plus original zga_ae2_setup_attempted',
            'newgame_dispatcher_mounted': False,
            'original_wallets_costs_eligibility_and_production_effects_changed': False,
        },
    }
    with (output / 'setup-receipt.json').open('x', encoding='utf-8', newline='\n') as f:
        json.dump(receipt, f, ensure_ascii=False, indent=2)
        f.write('\n')
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--saved-entry-bridge', action='store_true')
    args = parser.parse_args()
    repo = args.repo.resolve()
    sys.path.insert(0, str(repo / 'tools'))
    import fixture_engine_prepare as prep
    receipt = generate(repo, args.output, prep.engine_identity(repo), saved_entry_bridge=args.saved_entry_bridge)
    print(json.dumps({'status': 'SETUP_EMITTED_NOT_RUN', 'output': str(args.output.resolve()),
                      'fixture_files': len(receipt['fixture_files']), 'business_pass': False}))


if __name__ == '__main__':
    main()
