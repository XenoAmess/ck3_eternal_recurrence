package org.xar.ck3.control.application.planning;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.PlanningFixtures.*;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.planning.military.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Exercises the real factory/collector/leaf path and the original missing-rich-row failure. */
final class WarCoreActualPreludeTest {
    private static Obj json(String value){return OpportunityJson.object(OpportunityJson.parse(value.getBytes(StandardCharsets.UTF_8)),"fixture");}
    private static Obj war(){return json("{\"war_id\":88,\"player_side\":\"attacker\",\"player_is_primary_war_leader\":true,\"player_relative_war_score\":24,\"allied_armies\":[],\"objective_province_states\":[]}");}
    private static Obj start(boolean decorated){
        Obj action=json("{\"assault_action\":{\"status\":\"assault_started\",\"siege_id\":9,\"war_id\":88,\"province_id\":2585}}");
        return decorated?json("{\"index\":1,\"command\":\"auto-turn\",\"ok\":true,\"result\":{\"auto_turn\":{\"selected_step\":\"start-assault-9\"}}}")
                .with("result",json("{\"auto_turn\":{\"selected_step\":\"start-assault-9\"}}").with("assault_action",action.get("assault_action"))):
                json("{\"index\":1,\"command\":\"start-assault-9\",\"ok\":true}").with("result",action);
    }
    @Test void actualSummaryLeafLatchesDirectAndDecoratedStartWithoutRichObjectiveRow(){
        for(boolean decorated:List.of(false,true)){
            var request=request(snapshot().with("war_objective_assault_supported",new Bool(true)).with("active_wars",new Arr(List.of(war()))),List.of(start(decorated)),Set.of());
            var leaf=AssaultLifecycle.factory(SOURCE);assertEquals(WarCorePlanner.Boundary.WAR_SUMMARY_AND_ASSAULT_LIFECYCLE,leaf.boundary());
            var result=assertInstanceOf(MilitaryPlanningDecision.Hold.class,leaf.producer().evaluate(request,OrdinaryPolicy.Draft.empty()));
            assertEquals("native_war_assault_lifecycle_blocked",result.phase());assertTrue(result.detail().get("selected_step")==Nil.INSTANCE);
            Obj blocked=(Obj)((Arr)result.detail().get("assault_lifecycles")).items().getFirst();
            assertEquals(new Text("objective_row_unavailable_after_start"),blocked.get("reason"));
            Obj summary=(Obj)((Arr)result.detail().get("active_wars")).items().getFirst();assertTrue(summary.get("native_end_conditions") instanceof Obj);
        }
    }
    @Test void exactStopNullSiegeReplacementAndSuccessfulRestoreCloseOnlyTheirOwnLifecycle(){
        Obj noSiege=war().with("objective_province_states",new Arr(List.of(json("{\"province_id\":2585,\"siege_observable\":true,\"active_siege\":null}"))));
        Obj sem=snapshot().with("war_objective_assault_supported",new Bool(true)).with("active_wars",new Arr(List.of(noSiege)));
        assertTrue(AssaultLifecycle.pending(sem,List.of(noSiege),List.of(start(false))).isEmpty());
        Obj missingSiege=war().with("objective_province_states",new Arr(List.of(json("{\"province_id\":2585,\"siege_observable\":true}"))));
        assertEquals("active_siege_unavailable_after_start",AssaultLifecycle.pending(sem,List.of(missingSiege),List.of(start(false))).getFirst().reason());
        Obj replaced=war().with("objective_province_states",new Arr(List.of(json("{\"province_id\":2585,\"siege_observable\":true,\"active_siege\":{\"siege_id\":10}}"))));
        assertTrue(AssaultLifecycle.pending(sem,List.of(replaced),List.of(start(false))).isEmpty());
        Obj zeroGeneration=war().with("objective_province_states",new Arr(List.of(json("{\"province_id\":2585,\"siege_observable\":true,\"active_siege\":{\"siege_id\":0}}"))));
        assertTrue(AssaultLifecycle.pending(sem,List.of(zeroGeneration),List.of(start(false))).isEmpty());
        Obj impossibleZeroStart=start(false).with("command",new Text("start-assault-0")).with("result",json("{\"assault_action\":{\"status\":\"assault_started\",\"siege_id\":0,\"war_id\":88,\"province_id\":2585}}"));
        assertTrue(AssaultLifecycle.open(List.of(impossibleZeroStart)).isEmpty());
        Obj stop=json("{\"index\":2,\"command\":\"stop-assault-9\",\"ok\":true,\"result\":{\"assault_action\":{\"status\":\"assault_stopped\",\"siege_id\":9,\"war_id\":88,\"province_id\":2585}}}");
        assertTrue(AssaultLifecycle.open(List.of(start(false),stop)).isEmpty());
        Obj restored=json("{\"index\":2,\"command\":\"restore-checkpoint\",\"ok\":true,\"result\":{\"status\":\"restored\"}}");
        assertTrue(AssaultLifecycle.open(List.of(start(false),restored)).isEmpty());
        assertEquals(1,AssaultLifecycle.open(List.of(start(false),restored.with("ok",new Bool(false)))).size());
        assertEquals(1,AssaultLifecycle.open(List.of(start(false),stop.with("result",json("{\"assault_action\":{\"status\":\"submitted\",\"siege_id\":9,\"war_id\":88,\"province_id\":2585}}")))).size());
    }
    private static Obj occupation(){return json("{\"index\":2,\"command\":\"query-war-occupation-targets-v1-88\",\"ok\":true,\"result\":{\"queried_snapshot_id\":\"snapshot-1\",\"queried_revision\":1,\"queried_native_revision\":1,\"queried_connection_generation\":1,\"queried_episode_run_id\":\"episode-1\",\"war_occupation_targets_v1\":{\"available\":true,\"collection_complete\":true,\"war_id\":88,\"actor_character_id\":29829,\"player_side\":\"attacker\",\"snapshot_revision\":1,\"date_raw\":24000,\"rows\":[{\"province_id\":2585,\"siege_observable\":true,\"active_siege\":null,\"occupation_observable\":true,\"is_occupied\":true,\"occupying_character_id\":999,\"occupier_side\":\"attacker\"}]}}}");}
    @Test void originalOccupationHistoryFailureUsesFreshNativeParticipantSideAndRejectsStaleOrOpposingSide(){
        Obj objective=json("{\"province_id\":2585,\"siege_observable\":false,\"occupation_observable\":true,\"is_occupied\":true,\"occupying_character_id\":999}");
        Obj war=war().with("objective_province_states",new Arr(List.of(objective)));Obj sem=snapshot().with("active_wars",new Arr(List.of(war))).with("war_objective_assault_supported",new Bool(true));
        assertTrue(AssaultLifecycle.pending(sem,List.of(war),List.of(start(true),occupation())).isEmpty());
        Obj result=(Obj)occupation().get("result"),value=(Obj)result.get("war_occupation_targets_v1");
        Obj stale=occupation().with("result",result.with("war_occupation_targets_v1",value.with("date_raw",integer(23976))));
        assertEquals("siege_unobservable_after_start",AssaultLifecycle.pending(sem,List.of(war),List.of(start(true),stale)).getFirst().reason());
        Obj holding=(Obj)((Arr)value.get("rows")).items().getFirst();
        Obj opposed=occupation().with("result",result.with("war_occupation_targets_v1",value.with("rows",new Arr(List.of(holding.with("occupier_side",new Text("defender")))))));
        assertEquals("siege_unobservable_after_start",AssaultLifecycle.pending(sem,List.of(war),List.of(start(true),opposed)).getFirst().reason());
        Obj failedLatest=occupation().with("index",integer(3)).with("ok",new Bool(false));
        assertEquals("siege_unobservable_after_start",AssaultLifecycle.pending(sem,List.of(war),List.of(start(true),occupation(),failedLatest)).getFirst().reason());
    }
    @Test void endConditionsNeverConvertRawAcceptanceOrWrongTokenIntoRecipientAnswer(){
        Obj option=json("{\"outcome\":\"white_peace\",\"context_constructed\":true,\"native_validator_passed\":true,\"available\":true,\"ai_acceptance\":100,\"auto_accept\":false,\"recipient_response\":{\"status\":\"unavailable\",\"would_accept_now\":true}}");
        Obj options=json("{}").with("surrender",option).with("victory",option.with("available",new Bool(false))).with("white_peace",option);
        Obj conditions=NativeWarEndConditions.assess(war(),json("{}").with("options",options));
        assertEquals(new Text("current_white_peace_recipient_response"),conditions.get("required_native_input"));
        Obj white=(Obj)((Obj)conditions.get("native_options")).get("white_peace");assertEquals(Nil.INSTANCE,white.get("recipient_would_accept_now"));
        Obj typed=NativeWarEndConditions.assess(war().with("player_relative_war_score",new Bool(true)),json("{}").with("options",options.with("white_peace",option.with("available",integer(1)))));
        assertEquals(Nil.INSTANCE,typed.get("player_relative_war_score"));assertEquals(Nil.INSTANCE,typed.get("native_nonloss_exit_available"));
        assertEquals(typed,OpportunityJson.parse(OpportunityJson.encode(typed)));
    }
    @Test void noCombatPreludeUsesActualCollectorRatherThanInjectedStatus(){
        var result=BattleControlPrelude.factory(SOURCE).producer().evaluate(request(snapshot(),List.of(),Set.of()),OrdinaryPolicy.Draft.empty());
        var keep=assertInstanceOf(MilitaryPlanningDecision.Keep.class,result);
        Obj state=(Obj)keep.annotations().get("battle_control_state");assertEquals(new Text("not_in_combat"),state.get("status"));
    }
    @Test void actualNoSubjectResidualIsDistinctFromMissingCollectorAndRejectsCanonicalUnitBypass(){
        var request=request(snapshot().with("active_wars",new Arr(List.of(war()))),List.of(),Set.of(new org.xar.ck3.control.application.action.OperationKey("life-advance")));
        LateWarCoreInputs.Provider provider=(input,current)->new LateWarCoreInputs.NoPursuit(input.before(),List.of(),java.util.Optional.empty(),NativeWarEndConditions.summaries(input));
        var leaves=LateWarCoreLeaves.factories(SOURCE,SOURCE,provider);
        assertInstanceOf(MilitaryPlanningDecision.Keep.class,leaves.getFirst().producer().evaluate(request,OrdinaryPolicy.Draft.empty()));
        var fallback=assertInstanceOf(MilitaryPlanningDecision.Select.class,leaves.getLast().producer().evaluate(request,OrdinaryPolicy.Draft.empty()));
        assertEquals("native_war_reconnaissance",fallback.phase());
        var actualArmy=json("{\"army_id\":0,\"current_province_id\":48,\"controllable\":true}");
        var withSubject=request(request.observations().snapshot().with("player_armies",new Arr(List.of(actualArmy))),List.of(),Set.of());
        assertThrows(IllegalArgumentException.class,()->leaves.getLast().producer().evaluate(withSubject,OrdinaryPolicy.Draft.empty()));
    }
}
