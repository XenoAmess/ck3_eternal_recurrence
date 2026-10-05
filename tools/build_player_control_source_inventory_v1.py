"""Create-only static inventory from an actual prepared managed profile.

This command does not start/inspect a process or Steam, invoke a game/tool/pipe,
or assert a future runtime PID/generation. Input must be the actual new profile.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import sys

module_root=Path(__file__).resolve().parent
sdk_root=module_root.parent / 'ck3_autonomous_player/src'
if not sdk_root.is_dir(): sdk_root=module_root / 'candidate/ck3_autonomous_player/src'
sys.path.insert(0, str(sdk_root))
from xar_autoplayer.bridge.player_control_source_inventory_v1 import (
    INVENTORY_BASENAME, SCHEMA, STOCK_GUI_PATHS, IMPLEMENTATION_PATHS, canonical_profile_projection,
    verify_source_inventory_v1,
)


def file_record(path: Path) -> dict:
    content = path.read_bytes()
    return {'path': path.resolve().as_posix(), 'bytes': len(content),
            'sha256': hashlib.sha256(content).hexdigest()}


def build_inventory(profile: dict, game_root: Path, implementation_root: Path) -> tuple[dict, bytes]:
    userdir = Path(profile['userdir']).resolve()
    dlc = userdir / 'dlc_load.json'
    enabled = json.loads(dlc.read_bytes())['enabled_mods']
    if type(enabled) is not list or any(type(value) is not str for value in enabled):
        raise ValueError('actual enabled mods are not a complete ordered list')
    mods = []
    for registration in enabled:
        outer = (userdir / registration).resolve()
        if not outer.is_relative_to(userdir):
            raise ValueError('enabled mod outer descriptor escapes userdir')
        text = outer.read_text(encoding='utf-8-sig')
        paths = re.findall(r'(?m)^\s*path\s*=\s*"([^"\r\n]+)"', text)
        if len(paths) != 1 or not Path(paths[0]).is_absolute():
            raise ValueError('actual enabled mod does not have one absolute directory mount')
        mod_root = Path(paths[0]).resolve()
        rows = []
        for path in sorted(mod_root.rglob('*')):
            if path.is_file():
                row = file_record(path)
                rows.append({'relative_path': path.relative_to(mod_root).as_posix(),
                             'bytes': row['bytes'], 'sha256': row['sha256']})
        mods.append({'registration': registration, 'root': mod_root.as_posix(),
                     'outer_descriptor': file_record(outer),
                     'inner_descriptor': file_record(mod_root / 'descriptor.mod'), 'files': rows})
    executable = Path(profile['guard']['target']['executable']).resolve()
    source = file_record(executable)
    projection = canonical_profile_projection(profile)
    inventory = {'schema': SCHEMA, 'userdir': userdir.as_posix(),
                 'profile_binding_sha256': hashlib.sha256(projection).hexdigest(),
                 'settings_file': file_record(userdir / 'pdx_settings.txt'), 'dlc_load': file_record(dlc),
                 'stock_game_root': game_root.resolve().as_posix(),
                 'source_executable': {'path': source['path'], 'sha256': source['sha256']},
                 'stock_gui': [file_record(game_root / relative) for relative in STOCK_GUI_PATHS],
                 'enabled_mods': mods, 'implementation_root': implementation_root.resolve().as_posix(),
                  'implementation_sources': [file_record(implementation_root / relative) for relative in IMPLEMENTATION_PATHS]}
    return inventory, projection


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--stock-game-root', type=Path, required=True)
    parser.add_argument('--implementation-root', type=Path, required=True)
    args = parser.parse_args()
    profile = json.loads(args.profile.read_bytes())
    guard_bytes=Path(profile['guard_profile']).read_bytes()
    if hashlib.sha256(guard_bytes).hexdigest() != profile['guard_profile_sha256'].lower():
        raise ValueError('actual guard-profile bytes differ from managed-profile binding')
    guard = json.loads(guard_bytes)
    profile['guard'] = guard
    inventory, projection = build_inventory(profile, args.stock_game_root, args.implementation_root)
    userdir = Path(profile['userdir']).resolve()
    destination = userdir / INVENTORY_BASENAME
    encoded = json.dumps(inventory, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    reference = {'path': destination.as_posix(), 'sha256': hashlib.sha256(encoded).hexdigest()}
    with destination.open('xb') as stream: stream.write(encoded)
    with (userdir / 'player-control-profile-binding-projection-v1.json').open('xb') as stream: stream.write(projection)
    verified = verify_source_inventory_v1(reference, profile)
    print(json.dumps({'player_control_source_inventory': reference, 'verification': verified,
                      'actual_runtime_binding': 'NOT_RUN; actual driver/native bind after launch'}, ensure_ascii=False, indent=2))


if __name__ == '__main__': main()
