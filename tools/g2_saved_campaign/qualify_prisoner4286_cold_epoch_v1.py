"""Closed-input qualification and create-only source preparation, zero RPC."""
import ast
import copy
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')
REVIEW=Path('Z:/ck3_mod_rewrite/_runtime/c11-prisoner4286-review85')
MACHINE='xenoamess-full-tower-eb9d2c1186'
sys.path[:0]=[str(HERE),str(ROOT),str(ROOT.parent.parent/'sdk-v20261019-candidate/src10')]
import prisoner4286_cold_epoch_credit_v1 as helper
sys.modules['root_c11_prisoner_cold_epoch_credit']=helper


def require(ok,why):
    if not ok:raise ValueError('closed4286 qualifier: '+why)


def pin(path):
    p=Path(path);raw=p.read_bytes()
    return {'path':str(p.resolve()),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def selected(text):
    out=[]
    for n in ast.parse(text).body:
        if isinstance(n,ast.FunctionDef) and n.name.startswith('classify_'):
            out.append(n)
        elif isinstance(n,ast.Assign) and all(isinstance(t,ast.Name) and t.id.isupper() for t in n.targets):
            try:ast.literal_eval(n.value)
            except (ValueError,TypeError):continue
            out.append(n)
    return ast.Module(body=out,type_ignores=[])


def main():
    packet=helper.fixed(helper.PACK/'FROZEN.json',helper.PACK_SHA)
    refs={r['original_source']:r for r in packet['source_refs'] if 'path' in r}
    body=helper.checked(refs[str(ROOT/'p37-responses/4286-1-result.json')])['result']['structured_content']
    state=helper.checked(refs[str(ROOT/'p37-queue/ROOT-GOVERNANCE-RESULT-STATE.json')])['state']
    bound=helper.fixed(ROOT/'p37-queue/ROOT-C11-NORMAL-COLD-BOUND.json',helper.BOUND_SHA)
    queue=(ROOT/'root_p37c11_sdk_queue.py').read_bytes()
    baseline=(ROOT/'root_p37c4_result_classifier.py').read_bytes()
    require(hashlib.sha256(baseline).hexdigest()=='d47350282ad422978bac99653aa5757a5d72d6af10fb690e615592a3ff825991','classifier baseline differs')
    wrapper='''\n\ndef classify_existing_typed_v1(body, *, state=None, initial_frame=None, game_pid=None):
    from root_c11_prisoner_cold_epoch_credit import classify
    return classify(body, state=state, initial_frame=initial_frame, game_pid=game_pid, namespace=globals())
'''
    candidate=baseline+wrapper.encode()
    require(len(candidate)<=262144,'candidate exceeds existing loader limit')
    compile(candidate,'root_p37c11_prisoner_epoch_classifier.py','exec')
    namespace={'json':json,'ast':ast,'Path':Path,'N':ROOT,'__file__':str(ROOT/'root_p37c11_prisoner_epoch_classifier.py')}
    exec(compile(selected(queue),'actualQueueTyped','exec'),namespace)
    before=(copy.deepcopy(body),copy.deepcopy(state))
    args={'state':state,'initial_frame':bound['opening_frame'],'game_pid':15512}
    red=None
    try:namespace['classify_existing_typed_v1'](body,**args)
    except ValueError as e:red=str(e)
    require(red and 'prisoner receipt original target/ACK/frame differs' in red,'original RED not reproduced')
    exec(compile(selected(candidate),'actualLoaderSelected','exec'),namespace)
    record,changed=namespace['classify_existing_typed_v1'](body,**args)
    require(record['existing_typed_material_verified'] is True and record['custody_causation_or_cost_credit_inferred'] is False
        and record['primitive_accepted'] is False and record['replay_allowed'] is False
        and changed['prisoner_release_pending'] is None and (body,state)==before,'actual receipt/preservation qualification failed')
    original,across=helper.functions(namespace)
    helper_before=helper.checked
    def foreign_identity(ref,limit=262144):
        value=helper_before(ref,limit)
        if Path(ref['path']).name=='FINAL-DRIVER-CLOSE.json':
            value=copy.deepcopy(value);value['old_Game']['creation_filetime']+=1
        return value
    helper.checked=foreign_identity
    try:
        try:namespace['classify_existing_typed_v1'](body,**args)
        except ValueError as e:require('old Game/canonical cold identity' in str(e),'wrong identity failed elsewhere')
        else:raise ValueError('wrong old identity accepted')
    finally:helper.checked=helper_before
    bad=copy.deepcopy(body);bad['result']['source_pending']['action_ack']['request_id']='prisoner-release-foreign'
    try:namespace['classify_existing_typed_v1'](bad,**args)
    except ValueError:pass
    else:raise ValueError('foreign ACK accepted')
    # The same-epoch path delegates to the byte-original function, without any
    # cold proof files or substituted input. Reuse the real receipt structurally.
    same=copy.deepcopy(body);same_state=copy.deepcopy(state)
    same_state['prisoner_release_pending']['pre_native_revision']=27
    same_state['prisoner_release_pending']['action_ack']['pre_native_revision']=27
    same['plan']['prisoner_release_pending']=copy.deepcopy(same_state['prisoner_release_pending'])
    same['result']['source_pending']=copy.deepcopy(same_state['prisoner_release_pending'])
    same_args={**args,'state':same_state}
    require(namespace['classify_existing_typed_v1'](same,**same_args)==original(same,**same_args),'same epoch delegation differs')
    admission=Path('D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01/C11-P0-CLASSIFIER-SOURCE-COMMITMENT01.json')
    a=json.loads(admission.read_bytes())
    require(a['machine_id']==MACHINE and a['status']=='ADMITTED_BOUNDED_REVIEW_AND_EXACT_RUNTIME_SOURCE_COPY'
        and Path(a['exact_source_review_root']).resolve()==REVIEW.resolve()
        and pin(admission)['sha256']=='18414a4c5c5763cfe785388fa8ecd376abeef832496d2f3f12de21a9304d3d7b',
        'actual finite source storage admission required')
    require(not REVIEW.exists(),'create-only review already exists')
    REVIEW.mkdir(parents=True)
    files={'root_p37c11_prisoner_epoch_classifier.py':candidate,
        'root_c11_prisoner_cold_epoch_credit.py':(HERE/'prisoner4286_cold_epoch_credit_v1.py').read_bytes()}
    for name,raw in files.items():
        with (REVIEW/name).open('xb') as f:f.write(raw)
    report={'schema':'xar.C11-prisoner4286-cold-classifier-qualification/v1','machine_id':MACHINE,
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),'status':'CLOSED_SOFTWARE_QUALIFIED_NOT_RUNTIME_ADOPTED',
        'sources':[pin(HERE/'prisoner4286_cold_epoch_credit_v1.py'),pin(__file__)],
        'candidate_files':[pin(REVIEW/n) for n in files], 'packet':pin(helper.PACK/'FROZEN.json'),
        'storage_admission':pin(admission),'original_RED':red,
        'results':{'actual4286':record,'wrong_old_identity_rejected':True,'wrong_ACK_rejected':True,
            'same_epoch_original_unchanged':True,'body_known_ACK_unchanged':True},
        'single_comparison_source':'inner["post_native_revision"] >= known["pre_native_revision"]',
        'new_release_or_RPCS':0,'live_runtime_writes':0}
    with (REVIEW/'QUALIFICATION.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps(pin(REVIEW/'QUALIFICATION.json')))
    print(json.dumps(report['candidate_files']))


if __name__=='__main__':main()
