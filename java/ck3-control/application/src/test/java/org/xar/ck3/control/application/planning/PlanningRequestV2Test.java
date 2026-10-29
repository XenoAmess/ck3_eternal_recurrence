package org.xar.ck3.control.application.planning;

import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.PlanningFixtures.*;

final class PlanningRequestV2Test {
    @Test void actualRequestProducerRejectsTheRemovedCandidateDependentGlobalCashContract() {
        var original = request(snapshot().with("explicit_null", OpportunityJson.Nil.INSTANCE), List.of(), Set.of());
        byte[] encoded = PlanningWire.encodeRequest(original);
        String raw = new String(encoded, StandardCharsets.UTF_8);
        assertTrue(raw.contains("xar.java-ordinary-plan-request/v2"));
        assertFalse(raw.contains("construction_cash"));
        assertEquals(original, PlanningWire.decodeRequest(encoded));
        assertThrows(IllegalArgumentException.class, () -> PlanningWire.decodeRequest(raw.replace(
                "xar.java-ordinary-plan-request/v2", "xar.java-ordinary-plan-request/v1").getBytes(StandardCharsets.UTF_8)));
        String obsolete = raw.replace("\"initial_lifestyle_focus_required\":false",
                "\"initial_lifestyle_focus_required\":false,\"construction_cash\":null");
        assertNotEquals(raw, obsolete);
        assertThrows(IllegalArgumentException.class, () -> PlanningWire.decodeRequest(obsolete.getBytes(StandardCharsets.UTF_8)));
    }

    @Test void actualFreshOptionalContinuationSkipsOnlySwayOnceAndStillRunsEveryOtherStage() {
        var operation = new OperationKey("save-checkpoint");
        var fresh = request(snapshot(), List.of(), Set.of(operation));
        var sway = new AtomicInteger(); var construction = new AtomicInteger();
        var policies = new ArrayList<OrdinaryPolicy>();
        var realm = new RealmLifecycle(SOURCE);
        for (PlanningStage stage : PlanningStage.values()) {
            if (stage == PlanningStage.REALM_MEMBERSHIP_PUBLICATION) { policies.add(realm); continue; }
            policies.add(new OrdinaryPolicy() {
                @Override public PlanningStage stage() { return stage; }
                @Override public ExactRef implementationSource() { return SOURCE; }
                @Override public Decision evaluate(PlanningRequest input, Draft previous) {
                    if (stage == PlanningStage.ORDINARY_SWAY) sway.incrementAndGet();
                    if (stage == PlanningStage.CONSTRUCTION) construction.incrementAndGet();
                    if (stage != PlanningStage.ORDINARY_CORE) return new Keep("actual existing choice retained");
                    return new Replace(new Draft("fixture", "baseline", "current real fixture command", Kind.ORDINARY,
                            Optional.of(command(input, operation, new OpportunityJson.Obj(Map.of()))), Purpose.WORLD_ACTION,
                            Optional.empty(), new OpportunityJson.Obj(Map.of())), "baseline selected");
                }
            });
        }
        var planner = new OrdinaryPlanner(policies, Clock.fixed(NOW, ZoneOffset.UTC), realm);
        var selected = assertInstanceOf(PlanningResult.ActionSelected.class,
                planner.planAfterOptional(fresh, PlanningStage.ORDINARY_SWAY));
        assertEquals(0, sway.get()); assertEquals(1, construction.get());
        assertEquals(PlanTrace.Outcome.NOT_APPLICABLE, selected.trace().visits().stream()
                .filter(visit -> visit.stage() == PlanningStage.ORDINARY_SWAY).findFirst().orElseThrow().outcome());
        assertEquals(fresh.before(), selected.command().before());
        planner.plan(fresh); assertEquals(1, sway.get()); assertEquals(2, construction.get());
        assertThrows(IllegalArgumentException.class, () -> planner.planAfterOptional(fresh, PlanningStage.CONSTRUCTION));
    }
}
