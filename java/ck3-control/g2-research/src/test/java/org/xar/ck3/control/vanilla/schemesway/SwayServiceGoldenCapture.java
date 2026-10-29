package org.xar.ck3.control.vanilla.schemesway;

import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

/** Explicit finite compatibility capture; default Maven tests consume its committed result without Python. */
public final class SwayServiceGoldenCapture {
    private SwayServiceGoldenCapture() { }
    private static final String SCRIPT = """
            import copy, datetime, hashlib, json, pathlib, sys, tempfile, types
            from unittest.mock import patch
            root, fixture, output, machine = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3]), sys.argv[4]
            sys.path.insert(0, str(root/'ck3_autonomous_player/src'))
            from xar_autoplayer.bridge import ordinary_sway_service_v1 as original
            from xar_autoplayer.ordinary_sway_schedule_v1 import plan_ordinary_sway_schedule_v1
            from xar_autoplayer.sway_formal_consumer import SCHEMA, LEDGER_FILE
            from xar_autoplayer.bridge.driver import BridgeUnavailableError
            base = json.loads(fixture.read_bytes())['plan_cases'][0]['input']
            sources = ['ck3_autonomous_player/src/xar_autoplayer/bridge/ordinary_sway_service_v1.py',
                'ck3_autonomous_player/src/xar_autoplayer/ordinary_sway_schedule_v1.py',
                'ck3_autonomous_player/src/xar_autoplayer/sway_formal_consumer.py',
                'ck3_autonomous_player/src/xar_autoplayer/ordinary_sway_lifecycle_observation_v1.py']
            def refs():
                return [{'path':p,'bytes':len((root/p).read_bytes()),'sha256':hashlib.sha256((root/p).read_bytes()).hexdigest()} for p in sources]
            before = refs()
            cases = []
            specs = [
                ('new-start', 'query_selected_target', {'status':'applied','postcondition_verified':True,'action_id':'actual-consumer-action'}, None, False),
                ('ack-applied-unverified', 'query_selected_target', {'status':'applied','postcondition_verified':False}, None, False),
                *[(s,'query_selected_target',{'status':s},None,False) for s in ['receipt_pending','postcondition_pending','submission_unresolved','pending_recovery','no_positive_opportunity','future_status']],
                *[('followup-'+s,'query_selected_target',{'status':'already_applied','followup':{'decision':s}},None,False) for s in ['finish_selected_relation','return_to_opportunity_selection','native_start_unavailable','unknown']],
                ('pending-appeared','query_selected_target',{'status':'applied','postcondition_verified':True},'original',False),
                ('reconcile-original','reconcile_pending',{'status':'applied','postcondition_verified':True},'original',False),
                ('reconcile-changed','reconcile_pending',{'status':'applied','postcondition_verified':True},'changed',False),
                ('query-unavailable','query_selected_target',{},None,True),
                ('observed-empty','complete_no_relation',{},None,False),
                ('lifecycle-observed','observe_applied',{'status':'observed'},None,False),
                ('lifecycle-unavailable','observe_applied',{'status':'query_failed'},None,False)]
            for name, kind, result, current_pending, failure in specs:
                request = copy.deepcopy(base)
                ledger = {'schema':SCHEMA,'pending':None,'resolved':None}
                if kind == 'reconcile_pending':
                    ledger['pending'] = {'action_id':'original','actor_character_id':7,'target_character_id':900}
                    request['ledger']['pending'] = copy.deepcopy(ledger['pending'])
                if kind == 'observe_applied':
                    ledger['resolved'] = {'action_id':'original','status':'applied','postcondition_verified':True,'actor_character_id':7,'target_character_id':900}
                    request['ledger']['resolved'] = {'identity':{'action_id':'original','actor_character_id':7,'target_character_id':900,'scheme_instance_id':16777233,'scheme_instance_generation':1},'applied':True,'postcondition_verified':True,'terminal_observed':False,'reuse_gap':None}
                if kind == 'complete_no_relation': request['root']['direct_landed_vassal_character_ids'] = []
                job = plan_ordinary_sway_schedule_v1(request['snapshot'], selected_step='life-advance', root=request['root'], ledger=ledger, state=None)
                assert job['job'] == kind, (name,job)
                current = copy.deepcopy(ledger)
                if current_pending is not None:
                    current['pending'] = {'action_id':current_pending,'actor_character_id':7,'target_character_id':900}
                counts = {'query':0,'consume':0,'lifecycle':0,'fresh_plan':0,'fresh_execute':0}
                def query(**kwargs):
                    counts['query'] += 1
                    assert kwargs == {'expected_revision':4,'target_character_id':900}
                    if failure: raise BridgeUnavailableError('original writer retains unresolved durable intent')
                    return {'synthetic_native_boundary':True}
                def consume(*args,**kwargs): counts['consume'] += 1; return copy.deepcopy(result)
                def observe(*args,**kwargs): counts['lifecycle'] += 1; return copy.deepcopy(result)
                def fresh_plan(): counts['fresh_plan'] += 1; return {'id':'fresh-current-plan'}
                def fresh_execute(plan,**kwargs): counts['fresh_execute'] += 1; return {'status':'executed'}
                with tempfile.TemporaryDirectory(prefix='ordinary-sway-oracle-',dir=output.parent) as temp:
                    state_dir = pathlib.Path(temp)
                    (state_dir/LEDGER_FILE).write_text(json.dumps(current),encoding='utf-8')
                    service = types.SimpleNamespace(driver=types.SimpleNamespace(query_active_scheme_sway_target_private_v1=query),
                        _strategy_state_dir=lambda:state_dir,_plan_turn_internal=fresh_plan,_execute_planned_turn=fresh_execute)
                    planned = {'plan':{'selected_step':original.STEP,'ordinary_sway_job_v1':job},original.INPUT:{'snapshot':request['snapshot'],'root':request['root']}}
                    # Only external formal/native/lifecycle results are synthetic. Adapter, scheduler,
                    # lazy ledger read, scheduler write and fresh ordinary control flow are unchanged.
                    with patch.object(original,'consume_sway_private_once',consume), patch.object(original,'observe_resolved_sway_lifecycle_v1',observe):
                        actual = original.execute_ordinary_sway_v1(service,planned)
                    optional = actual['ordinary_sway_optional']
                    cases.append({'id':name,'request':request,'current_pending':current['pending'],'formal_result':result,
                        'query_failure':failure,'expected':{'job':optional['job'],'outcome':optional['outcome'],
                            'scheduler_state':optional['scheduler_state'],'turn_owned':actual.get('selected_step')==original.STEP,
                            'counts':counts}})
            assert refs() == before, 'original sources changed during capture'
            output.write_text(json.dumps({'schema':'xar.java-ordinary-sway-service-original-golden/v1','machine_id':machine,
                'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),
                'sources':before,'scope':'actual unchanged ordinary adapter/scheduler with explicitly synthetic formal/native/lifecycle boundaries; no Game or full formal qualification',
                'cases':cases},ensure_ascii=False,sort_keys=True,separators=(',',':')),encoding='utf-8')
            print(json.dumps({'status':'PASS','cases':len(cases),'source_pre_post':'MATCH','native_game_calls':0}))
            """;

    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 5) { throw new IllegalArgumentException("windows-python repository original-golden output machine-id required"); }
        Path output = Path.of(arguments[3]);
        Process process = new ProcessBuilder(arguments[0], "-B", "-X", "utf8", "-c", SCRIPT,
                arguments[1], arguments[2], output.toString(), arguments[4]).inheritIO().start();
        if (!process.waitFor(30, TimeUnit.SECONDS)) {
            process.destroyForcibly(); process.waitFor(); throw new IllegalStateException("finite original adapter capture timeout");
        }
        if (process.exitValue() != 0) { throw new IllegalStateException("original adapter capture exit " + process.exitValue()); }
    }
}
