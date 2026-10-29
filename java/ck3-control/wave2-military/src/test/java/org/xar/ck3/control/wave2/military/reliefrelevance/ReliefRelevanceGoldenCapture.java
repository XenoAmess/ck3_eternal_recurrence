package org.xar.ck3.control.wave2.military.reliefrelevance;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Offline exact original-function capture; only the shared Win32 Job owner launches this class. */
public final class ReliefRelevanceGoldenCapture {
    private ReliefRelevanceGoldenCapture() { }
    public static void main(String[] arguments) throws Exception {
        if (arguments.length == 10 && arguments[3].equals("--compiled-consumers")) {
            org.xar.ck3.control.wave2.military.refuge.CompiledConsumerSupport.run(arguments, ReliefRelevanceConsumerTransfer.class, ReliefRelevanceGoldenCapture.class, ReliefRelevanceConsumerTransfer.INPUT_SCHEMA, ReliefRelevanceConsumerTransfer.OUTPUT_SCHEMA, ReliefRelevanceConsumerTransfer::evaluate, compiledScript());
            return;
        }
        if (arguments.length != 3) { throw new IllegalArgumentException("repo python new-output required"); }
        Path output = Path.of(arguments[2]).toAbsolutePath();
        if (Files.exists(output)) { throw new IllegalArgumentException("new capture output required"); }
        Process child = new ProcessBuilder(List.of(arguments[1], "-c", SCRIPT, arguments[0], output.toString()))
                .directory(Path.of(arguments[0]).toFile()).inheritIO().start();
        if (!child.waitFor(90, TimeUnit.SECONDS)) {
            child.destroyForcibly(); throw new IllegalStateException("capture timeout; shared Job owns descendants");
        }
        if (child.exitValue() != 0) { throw new IllegalStateException("original consumer producer exited " + child.exitValue()); }
        if (!Files.isRegularFile(output) || Files.size(output) == 0 || Files.size(output) > 71_680) {
            throw new IllegalStateException("finite capture output required");
        }
    }

