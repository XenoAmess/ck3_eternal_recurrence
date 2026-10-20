"""Independent Source28/A12 preparation. Root alone adopts a new runtime."""
from __future__ import annotations
import ast, hashlib, json, sys, types
from pathlib import Path
sys.dont_write_bytecode = True
OWN = Path(__file__).resolve().parent
sys.path.insert(0, str(OWN))
import prepare_source27_a11_union_v1 as previous
from prepare_c23_a10_union_v1 import ExactRef, JSONObject, Outputs
from tools.g2_saved_campaign.file_stat_identity_v1 import (
    SCHEMA, normalize_file_stat_identity_v1, parse_file_stat_identity_v1)
import patch_observed_halt_close_loop_v1 as stop_patch
import patch_complete_tool_result_v1 as result_patch
old, prior = previous.old, previous.prior
MACHINE, O, T0 = previous.MACHINE, previous.O, previous.T0
U11, U12 = previous.U11, previous.U11.with_name("runtime-a12")
T5 = U12
require, exact = previous.require, previous.exact
PIN = (13790, "ed8aa98822ccfe9468f558081c81e210807ed588b7345c1fe29d93e3855c2eda")
PREPARED = O / "A11-PREPARED01.json"
PREPARED_PIN = (38307, "b1d58577d8c347bbacb16a620c1a0b5d8507c4d31d0a5f1dfa5dc636fc1e9599")
QUOTE = O / "source27-a11-prep01/A11-ROOT-QUOTE02.json"
QUOTE_PIN = (173615, "71eb23592d6baf46279393498e25ac96d24a54d7f6db9bed6e51ab036aa34b2d")
INDEX = U11 / "ROOT-A11-ACTUAL-CLOSURE-INDEX01.json"
INDEX_PIN = (3765, "ea4a5859aa3f862c1b58b32154655cc1e0df294dac3d48c7ada79144794302c5")
NEXT_PIN = (67, "259e69214a4987374eb0367d281d287970c2981748e1dc9f8a187b050af1be43")
LEDGER_PIN = (15703, "3cf0f4c49417096a194b96cf5a49c74d24afe63c98f678a438c74df25110fe28")
STATE_PIN = (9457, "81cbebfa0f5409e823e411cea062a85f988aadffe0ea33b17e51bab2d9fe33f6")
ROWS_PIN = (376075, "27fd27a2024fc95614877c45ba435a4dbcb72ea2c8b7d45c40dd73a12e3fe63b")

def replace_function(raw: bytes, name: str, replacement: str) -> bytes:
    text = raw.decode("utf-8")
    nodes = [n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == name]
    require(len(nodes) == 1, "one original function: " + name)
    original = ast.get_source_segment(text, nodes[0])
    require(isinstance(original, str) and text.count(original) == 1, "unique function bytes")
    return text.replace(original, replacement.rstrip(), 1).encode()

def closure_source(plan):
    return "A12_INDEX=" + repr(prior.ref(INDEX)) + "\nA12_LEDGER=" + repr(plan["continuity_predecessor_ref"]) + r'''
def validate_actual_a11_index_v1(reference,checked):
    require(reference==A12_INDEX,'actual closed A11 source required')
    x=checked(reference,16384)
    require(x['machine_id']==MACHINE and x['status']=='FAILED_CLOSED'
        and x['saved_days']==5429 and x['saved_cycles']==4753 and x['SAVE']==10480
        and x['unknown_request']==10534 and x['observed_zero_day_cycles']==5
        and x['late_observation_credit']==0 and x['Game_exit']==1 and x['sdk_exits']==[1,0]
        and x['recording_normal'] is True and x['early_helper_live_validated'] is False
        and x['campaign_wall_start']=='2026-10-19T03:26:49.420926Z','A11 unknown tail gives no new saved credit')
    docs={Path(r['path']).name:checked(r,16384) for r in x['references']}
    require(len(docs)==11,'all eleven actual closure facts')
    closed=docs['ROOT-FRESH-SUPERVISOR-CLOSED-C23-A11.json']
    require(closed['attempt_id']=='a11' and closed['cleanup_classification']=='FORCED_OWNED_GAME_CLEANUP'
        and closed['owned_cleanup']['ck3_pid']==256328 and closed['owned_cleanup']['job_active_processes_final']==0
        and closed['owned_cleanup']['cleanup_proven'] is True and closed['sdk_actual_exit']['normal'] is False
        and closed['keeper']['thread_exited'] is True,'actual A11 Game/SDK and keeper closed')
    osdoc=docs['ROOT-A11-FINAL-KERNEL-QUIESCENCE01.json']
    require(osdoc['machine_id']==MACHINE and osdoc['games']==[] and osdoc['active_related']==[],
        'actual OS closure belongs to machine and all owned processes absent')
    wrappers=[v for k,v in docs.items() if k.endswith('-UNREGISTER01.json')]
    require(len(wrappers)==3,'three old Tasks')
    for v in wrappers:
        require(v['returncode']==0 and v['stderr']=='','actual unregister returned')
        a=json.loads(v['stdout'])
        require(a['machine_id']==MACHINE and a['operation']=='unregister'
            and a['actual']['instances']==0 and a['actual']['absent_after'] is True,'old once-only Task actually absent')
    state=checked(A12_LEDGER,32768)
    require(state['status']=='repair_required' and state['window_id']==2
        and state['last_settled_cycles']==4758 and state['last_settled_date_raw']==53274624
        and state['start_date_raw']==53144328 and state['target_date_raw']==53407128
        and state['target_days']==10950,'same original window and unsaved five cycles')
    return closed
'''

