"""Keep allocated originals immutable while observing exact game-owned outputs."""
from __future__ import annotations

from collections.abc import Callable, Mapping
import hashlib
import json
from pathlib import Path
import re
from typing import TypedDict


MUTABLE_PROFILE_FILES = frozenset({"pdx_settings.txt", "player/game_rules/presets.txt"})


class InputDigest(TypedDict):
    bytes: int
    sha256: str


class FileIdentity(InputDigest):
    path: str


class GameOwnedProfileObservation(TypedDict):
    original_launch_pin: FileIdentity
    immutable_original_snapshot: FileIdentity
    current_game_owned_output: FileIdentity
    bytes_changed: bool
    meaning: str


class RunningInputsObservation(TypedDict):
    immutable_inputs_checked: int
    mutable_profile_observations: list[GameOwnedProfileObservation]


class AllocatedRunningSettings(TypedDict):
    allocation: FileIdentity
    settings: GameOwnedProfileObservation
    immutable_inputs_checked: int
    mutable_profile_observations: list[GameOwnedProfileObservation]


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or any(type(key) is not str for key in value):
        raise ValueError('JSON object with string keys required')
    return {key: item for key, item in value.items()}


def _path(value: object) -> Path:
    if type(value) is not str or not value or not Path(value).is_absolute():
        raise ValueError('Actual absolute input path required')
    return Path(value).resolve()


def _digest(value: object) -> InputDigest:
    row = _object(value)
    size, digest = row.get('bytes'), row.get('sha256')
    if (set(row) != {'bytes', 'sha256'} or type(size) is not int or size < 0
            or type(digest) is not str or re.fullmatch('[0-9a-f]{64}', digest) is None):
        raise ValueError('Exact original input byte count and SHA-256 required')
    return {'bytes': size, 'sha256': digest}


def identity(path: str | Path) -> FileIdentity:
    path = Path(path).resolve()
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest.hexdigest()}


def validate_running_inputs(live: str | Path, frozen: Mapping[str, object], *,
                            observer: Callable[[Path], FileIdentity] = identity) -> RunningInputsObservation:
    """Check every original Pin; only two exact allocated profile outputs may vary.

    CK3 rewrites settings and writes LastAppliedRules on ordinary Rules Apply.
    Each allowed output still needs its exact immutable allocation snapshot.
    Sibling presets, mod content, DLC and all snapshots remain immutable.
    """
    live = Path(live).resolve()
    profile = (_path(frozen.get('state_dir')) / 'profile').resolve()
    files = _object(frozen.get('files'))
    result: RunningInputsObservation = {'immutable_inputs_checked': 0, 'mutable_profile_observations': []}
    for name, value in files.items():
        row = _digest(value)
        path = _path(name)
        relative = path.relative_to(profile).as_posix() if path.is_relative_to(profile) else None
        if relative is not None and relative in MUTABLE_PROFILE_FILES:
            snapshot = (live / 'input-snapshots/profile' / relative).resolve()
            if files.get(str(snapshot)) != row:
                raise ValueError('Mutable input has no exact original immutable snapshot: ' + name)
            original = observer(snapshot)
            if (original['bytes'], original['sha256']) != (row['bytes'], row['sha256']):
                raise ValueError('Original mutable input snapshot changed: ' + str(snapshot))
            observed = observer(path)
            result['mutable_profile_observations'].append({
                'original_launch_pin': {'path': str(path), **row},
                'immutable_original_snapshot': original, 'current_game_owned_output': observed,
                'bytes_changed': (observed['bytes'], observed['sha256']) != (row['bytes'], row['sha256']),
                'meaning': 'current game-owned profile output; original input remains retained and unchanged'})
            continue
        actual = observer(path)
        if (actual['bytes'], actual['sha256']) != (row['bytes'], row['sha256']):
            raise ValueError('Immutable original input changed: ' + name)
        result['immutable_inputs_checked'] += 1
    return result


def verify_allocated_running_settings(profile: Mapping[str, object], settings_row: object) -> AllocatedRunningSettings:
    """Bind settings to its allocation and retain every game-owned observation."""
    live = _path(profile.get('evidence_directory'))
    frozen_path = live / 'frozen-argv.json'
    frozen = _object(json.loads(frozen_path.read_text(encoding='utf-8-sig')))
    context = _object(json.loads((live / 'ready-context.json').read_text(encoding='utf-8-sig')))
    if (identity(frozen_path) != context.get('frozen_argv') or context.get('run_id') != frozen.get('run_id')
            or _path(context.get('run_dir')) != live):
        raise ValueError('Normal-exit running profile lacks its exact original ready/frozen allocation')
    state, userdir = _path(profile.get('state_directory')), _path(profile.get('userdir'))
    if _path(frozen.get('state_dir')) != state or userdir != state / 'profile':
        raise ValueError('Normal-exit running profile crossed the actual allocated state/userdir')
    settings = _object(settings_row)
    if set(settings) != {'path', 'bytes', 'sha256'} or _path(settings.get('path')) != userdir / 'pdx_settings.txt':
        raise ValueError('Only allocated top-level pdx_settings is the settings output')
    original = _digest({key: settings[key] for key in ('bytes', 'sha256')})
    if _object(frozen.get('files')).get(str(userdir / 'pdx_settings.txt')) != original:
        raise ValueError('Normal-exit settings inventory differs from the original allocated launch pin')
    observed = validate_running_inputs(live, frozen)
    values = [value for value in observed['mutable_profile_observations']
              if value['original_launch_pin']['path'] == str(userdir / 'pdx_settings.txt')]
    if len(values) != 1:
        raise ValueError('One exact allocated settings output observation required')
    return {'allocation': identity(frozen_path), 'settings': values[0],
            'immutable_inputs_checked': observed['immutable_inputs_checked'],
            'mutable_profile_observations': observed['mutable_profile_observations']}
