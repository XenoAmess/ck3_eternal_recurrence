package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.Arrays;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceQualification;
import org.xar.ck3.control.service.root.RootLifecycleAuthority;

/** Actual already-accepted packet -> sole physical qualifier. Controlled software edges grant no live qualification. */
final class RootReceivedSnapshotAuthorityTest {
    @TempDir Path temporary;
    private static RootLifecycleAuthority physical(ActionWriterIntegrationFixture actual, AtomicInteger sourceChecks) {
        var inputs = actual.physicalInputs();
        return new RootLifecycleAuthority(actual.writer, actual.archive, inputs.transport(), inputs.driverAssembler(),
                inputs.observationAssembler(), inputs.source(), (same, session, source, packet, received, deadline) -> {
                    actual.writer.requireSession(same); assertEquals(inputs.source(), source);
                    assertEquals(session, received.session().orElseThrow()); assertEquals(actual.observationIdentity().game(), session.game());
                    var sourcePin = same.capturePin(source.sourceRef(), 65_536);
                    var packetPin = same.capturePin(packet, 64 * 1024 * 1024 + 4);
                    same.verifyPin(sourcePin); same.verifyPin(packetPin);
                    return new SourceQualification(source.sourceRef(), original -> {
                        assertSame(same, original); actual.writer.requireSession(original);
                        original.verifyPin(sourcePin); original.verifyPin(packetPin); sourceChecks.incrementAndGet();
                    });
                }, Clock.systemUTC(), Duration.ofSeconds(30));
    }
    private static ObservedFrame accepted(ActionWriterIntegrationFixture actual) throws IOException {
        return actual.physicalInputs().transport().currentSnapshot(Instant.now().plusSeconds(10));
    }

