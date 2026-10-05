"""One new source-conditioned request-emitter case; no old fixtures or SDK."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path

from xar_autoplayer.simulation.battle_context_preparation_branch_291e210_12003 import (
    NativePreparationSourceRow12003 as Row,
    NativePreparationSourceSpan12003 as Span,
    emit_291e210_contribution_requests_12003,
)


class FocusedCheckError(RuntimeError):
    pass


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n',
                    encoding='utf-8', newline='\n')


def run_focused_case(artifacts: Path | None = None) -> dict[str, object]:
    checks: list[str] = []
    def require(condition: bool, label: str) -> None:
        if not condition:
            raise FocusedCheckError(label)
        checks.append(label)

    block_a = {'count': 2, 'keys_u16': [2, 9], 'values_q64': [301, -77]}
    empty_block = {'count': 0, 'keys_u16': [], 'values_q64': []}
    block_c = {'count': 1, 'keys_u16': [8], 'values_q64': [0]}
    block_d = {'count': 1, 'keys_u16': [3], 'values_q64': [-9]}
    maximum = (1 << 63)-1
    lifestyle = Span(6, (
        Row('frame84:A', maximum, block_a), Row('frame84:A', 1, block_a),
        Row('frame84:B', 0, empty_block),
        Row('frame84:A', 7, block_a), Row('frame84:A', -7, block_a),
        Row('frame84:C', -5, block_c), None,
    ))
    dynasty = Span(3, (
        Row('frame84:C', 5, block_c), Row('frame84:C', -5, block_c),
        Row('frame84:D', -2, block_d),
    ))
    house = Span(2, (Row('frame84:A', 9, block_a), Row('frame84:A', -1, block_a), None))
    unread_extra = Span(None, None)
    inputs = (lifestyle, dynasty, house, False, unread_extra)
    before = deepcopy(inputs)
    if artifacts is not None:
        _write(artifacts/'INPUT.json', {
            'value_origin': 'one explicit synthetic exact-source grouping case; no native frame',
            'lifestyle': asdict(lifestyle), 'dynasty': asdict(dynasty),
            'house': asdict(house), 'house_extra_enabled': False,
            'unread_house_extra': asdict(unread_extra),
        })
    requests = emit_291e210_contribution_requests_12003(*inputs)
    if artifacts is not None:
        _write(artifacts/'OUTPUT.json', [asdict(row) for row in requests])
    require(len(requests) == 7, 'exactly seven native contiguous runs')
    require([r.definition_identity for r in requests] == [
        'frame84:A','frame84:B','frame84:A','frame84:C','frame84:C','frame84:D','frame84:A',
    ], 'native order keeps nonadjacent and cross-span equal identities separate')
    require([r.source_ordinal for r in requests] == [1,1,1,1,2,2,3],
            'fixed lifestyle dynasty house order and no disabled fourth-source requests')
    require([r.source_name for r in requests] == [
        'lifestyle','lifestyle','lifestyle','lifestyle','dynasty','dynasty','house',
    ], 'request source names directly identify consumed spans')
    require([r.first_row_index for r in requests] == [0,2,3,5,0,2,0],
            'run starting indices restart per span')
    require([r.row_count for r in requests] == [2,1,2,1,2,1,2],
            'only adjacent equal identities combine')
    require([r.weight_q64 for r in requests] == [-(1 << 63),0,0,-5,0,-2,8],
            'signed wrap64 and cancellation preserve actual grouped Q64 weights')
    require(requests[1].base_property_block is empty_block,
            'legal zero-weight empty PropertyContainer request retained by identity')
    require(requests[0].base_property_block is block_a and
            requests[2].base_property_block is block_a and
            requests[6].base_property_block is block_a,
            'opaque Def+40 blocks passed through by reference across independent runs')
    require(requests[3].base_property_block is block_c and
            requests[4].base_property_block is block_c and
            requests[5].base_property_block is block_d,
            'remaining actual blocks preserved by reference')
    require(inputs == before, 'source rows and opaque block content/order unchanged')
    return {'status':'FIRST GREEN', 'unique_new_cases':1,
            'public_emitter_invocations':1, 'explicit_check_count':len(checks),
            'checks':checks, 'request_count':len(requests),
            'actual_count_used':True, 'disabled_extra_not_read':True,
            'opaque_blocks_preserved':True, 'old_tests_run':0,
            'native_invocations':0, 'actual_game_days_advanced':0,
            'full_future_context_ready':False}


def test_native_291e210_ordered_contribution_requests() -> None:
    run_focused_case()
