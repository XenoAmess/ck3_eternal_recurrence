"""Consume the focused native fixture's actual serializer bytes, offline only."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--repo-root',type=Path,required=True)
    parser.add_argument('--native-jsonl',type=Path,required=True)
    args=parser.parse_args()
    sys.path.insert(0,str(args.repo_root/'ck3_autonomous_player/src'))
    from xar_autoplayer.bridge.military_reinforcement_12004_contract import (
        normalize_reinforcement_ack, observe_fixed_reinforcement, reinforcement_binding)
    fixture=args.repo_root/'ck3_autonomous_player/tests/unit/test_military_reinforcement_12004.py'
    spec=importlib.util.spec_from_file_location('reinforcement_fixture_data',fixture)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    rows=[json.loads(line) for line in args.native_jsonl.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    if len(rows)!=4:raise ValueError('expected four native fixture JSON lines')
    if rows[0]!={'case':'fixed_source_owner_and_visibility','passed':True}:raise ValueError('source-selection native case failed')
    if rows[3]!={'case':'unknown_dispatch_no_internal_retry','passed':True}:raise ValueError('native unknown-dispatch case failed')
    snapshot=module.snapshot();binding=reinforcement_binding(snapshot)
    before=observe_fixed_reinforcement(module.census(1),snapshot,snapshot)
    same=normalize_reinforcement_ack(rows[1],binding,True,before)
    changed=normalize_reinforcement_ack(rows[2],binding,False,before)
    if same['status']!='noaction_already_desired' or changed['status']!='acknowledged_verification_pending':
        raise ValueError('native decisions disagree with strict Python consumer')
    if same['postcondition_verified'] or changed['postcondition_verified']:
        raise ValueError('native ACK incorrectly verified business outcome')
    print(json.dumps({'status':'PASS','scope':'offline-native-serializer-to-production-consumer',
        'native_lines':4,'ack_rows_consumed':2,'game_execution_performed':False,
        'native_io_mocked':True,'live_toggle_or_ADD_qualified':False}))

if __name__=='__main__':main()