    @Test void exactAcceptedOriginalUsesSharedFullDriverSourceAndSemanticsWithZeroAdditionalNativeReads() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("accepted"), false)) {
            actual.ready(); var sourceChecks = new AtomicInteger(); var authority = physical(actual, sourceChecks);
            ObservedFrame original = accepted(actual); int reads = actual.nativePacketReads(); byte[] head = actual.ledgerBytes();
            AtomicReference<RootLifecycleAuthority.SnapshotLease> escaped = new AtomicReference<>();
            actual.writer.locked(same -> authority.withReceivedSnapshot(same, Instant.now().plusSeconds(10), original, lease -> {
                lease.assertCurrent(same); escaped.set(lease);
                assertEquals(original.session(), lease.fullSnapshot().actual().session());
                assertEquals(original.observedAt(), lease.fullSnapshot().actual().observedAt());
                assertArrayEquals(original.originalPacket(), lease.fullSnapshot().actual().originalPacket());
                assertArrayEquals(lease.factsKnown().driver().encode(), actual.archive.readArtifact(same, lease.originalDriver(), 64 << 20));
                var semantic = authority.semantic(same, actual.observationIdentity(), lease);
                assertEquals(lease.originalDriver(), semantic.originalDriver());
                assertEquals(lease.fullSnapshot().originalEvidence(), semantic.originalNativePacket());
                assertEquals(DriverJson.sha256(lease.factsKnown().driver().encode()), lease.originalDriver().sha256());
                assertEquals(reads, actual.nativePacketReads()); return null;
            }));
            actual.writer.locked(same -> { assertThrows(IllegalArgumentException.class, () -> escaped.get().assertCurrent(same)); return null; });
            assertEquals(reads, actual.nativePacketReads()); assertArrayEquals(head, actual.ledgerBytes()); assertTrue(sourceChecks.get() >= 2);
            // The original independent sampling method keeps its existing Native receive semantics.
            actual.writer.locked(same -> authority.withSnapshot(same, Instant.now().plusSeconds(10), lease -> { lease.assertCurrent(same); return null; }));
            assertTrue(actual.nativePacketReads() > reads);
        }
    }

    @Test void copiedWrongSessionTimeStateAndPacketRejectBeforeSourceQualificationOrNativeRead() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("mismatch"), false)) {
            actual.ready(); var sourceChecks = new AtomicInteger(); var authority = physical(actual, sourceChecks);
            ObservedFrame original = accepted(actual); int reads = actual.nativePacketReads();
            var session = original.session();
            var foreign = new TransportSession(session.machineId(), session.game(), session.connectionGeneration(), session.sessionId() + "-foreign");
            byte[] altered = original.originalPacket(); altered[altered.length - 1] ^= 1;
            var wrong = java.util.List.of(
                    new ObservedFrame(foreign, original.snapshotId(), original.nativeRevision(), original.state(), original.originalPacket(), original.observedAt()),
                    new ObservedFrame(session, original.snapshotId(), original.nativeRevision(), original.state(), original.originalPacket(), original.observedAt().minusNanos(1)),
                    new ObservedFrame(session, original.snapshotId(), original.nativeRevision(), new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8)), original.originalPacket(), original.observedAt()),
                    new ObservedFrame(session, original.snapshotId(), original.nativeRevision(), original.state(), altered, original.observedAt()));
            for (var frame : wrong) actual.writer.locked(same -> {
                assertThrows(IllegalArgumentException.class, () -> authority.withReceivedSnapshot(same, Instant.now().plusSeconds(10), frame,
                        ignored -> fail("a copied changed original cannot reach the physical consumer"))); return null;
            });
            actual.writer.locked(same -> {
                assertThrows(IllegalArgumentException.class, () -> authority.withReceivedSnapshot(same, Instant.now().minusSeconds(1), original,
                        ignored -> fail("expired input cannot reach physical consumer"))); return null;
            });
            assertEquals(0, sourceChecks.get()); assertEquals(reads, actual.nativePacketReads());
        }
    }

    @Test void identicalCopiedDataCannotBorrowTheActualAcceptedOccurrenceOrReachItsSourceQualifier() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("copied-occurrence"), false)) {
            actual.ready(); var sourceChecks = new AtomicInteger(); var authority = physical(actual, sourceChecks);
            ObservedFrame original = accepted(actual);
            var copied = new ObservedFrame(original.session(), original.snapshotId(), original.nativeRevision(), original.state(),
                    original.originalPacket(), original.observedAt());
            assertNotSame(original, copied); assertEquals(original.session(), copied.session());
            assertEquals(original.observedAt(), copied.observedAt()); assertArrayEquals(original.originalPacket(), copied.originalPacket());
            int reads = actual.nativePacketReads(); byte[] head = actual.ledgerBytes();
            actual.writer.locked(same -> {
                assertThrows(IOException.class, () -> authority.withReceivedSnapshot(same, Instant.now().plusSeconds(10), copied,
                        ignored -> fail("identical copied DATA is not an actual accepted receive occurrence")));
                assertEquals(0, sourceChecks.get());
                return null;
            });
            assertEquals(reads, actual.nativePacketReads()); assertArrayEquals(head, actual.ledgerBytes());
            actual.writer.locked(same -> authority.withReceivedSnapshot(same, Instant.now().plusSeconds(10), original, lease -> {
                lease.assertCurrent(same);
                assertSame(original, lease.fullSnapshot().actual());
                assertThrows(IOException.class, () -> authority.withReceivedSnapshot(same, Instant.now().plusSeconds(10), copied,
                        ignored -> fail("a nested active source scope cannot grant a copied receive occurrence")));
                return null;
            }));
            assertTrue(sourceChecks.get() >= 2); assertEquals(reads, actual.nativePacketReads());
            assertEquals(0, actual.nativeActionWrites()); assertArrayEquals(head, actual.ledgerBytes());
        }
    }

    @Test void actualConsumerFailureClosesScopeAndActualSourceCorruptionFailsRevalidationWithoutSampling() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("failure"), false)) {
            actual.ready(); var authority = physical(actual, new AtomicInteger()); var original = accepted(actual);
            int reads = actual.nativePacketReads(); AtomicReference<RootLifecycleAuthority.SnapshotLease> escaped = new AtomicReference<>();
            actual.writer.locked(same -> {
                IOException failure = assertThrows(IOException.class, () -> authority.withReceivedSnapshot(same, Instant.now().plusSeconds(10), original,
                        lease -> { escaped.set(lease); throw new IOException("actual received consumer failure"); }));
                assertEquals("actual received consumer failure", failure.getMessage());
                assertThrows(IllegalArgumentException.class, () -> escaped.get().assertCurrent(same)); return null;
            });
            actual.writer.locked(same -> authority.withReceivedSnapshot(same, Instant.now().plusSeconds(10), original,
                    lease -> { lease.assertCurrent(same); return null; }));
            var source = actual.observationSource().sourceRef(); Path path = Path.of(source.path()).toAbsolutePath().normalize();
            assertTrue(path.startsWith(actual.root.toAbsolutePath().normalize())); byte[] bytes = Files.readAllBytes(path);
            assertThrows(IOException.class, () -> actual.writer.locked(same -> authority.withReceivedSnapshot(same, Instant.now().plusSeconds(10), original,
                    lease -> { Files.write(path, Arrays.copyOf(bytes, bytes.length + 1)); return null; })));
            assertEquals(reads, actual.nativePacketReads());
        }
    }
}
