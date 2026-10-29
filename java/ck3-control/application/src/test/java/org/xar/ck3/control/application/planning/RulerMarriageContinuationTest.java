package org.xar.ck3.control.application.planning;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.military.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.PlanningFixtures.*;

final class RulerMarriageContinuationTest {
    @Test void identicalActualPendingChoiceCannotFallThroughIntoLegacyMarriageOrWarEntry() {
        var request = request(snapshot(), List.of(new OpportunityJson.Obj(Map.of(
                "command", new OpportunityJson.Text("save-checkpoint"), "ok", new OpportunityJson.Bool(true)))),
                Set.of(new OperationKey("life-advance")));
        var selected = new OrdinaryPolicy.Draft("one-life-turn-v1", "native_arrange_marriage_response_wait",
                "actual original marriage outcome remains UNKNOWN", OrdinaryPolicy.Kind.ORDINARY,
                java.util.Optional.of(command(request, new OperationKey("life-advance"), new OpportunityJson.Obj(Map.of()))),
                OrdinaryPolicy.Purpose.WORLD_ACTION, java.util.Optional.empty(), new OpportunityJson.Obj(Map.of()));
        var entered = new AtomicInteger();
        var finalSelection = new OrdinaryPolicy.Replace(selected, "the same pending choice remains selected");
        var core = core((actual, previous) -> { assertEquals(selected, previous); return finalSelection; }, entered);
        assertSame(finalSelection, core.evaluate(request, selected));
        assertEquals(0, entered.get(), "explicit pending selection must not reach legacy or war-entry producers");

        var noAction = core((actual, previous) -> new OrdinaryPolicy.Annotate(previous, "only current family evidence retained"), entered);
        assertInstanceOf(OrdinaryPolicy.Wait.class, noAction.evaluate(request, selected));
        assertEquals(1, entered.get(), "explicit non-action annotation still permits the actual next producer");
    }

    private static OrdinaryCorePolicy core(OrdinaryCorePolicy.CoreProducer family, AtomicInteger entered) {
        var leaves = new ArrayList<WarCorePlanner.Leaf>();
        for (var boundary : List.of(WarCorePlanner.Boundary.TERMINATION_SCORE_PRELUDE,
                WarCorePlanner.Boundary.PENDING_WAR_INTERACTION_PRELUDE, WarCorePlanner.Boundary.BATTLE_CONTROL_PRELUDE))
            leaves.add(new WarCorePlanner.Leaf(boundary, SOURCE,
                    (request, previous) -> new MilitaryPlanningDecision.Keep(new OpportunityJson.Obj(Map.of()))));
        PlanningReadPort reads = new PlanningReadPort() {
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
                throw new AssertionError("no native query in this actual family continuation boundary");
            }
        };
        var war = new WarCorePlanner(leaves, request -> { throw new AssertionError("no active war"); },
                (request, choice) -> { throw new AssertionError("no military submission"); }, reads,
                (request, choice) -> { throw new AssertionError("no read selection"); },
                (request, previous) -> { throw new AssertionError("no battle continuation"); });
        OrdinaryCorePolicy.CoreProducer keep = (request, previous) -> new OrdinaryPolicy.Keep("actual producer retained the choice");
        return new OrdinaryCorePolicy(SOURCE, war, keep, keep, family,
                (request, previous) -> { entered.incrementAndGet(); return new OrdinaryPolicy.Wait("actual next producer reached"); },
                (request, operation, arguments, plan, purpose, domain) -> { throw new AssertionError("legacy mutation must not be constructed"); },
                operation -> operation.equals("life-advance"));
    }
}
