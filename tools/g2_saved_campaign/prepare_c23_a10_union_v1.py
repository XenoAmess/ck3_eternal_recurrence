"""A10 Source27 RAM preparation; Root alone adopts."""
from __future__ import annotations
import ast, hashlib, json, sys, types
from pathlib import Path
from typing import TypedDict
sys.dont_write_bytecode = True
OWN = Path(__file__).resolve().parent
sys.path.insert(0, str(OWN))
import prepare_c23_a09_union_v1 as previous
prior = previous.prior
MACHINE, O, T0 = previous.MACHINE, previous.O, previous.T0
U9, U10 = previous.U9, previous.U9.with_name("runtime-a10")
T5, HELPER = U10, previous.HELPER
require, exact = previous.require, previous.exact
PREVIOUS_PIN = (17280, "594e66e068b4cd39b3f1e9e19d12f3726a5d26e11b44a12916b730e2dfb05fce")
PREPARED = O / "A09-PREPARED01.json"
PREPARED_PIN = (36943, "cb9919a6eb0756288d86f5ae672f6cc4c0f602c71dec493e97ac39f1d57787fa")
QUOTE = O / "A09-ROOT-QUOTE01.json"
QUOTE_PIN = (161691, "037b6b30959990e55c184f32a43aa2b582bc3a91b37370921a16917a5641bd85")
INDEX = U9 / "a09-readonly-diagnostics01/A09-ACTUAL-CLOSURE-INDEX01.json"
INDEX_PIN = (7036, "d0d13ae2cf51838092e1ae8c7b3a5bcb141bdd84313d56015ba12003f6cabfee")
P = O / "source27-a10-prep01"
BASE27 = P / "ROOT-FINAL-SDK-SOURCE27-BASE.json"
BASE27_PIN = (398331, "c93cc3e4d4d4996a7787d0f4b095ae67b8e4d145e725f2d7e288c8010b64a8fe")
ANCHOR27 = P / "source27-canonical01/SOURCE27-CANONICAL-ANCHOR.json"
ANCHOR27_PIN = (9235, "390e368a1101d6ab6ac4c311aba0f453859d51276dc825ed352d6340a3378d38")
STAGING = P / "operational-source-staging01"
STAGE_NAMES = ("root_a10_observe_halted_state_v1.py", "root_a10_early_owned_close_v1.py",
 "launch_a10_saved10480_feeder01.py", "interactive_task_owner_a10_v1.py", "owner_prepare_contract_v1.py")
STAGE_CAPS = (16384, 12288, 16384, 32768, 4096)
DISPLAY_PIN = (8189, "46837b265d2112e764155302f0461fba74f40ef0e7c716ad1e61d83180ad1f23")
FULL_PIN = (28046, "74e1ec7ce3dfe56f0920f1175ee01b1d8c4a2e040787f336bf1eb8df3048400a")
UNION_PIN, ADOPTER_PIN = previous.UNION_PIN, previous.ADOPTER_PIN

type JSONValue = None | bool | int | float | str | list[JSONValue] | dict[str,JSONValue]
type JSONObject = dict[str,JSONValue]
type Outputs = dict[Path,bytes]

class ExactRef(TypedDict):
    path: str
    bytes: int
    sha256: str

def content(a, b):
    return type(a) is dict and type(b) is dict and all(a.get(k) == b.get(k) for k in ("bytes", "sha256"))

def get_function(module, name, expected):
    text = exact(module.__file__, expected).decode("utf-8")
    nodes = [n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == name]
    require(len(nodes) == 1, "one exact source function required")
    return ast.get_source_segment(text, nodes[0])

def actual_graph():
    exact(previous.__file__, PREVIOUS_PIN)
    prepared = json.loads(exact(PREPARED, PREPARED_PIN))
    quote = json.loads(exact(QUOTE, QUOTE_PIN))
    index = json.loads(exact(INDEX, INDEX_PIN))
    require(prepared["machine_id"] == quote["machine_id"] == index["machine_id"] == MACHINE
        and prepared["outputs"] == [{k:r[k] for k in ("path","bytes","sha256")} for r in quote["files"]]
        and len(prepared["outputs"]) == 135, "actual accepted A09 graph")
    idx = {r["relative"]: r for r in index["files"] if r["root"] == "U9"}
    nextrow = idx["NEXT-SEQUENCE-P37.json"]
    nextref = {"path":str(U9/"NEXT-SEQUENCE-P37.json"), "bytes":nextrow["bytes"], "sha256":nextrow["sha256"]}
    require(prior.checked(nextref)["next_sequence"] == index["next_sequence"] == 10521, "A09 consumed NEXT10521")
    profile = prior.checked(prior.ref(U9/"ROOT-OBS-PROFILE-C23.json"))
    config = Path(profile["config_root"]).resolve()
    name = profile["profile_name"]
    mutable = {config/"basic/profiles"/name/"basic.ini", config/"basic/scenes"/(name+".json")}
    values, rows, observations = {}, {}, []
    for row in prepared["outputs"]:
        path = Path(row["path"]).resolve()
        if path in mutable:
            observations.append(prior.ref(path))
            continue
        current = nextref if path == U9/"NEXT-SEQUENCE-P37.json" else row
        body = prior.raw(path, 524288)
        require(prior.ref(path) == current, "actual A09 immutable accepted input differs: " + str(path))
        values[path], rows[path] = body, current
    require(len(observations) == 2 and len(values) == 133, "only OBS2 mutable; NEXT separately proven")
    names = [Path(r["path"]).relative_to(previous.U8).as_posix()
             for r in quote["sources"]["actual_source_rows"]]
    require(len(names) == len(set(names)) == 105 and all(U9/n in values for n in names), "105 actual source leaves")
    return values, rows, quote, observations, names

