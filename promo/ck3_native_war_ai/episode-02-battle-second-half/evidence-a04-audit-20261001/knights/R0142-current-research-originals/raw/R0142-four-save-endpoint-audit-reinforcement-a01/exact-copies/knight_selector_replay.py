"""Replay captured original selector calls; never evaluates game predicates.

The filter ABI and swap behavior are pinned to CK3 1.19.0.6. This module
checks the actual emitted sequence, including duplicate candidates and a
preexisting vector prefix. An offline fixture is not native game evidence.
"""
from __future__ import annotations


def _word(token):
    if type(token) is int:
        return token
    if isinstance(token, str) and token.startswith('process-local-0x'):
        return int(token[len('process-local-0x'):], 16)
    raise ValueError('missing original process-local raw word')


def candidate_words(record):
    words = []
    for row in record['selector_candidates']:
        first, second = row['scope_word0'], _word(row['scope_word1_token'])
        if type(first) is not int or first < 0:
            raise ValueError('invalid raw candidate word0')
        if first & 0xFFFF == 4:
            if row['character_full_identity_matches'] is not True or row['character_id'] != second & 0xFFFFFFFF:
                raise ValueError('candidate typed full character identity not read')
        words.append((first, second))
    return words


def replay_selector_filters(journal: dict) -> dict:
    """Check materialization, short circuit, original AL, and actual tail swaps.

    A return-point vector is captured before the caller performs its swap.
    The subsequent enter or filter-return vector must match the simulated
    swap. No RNG, predicate, or materializer is invoked by this function.
    """
    records = journal['records']
    if journal['failure_flags'] != 0 or journal['truncated'] is not False:
        raise ValueError('selector replay requires untruncated zero-flag journal')
    pairs = {}
    for row in records:
        if row['boundary'] not in ('filter_enter', 'filter_return'):
            continue
        edge = row['boundary'].rsplit('_', 1)[1]
        pair = pairs.setdefault(row['invocation'], {})
        if edge in pair:
            raise ValueError('duplicate filter edge')
        pair[edge] = row
    if not pairs:
        return {'status': 'NOT_CAPTURED', 'complete': False, 'filters': [],
                'gaps': ['original materializer/filter/predicate journal absent']}
    results = []
    for invocation, pair in pairs.items():
        if set(pair) != {'enter', 'return'}:
            raise ValueError('incomplete original filter pair')
        begin, end = pair['enter'], pair['return']
        if begin['sequence'] >= end['sequence']:
            raise ValueError('reversed filter pair')
        group = [r for r in records if begin['sequence'] <= r['sequence'] <= end['sequence']]
        mats = {edge: [r for r in group if r['boundary'] == 'materializer_' + edge] for edge in ('enter', 'return')}
        if any(len(rows) != 1 for rows in mats.values()):
            raise ValueError('one original materializer pair per filter required')
        materialize_in, materialize_out = mats['enter'][0], mats['return'][0]
        if not begin['sequence'] < materialize_in['sequence'] < materialize_out['sequence'] < end['sequence']:
            raise ValueError('materializer ordering')
        meta = ('selector_vector_token', 'selector_list_context_token', 'selector_prefix_count',
                'selector_source_side_index', 'source_predicate_count', 'shared_predicate_count',
                'native_scope_words')
        relevant = [r for r in group if r['boundary'] in (
            'filter_enter', 'filter_return', 'materializer_enter', 'materializer_return',
            'predicate_enter', 'predicate_return')]
        if not all(all(r[k] == begin[k] for k in meta) and r['failure_flags'] == 0 and
                   r['selector_source_combat_identity_matches'] is True for r in relevant):
            raise ValueError('same original vector/source/predicate identity required')
        if any(r['invocation'] != invocation for r in (materialize_in, materialize_out, end)):
            raise ValueError('materializer belongs to different filter')
        scope0, scope1 = begin['native_scope_words']
        side = begin['selector_source_side_index']
        if scope0 & 0xFFFF != 0xB or side not in (0, 1) or \
                ((scope0 >> 16) & 0xFFFF == 0) != (side == 0) or scope1 & 0xFFFFFFFF != journal['combat_id']:
            raise ValueError('raw combat-side scope does not resolve declared original side')
        prefix = candidate_words(begin)
        if begin['selector_prefix_count'] != len(prefix) or candidate_words(materialize_in) != prefix:
            raise ValueError('preexisting prefix count/vector not preserved at materializer entry')
        source_sides = [s for s in materialize_in['sides'] if s['side_index'] == side]
        if len(source_sides) != 1:
            raise ValueError('unique original source-side entries required')
        source_rows = [r for r in source_sides[0]['entries'] if r['bucket'] == 1]
        source_ids = [r['character_id'] for r in source_rows if r['character_id'] != -1]
        if any(type(cid) is not int or cid <= 0 for cid in source_ids):
            raise ValueError('invalid full character ID in original knight rows')
        expected = prefix + [(4, cid) for cid in source_ids]
        if candidate_words(materialize_out) != expected:
            raise ValueError('materializer append does not match original source knight order')
        predicates = [r for r in relevant if r['boundary'].startswith('predicate_')]
        if len(predicates) % 2:
            raise ValueError('odd predicate boundary count')
        cursor, index, swaps, observed = 0, len(prefix), [], []
        no_calls = begin['source_predicate_count'] == begin['shared_predicate_count'] == 0

        def observe(role: int):
            nonlocal cursor
            if cursor + 1 >= len(predicates):
                raise ValueError('missing original predicate call')
            enter, returned = predicates[cursor:cursor + 2]
            cursor += 2
            if enter['boundary'] != 'predicate_enter' or returned['boundary'] != 'predicate_return' or \
                    enter['invocation'] != returned['invocation'] or enter['predicate_role'] != role or \
                    returned['predicate_role'] != role or enter['selector_current_index'] != index or \
                    returned['selector_current_index'] != index:
                raise ValueError('original predicate role/index/edge mismatch')
            if candidate_words(enter) != expected or candidate_words(returned) != expected:
                raise ValueError('predicate original vector or pre-swap return vector differs')
            if returned['original_predicate_boolean_read'] is not True or \
                    type(returned['original_predicate_boolean']) is not bool or \
                    bool(returned['original_return_bits'] & 0xFF) != returned['original_predicate_boolean']:
                raise ValueError('original AL boolean not independently preserved')
            observed.append({'invocation': enter['invocation'], 'index': index, 'role': role,
                             'candidate': list(expected[index]), 'original_return_bits': returned['original_return_bits'],
                             'original_boolean': returned['original_predicate_boolean']})
            return returned['original_predicate_boolean']

        if not no_calls:
            while index < len(expected):
                accepted = expected[index][0] & 0xFFFF != 0
                if accepted:
                    accepted = observe(1)
                if accepted:
                    accepted = observe(2)
                if accepted:
                    index += 1
                else:
                    removed, tail = expected[index], expected[-1]
                    expected[index] = tail
                    expected.pop()
                    swaps.append({'index': index, 'removed': list(removed), 'tail': list(tail),
                                  'result': [list(w) for w in expected]})
        if cursor != len(predicates):
            raise ValueError('extra predicate call, including a forbidden source call after shared false')
        if candidate_words(end) != expected or expected[:len(prefix)] != prefix:
            raise ValueError('filter return differs from original short-circuit/tail-swap replay')
        results.append({'invocation': invocation, 'parent_invocation': begin['parent_invocation'],
                        'sequence_enter': begin['sequence'], 'sequence_return': end['sequence'],
                        'prefix_count': len(prefix), 'source_side': side, 'source_character_ids': source_ids,
                        'materialized_raw_words': [list(w) for w in candidate_words(materialize_out)],
                        'original_predicate_calls': observed, 'tail_swaps': swaps,
                        'final_raw_words': [list(w) for w in expected], 'both_predicate_counts_zero': no_calls,
                        'vector_token': begin['selector_vector_token'], 'complete': True})
    return {'status': 'ORIGINAL_SELECTOR_FILTER_SEQUENCE_REPLAYED', 'complete': True,
            'filters': results, 'gaps': [], 'limits': 'Completeness covers these captured original filter calls. Outer RNG and returned selection require their separately bound original selector record.'}
