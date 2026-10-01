"""Join two already-admitted same-run original-evidence projections.

Create-only output. Reads no game state. The stopped READY verifiers must first
validate raw receipts, source/connection identity, saves and monitor lifecycle.
This adds a03 current-original-commit ancestry without changing those sources.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import pathlib
import shutil
import sys

ADDON=pathlib.Path(__file__).with_name('signature_commit_correlation_a02.py')


def identity(p):
    p=pathlib.Path(p)
    with p.open('rb') as f:
        sha=hashlib.file_digest(f,'sha256').hexdigest().upper()
    return {'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':sha}


def read(p):
    return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))


def verify(args):
    out=args.output_dir.resolve()
    out.mkdir(parents=True,exist_ok=False)
    checks=[]
    report={'schema_version':1,'kind':'ADDITIVE_SAME_RUN_ORIGINAL_COMMIT_CORRELATION',
            'created_at_utc':datetime.datetime.now(datetime.UTC).isoformat(),'status':'UNKNOWN',
            'checks':checks,'frozen_READY_source_changed':False,'game_calls':0,'desktop_inputs':0,
            'master_intake':False,'sole_cause_proven':False,'whole_game_mutable_bundle_complete':False}
    def gate(name,passed):
        checks.append({'name':name,'pass':bool(passed)})
        if not passed:
            raise ValueError(name)
    def checked(declared):
        actual=identity(declared['path'])
        gate('original declared bytes '+declared['path'],actual['bytes']==declared['bytes'] and actual['sha256']==declared['sha256'].upper())
        return pathlib.Path(declared['path'])
    def freeze(p,label):
        dest=out/label
        with pathlib.Path(p).open('rb') as source,dest.open('xb') as target:
            shutil.copyfileobj(source,target)
        left,right=identity(p),identity(dest)
        gate('exact copy '+label,left['bytes']==right['bytes'] and left['sha256']==right['sha256'])
        return {'original':left,'exact_copy':right}
    try:
        report['sources']=[freeze(__file__,'additive-run-verifier-exact.py'),freeze(ADDON,'additive-pure-exact.py'),
                           freeze(args.monitor_verification,'monitor-verification-exact.json'),
                           freeze(args.causal_verification,'causal-verification-exact.json')]
        mon_report,causal=read(args.monitor_verification),read(args.causal_verification)
        gate('original monitor prerequisite passed',mon_report['status']=='PASS_SAME_RUN_ORIGINAL_MONITOR_OPERATIONS_AND_SAVED_ENDPOINT_PROJECTION')
        gate('original save/trace prerequisite passed',causal['status']=='PASS_SAME_RUN_SELECTED_SAVED_BLOCKS_AND_ORIGINAL_TRACE' and causal['input_format']=='explicit_binding_identity_saved_pair_v1')
        gate('all prerequisite machine gates passed',all(r['pass'] is True for r in mon_report['checks']+causal['checks']))
        gate('global and sole-cause boundaries retained',mon_report['whole_game_mutable_bundle_complete'] is False and mon_report['sole_cause_proven'] is False and causal['global_bundle_complete'] is False)
        copies=mon_report['exact_sources']
        for entry in copies:
            checked(entry['original']);checked(entry['exact_copy'])
        referenced=[entry for entry in copies if pathlib.Path(entry['exact_copy']['path']).name=='causal-projection-exact.json']
        gate('unique original causal projection bound by monitor',len(referenced)==1 and referenced[0]['original']==identity(args.causal_verification))
        finish=[entry for entry in copies if pathlib.Path(entry['exact_copy']['path']).name=='finish-wrapper-exact.json']
        gate('unique original drained monitor wrapper',len(finish)==1)
        wrapper=read(finish[0]['exact_copy']['path'])
        config_identity=causal['source_binding']['original']
        gate('same original frozen source binding',wrapper['source_binding']==config_identity)
        config=read(checked(config_identity))
        journal=causal['original_scoped_transition_chain']
        mon=wrapper['scoped_variable_monitor']
        chars=[config['victim_id'],config['killer_id']]
        gate('two full character IDs and both independent tokens match current binding',
             mon['character_ids']==journal['character_ids']==chars and
             mon['monitor_sequence_token']==config['monitor_sequence_token'] and
             journal['managed_daily_sequence_token']==config['managed_daily_sequence_token'] and
             mon['monitor_sequence_token']!=journal['managed_daily_sequence_token'])
        spec=importlib.util.spec_from_file_location('external_additive',ADDON)
        addon=importlib.util.module_from_spec(spec);spec.loader.exec_module(addon)
        result=addon.correlate_signature_commits(mon,journal,victim=chars[0],related=chars[1])
        report['same_run_episode']=causal['episode_run_id']
        report['same_native_connection']=causal['native_connection']
        report['source_binding']=config_identity
        report['projection']=result
        report['raw_monitor_source']=finish[0]
        report['raw_journal_source']=causal['trace_original']
        report['status']='PASS_ADMITTED_SAME_RUN_ORIGINAL_CALL_PROJECTION'
        report['semantic_status']='closed' if result['specific_victim_trigger_closed'] else 'pending'
        report['limits']=['PASS is input/operation validation, not six-gap or 13-domain completion.',
                          'This projection attributes individual writes to actual-current commit ancestry, not inferred notification receiver.',
                          'The complete selector/death request/enqueue/commit/day and case uniqueness verdict remain separate.',
                          'No old run values, UI scope RNG, or named dead_character contents are inserted.']
    except Exception as error:
        report['status']='RED_INPUT_OR_FACT_GATE'
        report['error']=type(error).__name__+': '+str(error)
    dest=out/'signature-commit-correlation-run-verification.json'
    with dest.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'status':report['status'],'semantic_status':report.get('semantic_status'),
                      'error':report.get('error'),'receipt':identity(dest)}))
    return 0 if report['status'].startswith('PASS') else 2


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--monitor-verification',type=pathlib.Path,required=True)
    parser.add_argument('--causal-verification',type=pathlib.Path,required=True)
    parser.add_argument('--output-dir',type=pathlib.Path,required=True)
    return verify(parser.parse_args())


if __name__=='__main__':
    sys.exit(main())