def stage_values(plan):
    refs = plan["source_staging_refs"]
    require(type(refs) is list and len(refs) == 5, "five admitted source staging refs")
    index = {Path(r["path"]).name:r for r in refs}
    require(set(index) == set(STAGE_NAMES), "exact operational staging names")
    out = {}
    for name, cap in zip(STAGE_NAMES, STAGE_CAPS):
        row = index[name]
        path = Path(row["path"]).resolve()
        require(path == STAGING/name and type(row["bytes"]) is int and 0 < row["bytes"] <= cap
            and prior.ref(path) == row, "actual staged operational source")
        body = prior.raw(path, cap)
        compile(body, name, "exec")
        out[name] = body
    return out, index

def source27_guard():
    base = json.loads(exact(BASE27, BASE27_PIN))
    anchor = json.loads(exact(ANCHOR27, ANCHOR27_PIN))
    require(base["machine_id"] == anchor["machine_id"] == MACHINE
        and base["business_source_commit"] == anchor["commit"] == "4b0f3771b51d65af2cd6d576116535237aac7ef0"
        and anchor["parent"] == "394865df3259be5db29014ab1d17db7bdd48c21d"
        and anchor["schema"] == "xar.source27.canonical-git-anchor/v1"
        and anchor["status"] == "CANONICAL_REF_CREATED_NOT_DEPLOYED"
        and base["source27_canonical_anchor"] == prior.ref(ANCHOR27)
        and "canonical_preload_policy" not in base and base["runtime_admitted"] is False, "actual policy-free Source27")
    rows = base["files"]
    packed = json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()
    require(len(rows) == 1462 and sum(r["bytes"] for r in rows) == 59255805
        and {"bytes":len(packed), "sha256":prior.sha(packed)}
        == anchor["complete_rows_JSON"], "all canonical Source27 rows")
    return base, anchor

