package org.xar.ck3.control.application.planning;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.PlanningFixtures.*;
import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.military.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

final class EarlyWarCoreProductionTest {
    @Test void completeFactoryUsesEveryActualEarlyProducerExactlyOnce() {
        var sources=new EarlyWarCoreLeaves.Sources(SOURCE,SOURCE,SOURCE);
        var actual=EarlyWarCoreLeaves.completeFactories(sources,SOURCE,new EarlyWarCoreInputs());
        assertEquals(9,actual.size());
        assertEquals(java.util.EnumSet.range(WarCorePlanner.Boundary.DEFAULT_RAISE_AND_PRIMARY_IDENTITY,WarCorePlanner.Boundary.OBJECTIVE_SOURCE_SELECTION),
                actual.stream().map(WarCorePlanner.Leaf::boundary).collect(java.util.stream.Collectors.toSet()));
    }
    @Test void publicUnitZeroFlowsThroughActualFactoriesAndCannotTriggerAnotherDefaultRaise() {
        var input=current(base(war(List.of()),List.of(army(0,20,"regular"))),List.of(),Set.of(new OperationKey("raise-troops-default")));
        assertInstanceOf(MilitaryPlanningDecision.Keep.class,EarlyWarCoreLeaves.defaultRaise(input,OrdinaryPolicy.Draft.empty()));
        var actual=assertInstanceOf(EarlyWarCoreInputs.Available.class,new EarlyWarCoreInputs().capture(input,OrdinaryPolicy.Draft.empty())).state();
        assertEquals(0,actual.subject().id());assertEquals(List.of(21,20),actual.objectives().rankedExactObjectives());
        var late=assertInstanceOf(LateWarCoreInputs.Available.class,new EarlyWarCoreInputs().collect(input,OrdinaryPolicy.Draft.empty()));
        assertEquals(0,late.context().subject().id());assertEquals(input.before(),late.context().published().before());
    }
    @Test void actualNoArmySelectsRaiseAndUnknownDefenderPrimaryIdentityHolds() {
        var empty=current(base(war(List.of()),List.of()),List.of(),Set.of(new OperationKey("raise-troops-default")));
        assertEquals("raise-troops-default",assertInstanceOf(MilitaryPlanningDecision.Select.class,EarlyWarCoreLeaves.defaultRaise(empty,OrdinaryPolicy.Draft.empty())).operation().value());
        Obj unknown=war(List.of()).with("player_side",text("defender")).with("player_is_primary_war_leader",Nil.INSTANCE);
        var request=current(base(unknown,List.of(army(0,20,"regular"))),List.of(),Set.of(new OperationKey("life-advance")));
        assertEquals("defensive_war_primary_identity_required",assertInstanceOf(MilitaryPlanningDecision.Hold.class,EarlyWarCoreLeaves.defaultRaise(request,OrdinaryPolicy.Draft.empty())).phase());
    }
    @Test void incompleteActualRouteCannotBeHiddenByDownstreamContextOrLatePublication() {
        Obj moving=army(0,20,"moving").with("army_state_code",number(7)).with("move_target_province_id",number(40))
                .with("route_read_status",text("target_only")).with("route_source_count",number(2))
                .with("move_target_observable",new Bool(true)).with("route_province_ids",numbers(List.of()));
        var request=current(base(war(List.of()),List.of(moving)),List.of(),Set.of(new OperationKey("life-advance")));
        var inputs=new EarlyWarCoreInputs();
        assertEquals("native_war_route_evidence_blocked",assertInstanceOf(MilitaryPlanningDecision.Hold.class,inputs.contactPolicy().ingress(request,OrdinaryPolicy.Draft.empty())).phase());
        assertInstanceOf(EarlyWarCoreInputs.Unavailable.class,inputs.capture(request,OrdinaryPolicy.Draft.empty()));
        assertInstanceOf(LateWarCoreInputs.Unavailable.class,inputs.collect(request,OrdinaryPolicy.Draft.empty()));
    }
    @Test void missingStrengthUsesActualReadonlyQueryAndNeverInventsEqualForce() {
        Obj enemy=army(7,40,"regular").with("controllable",new Bool(false));
        var request=current(base(war(List.of(enemy)),List.of(army(0,20,"regular"))),List.of(),Set.of(new OperationKey("query-army-strengths")));
        var selected=assertInstanceOf(MilitaryPlanningDecision.Select.class,EarlyWarCoreLeaves.strength(request,OrdinaryPolicy.Draft.empty(),new EarlyWarCoreInputs()));
        assertEquals("query-army-strengths",selected.operation().value());assertEquals(OrdinaryPolicy.Purpose.READ_ONLY,selected.purpose());
        assertEquals(numbers(List.of(7)),((Obj)selected.detail().get("army_strength_scope")).get("enemy_army_ids"));
    }
    @Test void exactOneDayHistoryInvalidatesOldUnknownQueryButMalformedMoveIsNotABarrier() {
        var query=new MilitaryTimeline.Query(0,20,40,List.of(7),List.of(40));
        Obj failed=obj(f("command",text(query.step())),f("ok",new Bool(false)),f("error",text("provider unavailable without retained lease")));
        Obj advance=obj(f("command",text("life-advance-one-day")),f("ok",new Bool(true)),f("result",empty()));
        var snapshot=base(war(List.of()),List.of(army(0,20,"regular")));
        assertTrue(MilitaryTimeline.failure(current(snapshot,List.of(failed),Set.of()),query).isPresent());
        assertTrue(MilitaryTimeline.failure(current(snapshot,List.of(failed,advance),Set.of()),query).isEmpty());
        Obj malformed=obj(f("command",text("move-army-0-to-40-junk")),f("ok",new Bool(false)));
        assertTrue(MilitaryTimeline.failure(current(snapshot,List.of(failed,malformed),Set.of()),query).isPresent());
    }
    @Test void realHistoryCompletionIsOverriddenByCurrentExactOccupation() {
        Obj beforeArmy=army(0,20,"sieging"),afterArmy=army(0,20,"regular");
        Obj before=war(List.of()).with("player_armies",objects(List.of(beforeArmy))).with("player_relative_war_score",number(0));
        Obj after=war(List.of()).with("player_armies",objects(List.of(afterArmy))).with("player_relative_war_score",number(1));
        Obj beforeProgress=obj(f("date_raw",number(23976)),f("wars",objects(List.of(before))));
        Obj afterProgress=obj(f("date_raw",number(24000)),f("wars",objects(List.of(after))));
        Obj progress=obj(f("command",text("life-advance")),f("ok",new Bool(true)),
                f("result",obj(f("war_progress_before",beforeProgress),f("war_progress_after",afterProgress))));
        Obj actualWar=war(List.of()).with("objective_province_states",objects(List.of(state(20,2,1000,false),state(21,1,2000,true))));
        var request=current(base(actualWar,List.of(afterArmy)),List.of(progress),Set.of());
        var actual=assertInstanceOf(EarlyWarCoreInputs.Available.class,new EarlyWarCoreInputs().capture(request,OrdinaryPolicy.Draft.empty())).state();
        assertEquals(numbers(List.of(20)),actual.tactical().get("completed_objective_province_ids"));
        assertEquals(Set.of(21),actual.objectives().completedObjectives());assertEquals(List.of(20),actual.siegeObjectives());
        assertFalse(actual.objectives().allSiegeObjectivesCompleted());
    }
    @Test void realDefeatHistoryBlocksRemainInTheActualLatePublication() {
        Obj player=army(0,20,"regular"),enemy=army(7,20,"regular").with("controllable",new Bool(false));
        Obj before=war(List.of(enemy)).with("player_armies",objects(List.of(player))).with("player_relative_war_score",number(0));
        Obj after=before.with("player_relative_war_score",number(-30));
        Obj beforeProgress=obj(f("date_raw",number(23976)),f("wars",objects(List.of(before))));
        Obj afterProgress=obj(f("date_raw",number(24000)),f("wars",objects(List.of(after))));
        Obj row=obj(f("command",text("life-advance")),f("ok",new Bool(true)),
                f("result",obj(f("war_progress_before",beforeProgress),f("war_progress_after",afterProgress))));
        var request=current(base(after,List.of(player)),List.of(row),Set.of());
        var inputs=new EarlyWarCoreInputs();
        var actual=assertInstanceOf(EarlyWarCoreInputs.Available.class,inputs.capture(request,OrdinaryPolicy.Draft.empty())).state();
        assertEquals(numbers(List.of(7)),actual.tactical().get("blocked_enemy_ids"));
        assertEquals(Set.of(20),actual.objectives().blockedProvinces());
        var late=assertInstanceOf(LateWarCoreInputs.Available.class,inputs.collect(request,OrdinaryPolicy.Draft.empty()));
        assertTrue(late.context().published().blockedProvinces().contains(20));
        assertFalse(late.context().published().stationaryThreats().isEmpty());
    }
    @Test void incompleteReliefQueriesReservesOnceAndCurrentUnknownReplyCannotRepeatTheRead() {
        Obj enemy=army(7,40,"sieging").with("controllable",new Bool(false)).with("siege_province_in_player_subrealm",new Bool(true)).with("siege_province_holder_character_id",number(1));
        Obj other=army(9,50,"regular").with("controllable",new Bool(false));
        Obj defender=war(List.of(enemy,other)).with("player_side",text("defender")).with("war_objective_province_ids",numbers(List.of(40)));
        Obj snapshot=base(defender,List.of(army(0,20,"regular"))).with("army_strengths_status",text("partial"))
                .with("army_strengths_queried_snapshot_id",text("snapshot-1")).with("army_strengths_queried_revision",number(1))
                .with("army_strengths",objects(List.of(strength(0,"player",1000),strength(7,"active_war_enemy",2000))));
        Set<OperationKey> steps=Set.of(new OperationKey("query-player-default-raise-v1"),new OperationKey("raise-troops-default"));
        var first=current(snapshot,List.of(),steps);
        var selected=assertInstanceOf(MilitaryPlanningDecision.Select.class,EarlyWarCoreLeaves.strength(first,OrdinaryPolicy.Draft.empty(),new EarlyWarCoreInputs()));
        assertEquals("query-player-default-raise-v1",selected.operation().value());assertEquals(OrdinaryPolicy.Purpose.READ_ONLY,selected.purpose());
        Obj failureResult=obj(
                f("queried_episode_run_id",text("episode-1")),f("queried_connection_generation",number(1)),f("queried_bridge_pid",number(123)),
                f("player_default_raise",obj(f("actor_character_id",number(29829)),f("date_raw",number(24000)))));
        Obj failure=obj(f("command",text("query-player-default-raise-v1")),f("ok",new Bool(false)),f("result",failureResult));
        var retried=current(snapshot,List.of(failure),steps);
        assertEquals("native_war_defender_siege_relief_observation_blocked",assertInstanceOf(MilitaryPlanningDecision.Hold.class,
                EarlyWarCoreLeaves.strength(retried,OrdinaryPolicy.Draft.empty(),new EarlyWarCoreInputs())).phase());
    }
    private static PlanningRequest current(Obj snapshot,List<Obj> history,Set<OperationKey> steps) {
        var fixture=request(snapshot,history,steps);
        return new PlanningRequest(fixture.before(),new G2Source(fixture.before().machineId(),NOW.toString(),"1.20.0.4",SOURCE),fixture.sessionId(),fixture.deadline(),fixture.observations());
    }
    private static Obj base(Obj war,List<Obj> armies) {
        Obj result=snapshot().with("active_wars",objects(List.of(war))).with("player_armies",objects(armies))
                .with("active_event",Nil.INSTANCE).with("pending_character_interaction",Nil.INSTANCE)
                .with("war_termination_options",objects(List.of())).with("war_termination_terms",objects(List.of())).with("war_termination_exit_terms",objects(List.of()));
        for(String flag:List.of("army_routes_supported","move_route_preview_supported","route_contact_horizon_supported","war_objective_garrison_supported",
                "war_objective_siege_progress_supported","war_objective_assault_supported","war_objective_occupation_supported","war_objective_fort_level_supported"))result=result.with(flag,new Bool(true));
        return result;
    }
    private static Obj war(List<Obj> enemies) {return obj(f("war_id",number(1)),f("player_side",text("attacker")),f("player_is_primary_war_leader",new Bool(true)),
            f("player_relative_war_score",number(0)),f("war_objective_province_ids",numbers(List.of(20,21))),f("enemy_primary_default_raise_province_id",number(30)),
            f("allied_armies",objects(List.of())),f("enemy_armies",objects(enemies)),f("objective_province_states",objects(List.of(state(20,2,1000,false),state(21,1,2000,false)))));}
    private static Obj state(int province,int fort,int garrison,boolean occupied) {return obj(f("province_id",number(province)),f("fort_level",number(fort)),f("garrison_size",number(garrison)),
            f("siege_observable",new Bool(true)),f("active_siege",Nil.INSTANCE),f("occupation_observable",new Bool(true)),f("is_occupied",new Bool(occupied)),
            f("occupying_character_id",occupied?number(29829):Nil.INSTANCE));}
    private static Obj army(int id,int province,String state) {return obj(f("army_id",number(id)),f("source",text("native")),f("owner_character_id",number(29829)),f("soldiers",number(1000)),
            f("current_province_id",number(province)),f("army_state",text(state)),f("army_state_code",number(state.equals("sieging")?3:0)),f("in_combat",new Bool(false)),f("retreating",new Bool(false)),
            f("controllable",new Bool(true)),f("move_target_observable",new Bool(false)),f("move_target_province_id",Nil.INSTANCE),f("route_read_status",text("complete_empty")),f("route_source_count",number(0)),f("route_province_ids",numbers(List.of())));}
    private static Obj strength(int id,String role,int soldiers) {return obj(f("army_id",number(id)),f("status",text("available")),f("scope_role",text(role)),f("war_ids",numbers(List.of(1))),
            f("current_soldiers",number(soldiers)),f("maximum_soldiers",number(soldiers)),f("ai_base_power_raw",number(soldiers)));}
}

