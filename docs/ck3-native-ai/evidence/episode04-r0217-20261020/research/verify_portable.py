"""Replay the exact small R0217 direct-v2 input projection without large raw IO."""
from __future__ import annotations
import argparse,datetime,hashlib,json,pathlib,subprocess,sys

def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=pathlib.Path,required=True)
    p.add_argument('--projection',type=pathlib.Path,required=True)
    p.add_argument('--projection-sha256',required=True)
    p.add_argument('--output',type=pathlib.Path,required=True)
    a=p.parse_args();repo=a.repo.resolve()
    assert a.projection.stat().st_size<=262144
    raw=a.projection.read_bytes();assert sha(raw)==a.projection_sha256
    value=json.loads(raw)
    assert value['schema']=='xar.e04.R0217-direct-v2-portable-projection.v1'and value['projection_not_complete_original']is True
    for ref in value['direct_source_pins']:
        path=(repo/ref['path']).resolve();assert path.is_relative_to(repo)
        source=path.read_bytes();assert len(source)==ref['bytes']and sha(source)==ref['sha256']
    sys.path.insert(0,str(repo/'ck3_autonomous_player/src'))
    from xar_autoplayer.bridge.army_county_primary_direct_owner_12004 import evaluate_county_primary_direct_owner_evidence_12004
    f=value['baseline_writer_fences']
    result=evaluate_county_primary_direct_owner_evidence_12004(value['row'],executable_sha256=value['executable_sha256'],after_sequence=f['latest_sequence'],before_unattributed_capture_failures=f['unattributed_capture_failures'])
    actual=sha(canonical(result));assert actual==value['expected_consumer_result_canonical_sha256']
    machine=subprocess.run([sys.executable,str(repo/'tools/ck3_live_run_id.py'),'machine'],stdout=subprocess.PIPE,text=True,check=True).stdout.strip()
    record={'schema':'xar.e04.R0217-direct-v2-portable-replay.v1','producer_machine_id':value['machine_id'],'review_machine_id':machine,'reviewed_at_utc':datetime.datetime.now(datetime.UTC).isoformat(),
        'projection_pin':{'path':str(a.projection),'bytes':len(raw),'sha256':sha(raw)},'consumer_result_canonical_sha256':actual,
        'matches_original_scene_consumer':True,'qualified_positive_invocations':len(result['positive_invocations']),'other_qualified_invocations':len(result['other_qualified_invocations']),
        'excluded_invocations':len(result['excluded_invocations']),'individual_debit_sum':sum(x['actual_physical_soldier_debit']for x in result['positive_invocations']),
        'global_window_continuous':result['global_window_continuous'],'whole_county_debit':None,'whole_county_card_closed':False,
        'large_original_or_EXE_read':False,'SDK_game_GUI_build_action':False,'new_runtime_qualification_granted':False,'original_source_truth_not_independently_reestablished':True}
    with a.output.open('x',encoding='utf-8')as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(record,ensure_ascii=False))

if __name__=='__main__':main()
