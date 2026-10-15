"""Fresh paused cash-query raw context; no wallet callback or business labels."""
from __future__ import annotations
from collections.abc import Mapping

from .version_identity import CK3_12004, require_exact_native_build
from .war_payment_observations_v1 import fields, generic_context_snapshot

KEY = 'current_raw_context_v1'
U64 = (1 << 64)-1


def need(condition, message):
    if not condition:
        raise ValueError('war cash current raw context '+message)


def validate_current_raw_context_v1(current: Mapping[str, object], *, snapshot: Mapping[str, object]) -> None:
    if KEY not in current:
        return
    value = current[KEY]
    fields(value, u32='schema_version character_full_id', unsigned='character snapshot_revision', i32='date_raw',
           boolean='actor_identity_stable same_frame_ready admission_ready',
           strings='observation_kind attribution_scope maintenance_attribution', nested='values unavailable_reason')
    need(require_exact_native_build(current.get('game_version'), current.get('executable_sha256')) == CK3_12004,
         'requires the exact .4 source')
    need(value['schema_version'] == 1 and value['observation_kind'] == 'paused_current_raw_context'
         and value['attribution_scope'] == 'current_raw_context_only' and value['maintenance_attribution'] == 'unclosed',
         'source scope was relabeled')
    actor = snapshot.get('played_character')
    need(isinstance(actor, Mapping) and type(actor.get('character_id')) is int
         and 0 < value['character_full_id'] < (1 << 31)
         and value['character_full_id'] == current.get('played_character_id') == actor['character_id']
         and value['character'] != 0 and value['actor_identity_stable'] is True,
         'does not retain its current played Character')
    need(type(snapshot.get('native_revision')) is int and type(snapshot.get('date_raw')) is int
         and value['snapshot_revision'] == current.get('snapshot_revision') == snapshot['native_revision']
         and value['date_raw'] == current.get('date_raw') == snapshot['date_raw'],
         'belongs to another revision or date')
    readiness = current.get('readiness')
    need(isinstance(readiness, Mapping) and type(readiness.get('same_frame_ready')) is bool
         and value['same_frame_ready'] is readiness['same_frame_ready'], 'same-frame result is inconsistent')
    generic_context_snapshot(value['values'])
    raw = value['values']
    frame = (value['same_frame_ready'] and snapshot.get('paused') is True and snapshot.get('map_ready') is True
             and actor.get('alive') is True)
    base = raw['context_identity_before']
    aligned = bool(base and base % 8 == 0 and base <= U64-0x2cf)
    admitted = bool(frame and raw['capture_complete'] and aligned)
    reason = ('war_cash_current_raw_context_frame_unqualified' if not frame else
              'war_cash_current_raw_context_incomplete' if not raw['capture_complete'] else
              'war_cash_current_raw_context_unaligned_or_overflow' if not aligned else None)
    need(value['admission_ready'] is admitted and value['unavailable_reason'] == reason,
         'admission flag or unavailable reason disagrees with raw evidence')
