"""Replay production Python/C++ source verification without launching CK3.

The explicit prepared profile supplies source files, never gameplay state. All
mutations occur in new short-path corpus directories. No original is edited.
"""
from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'ck3_autonomous_player/src'))
from xar_autoplayer.bridge.normal_exit_source_inventory_v1 import (
    INVENTORY_BASENAME, canonical_profile_projection, verify_source_inventory_v1,
)


def digest(raw): return hashlib.sha256(raw).hexdigest()


def pin(path):
    path = Path(path).resolve(); raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': digest(raw)}


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode('utf-8'))
    return pin(path)


def replace(path, raw):
    temporary = path.with_name(path.name + '.corpus-delta')
    temporary.write_bytes(raw); temporary.replace(path)


def clone_case(root, original, template, settings_source):
    root.mkdir(exist_ok=False); userdir = root / 'u'; userdir.mkdir()
    profile = copy.deepcopy(template)
    profile.update(userdir=str(userdir), state_directory=str(root), evidence_directory=str(root))
    profile['guard'] = json.loads(Path(profile['guard_profile']).read_bytes())
    inventory = copy.deepcopy(original); inventory['userdir'] = str(userdir)
    for key, name in [('settings_file', 'pdx_settings.txt'), ('dlc_load', 'dlc_load.json')]:
        reference = original[key]
        source = settings_source if key == 'settings_file' and settings_source else Path(reference['path'])
        raw = source.read_bytes()
        if digest(raw) != reference['sha256'] or len(raw) != reference['bytes']:
            raise ValueError('Original preparation source bytes unavailable: ' + str(source))
        path = userdir / name; path.write_bytes(raw); inventory[key] = pin(path)
    for index, mod in enumerate(inventory['enabled_mods']):
        old = original['enabled_mods'][index]; mod_root = root / ('m' + str(index)); mod_root.mkdir()
        for row in old['files']:
            source = Path(old['root']) / row['relative_path']; raw = source.read_bytes()
            if digest(raw) != row['sha256'] or len(raw) != row['bytes']:
                raise ValueError('Original product file changed: ' + str(source))
            path = mod_root / row['relative_path']; path.parent.mkdir(parents=True, exist_ok=True)
            os.link(source, path)
        outer = userdir / mod['registration']; outer.parent.mkdir(parents=True, exist_ok=True)
        outer.write_text('name="Native source corpus"\npath="' + mod_root.as_posix() + '"\n', encoding='utf-8')
        mod.update(root=str(mod_root), outer_descriptor=pin(outer), inner_descriptor=pin(mod_root / 'descriptor.mod'))
    inventory['profile_binding_sha256'] = digest(canonical_profile_projection(profile))
    return profile, inventory, userdir


def add_source(inventory, relative, raw):
    mod = inventory['enabled_mods'][0]; path = Path(mod['root']) / relative
    path.parent.mkdir(parents=True, exist_ok=True); replace(path, raw)
    row = {'relative_path': relative, 'bytes': len(raw), 'sha256': digest(raw)}
    mod['files'] = [old for old in mod['files'] if old['relative_path'] != relative] + [row]


