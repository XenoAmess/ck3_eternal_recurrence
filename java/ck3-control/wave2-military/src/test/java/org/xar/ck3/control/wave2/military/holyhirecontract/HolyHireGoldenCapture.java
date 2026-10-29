package org.xar.ck3.control.wave2.military.holyhirecontract;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Once-only genuine legacy function capture, with explicitly synthetic offline transport callbacks. */
public final class HolyHireGoldenCapture {
    private HolyHireGoldenCapture() { }
    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 4) { throw new IllegalArgumentException("repository python-exe fresh-output.gz machine-id required"); }
        Path repository = Path.of(args[0]).toAbsolutePath().normalize(), output = Path.of(args[2]).toAbsolutePath().normalize();
        if (Files.exists(output)) { throw new IllegalArgumentException("fresh output required"); }
        ProcessBuilder builder = new ProcessBuilder(List.of(args[1], "-B", "-X", "utf8", "-c", PROGRAM, repository.toString(), args[3]));
        builder.directory(repository.toFile()); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTHONPATH", repository.resolve("ck3_autonomous_player/src") + File.pathSeparator + repository.resolve("ck3_autonomous_player/tests/unit"));
        builder.redirectError(ProcessBuilder.Redirect.INHERIT); Process process = builder.start(); byte[] bytes;
        try (var executor = Executors.newSingleThreadExecutor()) {
            var response = executor.submit(() -> { try (var stream = process.getInputStream()) { return stream.readNBytes(65_537); } });
            if (!process.waitFor(90, TimeUnit.SECONDS)) {
                process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly(); throw new IOException("producer capture timeout");
            }
            try { bytes = response.get(); } catch (ExecutionException error) { throw new IOException("producer read failed", error.getCause()); }
        }
        if (process.exitValue() != 0 || bytes.length == 0 || bytes.length > 65_536) { throw new IOException("capture failed/over budget: " + process.exitValue()); }
        Files.createDirectories(output.getParent()); Files.write(output, bytes, StandardOpenOption.CREATE_NEW);
        System.out.println("captured " + bytes.length + " bytes to " + output);
    }
    private static final String PROGRAM = """
            import sys,json,copy,hashlib,datetime,gzip
            from pathlib import Path
            from test_holy_order_siege_reinforcement_service_v1 import _SyntheticCurrentWorld
            from xar_autoplayer.bridge.hire_holy_order import validate_hire_holy_order_request_v1,normalize_hire_holy_order_v1
            from xar_autoplayer.bridge.player_holy_order_context_private_transport import query_player_holy_order_context_private_v1
            root=Path(sys.argv[1]); machine=sys.argv[2]; cases=[]
            def put(name,operation,x,fn):
                try: expected=fn(); case=dict(name=name,operation=operation,input=copy.deepcopy(x),accepted=True,expected=expected)
                except ValueError as error: case=dict(name=name,operation=operation,input=copy.deepcopy(x),accepted=False,original_error=str(error))
                cases.append(case)
            for name,id,revision in [('request-id-zero',0,0),('request-last-valid-ref',4294967294,10),('request-invalid-sentinel',4294967295,10),('request-bool-ref',True,10),('request-negative-revision',0,-1),('request-big-public-revision',0,2**80)]:
                x=dict(schema='xar.ck3.holy-hire-request-input.v1',holy_order_id=id,expected_revision=revision)
                def run(id=id,revision=revision):
                    validate_hire_holy_order_request_v1(id,revision); return dict(holy_order_id=id,expected_revision=revision)
                put(name,'request',x,run)
            w=_SyntheticCurrentWorld(); s=w.take_snapshot(); ack=w.hire_holy_order_v1(holy_order_id=0,expected_revision=10)
            def ackcase(name,edit,bind=False):
                value=copy.deepcopy(ack); edit(value); x=dict(schema='xar.ck3.holy-hire-ack-input.v1',snapshot=s,expected_holy_order_id=0,expected_revision=10,ack=value,bind_submission_frame=bind)
                def run():
                    out=normalize_hire_holy_order_v1(value,snapshot=s,expected_holy_order_id=0)
                    if bind: out.update(submitted_snapshot_id=s['snapshot_id'],submitted_revision=10,submitted_native_revision=s['native_revision'])
                    return out
                put(name,'ack',x,run)
            ackcase('submitted-ack-preserved',lambda a:None)
            ackcase('native-driver-submitted-binding',lambda a:None,True)
            ackcase('rejected-ack-preserved',lambda a:(a.update(accepted=False,status='rejected'),a['holy_order_hire'].update(status='rejected',command_submitted=False,verification_pending=False)))
            ackcase('already-hired-is-still-no-after-state',lambda a:(a.update(status='already_hired'),a['holy_order_hire'].update(status='already_hired',command_submitted=False,verification_pending=False,prior_employer_character_id=29829)))
            ackcase('unavailable-without-prior-capture',lambda a:(a.update(accepted=False,status='unavailable'),a['holy_order_hire'].update(status='unavailable',command_submitted=False,verification_pending=False,prior_context=None)))
            for name,edit in [('ack-is-not-independent-after-state',lambda a:a['holy_order_hire'].update(after_state_observed=True)),('wrong-native-frame',lambda a:a.update(snapshot_revision=10)),('invalid-native-mode',lambda a:a['holy_order_hire'].update(native_hire_mode=4)),('accepted-status-conflict',lambda a:a.update(accepted=False)),('unobservable-validity-conflict',lambda a:a['holy_order_hire'].update(native_command_validation_observable=False)),('unsubmitted-claims-mutation',lambda a:(a.update(accepted=False,status='rejected'),a['holy_order_hire'].update(status='rejected'))),('invalid-prior-employer-sentinel',lambda a:a['holy_order_hire'].update(prior_employer_character_id=4294967295)),('bool-command-sequence',lambda a:a.update(command_sequence=True)),('wrong-current-actor',lambda a:a['holy_order_hire'].update(actor_character_id=29830)),('submitted-without-native-validation',lambda a:a['holy_order_hire'].update(native_command_valid=False))]: ackcase(name,edit)
            def querycase(name,edit):
                world=_SyntheticCurrentWorld(); before=world.take_snapshot(); context=world.query_player_holy_order_context_private_v1(expected_revision=10)
                result=dict(step='query-player-holy-order-context-v1',accepted=True,private_build=True,read_only=True,advertised=False,game_version=context['game_version'],executable_sha256=context['executable_sha256'],snapshot_revision=before['native_revision'],date_raw=before['date_raw'],backend_id='ck3-1.20.0.4-native-player-holy-order-context-v1',domain_key='player_holy_order_context_v1',status='observed',player_holy_order_context=context)
                edit(result)
                class Reader:
                    allow_private_player_religion_context_query=True
                    def __init__(self): self.endpoint=self; self.state=self; self.request=None; self.packet=None
                    def take_snapshot(self): return copy.deepcopy(before)
                    def send(self,request): self.request=request
                    def wait_for_command_result(self,request_id,timeout):
                        self.packet=dict(type='command_result',protocol_version=1,request_id=request_id,ok=True,result=copy.deepcopy(result)); return self.packet
                driver=Reader()
                try: expected=query_player_holy_order_context_private_v1(driver,expected_revision=10); accepted=True; error=None
                except Exception as ex: expected=None; accepted=False; error=str(ex)
                if driver.packet is None: raise RuntimeError('actual read helper did not consume packet')
                x=dict(schema='xar.ck3.holy-context-query-input.v1',before_snapshot=before,after_snapshot=copy.deepcopy(before),expected_revision=10,request_id=driver.request['request_id'],packet=driver.packet)
                case=dict(name=name,operation='query',input=x,accepted=accepted)
                if accepted:case['expected']=expected
                else:case['original_error']=error
                cases.append(case)
            querycase('query-normalized-current-context',lambda r:None)
            querycase('query-unavailable-status-preserved',lambda r:(r.update(status='unavailable'),r['player_holy_order_context'].update(available=False,unavailable_reason='current input unavailable')))
            querycase('query-status-mismatch-rejected',lambda r:r.update(status='unavailable'))
            querycase('query-native-frame-mismatch-rejected',lambda r:r.update(snapshot_revision=10))
            querycase('query-build-backend-mismatch-rejected',lambda r:r.update(backend_id='ck3-1.20.0.3-native-player-holy-order-context-v1'))
            paths=['ck3_autonomous_player/src/xar_autoplayer/bridge/hire_holy_order.py','ck3_autonomous_player/src/xar_autoplayer/bridge/player_holy_order_context_private_transport.py','ck3_autonomous_player/src/xar_autoplayer/bridge/g2_private_query_transport.py','ck3_autonomous_player/src/xar_autoplayer/bridge/timeline_blocker_private_transport.py','ck3_autonomous_player/src/xar_autoplayer/bridge/nonwar_private_build.py','ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py','ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py','ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py','ck3_autonomous_player/src/xar_autoplayer/bridge/service.py','ck3_autonomous_player/tests/unit/test_holy_order_siege_reinforcement_service_v1.py','ck3_autonomous_player/tests/unit/test_holy_order_hire_registered_mcp_v1.py']
            pins=[dict(path=path,sha256=hashlib.sha256((root/path).read_bytes()).hexdigest()) for path in paths]
            output=dict(schema='xar.ck3.holy-hire-contract-golden.v1',machine_id=machine,captured_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_machine_id='unknown',actual_original_normalizers=True,actual_private_query_helper=True,synthetic_transport_callbacks=True,game_operations=0,source_pins=pins,cases=cases)
            raw=json.dumps(output,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
            if len(raw)>262144: raise RuntimeError('uncompressed capture exceeds budget')
            packed=gzip.compress(raw,mtime=0)
            if len(packed)>65536: raise RuntimeError('compressed capture exceeds budget')
            sys.stdout.buffer.write(packed)
            """;
}
