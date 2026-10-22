"""Validated managed-campaign identity for idempotent map-pause recovery."""
from __future__ import annotations

from dataclasses import dataclass
import re

from .version_identity import require_exact_native_build


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or any(type(key) is not str for key in value):
        raise ValueError('Expected a native metadata object')
    return {key: item for key, item in value.items()}


def _text(value: object) -> str:
    if type(value) is not str or not isinstance(value, str) or not value or '\0' in value:
        raise ValueError('Expected nonempty native identity text')
    return value


def _integer(value: object, low: int, high: int) -> int:
    if type(value) is not int or not isinstance(value, int) or not low <= value <= high:
        raise ValueError('Expected an exact bounded native integer')
    return value


@dataclass(frozen=True)
class ManagedPauseOwnerV1:
    game_version: str
    executable_sha256: str
    bridge_pid: int
    connection_generation: int
    adapter_id: str
    pipe_name: str
    run_id: str
    state_dir: str
    host_path: str
    frozen_argv_sha256: str
    actor_id: int
    local_player_id: int
    speed: int


def managed_pause_owner_v1(value: object) -> ManagedPauseOwnerV1 | None:
    """Bind the allocated campaign without manufacturing a one-life episode."""
    try:
        row = _object(value)
        diagnostic = _object(row.get('diagnostics'))
        hello = _object(diagnostic.get('hello'))
        actor = _object(row.get('played_character'))
        run = _object(row.get('managed_campaign_run_binding'))
        if (row.get('episode_projection') != 'native_campaign' or row.get('episode_run_id') is not None
                or row.get('backend_id') != 'native-headless' or row.get('source') != 'injected-dll-named-pipe'
                or row.get('map_ready') is not True or row.get('one_life_terminal_reason') is not None
                or actor.get('alive') is not True or actor.get('source') != 'native'
                or diagnostic.get('connected') is not True or hello.get('ck3_build_match') is not True
                or set(run) != {'run_id', 'state_dir', 'bridge_pipe', 'host_path', 'frozen_argv_sha256'}):
            raise ValueError('Managed native campaign owner is unavailable')
        _integer(row.get('format_version'), 1, 1)
        _integer(row.get('revision'), 1, 2**63 - 1)
        _integer(row.get('native_revision'), 1, 2**63 - 1)
        _integer(row.get('date_raw'), 1, 2**31 - 1)
        build = require_exact_native_build(hello.get('expected_ck3_version'), hello.get('expected_ck3_sha256'))
        pid = _integer(diagnostic.get('bridge_pid'), 1, 2**32 - 1)
        generation = _integer(diagnostic.get('connection_generation'), 1, 2**64 - 1)
        if (_integer(hello.get('pid'), 1, 2**32 - 1) != pid
                or _integer(hello.get('connection_generation'), 1, 2**64 - 1) != generation):
            raise ValueError('Native hello process/generation differs')
        pipe = _text(diagnostic.get('pipe_name'))
        if _text(run.get('bridge_pipe')) != pipe:
            raise ValueError('Allocated and observed pipes differ')
        digest = _text(run.get('frozen_argv_sha256'))
        if re.fullmatch('[0-9a-f]{64}', digest) is None:
            raise ValueError('Frozen argv SHA is invalid')
        adapter = _text(hello.get('game_adapter_id'))
        if adapter != f'ck3-{build.game_version}-msvc-x64':
            raise ValueError('Native adapter and exact build differ')
        return ManagedPauseOwnerV1(build.game_version, build.executable_sha256, pid, generation, adapter, pipe,
            _text(run.get('run_id')), _text(run.get('state_dir')), _text(run.get('host_path')), digest,
            _integer(actor.get('character_id'), 1, 2**32 - 2), _integer(row.get('local_player_id'), 0, 2**31 - 1),
            _integer(row.get('speed'), 1, 5))
    except ValueError:
        return None
