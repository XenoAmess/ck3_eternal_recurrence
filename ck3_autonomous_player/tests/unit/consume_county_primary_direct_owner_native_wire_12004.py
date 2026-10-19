"""Consume future native synthetic cold wire; no live or R04 credit."""
from pathlib import Path
import argparse
import hashlib
import json
import sys

sys.dont_write_bytecode = True


def need(ok, why):
    if not ok:
        raise ValueError(why)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--wire', type=Path, required=True)
    p.add_argument('--wire-bytes', type=int, required=True)
    p.add_argument('--wire-sha256', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    need(not a.output.exists(), 'output must be create-only')
    need(0 < a.wire_bytes <= 1048576 and a.wire.stat().st_size == a.wire_bytes,
         'bounded wire size differs')
    raw = a.wire.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    need(len(raw) == a.wire_bytes and digest == a.wire_sha256, 'wire pin differs')
    wire = json.loads(raw)
    need(set(wire) == {'schema', 'live_qualification', 'cases'} and
         wire['schema'] == 'xar.county-primary-direct-owner-v2.cold.v1' and
         wire['live_qualification'] is False, 'not synthetic cold wire')
    names = [c.get('case') for c in wire['cases']]
    need(len(names) == len(set(names)) == 15, 'expected 15 distinct cold cases')
    sys.path.insert(0, str(a.repo/'ck3_autonomous_player/src'))
    from xar_autoplayer.bridge.army_actual_loss_writer_observations_contract import normalize_actual_loss_writer_observations_v1 as normalize
    from xar_autoplayer.bridge.army_county_primary_direct_owner_12004 import KEY, EXE, UNBOUND_KEY, evaluate_county_primary_direct_owner_evidence_12004 as consume
    from xar_autoplayer.bridge.army_county_primary_owner_12004 import evaluate_county_primary_owner_evidence_12004 as old_consume
    positive_names = {'ON_no_phaseTLS_direct_Army0_physical7',
                      'ON_postDate_direct_complete_v1_absent',
                      'nested_unknown_masks_outer_context'}
    need(positive_names <= set(names), 'complete cold cases missing')
    facts = []
    for c in wire['cases']:
        need(set(c) == {'case', 'synthetic_fixture_only', 'observations'} and
             c['synthetic_fixture_only'] is True, 'case provenance differs')
        ids = sorted({e['army_regiment_id'] for e in c['observations']['events']}) or [0x03000001]
        f = normalize(c['observations'], current_regiment_ids=ids)
        row = dict(status='available', army_id=0, native_carmy_id=0,
                   regiment_strengths=[dict(army_regiment_id=i) for i in ids],
                   actual_loss_writer_observations_v1=f)
        r = consume(row, executable_sha256=EXE, after_sequence=0,
                    before_unattributed_capture_failures=0)
        positives = r['positive_invocations']
        if c['case'] in positive_names:
            need(len(positives) == 1 and positives[0]['actual_physical_soldier_debit'] == 7,
                 'native direct fact failed production physical consumer')
        else:
            need(not positives, 'native negative acquired direct positive')
        need(r['county_total_debit'] is None and not r['complete_army_loss_history'],
             'individual fact acquired Army total')
        need(not old_consume(row, executable_sha256=EXE, after_sequence=0,
                            before_unattributed_capture_failures=0)['positive_invocations'],
             'v2 bypassed old returned-phase contract')
        if c['case'] == 'ON_no_phaseTLS_direct_Army0_physical7':
            need(not positives[0][KEY]['active_phase_observed'], 'missing phase invented')
        if c['case'] == 'ON_postDate_direct_complete_v1_absent':
            owner = positives[0][KEY]
            need(owner['active_phase_observed'] and owner['active_phase_entry_rva'] == 0x2A9A570,
                 'post-date phase relabeled')
        if c['case'].startswith('unreadable_'):
            need(f['latest_sequence'] == f['event_count'] == 0 and
                 f['unattributed_capture_failures'] == 1 and len(f[UNBOUND_KEY]) == 1,
                 'unbound diagnostic changed old global accounting')
        facts.append(dict(case=c['case'], direct_positive_count=len(positives),
                          global_window_continuous=r['global_window_continuous']))
    report = dict(schema='xar.county-primary-direct-owner-v2.native-wire-ingress.v1',
                  status='PASS_NATIVE_SYNTHETIC_WIRE_PRODUCTION_CONSUMERS',
                  wire=dict(path=str(a.wire), bytes=len(raw), sha256=digest), cases=facts,
                  live_or_R04_credit=False, SDK_calls=0,
                  native_process_started_by_this_consumer=False,
                  original_call_and_OFF_read_counts='asserted inside native fixture, not inferred by Python')
    with a.output.open('x', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
        f.write('\n')
    print(report['status'])


if __name__ == '__main__':
    main()
