package org.xar.ck3.control.nativebridge.capabilities.army;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.concurrent.TimeUnit;

/** Test-only complete original producer capture. Root owns admission, process containment and execution. */
public final class CaptureLossAllocationGolden {
    private CaptureLossAllocationGolden(){}
    private static final String SCRIPT="""
import contextlib,copy,datetime,hashlib,json,pathlib,runpy,sys,unittest
root=pathlib.Path(sys.argv[1]);machine=sys.argv[2]
sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
sys.path.insert(0,str(root/'ck3_autonomous_player/tests/unit'))
bridge='ck3_autonomous_player/src/xar_autoplayer/bridge/'
pure=('army_loss_allocation_projection.py','army_chunk_loss_writeback_projection.py','army_loss_sequence_replay.py','army_monthly_loss_budget_projection.py','army_monthly_caller_effect_projection.py','army_daily_queue_transfer_projection.py','army_manager_cleanup_projection.py','army_current_helper_domain_projection.py','army_current_helper_point_store_projection.py','army_associated_refill_current_projection.py','army_current_province_supply_usage_projection.py','army_regiment_refresh_projection.py')
tests=('test_army_loss_allocation_projection.py','test_conditional_monthly_loss_budgets.py','test_conditional_monthly_caller_effects.py','test_conditional_daily_queue_transfer.py','test_conditional_manager_cleanup.py','test_conditional_current_helper_domain_updates.py','test_conditional_current_helper_point_stores.py','test_associated_refill_current_assembly.py','test_current_province_supply_contributors.py')
contracts=('army_monthly_loss_budget_inputs_contract.py','army_monthly_caller_effect_inputs_contract.py','army_daily_queue_inputs_contract.py','army_manager_cleanup_inputs_contract.py','army_current_helper_domain_inputs_contract.py','army_current_helper_point_store_inputs_contract.py','war_contract.py')
paths=[bridge+v for v in pure+contracts]+['ck3_autonomous_player/tests/unit/'+v for v in tests]+['ck3_autonomous_player/src/xar_autoplayer/replenishment_numeric.py','ck3_autonomous_player/src/xar_autoplayer/simulation/battle_trait_numeric_inputs_12003.py']
before={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths}
from xar_autoplayer.bridge.army_loss_allocation_projection import project_observed_army_loss_requests
fixtures={p:runpy.run_path(str(root/'ck3_autonomous_player/tests/unit'/p)) for p in tests}
suite=unittest.TestSuite()
for fixture in fixtures.values():
    for name,value in fixture.items():
        if isinstance(value,type) and issubclass(value,unittest.TestCase) and value.__module__=='<run_path>':
            suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(value))
with contextlib.redirect_stdout(sys.stderr):
    result=unittest.TextTestRunner(stream=sys.stderr,verbosity=1).run(suite)
if not result.wasSuccessful() or result.skipped or result.testsRun==0:
    raise RuntimeError('original complete loss closure tests failed/skipped/empty')
def factory(file,name,*args):return copy.deepcopy(fixtures[file][name](*args))
cases=[]
def add(label,row):
    original=copy.deepcopy(row)
    expected=project_observed_army_loss_requests([row])[0]
    if row!=original:raise RuntimeError('original producer mutated input '+label)
    cases.append(dict(id=label,input=row,expected=expected))
add('base_monthly',factory(tests[1],'monthly_budget_packet'))
add('ordered_counter_aliases',factory(tests[2],'caller_packet'))
add('cleanup_pointer_memberships',factory(tests[4],'manager_cleanup_packet'))
add('cleanup_signed_fullid',factory(tests[4],'manager_cleanup_packet',-2147483647))
add('all_helper_point_effects',factory(tests[6],'point_packet'))
d=fixtures[tests[5]]
add('domain_alias_accumulation',d['domain_packet']([d['domain_row'](0),d['domain_row'](1)]))
add('domain_signed64_wrap_clamp',d['domain_packet']([d['domain_row'](0,old_value=(1<<63)-2)]))
unknown=d['domain_row'](0);unknown.update(domain_alias_ordinal=None,domain_flag_17e_raw=None)
add('domain_unknown_alias_poison',d['domain_packet']([unknown,d['domain_row'](1)]))
add('associated_single_add_repeated_refresh',factory(tests[7],'packet'))
add('province_repeated_occurrences',factory(tests[8],'contributor_packet'))
raw=factory(tests[0],'observed_army')
add('observed_zero_quantity_order',raw)
raw=factory(tests[0],'observed_army');raw['loss_application_inputs_v1']['current_supply_loss_budget']=2
add('missing_real_post_supply_stage',raw)
raw=factory(tests[0],'observed_army');raw['loss_application_inputs_v1']['siege_loss_budget']=5
add('missing_real_post_preferred_stage',raw)
raw=factory(tests[0],'observed_army');raw['regiment_strengths'][0].update(siege_tier_observable=False,siege_tier=None)
add('unknown_tier_no_name_inference',raw)
add('unavailable_row',dict(status='unavailable',army_id=0))
refs=[]
for p in paths:
    data=(root/p).read_bytes();sha=hashlib.sha256(data).hexdigest()
    if sha!=before[p]:raise RuntimeError('source drift during original capture '+p)
    refs.append(dict(path=p,bytes=len(data),sha256=sha))
print(json.dumps(dict(schema='xar.loss-allocation.complete-original-golden/v1',machine_id=machine,observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),original_test_count=result.testsRun,original_skipped=len(result.skipped),source_refs=refs,cases=cases),separators=(',',':')))
""";
    public static void main(String[] args)throws Exception{
        if(args.length!=5)throw new IllegalArgumentException("repo-root python-exe admitted-output-root fresh-output machine-id required");
        Path repo=Path.of(args[0]).toRealPath(),admitted=Path.of(args[2]).toRealPath(),output=Path.of(args[3]).toAbsolutePath().normalize();
        if(!output.startsWith(admitted)||Files.exists(output)||args[4].isBlank())throw new IllegalArgumentException("fresh admitted capture output and actual machine required");
        Path stdout=Files.createTempFile(admitted,"loss-original-",".json"),stderr=Files.createTempFile(admitted,"loss-original-",".log");
        ProcessBuilder builder=new ProcessBuilder(args[1],"-B","-X","utf8","-c",SCRIPT,repo.toString(),args[4]);
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1");builder.environment().put("OPENBLAS_NUM_THREADS","1");builder.environment().put("OMP_NUM_THREADS","1");builder.redirectOutput(stdout.toFile()).redirectError(stderr.toFile());
        Process child=builder.start();
        if(!child.waitFor(120,TimeUnit.SECONDS)){child.descendants().forEach(ProcessHandle::destroyForcibly);child.destroyForcibly();throw new IllegalStateException("original complete loss capture timed out");}
        System.err.print(Files.readString(stderr,StandardCharsets.UTF_8));
        if(child.exitValue()!=0)throw new IllegalStateException("original complete loss capture exit "+child.exitValue());
        byte[] data=Files.readAllBytes(stdout);if(data.length==0||data.length>1_048_576)throw new IllegalStateException("original complete loss capture outside admitted runtime budget");
        Files.write(output,data,StandardOpenOption.CREATE_NEW);System.out.println("machine_id="+args[4]+" observed_at_utc="+Instant.now()+" captured_bytes="+data.length);
    }
}