def bridge_source(plan):
    constants = {"A10_MIGRATION_REF":plan["environment_migration_ref"],
        "A10_DRIVER_REVIEW_REF":plan["driver_review_ref"],
        "A10_SOURCE27_BASE":prior.ref(BASE27), "A10_SOURCE27_ANCHOR":prior.ref(ANCHOR27),
        "A10_SOURCE26_BASE":prior.ref(O/"ROOT-FINAL-SDK-SOURCE26-BASE.json"),
        "A10_A09_INDEX":prior.ref(INDEX)}
    header = "\n".join(name+"="+repr(value) for name,value in constants.items())+"\n"
    return header + r'''
def _a10_content(a,b):
    return type(a) is dict and type(b) is dict and all(a.get(k)==b.get(k) for k in ('bytes','sha256'))

def _a10_helper():
    import types
    p=Path(__file__).with_name('root_c23_a03_source_abort_checkpoint_inputs.py')
    raw=p.read_bytes()
    require(len(raw)==17637 and hashlib.sha256(raw).hexdigest()=='bae312f0fb07d370252ecc5714666fe1790a4db33bca32599e0e9bcb56d64a8e','unchanged original Source26 helper')
    module=types.ModuleType('_a10_original_source26_saved_authority')
    module.__file__=str(p)
    exec(compile(raw,str(p),'exec'),vars(module))
    return module

def validate_actual_a09_index_v1(ref,checked):
    require(ref==A10_A09_INDEX,'actual A09 closed index')
    x=checked(ref,16384)
    require(x['schema']=='xar.A09-actual-closure-index/v1' and x['machine_id']==MACHINE
        and x['next_sequence']==10521 and x['unknown_AUTO']==10519
        and x['saved_cycles']==4753 and x['settled_cycles']==4760
        and x['SDK_actual_exits']==[1,0] and x['Game_actual_exit']==1
        and x['Game_forced'] is True and x['original_T0_end_wall_preserved'] is True
        and x['original_actions_replayed'] is False and x['new_FULL_success'] is False,'actual abnormal A09, no unknown action credit')
    out={}
    for row in x['files']:
        root=Path(x['roots'][row['root']]).resolve()
        p=(root/row['relative']).resolve()
        require(p.is_relative_to(root) and row['relative'] not in out,'A09 closure exact scope')
        out[row['relative']]=checked({'path':str(p),'bytes':row['bytes'],'sha256':row['sha256']},65536)
    require(len(out)==23 and out['NEXT-SEQUENCE-P37.json']['next_sequence']==10521,'all actual A09 closed facts')
    game=out['ROOT-ACTUAL-GAME-EXIT-C23.json'];sdk=out['ROOT-P37C23-OWNER-CLOSED.json']
    require(game['machine_id']==sdk['machine_id']==MACHINE and game['exit_code']==1
        and game['forced_owned_job_cleanup'] is True and sdk['normal'] is False
        and sorted((r['role'],r['exit_code']) for r in sdk['processes'])==[('sdk_application',0),('sdk_queue',1)]
        and all(r['kernel_exit_observed'] is True and r['wait_result']==0 and r['observation_error'] is None for r in sdk['processes']),'actual prior Game/SDK exit tuple')
    for name,doc in out.items():
        if name.startswith('tasks/') and name.endswith('/CLOSED.json'):
            require(doc['job_active_after_stage']==0,'old Task Job zero')
        if name.endswith('-UNREGISTER01.json'):
            require(doc['returncode']==0 and doc['stderr']=='','actual unregister wrapper')
            actual=json.loads(doc['stdout'])
            require(actual['machine_id']==MACHINE and actual['operation']=='unregister'
                and actual['actual']['instances']==0 and actual['actual']['absent_after'] is True,'old once-only Task actually absent')
    return x

def validate_source27_business_anchor(anchor,checked):
    expected=checked(A10_SOURCE27_ANCHOR,65536)
    require(anchor==expected and anchor['schema']=='xar.source27.canonical-git-anchor/v1'
        and anchor['machine_id']==MACHINE and anchor['status']=='CANONICAL_REF_CREATED_NOT_DEPLOYED'
        and anchor['parent']=='394865df3259be5db29014ab1d17db7bdd48c21d'
        and anchor['commit']=='4b0f3771b51d65af2cd6d576116535237aac7ef0'
        and anchor['tree']=='a5ab65d7a7e2025366c06657010ceb6f2fff5a21'
        and len(anchor['output_pins'])==6 and len(anchor['canonical_patch_rows'])==15,'actual Source27 canonical authority')
    helper=_a10_helper();old=checked(A10_SOURCE26_BASE,524288)
    helper.validate_frozen_business({'business_anchor':old['source26_canonical_anchor'],
        'business_source_commit':old['business_source_commit']},old,checked)
    require(anchor['actual_Source26_anchor']==old['source26_canonical_anchor'],'exact historical Source26 parent')
    return anchor

def validate_source27_frozen_business(admission,freeze,checked):
    require(admission['business_anchor']==A10_SOURCE27_ANCHOR,'new admission has actual Source27 anchor')
    anchor=validate_source27_business_anchor(checked(A10_SOURCE27_ANCHOR,65536),checked)
    base=checked(A10_SOURCE27_BASE,524288);old=checked(A10_SOURCE26_BASE,524288)
    rows=freeze['files'];raw=json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    require(freeze['machine_id']==MACHINE and freeze['business_source_commit']==admission['business_source_commit']==anchor['commit']
        and rows==base['files'] and len(rows)==1462 and sum(r['bytes'] for r in rows)==59255805
        and {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}==anchor['complete_rows_JSON'],'all actual Source27 rows')
    before={r['relative']:r for r in old['files']};after={r['relative']:r for r in rows}
    require(set(before)==set(after) and {n for n in after if after[n]!=before[n]}=={r['relative'] for r in anchor['output_pins']}
        and all(after[r['relative']]==r for r in anchor['output_pins']),'only six Source27 SDK changes')
    return anchor

def _a10_migration(checked):
    r=checked(A10_MIGRATION_REF,32768)
    require(r['schema']=='xar.C23-A10-environment-migration/v1' and r['machine_id']==MACHINE
        and r['reviewer']=='/root' and r['sdk_base']==A10_SOURCE27_BASE
        and r['source27_anchor']==A10_SOURCE27_ANCHOR and r['actual_A09_closure']==A10_A09_INDEX
        and r['history_or_actions_reconstructed'] is False and r['SAVE_bytes_modified'] is False
        and r['materialize_closed_directory_called'] is False and r['outputs_written']==0
        and r['actual_next_sequence']==10521 and r['historical_helper_next_sequence']==10481
        and r['rollback_cycles']==7 and r['rollback_days']==1 and r['unknown10519_credit']==0
        and r['Game_Task_RPC_calls']==0,'qualified pure windowed environment migration')
    validate_actual_a09_index_v1(A10_A09_INDEX,checked)
    require(r['source27_export']==checked(A10_SOURCE27_BASE,524288)['immutable_source_export'],'actual Source27 export provenance')
    target=checked(r['target_manifest'],32768)
    require(target['display']['mode']=='windowed' and target['display']['resolution']==[1280,720]
        and target['load_profile']['enabled_mods']==[] and target['mod']=={'enabled':False,'mounted_mods':[]}
        and target['environment_sha256']==r['target_lifecycle']['environment_sha256'],'target vanilla windowed contract')
    require({**r['target_lifecycle'],'environment_sha256':r['source_lifecycle']['environment_sha256']}==r['source_lifecycle']
        and r['target_lifecycle']!=r['source_lifecycle'],'only lifecycle environment digest changed')
    cp=json.loads(json.dumps(r['target_checkpoint']))
    cp['succession_lifecycle']=r['source_lifecycle']
    require(cp==r['original_checkpoint'] and r['target_checkpoint']['succession_lifecycle']==r['target_lifecycle'],'checkpoint differs only by environment lifecycle')
    original=checked(r['original_seed'],16384);derived=checked(r['derived_seed'],16384)
    view=json.loads(json.dumps(derived));view['actual_saved_checkpoint']=r['original_checkpoint']
    require(view==original and original['actual_saved_checkpoint']==r['original_checkpoint']
        and derived['actual_saved_checkpoint']==r['target_checkpoint']
        and original['completed_cycles']==derived['completed_cycles']==4753
        and original['counts']==derived['counts'] and derived['counts']['checkpoint_saved']==74,'derived9054 carries no new action/count')
    return r,derived

def migration_seed(checked):
    r,seed=_a10_migration(checked)
    return r['derived_seed'],seed

def migration_checkpoint(pre,close,checked):
    r,_=_a10_migration(checked)
    require(close['checkpoint']==r['original_checkpoint'] and pre['checkpoint']==r['target_checkpoint'],'historical close and target checkpoint explicit bridge')
    return True

def validate_post_sem_driver(pre,close,checked,verify_current_stat=True):
    require(pre['materialized_driver_review']==A10_DRIVER_REVIEW_REF,'actual installed Driver review')
    review=checked(A10_DRIVER_REVIEW_REF,32768);r,_=_a10_migration(checked)
    require(review['machine_id']==MACHINE and review['reviewer']=='/root'
        and review['environment_migration']==A10_MIGRATION_REF
        and review['driver_state']==pre['driver_state'] and _a10_content(review['driver_state'],r['target_driver'])
        and Path(review['driver_state']['path']).resolve()==Path(r['source_pair']['base']['path']).resolve()
        and review['checkpoint']==pre['checkpoint']==r['target_checkpoint']
        and review['canonical_validation']==pre['validation']==r['target_validation']
        and [row['ref'] for row in review['sidecars']]==pre['sidecars']
        and all(type(row['pending_key_present']) is bool and row['pending'] is None for row in review['sidecars'])
        and review['SDK_normal'] is False and review['Game_normal'] is False and review['new_day_credit']==0,'actual target Driver/canonical validation')
    _a10_helper().validate_source_abort_closure(close,checked)
    migration_checkpoint(pre,close,checked)
    manifest_ref=review['installed_environment_manifest'];settings_ref=review['installed_settings']
    require(_a10_content(manifest_ref,r['target_manifest'])
        and Path(manifest_ref['path']).resolve()==Path(r['source_manifest']['path']).resolve()
        and _a10_content(settings_ref,r['staged_target_settings']),'actual installed small environment contents')
    manifest=checked(manifest_ref,32768)
    require(Path(settings_ref['path']).resolve()==Path(manifest['profile_dir']).resolve()/'pdx_settings.txt'
        and manifest['environment_sha256']==pre['environment_sha256']==r['target_lifecycle']['environment_sha256']
        and manifest['load_profile']['pdx_settings_prepared_sha256']==settings_ref['sha256'],'canonical ENV/settings exact paths')
    archive=review['old_manifest_archive']
    require(_a10_content(archive,r['source_manifest']) and Path(archive['path']).resolve()!=Path(manifest_ref['path']).resolve(),'retained original manifest archive')
    checked(archive,32768)
    if verify_current_stat:
        raw=Path(settings_ref['path']).read_bytes()
        require(len(raw)<=65536 and len(raw)==settings_ref['bytes'] and hashlib.sha256(raw).hexdigest()==settings_ref['sha256'],'actual cold settings bytes')
        s=Path(pre['driver_state']['path']).stat();d=review['driver_stat']
        require((s.st_size,str(s.st_mtime_ns),str(s.st_ino))==(d['size'],d['mtime_ns'],d['FileID']),'actual current cold Driver stat')
        for name,oldref in (('base',r['source_pair']['base']),('wal',r['source_pair']['wal'])):
            s=(Path(review['source_pair_archive'])/Path(oldref['path']).name).stat()
            require([str(v) for v in (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)]==r['source_pair']['identity'][name],'original pair retained by exact identity')
        for ref in pre['sidecars']:
            value=checked(ref,65536);require(value.get('pending') is None,'cold business sidecar pending absent')
    return True

def historical_saved_basis_view(admission):
    require(type(admission['next_sequence']) is int and admission['next_sequence']==10521
        and admission['environment_migration']==A10_MIGRATION_REF and admission['source27_anchor']==A10_SOURCE27_ANCHOR,'actual A10 frontier remains10521')
    return {**admission,'next_sequence':10481}

def validate_saved_seed_a10(admission,seed,original,save,semantic,governance,*,checked,projector=None):
    r,derived=_a10_migration(checked)
    require(admission['seed']==r['derived_seed'] and admission['original_state']==r['original_seed']
        and seed==derived,'actual derived seed source')
    helper=_a10_helper()
    helper.validate_saved_seed(historical_saved_basis_view(admission),original,original,save,semantic,governance,checked=checked)
    pre=checked(admission['cold_prelaunch'],16384);close=checked(pre['final_driver_close'],16384)
    validate_post_sem_driver(pre,close,checked,verify_current_stat=False)
    return True

'''

