"""Strict consumer regressions over frozen compiled 1.20.0.4 payment wire.

These fixtures are synthetic native callbacks, not game runtime qualification.
The tests use explicit checks so Python optimization cannot remove validation.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(REPO), str(REPO/'ck3_autonomous_player/src')]
from xar_autoplayer.bridge import war_payment_observations_v1 as payment
from xar_autoplayer.bridge.version_identity import CK3_12004

FIXTURES = Path(__file__).with_name('fixtures')
CONTEXT_KEY = 'generic_wallet_context_v1'
NATIVE_FIXTURE_SHA256 = '27214c3ccdf6aba2b9510f65fd50e29ff03539a80aecddd8ea42e051c75320d3'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def load_cases(name, *, expected_sha256=None):
    raw = (FIXTURES/name).read_bytes()
    if expected_sha256 is not None:
        require(hashlib.sha256(raw).hexdigest() == expected_sha256, 'Compiled native wire changed')
    rows = json.loads(raw)
    require(isinstance(rows, list) and rows, 'Compiled wire must be a nonempty case list')
    result = []
    for row in rows:
        require(isinstance(row, dict) and isinstance(row.get('case'), str)
                and isinstance(row.get('value'), dict), 'Compiled wire envelope is malformed')
        journal = row['value'].get(payment.JOURNAL_KEY, row['value'])
        require(isinstance(journal, dict), 'Compiled wire contains no journal')
        result.append((row['case'], journal))
    return result


LEGACY_CASES = load_cases('war_payment_compiled_12004_a06.json')
NATIVE_CASES = load_cases('war_payment_generic_context_12004_a04.json', expected_sha256=NATIVE_FIXTURE_SHA256)
require(len(LEGACY_CASES) == 9 and len(NATIVE_CASES) == 16, 'Frozen fixture case count changed')
BASE_JOURNAL = next(journal for name, journal in NATIVE_CASES if name == 'positive')
BASE_RECORD_INDEX = next(index for index, row in enumerate(BASE_JOURNAL['records']) if CONTEXT_KEY in row)
BASE_CONTEXT = BASE_JOURNAL['records'][BASE_RECORD_INDEX][CONTEXT_KEY]
require(BASE_CONTEXT['before']['capture_complete'] and BASE_CONTEXT['after']['capture_complete'],
        'Native positive source has no complete context')


def snapshot(journal):
    session = journal['current_session']
    date = session['native_date_raw'] & 0xffffffff
    if date >= 1 << 31:
        date -= 1 << 32
    return dict(paused=True, map_ready=True, revision=session['snapshot_revision']+1,
                native_revision=session['snapshot_revision'], date_raw=date,
                snapshot_id='synthetic-generic-wallet-consumer:'+str(session['snapshot_revision']),
                played_character=dict(character_id=session['player_character_full_id'], alive=True),
                diagnostics=dict(bridge_pid=session['pid'], connection_generation=session['connection_generation'],
                                 hello=dict(expected_ck3_version=CK3_12004.game_version,
                                            expected_ck3_sha256=CK3_12004.executable_sha256)))


def normalize(journal):
    # A fixture's source identity binds its own synthetic snapshot; no host identity
    # is inferred and no runtime qualification is claimed by these tests.
    return payment.normalize_journal(journal, snapshot=snapshot(journal), machine_id=journal['machine_id'])


def record_change(change):
    def apply(journal):
        row = journal['records'][BASE_RECORD_INDEX]
        change(row, row[CONTEXT_KEY])
    return apply


def negative_cases():
    result = []

    def add(name, change):
        result.append(pytest.param(record_change(change), id=name))

    add('optional_key_null', lambda r,c:r.update({CONTEXT_KEY:None}))
    add('optional_key_scalar', lambda r,c:r.update({CONTEXT_KEY:0}))
    for key in BASE_CONTEXT:
        add('missing_context_key:'+key, lambda r,c,k=key:c.pop(k))
    add('extra_context_key', lambda r,c:c.update(invented=True))
    for key, value in (('schema_version',True), ('schema_version',2),
                       ('source_entry_rva',True), ('source_entry_rva',0x28a6d11),
                       ('source_wallet_return_rva',0x28a6d7d),
                       ('attribution_scope','military_maintenance'), ('maintenance_attribution','closed'),
                       ('before_computed_add_raw',True), ('before_computed_add_raw',1 << 63),
                       ('before_formula_matches_amount',1), ('context_values_stable',1)):
        add('malformed_context_scalar:'+key+':'+repr(value), lambda r,c,k=key,v=value:c.update({k:v}))
    add('wrong_record_kind', lambda r,c:r.update(kind=3))
    add('wrong_record_caller', lambda r,c:r.update(caller_return_rva=0x28a6d7d))
    add('wrong_computed_formula', lambda r,c:c.update(before_computed_add_raw=c['before_computed_add_raw'] ^ 1))
    add('wrong_formula_match', lambda r,c:c.update(before_formula_matches_amount=not c['before_formula_matches_amount']))
    add('wrong_values_stability', lambda r,c:c.update(context_values_stable=not c['context_values_stable']))
    for phase in ('before', 'after'):
        add('null_snapshot:'+phase, lambda r,c,p=phase:c.update({p:None}))
        add('extra_snapshot_key:'+phase, lambda r,c,p=phase:c[p].update(invented=True))
        for key in BASE_CONTEXT[phase]:
            add('missing_snapshot_key:'+phase+':'+key, lambda r,c,p=phase,k=key:c[p].pop(k))
        for key, value in (('context_identity_before',True), ('context_identity_after',-1),
                           ('value_2c0',True), ('value_2c8',-(1 << 63)-1),
                           ('value_28',1 << 63), ('value_30',0.0), ('failed_reads',1 << 32),
                           ('capture_complete',1), ('context_stable',0)):
            add('malformed_snapshot_scalar:'+phase+':'+key,
                lambda r,c,p=phase,k=key,v=value:c[p].update({k:v}))
        add('wrong_snapshot_identity_stability:'+phase,
            lambda r,c,p=phase:c[p].update(context_stable=not c[p]['context_stable']))
        add('wrong_snapshot_completeness:'+phase,
            lambda r,c,p=phase:c[p].update(capture_complete=not c[p]['capture_complete']))
        add('values_without_input_identity:'+phase,
            lambda r,c,p=phase:c[p].update(context_identity_before=None, context_stable=False, capture_complete=False))
    add('null_parent_trace', lambda r,c:c.update(parent_trace=None))
    add('extra_parent_trace_key', lambda r,c:c['parent_trace'].update(invented=True))
    for key in BASE_CONTEXT['parent_trace']:
        add('missing_trace_key:'+key, lambda r,c,k=key:c['parent_trace'].pop(k))
    for key, value in (('module_base',True), ('module_base',1 << 64), ('module_image_size',1 << 32),
                       ('reported_frame_count',True), ('caller_match_count',-1), ('capture_succeeded',1),
                       ('truncated',0), ('parent_in_same_image',1), ('parent_return_absolute',True),
                       ('parent_return_rva',-1), ('frames_absolute',[0]), ('frames_absolute',[True]),
                       ('frames_absolute',[1 << 64]), ('frames_absolute',[1]*33), ('frames_absolute',None)):
        add('malformed_trace_scalar:'+key+':'+repr(value),
            lambda r,c,k=key,v=value:c['parent_trace'].update({k:v}))
    add('wrong_trace_capture', lambda r,c:c['parent_trace'].update(capture_succeeded=not c['parent_trace']['capture_succeeded']))
    add('wrong_trace_truncation', lambda r,c:c['parent_trace'].update(truncated=not c['parent_trace']['truncated']))
    add('wrong_trace_match_count', lambda r,c:c['parent_trace'].update(caller_match_count=c['parent_trace']['caller_match_count']+1))
    add('wrong_trace_parent_address', lambda r,c:c['parent_trace'].update(
        parent_return_absolute=(c['parent_trace']['parent_return_absolute'] ^ 1)
        if c['parent_trace']['parent_return_absolute'] is not None else 1))
    add('wrong_trace_image', lambda r,c:c['parent_trace'].update(parent_in_same_image=not c['parent_trace']['parent_in_same_image']))
    add('wrong_trace_parent_rva', lambda r,c:c['parent_trace'].update(
        parent_return_rva=(c['parent_trace']['parent_return_rva'] ^ 1)
        if c['parent_trace']['parent_return_rva'] is not None else 1))
    result.append(pytest.param(lambda journal:journal.update(maintenance_attribution='closed'),
                               id='journal_attribution_promotion'))
    require(len(result) == 110, 'Malformed-context parameter count changed')
    return result


def incomplete_before(row, context):
    context['before'].update(context_identity_after=None, context_stable=False, capture_complete=False)
    context.update(before_computed_add_raw=None, before_formula_matches_amount=None, context_values_stable=False)


def changed_after(row, context):
    context['after'].update(context_identity_after=(context['after']['context_identity_before'] ^ 1),
                            context_stable=False, capture_complete=False)
    context['context_values_stable'] = False


def incomplete_values(row, context):
    context['before'].update(value_2c0=None, failed_reads=1, capture_complete=False)
    context.update(before_computed_add_raw=None, before_formula_matches_amount=None, context_values_stable=False)


def formula_mismatch(row, context):
    row['amount_raw'] = context['before_computed_add_raw'] ^ 1
    context['before_formula_matches_amount'] = False


def no_parent(row, context):
    context['parent_trace'].update(module_base=0, module_image_size=0, reported_frame_count=0,
                                  capture_succeeded=False, truncated=False, caller_match_count=0,
                                  frames_absolute=[], parent_return_absolute=None,
                                  parent_return_rva=None, parent_in_same_image=False)


UNKNOWN_CASES = [
    pytest.param(record_change(incomplete_before), id='returned_pointer_unknown_preserves_observed_values'),
    pytest.param(record_change(changed_after), id='returned_pointer_changed_preserves_observed_values'),
    pytest.param(record_change(incomplete_values), id='failed_read_preserves_unknown'),
    pytest.param(record_change(formula_mismatch), id='formula_mismatch_retained_without_attribution'),
    pytest.param(record_change(no_parent), id='unwind_unknown_preserves_unknown'),
]


@pytest.mark.parametrize('case_name,journal', LEGACY_CASES, ids=[name for name, _ in LEGACY_CASES])
def test_legacy_exact_compatibility(case_name, journal):
    original = copy.deepcopy(journal)
    result = normalize(journal)
    require(result == original and journal == original, 'Legacy journal changed: '+case_name)
    require(result is not journal, 'Legacy result aliases its input: '+case_name)
    require(all(CONTEXT_KEY not in row for row in result['records']), 'Legacy context was synthesized: '+case_name)


@pytest.mark.parametrize('case_name,journal', NATIVE_CASES, ids=[name for name, _ in NATIVE_CASES])
def test_compiled_native_wire(case_name, journal):
    original = copy.deepcopy(journal)
    result = normalize(journal)
    require(result == original and journal == original, 'Compiled journal changed: '+case_name)
    require(result is not journal, 'Compiled result aliases its input: '+case_name)
    require(result['maintenance_attribution'] == 'unclosed', 'Native fixture attribution was promoted: '+case_name)


@pytest.mark.parametrize('change', negative_cases())
def test_rejects_malformed_context(change):
    journal = copy.deepcopy(BASE_JOURNAL)
    change(journal)
    with pytest.raises(ValueError):
        normalize(journal)


@pytest.mark.parametrize('change', UNKNOWN_CASES)
def test_preserves_unknown_without_attribution(change):
    journal = copy.deepcopy(BASE_JOURNAL)
    change(journal)
    result = normalize(journal)
    require(result == journal, 'Valid raw unknown evidence changed')
    require(result['maintenance_attribution'] == 'unclosed', 'Raw context promoted attribution')
    require(result['qualified_boarding_debits'] == BASE_JOURNAL['qualified_boarding_debits'],
            'Raw context changed boarding qualifications')
