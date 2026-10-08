"""Use current refill opportunity only after actual troop strength is tied."""
from __future__ import annotations

from typing import Iterable

from .bridge.army_scoped_ordered_refill_projection import (
    project_scoped_observed_prepared_ordered_refill,
)
from .bridge.public_unit_contract import is_public_cunit_id


def _integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def select_current_replenishment_army_v1(
    armies: Iterable[dict[str, object]], snapshot: dict[str, object],
    *, active_war_ids: Iterable[int],
) -> tuple[dict[str, object] | None, dict[str, object]]:
    """Leave the more productive current garrison when present force is equal.

    The native projection is an explicit held-context core pass, not a date or
    a next-month forecast. Unknown input keeps the existing stable ID choice.
    """
    rows = [army for army in armies if is_public_cunit_id(army.get('army_id'))]
    wars = sorted({identity for identity in active_war_ids
                   if _integer(identity) and identity > 0})
    ledger = {
        'status': 'not_applicable', 'selected_army_id': None,
        'policy_basis': 'actual_current_strength_then_least_current_refill_opportunity',
        'input_basis': 'same_capture_prepared148_ordered_occurrences',
        'context_basis': 'held_current_nonphysical_native_context',
        'active_war_ids': wars, 'query_needed': False, 'candidates': [],
        'actual_after': False, 'full_monthly_ready': False,
    }
    if not rows:
        return None, ledger
    strongest = max(army.get('soldiers') if _integer(army.get('soldiers')) else -1
                    for army in rows)
    tied = [army for army in rows
            if (army.get('soldiers') if _integer(army.get('soldiers')) else -1) == strongest]
    selected = min(tied, key=lambda army: army['army_id'])
    ledger['selected_army_id'] = selected['army_id']
    if (not wars or strongest < 0 or len(tied) < 2
            or any(army.get('army_state') != 'regular'
                   or army.get('move_target_province_id') is not None
                   or army.get('route_province_ids') != []
                   or not _integer(army.get('current_province_id'))
                   or army.get('current_province_id') <= 0 for army in tied)
            or len({army['current_province_id'] for army in tied}) != len(tied)):
        return selected, ledger
    ledger['status'] = 'current_inputs_unavailable'
    if snapshot.get('paused') is not True:
        return selected, ledger
    status = snapshot.get('army_strengths_status')
    if status is None:
        ledger['query_needed'] = True
        return selected, ledger
    if (status != 'available'
            or not isinstance(snapshot.get('snapshot_id'), str)
            or snapshot.get('army_strengths_queried_snapshot_id') != snapshot.get('snapshot_id')
            or snapshot.get('army_strengths_queried_revision') != snapshot.get('revision')
            or not isinstance(snapshot.get('army_strengths'), list)):
        return selected, ledger

    strength_rows = snapshot['army_strengths']
    complete = True
    for army in sorted(tied, key=lambda candidate: candidate['army_id']):
        identity = army['army_id']
        matches = [row for row in strength_rows if isinstance(row, dict)
                   and row.get('army_id') == identity]
        receipt = {'army_id': identity, 'current_soldiers': strongest,
                   'status': 'unavailable', 'conditional_current_soldiers': None,
                   'native_signed_current_delta': None, 'positive_refill_opportunity': None}
        ledger['candidates'].append(receipt)
        if len(matches) != 1:
            complete = False
            continue
        row = matches[0]
        if (row.get('status') != 'available' or row.get('scope_role') != 'player'
                or row.get('current_soldiers') != strongest
                or not isinstance(row.get('war_ids'), list)
                or not set(wars).intersection(row['war_ids'])
                or not isinstance(row.get('scoped_ordered_refill_inputs_v1'), dict)):
            complete = False
            continue
        projection = project_scoped_observed_prepared_ordered_refill(row)
        current = projection.get('conditional_current_soldiers')
        if (projection.get('ordered_core_ready') is not True
                or projection.get('conditional_raised_current_maximum_ready') is not True
                or not _integer(current)):
            receipt['missing_inputs'] = list(projection.get('missing_inputs', []))
            complete = False
            continue
        delta = current - strongest
        receipt.update(status='available', conditional_current_soldiers=current,
                       native_signed_current_delta=delta,
                       positive_refill_opportunity=max(0, delta))
    if not complete:
        return selected, ledger
    chosen = min(ledger['candidates'],
                 key=lambda receipt: (receipt['positive_refill_opportunity'], receipt['army_id']))
    selected = next(army for army in tied if army['army_id'] == chosen['army_id'])
    ledger.update(status='available', selected_army_id=chosen['army_id'])
    return selected, ledger
