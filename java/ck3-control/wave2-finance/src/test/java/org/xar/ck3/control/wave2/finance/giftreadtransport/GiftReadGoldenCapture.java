package org.xar.ck3.control.wave2.finance.giftreadtransport;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.List;
import org.xar.ck3.control.wave2.finance.capture.PythonStdinCapture;

/** Offline source capture, executed only by the shared qualified whole-tree Job owner. */
public final class GiftReadGoldenCapture {
    private GiftReadGoldenCapture() { }
    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 3) { throw new IllegalArgumentException("python repo new-output-gzip required"); }
        PythonStdinCapture.requireCompiledLauncher(GiftReadGoldenCapture.class);
        Path output = Path.of(args[2]).toAbsolutePath();
        if (Files.exists(output)) { throw new IllegalArgumentException("capture output must be new"); }
        var result = PythonStdinCapture.run(new PythonStdinCapture.Invocation(Path.of(args[0]), Path.of(args[1]),
                SCRIPT, List.of(args[1], output.toString()), Duration.ofSeconds(90), 16_384));
        System.out.write(result.stdout()); System.out.flush();
        if (!Files.isRegularFile(output) || Files.size(output) == 0 || Files.size(output) > 48_000) {
            throw new IllegalStateException("bounded gzip golden required");
        }
    }
    private static final String SCRIPT = """
            import sys,json,copy,hashlib,datetime,gzip
            from pathlib import Path
            from types import SimpleNamespace
            from unittest.mock import patch
            repo=Path(sys.argv[1]); output=Path(sys.argv[2])
            sys.path.insert(0,str(repo/'ck3_autonomous_player/src'))
            sys.path.insert(0,str(repo/'ck3_autonomous_player/tests/unit'))
            from test_faction_gift_formal_candidate_v1 import snapshot,root,private_result
            from xar_autoplayer.bridge.faction_gift_private_transport_v1 import query_faction_gift_private_candidate_v1
            cases=[]
            def add(name,change=None):
                expected=snapshot(); before=copy.deepcopy(expected); after=copy.deepcopy(expected)
                scenario={'request':{'schema':'xar.gift-read-transport-input.v1','snapshot':expected,'root':root(1),'minimum_gold_reserve_raw':10000000,'timeout_seconds':30},'before':before,'after':after,
                    'diagnostics':{'last_heartbeat':{'g2_faction_gift_mitigation_async_glue_v1':{'private_build':True}}},
                    'private_result':private_result(),'reply_overrides':{},'timeout':False}
                if change is not None: change(scenario)
                class Driver:
                    def __init__(self):
                        self.snapshots=0;self.diagnostic_reads=0;self.sent=[];self.waits=0
                        self.endpoint=SimpleNamespace(send=lambda command:self.sent.append(copy.deepcopy(command)))
                        self.state=SimpleNamespace(wait_for_command_result=self.wait)
                    def take_internal_semantic_snapshot(self):
                        self.snapshots+=1
                        return copy.deepcopy(scenario['before'] if self.snapshots==1 else scenario['after'])
                    def diagnostics(self):
                        self.diagnostic_reads+=1;return copy.deepcopy(scenario['diagnostics'])
                    def wait(self,request_id,timeout):
                        self.waits+=1
                        if scenario['timeout']:return None
                        return {'type':'command_result','protocol_version':1,'request_id':request_id,'ok':True,'result':copy.deepcopy(scenario['private_result']),**scenario['reply_overrides']}
                driver=Driver()
                with patch('xar_autoplayer.bridge.faction_gift_private_transport_v1.uuid.uuid4',return_value=SimpleNamespace(hex='0'*32)):
                    try:
                        result=query_faction_gift_private_candidate_v1(driver,snapshot=scenario['request']['snapshot'],same_frame_root=scenario['request']['root'],minimum_gold_reserve_raw=scenario['request']['minimum_gold_reserve_raw'],timeout_seconds=scenario['request']['timeout_seconds'])
                        outcome={'kind':'return','result':result}
                    except Exception as error:
                        outcome={'kind':'error','error_type':type(error).__name__,'message':str(error)}
                cases.append({'name':name,'scenario':scenario,'expected':outcome,'effects':{'snapshots':driver.snapshots,'diagnostic_reads':driver.diagnostic_reads,'send_count':len(driver.sent),'wait_count':driver.waits,'commands':driver.sent}})
            add('selected')
            add('private_route_off',lambda s:s.update(diagnostics={}))
            add('source_changed',lambda s:s['before'].update(revision=413))
            add('ordinary_unpaused',lambda s:(s['request']['snapshot'].update(paused=False),s['before'].update(paused=False)))
            add('ordinary_terminal',lambda s:(s['request']['snapshot'].update(one_life_terminal_reason='dead'),s['before'].update(one_life_terminal_reason='dead')))
            add('root_government',lambda s:s['request']['root'].update(government={'key':'clan_government'}))
            add('root_stale',lambda s:s['request']['root'].update(snapshot_revision=411))
            add('root_empty_count',lambda s:s['request']['root'].update(player_targeting_faction_count=0))
            add('timed_out',lambda s:s.update(timeout=True))
            add('wrong_response_id',lambda s:s['reply_overrides'].update(request_id='unrelated'))
            add('wrong_response_type',lambda s:s['reply_overrides'].update(type='heartbeat'))
            add('native_red',lambda s:s['reply_overrides'].update(ok=False,error='native-refused'))
            add('result_missing',lambda s:s['reply_overrides'].update(result=None))
            add('frame_crossed',lambda s:s['after'].update(revision=413))
            add('active_event_after',lambda s:s['after'].update(active_event={'instance_id':71}))
            add('null_get_missing_equivalence',lambda s:s['before'].pop('active_event'))
            add('terminal_reason_not_in_after_binding',lambda s:s['after'].update(one_life_terminal_reason='unread_legacy_field'))
            sources=['ck3_autonomous_player/src/xar_autoplayer/bridge/faction_gift_private_transport_v1.py','ck3_autonomous_player/src/xar_autoplayer/faction_gift_formal_candidate_v1.py','ck3_autonomous_player/src/xar_autoplayer/faction_gift_policy_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/driver.py','ck3_autonomous_player/tests/unit/test_faction_gift_formal_candidate_v1.py']
            capture={'schema':'xar.gift-read-transport-original-producer-golden.v1','machine_id':'xenoamess-full-tower-eb9d2c1186','observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'capture_method':'Real unchanged private query producer and real candidate/policy; only original owned-driver IO is synthetic. Stable UUID for deterministic evidence. No live native pipe, RPC or Game.','source_bindings':[{'path':path,'sha256':hashlib.sha256((repo/path).read_bytes()).hexdigest()} for path in sources],'cases':cases}
            raw=(json.dumps(capture,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode('utf-8')
            if len(raw)>180000:raise ValueError('uncompressed artifact budget exceeded')
            packed=gzip.compress(raw,mtime=0)
            if len(packed)>48000:raise ValueError('gzip artifact budget exceeded')
            output.parent.mkdir(parents=True,exist_ok=True)
            with output.open('xb') as handle:handle.write(packed)
            print(json.dumps({'cases':len(cases),'bytes':len(packed),'uncompressed_bytes':len(raw),'sha256':hashlib.sha256(packed).hexdigest(),'machine_id':capture['machine_id'],'observed_at_utc':capture['observed_at_utc']}))
            """;
}
