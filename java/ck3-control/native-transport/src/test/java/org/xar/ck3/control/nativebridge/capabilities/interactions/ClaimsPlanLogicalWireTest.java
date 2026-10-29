package org.xar.ck3.control.nativebridge.capabilities.interactions;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.nativebridge.NativeWire;

/** The installed Plan and arbitrary selector producers must dispatch the same original ordered claims wire. */
final class ClaimsPlanLogicalWireTest {
    private static final ExactRef SOURCE = new ExactRef("software-claims-source", 1, "a".repeat(64));
    private static Context context() {
        var now = java.time.Instant.parse("2026-10-24T00:00:00Z");
        var source = new org.xar.ck3.control.g2.common.G2Source("software-claims-machine", now.toString(), "1.20.0.4@sha256:" + Build.CROZIER4.sha256(), SOURCE);
        var frame = new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame(new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame(BigInteger.valueOf(707), BigInteger.valueOf(41), BigInteger.valueOf(24000)), "software-claims-snapshot", BigInteger.valueOf(7), "episode-1");
        var before = new org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity(source.machineId(), new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("134000000000000001"))), frame, 1);
        return new Context(before, source, "software-claims-session", BigInteger.ONE, Build.CROZIER4, now.plusSeconds(60), new ControlFrame(true,true,true,1,707L,707,"episode-1",false,null,null,List.of()));
    }
    @Test void installedAndDynamicProducerRetainOrderedTitlesThroughDescriptorAndNativeWire() throws Exception {
        var sets = List.of(List.of(new Int32Id(2), new Int32Id(1)), List.of(new Int32Id(1), new Int32Id(2)),
                List.of(new Int32Id(0), new Int32Id(Integer.MAX_VALUE)), List.of(new Int32Id(2)));
        var installed = new InteractionCapabilities.Installation(new InteractionCapabilities.Sources(SOURCE,SOURCE,SOURCE,SOURCE,SOURCE,SOURCE,SOURCE,SOURCE,SOURCE,SOURCE),
                new InteractionCapabilities.ReadPlan(List.of(),sets,List.of()),new InteractionCapabilities.RootHeirSource(){
                    public PlanningReadResult<HeirSubject> read(Context context){throw new AssertionError("not an heir read");}
                    public PlanningReadResult<HeirSubject> read(Session session,Context context){throw new AssertionError("not an heir read");}
                });
        var context = context();
        var family = new InteractionTitleSelectorReads(SOURCE,SOURCE);
        var catalog = new RootReadContractCatalog(List.of(),family.families());
        family.attach(catalog);
        for (var route : installed.claims()) {
            var selector = new InteractionTitleSelectorReads.ClaimsSelector(route.titles());
            var dynamic = family.issue(selector);
            assertEquals(route.contract().operation(), dynamic.operation());
            assertEquals(selector, InteractionTitleSelectorReads.decodeSelector(InteractionTitleSelectorReads.encodeSelector(selector)));
            var fixedRequest = new PlanningReadRequest(context.before(),context.source(),context.sessionId(),route.contract().operation(),InteractionArguments.app(InteractionArguments.body(context)),context.deadline());
            var dynamicRequest = new PlanningReadRequest(context.before(),context.source(),context.sessionId(),dynamic.operation(),InteractionTitleSelectorReads.arguments(context,selector),context.deadline());
            var fixedWire = route.contract().prepare(fixedRequest,"claims-wire");
            var dynamicWire = dynamic.prepare(dynamicRequest,"claims-wire");
            assertEquals(fixedWire,dynamicWire);
            var identity = NativeStepDiscriminator.identity(dynamic.operation());
            assertEquals(identity,NativeStepDiscriminator.fromJson(NativeStepDiscriminator.toJson(identity)));
            assertEquals(identity.nativeStep(),fixedWire.step());
            assertEquals("{}", new String(fixedWire.additionalFields().bytes(),java.nio.charset.StandardCharsets.UTF_8));
            NativeStepDiscriminator.requireRequest(dynamic.operation(),ExecutableStepBindings.Kind.READ,fixedWire);
            var packet = NativeWire.decodeExecuteRequest(NativeWire.execute("claims-wire",fixedWire.step(),context.revision(),fixedWire.additionalFields().bytes()));
            assertEquals(fixedWire.step(),packet.step());
            assertEquals("claims-wire",packet.requestId());
            assertEquals(context.revision(),packet.expectedRevision().orElseThrow());
            assertEquals("{}", new String(packet.normalizedAdditionalFields().value(), java.nio.charset.StandardCharsets.UTF_8));
        }
    }
}
