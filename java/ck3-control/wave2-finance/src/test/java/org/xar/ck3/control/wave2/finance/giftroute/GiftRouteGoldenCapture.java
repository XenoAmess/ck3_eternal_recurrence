package org.xar.ck3.control.wave2.finance.giftroute;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.List;
import org.xar.ck3.control.wave2.finance.capture.PythonStdinCapture;

/** Original full planning producer capture, run only by the centralized qualified Job owner. */
public final class GiftRouteGoldenCapture {
    private GiftRouteGoldenCapture() { }
    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 3) { throw new IllegalArgumentException("python repo new-gzip required"); }
        PythonStdinCapture.requireCompiledLauncher(GiftRouteGoldenCapture.class);
        Path output = Path.of(args[2]).toAbsolutePath();
        if (Files.exists(output)) { throw new IllegalArgumentException("new output path required"); }
        var result = PythonStdinCapture.run(new PythonStdinCapture.Invocation(Path.of(args[0]), Path.of(args[1]),
                SCRIPT, List.of(args[1], output.toString()), Duration.ofSeconds(90), 16_384));
        System.out.write(result.stdout()); System.out.flush();
        if (!Files.isRegularFile(output) || Files.size(output) == 0 || Files.size(output) > 48_000) {
            throw new IllegalStateException("bounded gzip artifact required");
        }
    }
    private static final String SCRIPT = """
            import sys,json,copy,gzip,hashlib,datetime,threading
            from pathlib import Path
            from types import SimpleNamespace
            from unittest.mock import patch
            repo=Path(sys.argv[1]);output=Path(sys.argv[2])
            sys.path.insert(0,str(repo/'ck3_autonomous_player/src'))
            sys.path.insert(0,str(repo/'ck3_autonomous_player/tests/unit'))
            from test_faction_gift_formal_candidate_v1 import snapshot,root,private_result,observation
            from xar_autoplayer.bridge import faction_gift_formal_route_v1 as route
            from xar_autoplayer.bridge.faction_gift_private_transport_v1 import query_faction_gift_private_candidate_v1
            from xar_autoplayer import faction_gift_pending_v1 as pending
            from xar_autoplayer import activity_feast_stage5_budget_v1 as budget
            from xar_autoplayer import war_mercenary_consumer_v1 as mercenary
            from xar_autoplayer.m5_observed_opportunity_selector import observed_frame
            clear=pending._empty()
            # Invoke the actual pending producer with only its file read/write boundary replaced in memory.
            memory={'value':copy.deepcopy(clear)}
            def store(path,value):memory['value']=copy.deepcopy(value)
            with patch.object(pending,'read_faction_gift_ledger_v1',side_effect=lambda path:copy.deepcopy(memory['value'])),patch.object(pending,'write_json_atomic',side_effect=store):
                seeded=pending.begin_faction_gift_submission_v1(output.parent/'giftroute-fixture-not-written',request_id='gift-route-1',episode_run_id='native-32904-a',source_round_id='R742',source_bridge_pid=12345,source_bridge_creation_date='20260916120000.000000+000',observation=observation(),minimum_gold_reserve_raw=10000000,checkpoint_sha256_before_submit='a'*64)
            def base():
                snap=snapshot();snap.update(episode_run_id='native-32904-a',played_character_gold={'raw':100000000,'scale':100000},active_wars=[{'war_id':9,'enemy_armies':[]}],diagnostics={'bridge_pid':12345,'connection_generation':1})
                campaign=root(1);campaign['player_max_monthly_gold_maintenance_v1']={'status':'available','value':{'raw':500000,'scale':100000}}
                private=private_result();private['native']['observation'].update(player_gold_raw=100000000,native_snapshot_revision=412)
                alert={'status':'available','snapshot_revision':412,'date_raw':snap['date_raw'],'player_character_id':32904,'readiness':{'targeting_rows_ready':True,'stock_dangerous_predicate_ready':True,'same_frame_ready':True},'targeting_factions':[{'faction_id':771,'target_character_id':32904,'leader_character_id':33011,'character_member_ids':[33011],'dangerous_by_stock_rule':True,'faction_at_war':False}]}
                history=[{'command':route.ROOT_STEP,'ok':True,'result':{'status':'available','campaign_root_context':campaign}},{'command':'query-player-faction-alerts-v1','ok':True,'result':{'player_faction_alerts':alert}}]
                market={'available':True,'actor_character_id':32904,'date_raw':snap['date_raw'],'rows':[{'company_id':9,'employer_id':None,'final_terms':{'resource_costs_raw':[30000000]+[0]*9,'resource_scale':100000,'available':True,'can_hire':True,'can_afford':True},'troop_strength':{'available':True,'current_soldiers':1800},'location':{'hire_auto_raise_province_id':2630,'hire_auto_raise_position_ready':True,'hire_auto_raise_attempted_in_active_war':True},'readiness_v1':{'hire_ready':True}}]}
                return {'input':{'schema':'xar.faction-gift-route-input.v1','planned':{'revision':412,'trace_tag':'preserve','plan':{'selected_step':'life-advance','phase':'native_war_no_safe_route_defensive_hold_progress','reason':'original war choice','unrelated':[1,None,[]]}},'snapshot':snap,'history':history,'available_steps':['life-advance','save-checkpoint',route.ROOT_STEP]},'managed':True,'candidate_reader':True,'ledger':copy.deepcopy(clear),'current_process':{'pid':12345,'creation_date':'20260916120000.000000+000'},'private_result':private,'private_diagnostics':{'last_heartbeat':{'g2_faction_gift_mitigation_async_glue_v1':{'private_build':True}}},'market':market,'market_source_frame':observed_frame(snap),'mercenary_ledger':{'pending':None},'checkpoint':None,'wait_enabled':True,'fresh_snapshot':None}
            cases=[]
            def add(name,change=None):
                s=base()
                if change is not None:change(s)
                class Driver:
                    def __init__(self):
                        self.state_dir=output.parent/'giftroute-fixture-not-written' if s['managed'] else None
                        self._session_bridge_pid=s['current_process']['pid'];self._driver_state_lock=threading.RLock();self._last_checkpoint=s['checkpoint']
                        self.queries=0;self.sent=[];self.snapshots=0;self.waits=0;self.checkpoint_reads=0
                        self.endpoint=SimpleNamespace(send=lambda command:self.sent.append(copy.deepcopy(command)))
                        self.state=SimpleNamespace(wait_for_command_result=self.wait)
                        if not s['candidate_reader']:self.query_faction_gift_private_candidate_v1=None
                        if not s['wait_enabled']:self._wait_for_snapshot=None
                    def take_internal_semantic_snapshot(self):self.snapshots+=1;return copy.deepcopy(s['input']['snapshot'])
                    def diagnostics(self):return copy.deepcopy(s['private_diagnostics'])
                    def wait(self,request_id,timeout):return {'type':'command_result','protocol_version':1,'request_id':request_id,'ok':True,'result':copy.deepcopy(s['private_result'])}
                    def query_faction_gift_private_candidate_v1(self,**kwargs):
                        self.queries+=1;result=query_faction_gift_private_candidate_v1(self,**kwargs)
                        s['observed_candidate']=copy.deepcopy(result)
                        return result
                    def _wait_for_snapshot(self,source,predicate,timeout_seconds):
                        self.waits+=1
                        fresh=copy.deepcopy(s['fresh_snapshot'] or source)
                        s['wait_predicate_ready']=predicate(fresh)
                        return fresh
                driver=Driver()
                real_checkpoint=route._current_checkpoint
                def checkpoint(*args):driver.checkpoint_reads+=1;return real_checkpoint(*args)
                with patch.object(route,'read_faction_gift_ledger_v1',side_effect=lambda path:copy.deepcopy(s['ledger'])),patch.object(route,'_process_identity',return_value={'creation_date':s['current_process']['creation_date']}),patch.object(route,'_current_checkpoint',side_effect=checkpoint),patch.object(budget,'read_construction_ledger',return_value={'pending':None}),patch.object(budget,'read_faction_gift_ledger_v1',side_effect=lambda path:copy.deepcopy(s['ledger'])),patch.object(budget,'read_family_marriage_ledger',return_value={'pending':None}),patch.object(budget,'read_child_matrilineal_ledger',return_value={'pending':None}),patch.object(mercenary,'_context_with_reference',side_effect=lambda history,snapshot:(copy.deepcopy(s['market']),{'source_frame':copy.deepcopy(s['market_source_frame'])})),patch.object(mercenary,'_ledger',side_effect=lambda path:copy.deepcopy(s['mercenary_ledger'])),patch('xar_autoplayer.bridge.faction_gift_private_transport_v1.uuid.uuid4',return_value=SimpleNamespace(hex='0'*32)):
                    try:
                        actual=route.plan_faction_gift_private_v1(driver,copy.deepcopy(s['input']['planned']),copy.deepcopy(s['input']['snapshot']),copy.deepcopy(s['input']['history']),set(s['input']['available_steps']))
                        expected={'kind':'return','planned':actual}
                    except route.FactionGiftPendingFrameReadyError as error:expected={'kind':'read_only_replan','proof':error.readonly_faction_pending_frame_v1}
                    except Exception as error:expected={'kind':'error','error_type':type(error).__name__,'message':str(error)}
                    # Capture real spending producer output as a typed-input fact, never a precomputed cash approval.
                    if 'observed_candidate' in s and s['observed_candidate'].get('status')=='selected':
                        snap=s['input']['snapshot'];f=observed_frame(snap)
                        campaign=next((r['result']['campaign_root_context'] for r in s['input']['history'] if r.get('command')==route.ROOT_STEP),None)
                        s['spending']=budget.observe_feast_start_budget_v1(snap,{'actor_character_id':f['played_character_id'],'snapshot_revision':f['native_revision'],'date_raw':f['date_raw'],'post_snapshot_id':f['snapshot_id'],'queried_revision':f['revision']},state_dir=output.parent/'giftroute-fixture-not-written',campaign_root=campaign)
                cases.append({'name':name,'scenario':s,'expected':expected,'effects':{'candidate_queries':driver.queries,'candidate_sends':len(driver.sent),'snapshot_reads':driver.snapshots,'bounded_waits':driver.waits,'checkpoint_reads':driver.checkpoint_reads}})
            add('needs_checkpoint')
            add('checkpoint_missing_capability',lambda s:s['input'].update(available_steps=['life-advance',route.ROOT_STEP]))
            def saved(s):s['checkpoint']={'status':'saved','sha256':'a'*64,'date_raw':s['input']['snapshot']['date_raw'],'episode_run_id':'native-32904-a','save_slot':'exact-pre-gift'}
            add('ready_typed_submit_plan',saved)
            add('checkpoint_wrong_episode',lambda s:(saved(s),s['checkpoint'].update(episode_run_id='different-episode')))
            add('inactive_plan',lambda s:s['input']['planned']['plan'].update(selected_step='event-option-1'))
            add('absent_plan',lambda s:s['input']['planned'].pop('plan'))
            add('missing_managed_directory',lambda s:s.update(managed=False))
            add('root_not_observed',lambda s:s['input'].update(history=[]))
            add('root_query_unavailable',lambda s:(s['input'].update(history=[]),s['input'].update(available_steps=[])))
            add('known_empty',lambda s:s['input']['history'][0]['result']['campaign_root_context'].update(player_targeting_faction_count=0))
            add('government_out_of_scope',lambda s:s['input']['history'][0]['result']['campaign_root_context'].update(government={'key':'clan_government'}))
            add('candidate_reader_absent',lambda s:s.update(candidate_reader=False))
            add('private_route_off',lambda s:s.update(private_diagnostics={}))
            add('candidate_unavailable',lambda s:s['private_result']['native']['observation'].update(source_faction_discontent_raw=None))
            add('stock_not_dangerous',lambda s:s['input']['history'][1]['result']['player_faction_alerts']['targeting_factions'][0].update(dangerous_by_stock_rule=False))
            def wallet(s):s['input']['snapshot']['played_character_gold']['raw']=25000000;s['private_result']['native']['observation']['player_gold_raw']=25000000
            add('war_cash_floor_preserves_clock',wallet)
            add('query_native_frame_crossed_defer',lambda s:s['private_result']['native']['observation'].update(native_snapshot_revision=414))
            add('market_unknown_preserves_clock',lambda s:s.update(market=None))
            def with_pending(s):s['ledger']=copy.deepcopy(seeded)
            add('pending_receipt_precedes_cash',lambda s:(with_pending(s),s['input']['snapshot'].update(native_revision=415,revision=416),s['input']['planned'].update(revision=416)))
            add('pending_cold_process',lambda s:(with_pending(s),s['current_process'].update(pid=23456,creation_date='20260916120100.000000+000')))
            add('pending_unknown_birth',lambda s:(with_pending(s),s['current_process'].update(creation_date='unsupported-replaced-birth')))
            add('pending_equivalent_cim_birth',lambda s:(with_pending(s),s['current_process'].update(creation_date='2026-09-16T12:00:00.0000000Z'),s['input']['snapshot'].update(native_revision=415,revision=416),s['input']['planned'].update(revision=416)))
            def fresh(s):
                with_pending(s);s['fresh_snapshot']=copy.deepcopy(s['input']['snapshot']);s['fresh_snapshot'].update(native_revision=415,revision=413,snapshot_id='native:413')
            add('pending_fresh_frame_requires_whole_turn_replan',fresh)
            add('pending_wait_absent',lambda s:(with_pending(s),s.update(wait_enabled=False)))
            add('pending_wait_stale',with_pending)
            sources=['ck3_autonomous_player/src/xar_autoplayer/bridge/faction_gift_formal_route_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/faction_gift_private_transport_v1.py','ck3_autonomous_player/src/xar_autoplayer/faction_gift_formal_candidate_v1.py','ck3_autonomous_player/src/xar_autoplayer/faction_gift_policy_v1.py','ck3_autonomous_player/src/xar_autoplayer/faction_threat_response_inputs_v1.py','ck3_autonomous_player/src/xar_autoplayer/faction_gift_wartime_cash_v1.py','ck3_autonomous_player/src/xar_autoplayer/activity_feast_stage5_budget_v1.py','ck3_autonomous_player/src/xar_autoplayer/faction_gift_pending_v1.py','ck3_autonomous_player/src/xar_autoplayer/environment.py','ck3_autonomous_player/tests/unit/test_faction_gift_formal_candidate_v1.py']
            sources+=['ck3_autonomous_player/src/xar_autoplayer/bridge/driver.py','ck3_autonomous_player/src/xar_autoplayer/m5_observed_opportunity_selector.py','ck3_autonomous_player/src/xar_autoplayer/activity_feast_stage5_value_policy.py']
            result={'schema':'xar.faction-gift-route-original-producer-golden.v1','machine_id':'xenoamess-full-tower-eb9d2c1186','observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_bindings':[{'path':p,'sha256':hashlib.sha256((repo/p).read_bytes()).hexdigest()} for p in sources],'fixture_note':'Stock alert and market observations are explicit synthetic native-port facts. Real root/candidate/threat/spending/cash/process/wait/plan producers execute. Original begin producer writes only to an in-memory IO seam. No Game/native RPC/checkpoint/ledger write.','cases':cases}
            raw=json.dumps(result,sort_keys=True,separators=(',',':')).encode()
            if len(raw)>240000:raise ValueError('uncompressed golden budget')
            packed=gzip.compress(raw,mtime=0)
            if len(packed)>48000:raise ValueError('gzip golden budget')
            with output.open('xb') as target:target.write(packed)
            print(json.dumps({'cases':len(cases),'bytes':len(packed),'uncompressed_bytes':len(raw),'sha256':hashlib.sha256(packed).hexdigest()}))
            """;
}
