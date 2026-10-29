package org.xar.ck3.control.wave2.runtime.performancewindows;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Explicit existing-producer fixture capture, run only under the shared qualified Windows Job. */
public final class PerformanceWindowsGoldenCapture {
    private PerformanceWindowsGoldenCapture() { }
    public static void main(String[] args) throws Exception {
        if (args.length != 3) { throw new IllegalArgumentException("python-executable repository-root new-work-directory required"); }
        Path work = Path.of(args[2]).toAbsolutePath().normalize();
        if (Files.exists(work)) { throw new IllegalArgumentException("new capture work directory required"); }
        Files.createDirectories(work);
        Process child = new ProcessBuilder(args[0], "-I", "-B", "-O", "-c", PROGRAM, args[1], work.toString()).start();
        byte[] captured;
        try (var readers = Executors.newVirtualThreadPerTaskExecutor()) {
            var stdout = readers.submit(() -> drain(child.getInputStream(), 98_304));
            var stderr = readers.submit(() -> drain(child.getErrorStream(), 16_384));
            try {
                if (!child.waitFor(25, TimeUnit.SECONDS)) { throw new IllegalStateException("original producer capture timeout"); }
                Capture output = stdout.get(1, TimeUnit.SECONDS); Capture error = stderr.get(1, TimeUnit.SECONDS);
                if (output.count() > 98_304 || error.count() > 16_384 || child.exitValue() != 0) {
                    throw new IllegalStateException("original producer capture rejected: exit=" + child.exitValue()
                            + ", bytes=" + output.count() + ": " + new String(error.bytes(), StandardCharsets.UTF_8));
                }
                captured = output.bytes();
            } finally { if (child.isAlive()) { child.destroyForcibly(); child.waitFor(); } }
        }
        Files.write(work.resolve("producer-golden.json"), captured, StandardOpenOption.CREATE_NEW);
        System.out.println("captured existing performance-window producer: " + captured.length + " bytes");
    }

    private static Capture drain(InputStream stream, int limit) throws Exception {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream(limit); byte[] chunk = new byte[8_192];
        long count = 0; int read;
        while ((read = stream.read(chunk)) != -1) {
            int retained = Math.min(read, limit - bytes.size());
            if (retained > 0) { bytes.write(chunk, 0, retained); }
            count = Math.addExact(count, read);
        }
        return new Capture(bytes.toByteArray(), count);
    }
    private record Capture(byte[] bytes, long count) { }

