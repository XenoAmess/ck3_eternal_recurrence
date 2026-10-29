package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicBoolean;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Actual collector/writer/received-source regression. Controlled software packets grant no native/Game qualification. */
final class NativeHeldReadOccurrenceTest {
    @TempDir Path temporary;
    private static final String SHA = "ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d";

    private ActionWriterIntegrationFixture fixture(String name) throws IOException {
        var scenario = new ActionWriterIntegrationFixture.SoftwareReadScenario(SHA, "held-occurrence-software",
                ignored -> List.of(), ignored -> new RawJson(new byte[] {'{', '}'}), Optional.empty(), Set.of());
        return new ActionWriterIntegrationFixture(temporary.resolve(name), false, scenario,
                Clock.fixed(Instant.now(), ZoneOffset.UTC));
    }
    private static PlanningReadRequest original(ActionWriterIntegrationFixture actual, ActionCommand basis) {
        return new PlanningReadRequest(basis.before(), basis.source(), basis.sessionId(),
                actual.readContract.operation(), new Obj(java.util.Map.of()), basis.deadline());
    }
    private static ObservedFrame receive(NativeGameTransport transport, Instant deadline) throws IOException {
        try { return transport.observe(deadline); }
        catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt(); throw new IOException("controlled packet receive interrupted", interrupted);
        }
    }

    @Test void sameAcceptedOccurrenceCanBeBorrowedAndNestedWithoutAnotherRead() throws Exception {
        try (var actual = fixture("same-occurrence")) {
            var basis = actual.command("unsubmitted-held-source-basis");
            var request = original(actual, basis);
            int reads = actual.nativeReadWrites();
            actual.writer.locked(same -> actual.collector.withHeldReadScope(same, actual.observationIdentity(), basis.deadline(), frame -> {
                var transport = actual.physicalInputs().transport();
                var received = transport.currentSnapshot(basis.deadline());
                var token = transport.acceptedSnapshotRevision(received);
                actual.collector.currentHeldOriginal(same, request, lease -> {
                    assertSame(frame, lease.frame()); return null;
                });
                actual.collector.withHeldReadScope(same, actual.observationIdentity(), basis.deadline(), nested -> {
                    assertSame(frame, nested);
                    token.requireOriginal(transport.currentSnapshot(basis.deadline()));
                    actual.collector.currentHeldOriginal(same, request, lease -> {
                        assertSame(frame, lease.frame()); return null;
                    });
                    return null;
                });
                assertSame(received, transport.currentSnapshot(basis.deadline()));
                return null;
            }));
            assertEquals(reads, actual.nativeReadWrites(), "nested held verification must not dispatch a READ");
            assertEquals(0, actual.nativeActionWrites());
            actual.writer.locked(same -> {
                assertThrows(RuntimeException.class,
                        () -> actual.collector.currentHeldOriginal(same, request, ignored -> null),
                        "the actual physical source must expire with its callback");
                return null;
            });
        }
    }

    @Test void fixedClockAbaCannotReuseEqualPacketAndObservedTimeAsTheOriginalHeldSource() throws Exception {
        try (var actual = fixture("fixed-clock-aba")) {
            var basis = actual.command("unsubmitted-aba-source-basis");
            var request = original(actual, basis);
            int reads = actual.nativeReadWrites();
            var rejectedInside = new AtomicBoolean();
            assertThrows(IOException.class, () -> actual.writer.locked(same ->
                    actual.collector.withHeldReadScope(same, actual.observationIdentity(), basis.deadline(), frame -> {
                        var transport = actual.physicalInputs().transport();
                        var first = transport.currentSnapshot(basis.deadline());
                        var firstToken = transport.acceptedSnapshotRevision(first);
                        actual.collector.currentHeldOriginal(same, request, lease -> null);
                        byte[] originalPacket = first.originalPacket();
                        var middle = (ObjectNode) StrictJson.parse(Arrays.copyOfRange(originalPacket, 4, originalPacket.length));
                        middle.put("snapshot_id", first.snapshotId() + "-middle");
                        // Keep the native revision nondecreasing while the receiver sees genuinely different semantic DATA.
                        ((ObjectNode) middle.get("state")).putObject("played_character_gold").put("raw", 1).put("scale", 100000);
                        actual.enqueueSoftwareNativePacket(NativeWire.packet(StrictJson.canonical(middle)));
                        var changed = receive(transport, basis.deadline());
                        assertNotSame(first, changed);
                        assertEquals(first.snapshotId() + "-middle", changed.snapshotId(), "the actual legal B packet must be accepted");
                        assertEquals(first.nativeRevision(), changed.nativeRevision());
                        actual.enqueueSoftwareNativePacket(originalPacket);
                        var last = receive(transport, basis.deadline());
                        assertNotSame(first, last);
                        assertEquals(first.session(), last.session());
                        assertEquals(first.snapshotId(), last.snapshotId());
                        assertEquals(first.nativeRevision(), last.nativeRevision());
                        assertEquals(first.observedAt(), last.observedAt());
                        assertArrayEquals(first.originalPacket(), last.originalPacket());
                        assertSame(firstToken, transport.acceptedSnapshotRevision(first));
                        var lastToken = transport.acceptedSnapshotRevision(last);
                        assertTrue(lastToken.received().order().compareTo(firstToken.received().order()) > 0);
                        assertThrows(IOException.class,
                                () -> actual.collector.currentHeldOriginal(same, request, lease -> null),
                                "equal DATA must not replace the actual physical source occurrence");
                        rejectedInside.set(true);
                        return null;
                    })));
            assertTrue(rejectedInside.get(), "the post-ABA admission must reject inside the real held callback");
            assertEquals(reads, actual.nativeReadWrites(), "ABA rejection cannot refresh or replay a READ");
            assertEquals(0, actual.nativeActionWrites());
            assertTrue(actual.physicalInputs().transport().mailboxDiagnostics().poison().isEmpty());
        }
    }
}
