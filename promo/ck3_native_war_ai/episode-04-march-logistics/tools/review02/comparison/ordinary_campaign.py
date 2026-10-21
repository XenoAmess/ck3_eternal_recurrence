"""Ordinary campaign identity for B consumers; never synthesize an episode.

Snapshot birth is not published. Existing runtime/source-proof custody remains
responsible for birth; this projection binds the actual managed source route.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import re
from typing import TypeGuard


def need(ok: object, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def is_object(value: object) -> TypeGuard[Mapping[str, object]]:
    return isinstance(value, Mapping) and all(type(k) is str for k in value)


def text(value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError('explicit nonempty identity text required')
    return value


def positive(value: object) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError('positive exact identity integer required')
    return value


@dataclass(frozen=True)
class ManagedCampaign:
    run_id: str
    state_dir: str
    bridge_pipe: str
    host_path: str
    frozen_argv_sha256: str


def managed(value: object) -> ManagedCampaign:
    if not is_object(value):
        raise ValueError('actual managed campaign source binding required')
    names = ('run_id', 'state_dir', 'bridge_pipe', 'host_path', 'frozen_argv_sha256')
    need(set(value) == set(names), 'managed source binding shape differs')
    values = [text(value[k]) for k in names]
    need(re.fullmatch('[0-9a-f]{64}', values[4]) is not None, 'managed argv SHA differs')
    return ManagedCampaign(*values)


@dataclass(frozen=True)
class EpisodeIdentity:
    episode: str | None
    key_present: bool
    campaign: ManagedCampaign | None
    ordinary_process: tuple[int, int, int] | None


def episode_identity(frame: Mapping[str, object]) -> EpisodeIdentity:
    present = 'episode_run_id' in frame
    value = frame.get('episode_run_id')
    if value is not None:
        return EpisodeIdentity(text(value), present, None, None)
    need(frame.get('episode_projection') == 'native_campaign',
         'missing/null episode requires actual native_campaign projection')
    source = managed(frame.get('managed_campaign_run_binding'))
    diagnostics, actor = frame.get('diagnostics'), frame.get('played_character')
    if not is_object(diagnostics) or not is_object(actor):
        raise ValueError('ordinary process/actor identity missing')
    process = (positive(diagnostics.get('bridge_pid')),
               positive(diagnostics.get('connection_generation')),
               positive(actor.get('character_id')))
    need(diagnostics.get('pipe_name') == source.bridge_pipe,
         'actual managed pipe differs from snapshot transport')
    return EpisodeIdentity(None, present, source, process)


def episode_value(frame: Mapping[str, object]) -> str | None:
    return episode_identity(frame).episode


def same_episode(before: Mapping[str, object], after: Mapping[str, object]) -> None:
    a, b = episode_identity(before), episode_identity(after)
    need((a.episode, a.campaign, a.ordinary_process) ==
         (b.episode, b.campaign, b.ordinary_process),
         'action crossed episode or managed campaign/process/actor')


def check_runtime(frame: Mapping[str, object], runtime: Mapping[str, object]) -> None:
    identity = episode_identity(frame)
    need('episode' in runtime and runtime['episode'] == identity.episode,
         'runtime episode differs')
    if identity.campaign is not None:
        need(managed(runtime.get('managed_campaign_run_binding')) == identity.campaign,
             'ordinary runtime managed source differs')
        need(identity.ordinary_process == (positive(runtime.get('pid')),
             positive(runtime.get('connection_generation')),
             positive(runtime.get('player_character_id'))), 'ordinary runtime identity differs')
        positive(runtime.get('process_create_time_100ns'))
