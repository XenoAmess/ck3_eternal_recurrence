"""Detached future timing qualification. No Game/Task, D writes or body scans."""
import ast,asyncio,copy,hashlib,json,sys,types,unittest
from datetime import datetime,timezone
from pathlib import Path

import full_batch_timing_v1 as metrics
from full_lifecycle_timing_v1 import FullLifecycleTimingV1
import prepare_full_batch_timing_sources_v1 as producer

OWN=Path(__file__).resolve().parent
VALUES,CHANGES=producer.build_sources(enabled=True)
DISABLED,_=producer.build_sources(enabled=False)
FEEDER=producer.FEEDER
FTREE=ast.parse(VALUES[FEEDER])


def request(sequence,tool):return {'sequence':sequence,'tool':tool,'arguments':{}}


def row(r,elapsed,*,error=False,client=False):
    result={'request':r,'elapsed_seconds':elapsed,'result':{'is_error':error}}
    if client:result['client_error']='original client error'
    return result


def full(sequence=100):return {'sequence':sequence,'command':'full_loop','arguments':{'max_turns':30}}


class Clock:
    def __init__(self,values):self.values=iter(values);self.calls=0
    def __call__(self):self.calls+=1;return next(self.values)


class HelperCases(unittest.TestCase):
    def test_default_off_original_method_and_zero_clock(self):
        async def original(*args):return 'same'
        self.assertIs(metrics.full_rows_v1(enabled=False)(original),original)
        clock=Clock([]);timer=FullLifecycleTimingV1(clock=clock)
        timer.before_publish(100);self.assertEqual(timer.after_receipt(100),{})
        self.assertEqual(clock.calls,0)

    def test_all_tools_zero_day_and_error_rows(self):
        async def original(q,s,r,p):
            for i,tool in enumerate(metrics.TOOLS):
                child=request(101+i,tool)
                metrics.record_existing_rpc_row_v1(child,row(child,i,error=i==1,client=i==3),10+i*4)
            return metrics.current_full_row_fields_v1()
        result=asyncio.run(metrics.full_rows_v1(enabled=True)(original)(types.SimpleNamespace(),None,full(),None))
        value=result['full_rpc_rows_v1'];self.assertEqual(value['row_count'],4)
        self.assertEqual(value['elapsed_seconds_sum'],6)
        self.assertEqual(value['interval_union_seconds'],6)
        self.assertEqual(value['tools']['AUTO']['count'],1)
        self.assertEqual(value['tools']['MET']['error_count'],1)
        self.assertEqual(value['tools']['SAVE']['client_error_count'],1)
        self.assertTrue(value['zero_day_rows_included'] and value['error_rows_included'])
        self.assertIsNone(value['CPU_attribution'])
        self.assertEqual(metrics.current_full_row_fields_v1(),{})

    def test_overlap_union_and_duplicate_row(self):
        async def original(q,s,r,p):
            a,b=request(101,'ck3_auto_turn'),request(102,'root_current_runtime_metrics')
            for child,elapsed,start in ((a,3,10),(b,2,11),(a,3,10)):
                metrics.record_existing_rpc_row_v1(child,row(child,elapsed),start)
            return metrics.current_full_row_fields_v1()
        v=asyncio.run(metrics.full_rows_v1(enabled=True)(original)(types.SimpleNamespace(),None,full(),None))['full_rpc_rows_v1']
        self.assertEqual((v['row_count'],v['duplicate_rows_ignored']),(2,1))
        self.assertEqual((v['elapsed_seconds_sum'],v['interval_union_seconds'],v['overlap_seconds']),(5,3,2))

    def test_error_identity_and_failed_full_summary(self):
        error=ValueError('original business failure');q=types.SimpleNamespace()
        async def original(q,s,r,p):
            child=request(101,'ck3_auto_turn')
            metrics.record_existing_rpc_row_v1(child,row(child,2,error=True),10)
            raise error
        try:asyncio.run(metrics.full_rows_v1(enabled=True)(original)(q,None,full(),None))
        except ValueError as actual:self.assertIs(actual,error)
        else:self.fail('original error swallowed')
        fields=metrics.failed_full_row_fields_v1(q,full())
        self.assertEqual(fields['full_rpc_rows_v1']['tools']['AUTO']['error_count'],1)
        self.assertEqual(metrics.failed_full_row_fields_v1(q,full(200)),{})
        self.assertEqual(metrics.current_full_row_fields_v1(),{})

    def test_malformed_request_still_original_exception(self):
        error=ValueError('original malformed arguments')
        async def original(*args):raise error
        try:asyncio.run(metrics.full_rows_v1(enabled=True)(original)(None,None,{'command':'full_loop','arguments':[]},None))
        except ValueError as actual:self.assertIs(actual,error)
        else:self.fail('original error swallowed')

    def test_invalid_interval_keeps_count_without_fake_union(self):
        async def original(q,s,r,p):
            child=request(101,'ck3_save_checkpoint')
            metrics.record_existing_rpc_row_v1(child,row(child,float('nan')),10)
            return metrics.current_full_row_fields_v1()
        v=asyncio.run(metrics.full_rows_v1(enabled=True)(original)(types.SimpleNamespace(),None,full(),None))['full_rpc_rows_v1']
        self.assertEqual(v['row_count'],1);self.assertEqual(v['invalid_elapsed_rows'],1)
        self.assertIsNone(v['interval_union_seconds']);self.assertIsNone(v['overlap_seconds'])

    def test_batch_scalars_bound_full_and_residual_not_cpu(self):
        current=metrics._Rows(100);child=request(101,'ck3_auto_turn');current.record(child,row(child,3),10)
        result=current.fields();clock=Clock([100,15000000100]);timer=FullLifecycleTimingV1(enabled=True,clock=clock)
        timer.before_publish(100);fields=metrics.batch_timing_fields_v1(result,timer.after_receipt(100))
        self.assertEqual(fields['full_wall_minus_rpc_union_seconds'],12)
        self.assertIsNone(fields['full_wall_residual_attribution'])
        wrong=metrics.batch_timing_fields_v1(result,{'full_timing_control_sequence':200,'full_wall_ns':15000000000})
        self.assertNotIn('full_rpc_rows_v1',wrong)

    def test_follow_restart_origin_null_no_clock(self):
        clock=Clock([]);timer=FullLifecycleTimingV1(enabled=True,clock=clock)
        fields=timer.after_receipt(100)
        self.assertEqual(fields['full_timing_origin'],'submission_not_observed')
        self.assertIsNone(fields['full_submit_monotonic_ns']);self.assertIsNone(fields['full_receipt_validated_monotonic_ns'])
        self.assertIsNone(fields['full_wall_ns']);self.assertEqual(clock.calls,0)


