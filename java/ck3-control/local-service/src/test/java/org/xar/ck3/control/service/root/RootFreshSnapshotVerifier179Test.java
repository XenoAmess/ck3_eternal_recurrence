package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverStateAssembler;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * Regression test for RootAdvanceInfrastructureFactory.verifyFreshSnapshotQuery.
 * Uses actual fixture-generated data and the production wrapper.
 */
final class RootFreshSnapshotVerifier179Test {
    @TempDir Path root;

    private ActionWriterIntegrationFixture createFixture(String suffix) throws IOException {
        var profile = new ActionWriterIntegrationFixture.SoftwareReadScenario(
                ExactCk3Build.CK3_12004.executableSha256(), "ck3-1.20.0.4-msvc-x64",
                ignored -> List.of(), ignored -> { throw new AssertionError("no additional ordinary READ installed"); },
                Optional.of(ExactCk3Build.CK3_12004.version()), Set.of(NativeFreshSnapshotPort.CAPABILITY));
        var fixture = new ActionWriterIntegrationFixture(root.resolve(suffix), false, profile);
        fixture.configureSoftwareFreshRead179("success");
        return fixture;
    }

    @Test void actualFreshSnapshotQueryVerificationPassesAndNegativesFail() throws Exception {
        try (var fixture = createFixture("verifier-test")) {
            var command = fixture.command("verifier-action");
            var transport = fixture.physicalInputs().transport();

            // 1. Execute mutation to get setter ACK
            var receipt = fixture.coordinator.execute(command);
            var setterAck = receipt.ack().orElseThrow();
            assertTrue(setterAck.nativeOk());

            // 2. Perform actual fresh read
            var readResult = transport.readFreshFullState(Instant.now().plusSeconds(15));
            var received = assertInstanceOf(NativeFreshSnapshotPort.Received.class, readResult);

            // 3. Verify relationship
            NativeFreshSnapshotPort.verifyAfter(setterAck, received);

            // 4. Preserve actual ACKs in archive
            var setterRef = fixture.archive.preserve(setterAck);
            var readAckRef = fixture.archive.preserve(received.acknowledgement());

            // 5. Obtain REAL DriverObservationAssembler.Complete from actual received frame
            var complete = fixture.writer.locked(same -> {
                var driver = fixture.driverAuthority();
                var assembler = fixture.physicalInputs().observationAssembler();
                var frame = received.originalFrame();
                var nativeRef = fixture.archive.preserveNativeFrame(frame);
                return driver.withFrozenRawObservation(frame, same, frozen -> {
                    var result = assembler.assemble(frame, frozen.facts(), nativeRef);
                    assertInstanceOf(DriverObservationAssembler.Complete.class, result);
                    return (DriverObservationAssembler.Complete) result;
                });
            });

            // 6. Build new FreshSnapshotQuery with actual event/refs/LiveAfterSetter
            var requestId = received.acknowledgement().requestId();
            var snapshotReceived = received.snapshotReceived();
            var basis = new ObservationProvenance.LiveAfterSetter(setterRef);
            var query = new ObservationProvenance.FreshSnapshotQuery(
                    requestId, readAckRef, snapshotReceived, basis);

            // 7. Positive: invoke ACTUAL production wrapper verifyFreshSnapshotQuery
            var loader = RootAdvanceInfrastructureFactory.freshFrameLoader(fixture.frameLoader());
            loader.verifyFreshSnapshotQuery(query, complete, fixture.archive);

            // 8. Negative: Default original FrameLoader without installed new callback should refuse
            var defaultLoader = fixture.frameLoader();
            assertThrows(IllegalStateException.class, () -> defaultLoader.verifyFreshSnapshotQuery(query, complete, fixture.archive));

            // 9. Negative: actual setter ACK ref substituted for read ACK
            var badQuery1 = new ObservationProvenance.FreshSnapshotQuery(
                    requestId, setterRef, snapshotReceived, basis);
            assertThrows(IllegalArgumentException.class, () -> loader.verifyFreshSnapshotQuery(badQuery1, complete, fixture.archive));

            // 10. Negative: actual read's real writeEntered event substituted for snapshotReceived
            var badEvent = received.acknowledgement().custody().orElseThrow().writeEntered();
            var badQuery2 = new ObservationProvenance.FreshSnapshotQuery(
                    requestId, readAckRef, badEvent, basis);
            assertThrows(java.io.UncheckedIOException.class, () -> loader.verifyFreshSnapshotQuery(badQuery2, complete, fixture.archive));

            // A second real receiver has a distinct custody epoch, even if HELLO fields coincide.
            // Its own read/frame is valid; only the setter comes from the first held receiver.
            try (var alien = createFixture("alien-receiver")) {
                var alienReceipt = alien.coordinator.execute(alien.command("alien-action"));
                var alienSetter = alienReceipt.ack().orElseThrow();
                var alienReceived = assertInstanceOf(NativeFreshSnapshotPort.Received.class,
                        alien.physicalInputs().transport().readFreshFullState(Instant.now().plusSeconds(15)));
                NativeFreshSnapshotPort.verifyAfter(alienSetter, alienReceived);
                assertEquals(setterAck.custody().orElseThrow().session(),
                        alienReceived.acknowledgement().custody().orElseThrow().session());
                assertNotEquals(setterAck.custody().orElseThrow().custodyEpoch(),
                        alienReceived.acknowledgement().custody().orElseThrow().custodyEpoch());
                var alienComplete = alien.writer.locked(same -> {
                    var frame = alienReceived.originalFrame();
                    var nativeRef = alien.archive.preserveNativeFrame(frame);
                    return alien.driverAuthority().withFrozenRawObservation(frame, same, frozen ->
                            assertInstanceOf(DriverObservationAssembler.Complete.class,
                                    alien.physicalInputs().observationAssembler().assemble(frame, frozen.facts(), nativeRef)));
                });
                var alienReadRef = alien.archive.preserve(alienReceived.acknowledgement());
                var alienBasis = new ObservationProvenance.LiveAfterSetter(alien.archive.preserve(alienSetter));
                var alienQuery = new ObservationProvenance.FreshSnapshotQuery(
                        alienReceived.acknowledgement().requestId(), alienReadRef,
                        alienReceived.snapshotReceived(), alienBasis);
                var alienLoader = RootAdvanceInfrastructureFactory.freshFrameLoader(alien.frameLoader());
                alienLoader.verifyFreshSnapshotQuery(alienQuery, alienComplete, alien.archive);
                var mixedQuery = new ObservationProvenance.FreshSnapshotQuery(
                        alienQuery.requestId(), alienReadRef, alienQuery.snapshotReceived(),
                        new ObservationProvenance.LiveAfterSetter(alien.archive.preserve(setterAck)));
                assertThrows(java.io.UncheckedIOException.class,
                        () -> alienLoader.verifyFreshSnapshotQuery(mixedQuery, alienComplete, alien.archive));
            }
        }
    }
}