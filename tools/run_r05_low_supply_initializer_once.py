"""Root-owned one-shot fixture initializer through the existing request relay.

No SDK session, input API, console, tick, updater or soldier writer is created.
The owner must hold the current SDK lease. Failed/unknown Confirm never retries.
"""
from pathlib import Path
import argparse,datetime as dt,hashlib,importlib.util,json,math,os,re,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]

def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def write_receipt(path,row):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(row,stream,ensure_ascii=False,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())

def initialize_once(helper, contract, *, binding, prepared, package, army_id, carmy_id,
                    prefix, claims_dir, current_machine):
    """Only relay I/O is replaceable for offline contract checks."""
    m=contract
    m.require(binding['machine_id']==prepared['machine_id']==current_machine,'current machine mismatch')
    m.require(prepared.get('r05_low_supply_fixture') is not None,'explicit mounted fixture preparation required')
    m.validate_mount(prepared['profile_dir'],prepared['r05_low_supply_fixture'])
    m.require(package==m.validate_fixture(prepared['r05_low_supply_fixture']['manifest']['path']),
        'initializer parameters differ from the actual mounted controlled package')
    m.require(prepared['game']['sha256'].lower()==m.EXE_SHA,'prepared exact build differs')
    m.require(Path(helper.RUN).resolve()==Path(binding['run_dir']).resolve(),'helper current runtime mismatch')
    m.require(helper.CONTEXT['machine_id']==current_machine,'helper machine mismatch')
    if type(binding.get('create_filetime')) is int and binding['create_filetime']>0:
        creation={'windows_filetime':binding['create_filetime']}
    else:
        value=binding.get('process_creation_unix_seconds')
        m.require(type(value) in (int,float) and math.isfinite(value) and value>0,'fresh held process creation binding required')
        creation={'unix_seconds':value}
    actor_id=binding['actor_id'];province_id=package['config']['province_id'];key=package['config']['decision_key']
    identity={'machine_id':current_machine,'pid':binding['pid'],'process_creation':creation,
        'episode':binding['episode'],'army_id':army_id,'carmy_id':carmy_id}
    claim_key=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()
    claims_dir=Path(claims_dir);claim=claims_dir/(claim_key+'.claim.json');outcome=claims_dir/(claim_key+'.outcome.json')
    m.require(not claim.exists() and not outcome.exists(),'initializer already claimed for current process/episode/Army; never replay')
    capabilities=helper.request(prefix+'-capabilities','ck3_get_capabilities',{})['body']
    m.require_capabilities(capabilities)
    def sample(label):
        frame=helper.snapshot(prefix+'-'+label+'-snapshot')
        m.require(frame.get('episode_run_id')==binding['episode'],'current episode differs')
        m.require(frame.get('diagnostics',{}).get('bridge_pid')==binding['pid'],'current PID differs')
        m.require(frame.get('diagnostics',{}).get('connection_generation')==binding['generation'],'current generation differs')
        strengths=helper.request(prefix+'-'+label+'-strengths','ck3_query_army_strengths',
            {'army_ids':[army_id],'expected_revision':frame['revision'],'profile':'observed_history_full_v1'})['body']
        witness=m.target_witness(frame,strengths,actor_id=actor_id,army_id=army_id,carmy_id=carmy_id,province_id=province_id)
        return frame,witness
    f,initial=sample('initial')
    m.require(0 < initial['current_supply_raw'] <= initial['current_supply_capacity_raw'] <= 30000000,
              'initializer requires actual0<stock<=capacity<=300; no extrapolated clamp')
    helper.request(prefix+'-open','ck3_open_ingame_decisions_v1',{'expected_revision':f['revision']})
    opened=helper.snapshot(prefix+'-opened-snapshot')
    helper.request(prefix+'-select','ck3_select_ingame_decision_item_v1',
        {'decision_key':key,'expected_revision':opened['revision']})
    f,before=sample('before-confirm')
    for field in ('actor_id','army_id','carmy_id','province_id','pid','generation','current_supply_raw',
                  'ordered_regiment_ids','data_aliases','physical_slots','raw138_by_persistent'):
        m.require(initial[field]==before[field],'target changed during decision navigation: '+field)
    m.require(initial['machine_independent_frame']['date_raw']==f['date_raw'],'date changed during navigation')
    claims_dir.mkdir(parents=True,exist_ok=True)
    row={'schema':'xar.r05-initializer-once-claim.v1',**identity,'at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'fixture_mode':m.MODE,'decision_key':key,'config':package['config'],'before':before,
        'status':'claimed_result_unknown_no_retry','request_id':prefix+'-confirm','replay_permitted':False}
    write_receipt(claim,row)
    try:
        ack=helper.request(prefix+'-confirm','ck3_confirm_ingame_decision_outcome_v1',
            {'decision_key':key,'expected_outcome':'decision_closed','expected_revision':f['revision']})
        after_frame,after=sample('after')
        assessment=m.assess_initialization(before,after)
        result={'schema':'xar.r05-initializer-actual-outcome.v1',**identity,
            'at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'claim':m.pin(claim),
            'confirm_ack':ack['body'],'independent_after':after,'assessment':assessment,
            'SDK_effect_submissions':1,'natural_days_advanced':0,'replay_permitted':False}
        write_receipt(outcome,result)
        return result
    except BaseException as exc:
        write_receipt(claims_dir/(claim_key+'.failure.json'),{'machine_id':current_machine,
            'at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'claim':m.pin(claim),
            'error':type(exc).__name__+': '+str(exc),'result':'unknown_or_not_qualified_no_retry',
            'replay_permitted':False,'instruction':'Inspect same Confirm request/response and independently query actual state; do not apply initializer again'})
        raise

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo-root',type=Path,default=ROOT)
    p.add_argument('--binding',type=Path,required=True)
    p.add_argument('--prepared',type=Path,required=True)
    p.add_argument('--army-id',type=int,required=True)
    p.add_argument('--carmy-id',type=int,required=True)
    p.add_argument('--prefix',required=True)
    p.add_argument('--claims-dir',type=Path,required=True)
    a=p.parse_args();repo=a.repo_root.resolve()
    sys.path[:0]=[str(repo/'ck3_autonomous_player/src'),str(repo/'tools')]
    from ck3_live_run_id import current_machine_id
    module=load_module('xar_autoplayer.bridge.r05_low_supply_fixture',ROOT/'ck3_autonomous_player/src/xar_autoplayer/bridge/r05_low_supply_fixture.py')
    module.require(re.fullmatch(r'[a-z0-9][a-z0-9_-]{2,95}',a.prefix) is not None,'invalid fresh prefix')
    module.require(not a.claims_dir.resolve().is_relative_to(repo),'claims must stay outside source repository')
    binding=json.loads(a.binding.read_bytes());prepared=json.loads(a.prepared.read_bytes())
    hp=Path(binding['request_helper']['path']);module.require(module.pin(hp)==binding['request_helper'],'bound helper bytes changed')
    helper=load_module('r05_current_root_request_helper',hp)
    package=module.validate_fixture(prepared['r05_low_supply_fixture']['manifest']['path'])
    result=initialize_once(helper,module,binding=binding,prepared=prepared,package=package,
        army_id=a.army_id,carmy_id=a.carmy_id,prefix=a.prefix,claims_dir=a.claims_dir,current_machine=current_machine_id())
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