class SourceCases(unittest.TestCase):
    def test_every_hook_exact_inverse_bytes_and_ast(self):
        # Producer independently reverses each inserted hunk before compilation.
        self.assertEqual(set(VALUES),set(DISABLED))
        self.assertEqual(len(CHANGES['root_p37c17_sdk_queue.py']),5)
        self.assertEqual(len(CHANGES['root_p37c17_automatic_natural_succession_handoff.py']),1)
        self.assertEqual(len(CHANGES[FEEDER]),4)
        self.assertIn(b'@_full_rows_v1(enabled=False)',DISABLED['root_p37c17_sdk_queue.py'])
        for name,raw in VALUES.items():compile(raw,name,'exec')

    def _publish(self,*,exists=False,fail=False):
        function=next(n for n in FTREE.body if isinstance(n,ast.FunctionDef) and n.name=='publish_or_follow')
        events=[];error=OSError('original atomic failure');clock=Clock([100,200])
        timer=FullLifecycleTimingV1(enabled=True,clock=clock)
        class File:
            def __init__(self,value=False):self.value=value
            def exists(self):return self.value
        class Root:
            def __truediv__(self,value):return File()
        def atomic(path,r):
            events.append(('atomic',clock.calls))
            if fail:raise error
        scope=dict(INBOX='in',OUTBOX='out',STOP=File(),N=Root(),request_path=lambda sequence,root:File(exists if root=='in' else False),
                   read=lambda p:{},request_maximum=lambda s:30,next_sequence=lambda:100,atomic=atomic,_FULL_TIMING_V1=timer)
        exec(compile(ast.Module(body=[function],type_ignores=[]),'actual-publish','exec'),scope)
        return scope['publish_or_follow'],timer,clock,events,error

    def test_actual_publish_before_atomic_and_follow_no_start(self):
        publish,timer,clock,events,_=self._publish()
        self.assertEqual(publish(100),'published_new_exact_control')
        self.assertEqual(events,[('atomic',1)])
        self.assertEqual(timer.after_receipt(100)['full_wall_ns'],100)
        publish,timer,clock,events,_=self._publish(exists=True)
        self.assertEqual(publish(100),'following_existing_exact_control')
        self.assertEqual(events,[]);self.assertEqual(clock.calls,0)
        self.assertIsNone(timer.after_receipt(100)['full_wall_ns'])

    def test_actual_publish_error_identity_no_validated_end(self):
        publish,timer,clock,events,error=self._publish(fail=True)
        try:publish(100)
        except OSError as actual:self.assertIs(actual,error)
        else:self.fail('original write failure swallowed')
        self.assertEqual(timer.after_receipt(100),{});self.assertEqual(clock.calls,1)

    def test_actual_receipt_validation_precedes_end_clock(self):
        main=next(n for n in FTREE.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        candidate=next(n for n in ast.walk(main) if isinstance(n,ast.Try) and n.body
                       and isinstance(n.body[0],ast.Assign)
                       and isinstance(n.body[0].value,ast.Call)
                       and isinstance(n.body[0].value.func,ast.Name) and n.body[0].value.func.id=='result_for')
        parent=next(n for n in ast.walk(main) if isinstance(n,ast.Try) and n.body and n.body[0] is candidate)
        self.assertIsInstance(parent.body[1],ast.Assign)
        fn=ast.FunctionDef(name='receipt',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),
                           body=[candidate,parent.body[1],ast.Return(value=ast.Name(id='full_wall_fields',ctx=ast.Load()))],decorator_list=[])
        clock=Clock([100,200]);timer=FullLifecycleTimingV1(enabled=True,clock=clock);timer.before_publish(100)
        def result_for(*args,**kwargs):
            self.assertEqual(clock.calls,1);return {},0,None
        scope=dict(sequence=100,first=False,previous_cycles=0,result_for=result_for,_FULL_TIMING_V1=timer)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'actual-receipt-seam','exec'),scope)
        self.assertEqual(scope['receipt']()['full_wall_ns'],100)
        error=ValueError('original result contract rejected')
        def reject(*args,**kwargs):raise error
        scope['result_for']=reject;timer.before_publish(100)
        try:scope['receipt']()
        except ValueError as actual:self.assertIs(actual,error)
        else:self.fail('original validation failure swallowed')
        self.assertEqual(timer.after_receipt(100),{})


