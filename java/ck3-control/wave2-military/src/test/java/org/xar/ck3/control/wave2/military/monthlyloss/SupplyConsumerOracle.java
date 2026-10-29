package org.xar.ck3.control.wave2.military.monthlyloss;

/** Test-only original-consumer execution; no production Python module or fallback is introduced. */
final class SupplyConsumerOracle {
    private SupplyConsumerOracle() { }
    static String program() { return PROGRAM; }
    private static final String PROGRAM = """
import contextlib,copy,hashlib,importlib,json,pathlib,runpy,sys,threading,unittest
root=pathlib.Path(sys.argv[1]).resolve(); protocol=sys.stdout; sequence=0; calls={}; depth=threading.local()
sys.path[:0]=[str(root/'ck3_autonomous_player/src'),str(root/'ck3_autonomous_player/tests/unit')]
files=['test_conditional_monthly_loss_budgets.py','test_conditional_loss_sequence_replay.py','test_army_chunk_loss_writeback_projection.py','test_army_loss_allocation_projection.py','test_selected_refill_monthly_assembly_service.py','test_selected_refill_monthly_fleet_service.py','test_current_callback_soldier_effects_service_12004.py','test_army_zero_stock_clock_12004.py','test_r05_first_zero_budget_capture.py','test_r05_zero_preparation_decision.py']
fixtures=[]; classes=[]
for name in files:
    fixture=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit'/name));fixtures.append(fixture)
    found=[v for v in fixture.values() if isinstance(v,type) and issubclass(v,unittest.TestCase) and v is not unittest.TestCase and v.__module__=='<run_path>']
    if not found:raise RuntimeError('original suite class missing '+name)
    classes.extend(found)
def suite():
    return unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(value) for value in classes)
def run(label):
    with contextlib.redirect_stdout(sys.stderr):result=unittest.TextTestRunner(stream=sys.stderr,verbosity=0).run(suite())
    if not result.wasSuccessful() or result.skipped or not result.testsRun:raise RuntimeError(label+' complete original suite failed/skipped/empty')
    return result.testsRun
def source_inventory():
    result={}
    for name,module in list(sys.modules.items()):
        if (name.startswith('xar_autoplayer.') or name.startswith('test_')) and getattr(module,'__file__',None):
            location=pathlib.Path(module.__file__).resolve()
            source_root=root/('ck3_autonomous_player/src' if name.startswith('xar_autoplayer.') else 'ck3_autonomous_player/tests')
            if not location.is_relative_to(source_root):raise RuntimeError('consumer imported outside qualified source root '+name)
            if location.suffix=='.py':result[location.relative_to(root).as_posix()]=hashlib.sha256(location.read_bytes()).hexdigest()
    return result
before_loaded=source_inventory();baseline=run('original')
def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def invoke(operation,arguments):
    global sequence
    sequence+=1
    request=dict(schema='xar.military-supply-consumer-request/v1',operation=operation,arguments=arguments)
    protocol.write(canonical(dict(schema='xar.supply-probe-call/v1',sequence=sequence,request_json=canonical(request)))+'\\n');protocol.flush()
    line=sys.stdin.readline(262145)
    if not line or len(line)>262144:raise RuntimeError('Java response missing/over bound')
    response=json.loads(line)
    if type(response.get('sequence')) is not int or response['sequence']!=sequence:raise RuntimeError('Java response sequence differs')
    if response.get('status')=='rejected':raise ValueError(response['error'])
    if response.get('status')!='complete' or type(response.get('result_json')) is not str:raise RuntimeError('Java response is not complete')
    calls[operation]=calls.get(operation,0)+1
    return json.loads(response['result_json'])
bindings=[]
def bind(module,name,operation,pack,mutates=False):
    original=getattr(importlib.import_module('xar_autoplayer.bridge.'+module),name)
    def replacement(*args,**kwargs):
        if getattr(depth,'value',0):return original(*args,**kwargs)
        original_args=copy.deepcopy(args);original_kwargs=copy.deepcopy(kwargs)
        depth.value=1
        try:expected=original(*original_args,**original_kwargs)
        except (TypeError,ValueError) as failure:
            depth.value=0
            try:invoke(operation,pack(args,kwargs))
            except ValueError:raise failure
            raise AssertionError('Java accepted original rejected input '+operation)
        finally:depth.value=0
        actual=invoke(operation,pack(args,kwargs))
        wanted=original_args[0] if mutates else expected
        if canonical(actual)!=canonical(wanted):raise AssertionError('compiled Java differs at actual original consumer '+operation+' expected='+canonical(wanted)+' actual='+canonical(actual))
        if mutates:args[0].clear();args[0].update(actual);return None
        return actual
    bindings.append((original,replacement))
row=lambda a,k:dict(row=a[0])
bind('army_monthly_loss_budget_projection','construct_conditional_monthly_loss_budgets','MONTHLY_BUDGETS',row)
bind('army_loss_sequence_replay','project_conditional_army_loss_sequence','LOSS_SEQUENCE',row)
bind('army_chunk_loss_writeback_projection','project_observed_writer_chunk_changes','ASSOCIATED_WRITER',lambda a,k:dict(row=a[0],writer_request=a[1]))
bind('army_monthly_loss_budget_projection','_derive_supply_component','SUPPLY_COMPONENT',lambda a,k:dict(result=a[0],inputs=a[1],losses=a[2]),True)
bind('army_next_fleet_supply_budget_projection','project_source_derived_next_fleet_supply_budget_v1','FLEET_BUDGET',row)
bind('army_next_fleet_supply_budget_projection','_project_source_next_fleet_supply_budget_at_stock_v1','FLEET_AT_STOCK',lambda a,k:dict(row=a[0],stock=a[1],stock_basis=k.get('stock_basis','captured_current_stock_unchanged'),post_updater_stock_used=k.get('post_updater_stock_used',False),stock_input_name=k.get('stock_input_name','current_supply_raw')))
bind('army_future_daily_supply_schedule_contract','normalize_future_daily_supply_schedule_inputs_v1','NORMALIZE_SCHEDULE',lambda a,k:dict(family=a[0],expected_army_id=k.get('expected_army_id'),expected_carmy_id=k.get('expected_carmy_id')))
bind('army_future_daily_supply_schedule_projection','project_future_daily_supply_schedule_v1','PROJECT_SCHEDULE',lambda a,k:dict(row_or_family=a[0],prospective_frames=k.get('prospective_frames',())))
bind('army_source_derived_next_daily_supply_frame_projection','project_native_next_daily_supply_schedule_v1','NATIVE_NEXT_SCHEDULE',row)
bind('army_zero_stock_clock_12004','project_zero_stock_next_callback_candidate_12004','ZERO_CALLBACK',row)
bind('army_zero_stock_clock_12004','successful_supply_occurrences_to_zero_12004','SUCCESSFUL_OCCURRENCES',lambda a,k:dict(stock=a[0],capacity=a[1],monthly=a[2]))
namespaces=[vars(module) for name,module in list(sys.modules.items()) if name.startswith('xar_autoplayer.') and module is not None]
namespaces.extend(fixtures)
for cls in classes:
    namespaces.extend(value.__globals__ for value in vars(cls).values() if hasattr(value,'__globals__'))
changed=[];seen=set();replacements={id(old):(old,new) for old,new in bindings}
try:
    for namespace in namespaces:
        if id(namespace) in seen:continue
        seen.add(id(namespace))
        for key,value in list(namespace.items()):
            match=replacements.get(id(value))
            if match and value is match[0]:changed.append((namespace,key,value));namespace[key]=match[1]
    replaced=run('compiled Java replacements')
    # The real public schedule consumer is also called with its original clock-row factory.
    row_value=fixtures[7]['clock_row']()
    importlib.import_module('xar_autoplayer.bridge.army_future_daily_supply_schedule_projection').project_future_daily_supply_schedule_v1(row_value,prospective_frames=[dict(date_raw_i32=43800024,native_day_index_raw_i32=1)])
    if replaced!=baseline:raise RuntimeError('original suite count changed under Java replacement')
    required={'MONTHLY_BUDGETS','LOSS_SEQUENCE','ASSOCIATED_WRITER','SUPPLY_COMPONENT','FLEET_BUDGET','FLEET_AT_STOCK','NORMALIZE_SCHEDULE','PROJECT_SCHEDULE','NATIVE_NEXT_SCHEDULE','ZERO_CALLBACK','SUCCESSFUL_OCCURRENCES'}
    if not required<=set(calls):raise RuntimeError('actual original consumer route not executed '+str(sorted(required-set(calls))))
finally:
    for namespace,key,value in reversed(changed):namespace[key]=value
modules=source_inventory()
if any(modules.get(name)!=sha for name,sha in before_loaded.items()):raise RuntimeError('loaded original consumer source drifted during execution')
protocol.write(canonical(dict(schema='xar.supply-probe-complete/v1',original_tests=baseline,java_consumer_tests=replaced,skipped=0,consumer_calls=calls,loaded_source_before_sha256=before_loaded,loaded_source_sha256=modules,scope='offline actual original service/assembly/sequence/dispatch consumers only; no native/SDK/Game/writer'))+'\\n');protocol.flush()
""";
}
