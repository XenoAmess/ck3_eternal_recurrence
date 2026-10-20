"""Independent Source28 A13 native2560 cold preparation; Root alone applies."""
from __future__ import annotations
import ast, hashlib, json, sys, types
from pathlib import Path
from types import ModuleType
from prepare_c23_a10_union_v1 import ExactRef, JSONObject, Outputs
import prepare_source28_a12_union_v1 as base
from tools.g2_saved_campaign.file_stat_identity_v1 import SCHEMA, normalize_file_stat_identity_v1, parse_file_stat_identity_v1
OWN, MACHINE, O, T0 = base.OWN, base.MACHINE, base.O, base.T0
U12, U13, T5 = base.U12, base.U12.with_name("runtime-a13"), base.U12.with_name("runtime-a13")
P = O / "source28-a13-prep01"
prior, require = base.prior, base.require
BASE_PIN = (34648,"6aedb27de9990c1984c1e30e5da82910763e96a99890de79d6d5194c7f942b48")
PREPARED = O / "A12-PREPARED01.json"
PREPARED_PIN = (39403,"bd0d190984256b4252cdd8f02d392add1fe99b1dd09bd2045085df462de84465")
QUOTE = O / "source28-a12-prep01/A12-ROOT-QUOTE01.json"
QUOTE_PIN = (173639,"8d49ac6be1acbc402b028e251cb40c3791884be88b2ff32809b55f2d03602f94")
PLAN12 = O / "source28-a12-prep01/A12-ROOT-PLAN02.json"
PLAN12_PIN = (6241,"69510fb9b7947d1d25dce3d71482fbc9e9c9d31851079066c6c6f0908bb19970")
INDEX = U12 / "ROOT-A12-ACTUAL-CLOSURE-INDEX01.json"
INDEX_PIN = (5088,"5ad53086563d7c2d5dfa845760dd7b20f4db7511347d9d88c1b52c8a3c547d6d")

def checked_pin(path: Path, pin: tuple[int,str]) -> bytes:
    return base.exact(path,pin)

def function_source(module: ModuleType, name: str) -> str:
    source=Path(module.__file__).read_text(encoding="utf-8")
    nodes=[n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name==name]
    require(len(nodes)==1,"one exact function "+name)
    result=ast.get_source_segment(source,nodes[0])
    require(isinstance(result,str),"complete function source")
    return result

def swap(source: bytes, before: str, after: str, count: int=1) -> bytes:
    return prior.swap(source,before,after,count)

def closure_code() -> str:
    return "A13_INDEX="+repr(prior.ref(INDEX))+"\n"+r'''
def validate_actual_a12_index_v1(reference,checked):
    require(reference==A13_INDEX,'exact actual A12 closed index')
    x=checked(reference,16384)
    require(x['schema']=='xar.A12-actual-closure-index/v1' and x['machine_id']==MACHINE
        and x['classification']=='RESOLUTION_REJECTED_PRE_SDK_GAME_FORCED_CLEANUP'
        and x['game_exit_code']==1 and x['game_normal_exit_qualified'] is False
        and x['owned_job_active_final']==0 and x['SDK_status']=='SDK_NOT_STARTED'
        and x['SDK_dual_zero_qualified'] is False and x['NEXT']==10538
        and x['saved_cycles']==4753 and x['saved_days']==5429
        and x['new_business_credit']==0 and x['unknown_10534_replayed'] is False
        and x['wall_clock_reset'] is False and x['personal_recorder_touched'] is False
        and x['recording02_engine_exit_code']==x['recording02_publisher_exit_code']==0
        and x['screen_lease_released'] is True
        and x['next_contract']=={'game_render':[2560,1440],'capture_source':[2560,1440],'capture_scale':[1,1]},
        'actual forced preSDK A12, no business credit')
    rows=x['closure_refs'];require(len(rows)==11 and len({r['path'] for r in rows})==11,'all A12 facts')
    docs={Path(r['path']).name:checked(r,65536) for r in rows}
    closed=docs['ROOT-FRESH-SUPERVISOR-CLOSED-C23-A12.json']
    require(closed['owned_cleanup']['ck3_exit_code']==1 and closed['owned_cleanup']['job_active_processes_final']==0
        and closed['owned_cleanup']['tree_gone'] is True and closed['owned_cleanup']['cleanup_proven'] is True
        and closed['sdk_actual_exit']['status']=='SDK_NOT_STARTED'
        and closed['personal_recorder_touched'] is False,'actual kernel cleanup')
    for name,doc in docs.items():
        if name.endswith('-UNREGISTER01.json'):
            require(doc['returncode']==0 and doc['stderr']=='','actual unregister wrapper')
            actual=json.loads(doc['stdout']);v=actual
            for _ in range(2):
                if 'absent_after' in v:break
                v=v['actual']
            require(actual['machine_id']==MACHINE and actual['operation']=='unregister'
                and v['instances']==0 and v['absent_after'] is True,'both old Tasks absent')
    return x
'''

