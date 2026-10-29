package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.HeldDriverObservationPort.SnapshotExport;
import org.xar.ck3.control.application.driver.HeldDriverObservationPort.OrdinarySnapshotExport;
import org.xar.ck3.control.application.driver.HeldDriverObservationPort;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.driver.PublicSnapshotCodec;
import org.xar.ck3.control.application.driver.WaitForChangeDriverFixture;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.NativeSnapshotWaitReceiverFixture;
import org.xar.ck3.control.service.mcp.*;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Real strict service/descriptor/adapter/Driver consumers; the software subset grants no live Root or migration qualification. */
final class RootWaitForChangePublicProductsTest {
    private static final String NAME="ck3_wait_for_change";
    private static RawJson raw(String body){return new RawJson(body.getBytes(StandardCharsets.UTF_8));}
    private static ExactRef ref(RawJson body){return new ExactRef("fixture/wait-public-product",body.bytes().length,ActionCodec.sha256(body.bytes()));}
    private record Installed(PublicMcpDirectory directory,AtomicInteger calls,AtomicReference<SnapshotExport> result) { }
    private static Installed install(WaitForChangeDriverFixture.Scenario scenario,WaitForChangePublicCodec.Deadlines deadlines) {
        return install(scenario.held(),deadlines);
    }
    private static Installed install(HeldDriverObservationPort held,WaitForChangePublicCodec.Deadlines deadlines) {
        // Explicit original-shape test descriptor. public_mcp owns the separate actual SDK metadata producer regression.
        var original=new ToolDescriptor(NAME,raw("""
            {"name":"ck3_wait_for_change","inputSchema":{"type":"object","properties":{
              "after_revision":{"type":"integer"},"timeout_seconds":{"type":"number","default":10.0}},
              "required":["after_revision"],"additionalProperties":false}}
            """));
        var descriptor=RootPublicCatalogCodec.executableTool(original);
        var source=ref(original.original());var registry=new PublicBindings();var calls=new AtomicInteger();var result=new AtomicReference<SnapshotExport>();
        var binding=RootWaitForChangePublicProducts.register(registry,request->{
            calls.incrementAndGet();
            try {var actual=RootWaitForChangePublicProducts.wait(held,request,deadlines);result.set(actual);return actual;}
            catch(IOException failure){throw new UncheckedIOException(failure);}
        },source);
        registry.freeze(Set.of(PublicMethod.WAIT_FOR_CHANGE));
        var catalog=new McpCoverage.Catalog(List.of(new McpCoverage.Declaration(NAME,source,1,1,"explicit software WAIT consumer regression",List.of())));
        var products=new PublicMcpBindings(catalog,List.of(new McpCoverage.Decision(NAME,McpCoverage.Admission.ADMITTED,source,"explicit software-only route")));
        PublicMcpNativeAdapter.register(products,descriptor,binding);
        var directory=products.freezeSoftwareScope();assertEquals(Scope.SOFTWARE_ONLY,directory.scope());
        return new Installed(directory,calls,result);
    }
    private static ToolCall call(String body){return new ToolCall(NAME,new Arguments(Presence.VALUE,Optional.of(raw(body))),Optional.empty(),new McpCancellation());}
    private static WaitForChangePublicCodec.Deadlines future() {
        Instant wait=Instant.now().plusSeconds(30);return new WaitForChangePublicCodec.Deadlines(wait,wait.plusSeconds(30));
    }
    private static DriverObservationAssembler.Complete ordinary(SnapshotExport actual) {
        return assertInstanceOf(OrdinarySnapshotExport.class,actual).actual();
    }
    private static void sameEnvelope(CallResult encoded,SnapshotExport actual) {
        var envelope=PublicDataJson.object(new RawJson(encoded.bytes()));
        assertEquals("complete",envelope.get("resultType").textValue());assertFalse(envelope.get("isError").booleanValue());
        RawJson structured=PublicDataJson.encode(envelope.get("structuredContent"));
        RawJson text=raw(envelope.get("content").get(0).get("text").textValue());
        assertEquals(actual.semantic(),PublicSnapshotCodec.decode(structured));
        assertEquals(actual.semantic(),PublicSnapshotCodec.decode(text));
        assertEquals(ordinary(actual).identity().frame().revision().toString(),envelope.get("structuredContent").get("revision").textValue());
        assertEquals(ordinary(actual).identity().frame().identity().nativeRevision().toString(),envelope.get("structuredContent").get("native_revision").textValue());
        assertEquals(2,envelope.get("structuredContent").get("native_command_history").size());
    }
    @Test void actualReceivedPacketsFlowThroughSameHeldStrictServiceAndOriginalMcpEnvelope()throws Exception {
        var first=WaitForChangeDriverFixture.frame(8,BigInteger.valueOf(2),false);
        var last=WaitForChangeDriverFixture.frame(9,BigInteger.valueOf(3),false);
        var scenario=WaitForChangeDriverFixture.sequence(first,last);var deadlines=future();var installed=install(scenario,deadlines);
        var result=installed.directory().invoke(call("{\"after_revision\":\"2\"}"));
        sameEnvelope(result,installed.result().get());
        var actual=ordinary(installed.result().get());assertEquals(last.original(),actual.originalEvidence());
        assertSame(actual,scenario.held().requireRetained(actual.identity(),last.original()));
        assertEquals(1,installed.calls().get());assertEquals(1,scenario.currentSnapshots().get());assertEquals(1,scenario.waits().get());assertEquals(2,scenario.facts().get());assertEquals(2,scenario.evidence().get());
        assertEquals(0,scenario.genericObservations().get());
        assertTrue(scenario.receivedDeadlines().stream().allMatch(value->value.waitUntil().equals(deadlines.waitUntil())&&value.captureUntil().equals(deadlines.captureUntil())));
    }
    @Test void actualTypedElapsedReturnsTheSameOriginalSnapshotWithoutInventingALargerRevision()throws Exception {
        var original=WaitForChangeDriverFixture.frame(9,BigInteger.valueOf(2),true);
        var scenario=WaitForChangeDriverFixture.sequence(original);
        var deadlines=new WaitForChangePublicCodec.Deadlines(Instant.now().minusSeconds(1),Instant.now().plusSeconds(30));
        var installed=install(scenario,deadlines);
        var result=installed.directory().invoke(call("{\"after_revision\":\"18446744073709551616\",\"timeout_seconds\":0.5}"));
        sameEnvelope(result,installed.result().get());
        assertEquals(BigInteger.valueOf(2),ordinary(installed.result().get()).identity().frame().revision());
        assertEquals(original.original(),ordinary(installed.result().get()).originalEvidence());
        assertEquals(1,scenario.waits().get());assertEquals(0,scenario.genericObservations().get());
    }
    @Test void actualUnavailableIsNeverReclassifiedFromItsDeadlineMessageAndInterruptRemainsUnconfirmed()throws Exception {
        var original=new IOException("Native transport deadline expired after partial header");
        var missing=WaitForChangeDriverFixture.unavailable(original);var installed=install(missing,future());
        var failed=assertThrows(UncheckedIOException.class,()->installed.directory().invoke(call("{\"after_revision\":\"2\"}")));
        assertSame(original,failed.getCause());assertNull(installed.result().get());assertEquals(1,missing.waits().get());
        assertEquals(1,missing.facts().get());assertEquals(1,missing.evidence().get());
        var interrupted=WaitForChangeDriverFixture.interrupted(new InterruptedException("actual typed wait interrupted"));
        var interruptedRoute=install(interrupted,future());assertFalse(Thread.currentThread().isInterrupted());
        try {
            assertThrows(ToolFailure.class,()->interruptedRoute.directory().invoke(call("{\"after_revision\":\"2\"}")));
            assertTrue(Thread.currentThread().isInterrupted());assertNull(interruptedRoute.result().get());
        }finally{Thread.interrupted();}
    }
    @Test void actualDescriptorAndDecoderRejectBadRequestsBeforeTheSoleWaitProducer()throws Exception {
        var scenario=WaitForChangeDriverFixture.sequence(WaitForChangeDriverFixture.frame(9,BigInteger.valueOf(2),true));
        var installed=install(scenario,future());
        for(String body:List.of("{}","{\"after_revision\":2}","{\"after_revision\":true}","{\"after_revision\":2.0}",
                "{\"after_revision\":\"02\"}","{\"expected_revision\":\"2\"}",
                "{\"after_revision\":\"2\",\"timeout_seconds\":null}","{\"after_revision\":\"2\",\"timeout_seconds\":true}",
                "{\"after_revision\":\"2\",\"timeout_seconds\":0}","{\"after_revision\":\"2\",\"timeout_seconds\":0.0000000001}"))
            assertThrows(ToolFailure.class,()->installed.directory().invoke(call(body)));
        assertEquals(0,installed.calls().get());assertEquals(0,scenario.waits().get());assertNull(installed.result().get());
    }
    @Test void actualEndpointBytesAndNgtReceivedFlowThroughHeldAndTheOriginalServiceEnvelope()throws Exception {
        try(var receiver=new NativeSnapshotWaitReceiverFixture(WaitForChangeDriverFixture.fullState())) {
            receiver.transport().observe(Instant.now().plusSeconds(5)); // The same actual transport's already adopted original sample.
            byte[] original=receiver.publishSnapshot("actual-public-wait",9,WaitForChangeDriverFixture.fullState());
            var held=WaitForChangeDriverFixture.receiver(receiver.transport(),Map.of(BigInteger.valueOf(7),BigInteger.valueOf(2),BigInteger.valueOf(9),BigInteger.valueOf(3)));
            var installed=install(held,future());int reads=receiver.actualReadCalls();
            var result=installed.directory().invoke(call("{\"after_revision\":\"2\",\"timeout_seconds\":0.5}"));
            sameEnvelope(result,installed.result().get());
            assertEquals(BigInteger.valueOf(9),ordinary(installed.result().get()).identity().frame().identity().nativeRevision());
            assertEquals(original.length,ordinary(installed.result().get()).originalEvidence().bytes());
            assertEquals(ActionCodec.sha256(original),ordinary(installed.result().get()).originalEvidence().sha256());
            assertTrue(receiver.actualReadCalls()>reads);assertEquals(0,receiver.actualWriteCalls());
        }
    }
    @Test void actualEndpointZeroPrefixElapsedFlowsThroughNgtHeldAndUnchangedSnapshotEnvelope()throws Exception {
        try(var receiver=new NativeSnapshotWaitReceiverFixture(WaitForChangeDriverFixture.fullState())) {
            var accepted=receiver.transport().observe(Instant.now().plusSeconds(5));
            var held=WaitForChangeDriverFixture.receiver(receiver.transport(),Map.of(BigInteger.valueOf(7),BigInteger.valueOf(2)));
            Instant waitUntil=Instant.now().plusMillis(10);
            var installed=install(held,new WaitForChangePublicCodec.Deadlines(waitUntil,waitUntil.plusSeconds(5)));
            int reads=receiver.actualReadCalls();
            var result=installed.directory().invoke(call("{\"after_revision\":\"18446744073709551616\",\"timeout_seconds\":0.01}"));
            sameEnvelope(result,installed.result().get());
            assertFalse(Instant.now().isBefore(waitUntil));
            assertEquals(BigInteger.valueOf(2),ordinary(installed.result().get()).identity().frame().revision());
            assertEquals(accepted.nativeRevision(),ordinary(installed.result().get()).identity().frame().identity().nativeRevision());
            assertEquals(ActionCodec.sha256(accepted.originalPacket()),ordinary(installed.result().get()).originalEvidence().sha256());
            assertEquals(reads,receiver.actualReadCalls());assertEquals(0,receiver.actualWriteCalls());
        }
    }
    @Test void actualEndpointSourceFailureAtTheWaitBoundaryDoesNotBecomeAnElapsedSnapshot()throws Exception {
        try(var receiver=new NativeSnapshotWaitReceiverFixture(WaitForChangeDriverFixture.fullState())) {
            receiver.transport().observe(Instant.now().plusSeconds(5));
            receiver.failActualSource("Native transport deadline expired but actual source guard failed");
            var held=WaitForChangeDriverFixture.receiver(receiver.transport(),Map.of(BigInteger.valueOf(7),BigInteger.valueOf(2)));
            var installed=install(held,new WaitForChangePublicCodec.Deadlines(Instant.now().minusSeconds(1),Instant.now().plusSeconds(5)));
            assertThrows(UncheckedIOException.class,()->installed.directory().invoke(call("{\"after_revision\":\"2\"}")));
            assertNull(installed.result().get());assertEquals(0,receiver.actualWriteCalls());
        }
    }
    @Test void actualAlreadyNewerCurrentSnapshotReturnsWithoutWaitingForAnotherNativePacket()throws Exception {
        try(var receiver=new NativeSnapshotWaitReceiverFixture(WaitForChangeDriverFixture.fullState())) {
            var accepted=receiver.transport().observe(Instant.now().plusSeconds(5));
            var held=WaitForChangeDriverFixture.receiver(receiver.transport(),Map.of(BigInteger.valueOf(7),BigInteger.valueOf(3)));
            Instant waitUntil=Instant.now().plusSeconds(1);
            var installed=install(held,new WaitForChangePublicCodec.Deadlines(waitUntil,waitUntil.plusSeconds(5)));
            int reads=receiver.actualReadCalls();
            var result=installed.directory().invoke(call("{\"after_revision\":\"2\",\"timeout_seconds\":1}"));
            sameEnvelope(result,installed.result().get());
            assertTrue(Instant.now().isBefore(waitUntil));assertEquals(reads,receiver.actualReadCalls());assertEquals(0,receiver.actualWriteCalls());
            assertEquals(ActionCodec.sha256(accepted.originalPacket()),ordinary(installed.result().get()).originalEvidence().sha256());
        }
    }
    @Test void actualWaitedTerminalOriginalRemainsFullDataWithoutAnInventedOrdinaryIdentity()throws Exception {
        var state=PublicDataJson.object(new RawJson(WaitForChangeDriverFixture.fullState()));state.putNull("played_character");
        try(var receiver=new NativeSnapshotWaitReceiverFixture(PublicDataJson.encode(state).bytes())) {
            var accepted=receiver.transport().observe(Instant.now().plusSeconds(5));
            var held=WaitForChangeDriverFixture.receiver(receiver.transport(),Map.of(BigInteger.valueOf(7),BigInteger.valueOf(3)));
            var deadlines=future();int reads=receiver.actualReadCalls();
            var full=held.waitForChangeFull(BigInteger.valueOf(2),deadlines.waitUntil(),deadlines.captureUntil());
            assertEquals(accepted.session(),full.actual().session());assertEquals(accepted.snapshotId(),full.actual().snapshotId());
            assertEquals(accepted.nativeRevision(),full.actual().nativeRevision());assertEquals(accepted.observedAt(),full.actual().observedAt());
            assertArrayEquals(accepted.state().bytes(),full.actual().state().bytes());assertArrayEquals(accepted.originalPacket(),full.actual().originalPacket());
            assertEquals(ActionCodec.sha256(accepted.originalPacket()),full.originalEvidence().sha256());
            assertEquals(org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil.INSTANCE,full.semantic().get("played_character"));
            assertInstanceOf(DriverObservationAssembler.Incomplete.class,new DriverObservationAssembler().assemble(full.actual(),full.facts(),full.originalEvidence()));
            assertEquals(reads,receiver.actualReadCalls());assertEquals(0,receiver.actualWriteCalls());
        }
    }
}