def closure_guard(plan):
    exact(previous.__file__, PIN)
    previous.closure_guard()
    exact(INDEX, INDEX_PIN)
    reference = plan["continuity_predecessor_ref"]
    exact(reference["path"], LEDGER_PIN)
    require(Path(reference["path"]).resolve() != U11.parent / "ROOT-CONTINUITY-WINDOW.json", "immutable ledger archive required")
    namespace = dict(MACHINE=MACHINE, require=require, json=json, Path=Path)
    exec(closure_source(plan), namespace)
    closed = namespace["validate_actual_a11_index_v1"](prior.ref(INDEX), prior.checked)
    state = json.loads(exact(U11 / "p37-queue/ROOT-CUMULATIVE-LOOP-STATE.json", STATE_PIN))
    require(state["completed_cycles"] == 4758 and state["before"]["date_raw"] == 53274624
        and state["pending_cycle"]["global_turn"] == 4759
        and state["pending_cycle"]["auto_sequence"] == 10534
        and state["pending_cycle"]["stage"] == "auto_unsettled", "unknown10534 is not replayed")
    return closed

def source28_guard(plan):
    base=prior.checked(plan["compact_base_ref"],524288)
    anchor=prior.checked(plan["canonical_anchor_ref"],65536)
    require(base["source28_canonical_anchor"]==plan["canonical_anchor_ref"]
        and "canonical_preload_policy" not in base and base["runtime_admitted"] is False,"policy-free actual Source28")
    namespace=bridge_namespace(plan)
    namespace["validate_source28_frozen_business"](
        {"business_anchor":plan["canonical_anchor_ref"],"business_source_commit":base["business_source_commit"]},base,prior.checked)
    return base,anchor

def actual_graph(plan):
    closure_guard(plan)
    accepted = json.loads(exact(PREPARED, PREPARED_PIN))
    quote = json.loads(exact(QUOTE, QUOTE_PIN))
    require(accepted["machine_id"] == quote["machine_id"] == MACHINE
        and accepted["outputs"] == [{k:r[k] for k in ("path","bytes","sha256")} for r in quote["files"]]
        and len(accepted["outputs"]) == 140, "actual accepted A11 complete graph")
    profile = prior.checked(prior.ref(U11 / "ROOT-OBS-PROFILE-C23.json"))
    config, name = Path(profile["config_root"]), profile["profile_name"]
    mutable = {config/"basic/profiles"/name/"basic.ini", config/"basic/scenes"/(name+".json")}
    values, rows, observations = {}, {}, []
    for row in accepted["outputs"]:
        path = Path(row["path"]).resolve()
        if path in mutable:
            observations.append(prior.ref(path))
            continue
        if path == U11 / "NEXT-SEQUENCE-P37.json":
            body = exact(path, NEXT_PIN)
            require(json.loads(body)["next_sequence"] == 10538, "actual consumed A11 frontier")
        else:
            body = prior.raw(path, 524288)
            require(prior.ref(path) == row, "A11 immutable input changed: " + str(path))
        values[path], rows[path] = body, prior.ref(path)
    names = quote["sources"]["runtime_source_output_names"]
    require(len(values) == 138 and len(observations) == 2 and len(names) == len(set(names)) == 110, "only NEXT and OBS2 differ")
    return values, rows, quote, observations, names

