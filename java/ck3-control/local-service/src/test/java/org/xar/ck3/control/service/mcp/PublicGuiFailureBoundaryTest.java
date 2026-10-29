package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.GuiActionFailure;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.GuiReadFailure;
import org.xar.ck3.control.service.root.RootOriginalPublicTestInputs;
import org.xar.ck3.control.service.root.RootPublicCatalogCodec;

/** Actual GUI failure producer through the installed software Directory and both RPC versions.
 * No native request, Root permission or live read is manufactured by this boundary regression. */
final class PublicGuiFailureBoundaryTest {
    private static final String NAME = "ck3_query_white_rendered_text_v1";
    private record Query() { }

    private static PublicMcpDirectory directory(GuiReadFailure failure, AtomicInteger invoked,
            AtomicInteger encoded) throws Exception {
        return directory(NAME, failure, invoked, encoded);
    }
    private static PublicMcpDirectory directory(String name, RuntimeException failure, AtomicInteger invoked,
            AtomicInteger encoded) throws Exception {
        var original = RootOriginalPublicTestInputs.tools().stream().filter(tool -> tool.name().equals(name))
                .findFirst().orElseThrow(() -> new IllegalStateException("NOT_RUN_REQUIRED_ACTUAL_ORIGINAL_TOOL: " + name));
        var bindings = PublicMcpBindingTest.oneAdmitted(name);
        bindings.registerDirect(RootPublicCatalogCodec.executableTool(original),
                PublicMcpBindings.Kind.APPLICATION_COMPOSITE, Query.class, RawJson.class,
                query -> { invoked.incrementAndGet(); throw failure; }, call -> new Query(),
                response -> { encoded.incrementAndGet(); return CallResult.fromBusinessJson(response); },
                PublicMcpProtocolTest.target());
        return bindings.freezeSoftwareScope();
    }

    private static NativeActionPort.AckReceived ack(boolean ok, String error) {
        byte[] body = ("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"gui-read\",\"ok\":"
                + ok + ",\"error\":\"" + error + "\"}").getBytes(StandardCharsets.UTF_8);
        byte[] packet = ByteBuffer.allocate(body.length + Integer.BYTES).order(ByteOrder.LITTLE_ENDIAN)
                .putInt(body.length).put(body).array();
        return new NativeActionPort.AckReceived("gui-read", ok, Optional.empty(), new RawJson(body), packet);
    }

    private static List<PlanningReadResult.Unavailable<Object>> failures() {
        return List.of(
                new PlanningReadResult.Unavailable<>("actual provider unavailable", Optional.empty()),
                new PlanningReadResult.Unavailable<>("outer unavailable", Optional.of(
                        new NativeActionPort.RejectedBeforeDispatch("gui-read", new NativeActionPort.ZeroDispatchProof(
                                NativeActionPort.ZeroDispatchStage.BEFORE_WRITE, 0, "actual zero-write refusal", Optional.empty())))),
                new PlanningReadResult.Unavailable<>("outer unavailable", Optional.of(
                        new NativeActionPort.Unknown("gui-read", "actual unknown outcome", new byte[] {1}, Optional.empty()))),
                new PlanningReadResult.Unavailable<>("outer unavailable", Optional.of(ack(false, "actual native refusal"))),
                new PlanningReadResult.Unavailable<>("actual original ACK cannot decode", Optional.of(ack(true, ""))));
    }

    @Test void actualProducerKeepsTheIdenticalUnavailableOutcomeAndTypedCauseAtDirectory() throws Exception {
        for (var unavailable : failures()) {
            var failure = GuiReadFailure.from(unavailable);
            var invoked = new AtomicInteger(); var encoded = new AtomicInteger();
            var directory = directory(failure, invoked, encoded);
            var actual = assertThrows(ToolFailure.class,
                    () -> directory.invoke(PublicMcpBindingTest.call(NAME, "{}")));
            assertEquals(failure.getMessage(), actual.getMessage()); assertSame(failure, actual.getCause());
            var retained = (GuiReadFailure) actual.getCause();
            assertSame(unavailable, retained.unavailable()); assertEquals(unavailable.reason(), retained.sourceReason());
            unavailable.original().ifPresent(original -> assertSame(original, retained.original().orElseThrow()));
            assertEquals(1, invoked.get()); assertEquals(0, encoded.get());
        }
    }

    @Test void bothRpcVersionsUseTheOriginalToolErrorEnvelopeAndNeverEncodeSuccess() throws Exception {
        for (String version : List.of("2025-11-25", PublicMcpSession.MODERN)) for (var unavailable : failures()) {
            var failure = GuiReadFailure.from(unavailable);
            var invoked = new AtomicInteger(); var encoded = new AtomicInteger();
            try (var peer = new PublicMcpProtocolTest.Peer(directory(failure, invoked, encoded))) {
                peer.initialize(version);
                peer.send(PublicMcpProtocolTest.request(version, "1", "tools/call",
                        "\"name\":\"" + NAME + "\",\"arguments\":{}"));
                var response = peer.receive(); var result = response.get("result");
                assertFalse(response.has("error")); assertTrue(result.get("isError").booleanValue());
                assertFalse(result.has("structuredContent"));
                assertEquals("Error executing tool " + NAME + ": " + failure.getMessage(),
                        result.get("content").get(0).get("text").textValue());
            }
            assertEquals(1, invoked.get()); assertEquals(0, encoded.get());
        }
    }

