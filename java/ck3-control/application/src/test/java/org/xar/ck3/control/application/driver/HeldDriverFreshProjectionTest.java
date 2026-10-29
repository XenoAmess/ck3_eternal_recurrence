package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.time.Instant;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort;

/** Explicit original received-frame projection; freshness proof remains with the actual fresh READ port. */
final class HeldDriverFreshProjectionTest {
    private static final Instant DEADLINE = Instant.parse("2030-01-01T00:00:00Z");

    private static HeldDriverObservationPort held(AtomicInteger transportReads, AtomicInteger factsReads,
            AtomicInteger preserved) {
        return new HeldDriverObservationPort(deadline -> {
            transportReads.incrementAndGet();
            throw new AssertionError("received-frame projection must not observe or replace its supplied frame");
        }, actual -> {
            factsReads.incrementAndGet();
            return new DriverObservationFacts.Known(DriverObservationAssemblerTest.facts(actual));
        }, actual -> {
            preserved.incrementAndGet();
            return DriverStateAssemblerTest.ref(actual.originalPacket());
        }, new DriverObservationAssembler(), 2);
    }

    @Test void projectsOriginalReceivedFrameThroughSameFactsEvidenceAndRetainsExactComplete() throws IOException {
        var transportReads = new AtomicInteger();
        var factsReads = new AtomicInteger();
        var preserved = new AtomicInteger();
        var port = held(transportReads, factsReads, preserved);
        var received = DriverObservationAssemblerTest.actual(DriverObservationAssemblerTest.STATE);
        var complete = port.project(received, DEADLINE);
        assertEquals(0, transportReads.get());
        assertEquals(1, factsReads.get());
        assertEquals(1, preserved.get());
        assertEquals(received.observedAt(), complete.observedAt());
        assertEquals(received.snapshotId(), complete.identity().frame().snapshotId());
        assertEquals(received.nativeRevision(), complete.identity().frame().identity().nativeRevision());
        assertEquals(DriverStateAssemblerTest.ref(received.originalPacket()), complete.originalEvidence());
        assertSame(complete, port.requireRetained(complete.identity(), complete.originalEvidence()));
        var context = DriverPublicContext.from(complete);
        assertEquals(complete.semantic(), PublicSnapshotCodec.decode(context.snapshot()));
        assertEquals(0, transportReads.get());
    }

    @Test void fullProjectionKeepsOriginalFrameObjectAndNeverInventsLivingIdentity() throws IOException {
        var reads = new AtomicInteger();
        var facts = new AtomicInteger();
        var evidence = new AtomicInteger();
        var port = held(reads, facts, evidence);
        var received = DriverObservationAssemblerTest.actual(DriverObservationAssemblerTest.STATE
                .replace("{\"character_id\":73,\"alive\":true}", "null"));
        var full = port.projectFull(received, DEADLINE);
        assertSame(received, full.actual());
        assertEquals(received.observedAt(), full.actual().observedAt());
        assertThrows(IllegalStateException.class, () -> port.project(received, DEADLINE));
        assertEquals(0, reads.get());
    }

    @Test void expiredDeadlineFailsBeforeArchiveAndMissingFactsStayExplicit() {
        var reads = new AtomicInteger();
        var facts = new AtomicInteger();
        var preserved = new AtomicInteger();
        var received = DriverObservationAssemblerTest.actual(DriverObservationAssemblerTest.STATE);
        var port = held(reads, facts, preserved);
        assertThrows(IllegalArgumentException.class, () -> port.project(received, Instant.EPOCH));
        assertEquals(0, facts.get());
        assertEquals(0, preserved.get());
        var unavailable = new HeldDriverObservationPort(deadline -> {
            throw new AssertionError("unavailable facts must not fall back to another observation");
        }, actual -> new DriverObservationFacts.Unavailable(List.of("actual Driver facts unavailable")),
                actual -> DriverStateAssemblerTest.ref(actual.originalPacket()), new DriverObservationAssembler(), 2);
        IOException failure = assertThrows(IOException.class, () -> unavailable.project(received, DEADLINE));
        assertTrue(failure.getMessage().contains("actual Driver facts unavailable"));
    }

    @Test void changedPacketOrArchiveIdentityCannotReplaceOriginalReceivedEvidence() {
        var received = DriverObservationAssemblerTest.actual(DriverObservationAssemblerTest.STATE);
        byte[] packet = received.originalPacket();
        packet[0] ^= 1;
        var invalid = new NativeObservationPort.ObservedFrame(received.session(), received.snapshotId(),
                received.nativeRevision(), received.state(), packet, received.observedAt());
        var port = held(new AtomicInteger(), new AtomicInteger(), new AtomicInteger());
        assertThrows(IllegalArgumentException.class, () -> port.project(invalid, DEADLINE));
        var wrongArchive = new HeldDriverObservationPort(deadline -> {
            throw new AssertionError("archive mismatch must not observe again");
        }, actual -> new DriverObservationFacts.Known(DriverObservationAssemblerTest.facts(actual)),
                actual -> DriverStateAssemblerTest.ref(DriverStateAssemblerTest.bytes("different original packet")),
                new DriverObservationAssembler(), 2);
        assertThrows(IllegalArgumentException.class, () -> wrongArchive.project(received, DEADLINE));
    }
}
