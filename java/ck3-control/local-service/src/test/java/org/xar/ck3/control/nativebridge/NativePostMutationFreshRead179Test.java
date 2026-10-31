package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactCk3Build;

/** Actual software writer/coordinator -> mutation ACK -> same held receiver's independent READ/ACK.
 * No live Game authority, synthetic permit or constructed Received. */
final class NativePostMutationFreshRead179Test {
    @TempDir Path root;
    private ActionWriterIntegrationFixture fixture(String mode) throws Exception {
        var profile = new ActionWriterIntegrationFixture.SoftwareReadScenario(
                ExactCk3Build.CK3_12004.executableSha256(), "ck3-1.20.0.4-msvc-x64",
                ignored -> List.of(), ignored -> { throw new AssertionError("no additional ordinary READ installed"); },
                Optional.of(ExactCk3Build.CK3_12004.version()), Set.of(NativeFreshSnapshotPort.CAPABILITY));
        var fixture = new ActionWriterIntegrationFixture(root.resolve(mode), false, profile);
        fixture.configureSoftwareFreshRead179(mode); return fixture;
    }
    private static Instant deadline() { return Instant.now().plusSeconds(15); }
    @Test void actualMutationAckThenNoNewPushStillReceivesIndependentFreshPacketAndAck() throws Exception {
        try (var fixture = fixture("success")) {
            var command = fixture.command("post-mutation-success179");
            var transport = fixture.physicalInputs().transport();
            var originalBefore = transport.currentSnapshot(deadline());
            var receipt = fixture.coordinator.execute(command);
            var setter = receipt.ack().orElseThrow(); assertTrue(setter.nativeOk());
            assertEquals(1, fixture.nativeActionWrites());
            assertInstanceOf(ActionState.Unknown.class, receipt.state(), "an original ACK alone is not an applied effect");
            byte[] ledger = fixture.ledgerBytes();
            var result = assertInstanceOf(NativeFreshSnapshotPort.Received.class, transport.readFreshFullState(deadline()));
            NativeFreshSnapshotPort.verifyAfter(setter, result);
            assertEquals(originalBefore.session(), result.originalFrame().session());
            assertNotEquals(originalBefore.snapshotId(), result.originalFrame().snapshotId());
            assertArrayEquals(fixture.softwareFreshSnapshot179(), result.originalFrame().originalPacket());
            assertArrayEquals(fixture.softwareFreshAck179(), result.acknowledgement().originalPacket());
            assertNotEquals(setter.requestId(), result.acknowledgement().requestId());
            assertTrue(result.acknowledgement().custody().orElseThrow().writeEntered().order()
                    .compareTo(setter.custody().orElseThrow().responseReceived().order()) > 0);
            var marker = NativeWire.object(NativeWire.parse(java.util.Arrays.copyOfRange(result.originalFrame().originalPacket(), 4,
                    result.originalFrame().originalPacket().length))).path("read_request_id").textValue();
            assertEquals(result.acknowledgement().requestId(), marker);
            assertSame(result.originalFrame(), transport.observe(deadline(), Duration.ofMinutes(1)),
                    "cache becomes usable only after actual snapshot plus matching ACK");
            assertEquals(1, fixture.softwareFreshWrites179()); assertEquals(0, fixture.softwareEmptyAfterMutation179());
            assertArrayEquals(ledger, fixture.ledgerBytes());
            assertEquals(receipt, fixture.coordinator.execute(command)); assertEquals(1, fixture.nativeActionWrites());
        }
    }
    @Test void missingOrInvalidFreshAckKeepsPostMutationCacheUnavailableAndNeverReplaysMutation() throws Exception {
        for (String mode : List.of("missing-ack", "mismatched-ack", "negative-ack")) {
            try (var fixture = fixture(mode)) {
                var command = fixture.command("post-mutation-" + mode + "179");
                var transport = fixture.physicalInputs().transport();
                var before = transport.currentSnapshot(deadline());
                var receipt = fixture.coordinator.execute(command); assertTrue(receipt.ack().orElseThrow().nativeOk());
                assertEquals(1, fixture.nativeActionWrites()); byte[] ledger = fixture.ledgerBytes();
                var unavailable = assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class, transport.readFreshFullState(deadline()), mode);
                assertTrue(unavailable.originalFrame().isPresent(), "real request-marked packet arrived before failed/missing ACK");
                assertNotEquals(before.snapshotId(), unavailable.originalFrame().orElseThrow().snapshotId());
                assertThrows(java.io.UncheckedIOException.class, () -> transport.observe(deadline(), Duration.ofMinutes(1)), mode);
                if (!mode.equals("negative-ack")) {
                    var retained = assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class, transport.readFreshFullState(deadline()));
                    assertSame(unavailable.dispatch(), retained.dispatch()); assertEquals(1, fixture.softwareFreshWrites179());
                }
                assertEquals(receipt, fixture.coordinator.execute(command)); assertEquals(1, fixture.nativeActionWrites());
                assertArrayEquals(ledger, fixture.ledgerBytes());
            }
        }
    }
}