def bridge_source(plan):
    text = old.bridge_source(plan)
    replacement = """def historical_saved_basis_view(admission):
    require(type(admission['next_sequence']) is int and admission['next_sequence']==10538
        and admission['environment_migration']==A10_MIGRATION_REF
        and admission['source27_anchor']==A10_SOURCE27_ANCHOR
        and admission['source28_anchor']==A12_SOURCE28_ANCHOR,'actual10538 and historical10481 are distinct')
    return {**admission,'next_sequence':10481}
"""
    text = replace_function(text.encode(), "historical_saved_basis_view", replacement).decode()
    text = prior.swap(text.encode(), "r,derived=_a10_migration(checked)", "r,derived=_a10_migration(checked)\n    validate_actual_a11_index_v1(A12_INDEX,checked)", 1).decode()
    text=prior.swap(text.encode(),"review=checked(A10_DRIVER_REVIEW_REF,32768);r,_=_a10_migration(checked)",
        "current_review=checked(A10_DRIVER_REVIEW_REF,32768)\n    historical_review=checked(A12_HISTORICAL_DRIVER_REVIEW,32768)\n    require(current_review['schema']=='xar.A12-closed-migrated-Driver-review/v1' and current_review['actual_A11_closure']==A12_INDEX and current_review['source_environment_migration_is_historical'] is True,'explicit current Driver over historical archive/environment')\n    review={**historical_review,**current_review};r,_=_a10_migration(checked)",1).decode()
    historical=old.P/"environment-migration01/ROOT-A10-DRIVER-REVIEW01.json"
    exact(historical,(13729,"ce4e1155763819b590572592d17f0bff5bd2ce8c30986f57c505b1f493c5a19f"))
    constants = {"A12_SOURCE28_BASE":plan["compact_base_ref"],
        "A12_SOURCE28_ANCHOR":plan["canonical_anchor_ref"], "A12_ROWS_PIN":ROWS_PIN,
        "A12_HISTORICAL_DRIVER_REVIEW":prior.ref(historical)}
    return text + "\n" + "\n".join(k+"="+repr(v) for k,v in constants.items()) + "\n" + closure_source(plan) + r'''
def validate_source28_business_anchor(anchor,checked):
    historical=checked(A10_SOURCE27_ANCHOR,65536)
    validate_source27_business_anchor(historical,checked)
    expected=checked(A12_SOURCE28_ANCHOR,65536)
    require(anchor==expected and anchor['schema']=='xar.source28.canonical-git-anchor/v1'
        and anchor['machine_id']==MACHINE and anchor['parent']==historical['commit']
        and anchor['status']=='CANONICAL_REF_CREATED_NOT_DEPLOYED'
        and anchor['actual_Source27_anchor']==A10_SOURCE27_ANCHOR
        and len(anchor['output_pins'])==14 and len(anchor['canonical_patch_rows'])==28
        and anchor['actual_Source27_BASE']==A10_SOURCE27_BASE,'exact actual Source28 authority over historical Source27')
    return anchor

def validate_source28_frozen_business(admission,freeze,checked):
    anchor=validate_source28_business_anchor(checked(A12_SOURCE28_ANCHOR,65536),checked)
    base=checked(A12_SOURCE28_BASE,524288);old=checked(A10_SOURCE27_BASE,524288)
    rows=freeze['files'];raw=json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    require(admission['business_anchor']==A12_SOURCE28_ANCHOR and freeze['machine_id']==MACHINE
        and freeze['business_source_commit']==admission['business_source_commit']==anchor['commit']
        and rows==base['files'] and len(rows)==1464 and sum(r['bytes'] for r in rows)==59279032
        and (len(raw),hashlib.sha256(raw).hexdigest())==A12_ROWS_PIN
        and anchor['complete_rows_JSON']=={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()},'complete actual Source28 rows')
    before={r['relative']:r for r in old['files']};after={r['relative']:r for r in rows}
    changed={n for n in after if before.get(n)!=after[n]}
    require(set(before)<=set(after) and len(set(after)-set(before))==2 and len(changed)==14
        and changed=={r['relative'] for r in anchor['output_pins']}
        and all(after[r['relative']]==r for r in anchor['output_pins']),'finite Source28 delta only')
    return anchor
'''

def check_identity(plan):
    exact(sys.modules[normalize_file_stat_identity_v1.__module__].__file__,
        (2642,"b5c267b11d2b2b7933eec7a62092e29ec2e0d80a8342cab0c7818009385653d0"))
    pre = prior.checked(plan["cold_prelaunch_ref"], 16384)
    review = prior.checked(plan["driver_review_ref"], 32768)
    require(pre["materialized_driver_review"] == plan["driver_review_ref"]
        and review["actual_A11_closure"] == prior.ref(INDEX)
        and review["driver_stat_schema"] == SCHEMA, "new actual OS-stat review over A11")
    stat = review["driver_stat"]
    expected = parse_file_stat_identity_v1(
        {"bytes":stat["size"],"file_id":stat["FileID"],"mtime_ns":stat["mtime_ns"]}, schema=SCHEMA)
    require(normalize_file_stat_identity_v1(Path(pre["driver_state"]["path"]).stat()) == expected, "current cold Driver identity")
    return pre

def bridge_namespace(plan):
    namespace=dict(__file__=str(U12/"root_checkpoint_bootstrap_c23.py"),MACHINE=MACHINE,
        require=require,json=json,hashlib=hashlib,Path=Path)
    exec(bridge_source(plan),namespace)
    namespace["_a10_helper"]=lambda:prior._module(U11/"root_c23_a03_source_abort_checkpoint_inputs.py","_a12_original_saved_helper")
    return namespace

