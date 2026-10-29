package org.xar.ck3.control.wave2.governance.marriagehandoff;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Explicit offline original producer capture, executed only by the shared storage/M7 scheduler. */
public final class CaptureMarriageHandoffGolden {
    private static final int MAXIMUM_BYTES = 110_000;
    private CaptureMarriageHandoffGolden() { }
    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 4) { throw new IllegalArgumentException("repository-root existing-python output-json approved-temporary-root"); }
        Path root = Path.of(arguments[0]).toRealPath(); Path output = Path.of(arguments[2]).toAbsolutePath().normalize();
        Path temporary = Path.of(arguments[3]).toRealPath();
        if (Files.exists(output)) { throw new IllegalArgumentException("capture never replaces original evidence"); }
        ProcessBuilder builder = new ProcessBuilder(List.of(arguments[1], "-B", "-c", SCRIPT, root.toString(), temporary.toString()));
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTHONUTF8", "1"); builder.environment().put("PYTHONIOENCODING", "utf-8");
        builder.environment().put("TMP", temporary.toString()); builder.environment().put("TEMP", temporary.toString());
        Process child = builder.directory(root.toFile()).redirectError(ProcessBuilder.Redirect.INHERIT).start();
        byte[] raw;
        try (var readers = Executors.newVirtualThreadPerTaskExecutor()) {
            var read = readers.submit(() -> child.getInputStream().readNBytes(MAXIMUM_BYTES + 1));
            if (!child.waitFor(60, TimeUnit.SECONDS)) {
                child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly();
                throw new IllegalStateException("original marriage handoff capture timed out");
            }
            raw = read.get(5, TimeUnit.SECONDS);
        } finally { if (child.isAlive()) { child.destroyForcibly(); } }
        if (child.exitValue() != 0 || raw.length == 0 || raw.length > MAXIMUM_BYTES) {
            throw new IllegalStateException("original capture failed: exit=" + child.exitValue() + ", bytes=" + raw.length);
        }
        Files.createDirectories(output.getParent()); Files.write(output, raw, StandardOpenOption.CREATE_NEW);
        System.out.println("Captured original marriage handoff and shared consumers: " + raw.length + " bytes at " + output);
    }

    private static final String SCRIPT = """
            import sys,json,hashlib,subprocess,copy,datetime,tempfile,importlib.util
            from pathlib import Path
            from unittest.mock import patch
            root=Path(sys.argv[1]);temporary=Path(sys.argv[2]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'));sys.path.insert(0,str(root/'ck3_autonomous_player/tests/unit'))
            relatives=['ck3_autonomous_player/src/xar_autoplayer/family_marriage_episode_handoff_v1.py','ck3_autonomous_player/src/xar_autoplayer/family_marriage_formal_consumer.py','ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py','ck3_autonomous_player/src/xar_autoplayer/current_first_heir_betrothal_formal_consumer.py','ck3_autonomous_player/src/xar_autoplayer/activity_feast_stage5_budget_v1.py','ck3_autonomous_player/src/xar_autoplayer/family_alliance_result_query_run.py','ck3_autonomous_player/src/xar_autoplayer/m5_formal_proposal_collector.py','ck3_autonomous_player/src/xar_autoplayer/m5_peacetime_proposal_sources_v1.py','ck3_autonomous_player/src/xar_autoplayer/native_auto_run.py','ck3_autonomous_player/src/xar_autoplayer/player_child_default_formal_consumer.py','ck3_autonomous_player/src/xar_autoplayer/player_child_matrilineal_formal_consumer.py','ck3_autonomous_player/src/xar_autoplayer/bridge/service.py','ck3_autonomous_player/tests/unit/test_family_marriage_formal_consumer.py','ck3_autonomous_player/tests/unit/test_family_marriage_episode_handoff_compound.py']
            def refs():return [{'path':rel,'bytes':(root/rel).stat().st_size,'sha256':hashlib.sha256((root/rel).read_bytes()).hexdigest()} for rel in relatives]
            before=refs()
            def delta(before,after,path=''):
                if type(before) is dict and type(after) is dict:
                    result=[]
                    for key in sorted(before.keys()-after.keys()):result.append({'op':'remove','path':path+'/'+key})
                    for key in after:
                        at=path+'/'+key
                        if key not in before:result.append({'op':'set','path':at,'value':after[key]})
                        else:result.extend(delta(before[key],after[key],at))
                    return result
                return [] if type(before) is type(after) and before==after else [{'op':'set','path':path,'value':after}]
            from xar_autoplayer.family_marriage_episode_handoff_v1 import archive_predecessor_family_marriage_v1 as handoff
            from xar_autoplayer.family_marriage_formal_consumer import _write,read_family_marriage_ledger,plan_family_marriage_private,submit_family_marriage_private,query_family_marriage_result_private
            from xar_autoplayer.m5_peacetime_proposal_sources_v1 import _pending_family_commitments
            from xar_autoplayer.activity_feast_stage5_budget_v1 import observe_feast_start_budget_v1
            from xar_autoplayer.current_first_heir_betrothal_formal_consumer import plan_current_first_heir_betrothal_fulfillment_private
            import test_family_marriage_formal_consumer as fixture
            args={'source_episode_run_id':'robert-test','successor_episode_run_id':'natural-successor-继承人','predecessor_character_id':101,'successor_character_id':202}
            with tempfile.TemporaryDirectory(prefix='marriage-handoff-',dir=temporary) as directory:
                state=Path(directory);driver=fixture.FakeDriver(state);snapshot=fixture.scene()
                with patch('xar_autoplayer.family_marriage_formal_consumer.bridge_process_identity',return_value=(55,'created')):
                    planned=plan_family_marriage_private(driver,{'plan':{'selected_step':'life-advance'}},snapshot)
                    pending=submit_family_marriage_private(driver,plan=planned['plan'],snapshot=snapshot)
                    query_family_marriage_result_private(driver,pending=pending,cold=False)
                resolved=read_family_marriage_ledger(state)['resolved']
                base={'schema':'xar.ck3.first-heir-marriage-formal.v1','pending':pending,'resolved':resolved,'episode_history':[{'source_episode_run_id':'earlier-life','resolved':{'status':'marriage','material_result':True}}],'sdk_extension':{'unknown_state':'UNKNOWN','nullable':None,'empty':[],'exact_decimal':0.125,'status':0,'played_character_id':1.0,'unicode_source':'原角色→后继 🦊'}}
                cases=[]
                def add(name,ledger,present=True):
                    if present:_write(state,copy.deepcopy(ledger))
                    request={'schema':'xar.java-family-marriage-episode-handoff/v1','state_directory_present':present,'handoff':args,'ledger':copy.deepcopy(ledger) if present else None}
                    receipt=handoff(state if present else None,**args)
                    after=read_family_marriage_ledger(state) if present else None
                    cases.append({'name':name,'request':request,'expected':{'ledger':after,'receipt':receipt,'write_required':receipt is not None}})
                add('actual_submission_and_material_resolution',base)
                pending_only=copy.deepcopy(base);pending_only['resolved']=None;pending_only.pop('episode_history');add('pending_only_missing_history',pending_only)
                resolved_only=copy.deepcopy(base);resolved_only['pending']=None;add('resolved_only',resolved_only)
                other=copy.deepcopy(base);other['pending']['episode_run_id']='another-life';add('other_episode_pending_preserved',other)
                other_resolved=copy.deepcopy(base);other_resolved['resolved']['episode_run_id']='another-life';add('other_episode_resolved_preserved',other_resolved)
                unknown=copy.deepcopy(base);unknown['pending']['submission_state']='may_have_submitted';unknown['pending']['status']='UNKNOWN';unknown['resolved']=None;add('unknown_may_have_submitted_never_replayed',unknown)
                missing=copy.deepcopy(base);missing['pending'].pop('episode_run_id');missing['resolved']['episode_run_id']=None;add('missing_and_null_episode_no_archive',missing)
                empty={'schema':base['schema'],'pending':None,'resolved':None};add('empty_ledger_no_write',empty)
                add('no_state_directory_no_read_or_write',None,False)
                add('already_archived_repeat_is_noop',cases[0]['expected']['ledger'])
                # Actual shared-reader imports used by every existing ledger consumer must see the same bytes.
                import xar_autoplayer.activity_feast_stage5_budget_v1 as feast,xar_autoplayer.current_first_heir_betrothal_formal_consumer as betrothal,xar_autoplayer.family_alliance_result_query_run as alliance,xar_autoplayer.m5_formal_proposal_collector as collector,xar_autoplayer.m5_peacetime_proposal_sources_v1 as sources,xar_autoplayer.native_auto_run as auto,xar_autoplayer.player_child_default_formal_consumer as child,xar_autoplayer.player_child_matrilineal_formal_consumer as matrilineal,xar_autoplayer.bridge.service as service
                modules=[feast,betrothal,alliance,collector,sources,auto,child,matrilineal,service]
                for case in cases:
                    if case['expected']['ledger'] is None:continue
                    _write(state,case['expected']['ledger'])
                    for module in modules:
                        if module.read_family_marriage_ledger(state)!=case['expected']['ledger']:raise RuntimeError('consumer reader differs: '+module.__name__)
                _write(state,cases[0]['expected']['ledger'])
                successor={'episode_run_id':args['successor_episode_run_id'],'played_character_id':202}
                commitments=_pending_family_commitments(read_family_marriage_ledger(state)['pending'],successor)
                if any(commitments.values()):raise RuntimeError('archived predecessor still reserves successor commitments')
                current={**snapshot,'episode_run_id':args['successor_episode_run_id'],'played_character':{'character_id':202},'paused':False}
                driver.calls.clear();planned=plan_family_marriage_private(driver,{'plan':{'selected_step':'life-advance'}},current)
                if driver.calls or planned['plan']['selected_step']!='life-advance':raise RuntimeError('archived predecessor caused successor query/send')
                driver.allow_private_current_first_heir_betrothal_fulfillment=True
                fulfillment=plan_current_first_heir_betrothal_fulfillment_private(driver,{'plan':{'selected_step':'life-advance'}},current)
                if driver.calls or fulfillment['plan']['selected_step']!='life-advance':raise RuntimeError('archived predecessor caused fulfillment replay')
                budget_snapshot={'played_character':{'character_id':202},'paused':True,'map_ready':True,'native_revision':24,'date_raw':53180720,'snapshot_id':'successor-frame','revision':24,'active_wars':[],'pending_character_interaction':None}
                budget_inputs={'actor_character_id':202,'snapshot_revision':24,'date_raw':53180720,'post_snapshot_id':'successor-frame','queried_revision':24}
                budget=observe_feast_start_budget_v1(budget_snapshot,budget_inputs,state_dir=state)
                if budget['status']!='observed':raise RuntimeError('archived predecessor blocks budget: '+str(budget))
            after=refs()
            if before!=after:raise RuntimeError('source changed during original capture')
            machine=subprocess.run([sys.executable,str(root/'tools/ck3_live_run_id.py'),'machine'],check=True,capture_output=True,text=True).stdout.strip()
            base_request=cases[0]['request']
            compact=[{'name':case['name'],'request_patch':delta(base_request,case['request']),'expected_sha256':hashlib.sha256(json.dumps(case['expected'],ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')).hexdigest(),'expected_receipt':case['expected']['receipt'],'write_required':case['expected']['write_required']} for case in cases]
            value={'schema':'xar.java-family-marriage-episode-handoff-original-golden/v1','machine_id':machine,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_refs':before,'source_refs_unchanged':before==after,'scope':'Offline actual handoff producer, actual pending/resolved producers with existing test-driver native seams, all shared-reader imports, real M5 commitment/marriage planning/fulfillment planning/feast budget consumers. No native call, writer qualification, M3 admission or live game credit. Original compound driver test requires qualified native-wire fixtures and is not claimed executed.','consumer_modules':[module.__name__ for module in modules],'consumer_probe_results':{'successor_commitments':commitments,'successor_plan':planned,'successor_fulfillment_plan':fulfillment,'successor_budget':budget},'base_request':base_request,'cases':compact}
            print(json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False))
            """;
}
