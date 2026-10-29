package org.xar.ck3.control.application.planning.military;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

final class WarHistoryStepsTest {
    private static Obj fixture() throws Exception {
        String repository=System.getProperty("xar.repository.root");
        assertNotNull(repository,"full CI must supply the original producer repository; missing environment is a failure");
        return OpportunityJson.object(OpportunityJson.parse(Files.readAllBytes(Path.of(repository,
                "ck3_autonomous_player/tests/fixtures/portable_observed_move_fixture.json"))),"actual portable P44 receipt");
    }
    private static List<Obj> history(Obj f,Obj evidence) {
        return List.of((Obj)f.get("original_failed_move_row"),obj(f("command",text("reconcile-observed-move-intent")),f("ok",new Bool(false)),f("result",evidence)));
    }
    @Test void actualFailedNativeMoveRemainsUnknownWhileIndependentRouteSurvivesSdkRebind() throws Exception {
        Obj f=fixture(),s=(Obj)f.get("snapshot_457"),e=(Obj)f.get("observed_intent_evidence");
        Obj proof=WarHistorySteps.activeNativeMoveIntent(history(f,e),s,167772577,2621).orElseThrow();
        assertEquals(new Bool(false),proof.get("native_ack_verified"));
        assertEquals(new Text("active"),proof.get("status"));
        Obj rebound=((Obj)f.get("snapshot_462")).with("revision",number(2)).with("native_revision",number(6287)).with("snapshot_id",text("native:6287"));
        assertFalse(WarHistorySteps.activeNativeMoveIntent(history(f,e),rebound,167772577,2621).isEmpty());
        for(String field:List.of("native_ack_verified","accepted"))
            assertTrue(WarHistorySteps.activeNativeMoveIntent(history(f,e.with(field,new Bool(true))),s,167772577,2621).isEmpty());
        assertTrue(WarHistorySteps.activeNativeMoveIntent(history(f,e.with("new_move_submissions",number(1))),s,167772577,2621).isEmpty());
        assertTrue(WarHistorySteps.activeNativeMoveIntent(history(f,e),s.with("paused",new Bool(false)),167772577,2621).isEmpty());
    }
    @Test void typedDateFamiliesRejectNoncanonicalRosterOverflowAndUnknownSuffixes() {
        for(String valid:List.of("life-advance-one-day","battle-decision-epoch-advance-to-9223372036854775807",
                "committed-route-sentinel-advance-army-0-to-2-until-24-speed-5",
                "war-objective-hold-sentinel-advance-war-1-army-0-at-2-until-24",
                "advance-route-contact-window-v1-0-to-2-days-3-h-2-1-3"))assertTrue(WarHistorySteps.isLifeAdvance(valid),valid);
        for(String invalid:List.of("battle-decision-epoch-advance-to-9223372036854775808",
                "committed-route-sentinel-advance-army-0-to-2-until-24-speed-3",
                "advance-route-contact-window-v1-0-to-2-days-3-h-2-1-1",
                "advance-route-contact-window-v1-0-to-2-days-4-h-1-1"))assertFalse(WarHistorySteps.isLifeAdvance(invalid),invalid);
        assertTrue(WarHistorySteps.parseMove("move-army-0-to-02").isEmpty());
    }

    @Test void canonicalClassifierUsesTheActualSourceFamilyClosure() throws Exception {
        var steps=List.of("life-advance","life-advance-one-day","battle-terminal-cruise",
                "battle-decision-epoch-advance-to-9223372036854775807",
                "committed-route-sentinel-advance-army-0-to-2-until-24-speed-5",
                "war-objective-hold-sentinel-advance-war-1-army-0-at-2-until-24",
                "advance-route-contact-horizon-v1-0-to-2-h-2-1-3",
                "advance-route-contact-window-v1-0-to-2-days-3-h-2-1-3",
                "query-route-contact-horizon-v1-0-to-2-h-2-1-3",
                "life-advance-one-day-extra","battle-decision-epoch-advance-to-9223372036854775808",
                "committed-route-sentinel-advance-army-0-to-2-until-24-speed-3");
        var request=obj(f("operation",text("classify")),f("steps",new Arr(steps.stream().<Value>map(Text::new).toList())));
        var expected=new Arr(steps.stream().<Value>map(value -> new Bool(WarHistorySteps.isLifeAdvance(value))).toList());
        assertEquals(expected,OriginalWarTacticsOracle.call(request));
        assertFalse(WarHistorySteps.isLifeAdvance("advance-route-contact-horizon-v1-0-to-02-h-1-1"),
                "the already shared route consumer requires canonical tokens, including target and roster count");
    }
    @Test void sharedDailySelectorsPreserveIndependentMissingFactsAndZeroUnitAndSiege() {
        Obj siege=obj(f("siege_id",number(0)),f("player_army_besieging",new Bool(true)));
        Obj state=obj(f("province_id",number(2)),f("active_siege",siege));
        Obj army=obj(f("army_id",number(0)));
        Obj war=obj(f("war_id",number(1)),f("player_armies",new Arr(List.of(army))),f("objective_province_states",new Arr(List.of(state))));
        Obj result=obj(f("war_progress_before",obj(f("date_raw",new Bool(true)),f("wars",new Arr(List.of(war))))));
        var slice=WarHistorySteps.progressSlice(java.util.Optional.of(result),WarHistorySteps.ProgressPhase.BEFORE,1);
        assertTrue(slice.dateRaw().isEmpty()); assertEquals(war,slice.war().orElseThrow());
        assertEquals(army,WarHistorySteps.progressArmy(slice.war(),WarHistorySteps.ArmyRole.PLAYER,0).orElseThrow());
        assertEquals(siege,WarHistorySteps.progressActiveSiege(WarHistorySteps.progressObjective(slice.war(),2),0).orElseThrow());
        assertTrue(WarHistorySteps.progressSlice(java.util.Optional.of(result),WarHistorySteps.ProgressPhase.AFTER,1).war().isEmpty());
        assertThrows(IllegalArgumentException.class,()->WarHistorySteps.progressActiveSiege(java.util.Optional.of(state),-1));
    }
    @Test void sharedSelectorsNeverTreatBooleanOrDecimalIdsAsEqualIntegerIdentity() {
        Obj war=obj(f("war_id",new Bool(true)),f("player_armies",new Arr(List.of(obj(f("army_id",new Bool(false)))))));
        Obj result=obj(f("war_progress_before",obj(f("date_raw",number(24)),f("wars",new Arr(List.of(war))))));
        assertTrue(WarHistorySteps.progressSlice(java.util.Optional.of(result),WarHistorySteps.ProgressPhase.BEFORE,1).war().isEmpty());
        assertTrue(WarHistorySteps.progressArmy(java.util.Optional.of(war),WarHistorySteps.ArmyRole.PLAYER,0).isEmpty());
        Obj decimal=OpportunityJson.object(OpportunityJson.parse("{\"army_id\":0.0}".getBytes(java.nio.charset.StandardCharsets.UTF_8)),"bad ID");
        assertTrue(WarHistorySteps.progressArmy(java.util.Optional.of(obj(f("player_armies",new Arr(List.of(decimal))))),WarHistorySteps.ArmyRole.PLAYER,0).isEmpty());
    }
}