def metadata_source(source):
    data = source.encode()
    n=source.count("'control_sequence':10483")
    require(n in (0,1),"one optional original timing admission")
    if n:data=prior.swap(data,"'control_sequence':10483","'control_sequence':10523",1)
    data = prior.swap(data, "'next_sequence':10481", "'next_sequence':10521", 3)
    data = prior.swap(data, ".get('next_sequence')==10481", ".get('next_sequence')==10521", 1)
    data = prior.swap(data, "anchor_ref=freeze['source26_canonical_anchor'];anchor=helper.validate_business_anchor(checked(anchor_ref,65536))",
        "anchor_ref=freeze['source27_canonical_anchor'];anchor=validate_source27_business_anchor(checked(anchor_ref,65536),checked)", 1)
    data = prior.swap(data, "helper.validate_frozen_business(", "validate_source27_frozen_business(", 2)
    data = prior.swap(data, "seed=checked(original,16384)", "derived_ref,seed=migration_seed(checked)", 1)
    data = prior.swap(data, "'seed':original", "'seed':derived_ref", 1)
    data = prior.swap(data, "'source_abort_index':close['source_abort_index']", "'environment_migration':A10_MIGRATION_REF,'source27_anchor':A10_SOURCE27_ANCHOR,'source_abort_index':close['source_abort_index']", 1)
    data = prior.swap(data, "helper.validate_saved_seed(basis,", "validate_saved_seed_a10(basis,", 1)
    data = prior.swap(data, "helper.validate_saved_seed(admission,", "validate_saved_seed_a10(admission,", 1)
    seam = "sourcepins={str(path.relative_to(runtime)):digest for path,digest in entries.items() if path.is_relative_to(runtime)}"
    extra = seam+"\n    for item in policy['runtime_import_source_pins']:\n        require(ref(item['path'])==item,'exact A10 complete runtime import pin')\n        sourcepins[str(Path(item['path']).relative_to(runtime))]=item['sha256']"
    return prior.swap(data, seam, extra, 1).decode()

