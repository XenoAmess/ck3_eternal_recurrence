package org.xar.ck3.control.application.planning.sway;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real registered contract prepare/decode path; only archived source/paused guard context is synthetic. */
public final class SwayNativeBindingsTest {
    private static final ExactRef SOURCE = new ExactRef("fixture:synthetic-definition", 1, "b".repeat(64));
    private static final Instant NOW = Instant.parse("2026-10-23T17:30:00Z");
    @Test void frozenRootFamiliesIssueOnlyTheirIdenticalExactContractsAndRejectRebinding() {
        SwayRootReads reads = new SwayRootReads(new SwayRootReads.Sources(SOURCE, SOURCE, SOURCE));
        assertThrows(IllegalStateException.class, () -> reads.target(50331650));
        assertThrows(IllegalArgumentException.class, () -> reads.attach(new RootReadContractCatalog(List.of(), List.of())));
        RootReadContractCatalog actual = new RootReadContractCatalog(List.of(), reads.families()); reads.attach(actual);
        var first = reads.target(50331650); assertSame(first, reads.target(50331650)); assertTrue(actual.containsIdentity(first));
        assertNotSame(first, reads.target(50331651));
        assertThrows(IllegalArgumentException.class, () -> reads.attach(new RootReadContractCatalog(List.of(), reads.families())));
    }
    @Test void sharedNativeProducerEntersActualRootIssuedDefinitionAndPreservesUnsafeUint64Exactly() throws Exception {
        SwayRootReads reads = new SwayRootReads(new SwayRootReads.Sources(SOURCE, SOURCE, SOURCE)); RootReadContractCatalog catalog = new RootReadContractCatalog(List.of(), reads.families()); reads.attach(catalog);
        var definition = reads.target(50331650); PlanningReadReceipt receipt = receipt(definition, "");
        NativeRequest nativeRequest = definition.prepare(receipt.request(), receipt.requestId()); assertEquals(SwayNativeWire.TARGET + 50331650L, nativeRequest.step());
        assertTrue(nativeRequest.requiredCapability().isEmpty()); assertTrue(StrictJson.parse(nativeRequest.additionalFields().bytes()).isEmpty());
        var actual = definition.decode(receipt); assertEquals(new BigInteger("16786632562036001389"), actual.containerGeneration()); assertTrue(actual.startable(true));
    }
    @Test void originalTokenFullFrameAndGuardCustodyMustAllAgreeBeforeTypedConsumer() throws Exception {
        var definition = SwayNativeBindings.target(SOURCE, 50331650);
        for (String failure : List.of("token", "guard", "source", "request", "nativeAck", "unpaused")) {
            PlanningReadReceipt original = receipt(definition, failure); assertThrows(IllegalArgumentException.class, () -> definition.decode(original), failure);
        }
    }
    private static PlanningReadReceipt receipt(ReadContract<?> definition, String defect) throws Exception {
        var bound = SwayNativeFormalTest.binding(73, 7, 53220000); var source = new G2Source(bound.before().machineId(), NOW.toString(), SwayNativeWire.BUILD, SOURCE);
        ObjectNode arguments = StrictJson.object(); arguments.put("target_character_id", 50331650);
        var request = new PlanningReadRequest(bound.before(), source, bound.sessionId(), definition.operation(), OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(arguments)), "synthetic target args"), NOW.plusSeconds(30));
        ObjectNode frame = SwayNativeFormalTest.vector("query"), token = ((ObjectNode)frame.get("result")).deepCopy();
        if (defect.equals("token")) token.put("unexpected_alias", true);
        if (defect.equals("request")) frame.put("request_id", "foreign-native-request");
        var guardSource = defect.equals("source") ? new G2Source(source.machineId(), NOW.plusSeconds(1).toString(), source.exactBuild(), SOURCE) : source;
        var guard = new GuardEvidence(bound.before(), guardSource, bound.sessionId(), bound.connectionGeneration(), definition.operation(), SOURCE, SOURCE, bound.authorityId(), NOW, NOW.plusSeconds(30));
        var before = new PlanningReadGuard(guard, !defect.equals("unpaused"), true, true, "c".repeat(64));
        var after = new PlanningReadGuard(guard, true, true, true, (defect.equals("guard") ? "d" : "c").repeat(64));
        byte[] bytes = SwayNativeFormalTest.bytes(frame); var ack = new NativeActionPort.AckReceived("fixture-read", !defect.equals("nativeAck"), Optional.of(new RawJson(StrictJson.canonical(token))), new RawJson(bytes), bytes);
        return new PlanningReadReceipt(request, definition.contractId(), "fixture-read", before, after, ack);
    }
}