def main(output):
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    if not result.wasSuccessful():raise SystemExit(1)
    files=[OWN/'full_batch_timing_v1.py',OWN/'prepare_full_batch_timing_sources_v1.py',Path(__file__)]
    report=dict(schema='xar.future-full-batch-timing-source-qualification/v1',machine_id='xenoamess-full-tower-eb9d2c1186',
        observed_at_utc=datetime.now(timezone.utc).isoformat(),status='SOURCE_READY_UNAPPLIED_DEFAULT_OFF',
        scope='future canonical cold timing seams; actual C18 alliance warm untouched',
        files={str(p.resolve()):{'bytes':p.stat().st_size,'sha256':producer.sha(p.read_bytes())} for p in files},
        sources_in_memory={n:{'bytes':len(raw),'sha256':producer.sha(raw)} for n,raw in VALUES.items()},
        frozen_lifecycle_dependency={'bytes':2480,'sha256':producer.LIFECYCLE_SHA},
        canonical_outer_producer=producer.OUTER_SHA,actual_feeder=producer.FEEDER_SHA,
        focused_tests=result.testsRun,source_inverse_bytes_and_AST=True,scratch_files=0,
        existing_control_probe_enabled=False,Native_Service_clocks_added=0,new_IO_sinks=0,
        external_writes=0,Game_Native_MCP_Task_calls=0,
        limitations=['FULL wall null for following/restart or failed original validation',
          'row interval end derives from existing mono+elapsed, not a new clock',
          'normal Queue elapsed includes model_dump; resident custom row elapsed ends before model_dump',
          'failed FULL keeps row summary only on original error receipt; never becomes a successful batch',
          'residual is mixed outer/control/I-O/wait time; CPU/Native attribution remains null',
          'future namespace/cold admission and D output card require then-actual inputs'])
    with output.open('x',encoding='utf8',newline='\n') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps(report))


if __name__=='__main__':main(Path(sys.argv[1]))