def closure_guard(plan: JSONObject) -> JSONObject:
    checked_pin(Path(base.__file__),BASE_PIN)
    checked_pin(INDEX,INDEX_PIN)
    require(plan["actual_A12_closure_ref"]==prior.ref(INDEX),"actual A12 closure input")
    env=dict(MACHINE=MACHINE,Path=Path,json=json,require=require)
    exec(closure_code(),env)
    value=env["validate_actual_a12_index_v1"](prior.ref(INDEX),prior.checked)
    for name in ("ROOT-C23-SDKOWNER-CREATE-ADMITTED.json","ROOT-P37C23-COLD-RESUME-ADMISSION.json"):
        require(not (U12/name).exists(),"A12 cold owner gate must never have been published")
    require(not (U12/"p37-queue").exists(),"A12 SDK queue never started")
    require(prior.checked(prior.ref(U12/"NEXT-SEQUENCE-P37.json"))["next_sequence"]==10538,"actual10538")
    return value

def actual_graph(plan: JSONObject) -> tuple[dict[Path,bytes],dict[str,ExactRef],JSONObject,list[ExactRef],list[str]]:
    closure_guard(plan)
    prepared=json.loads(checked_pin(PREPARED,PREPARED_PIN));quote=json.loads(checked_pin(QUOTE,QUOTE_PIN))
    require(prepared["outputs"]==[{k:r[k] for k in ("path","bytes","sha256")} for r in quote["files"]]
        and len(prepared["outputs"])==140 and prepared["machine_id"]==quote["machine_id"]==MACHINE,
        "accepted A12 complete140")
    recovery=prepared["postwrite_recovery"]
    require(recovery["original_producer"]==quote["adopter"]
        and prior.ref(recovery["preserved_original_producer"]["path"])==recovery["preserved_original_producer"]
        and recovery["corrected_verifier_producer"]==prior.ref(base.__file__)
        and recovery["intent_replayed"] is False and recovery["runtime_outputs_rewritten"]==0,
        "original1bf and corrected6aed provenance remain separate")
    profile=prior.checked(prior.ref(U12/"ROOT-OBS-PROFILE-C23.json"))
    config,name=Path(profile["config_root"]),profile["profile_name"]
    mutable={config/"basic/profiles"/name/"basic.ini",config/"basic/scenes"/(name+".json")}
    values,rows,observations={},{},[]
    for row in prepared["outputs"]:
        path=Path(row["path"]).resolve()
        if path in mutable:
            observations.append(prior.ref(path));continue
        require(prior.ref(path)==row,"A12 immutable leaf differs: "+str(path))
        values[path]=prior.raw(path,524288)
        if path.is_relative_to(U12):rows[path.relative_to(U12).as_posix()]=row
    names=quote["sources"]["runtime_source_output_names"]
    require(len(values)==138 and len(observations)==2 and len(names)==len(set(names))==110,"exact graph shape")
    return values,rows,quote,observations,names