def metadata_scope(scope, runtime):
    bootstrap = prior._module(runtime/"root_checkpoint_bootstrap_c23.py", "_a10_actual_bootstrap_metadata")
    pre = prior.ref(runtime/"ROOT-C23-COLD-PRELAUNCH.json")
    scope["COLD_PRE_PIN"] = (pre["bytes"], pre["sha256"])
    for name in ("validate_source27_business_anchor", "validate_source27_frozen_business",
                 "migration_seed", "validate_saved_seed_a10", "A10_MIGRATION_REF", "A10_SOURCE27_ANCHOR"):
        scope[name] = getattr(bootstrap, name)

def patch_supervisor(data):
    text = data.decode("utf-8")
    for old,new,n in (
        ("args.attempt=='a09'","args.attempt=='a10'",1),
        ("value.get('attempt_id')=='a09'","value.get('attempt_id')=='a10'",1),
        ('choices=("a09",)','choices=("a10",)',1),
        ('"attempt_id":"a09"','"attempt_id":"a10"',2),
        ("_validate_a09_attempt(args, config)","_validate_a10_attempt(args, config)",1),
        ("    require(read(N/'NEXT-SEQUENCE-P37.json')['next_sequence']==10502,'new A09 consumes actual NEXT10502')\n","",1)):
        text = prior.swap(text.encode(),old,new,n).decode("utf-8")
    guard = r'''
def _validate_a10_attempt(args,config):
    value=_validate_a09_attempt(args,config)
    from root_checkpoint_bootstrap_c23 import validate_actual_a09_index_v1
    index=validate_actual_a09_index_v1(value['prior_failure_a09'],_a03_checked)
    require(read(N/'NEXT-SEQUENCE-P37.json')['next_sequence']==10521,'new A10 consumes actual NEXT10521 once')
    row=next(r for r in index['files'] if r['relative']=='ROOT-FRESH-SUPERVISOR-CLOSED-C23-A09.json')
    old=_a03_checked({'path':str(Path(index['roots']['U9'])/row['relative']),'bytes':row['bytes'],'sha256':row['sha256']})
    require(args.attempt_nonce not in (old['attempt_nonce'],old['task_nonce']) and args.task_nonce not in (old['attempt_nonce'],old['task_nonce']),'fresh A10 once-only nonces')
    return value

'''
    text = prior.swap(text.encode(),"def main(args):",guard+"def main(args):",1).decode("utf-8")
    early = r'''
from root_a10_early_owned_close_v1 import load_plan,execute_once
early_plan=load_plan(N,generation,now=now())
if early_plan is not None:
    normal_close_requested=True
    def early_stop_owned(h:object,*,require_running:bool=False)->object:
        nonlocal cleanup_attempted,cleanup,forced
        cleanup_attempted=True
        forced=handle.process.poll() is None
        cleanup=runtime.stop_tracked(h,require_running=require_running)
        return cleanup
    try:
        early=execute_once(N,early_plan,generation,handle,kernel=kernel_exit,
            normal_close=request_owned_close,stop_tracked=early_stop_owned,
            write=write,now=now(),deadline=deadline)
    except BaseException:
        if not cleanup_attempted:
            early_stop_owned(handle,require_running=False)
        raise
    normal_exit=early['normal_exit']
    forced=early['forced_path_used']
    cleanup_attempted=early['cleanup_attempted']
    cleanup=early['cleanup']
    reason='Root_observed_halt_early_owned_Game_close'
    break
'''
    seam = '        while not (N / "STOP-OWNED-GAME-C23").exists():\n'
    block = "".join("            "+line+"\n" for line in early.strip().splitlines())
    text = prior.swap(text.encode(),seam,seam+block,1).decode("utf-8")
    start = text.index("                if generation is not None and kernel_exit(generation) is None:")
    end = text.index("                if generation is not None:\n                    observed = kernel_exit(generation)",start)
    original = text[start:end]
    require("cleanup_attempted = True" in original and "runtime.stop_tracked(handle" in original, "entire original Game cleanup block")
    text = text[:start]+"                if not cleanup_attempted:\n"+"".join("    "+line+"\n" for line in original.splitlines())+text[end:]
    return text.encode()

