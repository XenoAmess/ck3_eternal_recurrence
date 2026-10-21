"""Close the independent public source bundle; no runtime or grant is produced."""
from __future__ import annotations
import ast,hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BASE=Path('C:/ck3-e04-resume-20261020-a01')

def pin(path: Path) -> dict[str,object]:
    raw=path.read_bytes()
    return {'path':str(path.resolve()),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def save(name: str,value: object) -> Path:
    path=ROOT/name
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,indent=2,ensure_ascii=False);stream.write('\n')
    return path

def main() -> None:
    if datetime.now(timezone.utc)>=datetime(2026,10,21,2,30,tzinfo=timezone.utc):raise ValueError('Expired source scope')
    sys.path.insert(0,'D:/workspace/ck3_eternal_recurrence/tools')
    from ck3_live_run_id import current_machine_id
    machine=current_machine_id()
    if machine!='desktop-3fevhd2-1c74096080':raise ValueError('Wrong actual machine')
    index=ROOT/'PUBLIC-SOURCE-INDEX.prepared-a04.json'
    bundle=json.loads(index.read_bytes())
    for ref in bundle['files']:
        if pin(Path(ref['path']))!=ref:raise ValueError('Index source changed')
    new_names=['postload_admission.py','prepare_parent_postload_admission.py','consume_parent_postload_actual.py','postload_root_scope.py']
    production=[]
    for name in new_names:
        path=ROOT/'candidate/native-tools'/name
        ast.parse(path.read_bytes(),filename=str(path))
        production.append({'source':pin(path),'repository_relative_path':
            'ck3_autonomous_player/native_bridge/research/maintenance_writer_cold_12004/'+name})
    for name in ['postload_public_models.py','r08_parent_postload_controller.py','r08_parent_postload_one_day.py',
                 'postload_bundle_loader.py','r08_postload_adapter.py','r08_postload.json']:
        path=ROOT/'candidate/tools/ck3_mod_acceptance_cases'/name
        if path.suffix=='.py':ast.parse(path.read_bytes(),filename=str(path))
        production.append({'source':pin(path),'repository_relative_path':'tools/ck3_mod_acceptance_cases/'+name})
    native=BASE/'r08-post-window-source-0130-a01/native-postload-a01'
    old_freeze=native/'SOURCE-FREEZE.actual-a01.json'
    if pin(old_freeze)['sha256']!='80c722a71e596d4cc3e2410042a80e6c897e9baa6918c833626f41f8f71a266e':raise ValueError('Fork source changed')
    typed=[]
    for name in ['postload_models.py','postload_wire.py','postload_owner_binding.py','parent_postload_contract.py']:
        original=pin(native/'candidate-a01'/name);copied=pin(ROOT/'candidate/native-tools'/name)
        if (original['bytes'],original['sha256'])!=(copied['bytes'],copied['sha256']):raise ValueError('Typed core fork drift')
        typed.append({'source':original,'unchanged_local_copy':copied})
    checks=[]
    for directory in sorted(ROOT.glob('checks-*')):
        path=directory/'ORIGINAL-WAIT.actual.json'
        value=json.loads(path.read_bytes())
        for key in ('stdout','stderr'):
            if pin(Path(value[key]['path']))!=value[key]:raise ValueError('Original check log changed')
        checks.append({'receipt':pin(path),'original_wait_returncode':value['original_wait_returncode'],
            'original_pid':value['original_pid'],'creation_time_100ns':value['creation_time_100ns']})
    final=[]
    for label in ('focused','mypy'):
        path=ROOT/('checks-'+label+'-final-a01/ORIGINAL-WAIT.actual.json')
        value=json.loads(path.read_bytes())
        if value['original_wait_returncode']!=0:raise ValueError('Final checks not PASS')
        for ref in value['sources']:
            if pin(Path(ref['path']))!=ref:raise ValueError('Final check source drift')
        final.append(pin(path))
    test_source=ROOT/'test_postload_public.py'
    test_ast=ast.parse(test_source.read_bytes())
    count=sum(isinstance(node,ast.FunctionDef) and node.name.startswith('test_') for node in ast.walk(test_ast))
    if count!=15:raise ValueError('Unexpected finite check method count')
    if list((ROOT/'tmp').rglob('*')):raise ValueError('Owned temporary files remain')
    contract=save('PUBLIC-SOURCE-CONTRACT.prepared-a01.json',{
        'schema':'xar.e04.postload.public-source-contract.v1','machine_id':machine,
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),
        'mode':'player-parent-postload-execution-once-v1','raw_schema':'xar.maintenance.parent_postload.raw.v1',
        'public_case_key':'r08_parent_postload_one_day','planner_autoload':False,
        'Q_schema':'xar.maintenance.parent_postload.qualification.v1',
        'Q_status':'SELECTED_POSTLOAD_EXECUTION_COLD_PASS',
        'Q_fields':['schema','status','mode','machine_id','observer_pin','target_pin','source_pins',
            'SYSTEM_receipt_pin','cold_suite_pin','Root_acceptance_pin'],
        'Root_cold_acceptance_schema':'xar.maintenance.parent_postload.root-cold-acceptance.v1',
        'Root_scope_schema':'xar.maintenance.parent_postload.root-scope.v1',
        'Root_authorization_schema':'xar.maintenance.parent_postload.conditional-root-authorization.v1',
        'Game_financial_schema':'xar.capacity.parent-postload.game-financial.v1',
        'actual_Game_financial_card_exists':False,'generic_source_planning_card_ineligible':True,
        'actual_native_Q_exists':False,'old_entry17_pointer21_Q_ineligible':True,
        'native_source_fork_only':pin(old_freeze),'native_live_keys_successor_frozen':False,
        'native_live_protocol_expected_keys':35,
        'missing':['Final reviewed native live-key successor and native runner/build/SYSTEM/cold/Q',
            'Future complete public runtime/import closure and original normal S0/plain profile inputs',
            'Fresh separate scene financial admission and explicit Root conditional execution authority'],
        'close_reserve_seconds':1050,'owner_pair_max_age_seconds':30,'OS_read_max_age_seconds':5,
        'Root_scope_lifetime_max_seconds':30,'prewatcher':True,
        'prewatcher_reserve':'min(original report hold, scene deadline) >=1050, original hold re-read before signal',
        'day_and_target_independent':True,'opportunity_complete':False,'full_R08':False,
        'paid_maintenance_raw':None,'payer':None,'cadence':None,'entryExact':False,
        'common_original_int64_producer_unchanged':True,'new_postload_u64_wire':'canonical unsigned decimal strings'})
    template=save('ROOT-AUTHORIZATION.source-template-a01.json',{
        'schema':'xar.e04.postload.conditional-authorization-template.v1','machine_id':machine,
        'not_an_actual_Root_scope_or_execution_grant':True,
        'authorization':{'schema':'xar.maintenance.parent_postload.conditional-root-authorization.v1',
            'machine_id':machine,'run_id':None,'execute_after_actual_awaiting':False,
            'ready_context_pin':None,'runtime_pin':None,'prepared_pin':None,'frozen_argv_pin':None,
            'bundle_index_pin':pin(index),'helper_pin':pin(ROOT/'candidate/native-tools/postload_root_scope.py'),
            'qualification_pin':None,'observer_pin':None,'Game_capacity_pin':None,'game_exe_path':None,
            'root_scope_path':None,'deadline_utc':None,
            'declarations':{'one_original_window_only':False,'no_replay_unknown':False,'postload_execution_reviewed':False}}})
    override=save('EXTERNAL-PUBLIC-CASE.source-fragment-a01.json',{
        'source_only_not_a_complete_product_catalog':True,'ordinary_planner_autoload':False,
        'adapter':{'path':str(ROOT/'candidate/tools/ck3_mod_acceptance_cases/r08_postload_adapter.py'),
            'config':str(ROOT/'candidate/tools/ck3_mod_acceptance_cases/r08_postload.json')},
        'actual_run_ready':False,'native_Q':None})
    readme=ROOT/'README.md'
    with readme.open('x',encoding='utf-8',newline='\n') as stream:stream.write('''# Independent postload public source bundle

This is source-only, on machine desktop-3fevhd2-1c74096080. No native build,
SYSTEM, cold EXE, SDK, Steam, Game, screen, allocation or profile preparation
was performed by this lane. The native successor/actual new Q is absent.
The new mode defaults to refusal; old entry17 and pointer21 Q cannot admit it.

The explicit external adapter follows the existing public Selection.load_adapter
path and passes the original CaseClient unchanged to the new actor. It is never
registered for ordinary planner autoload. Run calls the new actor directly,
matching the existing explicit pointer route, and preserves ordinary snapshots
where episode_run_id is missing. It does not run the unrelated legacy readiness
binding which indexed that field. Actual snapshot/common original rows remain
unchanged. Core typed source copies match the Root-adopted fork byte for byte.

Prepare has two roles. The public product prepare still delegates the existing
normal R10 profile/S0 preparation. Its full outer inputs (observed army_id,
war_id, goal_province_id, staging_province_id, director_scope_revision,
normal_checkpoint_receipt/player/date, source Save and plain config inputs)
remain required. The provided case-input template is only a PENDING postload
sub-block, not complete runnable preparation. No observed IDs are invented.
Separately, prepare_parent_postload_admission.py consumes exact fresh common
views, actual Root scope, new Q and its own explicit source index; it never
launches or performs an SDK request. Its 35 metadata keys match the proposed
native successor, which is NOT frozen/adopted by this package. Native Q must
cover that reviewed successor before any future execution.

RootScope is an explicit conditional-authorization metadata watcher. With a
future actual new Q it may be started before the marker exists, reads only
files until actual R08-POSTLOAD-AWAITING-ROOT.json, then verifies the actual
machine, allocated/frozen/prepared sources, same-client owner pair, current
PID/birth/module and CheckRemoteDebuggerPresent. Standard ready-context has
no state_dir: state comes from exact prepared.startup.state_dir. It requires
min(original native-report hold, scene deadline)-1050s, re-reads that original
hold, pair age <=30s and actual OS observation age <=5s before an fsync + atomic
create-only hardlink signal. The actual CaseClient guard independently repeats
1050s after prepare, before claim and immediately before Popen. A generic source
financial card cannot authorize Game, and the dedicated future Game schema has
not been issued. Root declarations remain mandatory and are not inferred from Q.

The observer uses execution DR0 at module+0x28F785A, RBP=admitted player,
one record, fixed 30s/4096 foreign bound, and full-six restore/detach. RDX may
be null; admitted secondary-context drift is a separate diagnostic. Prefix,
stack, owner/clock/source and new raw schema are independently checked. New
prepare/public peers are pinned by their own immutable index, not falsely
listed as compiled/cold inputs in native Q. The Q consumer binds both EXEs,
native sources and copied typed peers, SYSTEM, all 21 new-case proofs and the
independent Root cold acceptance. Every listed source pin must also be expanded
into the future allocator frozen.files; this small index is not a complete
host/runtime/transitive import closure by itself.

Exact-day completion and qualified target postload are separate outputs. One
day does not guarantee a player callback or that it occurs during the watcher.
Timeout/foreign limit/target0 never prove a complete natural opportunity or zero
payment. No unknown day or observer action is retried. Cleanup only proceeds
after typed native restore, then independent payment/nine-family OFF and the
unchanged shared ordinary-Save materialization/native-bracketing proof. Save
unknown is never resubmitted; existing oneLife unconfirmed remains unchanged.
full_R08/opportunity_complete stay false and paid/payer/cadence stay literal null.

Actual finite validation: 15 Python methods PASS, nine new production Python
files pass modified-scope strict mypy (follow-imports=skip, no cache). This does
not claim the complete legacy tree is typed. Standard Selection.load_adapter,
no preloaded R10, absent-Q zero SDK/Popen, execution-vs-data DR vector, canonical
u64/null/missing, same-client dispatch, unknown-day no retry/cleanup ordering,
real ready-context state source, and finite prewatch deadline were exercised.
Early source/fixture failures and all original Popen waits/logs remain intact.
No synthetic fixture or Python check is a native or Game qualification.
''')
    frozen=save('SOURCE-FREEZE.actual-a01.json',{
        'schema':'xar.e04.postload.public-source-freeze.v1','machine_id':machine,
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),'source_only':True,
        'native_fork':pin(old_freeze),'Root_fork_adoption':pin(ROOT.parent/'ROOT-FROZEN-SOURCE-FORK-ADOPTION.actual-a01.json'),
        'financial_source_card':pin(ROOT.parent/'capacity/FINANCIAL-SOURCE-PLANNING0230.actual-a01.json'),
        'production_mapping':production,'unchanged_native_typed_support':typed,
        'bundle_index':pin(index),'expanded_source_files':bundle['files'],'source_contract':pin(contract),
        'root_authorization_template':pin(template),'external_case_fragment':pin(override),
        'case_inputs_subblock_template':pin(ROOT/'CASE-INPUTS.source-only-template-a04.json'),
        'test_source':pin(test_source),'final_checks':final,'all_original_check_receipts':checks,
        'pure_Python_methods':count,'strict_new_production_files':9,'README':pin(readme),
        'actual_Q_exists':False,'native_successor_full_source_closed':False,
        'runtime_or_live_ready':False,'no_D_W_Git_mutations':True,'tmp_remaining':[],
        'source_writer_state':'FROZEN; metadata delivery only remains'})
    print(json.dumps({'freeze':pin(frozen),'source_contract':pin(contract),
        'actual_bytes':sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())}))

if __name__=='__main__':main()
