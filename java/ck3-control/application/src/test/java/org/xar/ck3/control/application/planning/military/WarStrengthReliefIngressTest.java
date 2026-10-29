package org.xar.ck3.control.application.planning.military;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Actual source-bound relief ingress must retain the complete semantic frame. */
final class WarStrengthReliefIngressTest {
    private static final String PROGRAM="""
            import hashlib,json,pathlib,runpy,sys
            repo=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(repo/'ck3_autonomous_player'/'src'))
            path=repo/'ck3_autonomous_player/tests/unit/test_general_battle_first_hop_before_endpoint_12004.py';pin=hashlib.sha256(path.read_bytes()).hexdigest();m=runpy.run_path(str(path));s=m['_snapshot']()
            s['active_wars'][0].update(player_side='defender',player_is_primary_war_leader=True,player_relative_war_score=-20,war_objective_province_ids=[31])
            assert hashlib.sha256(path.read_bytes()).hexdigest()==pin
            print(json.dumps({'snapshot':s,'history':[],'steps':[],'capabilities':[]},separators=(',',':')))
            """;
    private static final WarStrengthRelief.MovementEvidence NO_MOVEMENT=new WarStrengthRelief.MovementEvidence(){
        @Override public WarStrengthRelief.EvidenceLookup activeIntent(PlanningRequest r,int army,int target){throw new AssertionError("these input-reader cases cannot consume a movement intent");}
        @Override public WarStrengthRelief.EvidenceLookup acceptedArrival(PlanningRequest r,int army,int target){throw new AssertionError("these input-reader cases cannot consume an arrival");}
        @Override public WarStrengthRelief.EvidenceLookup observedErrorArrival(PlanningRequest r,int army,int target){throw new AssertionError("these input-reader cases cannot turn failed ACK into arrival");}
    };
    @Test void completeSnapshotAboveOld128KiBBoundaryReachesTheActualSharedRelevanceConsumer() throws Exception {
        Obj row=OrdinaryMilitaryOriginalProducerTest.original(PROGRAM);PlanningRequest small=GeneralBattleForecastIngressOriginalTest.request(row);
        var emptyFacts=new WarStrengthRelief.ContactFacts(small.before(),List.of(),Optional.empty(),Optional.empty());
        Obj expected=WarStrengthRelief.assess(small,emptyFacts,NO_MOVEMENT,r->{throw new AssertionError("no selected current Army");});
        assertEquals(new Text("not_applicable"),expected.get("status"));
        Obj snapshot=OpportunityJson.object(row.get("snapshot"),"source snapshot").with("complete_other_semantic_domains",text("x".repeat(200000))).with("opaque_original_fraction",new DecimalValue("1.0"));
        PlanningRequest large=GeneralBattleForecastIngressOriginalTest.request(row.with("snapshot",snapshot));
        assertTrue(org.xar.ck3.control.application.driver.DriverJson.encode(large.observations().snapshot()).length>131072);
        assertEquals(expected,WarStrengthRelief.assess(large,new WarStrengthRelief.ContactFacts(large.before(),List.of(),Optional.empty(),Optional.empty()),NO_MOVEMENT,r->{throw new AssertionError("no selected current Army");}));
        Obj wrongWar=rows(snapshot.get("active_wars")).getFirst().with("war_id",new DecimalValue("1.0"));
        PlanningRequest wrong=GeneralBattleForecastIngressOriginalTest.request(row.with("snapshot",snapshot.with("active_wars",objects(List.of(wrongWar)))));
        assertThrows(IllegalArgumentException.class,()->WarStrengthRelief.assess(wrong,new WarStrengthRelief.ContactFacts(wrong.before(),List.of(),Optional.empty(),Optional.empty()),NO_MOVEMENT,r->Optional.empty()));
    }
    @Test void selectedCurrentBattleBindingRetainsTheFullSignedCombatIdAndRefusesMissingSentinel() throws Exception {
        Obj row=OrdinaryMilitaryOriginalProducerTest.original(PROGRAM),snapshot=OpportunityJson.object(row.get("snapshot"),"snapshot");
        Obj own=rows(snapshot.get("player_armies")).getFirst().with("army_state",text("combat")).with("in_combat",new Bool(true)).with("retreating",new Bool(false)).with("controllable",new Bool(true));
        PlanningRequest request=GeneralBattleForecastIngressOriginalTest.request(row.with("snapshot",snapshot.with("player_armies",objects(List.of(own)))));Army army=army(own);
        var facts=new WarStrengthRelief.ContactFacts(request.before(),List.of(army),Optional.of(army),Optional.empty());
        for(int combat:List.of(Integer.MIN_VALUE,-2,0,Integer.MAX_VALUE)) {
            Obj control=obj(f("status",text("available")),f("battle_control_ready",new Bool(true)),f("subject_public_cunit_id",number(army.id())),f("province_id",number(army.current())),f("observed_date_raw",number(request.before().frame().identity().dateRaw())),f("combat_id",number(combat)));
            Obj result=WarStrengthRelief.assess(request,facts,NO_MOVEMENT,r->Optional.of(obj(f("status",text("ready")),f("full_frames",objects(List.of(control))))));
            assertEquals(new Text("active_combat"),result.get("status"));assertEquals(number(combat),result.get("combat_id"));
        }
        Obj missing=obj(f("status",text("available")),f("battle_control_ready",new Bool(true)),f("subject_public_cunit_id",number(army.id())),f("province_id",number(army.current())),f("observed_date_raw",number(request.before().frame().identity().dateRaw())),f("combat_id",number(-1)));
        assertEquals(new Text("observation_unavailable"),WarStrengthRelief.assess(request,facts,NO_MOVEMENT,r->Optional.of(obj(f("status",text("ready")),f("full_frames",objects(List.of(missing)))))).get("status"));
    }
}
