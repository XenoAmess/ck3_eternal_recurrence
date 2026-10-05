"""Immutable current opposite retained-row membership; no inferred19F operand."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class CurrentRetainedEligibilityRow:
    effect_key: str | None
    contribution_raw: int
    flag88_raw: int | None
    flag89_raw: int | None
    flags_unavailable_reason: str | None


@dataclass(frozen=True)
class CurrentRetainedEligibilitySide:
    side_index: int
    rows: tuple[CurrentRetainedEligibilityRow, ...] | None
    unavailable_reason: str | None


@dataclass(frozen=True)
class ActualOppositeEligibilityInputs:
    combat_id: int
    province_id: int
    snapshot_revision: int
    observed_date_raw: int
    sides: tuple[CurrentRetainedEligibilitySide, ...]


def adapt_actual_opposite_effect_eligibility(
    diagnostic: Mapping[str, object],
) -> ActualOppositeEligibilityInputs | None:
    if diagnostic.get('current_frame_qualified') is not True:
        return None
    stored = diagnostic.get('stored_inputs')
    if stored is None:
        return None
    source = diagnostic['source']
    sides = []
    for side in stored['sides']:
        rows = None
        if side['rows'] is not None:
            copied = []
            for row in side['rows']:
                flags = row.get('effect_flags_v1')
                copied.append(CurrentRetainedEligibilityRow(
                    row['effect_key'], row['contribution_raw'],
                    flags['flag88_raw'] if flags is not None else None,
                    flags['flag89_raw'] if flags is not None else None,
                    flags['unavailable_reason'] if flags is not None else 'stored_effect_flags_v1_not_published',
                ))
            rows = tuple(copied)
        sides.append(CurrentRetainedEligibilitySide(side['side_index'], rows, side['unavailable_reason']))
    return ActualOppositeEligibilityInputs(source['combat_id'], source['province_id'],
        source['snapshot_revision'], source['observed_date_raw'], tuple(sides))


def _wrap64(value: int) -> int:
    return ((value + (1 << 63)) % (1 << 64)) - (1 << 63)


def evaluate_actual_opposite_effect_eligibility(inputs: ActualOppositeEligibilityInputs) -> dict[str, object]:
    sides = []
    for own_index in range(2):
        opposite = inputs.sides[1 - own_index]
        rows = None
        sum_ready = opposite.rows is not None
        membership_ready = opposite.rows is not None
        total = 0
        if opposite.rows is not None:
            rows = []
            for ordinal, row in enumerate(opposite.rows):
                observed = row.flag88_raw is not None and row.flag89_raw is not None
                eligible = (row.flag88_raw != 0 or row.flag89_raw != 0) if observed else None
                contribution = row.contribution_raw if eligible else 0 if eligible is False or row.contribution_raw == 0 else None
                membership_ready = membership_ready and observed
                if contribution is None:
                    sum_ready = False
                else:
                    total = _wrap64(total + contribution)
                rows.append({'native_ledger_index': ordinal, 'effect_key': row.effect_key,
                             'retained_contribution_raw': row.contribution_raw,
                             'flag88_raw': row.flag88_raw, 'flag89_raw': row.flag89_raw,
                             'eligible': eligible, 'eligible_contribution_raw': contribution,
                             'flags_unavailable_reason': row.flags_unavailable_reason})
        sides.append({'side_index': own_index, 'opposite_side_index': opposite.side_index,
                      'ready': sum_ready, 'membership_ready': membership_ready,
                      'ordered_opposite_rows': rows,
                      'eligible_native_ledger_indices': [row['native_ledger_index'] for row in rows if row['eligible'] is True] if rows is not None else None,
                      'eligible_contribution_sum_raw': total if sum_ready else None,
                      'unavailable_reason': opposite.unavailable_reason if opposite.rows is None
                          else None if sum_ready else 'opposite_nonzero_retained_amount_flags_unavailable'})
    return {'schema_version': 1, 'mode': 'actual_current_opposite_effect_eligibility',
            'ready': all(side['ready'] for side in sides), 'scale': 100000,
            'combat_id': inputs.combat_id, 'province_id': inputs.province_id,
            'snapshot_revision': inputs.snapshot_revision, 'observed_date_raw': inputs.observed_date_raw,
            'sides': sides, 'membership_source': 'current_loaded_effect_raw_88_OR_89_nonzero',
            'amount_source': 'actual_retained_16B_row_8',
            'nested_19F_contribution_ready': False, 'own_19F_operand_observed': False,
            'current_effect_points_used_as_amount': False, 'constructor_clamp_reconstructed': False,
            'future_contact_preview': False, 'complete_forecast_ready': False}