def state_guard(plan):
    closure_guard(plan)
    pre=check_identity(plan)
    namespace=bridge_namespace(plan)
    namespace["validate_post_sem_driver"](pre,prior.checked(pre["final_driver_close"]),prior.checked)
    return {"machine_id":MACHINE,"cold_prelaunch":plan["cold_prelaunch_ref"],
        "driver_review":plan["driver_review_ref"],"actual_A11_index":prior.ref(INDEX),
        "actual_next_sequence":10538,"historical_saved_basis_next_sequence":10481,"Driver_SAVE_body_hash_reads":0}

def patch_feeder(raw, plan):
    text = raw.decode()
    constants = "\nA12_LEDGER_REF="+repr(plan["continuity_predecessor_ref"])+"\nA12_STATE_REF="+repr(prior.ref(U11/"p37-queue/ROOT-CUMULATIVE-LOOP-STATE.json"))+"\n"
    text = prior.swap(text.encode(), "def need(ok:bool,why:str)->None:", constants+"def need(ok:bool,why:str)->None:", 1).decode()
    for a,b,n in (
        ('source27_base:Ref;budget:Ref;', 'source27_base:Ref;source28_base:Ref;source28_anchor:Ref;prior_A11_index:Ref;budget:Ref;',1),
        ('"source27_base","budget"', '"source27_base","source28_base","source28_anchor","prior_A11_index","budget"',1),
        ('KIND="A10_SAVE10480_cold_environment_rollback_verified"', 'KIND="A12_SAVE10480_Source28_rollback_verified"',1),
        ('last_A10_SAVE10480_environment_rollback', 'last_A12_SAVE10480_Source28_rollback',1)):
        text = prior.swap(text.encode(), a, b, n).decode()
    start = text.index("ROLLBACK="); end = text.index("\n", start)
    text = text[:start]+'ROLLBACK={"saved_cycles":4753,"A11_settled_cycles":4758,"cycles_lost":5,"settled_days_lost":0,"unknown_AUTO":10534,"unknown_AUTO_credit":0}'+text[end:]
    text = replace_function(text.encode(), "old_basis", r'''def old_basis(a:Admit)->Json:
    r=a["sources"]["old_ledger"]
    need(r==A12_LEDGER_REF and Path(r["path"]).resolve()!=LEDGER.resolve(),"immutable A11 ledger")
    old=checked(r);q=checked(a["sources"]["old_state"]);pending=obj(q.get("pending_cycle"))
    need(a["sources"]["old_state"]==A12_STATE_REF and q.get("completed_cycles")==4758
        and obj(q.get("before")).get("date_raw")==53274624
        and matches(pending,{"global_turn":4759,"stage":"auto_unsettled","auto_sequence":10534,"before":q["before"]}),"unknown10534 never replayed")
    return old''').decode()
    text = replace_function(text.encode(), "source27", r'''def source27(a:Admit,cold:Json)->None:
    migration=checked(a["environment_migration"])
    need(migration.get("sdk_base")==a["source27_base"] and migration.get("source27_anchor")==a["source27_anchor"]
        and cold.get("environment_migration")==a["environment_migration"]
        and a["sources"]["environment_migration"]==a["environment_migration"],"historical Source27 environment")
    module=importlib.import_module("root_checkpoint_bootstrap_c23")
    getattr(module,"validate_actual_a11_index_v1")(a["prior_A11_index"],checked)
    freeze=checked(file_ref(cold.get("sdk_freeze")));base=checked(a["source28_base"])
    need(base.get("source28_canonical_anchor")==a["source28_anchor"]
        and freeze.get("source_root")==base.get("source_root")
        and freeze.get("business_source_commit")==base.get("business_source_commit"),"actual Source28")
    getattr(module,"validate_source28_frozen_business")(cold,freeze,checked)''').decode()
    return text.encode()

