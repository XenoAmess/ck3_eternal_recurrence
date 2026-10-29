package org.xar.ck3.control.wave2.finance.giftpending;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Once-only capture of the original producer. Run only by the shared bounded Job owner. */
public final class CaptureGiftPendingGolden {
    private CaptureGiftPendingGolden() { }
    public static void main(String[] args) throws Exception {
        if (args.length != 4) { throw new IllegalArgumentException("repository existing-python new-scratch output-json"); }
        Path root = Path.of(args[0]).toRealPath(); Path scratch = Path.of(args[2]).toAbsolutePath().normalize();
        Path output = Path.of(args[3]).toAbsolutePath().normalize();
        if (Files.exists(scratch) || Files.exists(output)) { throw new IllegalArgumentException("never overwrite original evidence or scratch"); }
        Files.createDirectories(scratch);
        Process child = new ProcessBuilder(List.of(args[1], "-B", "-c", SCRIPT, root.toString(), scratch.toString()))
                .directory(root.toFile()).redirectError(ProcessBuilder.Redirect.INHERIT).start();
        byte[] raw;
        try (var readers = Executors.newVirtualThreadPerTaskExecutor()) {
            var read = readers.submit(() -> child.getInputStream().readNBytes(98_305));
            if (!child.waitFor(Duration.ofSeconds(60).toMillis(), TimeUnit.MILLISECONDS)) {
                child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly();
                throw new IllegalStateException("original gift producer capture timed out");
            }
            raw = read.get(5, TimeUnit.SECONDS);
        } finally { if (child.isAlive()) { child.destroyForcibly(); } }
        if (child.exitValue() != 0 || raw.length == 0 || raw.length > 98_304) {
            throw new IllegalStateException("producer capture failed: exit=" + child.exitValue() + " bytes=" + raw.length);
        }
        Files.createDirectories(output.getParent()); Files.write(output, raw, StandardOpenOption.CREATE_NEW);
        System.out.println("Captured original pending producer: " + raw.length + " bytes");
    }
    private static final String SCRIPT = """
            import sys,json,hashlib,subprocess,runpy,copy,datetime
            from pathlib import Path
            root=Path(sys.argv[1]);scratch=Path(sys.argv[2]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            from xar_autoplayer import faction_gift_pending_v1 as p
            from xar_autoplayer.faction_gift_cold_recovery_contract_v1 import evaluate_faction_gift_cold_recovery_v1 as classify
            test=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_faction_gift_pending_v1.py'))
            coldtest=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_faction_gift_cold_recovery_contract_v1.py'))
            begin={'request_id':'gift-real-1','episode_run_id':'native-32904-a','source_round_id':'R742','source_bridge_pid':12345,'source_bridge_creation_date':'2026-09-16T12:00:00Z','observation':test['observation'](),'minimum_gold_reserve_raw':10000000,'checkpoint_sha256_before_submit':'a'*64}
            ack={'request_id':'gift-real-1','status':'submitted_verification_pending','verification_pending':True,'source_faction_id':771,'recipient_character_id':33011,'native_extension':{'empty':[],'nullable':None,'exact_integer':18446744073709551615,'float_extension':1.0}}
            receipt=test['receipt']();state=scratch/'state';states={}
            states['empty']=copy.deepcopy(p.read_faction_gift_ledger_v1(state))
            states['begun']=copy.deepcopy(p.begin_faction_gift_submission_v1(state,**begin))
            states['acknowledged']=copy.deepcopy(p.mark_faction_gift_ack_pending_v1(state,request_id='gift-real-1',ack=ack))
            states['restored']=copy.deepcopy(p.mark_faction_gift_restore_requery_v1(state,request_id='gift-real-1'))
            states['completed']=copy.deepcopy(p.complete_faction_gift_after_independent_receipt_v1(state,request_id='gift-real-1',receipt=receipt))
            pending=states['begun']['pending'];cases=[]
            def cold(name,r):cases.append({'name':name,'recovery':r,'expected':classify(pending,r)})
            r=coldtest['recovery']();cold('applied_absent',copy.deepcopy(r))
            r['independent_faction_storage_lookup_complete']=False;cold('unresolved_independent_lookup_missing',copy.deepcopy(r))
            r=coldtest['recovery']();r['new_round_id']='R742';cold('unresolved_old_round',copy.deepcopy(r))
            r=coldtest['recovery']();r['save_is_pre_action_checkpoint']=True;r['selected_save_sha256']='a'*64
            r['post_observation'].update(player_gold_raw=25000000,gift_opinion_present=False,gift_opinion_modifier_value=None,recipient_opinion_of_player=-40,source_faction_present=True,source_faction_targeting_player=True,source_faction_metrics_available=True,source_faction_power_raw=65000000,source_faction_discontent_raw=45000000,source_faction_member_character_ids=[33011])
            cold('unchanged_exact_checkpoint',copy.deepcopy(r));r['selected_save_sha256']='b'*64;cold('unresolved_wrong_checkpoint',copy.deepcopy(r))
            failures=[]
            for name,operation in [('pending_blocks_second',lambda:p.begin_faction_gift_submission_v1(scratch/'pending',**begin)),('resolved_blocks_old_id',lambda:p.begin_faction_gift_submission_v1(state,**begin))]:
                if name=='pending_blocks_second':p.begin_faction_gift_submission_v1(scratch/'pending',**begin)
                try:operation()
                except ValueError as error:failures.append({'name':name,'error':str(error)})
                else:raise RuntimeError('original expected rejection did not occur: '+name)
            for case in cases:
                target=scratch/case['name'];p.begin_faction_gift_submission_v1(target,**begin)
                case['resolved_result']=p.resolve_faction_gift_after_cold_native_query_v1(target,request_id='gift-real-1',recovery=case['recovery'])
                case['ledger_after']=p.read_faction_gift_ledger_v1(target)
            refs=[]
            for rel in ('ck3_autonomous_player/src/xar_autoplayer/faction_gift_pending_v1.py','ck3_autonomous_player/src/xar_autoplayer/faction_gift_cold_recovery_contract_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/faction_gift_formal_route_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/faction_gift_plan_augmentation_v1.py','ck3_autonomous_player/src/xar_autoplayer/activity_feast_stage5_budget_v1.py','ck3_autonomous_player/src/xar_autoplayer/m5_peacetime_proposal_sources_v1.py','ck3_autonomous_player/src/xar_autoplayer/m5_formal_proposal_collector.py','ck3_autonomous_player/src/xar_autoplayer/faction_gift_outcome_v1.py','ck3_autonomous_player/tests/unit/test_faction_gift_pending_v1.py','ck3_autonomous_player/tests/unit/test_faction_gift_cold_recovery_contract_v1.py'):
                raw=(root/rel).read_bytes();refs.append({'path':rel,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
            machine=subprocess.run([sys.executable,str(root/'tools/ck3_live_run_id.py'),'machine'],check=True,capture_output=True,text=True).stdout.strip()
            result={'schema':'xar.giftpending.original-producer-golden/v1','machine_id':machine,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Original pending producer and dynamic cold classifier with temporary scoped files; not Game or canonical ledger acceptance.','source_refs':refs,'begin':begin,'ack':ack,'receipt':receipt,'ledgers':states,'cold_cases':cases,'rejections':failures}
            print(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False))
            """;
}
