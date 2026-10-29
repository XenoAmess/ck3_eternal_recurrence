package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual coordinator/transport/archive on controlled packet edges; no private proof is constructed by tests. */
final class ReadFailureEvidenceTest {
    @TempDir Path root;
    private static final OperationKey QUERY = new OperationKey("query-fixture-failure-evidence-v1");
    private static final String CAPABILITY = "game.query.fixture-failure-evidence";
    private static RawJson raw(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }
    private static ReadContract<RawJson> contract(ExactRef source) {
        return new ReadContract<>("fixture-failure-evidence/v1", QUERY, Optional.of(CAPABILITY), "fixture-failure-evidence",
                ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, source,
                (request,id) -> new NativeRequest(QUERY.value(), CAPABILITY, raw("{}")),
                receipt -> receipt.original().originalResultToken().orElseThrow());
    }
    private static ActionWriterIntegrationFixture.SoftwareReadScenario scenario(AtomicReference<ReadContract<RawJson>> installed) {
        return new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64), "fixture-failure-evidence", source -> {
            var selected = contract(source); installed.set(selected); return List.of(selected);
        }, request -> raw("{\"actual_payload\":true}"));
    }
    private static PlanningReadRequest request(ActionWriterIntegrationFixture actual, ReadContract<?> selected) throws Exception {
        var command = actual.command("failure-evidence-basis");
        return new PlanningReadRequest(command.before(), command.source(), command.sessionId(), selected.operation(),
                new OpportunityJson.Obj(Map.of()), Instant.now().plusSeconds(10));
    }
    private static void require(PlanningReadCoordinator.FailedReadAttempt proof, Session same, ReadContract<?> contract,
            PlanningReadRequest request, PlanningReadResult.Unavailable<?> exact, ActionPorts.OutcomeArchive archive) {
        try { proof.requireOriginal(same,contract,request,exact,archive); }
        catch(IOException failure) { throw new java.io.UncheckedIOException(failure); }
    }
    @Test void actualNegativeAckIsObservedLocallyBeforeTheExistingGlobalPublisherWithIdenticalCustody() throws Exception {
        var installed = new AtomicReference<ReadContract<RawJson>>();
        try(var actual = new ActionWriterIntegrationFixture(root.resolve("negative"),false,scenario(installed))) {
            actual.rejectNextScenarioRead(); var requested = request(actual,installed.get());
            var order = new ArrayList<String>(); var captured = new AtomicReference<PlanningReadResult.Unavailable<?>>();
            actual.bindKnownReadObserver(new PlanningReadCoordinator.KnownReadObserver() {
                @Override public void afterKnown(Session same,ReadContract<?> contract,PlanningReadResult.Known<?> known) { fail(); }
                @Override public void afterUnavailable(Session same,ReadContract<?> contract,PlanningReadRequest request,
                        PlanningReadResult.Unavailable<?> exact,Optional<PlanningReadCoordinator.FailedReadAttempt> proof) {
                    assertSame(captured.get(),exact); order.add("global");
                }
            });
            var result = actual.reads.readWithFailureEvidence(installed.get(),requested,(same,contract,request,exact,origin,originals) -> {
                assertSame(installed.get(),contract); assertSame(requested,request);
                var proof = origin.orElseThrow(); require(proof,same,contract,request,exact,originals);
                assertSame(proof.original(),exact.original().orElseThrow());
                assertFalse(assertInstanceOf(NativeActionPort.AckReceived.class,proof.original()).nativeOk());
                assertEquals(proof.original(),originals.load(proof.originalRef()));
                var copied = new PlanningReadRequest(request.origin(),request.source(),request.sessionId(),request.operation(),request.arguments(),request.deadline());
                assertThrows(IllegalArgumentException.class,() -> proof.requireOriginal(same,contract,copied,exact,originals));
                var copiedResult = new PlanningReadResult.Unavailable<>(exact.reason(),exact.original(),exact.decodeFailure());
                assertThrows(IllegalArgumentException.class,() -> proof.requireOriginal(same,contract,request,copiedResult,originals));
                captured.set(exact); order.add("local");
            });
            assertSame(captured.get(),result); assertEquals(List.of("local","global"),order);
            assertEquals(1,actual.nativeReadWrites()); assertEquals(0,actual.nativeActionWrites());
        }
    }
    @Test void actualConsumedUnknownRetainsItsOriginalPacketAndNeverReplaysTheRead() throws Exception {
        var installed = new AtomicReference<ReadContract<RawJson>>();
        try(var actual = new ActionWriterIntegrationFixture(root.resolve("unknown"),false,scenario(installed))) {
            actual.loseReadAckOnce(); var callbacks = new AtomicInteger();
            var result = actual.reads.readWithFailureEvidence(installed.get(),request(actual,installed.get()),(same,contract,request,exact,origin,archive) -> {
                var proof = origin.orElseThrow(); require(proof,same,contract,request,exact,archive);
                assertInstanceOf(NativeActionPort.Unknown.class,proof.original()); callbacks.incrementAndGet();
            });
            assertInstanceOf(NativeActionPort.Unknown.class,assertInstanceOf(PlanningReadResult.Unavailable.class,result).original().orElseThrow());
            assertEquals(1,callbacks.get()); assertEquals(1,actual.nativeReadWrites()); assertEquals(0,actual.nativeActionWrites());
        }
    }
    @Test void localObserverFailureKeepsTheOriginalAckAndDoesNotReplaceTheGlobalPublicationPath() throws Exception {
        var installed = new AtomicReference<ReadContract<RawJson>>();
        try(var actual = new ActionWriterIntegrationFixture(root.resolve("observer"),false,scenario(installed))) {
            actual.rejectNextScenarioRead(); var global = new AtomicInteger();
            var original = new AtomicReference<NativeActionPort.DispatchOutcome>();
            actual.bindKnownReadObserver(new PlanningReadCoordinator.KnownReadObserver() {
                @Override public void afterKnown(Session same,ReadContract<?> contract,PlanningReadResult.Known<?> known) { fail(); }
                @Override public void afterUnavailable(Session same,ReadContract<?> contract,PlanningReadRequest request,
                        PlanningReadResult.Unavailable<?> exact,Optional<PlanningReadCoordinator.FailedReadAttempt> proof) {
                    assertSame(original.get(),exact.original().orElseThrow()); global.incrementAndGet();
                }
            });
            var result = assertInstanceOf(PlanningReadResult.Unavailable.class,actual.reads.readWithFailureEvidence(
                    installed.get(),request(actual,installed.get()),(same,contract,request,exact,proof,archive) -> {
                        require(proof.orElseThrow(),same,contract,request,exact,archive); original.set(exact.original().orElseThrow());
                        throw new IOException("controlled local observer failure");
                    }));
            assertSame(original.get(),result.original().orElseThrow()); assertEquals(1,global.get());
            assertTrue(result.reason().contains("original failed-read evidence observer unavailable"));
            assertEquals(1,actual.nativeReadWrites()); assertEquals(0,actual.nativeActionWrites());
        }
    }
    @Test void preflightFailureHasNoConsumedReadProofAndSuccessfulReadHasNoFailureCallback() throws Exception {
        var installed = new AtomicReference<ReadContract<RawJson>>();
        try(var actual = new ActionWriterIntegrationFixture(root.resolve("phase"),false,scenario(installed))) {
            var current = request(actual,installed.get());
            var foreign = new PlanningReadRequest(current.origin(),current.source(),current.sessionId(),
                    new OperationKey("query-foreign-evidence-v1"),current.arguments(),current.deadline());
            var callbacks = new AtomicInteger();
            assertInstanceOf(PlanningReadResult.Unavailable.class,actual.reads.readWithFailureEvidence(installed.get(),foreign,
                    (same,contract,request,exact,proof,archive) -> {
                        assertTrue(proof.isEmpty()); assertTrue(exact.original().isEmpty()); callbacks.incrementAndGet();
                    }));
            assertEquals(0,actual.nativeReadWrites());
            assertInstanceOf(PlanningReadResult.Known.class,actual.reads.readWithFailureEvidence(installed.get(),current,
                    (same,contract,request,exact,proof,archive) -> fail("Known must not publish a failed-read proof")));
            assertEquals(1,callbacks.get()); assertEquals(1,actual.nativeReadWrites()); assertEquals(0,actual.nativeActionWrites());
        }
    }
    @Test void anUnimplementedReadPortCannotSilentlyFallBackToAnOrdinaryRead() throws Exception {
        var installed = new AtomicReference<ReadContract<RawJson>>();
        try(var actual = new ActionWriterIntegrationFixture(root.resolve("unsupported"),false,scenario(installed))) {
            var ordinary = new AtomicInteger();
            PlanningReadPort unsupported = new PlanningReadPort() {
                @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request) {
                    ordinary.incrementAndGet(); throw new AssertionError("ordinary fallback must not be invoked");
                }
            };
            var current = request(actual,installed.get());
            assertThrows(IllegalStateException.class,() -> unsupported.readWithFailureEvidence(installed.get(),current,
                    (same,contract,request,exact,proof,archive) -> fail()));
            assertEquals(0,ordinary.get()); assertEquals(0,actual.nativeReadWrites());
        }
    }
}