def build_sources(plan):
    values, rows, quote, mutable, names = actual_graph(plan)
    source = {n:values[U11/n] if n in old.STAGE_NAMES else values[U11/n].replace(b"C23-A11", b"C23-A12") for n in names}
    bootstrap = source["root_checkpoint_bootstrap_c23.py"]
    first=bootstrap.index(b"A10_MIGRATION_REF=")
    last=bootstrap.index(b"A11_A10_INDEX=",first)
    bootstrap=bootstrap[:first]+bridge_source(plan).encode()+bootstrap[last:]
    source["root_checkpoint_bootstrap_c23.py"] = bootstrap
    body = source["root_native30_supervisor_c23.py"]
    for a,b,n in (("args.attempt=='a11'","args.attempt=='a12'",1),("value.get('attempt_id')=='a11'","value.get('attempt_id')=='a12'",1),
        ('choices=("a11",)','choices=("a12",)',1),('"attempt_id":"a11"','"attempt_id":"a12"',2),
        ("_validate_a11_attempt(args, config)","_validate_a12_attempt(args, config)",1),
        ("    require(read(N/'NEXT-SEQUENCE-P37.json')['next_sequence']==10521,'new A10 consumes actual NEXT10521 once')\n","",1)):
        body = prior.swap(body,a,b,n)
    guard = r'''
def _validate_a12_attempt(args,config):
    value=_validate_a11_attempt(args,config)
    from root_checkpoint_bootstrap_c23 import validate_actual_a11_index_v1
    closed=validate_actual_a11_index_v1(value['prior_failure_a11'],_a03_checked)
    require(read(N/'NEXT-SEQUENCE-P37.json')['next_sequence']==10538,'new A12 actual10538 once')
    require(args.attempt_nonce not in (closed['attempt_nonce'],closed['task_nonce'])
        and args.task_nonce not in (closed['attempt_nonce'],closed['task_nonce']),'independent A12 nonces')
    return value

'''
    body = prior.swap(body, "def main(args):", guard+"def main(args):", 1)
    exact(stop_patch.__file__, (3258,"577bd28fa07f049bb72fddd7d98acec34692a36c7b0678556677d54cc54e7c75"))
    source["root_native30_supervisor_c23.py"] = stop_patch.patch_observed_halt_close_loop_v1(body)
    exact(result_patch.__file__, (2176,"af5f280980a41f99098e8d393925c8d20f22e39901dc1bfc8445dd91da5934f2"))
    source["root_p37c23_sdk_queue.py"] = result_patch.transform(source["root_p37c23_sdk_queue.py"])
    source["launch_a10_saved10480_feeder01.py"] = patch_feeder(source["launch_a10_saved10480_feeder01.py"], plan)
    source["root_p37c23_cold_resume.py"] = prior.swap(source["root_p37c23_cold_resume.py"],
        "validate_source27_frozen_business", "validate_source28_frozen_business", 2)
    for name, body in source.items():
        if name.endswith(".py"): compile(body,name,"exec")
    return source, {"schema":"xar.A12-Source28-source/v1","machine_id":MACHINE,"feeder":{},
        "actual_source_rows":[rows[U11/n] for n in names],"runtime_source_output_names":names,
        "supplemental_import_rows":quote["sources"]["supplemental_import_rows"],
        "staging_files":[rows[U11/n] for n in old.STAGE_NAMES],"mutable_OBS_config_observations":mutable,
        "actual_A11_index":prior.ref(INDEX),"new_day_credit":0,
        "preparation_helper_refs":[prior.ref(m.__file__) for m in
            (stop_patch,result_patch,sys.modules[normalize_file_stat_identity_v1.__module__])]}


def metadata_source(source):
    source = old.metadata_source(source)
    for a,b,n in (("'next_sequence':10521","'next_sequence':10538",3),
        (".get('next_sequence')==10521",".get('next_sequence')==10538",1),
        ("source27_canonical_anchor","source28_canonical_anchor",1),
        ("validate_source27_business_anchor","validate_source28_business_anchor",1),
        ("validate_source27_frozen_business","validate_source28_frozen_business",2),
        ("'source27_anchor':A10_SOURCE27_ANCHOR","'source27_anchor':A10_SOURCE27_ANCHOR,'source28_anchor':A12_SOURCE28_ANCHOR",1)):
        source = prior.swap(source.encode(),a,b,n).decode()
    timing = "'control_timing_not_enabled':False,'control_timing':{'schema':'xar.ck3.queue-control-timing-admission/v1','enabled':True,'machine_id':MACHINE,'control_sequence':10523,'cycle_budget':30}}"
    disabled = "'control_timing_not_enabled':True}"
    counts = source.count(timing), source.count(disabled)
    require(counts in ((1, 0), (0, 1)), "one exact cold-owner or disabled startup timing shape")
    return prior.swap(source.encode(), timing, disabled, 1).decode() if counts[0] else source

def metadata_scope(scope, runtime):
    old.metadata_scope(scope, runtime)
    bootstrap = prior._module(runtime/"root_checkpoint_bootstrap_c23.py", "_a12_actual_business_bridge")
    for name in ("validate_source28_business_anchor","validate_source28_frozen_business","A12_SOURCE28_ANCHOR"):
        scope[name] = getattr(bootstrap,name)

def campaign_score_guard(*, alias_required=False):
    return types.FunctionType(old.campaign_score_guard.__code__,dict(vars(old),U10=U12))(alias_required=alias_required)

def scope(plan=None):
    env = dict(vars(old), __file__=__file__, U9=U11,U10=U12,T5=U12,build_sources=build_sources,
        state_guard=state_guard,metadata_source=metadata_source,metadata_scope=metadata_scope,
        campaign_score_guard=campaign_score_guard,compose_plan=compose_plan)
    ram = old.get_function(old,"ram_supervisor_spec",previous.PIN)
    ram = prior.swap(ram.encode(),'"--attempt","a10"','"--attempt","a12"',1).decode()
    exec(compile(ram,"A12-typed-SPEC-RAM","exec"),env)
    if plan is not None:
        full = prior.checked(plan["full_storage_ref"],65536)
        env.update(BASE27=Path(plan["compact_base_ref"]["path"]).resolve(),
            BASE27_PIN=(plan["compact_base_ref"]["bytes"],plan["compact_base_ref"]["sha256"]),
            FULL_PIN=(plan["full_storage_ref"]["bytes"],plan["full_storage_ref"]["sha256"]),
            source27_guard=lambda:source28_guard(plan))
    return env

