package org.xar.ck3.control.application.planning.military;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** OriginalCapture entry for the existing bounded CompiledOriginalCapture Job; never a ReferenceActual writer. */
public final class LateWarCoreGoldenCapture {
    private LateWarCoreGoldenCapture() {}
    public static void main(String[] arguments) throws IOException,InterruptedException {
        if(arguments.length!=3)throw new IllegalArgumentException("repo python fresh-output required");
        Path repo=Path.of(arguments[0]).toAbsolutePath(),output=Path.of(arguments[2]).toAbsolutePath();
        if(Files.exists(output))throw new IllegalArgumentException("fresh late original capture required");
        Process child=new ProcessBuilder(List.of(arguments[1],"-B","-c",SCRIPT,repo.toString(),output.toString()))
                .directory(repo.toFile()).inheritIO().start();
        if(!child.waitFor(90,TimeUnit.SECONDS)) {child.destroyForcibly();throw new IllegalStateException("late original capture timed out; parent Job owns cleanup");}
        if(child.exitValue()!=0)throw new IllegalStateException("actual original late producer exited "+child.exitValue());
        if(!Files.isRegularFile(output)||Files.size(output)==0||Files.size(output)>1_048_576)throw new IllegalStateException("late original output requires 1 MiB finite bound");
    }
    private static final String SCRIPT="""
            import sys,json,copy,hashlib,datetime,inspect,importlib.util
            from pathlib import Path
            repo=Path(sys.argv[1]); output=Path(sys.argv[2])
            sys.path.insert(0,str(repo/'ck3_autonomous_player/src'))
            sys.path.insert(0,str(repo/'tools'))
            from ck3_live_run_id import current_machine_id
            from xar_autoplayer import strategy
            tests=repo/'ck3_autonomous_player/tests/unit'
            def module(name):
                spec=importlib.util.spec_from_file_location(name,tests/(name+'.py'))
                value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
            arrived=module('test_arrived_refuge_lifecycle')
            defender=module('test_defender_refuge_candidates')
            p42=module('test_stationary_defensive_risk_v1')
            land=module('test_land_retained_unsafe_edge_watch_4892')
            excluded=module('test_stationary_excluded_siege_watch_6343')
            source,start=inspect.getsourcelines(strategy._choose_one_life_turn_core)
            late_line=next(start+i for i,line in enumerate(source) if line.strip()=='active_route_unsafe = bool(')
            cases=[]
            def publication(locals):
                gates=locals['battle_speed_gates'];ready=locals['battle_speed_readiness']
                return dict(tactical_war_id=locals['tactical_war_id'],subject_army_id=locals['army_id'],
                    ranked_exact_objectives=locals['exact_objective_province_ids'],siege_objectives=locals['siege_objective_province_ids'],
                    blocked_provinces=sorted(locals['blocked_province_ids']),stationary_threats=locals['stationary_threats'],
                    unsafe_army_ids=sorted(a['army_id'] for a in locals['unsafe_armies']),active_assaults=locals['active_assaults'],
                    passive_route_audit=locals['passive_route_audit'],siege_relief=locals['siege_relief'],exact_siege_rejection=locals['exact_siege_rejection'],
                    termination_rows=list(locals['termination_by_war_id'].values()),war_summaries=locals['war_summary'],tactical_state=locals['tactical'],
                    route_preview_supported=bool(locals['move_route_preview_supported']),contact_horizon_supported=bool(locals['route_contact_horizon_supported']),
                    exact_occupation_fully_observable=bool(locals['exact_occupation_fully_observable']),all_siege_objectives_completed=bool(locals['all_siege_objectives_completed']),
                    sentinel={'enabled':bool(gates['stationary_objective_hold_sentinel_live_ready'] or gates['stationary_objective_hold_sentinel_canary_ready']),
                        'speed':locals['stationary_objective_hold_sentinel_speed'],'high_speed_ab':isinstance(ready,dict) and ready.get('noncombat_sentinel_high_speed_ab') is True})
            def core_case(name,sem,rows,steps,caps,origin):
                captured=[]
                def trace(frame,event,arg):
                    if event=='line' and frame.f_code is strategy._choose_one_life_turn_core.__code__ and frame.f_lineno==late_line and not captured:
                        captured.append(json.loads(json.dumps(publication(frame.f_locals))))
                    return trace
                prior=sys.gettrace()
                try:
                    sys.settrace(trace)
                    expected=strategy._choose_one_life_turn_core(rows,snapshot=sem,action_steps=steps,bridge_capabilities=caps)
                finally:sys.settrace(prior)
                if len(captured)!=1:raise ValueError('real ordinary core did not reach late boundary: '+name+' '+str(expected.get('phase')))
                cases.append({'name':name,'scope':'actual_original_core_upstream_to_java_late_leaves','origin':origin,
                    'snapshot':sem,'history':rows,'steps':sorted(steps),'capabilities':sorted(caps),'publication':captured[0],'expected':expected})
            sem,rows,auto,root,cache=arrived.actual();steps,caps,_=arrived.steps(sem,cache,rows)
            core_case('actual_arrived_refuge',sem,rows,steps,caps,'historical_actual_consumed_projection')
            core_case('arrived_missing_current_root',sem,[r for r in rows if r.get('index',0)<547],steps,caps,'explicit_synthetic_drop_of_current_root')
            synthetic=[*rows,arrived.synthetic_current_query(sem,rows)]
            synthetic_steps,synthetic_caps,_=arrived.steps(sem,cache,synthetic)
            core_case('arrived_fresh_contact_free',sem,synthetic,synthetic_steps,synthetic_caps,'existing_test_explicit_synthetic_new_native_timeline')
            sem,rows,auto,cache=defender.actual();steps,caps,_=defender.step_set(sem,cache,rows)
            core_case('actual_defender_refuge',sem,rows,steps,caps,'historical_actual_consumed_projection')
            f=p42._fixture();core_case('actual_p42_timeline_unavailable',f['snapshot'],f['command_rows'],f['capabilities']['action_steps'],f['capabilities']['bridge_capabilities'],'actual_auto_dtos_with_reconstructed_row_wrappers')
            f=land.facts();core_case('actual4892_core_after_overview',f['snapshot'],f['command_rows'],land.steps(f),f['capabilities'],'actual_route_halt_dtos_core_scope_only_prior_public_overview_not_requalified')
            sem=excluded.reconstructed_adapter();rejection=excluded.rejection(sem)
            expected=excluded.watch(sem)
            war=sem['active_wars'][0];army=sem['player_armies'][0]
            p={'tactical_war_id':war['war_id'],'subject_army_id':army['army_id'],'ranked_exact_objectives':[],'siege_objectives':[],
                'blocked_provinces':[],'stationary_threats':[],'unsafe_army_ids':[],'active_assaults':[],'passive_route_audit':None,'siege_relief':{},
                'exact_siege_rejection':rejection,'termination_rows':[],'war_summaries':[],'tactical_state':{},'route_preview_supported':True,
                'contact_horizon_supported':True,'exact_occupation_fully_observable':False,'all_siege_objectives_completed':False,
                'sentinel':{'enabled':False,'speed':3,'high_speed_ab':False}}
            cases.append({'name':'closed6343_excluded_helper','scope':'actual_original_siege_producer_and_watch_helper_only',
                'origin':'existing_explicit_synthetic_ordinary_adapter_from_closed6343_facts','snapshot':sem,'history':[],
                'steps':sorted(excluded.STEPS),'capabilities':sorted(excluded.CAPS),'publication':p,'rejections':excluded.REJECTIONS,'expected':expected})
            sources=['tools/ck3_live_run_id.py','ck3_autonomous_player/src/xar_autoplayer/strategy.py',
                'ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py',
                'ck3_autonomous_player/src/xar_autoplayer/defender_refuge_candidates_v1.py',
                'ck3_autonomous_player/src/xar_autoplayer/bridge/campaign_root_context_contract.py']
            for name in ['test_arrived_refuge_lifecycle.py','test_defender_refuge_candidates.py','test_stationary_defensive_risk_v1.py',
                'test_land_retained_unsafe_edge_watch_4892.py','test_stationary_excluded_siege_watch_6343.py',
                'fixtures/arrived_refuge_actual_projection.json','fixtures/defender_refuge_actual_projection.json',
                'fixtures/p42_stationary_unavailable_actual.json.gz','fixtures/war4892_retained_land_edge_actual_v1.json','fixtures/war6343_excluded_siege_closed_v1.json']:
                sources.append('ck3_autonomous_player/tests/unit/'+name)
            data={'schema':'xar.late-war-core-original-producer-golden.v1','machine_id':current_machine_id(),
                'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'new_live_evidence':False,
                'capture_method':'Unmodified original Python ordinary core with a read-only trace of its actual late-boundary locals; Java consumes the exact typed publication. Existing closed6343 adapter is helper-only, explicitly synthetic. No mocks replace Java leaf logic.',
                'source_bindings':[{'path':p,'bytes':(repo/p).stat().st_size,'sha256':hashlib.sha256((repo/p).read_bytes()).hexdigest()} for p in sources],
                'cases':cases}
            raw=(json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode()
            if len(raw)>1048576:raise ValueError('one MiB finite late capture exceeded: '+str(len(raw)))
            output.parent.mkdir(parents=True,exist_ok=True)
            with output.open('xb') as stream:stream.write(raw)
            print(json.dumps({'machine_id':data['machine_id'],'cases':len(cases),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}))
            """;
}
