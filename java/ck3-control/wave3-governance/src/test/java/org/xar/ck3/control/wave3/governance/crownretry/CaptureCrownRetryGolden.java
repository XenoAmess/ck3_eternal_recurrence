package org.xar.ck3.control.wave3.governance.crownretry;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Once-only original cache predicate and actual file-reader/horizon capture. */
public final class CaptureCrownRetryGolden {
    private CaptureCrownRetryGolden() { }
    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 3) { throw new IllegalArgumentException("repository-root existing-python output-json"); }
        Path root = Path.of(arguments[0]).toRealPath(); Path output = Path.of(arguments[2]).toAbsolutePath().normalize();
        if (Files.exists(output)) { throw new IllegalArgumentException("never overwrite a captured original"); }
        Process child = new ProcessBuilder(List.of(arguments[1], "-B", "-c", SCRIPT, root.toString()))
                .directory(root.toFile()).redirectError(ProcessBuilder.Redirect.INHERIT).start();
        byte[] raw;
        try (var reader = Executors.newVirtualThreadPerTaskExecutor()) {
            var read = reader.submit(() -> child.getInputStream().readNBytes(65_537));
            if (!child.waitFor(60, TimeUnit.SECONDS)) {
                child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly();
                throw new IllegalStateException("original Crown retry capture timed out");
            }
            raw = read.get(5, TimeUnit.SECONDS);
        } finally { if (child.isAlive()) { child.destroyForcibly(); } }
        if (child.exitValue() != 0 || raw.length == 0 || raw.length > 65_536) {
            throw new IllegalStateException("original retry capture failed: exit=" + child.exitValue() + ", bytes=" + raw.length);
        }
        Files.createDirectories(output.getParent()); Files.write(output, raw, StandardOpenOption.CREATE_NEW);
        System.out.println("Captured original Crown retry predicate/horizon: " + raw.length + " bytes at " + output);
    }

    private static final String SCRIPT = """
            import sys,json,hashlib,copy,tempfile,subprocess,datetime
            from pathlib import Path
            from types import SimpleNamespace
            root=Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            path='ck3_autonomous_player/src/xar_autoplayer/crown_authority_formal_consumer_v1.py'
            source=(root/path).read_bytes();pin=hashlib.sha256(source).hexdigest()
            from xar_autoplayer.crown_authority_formal_consumer_v1 import _matching_future_retry,crown_authority_retry_horizon_days_v1,read_crown_authority_state_v1
            snapshot={'episode_run_id':'fixture-crown-retry-episode','played_character':{'character_id':29829,'alive':True},'date_raw':53279400,'native_revision':90,'revision':91}
            state={'pending':None,'resolved':None,'retry':{'source_context':{'bridge_pid':881,'episode_run_id':snapshot['episode_run_id']},'actor_character_id':29829,'law_key':'crown_authority_2','observed_date_raw':snapshot['date_raw'],'retry_date_raw':snapshot['date_raw']+25,'fixture_source_note':'source-shaped prior admitted retry, not a new native observation'}}
            cases=[];negatives=[]
            with tempfile.TemporaryDirectory(prefix='crown-retry-capture-') as directory:
                work=Path(directory);state_path=work/'crown-authority-formal-v1.json'
                def one(name,mutation=None,horizon=40,law=None,query_enabled=True,paused_enabled=True,state_available=True):
                    current=copy.deepcopy(snapshot);saved=copy.deepcopy(state);pid=881
                    if mutation:mutation(current,saved)
                    driver=SimpleNamespace(_session_bridge_pid=pid,state_dir=work if state_available else 'fixture-unavailable-state-dir',allow_private_realm_law_action=query_enabled,allow_private_realm_law_paused_query=paused_enabled)
                    state_path.write_text(json.dumps(saved),encoding='utf-8')
                    loaded=read_crown_authority_state_v1(work)
                    if loaded!=saved:raise RuntimeError('actual state reader changed the fixture')
                    matched=_matching_future_retry(driver,current,loaded,law_key=law)
                    actual_horizon=crown_authority_retry_horizon_days_v1(driver,current,horizon)
                    match={'schema':'xar.java-crown-future-retry-match/v1','bridge_pid':pid,'snapshot':current,'state':loaded,'law_key':law}
                    horizon_request={'schema':'xar.java-crown-retry-horizon/v1','bridge_pid':pid,'snapshot':current,'state':loaded if state_available else None,'horizon_days':horizon,'query_enabled':query_enabled,'paused_query_enabled':paused_enabled}
                    cases.append({'name':name,'match_request':match,'expected_match':matched,'horizon_request':horizon_request,'expected_horizon':actual_horizon,'actual_state_reader_executed':True})
                one('future_25_hours_ceil_two_days')
                one('future_one_hour',lambda s,r:r['retry'].update(retry_date_raw=s['date_raw']+1))
                one('future_exact_24_hours',lambda s,r:r['retry'].update(retry_date_raw=s['date_raw']+24))
                one('requested_one_day_is_never_extended',horizon=1)
                one('due_now_not_future',lambda s,r:r['retry'].update(retry_date_raw=s['date_raw']))
                one('past_hint_not_reused',lambda s,r:r['retry'].update(retry_date_raw=s['date_raw']-1))
                one('pending_original_action_blocks_hint',lambda s,r:r.update(pending={'stage':'receipt_pending','action_id':'fixture-existing-original'}))
                one('nonnull_false_pending_also_blocks',lambda s,r:r.update(pending=False))
                one('pending_missing_matches_legacy_get',lambda s,r:r.pop('pending'))
                one('bridge_generation_context_differs',lambda s,r:r['retry']['source_context'].update(bridge_pid=882))
                one('episode_context_differs',lambda s,r:r['retry']['source_context'].update(episode_run_id='other-episode'))
                one('extra_source_context_is_not_discarded',lambda s,r:r['retry']['source_context'].update(unmigrated_field='foreign'))
                one('current_actor_differs',lambda s,r:s['played_character'].update(character_id=29830))
                one('missing_played_character',lambda s,r:s.pop('played_character'))
                one('date_unavailable',lambda s,r:s.update(date_raw=None))
                one('retry_date_unavailable',lambda s,r:r['retry'].update(retry_date_raw=None))
                one('target_filter_matches',law='crown_authority_2')
                one('target_filter_differs',law='crown_authority_1')
                one('private_query_off',query_enabled=False)
                one('paused_query_off',paused_enabled=False)
                one('durable_state_unavailable',state_available=False)
                one('huge_exact_integer_delta',lambda s,r:r['retry'].update(retry_date_raw=s['date_raw']+(1<<128)),horizon=(1<<129))
                one('empty_retry',lambda s,r:r.update(retry=None))
                one('retry_extension_preserved',lambda s,r:r['retry'].update(extension={'retained':[1,2,3],'note':'future cache value only'}))
                for name,mutation in [('bool_retry_actor',lambda s,r:r['retry'].update(actor_character_id=True)),('float_retry_date',lambda s,r:r['retry'].update(retry_date_raw=float(s['date_raw']+25))),('bool_snapshot_date',lambda s,r:s.update(date_raw=True)),('float_source_pid',lambda s,r:r['retry']['source_context'].update(bridge_pid=881.0))]:
                    current=copy.deepcopy(snapshot);saved=copy.deepcopy(state);mutation(current,saved);driver=SimpleNamespace(_session_bridge_pid=881)
                    request={'schema':'xar.java-crown-future-retry-match/v1','bridge_pid':881,'snapshot':current,'state':saved,'law_key':None}
                    negatives.append({'name':name,'raw_request_json':json.dumps(request,separators=(',',':'),allow_nan=False),'legacy_match':_matching_future_retry(driver,current,saved),'expected_java_wire_rejection':True})
            after=(root/path).read_bytes()
            if source!=after:raise RuntimeError('original Crown retry source changed during capture')
            machine=subprocess.run([sys.executable,str(root/'tools/ck3_live_run_id.py'),'machine'],check=True,capture_output=True,text=True).stdout.strip()
            value={'schema':'xar.java-crown-retry-original-producer-golden/v1','machine_id':machine,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Actual unchanged matching helper plus actual original durable state reader and horizon consumer. Generated fixture files live only in task TEMP, not canonical campaign state; no Game, RPC, action, ledger or native qualification.','source_refs':[{'path':path,'bytes':len(source),'sha256':pin}],'source_refs_unchanged':True,'original_state_reader_cases':len(cases),'cases':cases,'wire_rejections':negatives}
            print(json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False))
            """;
}
