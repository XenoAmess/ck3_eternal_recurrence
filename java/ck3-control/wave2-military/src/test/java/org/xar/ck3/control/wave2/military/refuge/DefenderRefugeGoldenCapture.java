package org.xar.ck3.control.wave2.military.refuge;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Test-only transport for the unchanged legacy producers; shared bounded Job owner executes it. */
public final class DefenderRefugeGoldenCapture {
    private DefenderRefugeGoldenCapture() { }
    public static void main(String[] arguments) throws Exception {
        if (arguments.length == 10 && arguments[3].equals("--compiled-consumers")) {
            CompiledConsumerSupport.run(arguments, DefenderRefugeConsumerTransfer.class, DefenderRefugeGoldenCapture.class, DefenderRefugeConsumerTransfer.INPUT_SCHEMA, DefenderRefugeConsumerTransfer.OUTPUT_SCHEMA, DefenderRefugeConsumerTransfer::evaluate, compiledScript());
            return;
        }
        if (arguments.length != 3) { throw new IllegalArgumentException("repo python new-output required"); }
        Path output = Path.of(arguments[2]).toAbsolutePath();
        if (Files.exists(output)) { throw new IllegalArgumentException("capture must preserve existing output"); }
        Process child = new ProcessBuilder(List.of(arguments[1], "-c", SCRIPT, arguments[0], output.toString()))
                .directory(Path.of(arguments[0]).toFile()).inheritIO().start();
        if (!child.waitFor(90, TimeUnit.SECONDS)) {
            child.destroyForcibly(); throw new IllegalStateException("producer capture timeout; parent Job owns tree cleanup");
        }
        if (child.exitValue() != 0) { throw new IllegalStateException("legacy producer exited " + child.exitValue()); }
        if (!Files.isRegularFile(output) || Files.size(output) == 0 || Files.size(output) > 71_680) {
            throw new IllegalStateException("finite nonempty capture required");
        }
    }

