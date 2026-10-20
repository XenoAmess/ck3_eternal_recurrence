from __future__ import annotations
import hashlib, json, pathlib, subprocess, sys
from datetime import datetime, timezone

REPO=pathlib.Path('D:/workspace/ck3_eternal_recurrence')
OUT=pathlib.Path(__file__).resolve().parent
MACHINE='desktop-3fevhd2-1c74096080'
PROMO=pathlib.Path('C:/ck3-e04-resume-20261015-a01/r215-mar31-normal-source-a01/R214-MAR31-NORMAL-S0-PROMOTION.actual-a01.json')
R214=pathlib.Path('D:/workspace/ck3_native_war_ai_promo_work/common-runtime-a36/runs/desktop-3fevhd2-1c74096080--vanilla--R0209')
R215=R214.parent/'desktop-3fevhd2-1c74096080--vanilla--R0210'
pins=[]

def pin_read(path,expected=None,maximum=350000):
    p=pathlib.Path(path)
    s=p.stat()
    if s.st_size>maximum:raise ValueError('small-file bound exceeded: '+str(p))
    b=p.read_bytes()
    result={'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'mtime_ns':s.st_mtime_ns}
    if expected:
        result['expected_bytes_match']=len(b)==expected['bytes']
        result['expected_sha256_match']=result['sha256']==expected['sha256']
        if not result['expected_bytes_match'] or not result['expected_sha256_match']:raise ValueError('pin differs: '+str(p))
    pins.append(result)
    return json.loads(b),result

def checked(ref):return pin_read(ref['path'],ref)
def stat_only(path):
    p=pathlib.Path(path)
    try:
        s=p.stat()
        return {'path':str(p),'exists':True,'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'st_dev':s.st_dev,'st_ino':s.st_ino,'payload_read':False,'current_content_sha256':None}
    except FileNotFoundError:return {'path':str(p),'exists':False,'payload_read':False,'current_content_sha256':None}
def facts(v,keys,path=''):
    out={}
    if isinstance(v,dict):
        for k,x in v.items():
            q=path+'/'+k
            if k in keys and not isinstance(x,(dict,list)):out[q]=x
            elif isinstance(x,(dict,list)):out.update(facts(x,keys,q))
    elif isinstance(v,list):
        for i,x in enumerate(v):out.update(facts(x,keys,path+'/'+str(i)))
    return out
def army_rows(v):
    out=[]
    if isinstance(v,dict):
        if v.get('army_id')==0 and 'current_province_id' in v:out.append(v)
        for x in v.values():
            if isinstance(x,(dict,list)):out.extend(army_rows(x))
    elif isinstance(v,list):
        for x in v:out.extend(army_rows(x))
    return out
def git(args):
    r=subprocess.run(['git',*args],cwd=REPO,capture_output=True,text=True,encoding='utf-8')
    if r.returncode:raise ValueError(r.stderr)
    return r.stdout.strip()

p,pp=pin_read(PROMO)
assert p['machine_id']==MACHINE and p['normal_source_provenance_qualified'] is True
ready,rpin=pin_read(R215/'ready-context.json')
assert ready['case_inputs']['normal_checkpoint_receipt']['sha256']==pp['sha256']
prepared,prep_pin=checked(ready['prepared_case'])
profile,profile_pin=checked(ready['case_inputs']['normal_checkpoint_build_receipt'])
save,save_pin=checked(p['actual_save']['reference'])
after,after_pin=checked(p['independent_after']['reference'])
original_save=save['rows'][0]['result']['checkpoint']
af=after['rows'][0]['after_snapshot']
closure={}
for k in ('normal_close','host_original_wait','keeper'):
    v,ref=checked(p['closure'][k]);closure[k]={'pin':ref,'machine_id_in_raw':v.get('machine_id','unknown'),'facts':facts(v,{'normal_close_qualified','cleanup_ok','native_exit_code','host_exit_code','exit_code','returncode','signaled','managed_thread_finished','screen_released','last_sequence','run_id','pid','create_time'})}
cas,cas_pin=checked(p['closure']['actual_CAS_journal_event']['exact_line_preserved'])
closure['CAS6737']={'pin':cas_pin,'event':cas}
os_exit,os_pin=pin_read(R214/'case-output/actual-retained-handle-os-exit.json')
closure['retained_os_exit']={'pin':os_pin,'facts':os_exit}
config=[]
for name,ref in ready['case_inputs']['plain_configuration'].items():
    path=pathlib.Path(ref['path']);b=path.read_bytes()
    actual={'path':str(path),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
    actual['expected_match']=all(actual[k]==ref[k] for k in ('bytes','sha256'))
    config.append({'profile_relative_path':name,**actual});pins.append(actual)

B=REPO/'ck3_autonomous_player/native_bridge/build-e04-a37'
q,qp=pin_read(B/'ROOT-A37-PRODUCTION-QUALIFICATION.actual-a02.json')
cold,cp=checked(q['refill_cold_result'])
build,bp=pin_read(B/'REFILL-WORKER-LIVE-a01/native-msvc-result.json')
sr,srp=pin_read(build['defender_exclusions']['receipt'],{'bytes':262553,'sha256':build['defender_exclusions']['receipt_sha256']})
manifest,mp=pin_read(pathlib.Path(build['source_dir']).parents[3]/'SOURCE-MANIFEST.actual.json')
exe=B/'REFILL-WORKER-LIVE-a01/refill_add_hwprobe_12004.exe'
es=stat_only(exe)
es['historical_sha256']='f27826adcf3b0321614b3f8ed9dcd9bceb69da1a84f45233029245ea925ab9bf'
es['matching_SYSTEM_file_records']=[x for x in sr['files'] if pathlib.Path(x['path']).resolve()==exe.resolve()]
current_manifest,cm=pin_read('C:/ck3-e04-resume-20261020-a01/common-runtime-a39-a03/manifest.json')
cap,cap_pin=pin_read(OUT.parent/'capacity/R06-FINITE-RESERVE-AND-SHARED-ADMISSION.actual-a01.json',{'bytes':4981,'sha256':'8e7a1cac2ee78bf22f30b988f4282228a825b7a0cc6a73ca075fde26a9cdffd4'})

source_paths=[
 'tools/ck3_mod_acceptance_cases/r10_prepare.json',
 'tools/ck3_mod_acceptance_cases/r10_prepare_adapter.py',
 'tools/ck3_mod_acceptance_cases/r04_county_entry.py',
 'tools/ck3_mod_acceptance_cases/r04_county_entry_window.py',
 'tools/ck3_mod_acceptance_full_army.py',
 'ck3_autonomous_player/native_bridge/research/refill_add_hwprobe_12004.cpp',
 'ck3_autonomous_player/native_bridge/research/refill_add_live_12004/debug_thread_ownership_12004.hpp',
 'ck3_autonomous_player/native_bridge/research/refill_add_live_12004/prepare_live_refill_add.py',
 'ck3_autonomous_player/native_bridge/research/refill_add_live_12004/launch_live_refill_add.py',
 'ck3_autonomous_player/native_bridge/research/refill_add_live_12004/consume_live_refill_add.py',
 'ck3_autonomous_player/native_bridge/research/refill_add_live_12004/refill_core_carrier_reader_12004.hpp',
 'ck3_autonomous_player/native_bridge/include/xar_bridge/refill_core_carrier_12004.hpp',
 'ck3_autonomous_player/src/xar_autoplayer/bridge/army_target_instruction_core_proof_12004.py',
 'ck3_autonomous_player/src/xar_autoplayer/bridge/army_instruction_local_refill_add_12004.py',
 'ck3_autonomous_player/src/xar_autoplayer/bridge/r05_supply_observation_case.py',
]
sources=[]
for rel in source_paths:
    path=REPO/rel;b=path.read_bytes()
    blob=git(['rev-parse','HEAD:'+rel])
    sources.append({'repo_relative_path':rel,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'git_blob_HEAD':blob,'actual_bytes_match_HEAD_blob':hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==blob})
compare_paths=source_paths[5:7]+source_paths[10:12]
diff=git(['diff','--name-only','bc4604bed4eb8558b3f4e0e554a642aa69a4ba2f','43fd32670897f657da681cf0a94d162e3135a89c','--',*compare_paths])
frozen_cpp=pathlib.Path(build['source_dir']).parent/'refill_add_hwprobe_12004.cpp'
current_cpp=REPO/source_paths[5]
frozen_equal=frozen_cpp.read_bytes()==current_cpp.read_bytes()

audit={
 'schema':'xar.e04.r06.minimal_plan_source_audit.v1','machine_id':MACHINE,'observed_at_utc':datetime.now(timezone.utc).isoformat(),
 'HEAD':git(['rev-parse','HEAD']),'native_tree':git(['rev-parse','HEAD:ck3_autonomous_player/native_bridge']),'git_status':git(['status','--short']),
 'selected_source_only':{'source_machine_id':p['machine_id'],'source_run_id':p['source_run_id'],'source_head':p['source_head'],'promotion_pin':pp,'saved_campaign':p['source'],'current_save_stat_only':stat_only(p['source']['path']),'actual_native_checkpoint':original_save,'actual_after':{'date_raw':af['date_raw'],'paused':af['paused'],'map_ready':af['map_ready'],'episode_projection':af.get('episode_projection'),'episode_run_id':af.get('episode_run_id'),'actor':af['played_character'],'army0':army_rows(af),'game_hello':af.get('diagnostics',{}).get('hello')},'R215_reuse_ready_pin':rpin,'R215_prepared_case_pin':prep_pin,'R215_saved_campaign':prepared.get('saved_campaign'),'normalclose_originals':closure,'plain_configuration_current_pins':config,'profile_preparation_pin':profile_pin,'original_driver_state_save_binding_mismatch_preserved':p['driver_state_replace_receipt'],'not_used_to_infer_normal_source':True},
 'existing_producer_only':{'qualification_pin':qp,'machine_id':q['machine_id'],'production_bytes_qualified':q['production_bytes_qualified'],'focused_cold_qualified':q['focused_cold_qualified'],'cold_pin':cp,'cold_status':cold.get('status'),'cold_cases':[{k:v for k,v in x.items() if k in ('case','name','status')} for x in cold.get('cases',[])],'build_pin':bp,'source_dir':build['source_dir'],'frozen_source_manifest_pin':mp,'SYSTEM_receipt_pin':srp,'SYSTEM_status':sr.get('status'),'SYSTEM_admin_token':sr.get('admin_token'),'SYSTEM_sid':sr.get('system_token_sid'),'observer_exe_stat_only':es,'current_a39_manifest_pin':cm,'current_a39_game':current_manifest['game'],'current_a39_qualification':current_manifest['qualification'],'a37_to_a39_four_source_diff_empty':not diff,'compared_paths':compare_paths,'actual_frozen_probe_cpp_equals_current_bytes':frozen_equal,'new_build_required_for_N_le_256_by_this_analysis':False,'runtime_loaded_module_future_observation_required':True,'live_READY_or_ADD_granted':False},
 'current_sources':sources,'small_original_pins':pins,
 'capacity':{'parent_admission_pin':cap_pin,'scope':'shared128MiB C metadata only; own plan<=256KiB; no scene/native execution','hard_deadline_utc':'2026-10-20T08:00:00Z'},
 'limits':{'SDK_calls':0,'game_launches':0,'screen_calls':0,'process_census_calls':0,'DR_calls':0,'EXE_payload_reads':0,'large_save_payload_reads':0,'D_writes':0,'repo_writes':0,'new_business_credit':False}
}
audit['selected_source_only']['R215_saved_campaign']=prepared.get('startup',{}).get('saved_campaign')
audit['existing_producer_only']['current_HEAD_native_tree_differs_from_existing_a39']=audit['native_tree']!=current_manifest['qualification']['native_tree']
audit['existing_producer_only']['complete_current_native_coherent_qualification_granted']=False
(OUT/'SOURCE-AUDIT.actual.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'audit':str(OUT/'SOURCE-AUDIT.actual.json'),'bytes':(OUT/'SOURCE-AUDIT.actual.json').stat().st_size,'save_stat':audit['selected_source_only']['current_save_stat_only'],'normalclose':closure,'producer':audit['existing_producer_only'],'all_configuration_pins_match':all(x['expected_match'] for x in config)},ensure_ascii=False,indent=2))
