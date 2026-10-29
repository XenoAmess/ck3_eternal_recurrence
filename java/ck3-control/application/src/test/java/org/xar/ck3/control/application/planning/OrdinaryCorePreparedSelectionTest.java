package org.xar.ck3.control.application.planning;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.military.MilitaryPlanningDecision;
import org.xar.ck3.control.application.planning.military.MilitaryPlanningDecision.PreparedSelection;
import org.xar.ck3.control.application.planning.military.WarCorePlanner;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryPlannerSelection;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.PlanningFixtures.*;

/** Real ordinary-core chooser to the single Army mapper and strict prepared consumer; fixture data grants no native authority. */
final class OrdinaryCorePreparedSelectionTest {
    private static final OperationKey DISBAND = new OperationKey("disband-army-7");

    @Test void postwarChooserKeepsItsOriginalPlanWhileAcceptingTheOwnerArmyEnvelope() {
        var request = actualChoice();
        var core = core((input, operation, arguments, plan, purpose, domain) -> {
            var selected = selected(operation, arguments, plan, purpose);
            var actual = armyCommand(input, selected);
            return new OrdinaryCorePolicy.OwnerPrepared(
                    PreparedSelection.army(actual.actionId(), input, selected, actual));
        });
        var replacement = assertInstanceOf(OrdinaryPolicy.Replace.class,
                core.evaluate(request, OrdinaryPolicy.Draft.empty()));
        var actual = replacement.draft().command().orElseThrow();
        assertEquals(DISBAND, actual.operation());
        assertEquals(new Text("native_postwar_disband"), replacement.draft().detail().get("phase"));
        var wrapped = ArmyOrdinaryActionArguments.decode(actual.arguments());
        var publicSelection = ArmyOrdinaryPlannerSelection.decode(DISBAND,
                new Obj(Map.of("army_id", integer(7))), request.before().frame().revision());
        assertEquals(publicSelection.publicArguments(), wrapped.publicArguments());
        assertFalse(actual.arguments().members().containsKey("plan"));
    }

    @Test void theExactLegacyCoreBranchStillRejectsAnEnrichedEnvelope() {
        var request = actualChoice();
        var core = core((input, operation, arguments, plan, purpose, domain) ->
                new OrdinaryCorePolicy.Prepared(armyCommand(input, selected(operation, arguments, plan, purpose))));
        assertThrows(IllegalArgumentException.class, () -> core.evaluate(request, OrdinaryPolicy.Draft.empty()));
    }

    @Test void aPreparedOwnerCannotReplaceTheOriginalFullPlanWithAnAddedField() {
        var request = actualChoice();
        var core = core((input, operation, arguments, plan, purpose, domain) -> {
            var changed = selected(operation, arguments, plan.with("unowned", new Text("changed")), purpose);
            var actual = armyCommand(input, changed);
            return new OrdinaryCorePolicy.OwnerPrepared(
                    PreparedSelection.army(actual.actionId(), input, changed, actual));
        });
        assertThrows(IllegalArgumentException.class, () -> core.evaluate(request, OrdinaryPolicy.Draft.empty()));
    }

    private static ActionCommand armyCommand(PlanningRequest request, MilitaryPlanningDecision.Select selected) {
        var mapped = ArmyOrdinaryPlannerSelection.decode(selected.operation(), selected.arguments(),
                request.before().frame().revision());
        var wrapped = new ArmyOrdinaryActionArguments(mapped.kind(), mapped.publicArguments(), List.of());
        return command(request, selected.operation(), wrapped.encode());
    }

    private static MilitaryPlanningDecision.Select selected(OperationKey operation, Obj arguments, Obj plan,
            OrdinaryPolicy.Purpose purpose) {
        return new MilitaryPlanningDecision.Select(OpportunityJson.text(plan.get("policy"), "policy"),
                OpportunityJson.text(plan.get("phase"), "phase"), OpportunityJson.text(plan.get("reason"), "reason"),
                operation, arguments, purpose, plan);
    }

    private static PlanningRequest actualChoice() {
        var army = new Obj(Map.of("army_id", integer(7), "controllable", new Bool(true),
                "soldiers", new IntegerValue(BigInteger.valueOf(1000))));
        return request(snapshot().with("player_armies", new Arr(List.of(army))), List.of(), Set.of(DISBAND));
    }

    private static OrdinaryCorePolicy core(OrdinaryCorePolicy.CommandBinding binding) {
        return OrdinaryCorePolicy.assemble(SOURCE, continuation -> {
            var leaves = new ArrayList<WarCorePlanner.Leaf>();
            for (var boundary : WarCorePlanner.Boundary.values())
                leaves.add(new WarCorePlanner.Leaf(boundary, SOURCE,
                        (request, previous) -> new MilitaryPlanningDecision.Keep(new Obj(Map.of()))));
            PlanningReadPort reads = new PlanningReadPort() {
                @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
                    throw new AssertionError("this chooser regression performs no native read");
                }
            };
            return new WarCorePlanner(leaves,
                    request -> new WarCorePlanner.KnownTactics(request.before(), new WarCorePlanner.RouteTactics(Set.of(), Set.of())),
                    (request, selected) -> { throw new AssertionError("the postwar core owns this selection"); },
                    reads, (request, selected) -> { throw new AssertionError("no native read selected"); }, continuation);
        }, (request, previous) -> new OrdinaryPolicy.Keep("DATA event source checked"),
                (request, previous) -> new OrdinaryPolicy.Keep("DATA council source checked"),
                (request, previous) -> new OrdinaryPolicy.Keep("DATA marriage source checked"),
                (request, previous) -> new OrdinaryPolicy.Keep("DATA entry source checked"),
                binding, step -> step.equals("life-advance")).core();
    }
}

