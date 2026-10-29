package org.xar.ck3.control.wave2.military.prewaradmission;

import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Explicit original-producer capture, scheduled by the shared bounded Java capture owner only. */
public final class CapturePrewarAdmissionGolden {
    private CapturePrewarAdmissionGolden() { }

    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 3) { throw new IllegalArgumentException("repository-root existing-python fresh-output"); }
        Path root = Path.of(arguments[0]).toRealPath();
        Path output = Path.of(arguments[2]).toAbsolutePath().normalize();
        if (Files.exists(output)) { throw new IllegalArgumentException("capture must not overwrite evidence"); }
        Process child = new ProcessBuilder(List.of(arguments[1], "-B", "-c", SCRIPT, root.toString()))
                .directory(root.toFile()).redirectError(ProcessBuilder.Redirect.INHERIT).start();
        byte[] raw;
        try (var readers = Executors.newVirtualThreadPerTaskExecutor()) {
            var reader = readers.submit(() -> child.getInputStream().readNBytes(98_305));
            if (!child.waitFor(Duration.ofSeconds(100).toMillis(), TimeUnit.MILLISECONDS)) {
                child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly();
                throw new IllegalStateException("original producer capture timed out");
            }
            raw = reader.get(5, TimeUnit.SECONDS);
        } finally { if (child.isAlive()) { child.destroyForcibly(); } }
        if (child.exitValue() != 0 || raw.length == 0 || raw.length > 98_304) {
            throw new IllegalStateException("capture failed: exit=" + child.exitValue() + ", bytes=" + raw.length);
        }
        Files.createDirectories(output.getParent());
        Files.write(output, raw, java.nio.file.StandardOpenOption.CREATE_NEW);
        System.out.println("Captured " + raw.length + " bytes at " + output);
    }

    private static final String SCRIPT = """
            import sys,json,hashlib,subprocess,copy,datetime,contextlib
            from pathlib import Path
            root=Path(sys.argv[1]);sys.path[:0]=[str(root/'ck3_autonomous_player/src'),str(root/'ck3_autonomous_player/tests/unit')]
            import pytest
            from test_ordinary_prewar_force_admission_v2 import _evidence,_plan
            from xar_autoplayer.ordinary_prewar_force_admission_v2 import assess_ordinary_prewar_force_admission_v2 as assess
            class Results:
                tests=0;failed=0;skipped=0
                def pytest_runtest_logreport(self,report):
                    if report.skipped:self.skipped+=1
                def pytest_sessionfinish(self,session,exitstatus):self.tests=session.testscollected;self.failed=session.testsfailed
            stats=Results()
            with contextlib.redirect_stdout(sys.stderr):
                code=pytest.main(['-q','-p','no:cacheprovider',str(root/'ck3_autonomous_player/tests/unit/test_ordinary_prewar_force_admission_v2.py')],plugins=[stats])
            if code!=0 or stats.tests<30 or stats.failed or stats.skipped:raise RuntimeError('original full pytest failed or skipped')
            Q='prewar_force_coalition_coverage_v2_query';D='prewar_force_coalition_coverage_v2'
            sk=('paused','map_ready','snapshot_id','revision','native_revision','date_raw','episode_run_id','capture_epoch')
            dk=('declaration_id','target_character_id','casus_belli_index','casus_belli_key','configuration_index','claimant_character_id','target_title_ids')
            qk=('queried_snapshot_id','queried_revision','queried_native_revision','queried_date_raw','queried_actor_character_id','queried_connection_generation','queried_episode_run_id','accepted','status','execution_receipt','native_request_id',D)
            def dump(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
            def pick(v,keys):return {k:copy.deepcopy(v[k]) for k in keys if k in v}
            def decl(v):return pick(v,dk)
            def projection(snapshot,declaration):
                if snapshot is None:s=None
                else:
                    s=pick(snapshot,sk)
                    if 'played_character' in snapshot:s['played_character']=None if snapshot['played_character'] is None else pick(snapshot['played_character'],('alive','character_id'))
                    if 'diagnostics' in snapshot:
                        diag=snapshot['diagnostics'];s['diagnostics']=None if diag is None else pick(diag,('connection_generation',))
                        if isinstance(diag,dict) and 'hello' in diag:s['diagnostics']['hello']=None if diag['hello'] is None else pick(diag['hello'],('bridge_version','expected_ck3_version','expected_ck3_sha256'))
                    if 'declarable_wars' in snapshot:s['declarable_wars']=None if snapshot['declarable_wars'] is None else [decl(v) for v in snapshot['declarable_wars']]
                    if Q in snapshot:s[Q]=None if snapshot[Q] is None else pick(snapshot[Q],qk)
                return {'schema':'xar.ck3.ordinary-prewar-admission.input/v1','snapshot':s,'declaration':decl(declaration)}
            def diff(before,after,path=()):
                if dump(before)==dump(after):return []
                if isinstance(before,dict) and isinstance(after,dict):
                    result=[]
                    for key in sorted(before.keys()-after.keys()):result.append({'op':'remove','path':list(path+(key,))})
                    for key in sorted(after):
                        if key not in before:result.append({'op':'set','path':list(path+(key,)),'value_json':dump(after[key])})
                        else:result.extend(diff(before[key],after[key],path+(key,)))
                    return result
                return [{'op':'set','path':list(path),'value_json':dump(after)}]
            base_tuple=_evidence();base=projection(base_tuple[0],base_tuple[1]);cases=[]
            def add(name,change=None,lower=1500,upper=1000,path='general',planner=False,wire_rejection=False):
                s,d,v,e=_evidence(lower=lower,upper=upper,path=path);c={'snapshot':s,'declaration':d,'value':v,'envelope':e}
                if change:change(c)
                before=copy.deepcopy((c['snapshot'],c['declaration']))
                expected=assess(c['snapshot'],c['declaration'])
                if before!=(c['snapshot'],c['declaration']):raise RuntimeError('producer mutated input')
                case={'name':name,'patches':diff(base,projection(c['snapshot'],c['declaration'])),'expected':expected,'wire_rejection':wire_rejection}
                if planner:
                    p=_plan(c['snapshot'],c['declaration']);case['actual_original_planner']={k:copy.deepcopy(p.get(k)) for k in ('phase','selected_step','decision')}
                cases.append(case)
            add('complete-qualified-general',planner=True)
            for lower,upper in [(1499,1000),(0,0),(1,0)]:add('force-boundary-'+str(lower)+'-'+str(upper),lower=lower,upper=upper)
            for path in ('de_jure','player_claim'):add('complete-qualified-'+path,path=path,planner=True)
            add('null-snapshot',lambda c:c.update(snapshot=None))
            add('empty-snapshot',lambda c:c.update(snapshot={}))
            add('unpaused',lambda c:c['snapshot'].update(paused=False))
            add('map-not-ready',lambda c:c['snapshot'].update(map_ready=False))
            add('dead-controller',lambda c:c['snapshot']['played_character'].update(alive=False))
            add('zero-actor',lambda c:c['snapshot']['played_character'].update(character_id=0))
            add('wrong-bridge-version',lambda c:c['snapshot']['diagnostics']['hello'].update(bridge_version='0.1.0'))
            add('missing-hello',lambda c:c['snapshot']['diagnostics'].pop('hello'))
            add('empty-snapshot-id',lambda c:c['snapshot'].update(snapshot_id=''))
            add('negative-revision',lambda c:c['snapshot'].update(revision=-1))
            add('date-below-int32',lambda c:c['snapshot'].update(date_raw=-(1<<31)-1))
            add('date-above-int32',lambda c:c['snapshot'].update(date_raw=1<<31))
            add('empty-episode',lambda c:c['snapshot'].update(episode_run_id=''))
            add('missing-declaration-id',lambda c:c['declaration'].pop('declaration_id'))
            add('empty-declaration-id',lambda c:c['declaration'].update(declaration_id=''))
            add('query-absent',lambda c:c['snapshot'].pop(Q))
            add('query-null',lambda c:c['snapshot'].update({Q:None}))
            for field in ('queried_snapshot_id','queried_revision','queried_native_revision','queried_date_raw','queried_actor_character_id','queried_connection_generation','queried_episode_run_id'):
                def stale(c,field=field):
                    old=c['envelope'][field];c['envelope'][field]='stale' if isinstance(old,str) else old+1
                add('lease-stale-'+field,stale)
            add('query-not-accepted',lambda c:c['envelope'].update(accepted=False))
            add('receipt-absent',lambda c:c['envelope'].pop('execution_receipt'))
            add('receipt-extra-request-id',lambda c:c['envelope']['execution_receipt'].update(request_id='cannot-override'))
            add('receipt-empty',lambda c:c['envelope'].update(execution_receipt={}))
            add('request-id-empty',lambda c:c['envelope'].update(native_request_id=''))
            add('domain-null',lambda c:c['envelope'].update({D:None}))
            add('present-partial-no-requery',lambda c:c['envelope'].update(status='partial'))
            add('present-failed-no-requery',lambda c:c['envelope'].update(status='failed'))
            add('outer-receipt-wrong-epoch',lambda c:c['envelope']['execution_receipt'].update(capture_epoch=18))
            add('selected-title-mismatch',lambda c:c['value']['selected_declaration'].update(target_title_ids=[92]))
            add('duplicate-owner',lambda c:c['value']['owner_forces'].append(copy.deepcopy(c['value']['owner_forces'][1])))
            add('duplicate-participant',lambda c:c['value']['potential_enemy_participants']['participants'].append(copy.deepcopy(c['value']['potential_enemy_participants']['participants'][0])))
            add('missing-enemy-owner',lambda c:c['value']['owner_forces'].pop())
            add('ally-domain-incomplete',lambda c:c['value']['potential_enemy_participants'].update(current_allies_complete=False))
            add('mobilization-absent',lambda c:c['value'].pop('native_mobilization_qualification'))
            add('boolean-floor',lambda c:c['value'].update(actor_lower_soldiers=True))
            add('floating-floor',lambda c:c['value'].update(actor_lower_soldiers=1500.0))
            add('final-can-send-false',lambda c:c['value']['final_cb_roles'].update(final_can_send=False),planner=True)
            add('final-can-send-null',lambda c:c['value']['final_cb_roles'].update(final_can_send=None))
            add('nullable-episode',lambda c:(c['snapshot'].update(episode_run_id=None),c['envelope'].update(queried_episode_run_id=None)))
            add('missing-snapshot-episode-known-null',lambda c:(c['snapshot'].pop('episode_run_id'),c['envelope'].update(queried_episode_run_id=None)))
            add('missing-outer-episode',lambda c:(c['snapshot'].update(episode_run_id=None),c['envelope'].pop('queried_episode_run_id')))
            add('bool-revision-wire-rejected',lambda c:c['snapshot'].update(revision=True),wire_rejection=True)
            add('float-revision-wire-rejected',lambda c:c['snapshot'].update(revision=6.0),wire_rejection=True)
            add('float-date-wire-rejected',lambda c:c['snapshot'].update(date_raw=53171400.0),wire_rejection=True)
            add('float-actor-wire-rejected',lambda c:c['snapshot']['played_character'].update(character_id=29829.0),wire_rejection=True)
            add('raised-force-with-no-raise',lambda c:c['value']['native_mobilization_qualification'].update(native_raise_legal=False,raised_commandable_lower_soldiers=1500,raised_lower_ready=True))
            def unproven(c):
                c['value']['native_mobilization_qualification'].update(raised_commandable_lower_soldiers=1500,raised_lower_ready=True,executable_lower_soldiers=3000,physical_inventory_lower_soldiers=3000)
                c['value']['actor_lower_soldiers']=3000;c['value']['owner_forces'][0].update(actor_lower_soldiers=3000,inventory_upper_soldiers=3000)
            add('unproven-component-sum',unproven)
            refs=[]
            for rel in ('ck3_autonomous_player/src/xar_autoplayer/ordinary_prewar_force_admission_v2.py','ck3_autonomous_player/src/xar_autoplayer/bridge/prewar_force_coalition_v2_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/prewar_force_coalition_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py','ck3_autonomous_player/src/xar_autoplayer/strategy.py','ck3_autonomous_player/tests/unit/test_ordinary_prewar_force_admission_v2.py','ck3_autonomous_player/tests/unit/test_prewar_surrogate_authority_regression.py'):
                raw=(root/rel).read_bytes();refs.append({'path':rel,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
            machine=subprocess.run([sys.executable,str(root/'tools/ck3_live_run_id.py'),'machine'],check=True,capture_output=True,text=True).stdout.strip()
            output={'schema':'xar.ck3.prewar-admission.original-producer-golden/v1','machine_id':machine,'captured_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Actual original pure producer and full original pytest planner consumers; synthetic unit observations, no live native qualification. Deltas retain original JSON tokens in value_json strings.','source_refs':refs,'original_pytest':{'exit_code':int(code),'tests':stats.tests,'failures':stats.failed,'skipped':stats.skipped},'base_request':base,'cases':cases}
            print(dump(output))
            """;
}
