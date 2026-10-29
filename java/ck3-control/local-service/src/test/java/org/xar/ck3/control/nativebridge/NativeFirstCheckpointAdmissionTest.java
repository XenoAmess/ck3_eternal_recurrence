package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.io.InterruptedIOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.CheckpointRequest;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.readiness.NativeReadiness;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector;
import org.xar.ck3.control.application.readiness.NativeSemanticEvidenceVerifier;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameLifecycle;

/** Actual raw Native/Driver/SEM/source chain. Software stage admission does not claim Root Begun, SAVE or Game acceptance. */
final class NativeFirstCheckpointAdmissionTest {
    @TempDir Path temporary;
    private static NativeReadiness.Policy policy(boolean cold, Duration stable, boolean pump) {
        // Root's private adoption actor must replace this deliberately different bootstrap actor without clearing other guards.
        return new NativeReadiness.Policy(cold, false, Optional.of(BigInteger.valueOf(74)), stable, pump);
    }
    private static CheckpointRequest.Readiness observe(CheckpointRequest.ObservationPort port) throws IOException {
        try { return port.observe(Instant.now().plusSeconds(20)); }
        catch (InterruptedException failure) {
            Thread.currentThread().interrupt(); var interrupted = new InterruptedIOException("software first-checkpoint interrupted");
            interrupted.initCause(failure); throw interrupted;
        }
    }
    private static final class Probe {
        final ActionWriterIntegrationFixture actual;
        final NativeReadinessCollector collector;
        final NativeSemanticEvidenceVerifier verifier;
        final AtomicInteger sourceChecks = new AtomicInteger(), ordinaryCapabilities = new AtomicInteger(), admittedActors = new AtomicInteger(), locks = new AtomicInteger();
        Probe(ActionWriterIntegrationFixture actual, NativeReadiness.Policy policy) {
            this(actual, policy, actual.writer::activeSession);
        }
        Probe(ActionWriterIntegrationFixture actual, NativeReadiness.Policy policy,
                NativeReadinessCollector.ActiveObservationSession active) {
            this.actual = actual; var inputs = actual.physicalInputs();
            verifier = new NativeSemanticEvidenceVerifier((same, ref, maximum) -> actual.archive.readArtifact(same, ref, maximum));
            ContinuityStorePort counted = new ContinuityStorePort() {
                @Override public WriterContracts.Prepared preview(WriterContracts.Request request) throws IOException { return actual.writer.preview(request); }
                @Override public WriterContracts.Receipt commit(WriterContracts.Prepared prepared) throws IOException { return actual.writer.commit(prepared); }
                @Override public ExactRef persistedHead() throws IOException { return actual.writer.persistedHead(); }
                @Override public void requireSession(Session same) throws IOException { actual.writer.requireSession(same); }
                @Override public <T> T locked(SessionWork<T> work) throws IOException { locks.incrementAndGet(); return actual.writer.locked(work); }
            };
            collector = new NativeReadinessCollector(actual.observationIdentity(), counted, inputs.transport(), inputs.driverAssembler(),
                    inputs.observationAssembler(), (game, deadline) -> new GameLifecycle.Running(game, inputs.source().sourceRef()),
                    (same, role, bytes) -> actual.archive.preserveArtifact(same, bytes, role.maximumBytes()), verifier,
                    (same, owner, frame, known, diagnostics, process, deadline) -> {
                        actual.writer.requireSession(same); assertEquals(actual.observationIdentity(), owner);
                        assertEquals(inputs.source(), frame.source()); assertEquals(frame.identity().game(), process.measured());
                        var original = same.capturePin(inputs.source().sourceRef(), 65_536); same.verifyPin(original);
                        var proof = actual.archive.preserveArtifact(same, "software-first-checkpoint-source-only".getBytes(java.nio.charset.StandardCharsets.UTF_8), 65_536);
                        return new NativeReadinessCollector.SourceQualification(proof, current -> {
                            actual.writer.requireSession(current); assertSame(same, current); current.verifyPin(original); sourceChecks.incrementAndGet();
                        });
                    }, (same, frame, known, received, deadline) -> {
                        ordinaryCapabilities.incrementAndGet(); throw new IllegalStateException("six ordinary domains intentionally uninitialized before first SAVE");
                    }, (same, frame, known, received, deadline) -> { throw new AssertionError("first checkpoint cannot collect planning inputs"); },
                    policy, Duration.ofSeconds(30), Clock.systemUTC());
            collector.bindObservationSession(actual.writer::requireSession); collector.bindActiveObservationSession(active);
            collector.bindReadyPublication((same, request, frame, known, source) -> { throw new AssertionError("first checkpoint cannot publish M7/Ready"); });
            collector.bindAdmittedActorAuthority((same, owner, frame, known, deadline) -> {
                admittedActors.incrementAndGet(); return known.driver().session().actorId();
            });
        }
    }
    private static class Admission implements NativeReadinessCollector.FirstCheckpointAdmission {
        final Probe probe; final AtomicInteger stages = new AtomicInteger(), physical = new AtomicInteger();
        ContinuityStorePort.Session stageSession; SemanticEvidence semantic;
        BigInteger actor = BigInteger.valueOf(73);
        Admission(Probe probe) { this.probe = probe; }
        @Override public void requireStage(ContinuityStorePort.Session same, SessionIdentity owner, Instant deadline) throws IOException {
            probe.actual.writer.requireSession(same); assertEquals(probe.actual.observationIdentity(), owner);
            if (stages.get() % 2 == 0) stageSession = same; else assertSame(stageSession, same);
            assertTrue(Instant.now().isBefore(deadline)); stages.incrementAndGet();
        }
        @Override public BigInteger requirePhysical(ContinuityStorePort.Session same, SessionIdentity owner, Complete frame,
                Known known, SemanticEvidence actualSemantic, NativeReadinessCollector.SourceQualification source, Instant deadline) throws IOException {
            probe.actual.writer.requireSession(same); assertSame(stageSession, same); assertEquals(probe.actual.observationIdentity(), owner);
            assertEquals(frame.identity(), actualSemantic.frame()); assertEquals(frame.identity().game(), known.stamp().game());
            assertEquals(frame.identity().frame().episodeRunId(), known.stamp().episodeRunId());
            assertEquals(BigInteger.valueOf(73), known.driver().session().actorId());
            assertEquals(frame.source(), probe.actual.physicalInputs().source());
            source.guard().assertCurrent(same); probe.verifier.verify(same, owner, actualSemantic);
            semantic = actualSemantic; physical.incrementAndGet(); return actor;
        }
    }