def compose(plan, *, display_values, display_review, companion_values):
    source28_guard(plan)
    text = old.get_function(old,"compose",previous.PIN)
    full = prior.checked(plan["full_storage_ref"],65536)
    for a,b,n in (('.replace("C23-A05","C23-A10")','.replace("C23-A05","C23-A12")',1),
        ('.replace("C23-A04","C23-A09")','.replace("C23-A04","C23-A11")',1),
        (".replace(\"'a05'\",\"'a10'\")",".replace(\"'a05'\",\"'a12'\")",1),
        ('.replace("spec-supervisor-a05","spec-supervisor-a10")','.replace("spec-supervisor-a05","spec-supervisor-a12")',1),
        ('source27_canonical_anchor','source28_canonical_anchor',1),('xar.source27.','xar.source28.',1),
        ("2026-10-20T12:30:00+00:00",full["review_at_utc"],1),
        ("prior_failure_a09=ref(INDEX))","prior_failure_a09=ref(INDEX),prior_failure_a10=A10_INDEX,prior_failure_a11=A12_INDEX)",1),
        ('"INDEX":INDEX','"INDEX":INDEX,"A10_INDEX":A10_INDEX,"A12_INDEX":A12_INDEX',1),
        ('"394865df3259be5db29014ab1d17db7bdd48c21d"','"4b0f3771b51d65af2cd6d576116535237aac7ef0"',1),
        ("if path.parent==U10 and path.name in staged:","if path.parent==U10 and path.name in staged and outputs[path]==prior.raw(staged[path.name]['path'],32768):",1)):
        text = prior.swap(text.encode(),a,b,n).decode()
    env = scope(plan)
    env.update(A10_INDEX=prior.ref(previous.INDEX),A12_INDEX=prior.ref(INDEX))
    exec(compile(text,"A12-complete140-union","exec"),env)
    outputs, quote = env["compose"](plan,display_values=display_values,display_review=display_review,companion_values=companion_values)
    quote.update(schema="xar.C23-A12-union-prepare-quote/v1",actual_A11_index=prior.ref(INDEX),
        new_first_sequence=10538,unknown10534_credit=0,rollback_cycles=5,rollback_days=0,
        control_probe_sequence=None,control_probe_output_path=None,new_timing_enabled=False)
    return outputs, quote

def compose_plan(plan_ref: ExactRef) -> tuple[JSONObject, Outputs, JSONObject]:
    plan = prior.checked(plan_ref,131072)
    require(prior.ref(__file__)==plan["union_producer"],"exact A12 producer")
    values, review, companions = display_compose(plan)
    outputs, quote = compose(plan,display_values=values,display_review=review,companion_values=companions)
    quote.update(adopter=prior.ref(__file__),input_plan=plan_ref,
        original_adopter_source=prior.ref(OWN/"adopt_c23_a05_union_v1.py"))
    return plan, outputs, quote

def adopt(plan_ref: ExactRef, quote_ref: ExactRef, card_ref: ExactRef) -> ExactRef:
    text = old.get_function(old,"adopt",previous.PIN).replace("A10","A12").replace("a10","a12")
    env = scope();exec(compile(text,"A12-Root-only-adopt","exec"),env)
    return env["adopt"](plan_ref,quote_ref,card_ref)

def cold_owner(inputs: JSONObject) -> tuple[Outputs, JSONObject]:
    text = old.get_function(old,"cold_owner",previous.PIN).replace("A10","A12").replace("a10","a12")
    env = scope();exec(compile(text,"A12-cold-owner","exec"),env)
    return env["cold_owner"](inputs)

