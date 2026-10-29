package org.xar.ck3.control.wave2.finance.giftpendingreaders;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.util.List;
import org.xar.ck3.control.wave2.finance.capture.PythonStdinCapture;

/** Real producer to all current direct ledger readers; only the existing process observer is fixture supplied. */
public final class CaptureGiftPendingReadersGolden {
    private CaptureGiftPendingReadersGolden() { }
    public static void main(String[] args) throws Exception {
        if (args.length != 4) { throw new IllegalArgumentException("repository existing-python new-scratch output-json"); }
        PythonStdinCapture.requireCompiledLauncher(CaptureGiftPendingReadersGolden.class);
        Path root = Path.of(args[0]).toRealPath(); Path scratch = Path.of(args[2]).toAbsolutePath().normalize(); Path output = Path.of(args[3]).toAbsolutePath().normalize();
        if (Files.exists(scratch) || Files.exists(output)) { throw new IllegalArgumentException("never overwrite capture evidence"); }
        Files.createDirectories(scratch);
        byte[] raw = PythonStdinCapture.run(new PythonStdinCapture.Invocation(Path.of(args[1]), root,
                SCRIPT, List.of(root.toString(), scratch.toString()), Duration.ofSeconds(60), 65_536)).stdout();
        Files.createDirectories(output.getParent()); Files.write(output, raw, StandardOpenOption.CREATE_NEW); System.out.println("Captured actual ledger readers: " + raw.length + " bytes");
    }
    private static final String SCRIPT = """
            import sys,json,hashlib,subprocess,runpy,copy,datetime
            from pathlib import Path
            from unittest import mock
            root=Path(sys.argv[1]);scratch=Path(sys.argv[2]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            from xar_autoplayer import faction_gift_pending_v1 as p
            from xar_autoplayer.activity_feast_stage5_budget_v1 import observe_feast_start_budget_v1 as feast
            from xar_autoplayer.bridge.faction_gift_plan_augmentation_v1 import attach_faction_gift_private_candidate_v1 as augment
            from xar_autoplayer.m5_peacetime_proposal_sources_v1 import query_m5_peacetime_proposal_sources_v1 as peace
            from xar_autoplayer.m5_formal_proposal_collector import plan_m5_formal_query_only as collect
            core=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_faction_gift_pending_v1.py'))
            fixture=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_m5_formal_proposal_collector.py'))
            snapshot=fixture['_snapshot']();snapshot.update(active_wars=[],player_armies=[],active_event=None,pending_character_interaction=None)
            snapshot['played_character']['alive']=True
            obs=core['observation']();obs.update(player_character_id=snapshot['played_character']['character_id'],observed_date_raw=snapshot['date_raw'],snapshot_revision=snapshot['revision']-1,native_snapshot_revision=snapshot['native_revision']-1)
            begin={'request_id':'gift-readers-1','episode_run_id':snapshot['episode_run_id'],'source_round_id':'R742','source_bridge_pid':12345,'source_bridge_creation_date':'fixture-source-process','observation':obs,'minimum_gold_reserve_raw':10000000,'checkpoint_sha256_before_submit':'a'*64}
            state=scratch/'state';ledger=p.begin_faction_gift_submission_v1(state,**begin);path=p.faction_gift_ledger_path(state);before=path.read_bytes()
            inputs={'actor_character_id':snapshot['played_character']['character_id'],'snapshot_revision':snapshot['native_revision'],'date_raw':snapshot['date_raw'],'post_snapshot_id':snapshot['snapshot_id'],'queried_revision':snapshot['revision']}
            feast_result=feast(snapshot,inputs,state_dir=state)
            plan={'plan':{'selected_step':'life-advance'}};augmentation=augment(plan,snapshot,{'status':'targeting_present','root':{}},state_dir=state,query=None)
            driver=fixture['_ServiceDriver'](enabled=True,snapshot=snapshot);driver.state_dir=state;driver.allow_private_faction_gift_formal_trial=True;driver._session_bridge_pid=12345
            baseline={'policy':'one-life-turn-v1','phase':'peace_growth','selected_step':'life-advance'}
            try:peace(driver,snapshot=snapshot,history=[],baseline_plan=baseline,expected_revision=snapshot['revision'])
            except Exception as error:peace_result={'exception_class':type(error).__name__,'error':str(error)}
            else:raise RuntimeError('pending ledger unexpectedly admitted peacetime proposals')
            with mock.patch('xar_autoplayer.bridge.faction_gift_formal_route_v1._process_identity',return_value={'creation_date':'fixture-source-process'}):
                collector=collect(driver,{'revision':snapshot['revision'],'plan':baseline},snapshot=snapshot,history=[],available_steps=set())
            if driver.source_reads!=0:raise RuntimeError('pending collector read new proposal sources')
            if path.read_bytes()!=before:raise RuntimeError('read-only consumers changed original pending ledger')
            refs=[]
            for rel in ('ck3_autonomous_player/src/xar_autoplayer/faction_gift_pending_v1.py','ck3_autonomous_player/src/xar_autoplayer/activity_feast_stage5_budget_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/faction_gift_plan_augmentation_v1.py','ck3_autonomous_player/src/xar_autoplayer/m5_peacetime_proposal_sources_v1.py','ck3_autonomous_player/src/xar_autoplayer/m5_formal_proposal_collector.py','ck3_autonomous_player/src/xar_autoplayer/bridge/faction_gift_formal_route_v1.py','ck3_autonomous_player/tests/unit/test_faction_gift_pending_v1.py','ck3_autonomous_player/tests/unit/test_m5_formal_proposal_collector.py'):
                raw=(root/rel).read_bytes();refs.append({'path':rel,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
            machine=subprocess.run([sys.executable,str(root/'tools/ck3_live_run_id.py'),'machine'],check=True,capture_output=True,text=True).stdout.strip()
            result={'schema':'xar.giftpendingreaders.original-producer-consumers-golden/v1','machine_id':machine,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Actual producer and all direct scoped ledger readers; existing process identity reader fixture supplied, no native query, Game or runtime admission. Historical outcome reader is covered by giftoutcome leaf.','source_refs':refs,'begin':begin,'ledger':ledger,'snapshot':snapshot,'feast_budget':feast_result,'plan_augmentation':augmentation,'peacetime_guard':peace_result,'formal_collector':collector,'new_proposal_source_reads':driver.source_reads,'ledger_sha256_before':hashlib.sha256(before).hexdigest(),'ledger_sha256_after':hashlib.sha256(path.read_bytes()).hexdigest()}
            print(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False))
            """;
}
