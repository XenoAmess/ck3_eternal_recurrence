package org.xar.ck3.control.wave2.finance.giftwarcash;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Offline capture only. The shared qualified Job owner runs this source, never ordinary JUnit. */
public final class GiftWarCashGoldenCapture {
    private GiftWarCashGoldenCapture() { }

    public static void main(String[] arguments) throws IOException, InterruptedException {
        if (arguments.length != 3) { throw new IllegalArgumentException("python repo new-output required"); }
        Path output = Path.of(arguments[2]).toAbsolutePath();
        if (Files.exists(output)) { throw new IllegalArgumentException("output must be a new path"); }
        Process child = new ProcessBuilder(List.of(arguments[0], "-c", SCRIPT, arguments[1], output.toString()))
                .directory(Path.of(arguments[1]).toFile()).inheritIO().start();
        if (!child.waitFor(90, TimeUnit.SECONDS)) {
            child.destroyForcibly();
            throw new IllegalStateException("producer capture timeout; parent Job owns the full tree");
        }
        if (child.exitValue() != 0) { throw new IllegalStateException("producer capture exit " + child.exitValue()); }
        if (!Files.isRegularFile(output) || Files.size(output) > 90_000) {
            throw new IllegalStateException("bounded nonempty output required");
        }
    }

    private static final String SCRIPT = """
            import sys,json,copy,hashlib,datetime
            from pathlib import Path
            repo=Path(sys.argv[1]); output=Path(sys.argv[2])
            sys.path.insert(0,str(repo/'ck3_autonomous_player/src'))
            sys.path.insert(0,str(repo/'ck3_autonomous_player/tests/unit'))
            from test_faction_gift_wartime_cash_v1 import inputs,ACTUAL
            from xar_autoplayer.faction_gift_wartime_cash_v1 import assess_faction_gift_wartime_cash_v1
            cases=[]
            def add(name,change=None,gold=100000000,wars=True):
                snapshot,candidate,kwargs=inputs(gold=gold,wars=wars)
                if change is not None: change(snapshot,candidate,kwargs)
                expected=assess_faction_gift_wartime_cash_v1(snapshot,candidate,**kwargs)
                def project(source,names):
                    return {name:source[name] for name in names if name in source}
                candidate={'choice':project(candidate['choice'],['player_character_id','native_snapshot_revision','date_raw','gold_cost_raw']),
                    'observation':project(candidate['observation'],['player_character_id','native_snapshot_revision','observed_date_raw','player_gold_raw','player_gold_scale','gift_preview'])}
                candidate['observation']['gift_preview']=project(candidate['observation']['gift_preview'],['gold_cost_raw'])
                request={'schema':'xar.gift-war-cash-input.v1','snapshot':snapshot,'candidate':candidate,**kwargs}
                cases.append({'name':name,'request':request,'expected':expected})
            add('complete_ample_cash')
            add('outside_wartime',wars=False)
            add('actual4276_floor_failure',gold=ACTUAL['candidate']['observation']['player_gold_raw'])
            add('one_gold_below_package',gold=64000000)
            add('exact_package_threshold',gold=65000000)
            add('missing_wars',lambda s,c,k:s.pop('active_wars'))
            add('zero_war_id',lambda s,c,k:s['active_wars'][0].update(war_id=0))
            add('stale_choice',lambda s,c,k:c['choice'].update(native_snapshot_revision=1))
            add('wrong_wallet_scale',lambda s,c,k:s['played_character_gold'].update(scale=1))
            add('negative_gift_cost',lambda s,c,k:c['choice'].update(gold_cost_raw=-1))
            add('preview_cost_mismatch',lambda s,c,k:c['observation']['gift_preview'].update(gold_cost_raw=1))
            for name in ['root','spending','market','mercenary_ledger']:
                add(name+'_null',lambda s,c,k,name=name:k.update({name:None}))
            add('stale_root',lambda s,c,k:k['root'].update(snapshot_revision=1))
            add('maintenance_unknown',lambda s,c,k:k['root']['player_max_monthly_gold_maintenance_v1'].update(status='unavailable'))
            add('maintenance_high',lambda s,c,k:k['root']['player_max_monthly_gold_maintenance_v1']['value'].update(raw=3000000))
            add('maintenance_negative',lambda s,c,k:k['root']['player_max_monthly_gold_maintenance_v1']['value'].update(raw=-1))
            add('maintenance_uint64',lambda s,c,k:k['root']['player_max_monthly_gold_maintenance_v1']['value'].update(raw=18446744073709551615))
            add('stale_spending',lambda s,c,k:k['spending']['frame'].update(native_revision=1))
            add('wrong_spending_war_count',lambda s,c,k:k['spending']['budget'].update(active_war_count=2))
            add('negative_reserved',lambda s,c,k:k['spending']['budget']['reserved_raw'].update(gold=-1))
            add('pending_mercenary_unknown',lambda s,c,k:k['mercenary_ledger'].update(pending={'status':'unknown'}))
            add('stale_market_frame',lambda s,c,k:k['market_source_frame'].update(native_revision=1))
            add('incomplete_cost_vector',lambda s,c,k:k['market']['rows'][0]['final_terms'].update(resource_costs_raw=[30000000]))
            add('cannot_afford_quote',lambda s,c,k:k['market']['rows'][0]['final_terms'].update(can_afford=False))
            add('hostile_spawn',lambda s,c,k:s['active_wars'][0].update(enemy_armies=[{'current_province_id':2630}]))
            add('unready_quote',lambda s,c,k:k['market']['rows'][0]['readiness_v1'].update(hire_ready=False))
            add('employed_quote',lambda s,c,k:k['market']['rows'][0].update(employer_id=77))
            add('tie_chooses_larger_id',lambda s,c,k:k['market']['rows'].append({**copy.deepcopy(k['market']['rows'][0]),'company_id':10}))
            add('maximum_quote_not_cheapest',lambda s,c,k:k['market']['rows'].append({**copy.deepcopy(k['market']['rows'][0]),'company_id':11,'final_terms':{**copy.deepcopy(k['market']['rows'][0]['final_terms']),'resource_costs_raw':[40000000]+[0]*9}}))
            sources=['ck3_autonomous_player/src/xar_autoplayer/faction_gift_wartime_cash_v1.py','ck3_autonomous_player/src/xar_autoplayer/activity_feast_stage5_budget_v1.py','ck3_autonomous_player/src/xar_autoplayer/m5_observed_opportunity_selector.py','ck3_autonomous_player/src/xar_autoplayer/bridge/faction_gift_formal_route_v1.py','ck3_autonomous_player/tests/unit/test_faction_gift_wartime_cash_v1.py','ck3_autonomous_player/tests/unit/fixtures/c11_gift4276_applied4284.json']
            bindings=[{'path':path,'sha256':hashlib.sha256((repo/path).read_bytes()).hexdigest()} for path in sources]
            captured={'schema':'xar.gift-war-cash-original-producer-golden.v1','machine_id':'xenoamess-full-tower-eb9d2c1186','observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_bindings':bindings,'capture_method':'Unchanged real assess_faction_gift_wartime_cash_v1; existing test inputs reuse actual4276 gift source, with explicitly synthetic complete market and unpaid commitments. Consumed candidate projection only; no recreated live qualification. No Game or RPC.','cases':cases}
            raw=(json.dumps(captured,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode('utf-8')
            if len(raw)>90000: raise ValueError('golden budget exceeded')
            output.parent.mkdir(parents=True,exist_ok=True)
            with output.open('xb') as handle: handle.write(raw)
            print(json.dumps({'cases':len(cases),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'machine_id':captured['machine_id'],'observed_at_utc':captured['observed_at_utc']}))
            """;
}
