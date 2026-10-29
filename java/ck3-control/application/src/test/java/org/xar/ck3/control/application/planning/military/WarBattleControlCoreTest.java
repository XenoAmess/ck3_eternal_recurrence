package org.xar.ck3.control.application.planning.military;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

final class WarBattleControlCoreTest {
    @Test void pursuitResearchCandidateCannotReplaceProductionSentinelEvidence() {
        var frame=frame("pursuit","attacker",100,200,100,200);
        var research=BattleTerminalCruisePolicy.assess(frame,context(false,false,List.of(0)));
        assertTrue(research.candidateReady());assertTrue(research.researchRunReady());assertFalse(research.productionReady());
        assertEquals(new Text("pursuit_cleanup"),research.document().get("candidate_kind"));
        var live=BattleTerminalCruisePolicy.assess(frame,context(true,false,List.of(0)));
        assertTrue(live.productionReady());assertEquals(new Bool(false),live.document().get("overwhelming_matrix_required"));
    }
    @Test void doubleDominanceRequiresTheSeparateOverwhelmingLiveMatrix() {
        var frame=frame("main","none",800,100,800,100);
        var onlySentinel=BattleTerminalCruisePolicy.assess(frame,context(true,false,List.of(4)));
        assertTrue(onlySentinel.researchRunReady());assertFalse(onlySentinel.productionReady());
        assertEquals(strings(List.of("overwhelming_checkpoint_matrix_pending")),onlySentinel.document().get("production_blockers"));
        assertTrue(BattleTerminalCruisePolicy.assess(frame,context(true,true,List.of(4))).productionReady());
    }
    @Test void aMissingWatchOrDuplicatePublicUnitCannotGrantCruiseAdmission() {
        Obj frame=frame("pursuit","attacker",100,200,100,200);
        assertFalse(BattleTerminalCruisePolicy.assess(frame,context(true,true,List.of())).researchRunReady());
        assertFalse(BattleTerminalCruisePolicy.assess(frame,context(true,true,List.of(4,4))).researchRunReady());
        // Public CUnit zero is allowed by its actual shared producer, separately from private native Army IDs.
        assertTrue(BattleTerminalCruisePolicy.assess(frame,context(true,true,List.of(0))).productionReady());
    }
    @Test void wrongMetricTypesAreRejectedBeforeAnInternalAssessmentIsConstructed() {
        Obj frame=frame("main","none",800,100,800,100);
        Obj side=(Obj)frame.get("attacker");frame=put(frame,"attacker",put(side,"derived_current_fighting_raw",new Bool(true)));
        Obj malformed=frame;assertThrows(IllegalArgumentException.class,()->BattleTerminalCruisePolicy.assess(malformed,context(true,true,List.of(4))));
    }
    @Test void observedComparisonUsesSharedFixedMathAndDoesNotInventWinProbability() {
        Obj own=side(1000,100,100_000),enemy=side(1000,800,100_000);
        Obj frame=obj(f("phase",text("main")),f("winner_side",text("none")),f("finalized",new Bool(false)),f("side_index",number(0)),
                f("side_scope",text("full_side")),f("final_combat_width",number(100)),f("combat_id",number(88)),f("province_id",number(7)),
                f("subject_public_cunit_id",number(0)),f("attacker",own),f("defender",enemy));
        Obj result=ActiveCombatObservedComparison.compare(frame,Optional.empty()).orElseThrow();
        assertEquals(new Bool(true),result.get("severe_observed_disadvantage"));assertSame(Nil.INSTANCE,result.get("whole_battle_win_probability"));
        assertEquals(new Text("conditional_frozen_day"),((Obj)result.get("neutral_uncountered_damage_basis")).get("status"));
        assertEquals(new Text("current_frame_counter_unavailable"),result.get("current_frame_counter_basis_status"));
    }
    @Test void theFactoriesCoverExactlyTheTwoActualBoundaries() {
        ExactRef source=new ExactRef("D:/fixture/WarBattleControlCore.java",1,"a".repeat(64));
        var leaves=WarBattleControlCore.factories(source,(request,current)->new EarlyWarCoreInputs.Unavailable(List.of("actual source not available")));
        assertEquals(List.of(WarCorePlanner.Boundary.COMBAT_AND_RETREAT_PROGRESS,WarCorePlanner.Boundary.MERGE_RENDEZVOUS_BOUNDARY),leaves.stream().map(WarCorePlanner.Leaf::boundary).toList());
        assertTrue(leaves.stream().allMatch(leaf->leaf.implementationSource().equals(source)));
    }
    private static BattleTerminalCruisePolicy.Context context(boolean live,boolean overwhelming,List<Integer> ids) {
        return new BattleTerminalCruisePolicy.Context(true,true,false,false,ids,ids,Optional.of(BigInteger.valueOf(24048)),true,true,live,overwhelming,4);
    }
    private static Obj frame(String phase,String winner,long ownCurrent,long enemyCurrent,long ownStrength,long enemyStrength) {
        return obj(f("battle_control_ready",new Bool(true)),f("observed_date_raw",number(24000)),f("side_index",number(0)),f("phase",text(phase)),
                f("winner_side",text(winner)),f("finalized",new Bool(false)),f("attacker",obj(f("derived_current_fighting_raw",number(ownCurrent)),f("side_strength_raw",number(ownStrength)))),
                f("defender",obj(f("derived_current_fighting_raw",number(enemyCurrent)),f("side_strength_raw",number(enemyStrength)))));
    }
    private static Obj side(long starting,long current,long damage) {
        Obj entry=obj(f("fights_in_main_phase",new Bool(true)),f("starting_raw",number(starting)),f("current_fighting_raw",number(current)),f("effective_damage_raw",number(damage)));
        return obj(f("levy_entries",objects(List.of(entry))),f("men_at_arms_entries",objects(List.of())),f("ordered_armies",objects(List.of(empty()))),
                f("stored_current_matches_derived",new Bool(true)),f("stored_current_fighting_raw",number(current)));
    }
}
