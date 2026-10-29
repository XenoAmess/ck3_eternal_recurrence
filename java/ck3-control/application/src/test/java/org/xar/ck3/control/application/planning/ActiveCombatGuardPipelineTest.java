package org.xar.ck3.control.application.planning;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.PlanningFixtures.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.time.Clock;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.application.planning.military.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.capabilities.army.BattleOriginalOracle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual unchanged Python producers -> Java concrete guard -> complete typed pipeline/reducer/wire. No Game authority. */
final class ActiveCombatGuardPipelineTest {
    private static final String ORACLE="""
            import copy,json,sys
            from pathlib import Path
            root=Path(sys.argv[1])
            sys.dont_write_bytecode=True
            sys.path[:0]=[str(root/'ck3_autonomous_player/src'),str(root/'ck3_autonomous_player/tests/unit'),str(root/'ck3_autonomous_player/tests')]
            from xar_autoplayer import strategy
            from xar_autoplayer.formal_defender_exit_observation import observe_primary_defender_de_jure_exit
            from test_battle_control_snapshot_v1_bridge import _battle_frame,_planner_battle_snapshot,_active_resume_receipt,_rebind_battle_frame
            from test_h3937_date_hold import _h3937_snapshot
            from test_formal_defender_exit_observation import _h2743_snapshot_with_current_options
            rows=[]
            def add(name,snapshot,step):
                s=copy.deepcopy(snapshot)
                s.setdefault('snapshot_id','guard-fixture-native:1');s.setdefault('revision',1);s.setdefault('native_revision',1)
                s.setdefault('episode_run_id','guard-fixture-episode');s.setdefault('map_ready',True);s.setdefault('active_wars',[]);s.setdefault('player_armies',[])
                s.setdefault('diagnostics',{'connection_generation':1,'bridge_pid':123});s.setdefault('active_event',None);s.setdefault('pending_character_interaction',None)
                s['played_character'].setdefault('alive',True)
                plan={'policy':'guard-original-v1','phase':'before_guard','reason':'retain actual frozen choice','selected_step':step}
                expected=strategy._annotate_active_combat_resume_input(copy.deepcopy(plan),s)
                expected=strategy._h3937_hold_selected_control(expected,s)
                defender=observe_primary_defender_de_jure_exit(s)
                if defender is not None:
                    if defender.get('status')=='native_legality_observed_material_comparison_open':
                        candidate=expected.get('selected_step')
                        if isinstance(candidate,str) and candidate.startswith(('surrender-war-','offer-white-peace-')):candidate=None
                        defender={**defender,'continuation_handoff':{'status':'existing_tactical_candidate_requires_revalidation' if isinstance(candidate,str) else 'no_tactical_candidate','candidate_selected_step':candidate,'current_frame_revalidation_required':True,'exit_action_authorized':False}}
                    expected={**expected,'formal_defender_exit_observation':defender}
                annotation=expected.get('active_combat_resume_input')
                if annotation:
                    for subject in annotation['subjects']:
                        if subject['battle_control_query_sequence'] is not None:subject['battle_control_query_sequence']=str(subject['battle_control_query_sequence'])
                rows.append({'name':name,'snapshot':s,'plan':plan,'expected':expected})
            frame=_battle_frame();s=_planner_battle_snapshot(frame=frame)
            s['battle_control_snapshot_v1_queried_native_revision']=s['native_revision'];s['active_combat_resume_inputs_v1']=_active_resume_receipt(frame)
            add('original_valid_current_resume',s,'pause-map')
            wide=copy.deepcopy(s);wide['battle_control_snapshot_v1_query_sequence']=18446744073709551615;add('uint64_sequence_remains_exact_decimal',wide,'pause-map')
            bad=copy.deepcopy(s);bad['active_combat_resume_inputs_v1']['source']['combat_id']=True;add('wrong_boolean_combat_id',bad,'pause-map')
            missing=copy.deepcopy(s);missing.pop('active_combat_resume_inputs_v1');add('missing_resume_is_unavailable',missing,'pause-map')
            stale=copy.deepcopy(s);stale['battle_control_snapshot_v1_queried_native_revision']+=1;add('stale_query_retains_choice',stale,'pause-map')
            zero=_rebind_battle_frame(frame,subject=0,native_subject=frame['subject_native_carmy_id'],combat_id=frame['combat_id'],province_id=frame['province_id'])
            z=_planner_battle_snapshot(frame=zero);z['player_armies'][0]['army_id']=0;z['battle_control_snapshot_v1_subject_army_id']=0;z['battle_control_snapshot_v1_queried_native_revision']=z['native_revision'];z['active_combat_resume_inputs_v1']=_active_resume_receipt(zero);add('public_cunit_zero',z,'pause-map')
            add('historical_date_hold',_h3937_snapshot(),'life-advance-one-day')
            add('historical_move_hold',_h3937_snapshot(),'move-army-83886367-to-2614')
            ordinary=_h3937_snapshot();ordinary['succession_lifecycle']={'lifecycle':'ordinary_campaign_succession'};ordinary['campaign_goal']={'format_version':1,'goal_key':'dynasty_continuity','campaign_id':ordinary['episode_run_id'],'current_character_id':ordinary['played_character']['character_id']};add('ordinary_campaign_releases_old_research_hold',ordinary,'life-advance-one-day')
            add('actual_current_defender_options_remain_observations',_h2743_snapshot_with_current_options(),'pause-map')
            print(json.dumps({'cases':rows},ensure_ascii=False,allow_nan=False))
            """;
    @Test void unchangedOriginalProducersTraverseTheRealGuardWholePipelineReducerAndSerialization()throws Exception {
        JsonNode rows=BattleOriginalOracle.call(ORACLE,StrictJson.object()).get("cases");assertEquals(10,rows.size());
        var concrete=new ActiveCombatGuardProducers();var guard=new ActiveCombatDateGuards(SOURCE,concrete,concrete);
        for(JsonNode row:rows) {
            Obj snapshot=object(OpportunityJson.parse(StrictJson.canonical(row.get("snapshot"))),"original snapshot");
            Obj plan=object(OpportunityJson.parse(StrictJson.canonical(row.get("plan"))),"original plan");
            PlanningRequest request=current(snapshot,text(plan.get("selected_step"),"selected_step"));
            ActionCommand original=command(request,new OperationKey(text(plan.get("selected_step"),"selected_step")),new Obj(Map.of()));
            var draft=new OrdinaryPolicy.Draft("guard-original-v1","before_guard","retain actual frozen choice",OrdinaryPolicy.Kind.ORDINARY,
                    Optional.of(original),ActiveCombatDateGuards.dateControl(original.operation().value())?OrdinaryPolicy.Purpose.DATE_ADVANCE:OrdinaryPolicy.Purpose.WORLD_ACTION,Optional.empty(),plan);
            PlanningResult result=pipeline(guard,draft).create(Clock.fixed(NOW,ZoneOffset.UTC)).plan(request);
            var finalDraft=result.trace().finalPlan().orElseThrow();
            assertEquals(row.get("expected"),OpportunityJson.toNode(finalDraft.detail()),row.get("name").textValue());
            boolean held=row.get("expected").get("selected_step").isNull();
            if(held) {
                assertInstanceOf(PlanningResult.ReadOnlyWait.class,result);assertTrue(finalDraft.command().isEmpty());
                assertEquals(OrdinaryPolicy.Purpose.READ_ONLY,finalDraft.purpose());
                assertEquals(PlanTrace.Outcome.REPLACED,result.trace().visits().stream().filter(v->v.stage()==PlanningStage.ACTIVE_COMBAT_AND_DATE_GUARDS).findFirst().orElseThrow().outcome());
            } else {assertEquals(original,assertInstanceOf(PlanningResult.ActionSelected.class,result).command());}
            assertEquals(33,result.trace().visits().size());
            assertEquals(result,PlanningWire.decodeResult(PlanningWire.encodeResult(result)));
        }
    }
    private static PlanningRequest current(Obj snapshot,String selected) {
        Obj played=object(snapshot.get("played_character"),"played");
        var before=new ObservationIdentity("fixture-machine-1",GAME,new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(
                integer(played.get("character_id"),"actor"),integer(snapshot.get("native_revision"),"native"),integer(snapshot.get("date_raw"),"date")),
                text(snapshot.get("snapshot_id"),"snapshot"),integer(snapshot.get("revision"),"revision"),text(snapshot.get("episode_run_id"),"episode")),1);
        return new PlanningRequest(before,new G2Source(before.machineId(),NOW.toString(),"fixture-build",SOURCE),"session-1",NOW.plusSeconds(60),
                new PlanningObservation(snapshot,List.of(),Set.of(new OperationKey(selected)),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
    }
    private static OrdinaryPlanningPipeline pipeline(ActiveCombatDateGuards guard,OrdinaryPolicy.Draft selected) {
        var policies=new EnumMap<PlanningStage,OrdinaryPolicy>(PlanningStage.class);
        for(var stage:PlanningStage.values())policies.put(stage,new OrdinaryPolicy(){
            @Override public PlanningStage stage(){return stage;}
            @Override public ExactRef implementationSource(){return SOURCE;}
            @Override public Decision evaluate(PlanningRequest request,Draft previous){return new Keep("explicit unrelated fixture stage retains original work");}
        });
        policies.put(PlanningStage.ACTIVE_COMBAT_AND_DATE_GUARDS,guard);
        var core=OrdinaryCorePolicy.assemble(SOURCE,continuation->{
            var leaves=new ArrayList<WarCorePlanner.Leaf>();for(var boundary:WarCorePlanner.Boundary.values())
                leaves.add(new WarCorePlanner.Leaf(boundary,SOURCE,(request,previous)->new MilitaryPlanningDecision.Keep(new Obj(Map.of()))));
            PlanningReadPort noReads=new PlanningReadPort(){@Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){throw new AssertionError("guard regression must not issue a fresh native read");}};
            return new WarCorePlanner(leaves,request->new WarCorePlanner.KnownTactics(request.before(),new WarCorePlanner.RouteTactics(Set.of(),Set.of())),
                    (request,choice)->{throw new AssertionError("no world submission");},noReads,(request,choice)->{throw new AssertionError("no fresh observation");},continuation);
        },(request,previous)->new OrdinaryPolicy.Replace(selected,"actual frozen source selection"),
                (request,previous)->new OrdinaryPolicy.Keep("fixture council"),(request,previous)->new OrdinaryPolicy.Keep("fixture marriage"),
                (request,previous)->new OrdinaryPolicy.Keep("fixture entry"),
                (request,operation,args,plan,purpose,domain)->{throw new AssertionError("original command must survive without reconstruction");},step->step.startsWith("life-advance"));
        var realm=new RealmLifecycle(SOURCE);
        return new OrdinaryPlanningPipeline(policies.get(PlanningStage.SUCCESSION_PREFLIGHT),policies.get(PlanningStage.PENDING_MATERIAL_PUBLICATION),
                policies.get(PlanningStage.TERMINAL_AND_FOREGROUND_WINDOWS),policies.get(PlanningStage.OPENING_LIFESTYLE_FOCUS),core.core(),
                policies.get(PlanningStage.THREE_WAY_WAR_EXIT),policies.get(PlanningStage.EVENT_AND_INTERACTION_CONTINUATION),policies.get(PlanningStage.WAR_RENDEZVOUS),
                policies.get(PlanningStage.SIEGE_AND_BATTLE_FORECAST),policies.get(PlanningStage.ROUTE_ORIGIN_EXPOSURE),guard,policies.get(PlanningStage.ORDINARY_RETREAT),
                policies.get(PlanningStage.WAR_MERCENARY_CURRENT_CASH),policies.get(PlanningStage.PRISONER_RELEASE_DISCOVERY),policies.get(PlanningStage.HOLY_ORDER_REINFORCEMENT),
                policies.get(PlanningStage.COMMANDER_QUALITY),policies.get(PlanningStage.M5_JOINT_PEACETIME),policies.get(PlanningStage.LIFESTYLE),policies.get(PlanningStage.FACTION_GIFT),
                policies.get(PlanningStage.CONSTRUCTION),policies.get(PlanningStage.FAMILY_AND_EDUCATION),policies.get(PlanningStage.PRISONER_RANSOM),policies.get(PlanningStage.PRISONER_RELEASE),
                policies.get(PlanningStage.M5_WARTIME_OBSERVATION),policies.get(PlanningStage.COUNCIL),policies.get(PlanningStage.CROWN_AUTHORITY),policies.get(PlanningStage.FEAST),
                policies.get(PlanningStage.DEFERRED_SUCCESSION_ROOT),policies.get(PlanningStage.HOLY_WAR_DEFENDER_OBSERVATION),policies.get(PlanningStage.PREWAR_FORCE_COALITION),
                policies.get(PlanningStage.ORDINARY_SWAY),policies.get(PlanningStage.EVENT_MATERIAL_POSTCONDITION),policies.get(PlanningStage.CAMPAIGN_ADVANCE_CAP),realm);
    }
}