def build_sources(plan):
    values, rows, quote, mutable, names = actual_graph()
    source = {name:values[U9/name].replace(b"C23-A09",b"C23-A10") for name in names}
    staged, stage_refs = stage_values(plan)
    for name,body in staged.items():
        require(name not in source, "new staging source cannot overwrite accepted source")
        source[name] = body
    source["root_native30_supervisor_c23.py"] = patch_supervisor(source["root_native30_supervisor_c23.py"])
    body = source["root_checkpoint_bootstrap_c23.py"].decode("utf-8")
    start,end = body.index("def validate_actual_a08_index_v1("),body.index("def verify_cold_profile(spec):")
    require(start<end, "exact A09 bridge block")
    old=next(n for n in ast.parse(body).body if isinstance(n,ast.FunctionDef) and n.name=="validate_actual_a08_index_v1")
    body = body[:start]+ast.get_source_segment(body,old)+"\n\n"+bridge_source(plan)+body[end:]
    body = prior.swap(body.encode(),"and close['checkpoint'] == pre['checkpoint']","and migration_checkpoint(pre,close,checked)",1)
    source["root_checkpoint_bootstrap_c23.py"] = body
    body = source["root_p37c23_cold_resume.py"]
    body = prior.swap(body,"from root_c23_a03_source_abort_checkpoint_inputs import validate_saved_seed",
        "from root_checkpoint_bootstrap_c23 import validate_saved_seed_a10",1)
    body = prior.swap(body,"validate_saved_seed(historical_saved_basis_view(admission),", "validate_saved_seed_a10(admission,",1)
    body = prior.swap(body,"and close['checkpoint'] == seed['actual_saved_checkpoint']", "and migration_checkpoint(pre,close,checked)",1)
    body = prior.swap(body,"    for ref in pre['sidecars']:\n        checked(ref)\n","",1)
    body = prior.swap(body,"from root_c23_a03_source_abort_checkpoint_inputs import validate_frozen_business",
        "from root_checkpoint_bootstrap_c23 import validate_source27_frozen_business",1)
    body = prior.swap(body,"validate_frozen_business(admission, freeze, checked)", "validate_source27_frozen_business(admission, freeze, checked)",1)
    body = prior.swap(body,"from root_checkpoint_bootstrap_c23 import validate_post_sem_driver,historical_saved_basis_view",
        "from root_checkpoint_bootstrap_c23 import validate_post_sem_driver,historical_saved_basis_view,migration_checkpoint",1)
    factory = "def make_normal_checkpoint_cold_queue_v1("
    text = body.decode("utf-8")
    node = next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=="make_normal_checkpoint_cold_queue_v1")
    lines=text.splitlines(keepends=True)
    at=sum(len(line) for line in lines[:node.body[0].lineno-1])
    hook = r'''    import sys
    from root_a10_observe_halted_state_v1 import install
    module=sys.modules[env['__name__']]
    require(vars(module) is env,'actual Queue factory namespace')
    admission=env['read'](Path(admission_path),65536)
    current=checked(admission['sdk_freeze'],524288)
    policy=checked(current['canonical_preload_policy'],32768)
    queue_pin=next(digest for path,digest in policy['entry_source_pins'] if Path(path).resolve()==Path(module.__file__).resolve())
    install(module,expected_queue_sha256=queue_pin)
'''
    text=text[:at]+hook+text[at:]
    source["root_p37c23_cold_resume.py"] = text.encode()
    for name,body in source.items():
        if name.endswith(".py"):compile(body,name,"exec")
    return source, {"schema":"xar.A10-Source27-source/v1","machine_id":MACHINE,"feeder":{},
        "actual_source_rows":[rows[U9/n] for n in names],"runtime_source_output_names":sorted(source),
        "supplemental_import_rows":[rows[U9/Path(r["path"]).name] for r in quote["sources"]["supplemental_import_rows"]],
        "staging_files":[stage_refs[n] for n in STAGE_NAMES],
        "mutable_OBS_config_observations":mutable,"new_day_credit":0}

