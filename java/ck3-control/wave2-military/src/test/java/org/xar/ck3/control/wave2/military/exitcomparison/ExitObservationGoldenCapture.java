package org.xar.ck3.control.wave2.military.exitcomparison;

import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

/** Explicit offline capture; normal JUnit never starts Python or accesses a running game. */
public final class ExitObservationGoldenCapture {
    private ExitObservationGoldenCapture() { }
    public static void main(String[] args) throws Exception {
        if (args.length != 3) { throw new IllegalArgumentException("repository root, existing Python and new capture output required"); }
        Path root = Path.of(args[0]).toAbsolutePath().normalize();
        Path python = Path.of(args[1]).toAbsolutePath().normalize();
        Process identity = new ProcessBuilder(python.toString(), root.resolve("tools/ck3_live_run_id.py").toString(), "machine")
                .directory(root.toFile()).redirectErrorStream(true).start();
        if (!identity.waitFor(15, TimeUnit.SECONDS)) {
            identity.destroyForcibly();
            throw new IllegalStateException("machine probe timed out");
        }
        String machineId = new String(identity.getInputStream().readNBytes(1024), StandardCharsets.UTF_8).trim();
        if (identity.exitValue() != 0 || !machineId.matches("[A-Za-z0-9-]{1,128}")) {
            throw new IllegalStateException("actual machine identity required");
        }
        String script = """
                import sys,json,hashlib,datetime,copy,unittest,io
                from pathlib import Path
                from unittest.mock import patch
                root=Path(sys.argv[1])
                sys.path.insert(0,str(root/'ck3_autonomous_player/tests/unit'))
                import test_formal_defender_exit_observation as t
                observe=t.observe_primary_defender_de_jure_exit
                stream=io.StringIO()
                original=unittest.TextTestRunner(stream=stream).run(unittest.defaultTestLoader.loadTestsFromModule(t))
                if not original.wasSuccessful():
                    raise RuntimeError(stream.getvalue())
                base=t._h2743_snapshot()
                current=t._h2743_snapshot_with_current_options()
                cases=[]
                def add(name,snapshot):
                    cases.append({'name':name,'snapshot':snapshot,'expected':observe(snapshot)})
                def changed(change):
                    candidate=copy.deepcopy(current)
                    change(candidate)
                    return candidate
                add('null-snapshot',None)
                add('unpaused',dict(base,paused=False))
                add('active-event',dict(base,active_event={}))
                add('pending-interaction',dict(base,pending_character_interaction={}))
                add('query-required',base)
                add('current-native-options',current)
                old=json.loads(t.EVIDENCE.read_text(encoding='utf-8'))
                stale=dict(base,war_termination_options=[dict(old['war_termination_options'],query_sequence=old['query_sequence'],queried_snapshot_id=old['queried_snapshot_id'],queried_revision=old['queried_revision'],queried_native_revision=old['queried_native_revision'],queried_connection_generation=old['queried_connection_generation'],episode_run_id=old['queried_episode_run_id'])])
                add('historical-options-rejected',stale)
                add('duplicate-query',changed(lambda s:s['war_termination_options'].append(copy.deepcopy(s['war_termination_options'][0]))))
                add('unknown-native-query-field',changed(lambda s:s['war_termination_options'][0].update(unqualified_extra=1)))
                add('native-query-war-identity-mismatch',changed(lambda s:s['active_wars'][0].update(player_relative_war_score=-13)))
                add('another-casus-belli',changed(lambda s:s['war_termination_options'][0]['active_casus_belli_identity'].update(canonical_key='other_cb')))
                add('recipient-response-unavailable',changed(lambda s:s['war_termination_options'][0]['options']['surrender'].update(recipient_response={'status':'unavailable','decision_status_raw':None,'would_accept_now':None})))
                inferred=copy.deepcopy(current)
                del inferred['war_termination_options'][0]['source']
                add('source-default-normalized-native',inferred)
                add('forward-compatible-sdk-container',dict(current,future_sdk_container={'nested':['opaque',1.0,True,None]},diagnostics=dict(current['diagnostics'],future_diagnostic='not projected')))
                add('legacy-frame-zero-when-query-required',dict(base,revision=0,native_revision=0,diagnostics={'connection_generation':0}))
                add('multiple-losing-primary-defenders',dict(base,active_wars=base['active_wars']+copy.deepcopy(base['active_wars'])))
                handoffs=[]
                for selected in ['advance-route-contact-horizon-v1-candidate','surrender-war-16777231','surrender-war-16777232','offer-white-peace-16777231',None,'']:
                    plan={'policy':'one-life-turn-v1','selected_step':selected}
                    with patch.object(t.strategy,'plan_raiktor_formal_exit',return_value=None),patch.object(t.strategy,'_choose_one_life_turn_core',return_value=plan),patch.object(t.strategy,'_primary_defender_siege_forecast_ingress',side_effect=lambda plan,**kw:plan),patch.object(t.strategy,'_general_battle_forecast_ingress',side_effect=lambda plan,**kw:plan),patch.object(t.strategy,'_annotate_active_combat_resume_input',side_effect=lambda plan,snapshot:plan):
                        actual=t.strategy.choose_one_life_turn([],snapshot=copy.deepcopy(current),action_steps=[] if selected is None else [selected])
                    handoffs.append({'selected_step':selected,'expected':actual['formal_defender_exit_observation']['continuation_handoff'],'original_selected_step_preserved':actual.get('selected_step')==selected})
                paths=[root/'ck3_autonomous_player/src/xar_autoplayer/formal_defender_exit_observation.py',root/'ck3_autonomous_player/src/xar_autoplayer/formal_defender_exit_comparison.py',root/'ck3_autonomous_player/src/xar_autoplayer/strategy.py',root/'ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py',Path(t.__file__),t.EVIDENCE]
                result={'schema':'xar.ck3.java.exit-observation.golden.v1','machine_id':sys.argv[2],'captured_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'capture':'actual unmodified observer and strategy handoff; historical/synthetic fixture, not current-game qualification','original_unit_tests':original.testsRun,'original_failures':len(original.failures),'original_errors':len(original.errors),'sources':[{'path':p.relative_to(root).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in paths],'cases':cases,'handoffs':handoffs}
                raw=(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode('utf-8')
                if len(raw)>65536:
                    raise RuntimeError('golden exceeds explicit 64KiB fixture budget')
                out=Path(sys.argv[3])
                out.parent.mkdir(parents=True,exist_ok=True)
                with out.open('xb') as stream:
                    stream.write(raw)
                print(json.dumps({'path':str(out),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'cases':len(cases),'handoffs':len(handoffs),'original_tests':original.testsRun}))
                """;
        Process process = new ProcessBuilder(python.toString(), "-c", script, root.toString(), machineId,
                Path.of(args[2]).toAbsolutePath().normalize().toString())
                .directory(root.toFile()).redirectErrorStream(true).start();
        if (!process.waitFor(90, TimeUnit.SECONDS)) {
            process.destroyForcibly();
            process.waitFor(5, TimeUnit.SECONDS);
            throw new IllegalStateException("actual producer capture timed out");
        }
        byte[] output = process.getInputStream().readNBytes(8193);
        if (output.length > 8192) { throw new IllegalStateException("capture output exceeds limit"); }
        System.out.print(new String(output, StandardCharsets.UTF_8));
        if (process.exitValue() != 0) { throw new IllegalStateException("actual producer exited " + process.exitValue()); }
    }
}