    private static final String SCRIPT = """
            import sys,json,copy,hashlib,datetime
            from pathlib import Path
            repo=Path(sys.argv[1]);output=Path(sys.argv[2]);sys.path.insert(0,str(repo/'ck3_autonomous_player/src'))
            if hashlib.sha256((repo/'ck3_autonomous_player/src/xar_autoplayer/defender_refuge_candidates_v1.py').read_bytes()).hexdigest()!='972841812e30f9f5b5aca0f6f67210eb48c8e2165d3e244925d623cc4e64a220':raise ValueError('original-producer oracle requires retained original source preimage; Java delegation cannot generate its own expected values')
            from xar_autoplayer.defender_refuge_candidates_v1 import direct_vassal_capital_province_ids as capitals,direct_vassal_refuge_lifecycle_scope as lifecycle,same_frame_direct_vassal_refuge_scope as cached_scope
            def take(value,names):return {key:copy.deepcopy(value[key]) for key in names if key in value}
            def title(value):return None if value is None else take(value,['title_id','tier_raw'])
            def root_projection(value):
                result=take(value,['status','player_character_id','top_liege_character_id','snapshot_revision','date_raw','direct_landed_vassal_character_ids'])
                if 'readiness' in value:result['readiness']=take(value['readiness'],['direct_landed_vassals_ready','related_character_contexts_ready'])
                if 'related_character_contexts' in value:
                    result['related_character_contexts']=[]
                    for row in value['related_character_contexts']:
                        context=take(row,['relationship_role','character_id','immediate_liege_character_id','top_liege_character_id','capital_province_id'])
                        if 'primary_title' in row:context['primary_title']=title(row['primary_title'])
                        result['related_character_contexts'].append(context)
                if 'held_title_partition' in value:result['held_title_partition']=[{**take(row,['capital_province_id']),'title':title(row.get('title'))} for row in value['held_title_partition']]
                return result
            def snapshot_projection(value):
                result=take(value,['paused','map_ready','active_event','pending_character_interaction','actor_character_id','snapshot_id','revision','native_revision','date_raw'])
                if 'played_character' in value:result['played_character']=take(value['played_character'],['character_id'])
                if 'diagnostics' in value:result['diagnostics']=take(value['diagnostics'],['bridge_pid','connection_generation'])
                if 'active_wars' in value:
                    result['active_wars']=[]
                    for war in value['active_wars']:
                        row=take(war,['player_side','player_is_primary_war_leader','war_objective_province_ids'])
                        if 'enemy_armies' in war:row['enemy_armies']=[take(enemy,['army_id','retreating']) for enemy in war['enemy_armies']]
                        result['active_wars'].append(row)
                if 'player_armies' in value:result['player_armies']=[take(row,['army_id','current_province_id','owner_character_id','controllable','army_state','in_combat','retreating','route_province_ids','move_target_province_id']) for row in value['player_armies']]
                return result
            bases=[]
            for name,filename in [('initial','defender_refuge_actual_projection.json'),('arrived','arrived_refuge_actual_projection.json')]:
                original=json.loads((repo/'ck3_autonomous_player/tests/unit/fixtures'/filename).read_text(encoding='utf-8'))
                sem=original['semantic'];history=original['history']
                original_root=next(row['result']['campaign_root_context'] for row in (history if name=='initial' else reversed(history)) if (row.get('index')==388 if name=='initial' else row.get('command')=='query-campaign-root-context-v1') and isinstance(row.get('result'),dict) and 'campaign_root_context' in row['result'])
                root=root_projection(original_root);snapshot=snapshot_projection(sem)
                binding={key:sem[key] for key in ['snapshot_id','revision','native_revision','date_raw']}
                binding.update(actor_character_id=sem['played_character']['character_id'],bridge_pid=sem['diagnostics']['bridge_pid'],connection_generation=sem['diagnostics']['connection_generation'])
                request={'schema':'xar.defender-refuge-input.v1','snapshot':snapshot,'root':root,'cached_query':{'cache_binding':binding,'campaign_root_context':copy.deepcopy(root)}}
                if capitals(root)!=capitals(original_root) or lifecycle(snapshot,root)!=lifecycle(sem,original_root):raise ValueError('consumed projection changed original producer result')
                if lifecycle(snapshot,root) is None:raise ValueError('retained actual refuge scope unexpectedly unavailable')
                bases.append({'name':name,'origin':'historical_actual_consumed_projection_not_current_native_qualification','request':request})
            byname={row['name']:row['request'] for row in bases}
            cases=[]
            def patch(path,value,operation='set'):return {'operation':operation,'path':path,'value':value}
            def apply(request,operations):
                for operation in operations:
                    parent=request
                    for key in operation['path'][:-1]:parent=parent[int(key)] if isinstance(parent,list) else parent[key]
                    key=operation['path'][-1]
                    if isinstance(parent,list):key=int(key)
                    if operation['operation']=='remove':del parent[key]
                    else:parent[key]=copy.deepcopy(operation['value'])
            def add(name,base='initial',operations=None):
                operations=operations or [];request=copy.deepcopy(byname[base]);apply(request,operations)
                expected={'schema':'xar.defender-refuge-observation.v1','direct_vassal_capital_province_ids':capitals(request['root']),'lifecycle_scope':lifecycle(request['snapshot'],request['root']),'same_frame_cached_scope':cached_scope(request['snapshot'],request['cached_query'])}
                cases.append({'name':name,'base':base,'origin':'unchanged_historical_projection' if not operations else 'explicit_synthetic_variant','patches':operations,'expected':expected})
            def both(path,value):return [patch(['root']+path,value),patch(['cached_query','campaign_root_context']+path,value)]
            add('actual_initial');add('actual_arrived',base='arrived')
            add('snapshot_null',operations=[patch(['snapshot'],None)])
            add('root_null_cached_root_retained',operations=[patch(['root'],None)])
            add('cached_query_null',operations=[patch(['cached_query'],None)])
            add('readiness_unavailable',operations=both(['readiness','related_character_contexts_ready'],False))
            initial=byname['initial'];root=initial['root'];indices=[index for index,row in enumerate(root['related_character_contexts']) if row.get('relationship_role')=='direct_landed_vassal']
            if len(indices)<2:raise ValueError('two original vassal rows required for finite duplicate/ordering vectors')
            first,second=indices[:2]
            add('duplicate_direct_ids',operations=both(['direct_landed_vassal_character_ids'],root['direct_landed_vassal_character_ids']+[root['direct_landed_vassal_character_ids'][0]]))
            rows=copy.deepcopy(root['related_character_contexts']);rows.pop(first)
            add('incomplete_context_census',operations=both(['related_character_contexts'],rows))
            add('duplicate_context',operations=both(['related_character_contexts'],root['related_character_contexts']+[root['related_character_contexts'][first]]))
            add('wrong_immediate_liege',operations=both(['related_character_contexts',str(first),'immediate_liege_character_id'],1))
            add('wrong_top_liege',operations=both(['related_character_contexts',str(first),'top_liege_character_id'],1))
            add('duplicate_capital',operations=both(['related_character_contexts',str(second),'capital_province_id'],root['related_character_contexts'][first]['capital_province_id']))
            add('zero_capital',operations=both(['related_character_contexts',str(first),'capital_province_id'],0))
            add('nullable_capital_is_not_invented',operations=both(['related_character_contexts',str(first),'capital_province_id'],None))
            add('title_tier_outside_native_range',operations=both(['related_character_contexts',str(first),'primary_title','tier_raw'],7))
            add('primary_title_null',operations=both(['related_character_contexts',str(first),'primary_title'],None))
            add('reverse_input_order_still_sorts_capitals',operations=both(['related_character_contexts'],list(reversed(root['related_character_contexts'])))+both(['direct_landed_vassal_character_ids'],list(reversed(root['direct_landed_vassal_character_ids']))))
            add('observed_empty_direct_capital_set',operations=both(['direct_landed_vassal_character_ids'],[])+both(['related_character_contexts'],[row for row in root['related_character_contexts'] if row.get('relationship_role')!='direct_landed_vassal']))
            add('stale_root_revision',operations=both(['snapshot_revision'],root['snapshot_revision']+1))
            add('snapshot_native_revision_changed',operations=[patch(['snapshot','native_revision'],initial['snapshot']['native_revision']+1)])
            add('snapshot_date_changed',operations=[patch(['snapshot','date_raw'],initial['snapshot']['date_raw']+24)])
            for field in ['snapshot_id','revision','native_revision','date_raw','actor_character_id','bridge_pid','connection_generation']:
                prior=initial['cached_query']['cache_binding'][field]
                add('stale_cache_'+field,operations=[patch(['cached_query','cache_binding',field],prior+':old' if isinstance(prior,str) else prior+1)])
            add('public_unit_slot_zero',operations=[patch(['snapshot','player_armies','0','army_id'],0)])
            enemies=initial['snapshot']['active_wars'][0]['enemy_armies'];active=[row for row in enemies if row.get('retreating') is not True]
            if not active:raise ValueError('historical active hostile required')
            add('duplicate_active_hostile_id',operations=[patch(['snapshot','active_wars','0','enemy_armies'],active+[active[0]])])
            add('hostile_limit_65',operations=[patch(['snapshot','active_wars','0','enemy_armies'],[{'army_id':index,'retreating':False} for index in range(65)])])
            add('all_hostiles_retreating',operations=[patch(['snapshot','active_wars','0','enemy_armies'],[{**row,'retreating':True} for row in enemies])])
            add('committed_moving_intent',operations=[patch(['snapshot','player_armies','0','army_state'],'moving')])
            add('two_controlled_armies',operations=[patch(['snapshot','player_armies'],initial['snapshot']['player_armies']+[initial['snapshot']['player_armies'][0]])])
            add('war_objective_present',operations=[patch(['snapshot','active_wars','0','war_objective_province_ids'],[2619])])
            add('paused_false',operations=[patch(['snapshot','paused'],False)])
            sources=['ck3_autonomous_player/src/xar_autoplayer/defender_refuge_candidates_v1.py','ck3_autonomous_player/src/xar_autoplayer/strategy.py','ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py','ck3_autonomous_player/tests/unit/test_defender_refuge_candidates.py','ck3_autonomous_player/tests/unit/test_arrived_refuge_lifecycle.py','ck3_autonomous_player/tests/unit/fixtures/defender_refuge_actual_projection.json','ck3_autonomous_player/tests/unit/fixtures/arrived_refuge_actual_projection.json']
            bindings=[{'path':path,'bytes':(repo/path).stat().st_size,'sha256':hashlib.sha256((repo/path).read_bytes()).hexdigest()} for path in sources]
            data={'schema':'xar.defender-refuge-original-producer-golden.v1','machine_id':'xenoamess-full-tower-eb9d2c1186','observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_live_qualification':False,'source_bindings':bindings,'capture_method':'Unchanged three legacy producers. Two closed historical actual DTO projections; their cache binding wrapper is reconstructed exactly as existing tests from retained semantic metadata, not a current read qualification. Compact local test patches identify all synthetic variants. No Game/RPC/ledger.','bases':bases,'cases':cases}
            raw=(json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode('utf-8')
            if len(raw)>71680:raise ValueError('finite 70KiB golden budget exceeded')
            output.parent.mkdir(parents=True,exist_ok=True)
            with output.open('xb') as handle:handle.write(raw)
            print(json.dumps({'machine_id':data['machine_id'],'observed_at_utc':data['observed_at_utc'],'bases':len(bases),'cases':len(cases),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}))
            """;