def ram_supervisor_spec(owner, **kw):
    path=STAGING/"interactive_task_owner_a10_v1.py"
    raw=exact(path,(30672,"7a36400ef563d05dcc309900e51970a87fcf5c01a09f6b92643c57ca3b2ec51b"))
    module=prior._module(path,"_a10_exact_typed_owner")
    node=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=="prepare_spec")
    nonce=[n for n in ast.walk(node) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="nonce" for t in n.targets)]
    require(len(nonce)==1,"typed original nonce assignment")
    nonce[0].value=ast.Name(id="task_nonce",ctx=ast.Load())
    node.args.kwonlyargs.append(ast.arg(arg="task_nonce"))
    node.args.kw_defaults.append(ast.Constant(value=None))
    cut=next(i for i,n in enumerate(node.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)
        and isinstance(n.value.func,ast.Attribute) and isinstance(n.value.func.value,ast.Name)
        and n.value.func.value.id=="root" and n.value.func.attr=="mkdir")
    node.body=node.body[:cut]+[ast.Return(value=ast.Name(id="spec",ctx=ast.Load()))]
    node.returns=None
    tree=ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[]))
    stage=Path(kw["stage"]).resolve();boot=U10/"interactive_task_owner_a10_v1.py"
    def mapped_sha(path):
        p=Path(path).resolve()
        return prior.sha(kw["stage_raw"]) if p==stage else prior.sha(raw) if p==boot else module.sha(p)
    scope={**vars(module),"sha":mapped_sha}
    exec(compile(tree,"A10-original-typed-SPEC-RAM","exec"),scope)
    result=scope["prepare_spec"](root=kw["root"],role="supervisor",stage=stage,stage_sha256=prior.sha(kw["stage_raw"]),
        bootstrap_path=boot,cwd=kw["cwd"],machine_id=MACHINE,stage_args=["--clean-source-freeze",str(kw["clean"]),
        "--screen-admission",str(kw["screen"]),"--launch-config",str(kw["config"]),"--attempt","a10",
        "--attempt-nonce",kw["attempt"],"--task-nonce",kw["task"]],stop_path=U10/"STOP-OWNED-GAME-C23",
        pythonpath=str(kw["dependency_root"]),task_nonce=kw["task"])
    require(result["nonce"]==kw["task"] and result["bootstrap_sha256"]==prior.sha(raw),"exact typed future bootstrap SPEC")
    return result

def state_guard(plan):
    scope={"__file__":str(U10/"root_checkpoint_bootstrap_c23.py"),"MACHINE":MACHINE,"Path":Path,
        "require":require,"json":json,"hashlib":hashlib}
    exec(bridge_source(plan),scope)
    pre=prior.checked(plan["cold_prelaunch_ref"],16384)
    def original_helper():
        path=U9/"root_c23_a03_source_abort_checkpoint_inputs.py"
        raw=exact(path,(17637,"bae312f0fb07d370252ecc5714666fe1790a4db33bca32599e0e9bcb56d64a8e"))
        module=types.ModuleType("_a10_state_guard_source26_helper");module.__file__=str(path)
        exec(compile(raw,str(path),"exec"),vars(module))
        return module
    scope["_a10_helper"]=original_helper
    scope["validate_post_sem_driver"](pre,prior.checked(pre["final_driver_close"],16384),prior.checked)
    return {"machine_id":MACHINE,"cold_prelaunch":plan["cold_prelaunch_ref"],"driver_review":plan["driver_review_ref"],
        "environment_migration":plan["environment_migration_ref"],"actual_next_sequence":10521,
        "Driver_SAVE_body_hash_reads":0,"historical_saved_basis_next_sequence":10481}

def campaign_score_guard(*,alias_required=False):
    scope={**vars(prior),"MACHINE":MACHINE,"_a03_checked":prior.checked}
    exec(previous.previous.score_source(),scope)
    return scope["_a08_campaign_score"](U10,alias_required)