    private static final String SCRIPT = """
            import sys,json,gzip,copy,hashlib,datetime,ast
            from pathlib import Path
            repo=Path(sys.argv[1]);output=Path(sys.argv[2]);sys.path.insert(0,str(repo/'ck3_autonomous_player/src'))
            from xar_autoplayer.nonleading_player_realm_siege_v1 import nonleading_player_realm_siege_v1
            from xar_autoplayer.bridge.war_contract import war_objective_province_ids
            strategy=repo/'ck3_autonomous_player/src/xar_autoplayer/strategy.py';text=strategy.read_text(encoding='utf-8')
            if hashlib.sha256(strategy.read_bytes()).hexdigest()!='52b4381758ee712dc8555ac3a31186e13adbe10c3c18dc93b23bca5147934111':raise ValueError('original consumer oracle requires retained strategy preimage; delegated Java cannot become its own expected-value producer')
            tree=ast.parse(text)
            names=['_native_int','_defender_siege_is_relief_relevant'];nodes=[next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name==name) for name in names]
            namespace={'nonleading_player_realm_siege_v1':nonleading_player_realm_siege_v1,'war_objective_province_ids':war_objective_province_ids}
            exec(compile(ast.Module(body=nodes,type_ignores=[]),str(strategy),'exec'),namespace)
            relevant=namespace['_defender_siege_is_relief_relevant']
            extraction=[{'name':node.name,'first_line':node.lineno,'sha256':hashlib.sha256(ast.get_source_segment(text,node).encode()).hexdigest()} for node in nodes]
            actual=json.loads(gzip.decompress((repo/'ck3_autonomous_player/tests/fixtures/portable_actual_695.json.gz').read_bytes()))['snapshot']
            def take(value,keys):return {key:copy.deepcopy(value[key]) for key in keys if key in value}
            def enemy_projection(value):return take(value,['source','army_id','owner_character_id','controllable','army_state','army_state_code','in_combat','retreating','current_province_id','siege_province_in_player_subrealm','move_target_province_id','route_province_ids','route_read_status','siege_province_holder_character_id'])
            def war_projection(value):
                result=take(value,['source','war_id','player_side','player_is_primary_war_leader','player_relative_war_score','war_objective_province_ids'])
                if 'enemy_armies' in value:result['enemy_armies']=[enemy_projection(row) for row in value['enemy_armies']]
                return result
            snapshot=take(actual,['source','native_revision','snapshot_id','revision','date_raw','episode_run_id','paused','map_ready','active_event','pending_character_interaction'])
            snapshot['played_character']=take(actual['played_character'],['source','character_id','alive'])
            snapshot['diagnostics']=take(actual['diagnostics'],['connected','bridge_pid','connection_generation'])
            snapshot['active_wars']=[war_projection(row) for row in actual['active_wars']]
            frame={'schema':'xar.realm-siege-request.v1','snapshot':snapshot,'detached_wars':[],'detached_enemies':[],'candidate_war_ref':{'collection':'active_wars','index':0},'candidate_enemy_ref':{'collection':'candidate_war_enemy_armies','index':0}}
            original={'schema':'xar.siege-relief-relevance-input.v1','frame':frame}
            synthetic=copy.deepcopy(original);war=synthetic['frame']['snapshot']['active_wars'][0];war['player_is_primary_war_leader']=False
            for enemy in war['enemy_armies']:enemy.update(siege_province_in_player_subrealm=True,move_target_province_id=None,route_province_ids=[],route_read_status='complete_empty')
            bases=[{'name':'actual','origin':'historical_actual_projection','request':original},{'name':'nonleading','origin':'explicit_synthetic_nonleading_stationary_realm_siege','request':synthetic}]
            byname={row['name']:row['request'] for row in bases}
            def patch(path,value,operation='set'):return {'operation':operation,'path':path,'value':value}
            def apply(request,operations):
                for operation in operations:
                    parent=request
                    for key in operation['path'][:-1]:parent=parent[int(key)] if isinstance(parent,list) else parent[key]
                    key=operation['path'][-1];key=int(key) if isinstance(parent,list) else key
                    if operation['operation']=='remove':parent.pop(key)
                    else:parent[key]=copy.deepcopy(operation['value'])
            def select(request):
                frame=request['frame'];ref=frame['candidate_war_ref'];wars=frame['snapshot']['active_wars'] if ref['collection']=='active_wars' else frame['detached_wars'];war=wars[ref['index']]
                ref=frame['candidate_enemy_ref'];enemies=war['enemy_armies'] if ref['collection']=='candidate_war_enemy_armies' else frame['detached_enemies'];return frame['snapshot'],war,enemies[ref['index']]
            cases=[]
            def add(name,base='actual',operations=None,detach=None):
                operations=copy.deepcopy(operations or []);request=copy.deepcopy(byname[base]);apply(request,operations)
                snapshot,war,enemy=select(request)
                if detach=='war':operations.extend([patch(['frame','detached_wars'],[copy.deepcopy(war)]),patch(['frame','candidate_war_ref','collection'],'detached_wars')])
                if detach=='enemy':operations.extend([patch(['frame','detached_enemies'],[copy.deepcopy(enemy)]),patch(['frame','candidate_enemy_ref','collection'],'detached_enemies')])
                request=copy.deepcopy(byname[base]);apply(request,operations);snapshot,war,enemy=select(request)
                expected={'schema':'xar.siege-relief-relevance-observation.v1','candidate_siege_relief_relevant':relevant(snapshot,war,enemy),'objective_province_ids_in_stored_traversal':war_objective_province_ids(snapshot['active_wars'])}
                cases.append({'name':name,'base':base,'origin':'unchanged_historical_projection' if not operations and base=='actual' else 'explicit_synthetic_variant','patches':operations,'expected':expected})
            wp=['frame','snapshot','active_wars','0'];ep=wp+['enemy_armies','0'];sp=['frame','snapshot'];province=snapshot['active_wars'][0]['enemy_armies'][0]['current_province_id'];actor=snapshot['played_character']['character_id']
            add('actual_primary_factual_scope')
            add('nonleading_current_realm_siege',base='nonleading')
            add('primary_exact_objective',operations=[patch(wp+['war_objective_province_ids'],[province])])
            add('primary_observed_subrealm',operations=[patch(wp+['war_objective_province_ids'],[]),patch(ep+['siege_province_in_player_subrealm'],True)])
            add('objective_precedes_explicit_outside',operations=[patch(wp+['war_objective_province_ids'],[province]),patch(ep+['siege_province_in_player_subrealm'],False)])
            add('outside_blocks_holder_fallback',operations=[patch(wp+['war_objective_province_ids'],[]),patch(ep+['siege_province_in_player_subrealm'],False),patch(ep+['siege_province_holder_character_id'],actor)])
            holder=[patch(wp+['war_objective_province_ids'],[]),patch(ep+['siege_province_in_player_subrealm'],None),patch(ep+['siege_province_holder_character_id'],actor)]
            add('unknown_subrealm_own_holder',operations=holder)
            add('unknown_subrealm_foreign_holder',operations=holder[:-1]+[patch(ep+['siege_province_holder_character_id'],actor+1)])
            add('unknown_subrealm_missing_holder',operations=holder[:-1]+[patch(ep+['siege_province_holder_character_id'],None,'remove')])
            add('zero_province',operations=[patch(ep+['current_province_id'],0)])
            add('negative_province',operations=[patch(ep+['current_province_id'],-1)])
            add('unknown_leader_flag_retains_original_factual_branch',operations=[patch(wp+['player_is_primary_war_leader'],None),patch(wp+['war_objective_province_ids'],[province])])
            add('nonleading_outside_even_if_objective',base='nonleading',operations=[patch(ep+['siege_province_in_player_subrealm'],False),patch(wp+['war_objective_province_ids'],[province])])
            add('nonleading_stale_snapshot',base='nonleading',operations=[patch(sp+['snapshot_id'],'native:old')])
            add('nonleading_unknown_source',base='nonleading',operations=[patch(sp+['source'],'unknown')])
            add('nonleading_disconnected',base='nonleading',operations=[patch(sp+['diagnostics','connected'],False)])
            add('nonleading_committed_departure',base='nonleading',operations=[patch(ep+['move_target_province_id'],province+1),patch(ep+['route_province_ids'],[province+1])])
            add('nonleading_own_army',base='nonleading',operations=[patch(ep+['owner_character_id'],actor)])
            add('nonleading_detached_equal_war',base='nonleading',detach='war')
            add('nonleading_detached_equal_enemy',base='nonleading',detach='enemy')
            add('primary_detached_objective_factual_tie',operations=[patch(wp+['war_objective_province_ids'],[province])],detach='war')
            add('primary_detached_holder_factual_tie',operations=holder,detach='enemy')
            extra=copy.deepcopy(snapshot['active_wars'][0]);extra['war_objective_province_ids']=[9,3,9,-1]
            add('stable_objective_multiwar_traversal',operations=[patch(wp+['war_objective_province_ids'],[3,2,3]),patch(sp+['active_wars'],[{**copy.deepcopy(snapshot['active_wars'][0]),'war_objective_province_ids':[3,2,3]},extra])])
            add('objective_exact_integer_domain',operations=[patch(wp+['war_objective_province_ids'],[province,0,-1,2**80,province])])
            add('null_objectives',operations=[patch(wp+['war_objective_province_ids'],None)])
            add('missing_objectives',operations=[patch(wp+['war_objective_province_ids'],None,'remove')])
            add('no_played_holder_fallback',operations=holder+[patch(sp+['played_character'],None,'remove')])
            add('nonleading_score_minus100',base='nonleading',operations=[patch(wp+['player_relative_war_score'],-100)])
            add('nonleading_score_plus100',base='nonleading',operations=[patch(wp+['player_relative_war_score'],100)])
            add('nonleading_modal',base='nonleading',operations=[patch(sp+['active_event'],{'instance_id':44})])
            add('nonleading_enemy_in_combat',base='nonleading',operations=[patch(ep+['in_combat'],True)])
            add('nonleading_unknown_route',base='nonleading',operations=[patch(ep+['route_read_status'],'unknown')])
            sources=['ck3_autonomous_player/src/xar_autoplayer/strategy.py','ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py','ck3_autonomous_player/src/xar_autoplayer/nonleading_player_realm_siege_v1.py','ck3_autonomous_player/tests/unit/test_nonleading_siege_priority_v1.py','ck3_autonomous_player/tests/fixtures/portable_actual_695.json.gz']
            bindings=[{'path':path,'bytes':(repo/path).stat().st_size,'sha256':hashlib.sha256((repo/path).read_bytes()).hexdigest()} for path in sources]
            data={'schema':'xar.siege-relief-relevance-original-producer-golden.v1','machine_id':'xenoamess-full-tower-eb9d2c1186','observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_live_qualification':False,'source_bindings':bindings,'original_ast_extracts':extraction,'capture_method':'Exact unchanged strategy function AST bodies plus actual imported war_objective_province_ids and realm-siege dependency. Complete pure dependency closure only; full strategy/registered service not executed. Retained historical portable695 consumed projection with explicitly synthetic variants and independent detached objects. No Game/RPC/ledger.','bases':bases,'cases':cases}
            raw=(json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode()
            if len(raw)>71680:raise ValueError('finite 70KiB compact golden budget exceeded: '+str(len(raw)))
            output.parent.mkdir(parents=True,exist_ok=True)
            with output.open('xb') as handle:handle.write(raw)
            print(json.dumps({'machine_id':data['machine_id'],'observed_at_utc':data['observed_at_utc'],'bases':len(bases),'cases':len(cases),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}))
            """;