    @Test void malformedPublicArgumentsDoNotReachTheGuiProducer() throws Exception {
        var failure = GuiReadFailure.from(failures().get(0));
        var invoked = new AtomicInteger(); var encoded = new AtomicInteger();
        var directory = directory(failure, invoked, encoded);
        var actual = assertThrows(ToolFailure.class,
                () -> directory.invoke(PublicMcpBindingTest.call(NAME, "{\"expected_revision\":true}")));
        assertEquals("invalid tool arguments; no application invocation occurred", actual.getMessage());
        assertEquals(0, invoked.get()); assertEquals(0, encoded.get());
    }

    @Test void rejectedActionReceiptUsesTheSameTypedBoundaryAndBothRpcVersions() throws Exception {
        String name="ck3_open_ingame_decisions_v1";
        var failure=GuiActionFailure.fromRejectedAck(rejectedReceipt());
        var invoked=new AtomicInteger(); var encoded=new AtomicInteger();
        var directory=directory(name,failure,invoked,encoded);
        var actual=assertThrows(ToolFailure.class,()->directory.invoke(PublicMcpBindingTest.call(name,"{}")));
        assertSame(failure,actual.getCause()); assertEquals(failure.getMessage(),actual.getMessage());
        assertSame(failure.receipt().ack().orElseThrow(),failure.original());
        for(String version:List.of("2025-11-25",PublicMcpSession.MODERN)) {
            try(var peer=new PublicMcpProtocolTest.Peer(directory)) {
                peer.initialize(version);
                peer.send(PublicMcpProtocolTest.request(version,"1","tools/call","\"name\":\""+name+"\",\"arguments\":{}"));
                var response=peer.receive(); var result=response.get("result");
                assertFalse(response.has("error")); assertTrue(result.get("isError").booleanValue());
                assertFalse(result.has("structuredContent"));
                assertEquals("Error executing tool "+name+": "+failure.getMessage(),result.get("content").get(0).get("text").textValue());
            }
        }
        assertEquals(3,invoked.get()); assertEquals(0,encoded.get());
    }

    /** Canonical receipt DATA fixture following the real formatter failure regression; no writer lease. */
    private static org.xar.ck3.control.application.action.ActionReceipt rejectedReceipt() {
        Instant now=Instant.parse("2026-10-24T19:00:00Z");
        var evidence=new org.xar.ck3.control.contracts.ExactRef("software-data:gui-failure",1,"a".repeat(64));
        var source=new org.xar.ck3.control.g2.common.G2Source("xenoamess-full-tower-eb9d2c1186",now.toString(),"1.20.0.4",evidence);
        var frame=new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame(
                new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame(BigInteger.ONE,BigInteger.valueOf(3),BigInteger.ONE),
                "software-gui-before",BigInteger.valueOf(4),"software-gui-episode");
        var before=new ObservationIdentity(source.machineId(),
                new GameGeneration(12700,new PythonOnlyUInt64(BigInteger.ONE)),frame,1);
        var operation=new org.xar.ck3.control.application.action.OperationKey("navigate-ingame-ui-v1");
        var expected=new ExpectedPostcondition(1,before,source,"software.gui-observer/v1",
                List.of(new ExpectedBoolean(new FieldKey("gui.actual"),true)));
        var command=new org.xar.ck3.control.application.action.ActionCommand("software-gui-action",before,source,"software-gui-session",operation,
                new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(java.util.Map.of()),expected,
                new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),now.plusSeconds(60));
        var guard=new org.xar.ck3.control.application.action.GuardEvidence(before,source,"software-gui-session",BigInteger.TWO,operation,
                evidence,evidence,"software-only",now,now.plusSeconds(60));
        var attempt=new org.xar.ck3.control.application.action.ActionState.Attempt("gui-read",now,guard,
                new org.xar.ck3.control.application.action.NativeRequest(operation.value(),"game.command."+operation.value(),
                        new RawJson("{}".getBytes(StandardCharsets.UTF_8))));
        var state=new org.xar.ck3.control.application.action.ActionState.Unknown(Optional.of(attempt),Optional.of(ack(false,"actual native refusal")),
                "actual negative GUI outcome",List.of(evidence));
        return new org.xar.ck3.control.application.action.ActionReceipt(1,1,command,
                org.xar.ck3.control.application.action.ActionCodec.bodySha256(command),state);
    }
}
