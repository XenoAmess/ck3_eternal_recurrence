package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Arrays;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.CouncilPrivateCodec;
import org.xar.ck3.control.nativebridge.capabilities.governance.PrivateCouncilReads;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real READ/guard/transport/archive failures, with no constructed after observation or Known result. */
final class SharedFailedReadAfterWriterTest {
    @TempDir Path root;
    @FunctionalInterface private interface SourceWork<T> { T run(Session same) throws IOException; }
    private static <T> T source(ActionWriterIntegrationFixture actual, PlanningReadRequest request,
            AtomicInteger baseline, SourceWork<T> work) throws IOException {
        return actual.writer.locked(same -> actual.collector.current(same, request.before(), request.deadline(), lease -> {
            assertEquals(request.before(), lease.frame().identity());
            baseline.set(actual.nativeReadWrites());
            return work.run(same);
        }));
    }
    private static void oneOriginalRead(ActionWriterIntegrationFixture actual, AtomicInteger baseline) {
        assertEquals(baseline.get() + 1, actual.nativeReadWrites(), "after verification cannot issue a nested READ");
        assertEquals(1, actual.scenarioReadWrites());
        assertEquals(0, actual.nativeActionWrites());
    }
    private static RawJson raw(String text) { return new RawJson(text.getBytes(StandardCharsets.UTF_8)); }
    private static ActionWriterIntegrationFixture.SoftwareReadScenario scenario(AtomicReference<ReadContract<CouncilPrivateCodec.Reply>> installed) {
        return new ActionWriterIntegrationFixture.SoftwareReadScenario(
                "ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d", "fixture-council-failed-after", source -> {
            var definitions = new PrivateCouncilReads(source);
            installed.set(definitions.gates()); return definitions.registeredContracts();
        }, request -> raw("{}"), Optional.of("1.20.0.2"), Set.of());
    }
    private static PlanningReadRequest request(ActionWriterIntegrationFixture actual, ReadContract<?> contract) throws Exception {
        var command = actual.command("failed-after-source");
        return new PlanningReadRequest(command.origin(), command.source(), command.sessionId(), contract.operation(),
                new OpportunityJson.Obj(Map.of("position_key", new OpportunityJson.Text("councillor_steward"))), Instant.now().plusSeconds(15));
    }
    private static <T> PlanningReadResult.Unavailable<T> unavailable(PlanningReadResult<T> result) {
        if (result instanceof PlanningReadResult.Unavailable<T> unavailable) {
            System.out.println("actual failed READ reason: " + unavailable.reason());
            return unavailable;
        }
        throw new AssertionError("actual READ unexpectedly returned Known");
    }
    private static void malformedMustFail(ExactRef evidence, ActionPorts.OutcomeArchive archive) {
        for (int fault = 0; fault < 4; fault++) {
            var row = StrictJson.object(StrictJson.parse(archive.loadMaterial(evidence).bytes()),
                    Set.of("schema", "request", "contract_id", "request_id", "before", "after", "original_ref", "prepared_ref", "head_sequence", "head_digest"));
            switch (fault) {
                case 0 -> row.remove("after");
                case 1 -> row.put("head_sequence", true);
                case 2 -> row.set("original_ref", row.get("prepared_ref"));
                case 3 -> StrictJson.object(row.get("after"), Set.of("binding", "paused", "map_ready", "player_alive", "original_binding_sha256")).put("foreign", true);
                default -> throw new AssertionError();
            }
            ExactRef invalid = archive.preserveMaterial(new RawJson(StrictJson.canonical(row)));
            assertThrows(RuntimeException.class, () -> PlanningReadFailureCodec.load(invalid, archive));
        }
    }
    @Test void actualReadResponseFailureProducesAfterAndOneStrictArchivedClosureWithoutKnownCredit() throws Exception {
        var installed = new AtomicReference<ReadContract<CouncilPrivateCodec.Reply>>();
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("response-failure"), false, scenario(installed))) {
            actual.loseReadAckOnce();
            var requested = request(actual, installed.get());
            var captured = new AtomicReference<PlanningReadFailure>();
            var evidence = new AtomicReference<ExactRef>();
            var baseline = new AtomicInteger(-1);
            var result = source(actual, requested, baseline, borrowed -> actual.reads.readWithFailureEvidence(borrowed, installed.get(), requested,
                    (same, contract, current, exact, attempted, originals) -> {
                        var proof = attempted.orElseThrow();
                        proof.requireOriginal(same, contract, current, exact, originals);
                        var failed = exact.observedFailure().orElseThrow();
                        assertSame(failed, proof.observedFailure().orElseThrow());
                        assertSame(requested, failed.request());
                        assertEquals(proof.before(), failed.before());
                        assertNotSame(failed.before(), failed.after(), "the real after guard must be issued separately");
                        assertEquals(failed.before().binding().origin(), failed.after().binding().origin());
                        assertEquals(failed.before().originalBindingSha256(), failed.after().originalBindingSha256());
                        var unknown = assertInstanceOf(NativeActionPort.Unknown.class, failed.original());
                        assertEquals(NativeActionPort.FailureStage.RESPONSE_WAIT, unknown.failureCause().orElseThrow().stage());
                        assertArrayEquals(unknown.originalRequestPacket(),
                                assertInstanceOf(NativeActionPort.Unknown.class, originals.load(failed.originalRef())).originalRequestPacket());
                        ExactRef ref = PlanningReadFailureCodec.preserve(failed, originals);
                        assertEquals(failed, PlanningReadFailureCodec.load(ref, originals));
                        malformedMustFail(ref, originals);
                        captured.set(failed); evidence.set(ref);
                    }));
            var unavailable = unavailable(result);
            assertSame(captured.get(), unavailable.observedFailure().orElseThrow());
            assertNotNull(evidence.get());
            oneOriginalRead(actual, baseline);
            assertEquals(0, actual.snapshot().ledgerSequence());
            actual.writer.locked(same -> actual.archive.inSession(same, originals -> {
                assertEquals(captured.get(), PlanningReadFailureCodec.load(evidence.get(), originals)); return null;
            }));
            oneOriginalRead(actual, baseline);
        }
    }
    @Test void actualNegativeAckRetainsAfterAsUnavailableAndNeverBecomesSuccessfulRead() throws Exception {
        var installed = new AtomicReference<ReadContract<CouncilPrivateCodec.Reply>>();
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("negative"), false, scenario(installed))) {
            actual.rejectNextScenarioRead();
            var callbacks = new AtomicInteger();
            var requested = request(actual, installed.get());
            var baseline = new AtomicInteger(-1);
            var result = source(actual, requested, baseline, borrowed -> actual.reads.readWithFailureEvidence(borrowed, installed.get(), requested,
                    (same, contract, current, exact, attempted, originals) -> {
                        attempted.orElseThrow().requireOriginal(same, contract, current, exact, originals);
                        var failed = exact.observedFailure().orElseThrow();
                        assertFalse(assertInstanceOf(NativeActionPort.AckReceived.class, failed.original()).nativeOk());
                        assertEquals(failed, PlanningReadFailureCodec.load(PlanningReadFailureCodec.preserve(failed, originals), originals));
                        callbacks.incrementAndGet();
                    }));
            unavailable(result);
            assertEquals(1, callbacks.get()); oneOriginalRead(actual, baseline);
            assertEquals(0, actual.nativeActionWrites()); assertEquals(0, actual.snapshot().ledgerSequence());
        }
    }
    @Test void localPublicationFailurePreservesTheSameObservedOriginalForGlobalAndReturnedUnavailable() throws Exception {
        var installed = new AtomicReference<ReadContract<CouncilPrivateCodec.Reply>>();
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("observer"), false, scenario(installed))) {
            actual.rejectNextScenarioRead();
            var failed = new AtomicReference<PlanningReadFailure>();
            var globals = new AtomicInteger();
            actual.bindKnownReadObserver(new PlanningReadCoordinator.KnownReadObserver() {
                @Override public void afterKnown(Session same, ReadContract<?> contract, PlanningReadResult.Known<?> known) {
                    if (contract == installed.get()) fail("failed original Council READ cannot publish Known");
                }
                @Override public void afterUnavailable(Session same, ReadContract<?> contract, PlanningReadRequest current,
                        PlanningReadResult.Unavailable<?> exact, Optional<PlanningReadCoordinator.FailedReadAttempt> attempted) {
                    if (contract != installed.get()) return;
                    assertSame(failed.get(), exact.observedFailure().orElseThrow());
                    try { attempted.orElseThrow().requireOriginal(same, contract, current, exact, actual.archive.withSession(same)); }
                    catch (IOException failure) { throw new AssertionError(failure); }
                    globals.incrementAndGet();
                }
            });
            var requested = request(actual, installed.get());
            var baseline = new AtomicInteger(-1);
            var result = source(actual, requested, baseline, borrowed -> actual.reads.readWithFailureEvidence(borrowed, installed.get(), requested,
                    (same, contract, current, exact, attempted, originals) -> {
                        attempted.orElseThrow().requireOriginal(same, contract, current, exact, originals);
                        failed.set(exact.observedFailure().orElseThrow());
                        throw new IOException("controlled local publication failure");
                    }));
            var unavailable = unavailable(result);
            assertSame(failed.get(), unavailable.observedFailure().orElseThrow());
            assertEquals(1, globals.get()); oneOriginalRead(actual, baseline);
            assertEquals(0, actual.nativeActionWrites());
        }
    }
    @Test void preflightFailureHasNoAfterOrOutcomeOrNativeSubmission() throws Exception {
        var installed = new AtomicReference<ReadContract<CouncilPrivateCodec.Reply>>();
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("preflight"), false, scenario(installed))) {
            var current = request(actual, installed.get());
            var foreign = new PlanningReadRequest(current.origin(), current.source(), current.sessionId(),
                    new OperationKey("query-foreign-after-v1"), current.arguments(), current.deadline());
            var baseline = new AtomicInteger(-1);
            var result = source(actual, current, baseline, borrowed -> actual.reads.readWithFailureEvidence(borrowed, installed.get(), foreign,
                    (same, contract, requested, exact, attempted, originals) -> {
                        assertTrue(exact.observedFailure().isEmpty()); assertTrue(exact.original().isEmpty());
                        assertTrue(attempted.isEmpty());
                    }));
            assertTrue(unavailable(result).observedFailure().isEmpty());
            assertEquals(baseline.get(), actual.nativeReadWrites());
            assertEquals(0, actual.scenarioReadWrites());
            assertEquals(0, actual.nativeActionWrites());
        }
    }
    @Test void aFailureBeforeTheRealAfterGuardCannotAcquireAnObservedFailure() throws Exception {
        var installed = new AtomicReference<ReadContract<CouncilPrivateCodec.Reply>>();
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("before-after"), false, scenario(installed))) {
            var requested = request(actual, installed.get());
            var baseline = new AtomicInteger(-1);
            var result = source(actual, requested, baseline, borrowed -> actual.reads.read(borrowed, installed.get(), requested,
                    new PlanningReadCoordinator.ReadLifecycleObserver() {
                        @Override public void prepared(Session same, ReadContract<?> contract, PlanningReadRequest requested,
                                String requestId, NativeRequest prepared) { }
                        @Override public void received(Session same, ReadContract<?> contract, PlanningReadRequest requested,
                                String requestId, NativeActionPort.DispatchOutcome original) throws IOException {
                            throw new IOException("controlled failure before the actual after guard");
                        }
                        @Override public void known(Session same, ReadContract<?> contract, PlanningReadResult.Known<?> known) { fail(); }
                        @Override public void failed(Session same, ReadContract<?> contract, PlanningReadRequest requested,
                                Optional<NativeActionPort.DispatchOutcome> original, String reason) { }
                    }));
            assertTrue(unavailable(result).original().isPresent());
            assertTrue(unavailable(result).observedFailure().isEmpty());
            oneOriginalRead(actual, baseline);
        }
    }
    @Test void actualSourceDriftAfterReturnedReadCannotPublishAnObservedFailure() throws Exception {
        var installed = new AtomicReference<ReadContract<CouncilPrivateCodec.Reply>>();
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("source-drift"), false, scenario(installed))) {
            actual.rejectNextScenarioRead();
            var current = request(actual, installed.get());
            var baseline = new AtomicInteger(-1);
            var result = new AtomicReference<PlanningReadResult<CouncilPrivateCodec.Reply>>();
            var received = new AtomicInteger();
            assertThrows(Exception.class, () -> source(actual, current, baseline, same -> {
                result.set(actual.reads.read(same, installed.get(), current, new PlanningReadCoordinator.ReadLifecycleObserver() {
                    @Override public void prepared(Session callback, ReadContract<?> contract, PlanningReadRequest requested,
                            String requestId, NativeRequest prepared) { }
                    @Override public void received(Session callback, ReadContract<?> contract, PlanningReadRequest requested,
                            String requestId, NativeActionPort.DispatchOutcome original) throws IOException {
                        received.incrementAndGet();
                        var transport = actual.physicalInputs().transport();
                        var previous = transport.currentSnapshot(requested.deadline());
                        byte[] packet = previous.originalPacket();
                        var frame = (ObjectNode) StrictJson.parse(Arrays.copyOfRange(packet, 4, packet.length));
                        frame.put("snapshot_id", previous.snapshotId() + "-after-returned-read");
                        frame.put("revision", previous.nativeRevision().add(java.math.BigInteger.ONE));
                        actual.enqueueSoftwareNativePacket(NativeWire.packet(StrictJson.canonical(frame)));
                        try { transport.waitForSnapshot(Instant.now().plusMillis(50), requested.deadline()); }
                        catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IOException(interrupted); }
                    }
                    @Override public void known(Session callback, ReadContract<?> contract, PlanningReadResult.Known<?> known) { fail(); }
                    @Override public void failed(Session callback, ReadContract<?> contract, PlanningReadRequest requested,
                            Optional<NativeActionPort.DispatchOutcome> original, String reason) { }
                }));
                return null;
            }));
            assertEquals(1, received.get());
            assertNotNull(result.get(), "the actual coordinator must return its failed READ before outer source teardown rejects drift");
            assertTrue(unavailable(result.get()).original().isPresent());
            assertTrue(unavailable(result.get()).observedFailure().isEmpty(),
                    "a returned READ cannot borrow a changed physical source as its actual after guard");
            oneOriginalRead(actual, baseline);
        }
    }
}