    private static String compiledScript() { return SCRIPT.substring(0, SCRIPT.indexOf("actual=json.loads")) + SCRIPT.substring(SCRIPT.indexOf("def take"), SCRIPT.indexOf("snapshot=take")) + COMPILED_CONSUMERS; }
    private static final String COMPILED_CONSUMERS = """
            
            import contextlib,io,inspect,importlib.util,traceback
            sys.path.insert(0,str(repo))
            from tools.ck3_live_run_id import current_machine_id
            protocol_out=sys.__stdout__
            sequence=0
            site_counts={}
            def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
            def rpc(consumer,request):
                global sequence
                sequence+=1;site_counts[consumer]=site_counts.get(consumer,0)+1
                protocol_out.write(json.dumps({'type':'request','sequence':sequence,'consumer':consumer,'input_json':canonical(request).decode()},ensure_ascii=False,separators=(',',':'))+'\\n');protocol_out.flush()
                raw=sys.stdin.readline()
                if not raw:raise RuntimeError('compiled Java response missing; no Python fallback')
                response=json.loads(raw)
                if type(response.get('sequence')) is not int or response['sequence']!=sequence:raise RuntimeError('Java response sequence differs')
                value=json.loads(response['wire_json'])
                if value.get('schema')!='xar.relief-relevance-consumer-transfer-output.v1':raise RuntimeError('compiled Java response schema differs')
                if value.get('consumer')!=consumer or value.get('native_action_authorized') is not False:raise RuntimeError('typed Java consumer binding differs')
                return value
            def load_test(name,relative):
                spec=importlib.util.spec_from_file_location(name,repo/relative);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module
            def source_closure():
                paths={repo/'tools/ck3_live_run_id.py'}
                for module in tuple(sys.modules.values()):
                    location=getattr(module,'__file__',None)
                    if not isinstance(location,str):continue
                    path=Path(location).resolve()
                    if path.suffix=='.pyc':path=path.with_suffix('.py')
                    if path.is_file() and path.suffix=='.py' and path.is_relative_to(repo) and 'tools/.venv' not in path.as_posix():paths.add(path)
                if len(paths)>2048:raise RuntimeError('bounded original import closure exceeded')
                refs=[{'path':path.relative_to(repo).as_posix(),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()} for path in sorted(paths)]
                if sum(ref['bytes'] for ref in refs)>33554432:raise RuntimeError('bounded original source bytes exceeded')
                return refs
            class BoundedLog(io.TextIOBase):
                def __init__(self):self.length=0;self.digest=hashlib.sha256();self.parts=[]
                def write(self,value):
                    raw=value.encode('utf-8');self.length+=len(raw);self.digest.update(raw)
                    if sum(map(len,self.parts))<2048:self.parts.append(value[:max(0,2048-sum(map(len,self.parts)))])
                    return len(value)
                def flush(self):pass
            log=BoundedLog()
            def digest(value):return hashlib.sha256(canonical(value)).hexdigest()
            def terminal(summary):
                protocol_out.write(json.dumps({'type':'done','summary':summary},ensure_ascii=False,separators=(',',':'))+'\\n');protocol_out.flush()
            
            from xar_autoplayer import strategy
            from xar_autoplayer.bridge import native_driver
            actual=json.loads(gzip.decompress((repo/'ck3_autonomous_player/tests/fixtures/portable_actual_695.json.gz').read_bytes()))
            def frame_request(snapshot,war,enemy):
                projected=take(snapshot,['source','native_revision','snapshot_id','revision','date_raw','episode_run_id','paused','map_ready','active_event','pending_character_interaction'])
                if isinstance(snapshot.get('played_character'),dict):projected['played_character']=take(snapshot['played_character'],['source','character_id','alive'])
                if isinstance(snapshot.get('diagnostics'),dict):projected['diagnostics']=take(snapshot['diagnostics'],['connected','bridge_pid','connection_generation'])
                wars=snapshot.get('active_wars')
                projected['active_wars']=[war_projection(row) for row in wars] if isinstance(wars,list) else None
                index=next((index for index,row in enumerate(wars or []) if row is war),None)
                detached_wars=[] if index is not None else [war_projection(war)]
                war_ref={'collection':'active_wars','index':index} if index is not None else {'collection':'detached_wars','index':0}
                enemies=war.get('enemy_armies')
                enemy_index=next((index for index,row in enumerate(enemies or []) if row is enemy),None)
                detached_enemies=[] if enemy_index is not None else [enemy_projection(enemy)]
                enemy_ref={'collection':'candidate_war_enemy_armies','index':enemy_index} if enemy_index is not None else {'collection':'detached_enemies','index':0}
                return {'schema':'xar.siege-relief-relevance-input.v1','frame':{'schema':'xar.realm-siege-request.v1','snapshot':projected,'detached_wars':detached_wars,'detached_enemies':detached_enemies,'candidate_war_ref':war_ref,'candidate_enemy_ref':enemy_ref}}
            sites={'_choose_one_life_turn_core':'turn_core','_defender_siege_reserve_raise_plan':'reserve_raise','_defender_siege_observation_one_day_watch':'stationary_watch','_primary_defender_siege_relief_assessment':'relief_assessment'}
            def java_relevant(snapshot,war,enemy):
                current=inspect.currentframe().f_back;consumer=None
                while current is not None:
                    if current.f_code.co_name in sites:consumer=sites[current.f_code.co_name];break
                    current=current.f_back
                if consumer is None:raise RuntimeError('unmapped actual original relief consumer')
                result=rpc(consumer,frame_request(snapshot,war,enemy))
                if result.get('observation_status')!='available' or type(result.get('value')) is not bool:raise RuntimeError('missing Java observation cannot become false/zero')
                return result['value']
            def choose(case):
                return strategy.choose_one_life_turn(case['history_rows'],snapshot=case['snapshot'],action_steps=case['action_steps'],bridge_capabilities=case['bridge_capabilities'],battle_speed_readiness=case['battle_speed_readiness'])
            def assess(case):
                snapshot=case['snapshot'];army=snapshot['player_armies'][0]
                return strategy._primary_defender_siege_relief_assessment(snapshot,commands=case['history_rows'],active_wars=snapshot['active_wars'],controlled_armies=[army],pursuit_army=army)
            def nonleading():
                case=copy.deepcopy(actual);war=case['snapshot']['active_wars'][0];war['player_is_primary_war_leader']=False
                for enemy in war['enemy_armies']:enemy.update(siege_province_in_player_subrealm=True,move_target_province_id=None,route_province_ids=[],route_read_status='complete_empty')
                return case
            def without_termination(case):
                result=copy.deepcopy(case);result['action_steps']=[step for step in result['action_steps'] if not step.startswith('query-war-termination-options-')];return result
            def scenarios():
                case=nonleading();snapshot=case['snapshot'];war=snapshot['active_wars'][0];army=snapshot['player_armies'][0]
                result={'actual_primary':{'assessment':assess(actual),'plan':choose(actual)},'nonleading':{'assessment':assess(case),'plan':choose(case)},'nonleading_tactical':{'plan':choose(without_termination(case))}}
                missing=nonleading();missing['snapshot']['army_strengths_status']='partial'
                for row in missing['snapshot']['army_strengths']:
                    if row.get('scope_role')=='active_war_enemy' and war['war_id'] in row.get('war_ids',[]):row.update(status='unavailable',current_soldiers=None,maximum_soldiers=None,ai_base_power_raw=None)
                missing_assessment=assess(missing)
                if missing_assessment.get('status')!='observation_unavailable':raise AssertionError('missing native strength became an available numeric budget')
                result['missing_strength']={'assessment':missing_assessment,'plan':choose(without_termination(missing))}
                # The actual reserve/watch consumers receive the same retained data plus explicit missing observations.
                guard_case=copy.deepcopy(missing);guard=guard_case['snapshot'];guard_army=guard['player_armies'][0]
                guard['army_strengths_queried_snapshot_id']=guard['snapshot_id'];guard['army_strengths_queried_revision']=guard['revision']
                steps=set(guard_case['action_steps']);steps.update([strategy.QUERY_PLAYER_DEFAULT_RAISE_STEP,strategy.RAISE_TROOPS_STEP,'life-advance-one-day'])
                need={'status':'observation_unavailable','required_observation':'complete-same-frame-siege-position-and-war-strength','war_ids':[war['war_id']]}
                reserve=strategy._defender_siege_reserve_raise_plan(guard_case['history_rows'],guard,siege_relief=need,active_wars=guard['active_wars'],controlled_armies=[guard_army],available_steps=steps,war_summary=[])
                hostiles=tuple(sorted({enemy['army_id'] for observed_war in guard['active_wars'] for enemy in observed_war.get('enemy_armies',[]) if enemy.get('retreating') is not True}))
                watch=strategy._defender_siege_observation_one_day_watch(guard_case['history_rows'],guard,siege_relief=need,active_wars=guard['active_wars'],controlled_armies=[guard_army],hostile_army_ids=hostiles,route_evidence_issues=[],battle_control_status='not_in_combat',available_steps=steps,war_summary=[])
                if reserve is not None and str(reserve.get('selected_step')).startswith('raise'):raise AssertionError('missing native strength allowed reserve submission')
                result['missing_strength_guard_consumers']={'reserve':reserve,'watch':watch}
                unknown=nonleading();moving=unknown['snapshot']['player_armies'][0];moving.update(army_state='moving',army_state_code=7,move_target_province_id=2619,route_province_ids=[2619],route_read_status='complete_nonempty')
                unknown_plan=choose(without_termination(unknown))
                if str(unknown_plan.get('selected_step')).startswith('move-army-'):raise AssertionError('UNKNOWN committed move was reissued')
                result['unknown_committed_move']={'assessment':assess(unknown),'plan':unknown_plan}
                core=copy.deepcopy(unknown);core['snapshot'].pop('army_strengths_status',None);core['snapshot']['army_strengths']=[]
                result['moving_contact_guard']={'plan':choose(without_termination(core))}
                outside=nonleading()
                for enemy in outside['snapshot']['active_wars'][0]['enemy_armies']:enemy['siege_province_in_player_subrealm']=False
                result['outside_realm']={'assessment':assess(outside),'plan':choose(without_termination(outside))}
                if result['nonleading_tactical']['plan'].get('selected_step')==result['outside_realm']['plan'].get('selected_step') and result['nonleading_tactical']['plan'].get('phase')==result['outside_realm']['plan'].get('phase'):raise AssertionError('native realm observation did not affect actual plan/step')
                return result
            saved=strategy._defender_siege_is_relief_relevant
            try:
                with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                    golden_bytes=Path(sys.argv[2]).read_bytes();reference=json.loads(golden_bytes)
                    if hashlib.sha256(golden_bytes).hexdigest()!=sys.argv[3] or reference.get('schema')!='xar.siege-relief-relevance-original-producer-golden.v1':raise AssertionError('qualified original golden schema or SHA differs')
                    current=actual['snapshot'];current_war=current['active_wars'][0]
                    if frame_request(current,current_war,current_war['enemy_armies'][0])!=next(row['request'] for row in reference['bases'] if row['name']=='actual'):raise AssertionError('whole strategy input differs from actual original producer base')
                    baseline=scenarios();before=source_closure()
                    strategy._defender_siege_is_relief_relevant=java_relevant
                    observed=scenarios();after=source_closure()
                    if baseline!=observed:raise AssertionError('compiled Java bytes changed full original assessment/plan')
                    if before!=after:raise AssertionError('original import closure drifted')
                    if set(site_counts)!=set(sites.values()) or any(count<1 for count in site_counts.values()):raise AssertionError('not all four actual consumers traversed: '+str(site_counts))
                terminal({'status':'PASS','machine_id':current_machine_id(),'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_live_qualification':False,'source_unchanged':True,'source_closure_files':len(before),'source_closure_sha256':digest(before),'source_map':[{'consumer':name,'consumer_function':next(function for function,site in sites.items() if site==name),'calls':count,'source_ref':next(ref for ref in before if ref['path']=='ck3_autonomous_player/src/xar_autoplayer/strategy.py')} for name,count in sorted(site_counts.items())],'whole_consumer_scenarios':[{'name':name,'origin':'retained_portable695_or_explicit_synthetic_input_variant_no_new_after','baseline_sha256':digest(baseline[name]),'java_sha256':digest(observed[name]),'selected_step':observed[name].get('plan',{}).get('selected_step'),'phase':observed[name].get('plan',{}).get('phase')} for name in baseline],'realm_observation_changes_actual_plan_or_step':True,'missing_strength_not_zero':True,'unknown_move_not_reissued':True,'legacy_transform_preimage_guard':'unchanged; old BASE_SHA256 45c164297b90b32203e7860b4a7735cfa65c5ca1db7141e898d15395d2e47e78 suite not run against incompatible current source','log_bytes':log.length,'log_sha256':log.digest.hexdigest()})
            except BaseException as error:
                terminal({'status':'RED','machine_id':current_machine_id(),'error':str(error)[:2048],'traceback':traceback.format_exc()[-4096:],'site_counts':site_counts,'log_bytes':log.length,'log_sha256':log.digest.hexdigest(),'bounded_log':''.join(log.parts)})
                raise SystemExit(1)
            finally:strategy._defender_siege_is_relief_relevant=saved
            
            """;

}