CAPTURE_PIN = (73689,"89e7d416bc03863b50e17a4946e77bcc35207081677b7f4f7d34374f1c97efa5")
NEW_CAPTURE_PIN = (76250,"1b7fad4f9497c0f1f78e73be24a8effc9b0f043080005f151c5dd9257958173a")
CAPTURE_HELPERS = "def _require_game_client_1280_v1(client_rect):\n    if (not isinstance(client_rect, (tuple, list)) or len(client_rect) != 4\n            or any(type(value) is not int for value in client_rect)\n            or tuple(client_rect) != (0, 0, 1280, 720)):\n        raise RuntimeError(\"owned Game client must remain exactly 1280x720\")\n\n\ndef _game_canvas_transform_v1():\n    return {\"positionX\": 0.0, \"positionY\": 0.0, \"alignment\": 5,\n            \"scaleX\": 2.0, \"scaleY\": 2.0, \"rotation\": 0.0,\n            \"cropLeft\": 0, \"cropRight\": 0, \"cropTop\": 0, \"cropBottom\": 0,\n            \"boundsType\": \"OBS_BOUNDS_NONE\"}\n\n\ndef _owned_game_scene_item_v1(client, scene, source):\n    item_id = client.get_scene_item_id(scene, source).scene_item_id\n    rows = client.get_scene_item_list(scene).scene_items\n    matched = [row for row in rows if row.get(\"sourceName\") == source]\n    if (type(item_id) is not int or item_id < 0 or len(matched) != 1\n            or matched[0].get(\"sceneItemId\") != item_id\n            or matched[0].get(\"sceneItemEnabled\") is not True):\n        raise RuntimeError(\"owned Game scene item identity changed\")\n    return item_id\n\n\ndef _verify_game_canvas_v1(client, scene, source, item_id, client_rect):\n    _require_game_client_1280_v1(client_rect)\n    if _owned_game_scene_item_v1(client, scene, source) != item_id:\n        raise RuntimeError(\"owned Game scene item id changed\")\n    actual = client.get_scene_item_transform(scene, item_id).scene_item_transform\n    expected = _game_canvas_transform_v1()\n    if any(actual.get(key) != value for key, value in expected.items()):\n        raise RuntimeError(\"owned Game canvas transform changed\")\n    return {key: actual[key] for key in expected}\n\n\ndef _configure_game_canvas_v1(client, scene, source, client_rect):\n    _require_game_client_1280_v1(client_rect)\n    item_id = _owned_game_scene_item_v1(client, scene, source)\n    client.set_scene_item_transform(scene, item_id, _game_canvas_transform_v1())\n    return item_id, _verify_game_canvas_v1(client, scene, source, item_id, client_rect)\n\n\n"

def capture_variant(raw: bytes) -> bytes:
    require((len(raw),prior.sha(raw))==CAPTURE_PIN,"exact original capture source")
    text=raw.decode("utf-8")
    patches=(
        ("def run_worker(path):",CAPTURE_HELPERS+"def run_worker(path):"),
        ('            check_game_window(game, job["hwnd"])',
         '            check_game_window(game, job["hwnd"])\n            _require_game_client_1280_v1(win32gui.GetClientRect(job["hwnd"]))'),
        ('            by_name = {row["sourceName"]: row for row in items}',
         '            by_name = {row["sourceName"]: row for row in items}\n            _verify_game_canvas_v1(client, profile["profile_name"], source, game_id, win32gui.GetClientRect(job["hwnd"]))'),
        ('            client.create_input(scene, source, "game_capture", game_settings, True)',
         '            client.create_input(scene, source, "game_capture", game_settings, True)\n            game_id, game_transform = _configure_game_canvas_v1(\n                client, scene, source, win32gui.GetClientRect(job["hwnd"]))'),
        ('                "source_settings": client.get_input_settings(source).input_settings,',
         '                "source_settings": client.get_input_settings(source).input_settings,\n                "game_scene_item_id": game_id,\n                "game_transform": _verify_game_canvas_v1(client, scene, source, game_id, win32gui.GetClientRect(job["hwnd"])),'))
    for a,b in patches:text=prior.swap(text.encode(),a,b,1).decode()
    inverse=text
    for a,b in reversed(patches):inverse=prior.swap(inverse.encode(),b,a,1).decode()
    out=text.encode()
    require(inverse.encode()==raw and (len(out),prior.sha(out))==NEW_CAPTURE_PIN,"finite capture transform")
    compile(out,"A12-capture-variant","exec")
    return out

def predecessor(plan):
    d=previous.display_module()
    refs,forbidden=d.predecessor()
    old_closed=previous.closure_guard()
    closed=closure_guard(plan)
    profile=prior.checked(prior.ref(U11/"ROOT-OBS-PROFILE-C23.json"))
    forbidden.update((old_closed["attempt_nonce"],old_closed["task_nonce"],
        "807f943bfbed4552992431e6c1fd56c4",closed["attempt_nonce"],closed["task_nonce"],profile["A11_display_nonce"]))
    index=prior.checked(prior.ref(INDEX))
    for row in index["references"]:
        if row["path"].endswith("-UNREGISTER01.json"):
            doc=json.loads(prior.checked(row)["stdout"])
            require(doc["task_name"].startswith("XARG2ManagedOwner-"),"exact Task owner")
            forbidden.add(doc["task_name"].split("-",1)[1])
    return [*refs,prior.ref(previous.INDEX),prior.ref(INDEX)],forbidden