    private static String compiledScript() { return SCRIPT.substring(0, SCRIPT.indexOf("bases=[]")) + COMPILED_CONSUMERS; }
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
                if value.get('schema')!='xar.defender-refuge-consumer-transfer-output.v1':raise RuntimeError('compiled Java response schema differs')
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
            from xar_autoplayer.bridge.service import GameplayBridgeService
            import pytest
            initial=load_test('test_defender_refuge_candidates','ck3_autonomous_player/tests/unit/test_defender_refuge_candidates.py')
            arrived=load_test('test_arrived_refuge_lifecycle','ck3_autonomous_player/tests/unit/test_arrived_refuge_lifecycle.py')
            def request(snapshot=None,root=None,cache=None):
                return {'schema':'xar.defender-refuge-input.v1','snapshot':None if snapshot is None else snapshot_projection(snapshot),'root':None if root is None else root_projection(root),'cached_query':None if cache is None else {'cache_binding':copy.deepcopy(cache.get('cache_binding')),'campaign_root_context':root_projection(cache['campaign_root_context']) if isinstance(cache.get('campaign_root_context'),dict) else None}}
            def java_capitals(root):return rpc('strategy_capitals',request(root=root))['value']
            def java_lifecycle(snapshot,root):return rpc('strategy_lifecycle',request(snapshot=snapshot,root=root))['value']
            def java_cached(snapshot,cache):return rpc('native_capabilities',request(snapshot=snapshot,cache=cache))['value']
            class Counts:
                def __init__(self):self.passed=0;self.failed=0;self.skipped=0
                def pytest_runtest_logreport(self,report):
                    if report.skipped:self.skipped+=1
                    elif report.failed:self.failed+=1
                    elif report.when=='call':self.passed+=1
            def suite():
                counts=Counts()
                code=pytest.main(['-q','-p','no:cacheprovider','--disable-warnings',str(repo/'ck3_autonomous_player/tests/unit/test_defender_refuge_candidates.py'),str(repo/'ck3_autonomous_player/tests/unit/test_arrived_refuge_lifecycle.py')],plugins=[counts])
                if code!=0 or counts.failed or counts.skipped or counts.passed!=13:raise RuntimeError('unchanged original refuge suites RED: '+str((int(code),counts.passed,counts.failed,counts.skipped)))
                return {'passed':counts.passed,'failed':counts.failed,'skipped':counts.skipped,'exit_code':int(code)}
            def scenarios():
                first,rows,_auto,cache=initial.actual();driver=initial.native_capabilities_driver(first,cache,rows)
                initial_steps=sorted(driver.capabilities()['action_steps']);initial_plan=GameplayBridgeService(driver).plan_turn()['plan']
                sem,history,_auto,_root,arrived_cache=arrived.actual();driver2=arrived.real_native_driver(sem,history,arrived_cache)
                steps=set(driver2.capabilities()['action_steps']);caps=sem['diagnostics']['hello']['capabilities']
                plan=strategy.choose_one_life_turn(history,snapshot=sem,action_steps=steps,bridge_capabilities=caps)
                missing_rows=[row for row in history if row.get('index',0)<547]
                missing=strategy.choose_one_life_turn(missing_rows,snapshot=sem,action_steps=steps,bridge_capabilities=caps)
                stale=copy.deepcopy(sem);stale['native_revision']+=1
                stale_steps=sorted(arrived.real_native_driver(stale,history,arrived_cache).capabilities()['action_steps'])
                forbidden=native_driver.preview_move_army_step(1023410456,2610)
                if forbidden in stale_steps:raise AssertionError('stale cache advertised refuge native channel')
                if plan.get('selected_step')==missing.get('selected_step') or missing.get('selected_step')!='query-campaign-root-context-v1':raise AssertionError('missing observation did not alter actual planner step')
                return {'initial_service':{'plan':initial_plan,'action_steps':initial_steps},'arrived_strategy':{'plan':plan,'action_steps':sorted(steps)},'missing_current_root':{'plan':missing},'stale_cache':{'action_steps':stale_steps}}
            saved=(strategy.direct_vassal_capital_province_ids,strategy.direct_vassal_refuge_lifecycle_scope,native_driver.same_frame_direct_vassal_refuge_scope)
            try:
                with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                    golden_bytes=Path(sys.argv[2]).read_bytes();reference=json.loads(golden_bytes)
                    if hashlib.sha256(golden_bytes).hexdigest()!=sys.argv[3] or reference.get('schema')!='xar.defender-refuge-original-producer-golden.v1':raise AssertionError('qualified original golden schema or SHA differs')
                    reference_bases={row['name']:row['request'] for row in reference['bases']}
                    first,first_rows,_first_auto,first_cache=initial.actual()
                    later,later_rows,_later_auto,later_root,later_cache=arrived.actual()
                    if request(first,first_cache['campaign_root_context'],first_cache)!=reference_bases['initial'] or request(later,later_root,later_cache)!=reference_bases['arrived']:raise AssertionError('whole consumer retained inputs differ from actual captured producer bases')
                    baseline_suite=suite();baseline=scenarios();before=source_closure()
                    strategy.direct_vassal_capital_province_ids=java_capitals
                    strategy.direct_vassal_refuge_lifecycle_scope=java_lifecycle
                    native_driver.same_frame_direct_vassal_refuge_scope=java_cached
                    java_suite=suite();actual=scenarios();after=source_closure()
                    if before!=after:raise AssertionError('original consumer import closure drifted')
                    if baseline!=actual:raise AssertionError('actual Java bytes changed complete original plan/action_steps')
                    if set(site_counts)!={'strategy_capitals','strategy_lifecycle','native_capabilities'} or any(count<1 for count in site_counts.values()):raise AssertionError('an actual refuge consumer was not traversed')
                source_map=[{'consumer':name,'calls':count,'source_ref':next(ref for ref in before if ref['path']==('ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py' if name=='native_capabilities' else 'ck3_autonomous_player/src/xar_autoplayer/strategy.py'))} for name,count in sorted(site_counts.items())]
                terminal({'status':'PASS','machine_id':current_machine_id(),'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_live_qualification':False,'baseline_suite':baseline_suite,'java_suite':java_suite,'source_unchanged':True,'source_closure_files':len(before),'source_closure_sha256':digest(before),'source_map':source_map,'whole_consumer_scenarios':[{'name':name,'origin':'historical_actual_and_explicit_missing_observation_inputs_no_new_after','baseline_sha256':digest(baseline[name]),'java_sha256':digest(actual[name]),'selected_step':actual[name].get('plan',{}).get('selected_step'),'phase':actual[name].get('plan',{}).get('phase')} for name in baseline],'missing_observation_changes_selected_step':True,'log_bytes':log.length,'log_sha256':log.digest.hexdigest()})
            except BaseException as error:
                terminal({'status':'RED','machine_id':current_machine_id(),'error':str(error)[:2048],'traceback':traceback.format_exc()[-4096:],'site_counts':site_counts,'log_bytes':log.length,'log_sha256':log.digest.hexdigest(),'bounded_log':''.join(log.parts)})
                raise SystemExit(1)
            finally:
                strategy.direct_vassal_capital_province_ids,strategy.direct_vassal_refuge_lifecycle_scope,native_driver.same_frame_direct_vassal_refuge_scope=saved
            
            """;

}
