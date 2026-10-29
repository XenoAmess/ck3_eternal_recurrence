package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.service.root.RootRuntimePublicCatalog;

/** Public protocol regression; software callbacks do not confer a private Root or action capability. */
final class RootMcpPlanningBindingTest {
    private static final ExactRef SOURCE = new ExactRef("software-public-planning-source", 1, "b".repeat(64));
    @Test void completeSourceResultAndArbitraryCallerStepReachTheOriginalTypedFacadesOnce() throws Exception {
        var plans = new AtomicInteger(); var steps = new AtomicInteger();
        var seen = new AtomicReference<PublicPlanningCodec.ExecuteRequest>();
        RawJson output = PublicPlanningCodecTest.raw("{\"original_software_result\":{\"present\":null,\"rows\":[]}}");
        var adapter = new RootMcpPlanning(new RootMcpPlanning.Backend() {
            public RootMcpPlanning.Admission admission() { return new RootMcpPlanning.Admission(true, true, List.of()); }
            public RawJson plan(PublicPlanningCodec.PlanRequest request) { plans.incrementAndGet(); return output; }
            public RawJson execute(PublicPlanningCodec.ExecuteRequest request) { steps.incrementAndGet(); seen.set(request); return output; }
        });
        var registry = new PublicBindings();
        assertEquals(2, adapter.register(registry, SOURCE).size());
        registry.freeze(Set.of(PublicMethod.PLAN_TURN, PublicMethod.EXECUTE_STEP));
        assertEquals(output, registry.lookup(PublicMethod.PLAN_TURN).orElseThrow().invoke(new PublicBindings.Missing()));
        var execute = registry.lookup(PublicMethod.EXECUTE_STEP).orElseThrow();
        assertEquals(output, execute.invoke(PublicPlanningCodecTest.args("{\"step\":\"query-domain-owned-step-v7\",\"expected_revision\":null}")));
        assertEquals("query-domain-owned-step-v7", seen.get().step().value());
        assertInstanceOf(PublicPlanningCodec.RevisionNull.class, seen.get().expectedRevision());
        assertInstanceOf(PublicPlanningCodec.FrameMissing.class, seen.get().expectedH2743Frame());
        assertThrows(IllegalArgumentException.class, () -> execute.invoke(PublicPlanningCodecTest.args("{\"step\":\"pause-map\",\"revision\":1}")));
        assertThrows(IllegalArgumentException.class, () -> execute.invoke(PublicPlanningCodecTest.args("{\"step\":\"pause-map\",\"expected_revision\":true}")));
        assertEquals(1, plans.get()); assertEquals(1, steps.get());
    }
    @Test void h2743ReachesItsTypedOriginalBeforeFrameReadConsumerWithoutAnOrdinaryOperationAlias() throws Exception {
        var seen = new AtomicReference<PublicPlanningCodec.ExecuteRequest>();
        var result = PublicPlanningCodecTest.raw("{\"h2743_original_read\":{\"status\":\"software-data-only\"}}");
        var registry = new PublicBindings();
        new RootMcpPlanning(new RootMcpPlanning.Backend() {
            public RootMcpPlanning.Admission admission() { return new RootMcpPlanning.Admission(false, true, List.of()); }
            public RawJson plan(PublicPlanningCodec.PlanRequest request) { throw new AssertionError(); }
            public RawJson execute(PublicPlanningCodec.ExecuteRequest request) { seen.set(request); return result; }
        }).register(registry, SOURCE);
        registry.freeze(Set.of(PublicMethod.EXECUTE_STEP));
        assertEquals(result, registry.lookup(PublicMethod.EXECUTE_STEP).orElseThrow()
                .invoke(PublicPlanningCodecTest.args(PublicPlanningCodecTest.special("1"))));
        assertTrue(seen.get().h2743());
        assertInstanceOf(PublicPlanningCodec.FrameValue.class, seen.get().expectedH2743Frame());
    }
    @Test void missingActualProductsAreCatalogGapsWithZeroExecutableStub() {
        var gap = new RootRuntimePublicCatalog.DefinitionGap("ck3_plan_turn", "actual complete public producer is missing");
        var adapter = new RootMcpPlanning(new RootMcpPlanning.Backend() {
            public RootMcpPlanning.Admission admission() { return new RootMcpPlanning.Admission(false, false, List.of(gap)); }
            public RawJson plan(PublicPlanningCodec.PlanRequest request) { throw new AssertionError(); }
            public RawJson execute(PublicPlanningCodec.ExecuteRequest request) { throw new AssertionError(); }
        });
        var registry = new PublicBindings();
        assertTrue(adapter.register(registry, SOURCE).isEmpty());
        assertTrue(registry.lookup(PublicMethod.PLAN_TURN).isEmpty());
        assertTrue(registry.lookup(PublicMethod.EXECUTE_STEP).isEmpty());
        assertEquals(List.of(gap), adapter.admission().gaps());
    }
}