def display_compose(plan):
    d=previous.display_module();b=d.base
    refs,forbidden=predecessor(plan)
    require(plan["display"]["display_nonce"] not in forbidden,"fresh A12 display nonce")
    require(prior.ref(d.__file__)==plan["display_producer"],"exact prior display primitive")
    d.source(Path(b.__file__),d.prior.PRIOR_PIN)
    profile=prior.checked(prior.ref(U11/"ROOT-OBS-PROFILE-C23.json"))
    edits={
        "spec['generation'] == 'C23-A05'":"spec['generation'] == 'Source27-A11'",
        "spec.update(generation='C23-A06', target_runtime=str(T6), display_nonce=display_nonce)":
            "spec.update(generation='Source28-A12', target_runtime=str(T6), display_nonce=display_nonce, previous_Game_tuple=[256328,134369704160368681])",
        "A06_display_nonce=display_nonce":"A12_display_nonce=display_nonce",
        "profile.pop('A05_display_nonce', None)":"profile.pop('A11_display_nonce', None)",
        "xar.C23-A06-complete-display-RAM-review/v1":"xar.Source28-A12-complete-display-RAM-review/v1",
        "xar.C23-A06-display-prepare-input/v1":"xar.Source28-A12-display-prepare-input/v1",
        "spec['previous_Game_tuple'] == list(prior.OLD_GAME)":"spec['previous_Game_tuple'] == [139908,134369688444824386]"}
    patches=tuple((a,edits.get(a,z)) for a,z in b.PATCHES)+(
        ("profile['storage_review_at_utc'] == REVIEW_AT","profile['storage_review_at_utc'] == '2026-10-20T12:30:00+00:00'"),)
    p=prior.ref(U11/"ROOT-OBS-PROFILE-C23.json")
    env=dict(b.recipe.__globals__,U7=U11,U8=U12,TASK8=O/"tasks/spec-display-a12",
        QUOTE7=QUOTE,QUOTE7_PIN=QUOTE_PIN,PROFILE7_PIN=(p["bytes"],p["sha256"]),
        DISPLAY7_NONCE=profile["A11_display_nonce"],PATCHES=patches)
    namespace,recipe_ref=types.FunctionType(b.recipe.__code__,env)()
    full=prior.checked(plan["full_storage_ref"],65536)
    namespace.update(REVIEW_AT=full["review_at_utc"],FULL5_SHA=old.FULL_PIN[1])
    values,review,companions=namespace["compose"](plan["display"])
    capture="presentation-c23/ck3_obs_capture_png_retry_c23.py"
    values[capture]=capture_variant(values[capture])
    owner=next(n for n in values if n.endswith("start_new_game_display.py"))
    body=values[owner]
    for a,z,n in (("len(raw)==73689","len(raw)==76250",2),(CAPTURE_PIN[1],NEW_CAPTURE_PIN[1],3),
        ("    parser.add_argument('--game-birth',type=int,required=True)",
         "    parser.add_argument('--game-birth',type=int,required=True)\n    parser.add_argument('--child-import-timeout-seconds',type=int,choices=(120,),default=120)",1),
        ("timeout=30,creationflags=","timeout=a.child_import_timeout_seconds,creationflags=",1)):
        body=prior.swap(body,a,z,n)
    values[owner]=body
    manifest_name="presentation-c23/SOURCE-PINS-C23.json"
    manifest=json.loads(values[manifest_name])
    for row in manifest["files"]:
        name=row["relative_path"]
        if name.startswith("@frozen-host/"):continue
        require(name in values and name!=manifest_name,"complete runtime manifest row")
        row.update(path=str(U12/name),bytes=len(values[name]),sha256=prior.sha(values[name]))
    require(len(manifest["files"])==18,"eighteen manifest rows including original external validator")
    values[manifest_name]=(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n").encode()
    for name,raw in values.items():
        if name.endswith(".py"):compile(raw,name,"exec")
    review["files"]=[{**row,"bytes":len(values[row["relative_path"]]),"sha256":prior.sha(values[row["relative_path"]])} for row in review["files"]]
    review.update(changed_exact_three=None,changed_exact_four=[capture,owner,"ROOT-DECISION-TEXT-PROVIDER-C23.json",manifest_name],
        unchanged_source_leaves=14,source_graph_bytes=sum(map(len,values.values())),
        continuity_predecessor_ref=plan["continuity_predecessor_ref"],capture_live_qualified=False)
    review["inputs"].extend([*refs,recipe_ref,plan["union_producer"]])
    return values,review,companions

def build_task_spec(display_values: dict[str,bytes], display_review: JSONObject, *, task_nonce: str,
                    game_launch_ref: ExactRef, placement_ref: ExactRef, bootstrap_ref: ExactRef,
                    owner_contract_ref: ExactRef) -> tuple[Outputs,JSONObject]:
    d=previous.display_module()
    guard=lambda:predecessor({"continuity_predecessor_ref":display_review["continuity_predecessor_ref"]})
    binder=types.FunctionType(d.build_task_spec.__code__,dict(d.build_task_spec.__globals__,
        U10=U12,TASK10=O/"tasks/spec-display-a12",GAME9=[256328,134369704160368681],predecessor=guard))
    return binder(display_values,display_review,task_nonce=task_nonce,game_launch_ref=game_launch_ref,
        placement_ref=placement_ref,bootstrap_ref=bootstrap_ref,owner_contract_ref=owner_contract_ref)