def bridge_code(plan: JSONObject) -> str:
    constants={"A13_MIGRATION_REF":plan["environment_migration_ref"],"A13_DRIVER_REVIEW_REF":plan["driver_review_ref"],
        "A13_PREVIOUS_PRE":prior.ref(U12/"ROOT-C23-COLD-PRELAUNCH.json"),"A13_CANONICAL_DRIVER":str(T0/"state/native-session/driver-state.json")}
    return "\n".join(k+"="+repr(v) for k,v in constants.items())+"\n"+closure_code()+r'''
import types as _a13_types
_A13_HISTORY=dict(globals())
for _name,_fn in list(_A13_HISTORY.items()):
    if isinstance(_fn,_a13_types.FunctionType) and _fn.__globals__ is globals():
        _copy=_a13_types.FunctionType(_fn.__code__,_A13_HISTORY,_fn.__name__,_fn.__defaults__,_fn.__closure__)
        _copy.__kwdefaults__=_fn.__kwdefaults__
        _A13_HISTORY[_name]=_copy

def _a13_content(a,b):
    return all(a.get(k)==b.get(k) for k in ('bytes','sha256'))

def _a13_migration(checked):
    r=checked(A13_MIGRATION_REF,32768)
    require(r['schema']=='xar.C23-A13-environment-migration/v1' and r['machine_id']==MACHINE
        and r['prior_migration']==A10_MIGRATION_REF and r['sdk_base']==A12_SOURCE28_BASE
        and r['source28_anchor']==A12_SOURCE28_ANCHOR and r['actual_A12_closure']==A13_INDEX,
        'actual new A13 migration over original A10 and Source28')
    validate_actual_a12_index_v1(A13_INDEX,checked)
    old,_=_A13_HISTORY['_a10_migration'](checked)
    require(r['original_seed']==old['original_seed'] and r['source_derived_seed']==old['derived_seed']
        and r['original_checkpoint']==old['original_checkpoint'] and r['source_checkpoint']==old['target_checkpoint']
        and r['source_lifecycle']==old['target_lifecycle'],'exact original SAVE and migrated666 source')
    source=checked(r['source_derived_seed'],16384);target=checked(r['derived_seed'],16384)
    require(r['target_derived_seed']==r['derived_seed']
        and source['actual_saved_checkpoint']==r['source_checkpoint']
        and target['actual_saved_checkpoint']==r['target_checkpoint'],'source and new derived9054')
    view=json.loads(json.dumps(target));view['actual_saved_checkpoint']=r['source_checkpoint']
    require(view==source and source['completed_cycles']==target['completed_cycles']==4753
        and source['counts']==target['counts'] and target['counts']['checkpoint_saved']==74,'no new counts or history')
    cp=json.loads(json.dumps(r['target_checkpoint']));cp['succession_lifecycle']=r['source_lifecycle']
    require(cp==r['source_checkpoint'] and r['target_checkpoint']['succession_lifecycle']==r['target_lifecycle']
        and {**r['target_lifecycle'],'environment_sha256':r['source_lifecycle']['environment_sha256']}==r['source_lifecycle'],
        'only environment lifecycle changes')
    manifest=checked(r['target_manifest'],32768)
    require(manifest['display']['mode']=='fullscreen' and manifest['display']['resolution']==[2560,1440]
        and manifest['environment_sha256']==r['target_lifecycle']['environment_sha256']
        and manifest['load_profile']['enabled_mods']==[] and manifest['mod']=={'enabled':False,'mounted_mods':[]},
        'actual vanilla fullscreen2560 target')
    return r,target

def _a13_historical_checked(checked,r):
    previous=checked(A13_PREVIOUS_PRE,16384)
    old_review=checked(A12_HISTORICAL_DRIVER_REVIEW,32768)
    expected=old_review['installed_environment_manifest']
    def history(item,limit=262144):
        if item==expected:
            archive=r['source_manifest_archive']
            require(_a13_content(archive,item),'actual old ENV archive contents')
            return checked(archive,limit)
        return checked(item,limit)
    return history,previous

def migration_seed(checked):
    r,seed=_a13_migration(checked)
    return r['derived_seed'],seed

def migration_checkpoint(pre,close,checked):
    r,_=_a13_migration(checked)
    require(close['checkpoint']==r['original_checkpoint'] and pre['checkpoint']==r['target_checkpoint'],
        'historical SAVE close and new native2560 checkpoint')
    return True

def validate_post_sem_driver(pre,close,checked,verify_current_stat=True):
    r,_=_a13_migration(checked);review=checked(A13_DRIVER_REVIEW_REF,32768)
    require(pre['materialized_driver_review']==A13_DRIVER_REVIEW_REF
        and review['machine_id']==MACHINE and review['reviewer']=='/root'
        and review['environment_migration']==A13_MIGRATION_REF and review['actual_A12_closure']==A13_INDEX
        and review['driver_state']==pre['driver_state'] and _a13_content(review['driver_state'],r['target_driver'])
        and Path(pre['driver_state']['path']).resolve()==Path(A13_CANONICAL_DRIVER).resolve()
        and review['checkpoint']==pre['checkpoint']==r['target_checkpoint']
        and review['canonical_validation']==pre['validation']
        and [x['ref'] for x in review['sidecars']]==pre['sidecars']
        and all(x['pending'] is None for x in review['sidecars'])
        and review['SDK_normal'] is False and review['Game_normal'] is False,
        'new current canonical Driver review over forced preSDK A12')
    _a10_helper().validate_source_abort_closure(close,checked)
    migration_checkpoint(pre,close,checked)
    manifest_ref,settings_ref=review['installed_environment_manifest'],review['installed_settings']
    require(_a13_content(manifest_ref,r['target_manifest']) and _a13_content(settings_ref,r['staged_target_settings'])
        and Path(manifest_ref['path']).resolve()==Path(r['canonical_source_manifest']['path']).resolve()
        and Path(settings_ref['path']).resolve()==Path(r['canonical_source_settings']['path']).resolve(),
        'new canonical installed paths and contents')
    manifest=checked(manifest_ref,32768)
    require(manifest['environment_sha256']==pre['environment_sha256']==r['target_lifecycle']['environment_sha256']
        and manifest['load_profile']['pdx_settings_prepared_sha256']==settings_ref['sha256'],
        'new environment and settings')
    if verify_current_stat:
        d=review['driver_stat'];s=Path(pre['driver_state']['path']).stat()
        require(review['driver_stat_schema']=='xar.file-stat-identity.os-ns-decimal.v1'
            and (s.st_size,str(s.st_ino),str(s.st_mtime_ns))==(d['size'],d['FileID'],d['mtime_ns']),
            'current cold OS stat identity')
        raw=Path(settings_ref['path']).read_bytes()
        require(len(raw)==settings_ref['bytes'] and hashlib.sha256(raw).hexdigest()==settings_ref['sha256'],
            'cold prepared settings bytes')
        for row in review['sidecars']:
            require(checked(row['ref'],65536).get('pending') is None,'business pending absent')
    return True

def historical_saved_basis_view(admission):
    require(type(admission['next_sequence']) is int and admission['next_sequence']==10538
        and admission['environment_migration']==A13_MIGRATION_REF
        and admission['source28_anchor']==A12_SOURCE28_ANCHOR,'current10538 distinct from saved10481')
    return {**admission,'next_sequence':10481}

def validate_saved_seed_a10(admission,seed,original,save,semantic,governance,*,checked,projector=None):
    r,derived=_a13_migration(checked)
    require(admission['seed']==r['derived_seed'] and seed==derived
        and admission['environment_migration']==A13_MIGRATION_REF,'new actual derived seed')
    history,pre=_a13_historical_checked(checked,r)
    old,_=_A13_HISTORY['_a10_migration'](history)
    view={**admission,'seed':old['derived_seed'],'environment_migration':A10_MIGRATION_REF,
        'cold_prelaunch':A13_PREVIOUS_PRE}
    _A13_HISTORY['validate_saved_seed_a10'](view,history(old['derived_seed'],16384),
        original,save,semantic,governance,checked=history)
    validate_post_sem_driver(checked(admission['cold_prelaunch'],16384),
        checked(pre['final_driver_close'],16384),checked,verify_current_stat=False)
    return True
'''