def qualify(args):
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=False)
    template = json.loads(args.profile.read_bytes())
    source_inventory = Path(template['normal_exit_source_inventory']['path'])
    original = json.loads(source_inventory.read_bytes())
    original_ref = template['normal_exit_source_inventory']
    if digest(source_inventory.read_bytes()) != original_ref['sha256']:
        raise ValueError('Prepared source inventory reference changed')
    executable = Path(original['source_executable']['path']).resolve()
    if digest(executable.read_bytes()) != original['source_executable']['sha256']:
        raise ValueError('Actual source executable changed')
    cases = [
        ('actual_product', None, True),
        ('unrelated_type_and_widget_reference', ('gui/other.gui', b'types Other {type unrelated_native_fixture=button_standard{}} window={name="other" button_standard={}}'), True),
        ('protected_type', ('gui/other.gui', b'types Other {type button_standard=button{}}'), False),
        ('protected_template', ('gui/other.gui', b'template window_background {alpha=0}'), False),
        ('fixed_root', ('gui/other.gui', b'window={name="ingame_pausemenu"}'), False),
        ('pause_callback', ('gui/other.gui', b'window={onclick="[PauseMenu.ExitGame]"}'), False),
        ('resign_callback', ('gui/other.gui', b'window={onclick="[ResignConfirmationWindow.ExitGame]"}'), False),
        ('root_callback', ('gui/other.gui', b'window={onclick="[OnPauseMenu]"}'), False),
        ('protected_dependency_path', ('gui/shared/windows.gui', b'window={name="other"}'), False),
        ('protected_stock_path', ('gui/hud.gui', b'window={name="other"}'), False),
        ('gui_hash_changed', 'hash', False),
        ('unlisted_file', 'add', False),
        ('listed_file_missing', 'remove', False),
        ('dependency_missing', 'dependency_missing', False),
        ('dependency_hash_changed', 'dependency_hash', False),
        ('legacy_no_dependencies', 'legacy', False),
    ]
    # Select an actual protected template from the same generated contract,
    # rather than assuming a particular game's declaration names.
    sys.path.insert(0, str(ROOT / 'tools'))
    from gen_normal_exit_gui_source_contract_v1 import build_contract
    contract = build_contract(Path(original['stock_game_root']))
    template_name = next((name for name in contract['protected_gui_symbols'] if name == 'window_background'), None)
    if template_name is None:
        # All declaration names have identical collision semantics for type and
        # template; use a protected name present in this exact source contract.
        template_name = contract['protected_gui_symbols'][0]
    cases[3] = ('protected_template', ('gui/other.gui', ('template ' + template_name + ' {alpha=0}').encode()), False)
    rows = []
    for index, (name, mutation, expected) in enumerate(cases):
        case = output / ('c' + str(index).zfill(2))
        profile, inventory, userdir = clone_case(case, original, template, args.settings_source)
        if isinstance(mutation, tuple): add_source(inventory, *mutation)
        elif mutation == 'hash':
            gui = next(row for row in inventory['enabled_mods'][0]['files'] if row['relative_path'].endswith('.gui'))
            path = Path(inventory['enabled_mods'][0]['root']) / gui['relative_path']
            replace(path, path.read_bytes() + b'\n# actual bytes changed after inventory\n')
        elif mutation == 'add': (Path(inventory['enabled_mods'][0]['root']) / 'unlisted.txt').write_bytes(b'extra')
        elif mutation == 'remove':
            row = next(row for row in inventory['enabled_mods'][0]['files'] if row['relative_path'].endswith('.gui'))
            (Path(inventory['enabled_mods'][0]['root']) / row['relative_path']).unlink()
        elif mutation == 'dependency_missing': inventory['stock_gui_dependencies'].pop()
        elif mutation == 'dependency_hash': inventory['stock_gui_dependencies'][0]['sha256'] = '0' * 64
        elif mutation == 'legacy': del inventory['stock_gui_dependencies']
        reference = write(userdir / INVENTORY_BASENAME, inventory)
        python_reason = None
        try:
            verification = verify_source_inventory_v1({'path': reference['path'], 'sha256': reference['sha256']}, profile)
            python_accepted = verification['static_sources_verified'] is True
        except (ValueError, OSError) as error:
            python_accepted = False; python_reason = type(error).__name__ + ': ' + str(error)
        argv = [str(args.fixture.resolve()), '--source-context', str(userdir), '--executable', str(executable),
                '--sha256', reference['sha256'], 'accept' if expected else 'reject']
        process = subprocess.run(argv, capture_output=True, text=True, encoding='utf-8')
        native = json.loads(process.stdout) if process.stdout.strip() else None
        result = {'case': name, 'expected_accepted': expected, 'inventory': reference,
                  'python_accepted': python_accepted, 'python_reason': python_reason,
                  'argv': argv, 'exit_code': process.returncode, 'native': native,
                  'stdout': process.stdout, 'stderr': process.stderr}
        result['pass'] = (process.returncode == 0 and python_accepted == expected and
                          native is not None and native['accepted'] == expected and
                          native['production_filesystem_verifier_invoked'] is True)
        write(case / 'RESULT.actual.json', result); rows.append(result)
    result = {
        'schema': 'ck3-normal-exit-python-native-source-parity-v1',
        'machine_id': args.machine_id, 'observed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status': 'PASS' if all(row['pass'] for row in rows) else 'RED',
        'fixture': pin(args.fixture), 'source_profile': pin(args.profile),
        'source_inventory': pin(source_inventory),
        'original_product_file_count': sum(len(mod['files']) for mod in original['enabled_mods']),
        'original_product_gui_count': sum(row['relative_path'].endswith('.gui') for mod in original['enabled_mods'] for row in mod['files']),
        'settings_replay_source': pin(args.settings_source) if args.settings_source else None,
        'cases': rows, 'case_count': len(rows), 'game_started': False,
        'live_native_quit_qualified': False, 'business_pass': False,
        'open_kaishek': {'status': 'not-applicable', 'reason': 'Filesystem census, SHA256, GUI declaration namespace and Win32 source binding have no CK3 script/runtime semantics.'}}
    write(output / 'RESULT.actual.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', required=True, type=Path)
    parser.add_argument('--profile', required=True, type=Path)
    parser.add_argument('--settings-source', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--machine-id', required=True)
    args = parser.parse_args(); result = qualify(args)
    print(json.dumps({'status': result['status'], 'case_count': result['case_count'],
                      'result': str(args.output / 'RESULT.actual.json'), 'game_started': False}))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