    private static final String PROGRAM = """
            import contextlib,copy,hashlib,io,json,runpy,subprocess,sys
            from datetime import datetime,timezone
            from pathlib import Path
            repo=Path(sys.argv[1]);work=Path(sys.argv[2])
            producer=repo/'tools/g2_saved_campaign/summarize_performance_windows_v1.py'
            original=producer.read_bytes()
            expected='911ec426156340de682b5b8b5e943e0c3632d5d1bf898a2994a31d65af642fe9'
            if hashlib.sha256(original).hexdigest()!=expected:raise RuntimeError('original producer source drift')
            machine=subprocess.check_output([sys.executable,str(repo/'tools/ck3_live_run_id.py'),'machine'],text=True,cwd=repo).strip()
            observed=datetime.now(timezone.utc)
            class FrozenDatetime(datetime):
                @classmethod
                def now(cls,tz=None):return observed if tz is not None else observed.replace(tzinfo=None)
            names=['p49-settled-performance.json','p49-stage-slice.json',
                'p63-r6-performance-and-normal-sdk-close-2026-10-18.json',
                'p67-p68-combat-query-archive-performance-2026-10-18.json']
            roles=['P49_SETTLED','P49_STAGES','P63','P67']
            source_bytes={name:(repo/'docs/ck3-native-ai/evidence'/name).read_bytes() for name in names}
            if any(len(raw)>1048576 for raw in source_bytes.values()):raise RuntimeError('sealed source byte limit')
            source_data={name:json.loads(raw) for name,raw in source_bytes.items()}
            source_dir=work/'baseline-sources';source_dir.mkdir()
            for name,raw in source_bytes.items():
                with (source_dir/name).open('xb') as stream:stream.write(raw)
            namespace=runpy.run_path(str(producer));main=namespace['main'];scope=main.__globals__
            scope['datetime']=FrozenDatetime
            original_check=subprocess.check_output
            def checked_machine(command,**kwargs):
                if len(command)!=3 or command[-1]!='machine':raise RuntimeError('unexpected original subprocess')
                return machine+'\\n'
            cases=[]
            for name in ['baseline','all_zero_day_groups','all_progress_groups','zero_count_mismatch',
                         'auto_elapsed_mismatch','zero_turn_denominator','zero_persistence_denominator']:
                values=copy.deepcopy(source_data);settled=values[names[0]]['5104-5165']
                if name=='all_zero_day_groups':
                    for group in settled['auto_by_group'].values():group['game_days']=0
                    settled['game_days']=0;settled['zero_date_turns']=settled['turns']
                elif name=='all_progress_groups':
                    for group in settled['auto_by_group'].values():group['game_days']=max(1,group['count'])
                    settled['game_days']=sum(group['game_days'] for group in settled['auto_by_group'].values())
                    settled['zero_date_turns']=0
                elif name=='zero_count_mismatch':settled['zero_date_turns']+=1
                elif name=='auto_elapsed_mismatch':settled['rpc_elapsed_by_tool_seconds']['ck3_auto_turn']+=1
                elif name=='zero_turn_denominator':settled['turns']=0
                elif name=='zero_persistence_denominator':
                    next(row for row in values[names[1]]['stages'] if row['stage']=='driver.full_state_persistence')['nested_elapsed_sum_seconds']=0
                case_root=work/'cases'/name;evidence=case_root/'docs/ck3-native-ai/evidence';evidence.mkdir(parents=True)
                overrides=[]
                for role,filename in zip(roles,names,strict=True):
                    raw=source_bytes[filename] if values[filename]==source_data[filename] else (
                        json.dumps(values[filename],ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\\n').encode()
                    with (evidence/filename).open('xb') as stream:stream.write(raw)
                    if raw!=source_bytes[filename]:overrides.append({'role':role,'raw_json':raw.decode('utf-8')})
                receipt=case_root/'projection.json';scope['ROOT']=case_root;scope['EVIDENCE']=evidence
                previous_argv=sys.argv;sys.argv=[str(producer),'--receipt',str(receipt)]
                subprocess.check_output=checked_machine
                try:
                    with contextlib.redirect_stdout(io.StringIO()):main()
                except (AssertionError,ZeroDivisionError,ValueError,KeyError) as error:
                    cases.append({'name':name,'overrides':overrides,'accepted':False,'error_type':type(error).__name__})
                else:
                    result=json.loads(receipt.read_bytes())
                    cases.append({'name':name,'overrides':overrides,'accepted':True,'expected':result})
                finally:sys.argv=previous_argv;subprocess.check_output=original_check
            if producer.read_bytes()!=original:raise RuntimeError('producer changed during capture')
            for filename,raw in source_bytes.items():
                if (repo/'docs/ck3-native-ai/evidence'/filename).read_bytes()!=raw:raise RuntimeError('sealed source changed during capture')
            accepted=sum(row['accepted'] for row in cases)
            if accepted!=3 or len(cases)!=7:raise RuntimeError('producer branch capture incomplete')
            document={'schema':'xar.java.performance-windows-producer-golden/v1','machine_id':machine,
                'observed_at_utc':observed.isoformat(),'producer':{'path':str(producer),'bytes':len(original),'sha256':expected},
                'scope':'exact unchanged original main/read/arithmetic/serialization; copied sealed sources and fixed time/machine fixture seams; no live performance qualification',
                'python_optimization':True,'cases':cases,'source_refs':[
                    {'role':role,'path':'docs/ck3-native-ai/evidence/'+filename,'bytes':len(source_bytes[filename]),
                     'sha256':hashlib.sha256(source_bytes[filename]).hexdigest()}
                    for role,filename in zip(roles,names,strict=True)],
                'new_rpc_calls':0,'active_driver_or_save_reads':0,'new_saved_day_credit':0}
            payload=(json.dumps(document,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\\n').encode()
            if len(payload)>98304:raise RuntimeError('golden capture byte budget exceeded')
            sys.stdout.buffer.write(payload)
            """;
}