def bootstrap(plan: JSONObject, raw: bytes) -> bytes:
    body=swap(raw,"ROOT-FINAL-SDK-FREEZE-P37C23-A12.json","ROOT-FINAL-SDK-FREEZE-P37C23-A13.json")
    seam="if __name__ == '__main__':"
    return swap(body,seam,bridge_code(plan)+"\n"+seam)

def state_guard(plan: JSONObject) -> JSONObject:
    closure_guard(plan)
    pre=prior.checked(plan["cold_prelaunch_ref"],16384);review=prior.checked(plan["driver_review_ref"],32768)
    expected=parse_file_stat_identity_v1({"bytes":review["driver_stat"]["size"],
        "file_id":review["driver_stat"]["FileID"],"mtime_ns":review["driver_stat"]["mtime_ns"]},schema=SCHEMA)
    require(review["driver_stat_schema"]==SCHEMA and pre["materialized_driver_review"]==plan["driver_review_ref"]
        and normalize_file_stat_identity_v1(Path(pre["driver_state"]["path"]).stat())==expected,
        "current new Driver OS identity")
    namespace={"__file__":str(U13/"root_checkpoint_bootstrap_c23.py"),"__name__":"_a13_bridge_RAM"}
    exec(compile(bootstrap(plan,prior.raw(U12/"root_checkpoint_bootstrap_c23.py")), "A13-bootstrap-RAM","exec"),namespace)
    helper=lambda:prior._module(U12/"root_c23_a03_source_abort_checkpoint_inputs.py","_a13_original_helper")
    namespace["_a10_helper"]=helper;namespace["_A13_HISTORY"]["_a10_helper"]=helper
    namespace["validate_post_sem_driver"](pre,prior.checked(pre["final_driver_close"]),prior.checked)
    return {"machine_id":MACHINE,"cold_prelaunch":plan["cold_prelaunch_ref"],"driver_review":plan["driver_review_ref"],
        "actual_A12_index":prior.ref(INDEX),"actual_next_sequence":10538,"historical_saved_basis_next_sequence":10481,
        "Driver_SAVE_body_reads":0}

