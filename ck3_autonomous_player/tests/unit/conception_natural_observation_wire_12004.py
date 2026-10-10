"""One new actual ownedjournal -> strict -> independent consumer compound."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import argparse
import datetime
import importlib.util
import json
from pathlib import Path
import sys
import types


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--journal', type=Path, required=True)
    parser.add_argument('--journal-sha256', required=True)
    parser.add_argument('--candidate-src', type=Path, required=True)
    parser.add_argument('--caller-source-module', type=Path, required=True)
    parser.add_argument('--caller-source-sha256', required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise ValueError('new compound output already exists; do not replay')
    args.output_dir.mkdir(parents=True)
    raw = args.journal.read_bytes()
    if sha256(raw).hexdigest() != args.journal_sha256:
        raise ValueError('actual compiled ownedjournal pin changed')
    caller_bytes = args.caller_source_module.read_bytes()
    if sha256(caller_bytes).hexdigest() != args.caller_source_sha256:
        raise ValueError('qualified53 immutable source consumer changed')
    sys.dont_write_bytecode = True
    # Load the new production modules in their actual package namespace. This
    # fixture neither imports a Service/Game backend nor substitutes its facts.
    for name, path in (
        ('xar_autoplayer', args.candidate_src / 'xar_autoplayer'),
        ('xar_autoplayer.bridge', args.candidate_src / 'xar_autoplayer/bridge'),
        ('xar_autoplayer.simulation', args.candidate_src / 'xar_autoplayer/simulation'),
    ):
        package = types.ModuleType(name)
        package.__path__ = [str(path)]
        package.__package__ = name
        sys.modules[name] = package
    name = 'xar_autoplayer.bridge.conception_incoming_caller_sourcebinding_12004'
    spec = importlib.util.spec_from_file_location(name, args.caller_source_module)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    from xar_autoplayer.bridge.conception_natural_observation_contract_12004 import normalize_conception_natural_observations_12004
    from xar_autoplayer.simulation.conception_natural_observation_12004 import project_conception_natural_observations_12004

    journal = json.loads(raw)
    original = deepcopy(journal)
    checks: list[str] = []

    def normalize(value):
        # Actual19b native first/second is opposite to this household query.
        return normalize_conception_natural_observations_12004(
            value, expected_first_character_id=38822, expected_second_character_id=38718)

    def project(value):
        return project_conception_natural_observations_12004(normalize(value))

    def rejects(value):
        try:
            normalize(value)
        except ValueError:
            return
        raise AssertionError('malformed copied wire unexpectedly normalized')

    normalized = normalize(journal)
    observation = project_conception_natural_observations_12004(normalized)
    assert journal == original and normalized == journal and normalized is not journal
    assert len(observation['records']) == 2
    first, second = observation['records']
    assert first['original_parent_key']['first_full_id'] == 38718
    assert first['original_parent_key']['second_full_id'] == 38822
    assert first['original_parent_key']['parent_scope_id'] == journal['events'][0]['before_event']['sequence']
    assert first['original_parent_key']['parent_scope_id'] != first['journal_sequence']
    checks.append('actual-owned-wire-native-orientation-and-shared13-clock-preserved')
    assert first['copied_original_compare_causal'] is True
    assert first['sample_comparison']['threshold_at_sample_signed64'] == 3000000
    assert first['sample_comparison']['returned_sample_signed64'] == 1000000
    assert first['provider_first_qword']['first_qword_raw'] == 3000000
    assert first['native_parent_accepted'] is True
    assert second['native_parent_accepted'] is False
    assert second['copied_original_compare_causal'] is None
    assert second['provider_first_qword']['first_qword_raw'] is None
    checks.append('source-bound-comparison-independent-from-stale-postwrite-AL0')
    assert observation['status'] == 'unknown_current_observation'
    assert observation['journal_guards']['observer_installed'] is False
    assert observation['journal_guards']['current_session_guard'] is False
    assert observation['incoming_caller_source_binding']['status'] == 'unavailable'
    assert observation['incoming_caller_source_binding']['reason'] == 'owned-journal-guard-unavailable'
    assert observation['incoming_caller_source_binding']['records'] == []
    assert all(row['fixture_origin'] is True and row['original_compare_causal'] is None
               and row['original_compare_reason'] == 'current_journal_guard_unavailable'
               and row['accepted_causal'] is None and row['current_natural_observation_available'] is False
               for row in observation['records'])
    assert observation['monthly_or_stage_role'] == 'unknown'
    assert observation['incoming_caller_literal_call_status'] == 'unknown'
    assert observation['current_pair_actual_stack50'] is None
    assert observation['historical_reconstruction_available'] is False
    assert observation['conditional_software_provider_plane'] == 'separate'
    assert observation['pregnancy_or_birth_status'] == 'unknown'
    checks.append('false-liveguards-caller-source-monthly-stack50-history-and-consumed-math-stay-unknown')

    no_provider = deepcopy(journal)
    no_provider['events'][0]['provider'] = None
    p = project(no_provider)['records'][0]
    assert p['copied_original_compare_causal'] is True and p['provider_first_qword']['status'] == 'unknown'
    no_bookends = deepcopy(journal)
    for when in ('source_before', 'source_after'):
        for key in ('scalar_5c69ec8_raw', 'lower_5c69f00_raw', 'upper_5c69f10_raw'):
            no_bookends['events'][0][when][key] = None
    no_bookends['events'][0]['sample_state_before_2dword'] = None
    p = project(no_bookends)['records'][0]
    assert p['copied_original_compare_causal'] is True and p['accepted_causal'] is None
    checks.append('provider-and-parent-bookend-readiness-do-not-supply-or-block-original-comparison')

    no_threshold = deepcopy(journal)
    child = no_threshold['events'][0]['sample']['events'][0]
    child.update(threshold_at_sample_signed64=None, threshold_capture_ready=False,
                 comparison_at_sample_passed=None, capture_failure_flags=64)
    p = project(no_threshold)['records'][0]
    assert p['copied_original_compare_causal'] is None
    assert p['sample_comparison']['returned_sample_signed64'] == 1000000
    no_sample = deepcopy(journal)
    no_sample['events'][0]['sample'] = None
    p = project(no_sample)['records'][0]
    assert p['copied_original_compare_causal'] is None and p['provider_first_qword']['first_qword_raw'] == 3000000
    checks.append('missing-sample-or-captured-RBX-remains-independently-unknown')

    wrong_parent = deepcopy(journal)
    wrong_parent['events'][0]['sample']['events'][0]['parent']['parent_scope_id'] += 1
    assert project(wrong_parent)['records'][0]['copied_original_compare_causal'] is None
    changed_extended = deepcopy(journal)
    changed_extended['events'][0]['first_after']['extended_pointer'] += 8
    assert project(changed_extended)['records'][0]['copied_original_compare_causal'] is None
    wrong_write = deepcopy(journal)
    wrong_write['events'][0]['first_after']['pending_3f0_raw'] = 0
    wrong_write['events'][0]['first_post_pending_matches_write_pattern'] = False
    assert project(wrong_write)['records'][0]['copied_original_compare_causal'] is False
    checks.append('exact-parent-stable-extended-and-independent-BYTE-pointer-write-required')

    wrong_raw_pc = deepcopy(journal)
    wrong_raw_pc['events'][0]['caller_return_rva'] += 1
    rejects(wrong_raw_pc)
    wrong_pin = deepcopy(journal)
    wrong_pin['events'][0]['source_pin'] = '0' * 64
    rejects(wrong_pin)
    lost_low_rax = deepcopy(journal)
    lost_low_rax['events'][0]['original_rax_bits'] = '0'
    rejects(lost_low_rax)
    reconstructed = deepcopy(journal)
    reconstructed['events'][0]['source_before']['actual_original_consumed_values'] = True
    rejects(reconstructed)
    string_sample = deepcopy(journal)
    string_sample['events'][0]['sample']['events'][0]['returned_rax_signed64'] = '1000000'
    rejects(string_sample)
    try:
        normalize_conception_natural_observations_12004(
            journal, expected_first_character_id=38822 | 0x02000000, expected_second_character_id=38718)
    except ValueError:
        pass
    else:
        raise AssertionError('full generation was stripped from household join')
    checks.append('strict-fullpin-full-generation-rawRA-RAX-and-original-consumed-labels')

    returned_other = deepcopy(journal)
    provider = returned_other['events'][0]['provider']
    provider['native_return_bits'] = provider['output_pointer'] + 8
    provider['native_return_matches_output'] = False
    p = project(returned_other)['records'][0]
    assert p['provider_first_qword']['first_qword_raw'] == 3000000
    assert p['copied_original_compare_causal'] is True
    assert project(None)['status'] == 'unavailable'
    checks.append('provider-return-pointer-diagnostic-and-null-journal-separate')

    receipt = {
        'schema': 'xar.natural-conception-new-wire-compound-12004.v1', 'result': 'GREEN',
        'completed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'actual_input': {'path': str(args.journal), 'bytes': len(raw), 'sha256': args.journal_sha256},
        'checks': checks, 'check_count': len(checks), 'source_binding_metadata_reads': 0,
        'native_fixture_invocations': 0, 'old_fixture_replays': 0, 'live_verified': False,
        'current_natural_observation': 'unknown', 'accepted_consumed_arithmetic': 'unknown',
    }
    (args.output_dir / 'FOCUSED-VALIDATION.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    (args.output_dir / 'PROJECTED-ACTUAL-JOURNAL.json').write_text(json.dumps(observation, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'result': 'GREEN', 'check_count': len(checks), 'checks': checks}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
