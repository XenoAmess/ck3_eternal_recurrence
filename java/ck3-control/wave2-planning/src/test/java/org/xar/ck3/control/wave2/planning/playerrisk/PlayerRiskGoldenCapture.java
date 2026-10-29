package org.xar.ck3.control.wave2.planning.playerrisk;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

/** Explicit bounded existing-Python producer capture; only the shared execution owner runs this. */
public final class PlayerRiskGoldenCapture {
    private PlayerRiskGoldenCapture() { }
    private static final String SCRIPT = """
            import copy, datetime, hashlib, json, pathlib, runpy, sys
            from unittest.mock import patch
            from xar_autoplayer.ordinary_player_risk_context_v1 import build_ordinary_player_risk_context_v1 as build
            from xar_autoplayer.bridge.driver import CallbackGameplayDriver
            from xar_autoplayer.bridge.service import GameplayBridgeService
            from test_turn_bundle_v1 import _snapshot, _root
            from test_campaign_root_context_v1_bridge import STEP, _answer_with, _native_driver, _native_result
            from test_journaller_stress_relief_v1 import SyntheticDriver
            from xar_autoplayer import journaller_stress_relief_v1 as journaller
            repo, scratch, machine = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
            baseline = {'snapshot':_snapshot(),'campaign_root_result':_root()}
            baseline['snapshot']['diagnostics'] = {'connection_generation':2}
            baseline['campaign_root_result'].update(queried_snapshot_id=baseline['snapshot']['snapshot_id'],queried_revision=baseline['snapshot']['revision'],queried_native_revision=baseline['snapshot']['native_revision'])
            definitions = [
              ('current-partial',[]),
              ('healthy', [(['campaign_root_result','campaign_root_context','player_health','raw'],300000)]),
              ('dying-split', [(['campaign_root_result','campaign_root_context','player_health','raw'],150000)]),
              ('missing-stress', [(['snapshot','played_character','stress_points'],None,'remove')]),
              ('null-stress', [(['snapshot','played_character','stress_points'],None)]),
              ('boolean-stress', [(['snapshot','played_character','stress_points'],True)]),
              ('stress-below-threshold', [(['snapshot','played_character','stress_points'],99)]),
              ('stress-at-threshold', [(['snapshot','played_character','stress_points'],100)]),
              ('unavailable-root', [(['campaign_root_result','status'],'unavailable'),(['campaign_root_result','campaign_root_context','status'],'unavailable'),(['campaign_root_result','campaign_root_context','unavailable_reason'],'state_changed')]),
              ('missing-root', [(['campaign_root_result'],None)]),
              ('history-binding', [(['campaign_root_result','binding'],None,'remove')]),
              ('missing-observed-binding', [(['campaign_root_result','binding'],None,'remove'),(['campaign_root_result','queried_native_revision'],None,'remove')]),
              ('stale-native-revision', [(['campaign_root_result','queried_native_revision'],99)]),
              ('stale-actor', [(['snapshot','played_character','character_id'],99)]),
              ('response-generation-observed', [(['campaign_root_result','queried_connection_generation'],2)]),
              ('response-generation-drift', [(['campaign_root_result','queried_connection_generation'],3)]),
              ('no-current-generation', [(['snapshot','diagnostics'],{},'set')]),
              ('invalid-health-scale', [(['campaign_root_result','campaign_root_context','player_health','scale'],1)]),
              ('bool-query-sequence', [(['campaign_root_result','query_sequence'],True)]),
              ('duplicate-war', [(['snapshot','active_wars',1,'war_id'],20)]),
              ('partial-council', [(['campaign_root_result','campaign_root_context','council'],{'status':'unavailable','unavailable_reason':'outside_standard_landed_non_nomadic_core_scope'})]),
              ('landless', [(['campaign_root_result','campaign_root_context','primary_title'],None),(['campaign_root_result','campaign_root_context','primary_title_succession_character_ids'],[]),(['campaign_root_result','campaign_root_context','held_title_partition'],[])]),
              ('no-heir', [(['campaign_root_result','campaign_root_context','primary_title_succession_character_ids'],[]),(['campaign_root_result','campaign_root_context','held_title_partition',0,'first_heir_character_id'],None)]),
              ('family-county-vote', [(['campaign_root_result','campaign_root_context','held_title_partition',1],{'title':{'title_id':91,'tier_raw':2,'tier_key':'county'},'first_heir_character_id':77,'capital_province_id':None,'primary':False,'capital_province_kind':'landless_noble_family_no_province','title_key':'c_fixture_family'})]),
            ]
            cases=[]
            for name, edits in definitions:
                inputs=copy.deepcopy(baseline)
                for edit in edits:
                    path,value,*mode=edit
                    parent=inputs
                    for key in path[:-1]: parent=parent[key]
                    if mode and mode[0]=='remove': del parent[path[-1]]
                    else: parent[path[-1]]=value
                original=copy.deepcopy(inputs)
                expected=build(inputs['snapshot'],inputs['campaign_root_result'])
                if inputs != original: raise RuntimeError('original producer mutated input')
                cases.append({'id':name,'edits':[{'path':e[0],'value':e[1],'remove':len(e)>2 and e[2]=='remove'} for e in edits],'expected':expected})
            driver, endpoint = _native_driver()
            try:
                _answer_with(endpoint,_native_result)
                before=driver.take_snapshot()
                driver.execute_step(STEP,expected_revision=before['revision'])
                current=driver.take_snapshot()
                history=current['native_command_history'][-1]['result']
                input_native={'snapshot':current,'campaign_root_result':history}
                expected_native=build(current,history)
                sent=len(endpoint.frames)
                if 'queried_connection_generation' in history: raise RuntimeError('fixture invented response witness')
                if len(endpoint.frames)!=sent: raise RuntimeError('pure projection sent a command')
                skeys=('snapshot_id','revision','native_revision','date_raw','paused','backend_id','played_character','played_character_gold','active_event','pending_character_interaction','active_wars','diagnostics')
                rkeys=('binding','status','query_sequence','queried_snapshot_id','queried_revision','queried_native_revision','queried_connection_generation','campaign_root_context')
                projected={'snapshot':{key:copy.deepcopy(current[key]) for key in skeys if key in current},'campaign_root_result':{key:copy.deepcopy(history[key]) for key in rkeys if key in history}}
                projected['snapshot']['diagnostics']={'connection_generation':current['diagnostics']['connection_generation']}
                if build(**{'snapshot':projected['snapshot'],'campaign_root_result':projected['campaign_root_result']}) != expected_native: raise RuntimeError('declared native fixture projection changed risk')
                native_case={'id':'actual-driver-normalized-history','input':projected,'expected':expected_native,'transport':'existing-in-memory-FakeEndpoint-no-native-pipe'}
            finally: driver.close()
            plan={'policy':'synthetic-chooser-boundary','phase':'risk-consumer','selected_step':None,'reason':'capture existing plan attachment only'}
            service_frame=copy.deepcopy(baseline['snapshot'])
            service_frame.update(map_ready=True,player_armies=[],native_command_history=[{'ok':True,'step':STEP,'command':STEP,'result':copy.deepcopy(baseline['campaign_root_result'])}])
            callback=CallbackGameplayDriver(backend_id='native-headless',snapshot=lambda:copy.deepcopy(service_frame),execute=lambda *a,**k:(_ for _ in ()).throw(RuntimeError('capture forbids execution')),action_steps=())
            with patch('xar_autoplayer.bridge.service.choose_one_life_turn',return_value=copy.deepcopy(plan)):
                planned=GameplayBridgeService(callback).plan_turn()['plan']
            service_expected={key:copy.deepcopy(planned[key]) for key in (*plan,'player_risk_context')}
            if service_expected['player_risk_context'] != cases[0]['expected']: raise RuntimeError('registered Service did not consume same actual root')
            journaller_cases=[]
            for name,mode in [('urgent','urgent'),('low','low'),('unknown','missing'),('stale','stale')]:
                d=SyntheticDriver(scratch/('journaller-'+name))
                d.caps=set()
                if mode=='low': d.frame['played_character']['stress_points']=99
                if mode=='missing': d.frame['played_character'].pop('stress_points')
                if mode=='stale': d.root['queried_native_revision']+=1
                outcome=journaller.start_journaller_stress_relief_v1(d,expected_revision=d.frame['revision'],campaign_root_result=d.root,game_source_root=scratch/'unused-source',before_action=lambda row:None)
                if d.calls: raise RuntimeError('stress consumer capture sent an action')
                journaller_cases.append({'id':name,'input':{'snapshot':d.frame,'campaign_root_result':d.root},'expected_status':outcome['status'],'action_calls':d.calls})
            binder_specs=[('tools/g2_saved_campaign/battle_reader_unavailable_classifier_v1.py','classify_battle_reader_gameplay_start_binding_v1'),('tools/g2_saved_campaign/war_results_scope_transition_classifier_v1.py','classify_war_results_start_binding_v1')]
            binders=[runpy.run_path(str(repo/path))[name] for path,name in binder_specs]
            binder_cases=[]
            binder_defs=[('current-partial',[]),('current-generation-unavailable',[(['snapshot','diagnostics'],{})]),('unavailable-risk',[(['campaign_root_result'],None)]),('zero-public-revision',[(['snapshot','revision'],0),(['campaign_root_result','binding','revision'],0),(['campaign_root_result','queried_revision'],0)])]
            for name,edits in binder_defs:
                original=copy.deepcopy(baseline)
                for path,value in edits:
                    parent=original
                    for key in path[:-1]: parent=parent[key]
                    parent[path[-1]]=value
                risk=build(original['snapshot'],original['campaign_root_result'])
                goal={'campaign_id':'synthetic-risk-episode','current_character_id':12345}
                initial={'actor_character_id':12345,'episode_run_id':'synthetic-risk-episode'}
                body={'plan':{'player_risk_context':risk,'campaign_goal_plan_used':goal}}
                outcomes=[]
                for binder in binders:
                    try: outcomes.append({'accepted':True,'binding':binder(body,initial_frame=initial,game_pid=6767),'reason':None})
                    except ValueError as error: outcomes.append({'accepted':False,'binding':None,'reason':str(error)})
                if outcomes[0]!=outcomes[1]: raise RuntimeError('two actual risk binders disagree')
                binder_cases.append({'id':name,'edits':[{'path':p,'value':v,'remove':False} for p,v in edits],'goal':goal,'initial_frame':initial,'expected':outcomes[0],'actual_consumers':2})
            paths=['ck3_autonomous_player/src/xar_autoplayer/ordinary_player_risk_context_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/turn_bundle_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/player_vitals_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/campaign_root_context_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/service.py','ck3_autonomous_player/src/xar_autoplayer/bridge/current_first_heir_relationship_private_transport.py','ck3_autonomous_player/src/xar_autoplayer/journaller_stress_relief_v1.py','ck3_autonomous_player/tests/unit/test_turn_bundle_v1.py','ck3_autonomous_player/tests/unit/test_ordinary_player_risk_context_v1.py','ck3_autonomous_player/tests/unit/test_campaign_root_context_v1_bridge.py','ck3_autonomous_player/tests/unit/test_journaller_stress_relief_v1.py',*[p for p,n in binder_specs]]
            result={'schema':'xar.java.player-risk-producer-golden.v1','machine_id':machine,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),'sources':[{'path':p,'sha256':hashlib.sha256((repo/p).read_bytes()).hexdigest()} for p in paths],'baseline':baseline,'cases':cases,'driver_case':native_case,'service_consumer':{'plan':plan,'history':service_frame['native_command_history'],'expected':service_expected,'chooser_seam':'synthetic; risk producer and registered Service are original'},'journaller_consumers':journaller_cases,'output_binder_consumers':binder_cases,'game_rpc_count':0,'canonical_ledger_write_count':0,'production_cutover':False}
            output=json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':'))
            if len(output.encode())>94208: raise RuntimeError('golden exceeds bounded 92KiB budget')
            print(output)
            """;

