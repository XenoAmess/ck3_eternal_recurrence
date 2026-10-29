package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.io.InterruptedIOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.readiness.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Real physical guard/SEM/archive boundary. Finite software stage admission grants no private Root Begun, SAVE or Game result. */
final class RootFirstCheckpointGuardTest {
    @TempDir Path temporary;
    private static final String SAVE_CAPABILITY = "game.command.save-checkpoint", AUTHORITY = "software-first-save-guard";
    @FunctionalInterface private interface ObservationHook { CheckpointRequest.Readiness apply(CheckpointRequest.Readiness actual) throws IOException; }
    @FunctionalInterface private interface AdmissionHook { void apply(ContinuityStorePort.Session actual) throws IOException; }
    private static CheckpointRequest.Readiness observe(CheckpointRequest.ObservationPort port) throws IOException {
        try { return port.observe(Instant.now().plusSeconds(20)); }
        catch (InterruptedException failure) { Thread.currentThread().interrupt(); var wrapped = new InterruptedIOException("software checkpoint interrupted"); wrapped.initCause(failure); throw wrapped; }
    }
    private final class Fixture implements AutoCloseable {
        final ActionWriterIntegrationFixture actual;
        final RootLifecycleAuthority physical;
        final NativeReadinessCollector collector;
        final CheckpointRequest.ObservationPort first;
        final CheckpointRequest request;
        final ActionCommand command;
        final RootExecutableBindings bindings;
        final AtomicInteger admissionChecks = new AtomicInteger(), capabilityHooks = new AtomicInteger(), firstCaptures = new AtomicInteger();
        boolean rejectAdmission;
        ObservationHook observationHook = observed -> observed;
        AdmissionHook admissionHook = same -> { };
        Fixture(Path root, boolean advertiseSave) throws Exception {
            var scenario = new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64), "fixture-adapter", ref -> List.of(),
                    nativeRequest -> { throw new AssertionError("first SAVE guard may not issue a domain query"); }, Optional.empty(),
                    advertiseSave ? Set.of(SAVE_CAPABILITY) : Set.of());
            actual = new ActionWriterIntegrationFixture(root, false, scenario);
            var inputs = actual.physicalInputs(); var owner = actual.observationIdentity();
            inputs.driverAssembler().bindCapabilityObservation((frame, known) -> {
                capabilityHooks.incrementAndGet(); throw new AssertionError("first SAVE must skip actual Driver capability publication");
            });
            physical = new RootLifecycleAuthority(actual.writer, actual.archive, inputs.transport(), inputs.driverAssembler(),
                    inputs.observationAssembler(), inputs.source(), (same, held, source, packet, diagnostics, deadline) -> {
                        actual.writer.requireSession(same); assertEquals(inputs.source(), source); assertEquals(held, diagnostics.session().orElseThrow());
                        actual.archive.readArtifact(same, packet, WriterContracts.MAX_PIN_BYTES); return qualify(same);
                    }, Clock.systemUTC(), Duration.ofSeconds(30));
            collector = new NativeReadinessCollector(owner, actual.writer, inputs.transport(), inputs.driverAssembler(), inputs.observationAssembler(),
                    (game, deadline) -> new GameLifecycle.Running(game, inputs.source().sourceRef()),
                    (same, role, bytes) -> actual.archive.preserveArtifact(same, bytes, role.maximumBytes()),
                    new NativeSemanticEvidenceVerifier((same, ref, maximum) -> actual.archive.readArtifact(same, ref, maximum)),
                    (same, expected, frame, known, diagnostics, process, deadline) -> {
                        actual.writer.requireSession(same); assertEquals(owner, expected); assertEquals(inputs.source(), frame.source());
                        assertEquals(owner.game(), process.measured()); return qualify(same);
                    }, (same, frame, known, capabilities, deadline) -> { throw new AssertionError("six ordinary domains remain uninitialized before first SAVE"); },
                    (same, frame, known, capabilities, deadline) -> { throw new AssertionError("first SAVE cannot collect ordinary planning inputs"); },
                    new NativeReadiness.Policy(false, false, Optional.of(BigInteger.valueOf(73)), Duration.ZERO, false), Duration.ofSeconds(30), Clock.systemUTC());
            collector.bindObservationSession(actual.writer::requireSession); collector.bindActiveObservationSession(actual.writer::activeSession);
            collector.bindReadyPublication((same, original, frame, known, sources) -> { throw new AssertionError("first SAVE cannot publish ordinary Ready/M7"); });
            var rawFirst = collector.checkpointFirst("software-first-lineage", new NativeReadinessCollector.FirstCheckpointAdmission() {
                @Override public void requireStage(ContinuityStorePort.Session same,
                        org.xar.ck3.control.application.session.SessionPorts.SessionIdentity expected, Instant deadline) throws IOException {
                    actual.writer.requireSession(same); assertEquals(owner, expected); assertTrue(Instant.now().isBefore(deadline));
                }
                @Override public BigInteger requirePhysical(ContinuityStorePort.Session same,
                        org.xar.ck3.control.application.session.SessionPorts.SessionIdentity expected,
                        org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete frame,
                        org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known known,
                        org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence semantic,
                        NativeReadinessCollector.SourceQualification sources, Instant deadline) throws IOException {
                    requireStage(same, expected, deadline); assertEquals(frame.identity(), semantic.frame());
                    assertEquals(owner.game(), known.stamp().game()); assertEquals(inputs.source(), frame.source());
                    sources.guard().orElseThrow().assertCurrent(same); return known.driver().session().actorId();
                }
            });
            first = deadline -> {
                CheckpointRequest.Readiness observed = rawFirst.observe(deadline); firstCaptures.incrementAndGet();
                try { return observationHook.apply(observed); } catch (IOException failure) { throw new UncheckedIOException(failure); }
            };
            var opening = observe(first);
            request = new CheckpointRequestFactory(root.resolve("xar_checkpoint.ck3").toAbsolutePath(), first)
                    .prepare(opening.observed(), inputs.source(), owner.sessionId(), Optional.empty(), Instant.now().plusSeconds(20));
            command = request.saveCommand(); bindings = bindings(SAVE_CAPABILITY);
        }
        NativeReadinessCollector.SourceQualification qualify(ContinuityStorePort.Session same) throws IOException {
            actual.writer.requireSession(same); var source = actual.physicalInputs().source();
            var pin = same.capturePin(source.sourceRef(), WriterContracts.MAX_PIN_BYTES); same.verifyPin(pin);
            var body = StrictJson.object().put("schema", "xar.java-root-native-source-proof/v2").put("machine_id", source.machineId())
                    .put("session_id", actual.observationIdentity().sessionId()).put("scope", "software-only-no-live-package-or-game-grant");
            body.set("source", source.sourceRef().toJson());
            var proof = actual.archive.preserveArtifact(same, StrictJson.canonical(body), WriterContracts.MAX_PIN_BYTES);
            return new NativeReadinessCollector.SourceQualification(proof, current -> {
                actual.writer.requireSession(current); assertSame(same, current); current.verifyPin(pin);
            });
        }
        RootExecutableBindings bindings(String capability) {
            var source = actual.physicalInputs().source().sourceRef();
            var binding = NativeEffectRegistry.Binding.existing(RootSaveRuntime.OPERATION, source,
                    ignored -> { throw new AssertionError("guard regression must not prepare or submit SAVE"); },
                    (original, attempt, outcome) -> { throw new AssertionError("guard regression cannot claim native SAVE poststate"); });
            return RootExecutableBindings.freeze(List.of(new RootExecutableBindings.ActionBinding(binding,
                    ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, Optional.of(capability), source)), RootReadContractCatalog.staticOnly(List.of()), List.of(), 16);
        }
        void admit(ContinuityStorePort.Session same, WriterContracts.Head head, ActionCommand retained) throws IOException {
            actual.writer.requireSession(same); assertEquals(head.digest(), same.head().digest()); assertSame(command, retained);
            admissionChecks.incrementAndGet(); if (rejectAdmission) throw new IOException("software private stage admission was withdrawn");
            admissionHook.apply(same);
        }
        RootFirstCheckpointGuard guard() { return guard(bindings, first, Clock.systemUTC()); }
        RootFirstCheckpointGuard guard(RootExecutableBindings bindings, CheckpointRequest.ObservationPort observations, Clock clock) {
            return new RootFirstCheckpointGuard(actual.writer, actual.archive, physical, bindings, actual.observationIdentity(),
                    actual.physicalInputs().source(), observations, command, this::admit, clock, AUTHORITY);
        }
        @Override public void close() throws IOException { actual.close(); }
    }

    @Test void actualSharedSaveRequestProducesSingleV3PhysicalGuardAndReplaysItsOwnArchivedOriginals() throws Exception {
        try (var f = new Fixture(temporary.resolve("actual-guard"), true)) {
            var guard = f.guard();
            f.actual.writer.locked(same -> {
                var head = same.head(); int samples = f.firstCaptures.get(), reads = f.actual.nativeReadWrites(), packets = f.actual.nativePacketReads();
                GuardEvidence result = guard.verify(head, f.command); var archive = f.actual.archive.withSession(same);
                assertEquals(f.command.before(), result.observed()); assertEquals(f.command.source(), result.source());
                assertEquals(RootSaveRuntime.OPERATION, result.operation()); assertEquals(AUTHORITY, result.authorityId());
                assertEquals(1, result.supportingEvidence().size()); assertEquals(samples + 1, f.firstCaptures.get());
                assertTrue(f.actual.nativePacketReads() >= packets + 2, "stable producer and raw physical lease are distinct real captures");
                int after = f.actual.nativePacketReads();
                var frame = RootGuardEvidence.loadFrame(result, archive, f.actual.physicalInputs().frameLoader());
                assertEquals(result.observed(), frame.identity());
                RootGuardEvidence.requireHistory(result, archive, same);
                assertEquals(head.digest(), RootGuardEvidence.writerPoint(result, archive).digest());
                var originals = RootGuardEvidence.originalDriverSource(result, archive);
                assertTrue(archive.loadMaterial(originals.driverRef()).bytes().length > 0);
                assertTrue(archive.loadMaterial(originals.stampRef()).bytes().length > 0);
                assertEquals(after, f.actual.nativePacketReads(), "replay issues no Native I/O"); assertEquals(reads, f.actual.nativeReadWrites());
                assertEquals(head.digest(), same.head().digest()); return null;
            });
            assertTrue(f.admissionChecks.get() >= 4); assertEquals(0, f.capabilityHooks.get());
            assertNull(f.actual.lastPublishedReady.get()); assertEquals(0, f.actual.nativeActionWrites());
        }
    }

    @Test void distinctRealFramedPacketsForTheSameCheckedNativeStateAreVerifiedWithoutInventingASharedReference() throws Exception {
        try (var f = new Fixture(temporary.resolve("two-originals"), true)) {
            final ExactRef[] firstOriginal = new ExactRef[1];
            f.observationHook = ready -> {
                var same = f.actual.writer.borrowedSession(); byte[] original = f.actual.archive.readArtifact(same, ready.nativeEvidence(), WriterContracts.MAX_PIN_BYTES);
                byte[] payload = Arrays.copyOfRange(original, 4, original.length);
                byte[] independent = NativeWire.packet(("\n" + new String(payload, StandardCharsets.UTF_8) + "\n").getBytes(StandardCharsets.UTF_8));
                assertFalse(Arrays.equals(original, independent)); firstOriginal[0] = ready.nativeEvidence();
                f.actual.enqueueSoftwareNativePacket(independent); return ready;
            };
            f.actual.writer.locked(same -> {
                GuardEvidence result = f.guard().verify(same.head(), f.command);
                assertNotEquals(firstOriginal[0], result.nativeEvidence(), "guard must preserve the actual second original independently");
                var archive = f.actual.archive.withSession(same);
                assertEquals(result.observed(), RootGuardEvidence.loadFrame(result, archive, f.actual.physicalInputs().frameLoader()).identity());
                RootGuardEvidence.requireHistory(result, archive, same); return null;
            });
            assertEquals(0, f.capabilityHooks.get()); assertEquals(0, f.actual.nativeActionWrites());
        }
    }

    @Test void anotherCommandExpiredDeadlineForeignHeadAndMissingWriterRefuseBeforeNativeIo() throws Exception {
        try (var f = new Fixture(temporary.resolve("wrong-owner"), true);
             var other = new Fixture(temporary.resolve("other-owner"), true)) {
            var guard = f.guard(); int packets = f.actual.nativePacketReads();
            assertThrows(UncheckedIOException.class, () -> guard.verify(f.actual.writer.locked(same -> same.head()), f.command));
            var changed = new ActionCommand(f.command.actionId() + "-different", f.command.before(), f.command.source(), f.command.sessionId(),
                    f.command.operation(), f.command.arguments(), f.command.expected(), f.command.claims(), f.command.deadline());
            var foreign = other.actual.writer.locked(same -> same.head());
            f.actual.writer.locked(same -> {
                assertThrows(IllegalArgumentException.class, () -> guard.verify(same.head(), changed));
                assertThrows(IllegalArgumentException.class, () -> guard.verify(foreign, f.command));
                var expired = f.guard(f.bindings, f.first, Clock.fixed(f.command.deadline().plusSeconds(1), ZoneOffset.UTC));
                assertThrows(IllegalArgumentException.class, () -> expired.verify(same.head(), f.command)); return null;
            });
            assertEquals(packets, f.actual.nativePacketReads()); assertEquals(0, f.actual.nativeActionWrites());
        }
    }

    @Test void absentPrivateAdmissionUnstableReadinessAndWrongInstalledCapabilityCannotGrantSave() throws Exception {
        try (var f = new Fixture(temporary.resolve("admission"), true)) {
            var guard = f.guard(); f.rejectAdmission = true; int packets = f.actual.nativePacketReads();
            f.actual.writer.locked(same -> { assertThrows(UncheckedIOException.class, () -> guard.verify(same.head(), f.command)); return null; });
            assertEquals(packets, f.actual.nativePacketReads()); f.rejectAdmission = false;
            assertThrows(IllegalArgumentException.class, () -> f.guard(f.bindings("game.command.pause-map"), f.first, Clock.systemUTC()));
            f.observationHook = ready -> new CheckpointRequest.Readiness(ready.observed(), ready.source(), ready.sessionId(), ready.lineageId(),
                    ready.mapReady(), ready.paused(), false, "actual stable gate is not ready", ready.nativeEvidence(), ready.observedAt());
            f.actual.writer.locked(same -> { assertThrows(IllegalArgumentException.class, () -> guard.verify(same.head(), f.command)); return null; });
            f.observationHook = ready -> ready;
            f.actual.writer.locked(same -> { assertEquals(f.command.before(), guard.verify(same.head(), f.command).observed()); return null; });
            assertEquals(0, f.capabilityHooks.get()); assertEquals(0, f.actual.nativeActionWrites());
        }
    }

    @Test void actualHelloWithoutSaveCapabilityRefusesEvenWhenPhysicalMapIsEligible() throws Exception {
        try (var f = new Fixture(temporary.resolve("missing-save-cap"), false)) {
            f.actual.writer.locked(same -> { assertThrows(IllegalArgumentException.class, () -> f.guard().verify(same.head(), f.command)); return null; });
            assertEquals(0, f.actual.nativeReadWrites()); assertEquals(0, f.actual.nativeActionWrites()); assertEquals(0, f.capabilityHooks.get());
        }
    }

    @Test void changedActualSourceInsidePrivatePhysicalScopeCannotReturnGuardEvidence() throws Exception {
        try (var f = new Fixture(temporary.resolve("source-drift"), true)) {
            f.admissionHook = same -> {
                if (f.admissionChecks.get() == 3) Files.writeString(Path.of(f.command.source().sourceRef().path()), "changed true source inside physical admission");
            };
            f.actual.writer.locked(same -> { assertThrows(UncheckedIOException.class, () -> f.guard().verify(same.head(), f.command)); return null; });
            assertTrue(f.admissionChecks.get() >= 3); assertEquals(0, f.actual.nativeActionWrites()); assertNull(f.actual.lastPublishedReady.get());
        }
    }
}