def source28_guard(plan: JSONObject) -> tuple[JSONObject,JSONObject]:
    oldplan=json.loads(checked_pin(PLAN12,PLAN12_PIN))
    require(plan["compact_base_ref"]==oldplan["compact_base_ref"]
        and plan["canonical_anchor_ref"]==oldplan["canonical_anchor_ref"],"same actual Source28, no SDK rebuild")
    return base.source28_guard(oldplan)


def steam_native_patch(plan: JSONObject, source: bytes) -> bytes:
    expected={"guard":OWN/"steam_native_launch_guard_v1.py",
        "contract":OWN.parent/"steam_offline_state_contract.py",
        "provider":OWN.parent/"steam_offline_native_provider_v1.py"}
    refs=plan["steam_native_sources"]
    for name,path in expected.items():
        require(prior.ref(path)==refs[name],"actual typed Steam source "+name)
    module=types.ModuleType("_a13_exact_steam_prepare")
    module.__file__=str(expected["guard"]);sys.modules[module.__name__]=module
    exec(compile(prior.raw(expected["guard"]),module.__file__,"exec"),vars(module))
    return module.render_supervisor_patch(source,prior.raw(expected["contract"]),prior.raw(expected["provider"]))

def bind_steam_native_metadata(plan: JSONObject, outputs: Outputs, quote: JSONObject) -> None:
    proof=plan["steam_native_state_ref"]
    prior.checked(proof,16384)
    config_path=U13/"ROOT-LAUNCH-CONFIG-C23-A13.json"
    config=json.loads(outputs[config_path]);config["steam_native_state"]=proof
    spec_path=O/"tasks/spec-supervisor-a13/SPEC.json"
    spec=json.loads(outputs[spec_path])
    require("--steam-native-state" not in spec["stage_args"],"one native Steam argument")
    spec["stage_args"]+=["--steam-native-state",proof["path"]]
    for path,value in ((config_path,config),(spec_path,spec)):
        data=prior.enc(value);outputs[path]=data
        row=next(r for r in quote["files"] if Path(r["path"])==path)
        require(row["mode"]=="create-only" and row["source"] is None,"new A13 metadata")
        row.update(bytes=len(data),sha256=prior.sha(data),allocation_upper=((len(data)+4095)//4096)*4096)
    quote["logical_bytes"]=sum(map(len,outputs.values()))
    quote["fresh_allocation_upper"]=sum(r["allocation_upper"] for r in quote["files"])
    quote["max_atomic_copy"]=max(((len(b)+4095)//4096)*4096 for b in outputs.values())
    quote["prepare_peak_upper"]=sum(quote[k] for k in ("fresh_allocation_upper","max_atomic_copy",
        "future_owner_metadata_upper","control_probe_atomic_peak","intent_receipt_and_FS_upper"))
    quote["steam_native_sources"]=plan["steam_native_sources"]
    quote["steam_native_state_ref"]=proof

def build_sources(plan: JSONObject) -> tuple[dict[str,bytes],JSONObject]:
    values,rows,quote,mutable,names=actual_graph(plan)
    source={name:values[U12/name] for name in names}
    source["root_checkpoint_bootstrap_c23.py"]=bootstrap(plan,source["root_checkpoint_bootstrap_c23.py"])
    source["root_p37c23_cold_resume.py"]=swap(source["root_p37c23_cold_resume.py"],
        "ROOT-FINAL-SDK-FREEZE-P37C23-A12.json","ROOT-FINAL-SDK-FREEZE-P37C23-A13.json")
    body=source["root_native30_supervisor_c23.py"]
    body=body.replace(b"C23-A12",b"C23-A13")
    for a,b,n in (("args.attempt=='a12'","args.attempt=='a13'",1),("value.get('attempt_id')=='a12'","value.get('attempt_id')=='a13'",1),
        ('choices=("a12",)','choices=("a13",)',1),('"attempt_id":"a12"','"attempt_id":"a13"',2),
        ("    _validate_a12_attempt(args, config)","    _validate_a13_attempt(args, config)",1)):
        body=swap(body,a,b,n)
    extra=closure_code()+r'''
def _validate_a13_attempt(args,config):
    value=_validate_a12_attempt(args,config)
    validate_actual_a12_index_v1(value['prior_failure_a12'],_a03_checked)
    x=_a03_checked(A13_INDEX,16384)
    closed=_a03_checked(x['closure_refs'][0],65536)
    require(args.attempt_nonce not in (closed['attempt_nonce'],closed['task_nonce'])
        and args.task_nonce not in (closed['attempt_nonce'],closed['task_nonce']),'independent A13 nonces')
    return value

'''
    body=steam_native_patch(plan,body)
    source["root_native30_supervisor_c23.py"]=swap(body,"def main(args):",extra+"def main(args):")
    require(b"stop_requested: bool" in body and b"require_complete_tool_result(result)" in source["root_p37c23_sdk_queue.py"],
        "retain qualified stopSnapshot and complete result without duplicate patch")
    for name,data in source.items():
        if name.endswith(".py"):compile(data,name,"exec")
    return source,{"schema":"xar.A13-Source28-source/v1","machine_id":MACHINE,"feeder":{},
        "actual_source_rows":[rows[n] for n in names],"runtime_source_output_names":names,
        "supplemental_import_rows":quote["sources"]["supplemental_import_rows"],
        "staging_files":[rows[n] for n in base.old.STAGE_NAMES],"mutable_OBS_config_observations":mutable,
        "actual_A12_index":prior.ref(INDEX),"new_day_credit":0,
        "preparation_helper_refs":[prior.ref(base.__file__)]}

def scope(plan: JSONObject | None=None) -> dict[str,object]:
    namespace=dict(vars(base),__file__=__file__,U11=U12,U12=U13,build_sources=build_sources,
        state_guard=state_guard,metadata_source=metadata_source,metadata_scope=metadata_scope,
        campaign_score_guard=campaign_score_guard,compose_plan=compose_plan)
    env=types.FunctionType(base.scope.__code__,namespace)(plan)
    spec=base.old.get_function(base.old,"ram_supervisor_spec",base.previous.PIN)
    spec=swap(spec.encode(),'"--attempt","a10"','"--attempt","a13"').decode()
    exec(compile(spec,"A13-supervisor-SPEC-RAM","exec"),env)
    return env

def campaign_score_guard(*,alias_required: bool=False) -> JSONObject:
    return types.FunctionType(base.campaign_score_guard.__code__,dict(vars(base),U12=U13))(alias_required=alias_required)

def metadata_source(source: str) -> str:
    raw=base.metadata_source(source)
    return swap(raw.encode(),"'environment_migration':A10_MIGRATION_REF",
        "'environment_migration':A13_MIGRATION_REF").decode()

def metadata_scope(namespace: dict[str,object], runtime: Path) -> None:
    base.metadata_scope(namespace,runtime)
    module=prior._module(runtime/"root_checkpoint_bootstrap_c23.py","_a13_actual_bootstrap")
    namespace["A13_MIGRATION_REF"]=module.A13_MIGRATION_REF

def compose(plan: JSONObject, *, display_values: dict[str,bytes], display_review: JSONObject,
            companion_values: Outputs) -> tuple[Outputs,JSONObject]:
    text=function_source(base,"compose")
    changes=(('C23-A12','C23-A13'),("'a12'","'a13'"),
        ('.replace("C23-A04","C23-A11")','.replace("C23-A04","C23-A12")'),
        ('spec-supervisor-a12','spec-supervisor-a13'),
        ('prior_failure_a11=A12_INDEX)','prior_failure_a11=A12_INDEX,prior_failure_a12=A13_INDEX)'),
        ('"A12_INDEX":A12_INDEX','"A12_INDEX":A12_INDEX,"A13_INDEX":A13_INDEX'),
        ('env.update(A10_INDEX=prior.ref(previous.INDEX),A12_INDEX=prior.ref(INDEX))',
         'env.update(A10_INDEX=prior.ref(base.previous.INDEX),A12_INDEX=prior.ref(base.INDEX),A13_INDEX=prior.ref(INDEX))'),
        ('xar.C23-A13-union-prepare-quote/v1','xar.C23-A13-union-prepare-quote/v1'))
    for before,after in changes:
        if before!=after:
            require(before in text,"known A12 compose seam "+before);text=text.replace(before,after)
    env=dict(vars(base),base=base,__file__=__file__,U11=U12,U12=U13,INDEX=INDEX,
        source28_guard=source28_guard,scope=scope)
    exec(compile(text,"A13-complete-union","exec"),env)
    outputs,quote=env["compose"](plan,display_values=display_values,display_review=display_review,companion_values=companion_values)
    bind_steam_native_metadata(plan,outputs,quote)
    quote.update(actual_A12_index=prior.ref(INDEX),actual_A11_index=prior.ref(base.INDEX),
        target_display={"mode":"fullscreen","resolution":[2560,1440],"capture_scale":[1,1]},
        environment_migration=plan["environment_migration_ref"],new_timing_enabled=False)
    return outputs,quote

def display_compose(plan: JSONObject) -> tuple[dict[str,bytes],JSONObject,Outputs]:
    reference=plan["display_producer"]
    require(prior.ref(reference["path"])==reference
        and Path(reference["path"]).resolve()==OWN/"prepare_source28_a13_display_v1.py","exact A13 display producer")
    module=prior._module(reference["path"],"_a13_actual_display")
    values,review,companions=module.compose(plan["display"])
    review["a13_producer"]=reference
    return values,review,companions

def compose_plan(plan_ref: ExactRef) -> tuple[JSONObject,Outputs,JSONObject]:
    plan=prior.checked(plan_ref,131072)
    require(prior.ref(__file__)==plan["union_producer"] and plan["schema"]=="xar.C23-A13-union-prepare-input/v1",
        "exact independent A13 plan")
    values,review,companions=display_compose(plan)
    outputs,quote=compose(plan,display_values=values,display_review=review,companion_values=companions)
    quote.update(adopter=prior.ref(__file__),input_plan=plan_ref,
        original_adopter_source=prior.ref(OWN/"adopt_c23_a05_union_v1.py"))
    return plan,outputs,quote

def adopt(plan_ref: ExactRef, quote_ref: ExactRef, card_ref: ExactRef) -> ExactRef:
    text=function_source(base,"adopt").replace("A12","A13").replace("a12","a13")
    env=dict(vars(base),__file__=__file__,scope=scope)
    exec(compile(text,"A13-Root-only-adopt","exec"),env)
    return env["adopt"](plan_ref,quote_ref,card_ref)

def cold_owner(inputs: JSONObject) -> tuple[Outputs,JSONObject]:
    text=function_source(base,"cold_owner").replace("A12","A13").replace("a12","a13")
    env=dict(vars(base),__file__=__file__,scope=scope)
    exec(compile(text,"A13-actual-cold-owner","exec"),env)
    return env["cold_owner"](inputs)

def build_task_spec(display_values: dict[str,bytes],display_review: JSONObject,*,
    task_nonce: str,game_launch_ref: ExactRef,placement_ref: ExactRef,
    bootstrap_ref: ExactRef,owner_contract_ref: ExactRef) -> tuple[Outputs,JSONObject]:
    reference=display_review["a13_producer"]
    require(prior.ref(reference["path"])==reference,"exact actual display producer")
    module=prior._module(reference["path"],"_a13_late_display_Task")
    return module.build_task_spec(display_values,display_review,task_nonce=task_nonce,
        game_launch_ref=game_launch_ref,placement_ref=placement_ref,
        bootstrap_ref=bootstrap_ref,owner_contract_ref=owner_contract_ref)