    public static void main(String[] args) throws Exception {
        if (args.length != 5) { throw new IllegalArgumentException("python-exe repo-root new-output scratch-root machine-id required"); }
        Path python = Path.of(args[0]).toAbsolutePath().normalize(), repo = Path.of(args[1]).toAbsolutePath().normalize();
        Path output = Path.of(args[2]).toAbsolutePath().normalize(), scratch = Path.of(args[3]).toAbsolutePath().normalize();
        Path allowed = Path.of("D:/codex-ck3-demos/2026-10-22-java-phase1/scratch").toAbsolutePath().normalize();
        if (!Files.isRegularFile(python) || Files.exists(output) || !output.startsWith(allowed) || !scratch.startsWith(allowed) || args[4].isBlank()) {
            throw new IllegalArgumentException("actual Python, new bounded D scratch output and actual machine identity required");
        }
        Files.createDirectories(output.getParent());
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-B", "-X", "utf8", "-", repo.toString(), scratch.toString(), args[4]);
        builder.directory(repo.toFile()); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTHONPATH", repo.resolve("ck3_autonomous_player/src") + ";" + repo.resolve("ck3_autonomous_player/tests/unit"));
        builder.redirectOutput(output.toFile()); builder.redirectError(ProcessBuilder.Redirect.INHERIT);
        Process process = builder.start();
        try {
        try (var stdin = process.getOutputStream()) { stdin.write(SCRIPT.getBytes(java.nio.charset.StandardCharsets.UTF_8)); }
        if (!process.waitFor(30, TimeUnit.SECONDS)) { process.destroyForcibly(); process.waitFor(); throw new IllegalStateException("producer capture timed out; output retained"); }
        if (process.exitValue() != 0 || Files.size(output) == 0 || Files.size(output) > 94_208) { throw new IllegalStateException("producer capture failed; output retained"); }
        System.out.println("Player risk original producer and consumers captured " + Files.size(output) + " bytes");
        } finally {
            if (process.isAlive()) {
                process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly();
                process.waitFor(5, TimeUnit.SECONDS);
            }
        }
    }
}
