package org.xar.ck3.control.wave3.governance.marriagepending;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Offline actual original planner-branch capture, exclusively scheduled by storage/M7. */
public final class CaptureMarriagePendingGolden {
    private CaptureMarriagePendingGolden() { }
    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 4) { throw new IllegalArgumentException("repository-root existing-python output-json approved-temporary-root"); }
        Path root = Path.of(arguments[0]).toRealPath(); Path output = Path.of(arguments[2]).toAbsolutePath().normalize(); Path temporary = Path.of(arguments[3]).toRealPath();
        if (Files.exists(output)) { throw new IllegalArgumentException("capture never replaces original evidence"); }
        ProcessBuilder builder = new ProcessBuilder(List.of(arguments[1], "-B", "-c", SCRIPT, root.toString(), temporary.toString()));
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); builder.environment().put("TMP", temporary.toString()); builder.environment().put("TEMP", temporary.toString());
        builder.environment().put("PYTHONUTF8", "1"); builder.environment().put("PYTHONIOENCODING", "utf-8");
        Process child = builder.directory(root.toFile()).redirectError(ProcessBuilder.Redirect.INHERIT).start(); byte[] raw;
        try (var readers = Executors.newVirtualThreadPerTaskExecutor()) {
            var read = readers.submit(() -> child.getInputStream().readNBytes(65_537));
            if (!child.waitFor(60, TimeUnit.SECONDS)) {
                child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly(); throw new IllegalStateException("pending planner capture timeout");
            }
            raw = read.get(5, TimeUnit.SECONDS);
        } finally { if (child.isAlive()) { child.destroyForcibly(); } }
        if (child.exitValue() != 0 || raw.length == 0 || raw.length > 65_536) { throw new IllegalStateException("pending capture failed: exit=" + child.exitValue() + ", bytes=" + raw.length); }
        Files.createDirectories(output.getParent()); Files.write(output, raw, StandardOpenOption.CREATE_NEW);
        System.out.println("Captured original pending planner: " + raw.length + " bytes at " + output);
    }
    private static final String SCRIPT = """
            import sys,json,hashlib,subprocess,copy,datetime,tempfile
            from pathlib import Path
            from unittest.mock import patch
            root=Path(sys.argv[1]);temporary=Path(sys.argv[2]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'));sys.path.insert(0,str(root/'ck3_autonomous_player/tests/unit'))
            relatives=['ck3_autonomous_player/src/xar_autoplayer/family_marriage_formal_consumer.py','ck3_autonomous_player/src/xar_autoplayer/family_marriage_episode_handoff_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/domain_construction_private_transport_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/observed_heir_marriage_private_action_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/service.py','ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py','ck3_autonomous_player/src/xar_autoplayer/m5_formal_proposal_collector.py','ck3_autonomous_player/src/xar_autoplayer/m5_peacetime_proposal_sources_v1.py','ck3_autonomous_player/src/xar_autoplayer/native_auto_run.py','ck3_autonomous_player/tests/unit/test_family_marriage_formal_consumer.py']
            def refs():return [{'path':rel,'bytes':(root/rel).stat().st_size,'sha256':hashlib.sha256((root/rel).read_bytes()).hexdigest()} for rel in relatives]
            def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')).hexdigest()
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
            before=refs()
            from xar_autoplayer.family_marriage_formal_consumer import _write,read_family_marriage_ledger,plan_family_marriage_private,submit_family_marriage_private
            from xar_autoplayer.family_marriage_episode_handoff_v1 import archive_predecessor_family_marriage_v1
            from xar_autoplayer.bridge.observed_heir_marriage_private_action_v1 import RESULT_STEP
            from xar_autoplayer.bridge.service import GameplayBridgeService
            from xar_autoplayer.native_auto_run import _turn_record
            import test_family_marriage_formal_consumer as fixture
            with tempfile.TemporaryDirectory(prefix='marriage-pending-',dir=temporary) as directory:
                state=Path(directory);driver=fixture.FakeDriver(state);snapshot=fixture.scene()
                with patch('xar_autoplayer.family_marriage_formal_consumer.bridge_process_identity',return_value=(55,'created')):
                    planned=plan_family_marriage_private(driver,{'plan':{'selected_step':'life-advance'}},snapshot)
                    pending=submit_family_marriage_private(driver,plan=planned['plan'],snapshot=snapshot)
                ledger=read_family_marriage_ledger(state)
                base={'schema':'xar.java-family-marriage-pending-read-request/v1','planned':{'snapshot_id':'pending-fixture','plan':{'selected_step':'life-advance','original_extra':'原角色与 UNKNOWN 🦊'}},'snapshot':snapshot,'ledger':ledger,'bridge_identity':{'pid':55,'creation_date':'created'}}
                cases=[]
                def add(name,mutator=None,request=None):
                    value=copy.deepcopy(base if request is None else request)
                    if mutator:mutator(value)
                    _write(state,value['ledger']);driver.calls.clear();identity=value['bridge_identity']
                    with patch('xar_autoplayer.family_marriage_formal_consumer.bridge_process_identity',return_value=None if identity is None else (identity['pid'],identity['creation_date'])):
                        expected=plan_family_marriage_private(driver,value['planned'],value['snapshot'])
                    if driver.calls:raise RuntimeError('pending branch queried or submitted: '+str(driver.calls))
                    if read_family_marriage_ledger(state)!=value['ledger']:raise RuntimeError('pending scheduling wrote ledger')
                    handled=value['ledger']['pending'] is not None
                    cases.append({'name':name,'request_patch':delta(base,value),'expected_sha256':digest({'handled':handled,'planned':expected}),'expected_selected_step':expected['plan'].get('selected_step'),'expected_handled':handled})
                add('actual_warm_pending_awaits_new_frame')
                add('warm_later_native_revision_reads_result',lambda q:q['snapshot'].update(native_revision=8))
                add('cold_pid_lower_revision_reads_once',lambda q:(q['bridge_identity'].update(pid=99),q['snapshot'].update(native_revision=1)))
                add('same_pid_new_creation_reads_once',lambda q:q['bridge_identity'].update(creation_date='new-created'))
                add('foreign_episode_blocks_without_identity_lookup',lambda q:(q['snapshot'].update(episode_run_id='next-life'),q.update(bridge_identity=None)))
                add('missing_pending_episode_blocks',lambda q:q['ledger']['pending'].pop('episode_run_id'))
                add('null_pending_episode_blocks',lambda q:q['ledger']['pending'].update(episode_run_id=None))
                def checked(q):
                    q['bridge_identity'].update(pid=99,creation_date='restored');q['snapshot'].update(native_revision=1);q['ledger']['pending'].update(last_checked_native_revision=1,last_checked_bridge_pid=99,last_checked_bridge_creation_date='restored')
                add('cold_same_checked_frame_waits',checked)
                add('cold_checked_next_frame_reads',lambda q:(checked(q),q['snapshot'].update(native_revision=2)))
                add('checked_source_birth_drift_still_reads',lambda q:(checked(q),q['ledger']['pending'].update(last_checked_bridge_creation_date='old-birth')))
                add('missing_current_revision_preserves_pending',lambda q:q['snapshot'].pop('native_revision'))
                add('null_current_revision_preserves_pending',lambda q:q['snapshot'].update(native_revision=None))
                add('zero_current_revision_preserves_pending',lambda q:q['snapshot'].update(native_revision=0))
                add('last_checked_revision_overrides_pre_revision',lambda q:(q['ledger']['pending'].update(last_checked_native_revision=10),q['snapshot'].update(native_revision=9)))
                add('legacy_missing_pre_revision_defaults_zero',lambda q:(q['ledger']['pending'].pop('pre_native_revision'),q['snapshot'].update(native_revision=1)))
                add('full_uint64_revision_remains_exact',lambda q:(q['ledger']['pending'].update(pre_native_revision=18446744073709551614),q['snapshot'].update(native_revision=18446744073709551615)))
                add('unknown_may_have_submitted_never_replays',lambda q:q['ledger']['pending'].update(status='UNKNOWN',submission_state='may_have_submitted'))
                add('cold_absent_relation_keeps_active_outbound',lambda q:(checked(q),q['ledger']['pending'].update(cold_absent_relation_unresolved=True,last_outbound_pending_state='active',last_outbound_pending_id=-2013265918)))
                _write(state,ledger)
                receipt=archive_predecessor_family_marriage_v1(state,source_episode_run_id=snapshot['episode_run_id'],successor_episode_run_id='natural-next-life-继承人',predecessor_character_id=101,successor_character_id=202)
                next_request=copy.deepcopy(base);next_request['ledger']=read_family_marriage_ledger(state);next_request['bridge_identity']=None;next_request['snapshot'].update(episode_run_id='natural-next-life-继承人',played_character={'character_id':202},paused=False)
                add('actual_handoff_leaves_no_pending_branch',request=next_request)
                # Consume the real pending plan through the existing service and compact turn recorder.
                _write(state,ledger);driver.calls.clear();warm_snapshot={**snapshot,'native_revision':8}
                with patch('xar_autoplayer.family_marriage_formal_consumer.bridge_process_identity',return_value=(55,'created')):
                    warm_planned=plan_family_marriage_private(driver,copy.deepcopy(base['planned']),warm_snapshot)
                    service=GameplayBridgeService(driver)
                    service.plan_turn=lambda:{**warm_planned,'snapshot_id':'native:8','revision':8}
                    service.snapshot=lambda:copy.deepcopy(warm_snapshot)
                    outcome=service.auto_turn()
                turn=_turn_record(1,'2026-10-22T00:00:00Z',turn_class='query',outcome=outcome,before=warm_snapshot,after=warm_snapshot,evidence=[])
                consumed=read_family_marriage_ledger(state)
                if outcome['status']!='executed' or outcome['result']['status']!='marriage' or outcome['result']['material_result'] is not True:raise RuntimeError('existing service did not consume the original result query')
                if driver.calls!=['result'] or consumed['pending'] is not None or consumed['resolved']['source_pending']!=pending:raise RuntimeError('service result crossed its single pending source or resent')
                if turn['plan']['family_marriage_pending']!=pending or turn['plan']['family_marriage_cold_recovery'] is not False:raise RuntimeError('actual turn recorder lost pending source or cold branch')
                consumer_evidence={'service_status':outcome['status'],'service_selected_step':outcome['selected_step'],'result_status':outcome['result']['status'],'result_material_result':outcome['result']['material_result'],'native_test_seam_calls':driver.calls,'original_pending_sha256':digest(pending),'turn_record_pending_sha256':digest(turn['plan']['family_marriage_pending']),'resolved_source_pending_sha256':digest(consumed['resolved']['source_pending'])}
            after=refs()
            if before!=after:raise RuntimeError('original pending source changed during capture')
            machine=subprocess.run([sys.executable,str(root/'tools/ck3_live_run_id.py'),'machine'],check=True,capture_output=True,text=True).stdout.strip()
            print(json.dumps({'schema':'xar.java-family-marriage-pending-read-original-golden/v1','machine_id':machine,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_refs':before,'source_refs_unchanged':before==after,'scope':'Actual original pending producer, planner branch, archive handoff, GameplayBridgeService.auto_turn result consumer, native_auto_run._turn_record and resolved.source_pending fixture persistence. Native result and current bridge identity use the existing explicit offline native test seams. No native calls or schedule writes; the separate actual service result consumer writes only fixture state. No replay, writer qualification, Java service registration or live business credit.','base_request':base,'cases':cases,'result_step':RESULT_STEP,'actual_handoff_receipt':receipt,'consumer_evidence':consumer_evidence},ensure_ascii=False,separators=(',',':'),allow_nan=False))
            """;
}
