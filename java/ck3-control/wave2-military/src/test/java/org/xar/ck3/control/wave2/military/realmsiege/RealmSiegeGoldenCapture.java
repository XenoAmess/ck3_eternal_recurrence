package org.xar.ck3.control.wave2.military.realmsiege;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Offline fixture capture, run only by the shared bounded Job owner, never ordinary JUnit. */
public final class RealmSiegeGoldenCapture {
    private RealmSiegeGoldenCapture() { }

    public static void main(String[] arguments) throws IOException, InterruptedException {
        if (arguments.length != 3) { throw new IllegalArgumentException("repo python new-output required"); }
        Path output = Path.of(arguments[2]).toAbsolutePath();
        if (Files.exists(output)) { throw new IllegalArgumentException("new capture output required"); }
        Process child = new ProcessBuilder(List.of(arguments[1], "-c", SCRIPT, arguments[0], output.toString()))
                .directory(Path.of(arguments[0]).toFile()).inheritIO().start();
        if (!child.waitFor(90, TimeUnit.SECONDS)) {
            child.destroyForcibly();
            throw new IllegalStateException("capture timed out; shared Job owns remaining descendants");
        }
        if (child.exitValue() != 0) { throw new IllegalStateException("original producer capture exit " + child.exitValue()); }
        if (!Files.isRegularFile(output) || Files.size(output) == 0 || Files.size(output) > 71_680) {
            throw new IllegalStateException("capture did not produce bounded fixture");
        }
    }

