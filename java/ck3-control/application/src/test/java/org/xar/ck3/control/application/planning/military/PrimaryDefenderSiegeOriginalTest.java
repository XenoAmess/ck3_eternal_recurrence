package org.xar.ck3.control.application.planning.military;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.military.combatwire.CombatPhaseInputsCodec;
import org.xar.ck3.control.wave2.military.combatwire.CombatRequest;
import org.xar.ck3.control.wave2.military.combatwire.CombatSimulationInputsCodec;
import org.xar.ck3.control.wave2.military.combatwire.phaseevent.StockPhaseEventRuntime;
import org.xar.ck3.control.wave2.military.forecast.CombatObservationCache;

/** Unchanged Python producers feed Java readers/model; historical .3 operands with a synthetic .4 wrapper grant no new native or game receipt. */
final class PrimaryDefenderSiegeOriginalTest {
    private static final String PREFIX="""
            import copy,hashlib,json,pathlib,runpy,sys
            repo=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(repo/'ck3_autonomous_player'/'src'));sys.path.insert(0,str(repo/'ck3_autonomous_player'/'tests'/'unit'))
            from ck3_autonomous_player.tests.unit import test_combat_provisional_defense_canary as m
            from xar_autoplayer import strategy
            t=m.ProvisionalDefenseCanaryTests();baseline={'phase':'native_war_no_safe_exact_route','selected_step':None}
            names=['ck3_autonomous_player/src/xar_autoplayer/strategy.py','ck3_autonomous_player/tests/unit/test_combat_provisional_defense_canary.py','ck3_autonomous_player/tests/unit/test_siege_relief_v2_constructor_consumer_12004.py','ck3_autonomous_player/tests/fixtures/combat/live_814_12003_general_battle_v2.json','docs/autonomous-agent-progress/coordination/war-requests/evidence/WAR-ROBERT-R0271-SIEGE-PARTITION-20260928.r0271-blocker-excerpt.json','ck3_autonomous_player/src/xar_autoplayer/combat_profile_research_v1.py']
            pins={n:hashlib.sha256((repo/n).read_bytes()).hexdigest() for n in names}
            """;
    private static final String ROUTES=PREFIX+"""
            frame=t._frame();date=frame['date_raw'];preview=m._preview_row(1,origin=30,target=32,date_raw=date,route=[32]);contact=m._route_contact_row(2,origin=30,target=32,date_raw=date,route=[32],hostile_ids=(21,),contact_free=False,hostile_provinces={21:32})
            steps=['preview-move-army-11-to-32','move-army-11-to-32',strategy.query_route_contact_horizon_step(11,32,(21,))]
            cases=[]
            for name,commands in [('route',[]),('contact',[preview]),('inputs',[preview,contact]),('failed_epoch',[preview,contact,{'index':3,'command':strategy.query_combat_simulation_inputs_v3_step(32,30,[11],[21]),'ok':False}])]:
                expected=strategy._primary_defender_siege_forecast_ingress(baseline,commands=commands,snapshot=frame,action_steps=set(steps),bridge_capabilities={m.QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY})
                cases.append({'name':name,'snapshot':copy.deepcopy(frame),'history':copy.deepcopy(commands),'steps':steps,'capabilities':[m.QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY],'expected':expected})
            frame,rows=t._r0271_replay_inputs();hop=rows[0]['result']['route_preview']['route_province_ids'][0]
            steps=[f'preview-move-army-83886367-to-{hop}',f'move-army-83886367-to-{hop}',strategy.query_route_contact_horizon_step(83886367,hop,(50331920,83886484))]
            for name in ['uncertain_preview','uncertain_contact','uncertain_move']:
                expected=strategy._primary_defender_siege_forecast_ingress(baseline,commands=rows,snapshot=frame,action_steps=set(steps),bridge_capabilities={m.QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY})
                cases.append({'name':name,'snapshot':copy.deepcopy(frame),'history':copy.deepcopy(rows),'steps':steps,'capabilities':[m.QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY],'expected':expected})
                if name=='uncertain_preview':rows.append(m._preview_row(4,army_id=83886367,origin=2610,target=hop,date_raw=frame['date_raw'],route=[hop]))
                elif name=='uncertain_contact':rows.append(m._route_contact_row(5,army_id=83886367,origin=2610,target=hop,date_raw=frame['date_raw'],route=[hop],hostile_ids=(50331920,83886484),contact_free=True,hostile_provinces={50331920:2629,83886484:3719}))
            partitions=[];war=frame['active_wars'][0];balance=strategy._primary_defender_siege_relief_assessment(frame,commands=rows,active_wars=frame['active_wars'],controlled_armies=frame['player_armies'],pursuit_army=frame['player_armies'][0])['army_strength_balance'];horizon=rows[1]['result']['route_contact_horizon']
            for name in ['original','zero_subject','boolean_friendly','duplicate_enemy','missing_enemies','offsite_not_targeting','no_offsite']:
                w,b,h=copy.deepcopy(war),copy.deepcopy(balance),copy.deepcopy(horizon);subject=83886367
                if name=='zero_subject':subject=0;b['friendly_army_ids']=[0];h['subject_army_id']=0;h['subject_route']['army_id']=0
                elif name=='boolean_friendly':b['friendly_army_ids']=[True]
                elif name=='duplicate_enemy':w['enemy_armies'].append(copy.deepcopy(w['enemy_armies'][0]))
                elif name=='missing_enemies':w.pop('enemy_armies')
                elif name=='offsite_not_targeting':h['hostile_routes'][1].update(route_province_ids=[],arrival_date_raws=[],effective_origin_province_id=h['hostile_routes'][1]['current_province_id'])
                elif name=='no_offsite':w['enemy_armies']=w['enemy_armies'][:1];b['enemy_army_ids']=[w['enemy_armies'][0]['army_id']]
                expected=strategy._siege_forecast_participant_partition(w,b,h,army_id=subject,target_province_id=2629)
                partitions.append({'name':name,'snapshot':frame,'history':[],'steps':[],'capabilities':[],'war':w,'balance':b,'contact':h,'subject':subject,'target':2629,'expected':expected})
            assert pins=={n:hashlib.sha256((repo/n).read_bytes()).hexdigest() for n in names}
            print(json.dumps({'pins':pins,'cases':cases,'partitions':partitions},separators=(',',':')))
            """;
    private static final String V2=PREFIX+"""
            path=repo/'ck3_autonomous_player/tests/unit/test_siege_relief_v2_constructor_consumer_12004.py';module=runpy.run_path(str(path));method=module['SiegeReliefV2ConstructorConsumer12004Test'].test_v2_only_query_then_production_relief_forecast_without_complete_mc
            actual=method.__globals__['_primary_defender_siege_forecast_ingress'];cases=[]
            def capture(baseline,**kwargs):
                expected=actual(baseline,**kwargs)
                cases.append({'name':'v2_case_'+str(len(cases)),'snapshot':copy.deepcopy(kwargs['snapshot']),'history':copy.deepcopy(kwargs['commands']),'steps':sorted(kwargs['action_steps']),'capabilities':sorted(kwargs['bridge_capabilities']),'expected':copy.deepcopy(expected)})
                return expected
            method.__globals__['_primary_defender_siege_forecast_ingress']=capture
            method(module['SiegeReliefV2ConstructorConsumer12004Test']())
            assert pins=={n:hashlib.sha256((repo/n).read_bytes()).hexdigest() for n in names}
            print(json.dumps({'pins':pins,'cases':cases},separators=(',',':')))
            """;
    @Test void originalRoutesParticipantUncertaintyAndFailedEpochReachTheActualWrapper() throws Exception {
        Obj corpus=OrdinaryMilitaryOriginalProducerTest.original(ROUTES);requirePins(corpus);assertEquals(7,rows(corpus.get("cases")).size());
        for(Obj row:rows(corpus.get("cases"))) {
            var request=GeneralBattleForecastIngressOriginalTest.request(row);var cache=cache();Obj expected=OpportunityJson.object(row.get("expected"),"original plan");
            assertEquals(expected,policy(cache).review(request,baseline()),optionalText(row.get("name")));
            var previous=new OrdinaryPolicy.Draft("one-life-turn-v1","native_war_no_safe_exact_route","original ordinary candidate",OrdinaryPolicy.Kind.ORDINARY,
                    Optional.empty(),OrdinaryPolicy.Purpose.READ_ONLY,Optional.empty(),baseline());
            var general=new GeneralBattleForecastPolicy(new ExactRef("synthetic-siege-original-test",1,"a".repeat(64)),cache,policy(cache),
                    ignored->{throw new AssertionError("siege read-only fixture cannot invoke active combat");},(actual,prior,decision)->{
                        Obj detail=decision instanceof MilitaryPlanningDecision.Select selected?selected.detail():((MilitaryPlanningDecision.Hold)decision).detail();
                        assertEquals(expected,detail,"the actual General stage and application adapter must consume the complete primary-siege result");
                        return new OrdinaryPolicy.Wait("actual primary siege adapter reached");
                    });
            assertInstanceOf(OrdinaryPolicy.Wait.class,general.evaluate(request,previous));
        }
    }
    @Test void originalV2ReadProducerFlowsThroughSharedCacheToReal512TrialDefensiveModel() throws Exception {
        Obj corpus=OrdinaryMilitaryOriginalProducerTest.original(V2);requirePins(corpus);assertEquals(3,rows(corpus.get("cases")).size());
        for(Obj row:rows(corpus.get("cases"))) {
            PlanningRequest request=GeneralBattleForecastIngressOriginalTest.request(row);var cache=cache();Obj snapshot=request.observations().snapshot();
            if(snapshot.get("combat_simulation_inputs") instanceof Obj payload) {
                Obj scenario=OpportunityJson.object(payload.get("scenario"),"actual scenario");
                var encounter=new CombatRequest(province(payload.get("target_province_id")),province(scenario.get("attacker_entry_province_id")),ids(scenario.get("attacker_army_ids")),ids(scenario.get("defender_army_ids")),null);
                Obj receipt=obj(f("step",text(encounter.toStep())),f("accepted",new Bool(true)),f("status",text("available")),f("query_sequence",number(1)),f("combat_simulation_inputs",payload),f("backend_id",text("synthetic-original-fixture")));
                cache.receive(CombatObservationCache.Version.V2,OpportunityJson.toNode(receipt),OpportunityJson.toNode(snapshot),OpportunityJson.toNode(snapshot),encounter,request.before().frame().revision());
            }
            Obj observed=policy(cache).review(request,baseline());Obj expected=OpportunityJson.object(row.get("expected"),"actual original result");
            assertEquals(expected.get("phase"),observed.get("phase"));assertEquals(expected.get("selected_step"),observed.get("selected_step"));assertEquals(expected.get("active_attack_allowed"),observed.get("active_attack_allowed"));
            if(expected.get("provisional_forecast") instanceof Obj sourceForecast) {
                Obj result=OpportunityJson.object(observed.get("provisional_forecast"),"actual shared forecast result");
                for(String key:List.of("status","sample_count","player_wins","player_losses","no_resolution","model_p90_hard_loss_raw","hard_loss_budget_raw","calibrated_win_probability_available"))assertEquals(sourceForecast.get(key),result.get(key),key);
                assertEquals(number(512),result.get("sample_count"));
            }
        }
    }
    @Test void originalPartitionKeepsPublicZeroAndRefusesDuplicateMissingOrWrongTypedRosters() throws Exception {
        Obj corpus=OrdinaryMilitaryOriginalProducerTest.original(ROUTES);requirePins(corpus);assertEquals(7,rows(corpus.get("partitions")).size());
        for(Obj row:rows(corpus.get("partitions"))) {
            PlanningRequest request=GeneralBattleForecastIngressOriginalTest.request(row);Obj contact=OpportunityJson.object(row.get("contact"),"original horizon");Obj subject=OpportunityJson.object(contact.get("subject_route"),"subject");
            var query=new MilitaryTimeline.Query(id(row.get("subject")),province(subject.get("current_province_id")),province(row.get("target")),ids(contact.get("hostile_army_ids")),ids(subject.get("route_province_ids")));
            var horizon=MilitaryTimeline.decode(contact,request,query);
            assertEquals(row.get("expected"),SiegeForecastParticipantPartition.partition(OpportunityJson.object(row.get("war"),"war"),OpportunityJson.object(row.get("balance"),"balance"),horizon,query.subjectId(),query.targetProvinceId()).toJson(),optionalText(row.get("name")));
        }
    }
    @Test void noCandidateNeverRequestsMovementOrBattleAndPreservesTheBaselineObject() {
        Obj empty=obj(f("snapshot",obj(f("snapshot_id",text("synthetic:1")),f("revision",number(1)),f("native_revision",number(1)),f("date_raw",number(100)),f("episode_run_id",text("synthetic-episode")),
                f("played_character",obj(f("character_id",number(1)),f("alive",new Bool(true)))),f("paused",new Bool(true)),f("active_wars",new Arr(List.of())),f("player_armies",new Arr(List.of())))),f("history",new Arr(List.of())),f("steps",new Arr(List.of())),f("capabilities",new Arr(List.of())));
        var request=GeneralBattleForecastIngressOriginalTest.request(empty);Obj baseline=baseline();assertSame(baseline,policy(cache()).review(request,baseline));
    }
    @Test void suppliedQualifiedPayloadMustMatchExactEncounterBeforeTheRealEuEvaluatorRuns() {
        Obj snapshot=obj(f("episode_run_id",text("episode")),f("snapshot_id",text("native:1")),f("revision",number(1)),f("native_revision",number(1)),f("combat_entry_eu_v1",obj(f("identity",empty()))));
        assertEquals(text("encounter_identity_mismatch"),SiegeForecastAssessments.qualified(snapshot,1,0,2,3,List.of(8),true).get("status"));
        assertEquals(text("producer_unavailable"),SiegeForecastAssessments.qualified(empty(),1,0,2,3,List.of(8),true).get("status"));
    }
    private static void requirePins(Obj corpus) {
        Obj pins=OpportunityJson.object(corpus.get("pins"),"original source pins");
        assertEquals(text("52b4381758ee712dc8555ac3a31186e13adbe10c3c18dc93b23bca5147934111"),pins.get("ck3_autonomous_player/src/xar_autoplayer/strategy.py"));
        assertEquals(text("201d30d463a1021d02a520fd89bda3d2ebcff06f868fa8e539e63b0c7cd1de08"),pins.get("ck3_autonomous_player/tests/unit/test_combat_provisional_defense_canary.py"));
        assertEquals(text("8abe53316c7cdd8c49fb9ac4baf0fefe9438253e10abf1ed561ddf48d4f9e13b"),pins.get("ck3_autonomous_player/tests/unit/test_siege_relief_v2_constructor_consumer_12004.py"));
        assertEquals(text("79c432b922b77707e3b73d766a4d65e2931680452207a04678f257efe7a70a23"),pins.get("ck3_autonomous_player/tests/fixtures/combat/live_814_12003_general_battle_v2.json"));
        assertEquals(text("bc34b3a8c041599992eac23ddd6a05399aaba367fa772edb7c63b4746290d30e"),pins.get("docs/autonomous-agent-progress/coordination/war-requests/evidence/WAR-ROBERT-R0271-SIEGE-PARTITION-20260928.r0271-blocker-excerpt.json"));
        assertEquals(text("5bb5a12640bcdacd6b50b9135f74e9226e52868bb6eb663ed77dbb77b9566f9f"),pins.get("ck3_autonomous_player/src/xar_autoplayer/combat_profile_research_v1.py"));
    }
    private static Obj baseline() {return obj(f("phase",text("native_war_no_safe_exact_route")),f("selected_step",Nil.INSTANCE));}
    private static CombatObservationCache cache() {var v2=new CombatSimulationInputsCodec();return new CombatObservationCache(v2,new CombatPhaseInputsCodec(v2,new StockPhaseEventRuntime()));}
    private static PrimaryDefenderSiegePolicy policy(CombatObservationCache cache) {
        WarStrengthRelief.MovementEvidence movement=new WarStrengthRelief.MovementEvidence() {
            @Override public WarStrengthRelief.EvidenceLookup activeIntent(PlanningRequest r,int army,int target){throw new AssertionError("idle source fixture cannot ask for active move evidence");}
            @Override public WarStrengthRelief.EvidenceLookup acceptedArrival(PlanningRequest r,int army,int target){throw new AssertionError("regular source fixture cannot claim accepted siege arrival");}
            @Override public WarStrengthRelief.EvidenceLookup observedErrorArrival(PlanningRequest r,int army,int target){throw new AssertionError("regular source fixture cannot claim error arrival");}
        };
        return new PrimaryDefenderSiegePolicy(cache,movement,r->{throw new AssertionError("idle source fixture cannot query active battle");});
    }
}
