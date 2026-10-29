package org.xar.ck3.control.admission.batchtiming;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.Executors;

/** Explicit fixture capture only. Default Maven tests do not invoke Python. Run inside the shared Job. */
public final class BatchTimingGoldenCapture {
    private BatchTimingGoldenCapture() { }

    public static void main(String[] args) throws Exception {
        if (args.length != 3) {
            throw new IllegalArgumentException("python-executable repository-root new-output-file required");
        }
        Path output = Path.of(args[2]).toAbsolutePath().normalize();
        if (Files.exists(output)) { throw new IllegalArgumentException("capture output must be new"); }
        Process child = new ProcessBuilder(args[0], "-I", "-B", "-c", PROGRAM,
                Path.of(args[1]).toAbsolutePath().normalize().toString()).start();
        byte[] captured;
        try (var readers = Executors.newVirtualThreadPerTaskExecutor()) {
            // Outer native Job owns this process and its Python descendant; this timeout is additional.
            var stdout = readers.submit(() -> drain(child.getInputStream(), 65_536));
            var stderr = readers.submit(() -> drain(child.getErrorStream(), 8_192));
            try {
                if (!child.waitFor(Duration.ofSeconds(15).toMillis(), TimeUnit.MILLISECONDS)) {
                    throw new IllegalStateException("capture timeout");
                }
                CaptureBytes outputBytes = stdout.get(1, TimeUnit.SECONDS);
                CaptureBytes errors = stderr.get(1, TimeUnit.SECONDS);
                captured = outputBytes.bytes();
                if (outputBytes.observedBytes() > 65_536 || errors.observedBytes() > 8_192) {
                    throw new IllegalStateException("capture output exceeds budget: stdout="
                            + outputBytes.observedBytes() + ", stderr=" + errors.observedBytes());
                }
                if (child.exitValue() != 0) {
                    throw new IllegalStateException("original producer capture failed: "
                            + new String(errors.bytes(), StandardCharsets.UTF_8));
                }
            } finally {
                if (child.isAlive()) { child.destroyForcibly(); child.waitFor(); }
            }
        }
        Files.createDirectories(output.getParent());
        Files.write(output, captured, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        System.out.println("Captured existing Python timing producers: " + captured.length + " bytes");
    }

    /** Always drain the pipe; exceeding retained bytes must not deadlock the child writer. */
    private static CaptureBytes drain(InputStream stream, int retainedByteLimit) throws IOException {
        ByteArrayOutputStream retained = new ByteArrayOutputStream(retainedByteLimit);
        byte[] chunk = new byte[8_192];
        long observed = 0;
        int count;
        while ((count = stream.read(chunk)) != -1) {
            int copy = Math.min(count, retainedByteLimit - retained.size());
            if (copy > 0) { retained.write(chunk, 0, copy); }
            observed = Math.addExact(observed, count);
        }
        return new CaptureBytes(retained.toByteArray(), observed);
    }

    private record CaptureBytes(byte[] bytes, long observedBytes) { }

    private static final String PROGRAM = """
            import copy,hashlib,io,json,sys,unittest
            from datetime import datetime,timezone
            from pathlib import Path
            root=Path(sys.argv[1]);sys.path.insert(0,str(root/'tools'/'g2_saved_campaign'))
            sys.path.insert(0,str(root/'tools'))
            producer_pins={'full_batch_timing_v1.py':'197e4308b7d0f5a70a8c3474ec0b58581997f3e60bfc2d8414c668dae07c8e0b',
                'full_lifecycle_timing_v1.py':'dcbb92b3852123a24dac29f35f182eea6a731a46104d1837478c2990052a32ca'}
            originals={name:(root/'tools'/'g2_saved_campaign'/name).read_bytes()
                for name in (*producer_pins,'test_full_lifecycle_timing_v1.py')}
            if any(hashlib.sha256(originals[name]).hexdigest()!=digest for name,digest in producer_pins.items()):
                raise RuntimeError('original producer source pin differs')
            from ck3_live_run_id import current_machine_id
            import full_batch_timing_v1 as batch
            from full_lifecycle_timing_v1 import FullLifecycleTimingV1
            existing=unittest.TextTestRunner(stream=io.StringIO()).run(
                unittest.defaultTestLoader.loadTestsFromName('test_full_lifecycle_timing_v1'))
            if not existing.wasSuccessful() or existing.testsRun!=5 or existing.skipped:
                raise RuntimeError('existing lifecycle test group did not complete')
            def req(seq,tool='ck3_auto_turn',args=None):
                return {'sequence':seq,'tool':tool,'arguments':{} if args is None else args}
            def obs(seq,elapsed,start,tool='ck3_auto_turn',error=False,client=False,response=None,args=None):
                r=req(seq,tool,args)
                return {'request':r,'response_request':copy.deepcopy(r) if response is None else response,
                    'elapsed_seconds':elapsed,'monotonic_start_seconds':start,
                    'result_is_error':error,'client_error_present':client}
            def wall(seq=100,start=100,end=15000000100):
                clocks=iter([start,end]);timer=FullLifecycleTimingV1(enabled=True,clock=lambda:next(clocks))
                timer.before_publish(seq);return timer.after_receipt(seq)
            def following(seq=100):
                timer=FullLifecycleTimingV1(enabled=True,clock=lambda:(_ for _ in ()).throw(RuntimeError('no clock')))
                return timer.after_receipt(seq)
            def case(name,observations,fields=None):
                active=batch._Rows(100)
                for o in observations:
                    row={'request':o['response_request'],'elapsed_seconds':o['elapsed_seconds'],
                        'result':{'is_error':o['result_is_error']}}
                    if o['client_error_present']:row['client_error']='original client error'
                    active.record(o['request'],row,o['monotonic_start_seconds'])
                result=active.fields();fields=wall() if fields is None else fields
                return {'name':name,'input':{'control_sequence':100,'observations':observations},
                    'wall':fields,'expected_summary':result['full_rpc_rows_v1'],
                    'expected_combined':batch.batch_timing_fields_v1(result,fields)}
            cases=[
                case('empty',[]),
                case('all_four_zero_day_and_errors',[obs(101+i,i,10+i*4,t,error=i==1,client=i==3)
                    for i,t in enumerate(batch.TOOLS)]),
                case('overlap_and_duplicate',[obs(101,3,10),obs(102,2,11,'root_current_runtime_metrics'),obs(101,3,10)]),
                case('invalid_elapsed_preserves_count',[obs(101,None,10),obs(102,2,12)]),
                case('invalid_monotonic_preserves_elapsed',[obs(101,3,None),obs(102,2,12)]),
                case('negative_elapsed_is_not_zero',[obs(101,-1,10)]),
                case('nested_adjoining_and_disjoint',[obs(101,10,10),obs(102,2,11),obs(103,1,20),obs(104,2,30)]),
                case('response_request_mismatch_ignored',[obs(101,3,10,response=req(102))]),
                case('argument_mismatch_ignored',[obs(101,3,10,response=req(101,args={'x':2}),args={'x':1})]),
                case('unsupported_tool_ignored',[obs(101,3,10,'unsupported_readonly')]),
                case('sequence_unique_across_tools',[obs(101,3,10),obs(101,3,10,'root_current_runtime_metrics')]),
                case('client_timeout_is_error_row',[obs(101,30.3402217,10,error=True,client=True)],wall(end=40000000100)),
                case('follow_does_not_invent_origin',[obs(101,3,10)],following()),
                case('different_control_not_attached',[obs(101,3,10)],wall(seq=200)),
                case('union_exceeds_full_residual_unknown',[obs(101,3,10)],wall(end=1000000100)),
                case('precise_monotonic_above_js_safe',[obs(101,0.125,10.25)],
                    wall(start=18446744073709551616,end=18446744073711551616)),
                case('binary64_fractional_overlap',[obs(101,0.1,10.1),obs(102,0.2,10.15,'root_current_runtime_metrics')])]
            lifecycle=[]
            for name,events in [
                ('single_use',[['before',3,100],['after',3,9100],['after',3,9999]]),
                ('wrong_sequence_consumes_pending',[['before',4,100],['after',5,999],['after',4,999]]),
                ('discard_no_receipt',[['before',3,100],['discard'],['after',3,999]]),
                ('reverse_clock_drops_metric',[['before',3,100],['after',3,99]]),
                ('missing_start_drops_metric',[['before',3,None],['after',3,999]]),
                ('disabled_no_fields',[['before',3,100],['after',3,999]])]:
                current=[];timer=FullLifecycleTimingV1(enabled=name!='disabled_no_fields',clock=lambda:current.pop(0))
                expected=[]
                for event in events:
                    if event[0]=='before':current[:]=[event[2]];timer.before_publish(event[1])
                    elif event[0]=='discard':timer.discard()
                    else:current[:]=[event[2]];expected.append(timer.after_receipt(event[1]))
                lifecycle.append({'name':name,'enabled':name!='disabled_no_fields','events':events,'expected':expected})
            sources=[]
            for name in ('full_batch_timing_v1.py','full_lifecycle_timing_v1.py','test_full_lifecycle_timing_v1.py'):
                p=root/'tools'/'g2_saved_campaign'/name;raw=p.read_bytes()
                if raw!=originals[name]:raise RuntimeError('original source changed during capture')
                sources.append({'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
            document={'schema':'xar.java.batch-timing-producer-golden/v1',
                'machine_id':current_machine_id(),'observed_at_utc':datetime.now(timezone.utc).isoformat(),
                'producer_sources':sources,'cases':cases,'lifecycle_cases':lifecycle,
                'existing_lifecycle_tests':existing.testsRun,'existing_lifecycle_skipped':len(existing.skipped),
                'scope':'actual unchanged pure producers; no Game/Task/RPC/ledger/source-generation',
                'new_saved_day_credit':0,'cpu_attribution':None}
            payload=(json.dumps(document,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\\n').encode('utf-8')
            if len(payload)>65536:raise RuntimeError('golden byte budget exceeded: '+str(len(payload)))
            sys.stdout.buffer.write(payload)
            """;
}
