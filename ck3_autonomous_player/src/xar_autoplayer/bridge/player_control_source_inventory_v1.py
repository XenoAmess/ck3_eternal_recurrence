"""Static actual-byte source inventory verifier, with no process/UI operations.

The trusted managed profile supplies the fixed manifest reference. Runtime PID,
exact creation FILETIME and generation are supplied separately by the driver and
verified independently by the native owner. This inventory contains no future
process identity and no caller-provided admission booleans.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

INVENTORY_BASENAME = 'player-control-source-inventory-v1.json'
SCHEMA = 'ck3-player-control-source-inventory-v1'
STOCK_GUI_PATHS = (
    'gui/hud.gui', 'gui/frontend_ingame_menu.gui', 'gui/window_resign_confirmation.gui',
    'gui/shared/buttons_icons.gui', 'gui/shared/buttons.gui', 'gui/shared/sounds.gui',
    'gui/multiplayer_types.gui', 'gui/multiplayer_lobby.gui',
)
IMPLEMENTATION_PATHS = (
    'tools/ck3_native_profile_mcp.py',
    'tools/build_player_control_source_inventory_v1.py',
    'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py',
    'ck3_autonomous_player/src/xar_autoplayer/bridge/service.py',
    'ck3_autonomous_player/src/xar_autoplayer/bridge/player_control_contract_v1.py',
    'ck3_autonomous_player/src/xar_autoplayer/bridge/player_control_driver_v1.py',
    'ck3_autonomous_player/src/xar_autoplayer/bridge/player_control_source_inventory_v1.py',
    'ck3_autonomous_player/src/xar_autoplayer/bridge/normal_exit_map_driver_v1.py',
    'ck3_autonomous_player/src/xar_autoplayer/bridge/normal_exit_process_observer_v1.py',
    'ck3_autonomous_player/src/xar_autoplayer/bridge/ingame_decisions_open_contract.py',
    'ck3_autonomous_player/native_bridge/CMakeLists.txt',
    'ck3_autonomous_player/native_bridge/include/xar_bridge/player_control_v1.hpp',
    'ck3_autonomous_player/native_bridge/src/player_control_request_v1.cpp',
    'ck3_autonomous_player/native_bridge/src/player_control_v1.cpp',
    'ck3_autonomous_player/native_bridge/include/xar_bridge/player_control_identity_source_v1.hpp',
    'ck3_autonomous_player/native_bridge/src/player_control_identity_source_v1.cpp',
    'ck3_autonomous_player/native_bridge/src/player_control_identity_pins_v1.inc',
    'ck3_autonomous_player/native_bridge/src/bridge.cpp',
    'ck3_autonomous_player/native_bridge/include/xar_bridge/frontend_gui_route_v1.hpp',
    'ck3_autonomous_player/native_bridge/src/frontend_gui_route_v1.cpp',
)

PROFILE_BINDING_KEYS = {
    'schema_version', 'guard_profile', 'guard_profile_sha256', 'userdir', 'evidence_directory',
    'game_version', 'state_directory', 'dll', 'injector',
}


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def canonical_profile_projection(profile: dict) -> bytes:
    if type(profile) is not dict or not PROFILE_BINDING_KEYS <= set(profile):
        raise ValueError('managed profile lacks its static canonical projection fields')
    projection = {key: profile[key] for key in sorted(PROFILE_BINDING_KEYS)}
    return json.dumps(projection, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':')).encode('utf-8')


def _keys(value: object, expected: set[str], name: str) -> dict:
    if type(value) is not dict or set(value) != expected:
        raise ValueError(f'closed {name} fields mismatch')
    return value


def _digest(value: object) -> str:
    if type(value) is not str or re.fullmatch('[0-9a-f]{64}', value) is None:
        raise ValueError('exact lowercase SHA-256 required')
    return value


def _path(value: object) -> Path:
    if type(value) is not str or not Path(value).is_absolute():
        raise ValueError('actual absolute source path required')
    return Path(value).resolve()


def _file(row: object) -> tuple[Path, bytes]:
    row = _keys(row, {'path', 'bytes', 'sha256'}, 'source file')
    path = _path(row['path'])
    if type(row['bytes']) is not int or row['bytes'] < 0:
        raise ValueError('source file byte count requires exact integer')
    content = path.read_bytes()
    if len(content) != row['bytes'] or sha256(content) != _digest(row['sha256']):
        raise ValueError(f'actual source bytes changed: {path}')
    return path, content


def _relative(value: object) -> str:
    if type(value) is not str or not value or '\\' in value:
        raise ValueError('normalized relative source path required')
    path = Path(value)
    if path.is_absolute() or any(part in {'.', '..'} for part in path.parts):
        raise ValueError('source path escapes root')
    return value


def _descriptor(content: bytes, *, outer: bool, root: Path) -> None:
    text = content.decode('utf-8-sig')
    if re.search(r'(?m)^\s*(replace_path|archive)\s*=', text):
        raise ValueError('mod descriptor replaces source paths or uses an unverified archive')
    paths = re.findall(r'(?m)^\s*path\s*=\s*"([^"\r\n]+)"', text)
    if outer and (len(paths) != 1 or _path(paths[0]) != root):
        raise ValueError('enabled outer descriptor does not mount the inventoried mod root')
    if not outer and paths:
        raise ValueError('inner descriptor unexpectedly chooses a mount path')


def _reject_related_override(relative: str, content: bytes) -> None:
    # This private V1 has an explicitly limited zero-GUI-mod scope. Unrelated
    # mod GUI compatibility requires a later source-bound implementation.
    if relative.casefold().endswith('.gui'):
        raise ValueError('player-control private V1 does not support enabled mod GUI files')


def verify_source_inventory_v1(reference: dict, profile: dict) -> dict:
    reference = _keys(reference, {'path', 'sha256'}, 'inventory reference')
    userdir = _path(profile['userdir'])
    path = _path(reference['path'])
    if path != userdir / INVENTORY_BASENAME:
        raise ValueError('player-control inventory is not the fixed managed-userdir file')
    content = path.read_bytes()
    digest = _digest(reference['sha256'])
    if sha256(content) != digest:
        raise ValueError('source inventory bytes changed')
    inventory = _keys(json.loads(content), {
        'schema', 'userdir', 'profile_binding_sha256', 'settings_file', 'dlc_load',
        'stock_game_root', 'source_executable', 'stock_gui', 'enabled_mods',
        'implementation_root', 'implementation_sources',
    }, 'source inventory')
    if inventory['schema'] != SCHEMA or _path(inventory['userdir']) != userdir:
        raise ValueError('source inventory belongs to a different managed userdir')
    projection = canonical_profile_projection(profile)
    if _digest(inventory['profile_binding_sha256']) != sha256(projection):
        raise ValueError('source inventory canonical profile projection changed')
    settings_path, _ = _file(inventory['settings_file'])
    if settings_path != userdir / 'pdx_settings.txt':
        raise ValueError('actual launch contract uses managed-userdir pdx_settings.txt')
    dlc_path, dlc_bytes = _file(inventory['dlc_load'])
    if dlc_path != userdir / 'dlc_load.json':
        raise ValueError('source inventory dlc_load is outside actual managed userdir')
    enabled = json.loads(dlc_bytes).get('enabled_mods')
    if type(enabled) is not list or any(type(value) is not str for value in enabled):
        raise ValueError('actual enabled_mods configuration is incomplete')
    executable_row = _keys(inventory['source_executable'], {'path', 'sha256'}, 'source executable')
    executable = _path(executable_row['path'])
    executable_bytes = executable.read_bytes()
    if sha256(executable_bytes) != _digest(executable_row['sha256']) or sha256(executable_bytes) != str(profile['guard']['target']['executable_sha256']).lower():
        raise ValueError('inventoried executable is not the managed exact build')
    if executable != _path(profile['guard']['target']['executable']):
        raise ValueError('inventoried executable path changed')
    game_root = _path(inventory['stock_game_root'])
    if type(inventory['stock_gui']) is not list or len(inventory['stock_gui']) != len(STOCK_GUI_PATHS):
        raise ValueError('protected stock GUI inventory is incomplete')
    for relative, row in zip(STOCK_GUI_PATHS, inventory['stock_gui']):
        actual, _ = _file(row)
        if actual != game_root / relative:
            raise ValueError('protected stock GUI order/path mismatch')
    mods = inventory['enabled_mods']
    if type(mods) is not list or len(mods) != len(enabled):
        raise ValueError('actual enabled mod inventory is incomplete')
    for registration, mod in zip(enabled, mods):
        mod = _keys(mod, {'registration', 'root', 'outer_descriptor', 'inner_descriptor', 'files'}, 'enabled mod')
        if mod['registration'] != registration:
            raise ValueError('enabled mod order or registration changed')
        outer, outer_bytes = _file(mod['outer_descriptor'])
        if outer != (userdir / _relative(registration)).resolve():
            raise ValueError('enabled mod registration path mismatch')
        mod_root = _path(mod['root'])
        _descriptor(outer_bytes, outer=True, root=mod_root)
        inner, inner_bytes = _file(mod['inner_descriptor'])
        if inner != mod_root / 'descriptor.mod':
            raise ValueError('enabled mod inner descriptor path mismatch')
        _descriptor(inner_bytes, outer=False, root=mod_root)
        if type(mod['files']) is not list:
            raise ValueError('enabled mod full file inventory absent')
        listed: dict[str, str] = {}
        for row in mod['files']:
            row = _keys(row, {'relative_path', 'bytes', 'sha256'}, 'mod source file')
            relative = _relative(row['relative_path'])
            if relative.casefold() in listed:
                raise ValueError('enabled mod source inventory has duplicate paths')
            listed[relative.casefold()] = relative
            source = (mod_root / relative).resolve()
            if not source.is_relative_to(mod_root):
                raise ValueError('enabled mod source escapes actual root')
            _, source_bytes = _file({'path': str(source), 'bytes': row['bytes'], 'sha256': row['sha256']})
            _reject_related_override(relative, source_bytes)
        actual = {str(item.relative_to(mod_root)).replace('\\', '/').casefold()
                  for item in mod_root.rglob('*') if item.is_file()}
        if actual != set(listed):
            raise ValueError('enabled mod actual file set differs from complete inventory')
    implementation_root = _path(inventory['implementation_root'])
    implementation = inventory['implementation_sources']
    if type(implementation) is not list or len(implementation) != len(IMPLEMENTATION_PATHS):
        raise ValueError('player-control implementation source inventory is incomplete')
    for relative, row in zip(IMPLEMENTATION_PATHS, implementation):
        actual, _ = _file(row)
        if actual != implementation_root / relative:
            raise ValueError('fixed player-control implementation source order/path mismatch')
    return {'source_inventory_sha256': digest,
            'profile_binding_sha256': sha256(projection),
            'profile_projection_bytes': projection.decode('utf-8'),
            'userdir': str(userdir), 'settings_path': str(settings_path),
            'enabled_mod_count': len(mods), 'stock_gui_count': len(STOCK_GUI_PATHS),
            'static_sources_verified': True}