    private static final String SCRIPT = """
            import sys,json,gzip,copy,hashlib,datetime
            from pathlib import Path
            repo=Path(sys.argv[1]); output=Path(sys.argv[2])
            sys.path.insert(0,str(repo/'ck3_autonomous_player/src'))
            from xar_autoplayer.nonleading_player_realm_siege_v1 import nonleading_player_realm_siege_v1 as enemy_scope, nonleading_player_realm_siege_war_v1 as war_scope
            fixture=repo/'ck3_autonomous_player/tests/fixtures/portable_actual_695.json.gz'
            raw=fixture.read_bytes()
            if hashlib.sha256(raw).hexdigest()!='da619ee770f2a4c124e9e625a9acc6913b2af96b8b1ab2af90896a67bd5e2937':raise ValueError('historical portable695 input identity changed')
            actual=json.loads(gzip.decompress(raw))['snapshot']
            def project(value,names):return {key:copy.deepcopy(value[key]) for key in names if key in value}
            def project_enemy(enemy):
                return project(enemy,['source','army_id','owner_character_id','controllable','army_state','army_state_code','in_combat','retreating','current_province_id','siege_province_in_player_subrealm','move_target_province_id','route_province_ids','route_read_status'])
            def project_war(war):
                result=project(war,['source','war_id','player_side','player_is_primary_war_leader','player_relative_war_score'])
                if 'enemy_armies' in war:result['enemy_armies']=None if war['enemy_armies'] is None else [project_enemy(row) for row in war['enemy_armies']]
                return result
            def project_snapshot(snapshot):
                result=project(snapshot,['source','native_revision','snapshot_id','revision','date_raw','episode_run_id','paused','map_ready','active_event','pending_character_interaction'])
                if 'played_character' in snapshot:result['played_character']=project(snapshot['played_character'],['source','character_id','alive'])
                if 'diagnostics' in snapshot:result['diagnostics']=project(snapshot['diagnostics'],['connected','bridge_pid','connection_generation'])
                if 'active_wars' in snapshot:result['active_wars']=[project_war(row) for row in snapshot['active_wars']]
                return result
            base=copy.deepcopy(actual)
            base_war=base['active_wars'][0]
            base_war['player_is_primary_war_leader']=False
            for enemy in base_war['enemy_armies']:
                enemy.update(siege_province_in_player_subrealm=True,move_target_province_id=None,route_province_ids=[],route_read_status='complete_empty')
            if enemy_scope(actual,actual['active_wars'][0],actual['active_wars'][0]['enemy_armies'][0]):raise ValueError('historical primary baseline unexpectedly nonleading')
            if not enemy_scope(base,base_war,base_war['enemy_armies'][0]):raise ValueError('declared synthetic stationary realm siege did not qualify')
            cases=[]
            def add(name,change=None,source=base,detached=None):
                snapshot=copy.deepcopy(source); war=snapshot['active_wars'][0]; enemy=war['enemy_armies'][0]
                if change is not None:change(snapshot,war,enemy)
                detached_wars=[];detached_enemies=[]
                war_ref={'collection':'active_wars','index':0};enemy_ref={'collection':'candidate_war_enemy_armies','index':0}
                if detached=='war':
                    war=copy.deepcopy(war);detached_wars=[war];enemy=war['enemy_armies'][0];war_ref['collection']='detached_wars'
                if detached=='enemy':
                    enemy=copy.deepcopy(enemy);detached_enemies=[enemy];enemy_ref['collection']='detached_enemies'
                expected={'schema':'xar.realm-siege-observation.v1','candidate_enemy_scope_observed':enemy_scope(snapshot,war,enemy),'candidate_war_scope_observed':war_scope(snapshot,war),'current_war_scopes_in_stored_order':[{'war_id':row.get('war_id'),'scope_observed':war_scope(snapshot,row),'enemy_scopes_in_stored_order':[enemy_scope(snapshot,row,item) for item in row.get('enemy_armies',[])]} for row in snapshot.get('active_wars',[])]}
                request={'schema':'xar.realm-siege-request.v1','snapshot':project_snapshot(snapshot),'detached_wars':[project_war(row) for row in detached_wars],'detached_enemies':[project_enemy(row) for row in detached_enemies],'candidate_war_ref':war_ref,'candidate_enemy_ref':enemy_ref}
                cases.append({'name':name,'origin':'historical_actual_projection' if source is actual else 'explicit_synthetic_variant_of_historical_actual','request':request,'expected':expected})
            add('historical_actual_primary',source=actual)
            add('synthetic_current_realm_siege')
            add('outside_player_subrealm',lambda s,w,e:e.update(siege_province_in_player_subrealm=False))
            add('unknown_subrealm',lambda s,w,e:e.update(siege_province_in_player_subrealm=None))
            add('own_owner',lambda s,w,e:e.update(owner_character_id=s['played_character']['character_id']))
            add('enemy_source_unknown',lambda s,w,e:e.update(source='synthetic_or_unknown'))
            add('committed_departure',lambda s,w,e:e.update(move_target_province_id=2623,route_province_ids=[2623]))
            add('wrong_snapshot_id',lambda s,w,e:s.update(snapshot_id='native:old'))
            add('disconnected',lambda s,w,e:s['diagnostics'].update(connected=False))
            add('actor_dead',lambda s,w,e:s['played_character'].update(alive=False))
            add('unpaused',lambda s,w,e:s.update(paused=False))
            add('map_not_ready',lambda s,w,e:s.update(map_ready=False))
            add('native_revision_zero',lambda s,w,e:s.update(native_revision=0,snapshot_id='native:0'))
            add('public_revision_negative',lambda s,w,e:s.update(revision=-1))
            add('bridge_pid_zero',lambda s,w,e:s['diagnostics'].update(bridge_pid=0))
            add('connection_generation_negative',lambda s,w,e:s['diagnostics'].update(connection_generation=-1))
            add('event_modal',lambda s,w,e:s.update(active_event={'instance_id':44}))
            add('interaction_modal',lambda s,w,e:s.update(pending_character_interaction={'instance_id':45}))
            add('primary_leader',lambda s,w,e:w.update(player_is_primary_war_leader=True))
            add('attacker',lambda s,w,e:w.update(player_side='attacker'))
            add('score_at_minus100',lambda s,w,e:w.update(player_relative_war_score=-100))
            add('score_at_plus100',lambda s,w,e:w.update(player_relative_war_score=100))
            add('enemy_controllable',lambda s,w,e:e.update(controllable=True))
            add('enemy_in_combat',lambda s,w,e:e.update(in_combat=True))
            add('enemy_retreating',lambda s,w,e:e.update(retreating=True))
            add('enemy_stance_code_disagrees',lambda s,w,e:e.update(army_state_code=7))
            add('route_status_unknown',lambda s,w,e:e.update(route_read_status='unknown'))
            add('missing_move_target',lambda s,w,e:e.pop('move_target_province_id'))
            add('missing_route',lambda s,w,e:e.pop('route_province_ids'))
            add('detached_equal_war',detached='war')
            add('detached_equal_enemy',detached='enemy')
            add('large_exact_revision_and_negative_date',lambda s,w,e:s.update(native_revision=2**80+1,snapshot_id='native:'+str(2**80+1),revision=2**80,date_raw=-2**80))
            sources=['ck3_autonomous_player/src/xar_autoplayer/nonleading_player_realm_siege_v1.py','ck3_autonomous_player/src/xar_autoplayer/strategy.py','ck3_autonomous_player/src/xar_autoplayer/war_reinforcement_tradeoff_v1.py','ck3_autonomous_player/src/xar_autoplayer/war_strategic_reserve_v1.py','ck3_autonomous_player/tests/unit/test_nonleading_siege_priority_v1.py','ck3_autonomous_player/tests/fixtures/portable_actual_695.json.gz']
            bindings=[{'path':path,'bytes':(repo/path).stat().st_size,'sha256':hashlib.sha256((repo/path).read_bytes()).hexdigest()} for path in sources]
            data={'schema':'xar.realm-siege-original-producer-golden.v1','machine_id':'xenoamess-full-tower-eb9d2c1186','observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_bindings':bindings,'capture_method':'Unchanged real nonleading_player_realm_siege_v1 and war_v1 applied to declared consumed-field projection of historical portable695 plus explicitly synthetic variants. Actual historical row remains primary; synthetic stationary nonleading realm siege is not a live observation. Detached Python objects are captured as independent document nodes. No Game/RPC/ledger.','actual_live_qualification':False,'cases':cases}
            raw=(json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode('utf-8')
            if len(raw)>131072:raise ValueError('golden exceeds explicit 128KiB bounded decompression domain: '+str(len(raw)))
            payload=gzip.compress(raw,compresslevel=9,mtime=0)
            if len(payload)>71680:raise ValueError('compressed golden exceeds finite 70KiB disk budget')
            output.parent.mkdir(parents=True,exist_ok=True)
            with output.open('xb') as handle:handle.write(payload)
            print(json.dumps({'machine_id':data['machine_id'],'observed_at_utc':data['observed_at_utc'],'cases':len(cases),'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest(),'uncompressed_bytes':len(raw),'uncompressed_sha256':hashlib.sha256(raw).hexdigest()}))
            """;
}