    @Test void physicalFirstCheckpointUsesActualBorrowedWriterAndSkipsEveryOrdinaryHook() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("physical-only"), false)) {
            var probe = new Probe(actual, policy(false, Duration.ZERO, false)); var admission = new Admission(probe);
            actual.physicalInputs().driverAssembler().bindCapabilityObservation((frame, known) -> { throw new AssertionError("raw first checkpoint cannot run Driver capability hook"); });
            var port = probe.collector.checkpointFirst("first-lineage", admission);
            actual.writer.locked(same -> {
                String head = same.head().digest(); var readiness = observe(port);
                assertTrue(readiness.saveEligible(), readiness.reason()); assertTrue(readiness.mapReady()); assertTrue(readiness.paused());
                assertEquals("first-lineage", readiness.lineageId()); assertEquals(admission.semantic.frame(), readiness.observed());
                assertEquals(admission.semantic.originalNativePacket(), readiness.nativeEvidence());
                assertEquals(head, same.head().digest()); assertEquals(0, probe.locks.get());
                assertEquals(2, admission.stages.get()); assertEquals(1, admission.physical.get()); return null;
            });
            assertEquals(0, probe.ordinaryCapabilities.get()); assertEquals(0, probe.admittedActors.get()); assertEquals(0, actual.nestedPlanningReads.get());
            assertNull(actual.lastPublishedReady.get()); assertEquals(0, actual.nativeReadWrites()); assertEquals(0, actual.nativeActionWrites());
            assertTrue(probe.sourceChecks.get() >= 3);
        }
    }

    @Test void ordinaryCheckpointStillRequiresItsRealDomainsWhileFirstCheckpointCannotGrantOrdinaryReady() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("uninitialized-domains"), false)) {
            var probe = new Probe(actual, policy(false, Duration.ZERO, false));
            assertThrows(IllegalStateException.class, () -> observe(probe.collector.checkpoint("ordinary")));
            assertEquals(1, probe.ordinaryCapabilities.get()); assertEquals(1, probe.admittedActors.get());
            assertTrue(observe(probe.collector.checkpointFirst("physical-first", new Admission(probe))).saveEligible());
            assertEquals(1, probe.ordinaryCapabilities.get()); assertEquals(1, probe.admittedActors.get());
            assertNull(actual.lastPublishedReady.get()); assertEquals(0, actual.nativeActionWrites());
        }
    }

    @Test void rejectedStageAndForeignOrEscapedWriterCannotBeginNativeCapture() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("admission"), false);
             var foreign = new ActionWriterIntegrationFixture(temporary.resolve("foreign"), false)) {
            var probe = new Probe(actual, policy(false, Duration.ZERO, false));
            var rejected = new Admission(probe) {
                @Override public void requireStage(ContinuityStorePort.Session same, SessionIdentity owner, Instant deadline) throws IOException {
                    super.requireStage(same, owner, deadline); throw new IOException("actual private stage is absent");
                }
            };
            int packets = actual.nativePacketReads();
            assertThrows(UncheckedIOException.class, () -> observe(probe.collector.checkpointFirst("stage", rejected)));
            assertEquals(packets, actual.nativePacketReads()); assertEquals(0, rejected.physical.get());
            var escaped = new AtomicReference<ContinuityStorePort.Session>();
            actual.writer.locked(same -> { escaped.set(same); return null; });
            var escapedProbe = new Probe(actual, policy(false, Duration.ZERO, false), () -> Optional.of(escaped.get()));
            assertThrows(IllegalArgumentException.class, () -> observe(escapedProbe.collector.checkpointFirst("escaped", new Admission(escapedProbe))));
            foreign.writer.locked(other -> {
                var wrong = new Probe(actual, policy(false, Duration.ZERO, false), () -> Optional.of(other));
                assertThrows(UncheckedIOException.class, () -> observe(wrong.collector.checkpointFirst("foreign", new Admission(wrong)))); return null;
            });
            assertEquals(packets, actual.nativePacketReads()); assertEquals(0, actual.nativeActionWrites());
        }
    }

    @Test void firstCheckpointDoesNotCreateAPlanningLeaseAndRecursionRefusesBeforeAnotherNativeSample() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("no-planning"), false)) {
            var probe = new Probe(actual, policy(false, Duration.ZERO, false));
            var retained = new AtomicReference<CheckpointRequest.ObservationPort>();
            var admission = new Admission(probe) {
                @Override public BigInteger requirePhysical(ContinuityStorePort.Session same, SessionIdentity owner, Complete frame,
                        Known known, SemanticEvidence semantic, NativeReadinessCollector.SourceQualification source, Instant deadline) throws IOException {
                    BigInteger actor = super.requirePhysical(same, owner, frame, known, semantic, source, deadline);
                    int packets = actual.nativePacketReads();
                    assertThrows(IllegalArgumentException.class, () -> probe.collector.borrowCurrent(same, frame.identity(), deadline, lease -> lease));
                    assertThrows(IllegalArgumentException.class, () -> probe.collector.withOwnedPlanning(same, owner, deadline, (request, lease) -> request));
                    assertThrows(IllegalArgumentException.class, () -> observe(retained.get()));
                    assertEquals(packets, actual.nativePacketReads()); return actor;
                }
            };
            retained.set(probe.collector.checkpointFirst("no-planning", admission));
            assertTrue(observe(retained.get()).saveEligible());
            assertTrue(observe(probe.collector.checkpointFirst("cleanup", new Admission(probe))).saveEligible());
            assertEquals(0, probe.ordinaryCapabilities.get()); assertNull(actual.lastPublishedReady.get());
        }
    }

    @Test void actualSourceMutationAfterPrivateAdmissionCannotPublishCheckpointReadiness() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("changed-source"), false)) {
            var probe = new Probe(actual, policy(false, Duration.ZERO, false));
            var admission = new Admission(probe) {
                @Override public BigInteger requirePhysical(ContinuityStorePort.Session same, SessionIdentity owner, Complete frame,
                        Known known, SemanticEvidence semantic, NativeReadinessCollector.SourceQualification source, Instant deadline) throws IOException {
                    BigInteger actor = super.requirePhysical(same, owner, frame, known, semantic, source, deadline);
                    Files.writeString(Path.of(frame.source().sourceRef().path()), "mutated actual source after admission"); return actor;
                }
            };
            assertThrows(UncheckedIOException.class, () -> observe(probe.collector.checkpointFirst("mutated", admission)));
            assertEquals(1, admission.physical.get()); assertEquals(0, probe.ordinaryCapabilities.get());
            assertEquals(0, actual.nativeActionWrites()); assertNull(actual.lastPublishedReady.get());
        }
    }

    @Test void privateActorAdmissionCannotClearWrongActorColdPumpOrStabilityGuards() throws Exception {
        for (int branch = 0; branch < 4; branch++) {
            try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("guard-" + branch), false)) {
                var selected = switch (branch) {
                    case 1 -> policy(true, Duration.ZERO, false);
                    case 2 -> policy(false, Duration.ZERO, true);
                    case 3 -> policy(false, Duration.ofDays(1), false);
                    default -> policy(false, Duration.ZERO, false);
                };
                var probe = new Probe(actual, selected); var admission = new Admission(probe);
                if (branch == 0) admission.actor = BigInteger.valueOf(74);
                var port = probe.collector.checkpointFirst("guarded", admission);
                var first = observe(port); var second = observe(port);
                assertFalse(first.saveEligible(), "branch " + branch + ": " + first.reason());
                assertFalse(second.saveEligible(), "branch " + branch + ": " + second.reason());
                assertEquals(0, probe.ordinaryCapabilities.get()); assertEquals(0, actual.nativeActionWrites());
            }
        }
    }
}
