package org.xar.ck3.control.wave2.finance.giftpendingroute;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.util.List;
import org.xar.ck3.control.wave2.finance.capture.PythonStdinCapture;

/** Original fixed receipt/cold read routes, actual producer/writer/reducer and existing test transport. */
public final class CaptureGiftPendingReadRouteGolden {
    private CaptureGiftPendingReadRouteGolden() { }
    public static void main(String[] args) throws Exception {
        if (args.length != 4) { throw new IllegalArgumentException("repository existing-python new-scratch output-json"); }
        PythonStdinCapture.requireCompiledLauncher(CaptureGiftPendingReadRouteGolden.class);
        Path root = Path.of(args[0]).toRealPath(); Path scratch = Path.of(args[2]).toAbsolutePath().normalize(); Path output = Path.of(args[3]).toAbsolutePath().normalize();
        if (Files.exists(scratch) || Files.exists(output)) { throw new IllegalArgumentException("capture does not overwrite evidence"); }
        Files.createDirectories(scratch);
        byte[] raw = PythonStdinCapture.run(new PythonStdinCapture.Invocation(Path.of(args[1]), root,
                SCRIPT, List.of(root.toString(), scratch.toString()), Duration.ofSeconds(60), 98_304)).stdout();
        Files.createDirectories(output.getParent()); Files.write(output, raw, StandardOpenOption.CREATE_NEW); System.out.println("Captured original pending read routes: " + raw.length + " bytes");
    }
    private static final String SCRIPT = """
            import sys,json,hashlib,subprocess,runpy,copy,datetime
            from pathlib import Path
            from unittest import mock
            from types import SimpleNamespace
            root=Path(sys.argv[1]);scratch=Path(sys.argv[2]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            from xar_autoplayer.bridge import faction_gift_formal_route_v1 as route
            from xar_autoplayer.faction_gift_pending_v1 import read_faction_gift_ledger_v1
            fixture=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_faction_gift_formal_route_v1.py'))
            original_test=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_faction_gift_pending_v1.py'))
            cold_test=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_faction_gift_cold_recovery_contract_v1.py'))
            query_id='faction-gift-'+'0'*32;cases=[]
            for name in ('receipt_applied','receipt_wrong_gold','receipt_timeout','receipt_wrong_process','receipt_revision_changed','cold_applied','cold_unchanged','cold_unknown','cold_timeout','cold_same_process','cold_invalid_birth'):
                state=scratch/name;pending=fixture['pending'](state);before_ledger=copy.deepcopy(read_faction_gift_ledger_v1(state));cold=name.startswith('cold_')
                snapshot=fixture['snapshot'](revision=1 if cold else 414,native_revision=2 if cold else 14)
                driver=fixture['Driver'](state,snapshot);driver._session_bridge_pid=23456 if cold else 12345;driver.private_faction_round_id='R744' if cold else 'R742'
                birth='20261019051054.525693+000' if cold else pending['source_bridge_creation_date'];checkpoint=None;expected_revision=snapshot['revision']
                if cold:
                    post=cold_test['recovery']()['post_observation'];post.update(snapshot_revision=2,native_snapshot_revision=3,observed_date_raw=pending['pre_date_raw'])
                    checkpoint={'status':'saved','sha256':'b'*64,'date_raw':snapshot['date_raw'],'episode_run_id':snapshot['episode_run_id']}
                    if name=='cold_unchanged':
                        checkpoint['sha256']='a'*64
                        post.update(player_gold_raw=pending['pre_player_gold_raw'],gift_opinion_present=False,gift_opinion_modifier_value=None,recipient_opinion_of_player=pending['pre_recipient_opinion_of_player'],source_faction_present=True,source_faction_targeting_player=True,source_faction_metrics_available=True,source_faction_power_raw=pending['pre_source_faction_power_raw'],source_faction_discontent_raw=pending['pre_source_faction_discontent_raw'],source_faction_member_character_ids=pending['pre_source_faction_member_character_ids'])
                    native_result={'step':route.COLD_RECOVERY_STEP,'private_build':True,'advertised':False,'status':'independent_read_complete','native':{'failure_flags':0,'observation':post}}
                    if name=='cold_unknown':native_result['native']={'failure_flags':1,'observation':{}}
                    if name=='cold_same_process':driver._session_bridge_pid=12345;birth=pending['source_bridge_creation_date']
                    if name=='cold_invalid_birth':birth='malformed-birth'
                else:
                    receipt=original_test['receipt']();receipt.update(request_id=pending['request_id'],post_snapshot_revision=pending['pre_snapshot_revision']+1,post_native_snapshot_revision=pending['pre_native_snapshot_revision']+1,post_observed_date_raw=pending['pre_date_raw'])
                    if name=='receipt_wrong_gold':receipt['post_player_gold_raw']=pending['pre_player_gold_raw']
                    native_result={'step':route.RECEIPT_STEP,'status':'applied','receipt':receipt}
                    if name=='receipt_wrong_process':driver._session_bridge_pid=23456;birth='20261019051054.525693+000'
                    if name=='receipt_revision_changed':expected_revision+=1
                driver._last_checkpoint=checkpoint;timeout=name.endswith('_timeout');driver.state.result=None if timeout else native_result
                envelope=None if timeout else {'type':'command_result','protocol_version':1,'request_id':query_id,'ok':True,'result':native_result}
                try:
                    with mock.patch('xar_autoplayer.bridge.faction_gift_formal_route_v1._process_identity',return_value={'creation_date':birth}),mock.patch('xar_autoplayer.bridge.faction_gift_formal_route_v1.uuid.uuid4',return_value=SimpleNamespace(hex='0'*32)):
                        result=(route.query_faction_gift_cold_recovery_private_v1 if cold else route.query_faction_gift_receipt_private_v1)(driver,pending=pending,expected_revision=expected_revision)
                    expected={'returned':True,'result':result}
                except Exception as error:
                    expected={'returned':False,'exception_class':type(error).__name__,'error':str(error)}
                    if hasattr(error,'step_result'):expected['step_result']=error.step_result
                cases.append({'name':name,'cold':cold,'pending_ledger':before_ledger,'snapshot':snapshot,'expected_revision':expected_revision,'current_process':{'pid':driver._session_bridge_pid,'creation_date':birth},'round_id':driver.private_faction_round_id,'checkpoint':checkpoint,'raw_envelope_json':None if envelope is None else json.dumps(envelope,sort_keys=True,separators=(',',':'),allow_nan=False),'expected':expected,'sent':driver.endpoint.sent,'recorded':driver.recorded,'ledger_after':read_faction_gift_ledger_v1(state)})
            refs=[]
            for rel in ('ck3_autonomous_player/src/xar_autoplayer/bridge/faction_gift_formal_route_v1.py','ck3_autonomous_player/src/xar_autoplayer/faction_gift_pending_v1.py','ck3_autonomous_player/src/xar_autoplayer/faction_gift_cold_recovery_contract_v1.py','ck3_autonomous_player/src/xar_autoplayer/environment.py','ck3_autonomous_player/tests/unit/test_faction_gift_formal_route_v1.py','ck3_autonomous_player/tests/unit/test_faction_gift_pending_v1.py','ck3_autonomous_player/tests/unit/test_faction_gift_cold_recovery_contract_v1.py'):
                raw=(root/rel).read_bytes();refs.append({'path':rel,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
            machine=subprocess.run([sys.executable,str(root/'tools/ck3_live_run_id.py'),'machine'],check=True,capture_output=True,text=True).stdout.strip()
            result={'schema':'xar.giftpendingroute.original-producer-consumer-golden/v1','machine_id':machine,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Actual original two fixed read routes, reducer and scoped writer; existing fixture supplies process/native read results. No Game, pipe, canonical writer or lock qualification.','source_refs':refs,'query_id':query_id,'cases':cases}
            print(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False))
            """;
}
