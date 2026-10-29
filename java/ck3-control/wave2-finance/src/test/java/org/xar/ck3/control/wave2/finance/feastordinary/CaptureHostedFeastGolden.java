package org.xar.ck3.control.wave2.finance.feastordinary;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Explicit one-time differential capture. Default JUnit never launches this tool or Python. */
public final class CaptureHostedFeastGolden {
    private CaptureHostedFeastGolden() { }

    public static void main(String[] arguments) throws IOException, InterruptedException {
        if (arguments.length != 3) throw new IllegalArgumentException("expected repository, Python executable and fresh output path");
        Path root = Path.of(arguments[0]).toAbsolutePath().normalize();
        Path python = Path.of(arguments[1]).toAbsolutePath().normalize();
        Path output = Path.of(arguments[2]).toAbsolutePath().normalize();
        if (Files.exists(output)) throw new IllegalArgumentException("capture output already exists");
        String code = """
                import copy,datetime,hashlib,json,subprocess,sys,unittest
                from pathlib import Path
                root=Path(sys.argv[1]).resolve()
                output=Path(sys.argv[2]).resolve()
                sys.path.insert(0,str(root/'ck3_autonomous_player'/'src'))
                sys.path.insert(0,str(root/'ck3_autonomous_player'/'tests'/'unit'))
                from xar_autoplayer.bridge.activity_feast_stage5_start_private_transport import _hosted,POST_SCHEMA
                from xar_autoplayer.bridge.driver import BridgeUnavailableError
                import test_activity_feast_stage5_start_private_transport as existing_test
                source=root/'ck3_autonomous_player/src/xar_autoplayer/bridge/activity_feast_stage5_start_private_transport.py'
                tests=root/'ck3_autonomous_player/tests/unit/test_activity_feast_stage5_start_private_transport.py'
                refs=[dict(path=str(path),bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in (source,tests)]
                outcome=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromModule(existing_test))
                if not outcome.wasSuccessful() or outcome.skipped:
                    raise RuntimeError('existing transport tests did not pass with zero skips')
                base=dict(activity_id=18,host_character_id=29829,activity_type_key='activity_feast')
                cases=[]
                def add(name,value):
                    cases.append((name,json.dumps(value,ensure_ascii=False,separators=(',',':'))))
                add('empty',[])
                add('existing_common_payload',existing_test.common_payload(POST_SCHEMA)['hosted_activities'])
                add('identity_only',[base])
                add('terminal_ongoing',[dict(base,terminal_flags_observed=True,native_completed=False,native_invalidated=False)])
                add('terminal_completed',[dict(base,terminal_flags_observed=True,native_completed=True,native_invalidated=False)])
                add('terminal_invalidated',[dict(base,terminal_flags_observed=True,native_completed=False,native_invalidated=True)])
                add('terminal_both',[dict(base,terminal_flags_observed=True,native_completed=True,native_invalidated=True)])
                add('stamp_unknown',[dict(base,native_completion_stamp_observed=False,native_completion_stamp_raw=None)])
                add('stamp_zero',[dict(base,native_completion_stamp_observed=True,native_completion_stamp_raw=0)])
                add('stamp_uint64_max',[dict(base,native_completion_stamp_observed=True,native_completion_stamp_raw=2**64-1)])
                add('terminal_and_stamp',[dict(base,terminal_flags_observed=True,native_completed=True,native_invalidated=False,native_completion_stamp_observed=True,native_completion_stamp_raw=134371430348828741)])
                add('identity_uint32_max',[dict(base,activity_id=2**32-1,host_character_id=2**32-1)])
                add('other_activity_kind',[dict(base,activity_type_key='activity_hunt')])
                add('unicode_63_codepoints',[dict(base,activity_type_key=chr(0x1f525)*63)])
                add('maximum_64_rows',[dict(base,activity_id=index+1) for index in range(64)])
                add('over_64_rows',[dict(base,activity_id=index+1) for index in range(65)])
                add('duplicate_identity',[base,base])
                add('root_null',None)
                add('root_object',base)
                add('row_null',[None])
                add('missing_identity_field',[dict(activity_id=18,activity_type_key='activity_feast')])
                add('extra_field',[dict(base,unqualified=True)])
                for field in ('activity_id','host_character_id'):
                    for name,value in [('zero',0),('negative',-1),('overflow',2**32),('bool',True),('float',18.0),('string','18'),('null',None)]:
                        add(field+'_'+name,[dict(base,**{field:value})])
                for name,value in [('empty',''),('long','x'*64),('null',None),('int',1)]:
                    add('activity_type_'+name,[dict(base,activity_type_key=value)])
                add('terminal_false_observed',[dict(base,terminal_flags_observed=False,native_completed=False,native_invalidated=False)])
                add('terminal_partial',[dict(base,terminal_flags_observed=True,native_completed=False)])
                add('terminal_missing_observed',[dict(base,native_completed=False,native_invalidated=False)])
                add('terminal_null_completed',[dict(base,terminal_flags_observed=True,native_completed=None,native_invalidated=False)])
                add('terminal_numeric_completed',[dict(base,terminal_flags_observed=True,native_completed=1,native_invalidated=False)])
                add('stamp_partial',[dict(base,native_completion_stamp_observed=True)])
                add('stamp_without_observed',[dict(base,native_completion_stamp_raw=1)])
                add('stamp_unobserved_with_zero',[dict(base,native_completion_stamp_observed=False,native_completion_stamp_raw=0)])
                add('stamp_observed_null',[dict(base,native_completion_stamp_observed=True,native_completion_stamp_raw=None)])
                for name,value in [('negative',-1),('overflow',2**64),('bool',True),('float',1.0),('string','1')]:
                    add('stamp_'+name,[dict(base,native_completion_stamp_observed=True,native_completion_stamp_raw=value)])
                rows=[]
                for name,raw in cases:
                    value=json.loads(raw)
                    try:
                        result=_hosted(value)
                        accepted=True
                        error=None
                        if result and result[0] is value[0]:
                            raise RuntimeError('producer failed to copy hosted row')
                    except BridgeUnavailableError as exception:
                        accepted=False
                        result=None
                        error=dict(type=type(exception).__name__,message=str(exception))
                    rows.append(dict(name=name,input_json=raw,accepted=accepted,result=result,error=error))
                after=[dict(path=str(path),bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in (source,tests)]
                if refs!=after:
                    raise RuntimeError('producer source changed during capture')
                machine=subprocess.run([sys.executable,str(root/'tools/ck3_live_run_id.py'),'machine'],cwd=root,capture_output=True,text=True,check=True,timeout=20).stdout.strip()
                payload=dict(schema='xar.feast-ordinary-hosted-golden/v1',machine_id=machine,observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_refs=refs,capture_scope='actual _hosted producer invoked for every raw-token vector; no Game/RPC/native/ledger access',existing_tests=dict(run=outcome.testsRun,failures=len(outcome.failures),errors=len(outcome.errors),skipped=len(outcome.skipped)),cases=rows)
                encoded=(json.dumps(payload,ensure_ascii=False,indent=2)+chr(10)).encode('utf-8')
                if len(encoded)>98304:
                    raise RuntimeError('capture exceeds bounded output budget')
                output.parent.mkdir(parents=True,exist_ok=True)
                with output.open('xb') as stream:
                    stream.write(encoded)
                print(json.dumps(dict(cases=len(rows),bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest(),output=str(output))))
                """;
        ProcessBuilder builder = new ProcessBuilder(List.of(python.toString(), "-c", code, root.toString(), output.toString()));
        builder.directory(root.toFile()).inheritIO();
        Process process = builder.start();
        if (!process.waitFor(90, TimeUnit.SECONDS)) {
            process.destroyForcibly();
            process.waitFor();
            throw new IOException("hosted feast capture exceeded 90 seconds");
        }
        if (process.exitValue() != 0) throw new IOException("hosted feast capture exit " + process.exitValue());
    }
}