def compose(plan,*,display_values,display_review,companion_values):
    require((plan["full_storage_ref"]["bytes"],plan["full_storage_ref"]["sha256"])==FULL_PIN
        and plan["full_storage_ref"]==plan["live_storage_ref"]
        and Path(plan["compact_base_ref"]["path"]).resolve()==BASE27
        and (plan["compact_base_ref"]["bytes"],plan["compact_base_ref"]["sha256"])==BASE27_PIN,"one actual Source27 BASE/full02")
    source27_guard()
    source=get_function(prior,"compose",UNION_PIN).replace("C23-A05","C23-A10").replace("C23-A04","C23-A09").replace("'a05'","'a10'").replace("spec-supervisor-a05","spec-supervisor-a10")
    source=source.replace("2026-10-20T06:30:00+00:00","2026-10-20T12:30:00+00:00")
    source=source.replace("source26_canonical_anchor","source27_canonical_anchor").replace("xar.source26.","xar.source27.")
    seam="prior_failure_a04_unregistered=ref(O/'SUPERVISOR-A04-UNREGISTER.json'))"
    source=prior.swap(source.encode(),seam,seam[:-1]+",prior_failure_a09=ref(INDEX))",1).decode()
    source=prior.swap(source.encode(),"T5/name:raw(T4/name)","T5/name:(cold_prelaunch_bytes if name=='ROOT-C23-COLD-PRELAUNCH.json' else raw(T4/name))",1).decode()
    seam="policy_ref=put('ROOT-C23-CANONICAL-PRELOAD-POLICY-A05.json',policy)"
    addition="policy['runtime_import_source_pins']=[original.target_ref(T5/Path(r['path']).name,source[Path(r['path']).name]) for r in source_review['supplemental_import_rows']+source_review['staging_files']]\n    "
    source=prior.swap(source.encode(),seam,addition+seam,1).decode()
    original=types.SimpleNamespace(**vars(prior.original));original._ram_spec=ram_supervisor_spec
    scope={**vars(prior),"__file__":__file__,"T4":U9,"T5":U10,"INDEX":INDEX,"SOURCE26_PARENT":"394865df3259be5db29014ab1d17db7bdd48c21d",
        "build_sources":lambda:build_sources(plan),"state_guard":lambda:state_guard(plan),"original":original,
        "cold_prelaunch_bytes":prior.raw(plan["cold_prelaunch_ref"]["path"],16384),"CONTROL_SEQUENCE":10523}
    exec(compile(source,"A10-complete-union-RAM","exec"),scope)
    outputs,quote=scope["compose"](plan,display_values=display_values,display_review=display_review,companion_values=companion_values)
    _,staged=stage_values(plan)
    for row in quote["files"]:
        path=Path(row["path"])
        if path.parent==U10 and path.name in staged:
            row.update(mode="hardlink",source=staged[path.name],allocation_upper=0)
    quote["fresh_allocation_upper"]=sum(r["allocation_upper"] for r in quote["files"])
    quote["immutable_hardlinks"]=sum(r["mode"]=="hardlink" for r in quote["files"])
    quote["prepare_peak_upper"]=sum(quote[k] for k in ("fresh_allocation_upper","max_atomic_copy","future_owner_metadata_upper","control_probe_atomic_peak","intent_receipt_and_FS_upper"))
    require(len(outputs)==quote["unique_files"]==140,"complete A10 union 135+5")
    quote.update(campaign_score_junction=campaign_score_guard(),actual_A09_index=prior.ref(INDEX),
        new_first_sequence=10521,saved_basis_next_sequence=10481,unknown10519_credit=0,environment_migration=plan["environment_migration_ref"],control_probe_output_path=str(U10/"p37-queue/CONTROL-TIMING-10523.json"))
    quote["prerequisite_directories"].append(str(U10/"campaign-score"))
    return outputs,quote

def compose_plan(plan_ref: ExactRef) -> tuple[JSONObject,Outputs,JSONObject]:
    plan=prior.checked(plan_ref,131072)
    require(prior.ref(__file__)==plan["union_producer"],"exact A10 producer")
    path=Path(plan["display_producer"]["path"]).resolve()
    require(path==OWN/"prepare_source27_a10_display_v1.py"
        and (plan["display_producer"]["bytes"],plan["display_producer"]["sha256"])==DISPLAY_PIN
        and prior.ref(path)==plan["display_producer"],"exact A10 display producer")
    display=prior._module(path,"_a10_actual_display");v,r,c=display.compose(plan["display"])
    outputs,quote=compose(plan,display_values=v,display_review=r,companion_values=c)
    quote.update(adopter=prior.ref(__file__),input_plan=plan_ref,original_adopter_source=prior.ref(OWN/"adopt_c23_a05_union_v1.py"))
    return plan,outputs,quote

def adopt(plan_ref: ExactRef, quote_ref: ExactRef, card_ref: ExactRef) -> ExactRef:
    source=get_function(previous.previous,"adopt",previous.PREVIOUS_PIN).replace("A08","A10").replace("a08","a10")
    scope={**vars(previous.previous),"__file__":__file__,"U8":U10,"T5":U10,"compose_plan":compose_plan,
        "campaign_score_guard":campaign_score_guard,"metadata_source":metadata_source,"metadata_scope":metadata_scope}
    exec(compile(source,"A10-adopt-Root-only","exec"),scope)
    return scope["adopt"](plan_ref,quote_ref,card_ref)

def cold_owner(inputs: JSONObject) -> tuple[Outputs,JSONObject]:
    source=get_function(previous.previous,"cold_owner",previous.PREVIOUS_PIN).replace("A08","A10").replace("a08","a10")
    scope={**vars(previous.previous),"U8":U10,"T5":U10,"metadata_source":metadata_source,"metadata_scope":metadata_scope}
    exec(compile(source,"A10-current-cold-owner","exec"),scope)
    return scope["cold_owner"](inputs)
