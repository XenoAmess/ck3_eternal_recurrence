package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.DriverPlanningEvidence;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;

/** Real collector/Driver/original reader/sole writer chain; finite packet edges grant no live Game qualification. */
final class NativeOwnedPlanningAdmissionTest {
    @TempDir Path temporary;

    @Test void publicConsumerUsesTheExactPublishedRequestAndOnePhysicalLeaseThroughOriginalEvidenceReplay() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("same-request"), false)) {
            actual.collector.bindPlanningEvidence((same, request, lease) -> DriverPlanningEvidence.requireEquivalent(
                    same, request, lease, actual.physicalInputs().originals()));
            int locks = actual.collectorLocks.get(), inputs = actual.nestedPlanningReads.get();
            var retained = new AtomicReference<PlanningRequest>();
            actual.writer.locked(same -> {
                String head = same.head().digest();
                String result = actual.collector.withOwnedPlanning(same, actual.observationIdentity(), Instant.now().plusSeconds(20),
                        (request, lease) -> {
                            retained.set(request);
                            assertSame(request, actual.lastPublishedReady.get(), "M7 and public consumer retain the same produced request");
                            assertEquals(request.before(), lease.frame().identity());
                            assertEquals(request.source(), lease.frame().source());
                            assertEquals(request.sessionId(), lease.frame().sessionId());
                            int packets = actual.nativePacketReads(), queries = actual.nativeReadWrites();
                            assertSame(lease, actual.collector.currentOwned(same, actual.observationIdentity(), request.deadline(), nested -> nested));
                            assertSame(request, actual.collector.currentPlanning(same, request, request.deadline(), (original, nested) -> {
                                assertSame(lease, nested); return original;
                            }));
                            assertEquals(packets, actual.nativePacketReads(), "public preparation cannot recapture another physical frame");
                            assertEquals(queries, actual.nativeReadWrites(), "replaying original planning evidence issues no Native query");
                            // The real basic producer has no capability-cache source reference; its manifest still binds this packet.
                            assertFalse(request.observations().snapshot().members().containsKey("capability_observed_native_source"));
                            var originals = actual.physicalInputs().originals();
                            assertThrows(IllegalArgumentException.class, () -> DriverPlanningEvidence.requireEquivalent(same, request, lease,
                                    (borrowed, ref, maximum) -> {
                                        byte[] bytes = originals.read(borrowed, ref, maximum);
                                        if (ref.equals(lease.semantic().originalNativePacket())) { bytes=bytes.clone(); bytes[0]^=1; }
                                        return bytes;
                                    }));
                            var wrongSource = new org.xar.ck3.control.g2.common.G2Source(request.source().machineId(),
                                    request.source().observedAtUtc(), "another-build", request.source().sourceRef());
                            var changed = new PlanningRequest(request.before(), wrongSource, request.sessionId(), request.deadline(), request.observations());
                            assertThrows(IllegalArgumentException.class, () -> DriverPlanningEvidence.requireEquivalent(same, changed, lease, originals));
                            assertEquals(head, same.head().digest());
                            assertEquals(0, actual.nativeActionWrites());
                            return "prepared-only";
                        });
                assertEquals("prepared-only", result);
                assertEquals(head, same.head().digest(), "READ history must be flushed by Root after leaving the freeze");
                return null;
            });
            assertEquals(locks, actual.collectorLocks.get(), "public planning borrows the original writer without opening another lock");
            assertEquals(inputs + 1, actual.nestedPlanningReads.get(), "the ordinary actual inputs producer runs exactly once");
            assertSame(retained.get(), actual.lastPublishedReady.get());
            assertTrue(actual.writer.activeSession().isEmpty());
        }
    }

    @Test void recursivePlanningAndMissingOriginalVerifierFailBeforeAnotherCaptureAndScopeCleansUpAfterConsumerFailure() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("recursive"), false)) {
            actual.writer.locked(same -> {
                String head = same.head().digest();
                IOException failure = assertThrows(IOException.class, () -> actual.collector.withOwnedPlanning(
                        same, actual.observationIdentity(), Instant.now().plusSeconds(20), (request, lease) -> {
                            int packets = actual.nativePacketReads();
                            assertThrows(IllegalArgumentException.class, () -> actual.collector.withOwnedPlanning(
                                    same, actual.observationIdentity(), request.deadline(), (other, detached) -> other));
                            assertThrows(IllegalArgumentException.class, () -> actual.collector.currentPlanning(
                                    same, request, request.deadline(), (other, detached) -> other));
                            assertThrows(IllegalArgumentException.class, () -> actual.collector.checkpoint("held-scope").observe(request.deadline()));
                            assertEquals(packets, actual.nativePacketReads());
                            throw new IOException("controlled public preparation failure");
                        }));
                assertEquals("controlled public preparation failure", failure.getMessage());
                assertEquals(head, same.head().digest());
                actual.collector.withOwnedPlanning(same, actual.observationIdentity(), Instant.now().plusSeconds(20), (request, lease) -> {
                    assertSame(request, actual.lastPublishedReady.get()); return null;
                });
                assertEquals(head, same.head().digest());
                assertEquals(0, actual.nativeActionWrites());
                return null;
            });
        }
    }

    @Test void foreignEscapedWrongOwnerAndExpiredCallsCannotStartPublicPlanningNativeIo() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("owner"), false);
             var foreign = new ActionWriterIntegrationFixture(temporary.resolve("foreign"), false)) {
            var escaped = new AtomicReference<ContinuityStorePort.Session>();
            actual.writer.locked(same -> { escaped.set(same); return null; });
            int packets = actual.nativePacketReads();
            assertThrows(IllegalArgumentException.class, () -> actual.collector.withOwnedPlanning(
                    escaped.get(), actual.observationIdentity(), Instant.now().plusSeconds(20), (request, lease) -> request));
            assertThrows(IllegalArgumentException.class, () -> actual.collector.currentOwned(
                    escaped.get(), actual.observationIdentity(), Instant.now().plusSeconds(20), lease -> lease));
            foreign.writer.locked(other -> {
                assertThrows(IOException.class, () -> actual.collector.withOwnedPlanning(
                        other, actual.observationIdentity(), Instant.now().plusSeconds(20), (request, lease) -> request));
                assertThrows(IOException.class, () -> actual.collector.currentOwned(
                        other, actual.observationIdentity(), Instant.now().plusSeconds(20), lease -> lease));
                return null;
            });
            actual.writer.locked(same -> {
                var owner = actual.observationIdentity();
                var wrong = new SessionPorts.SessionIdentity(owner.machineId(), owner.game(), owner.sessionId() + "-other");
                assertThrows(IllegalArgumentException.class, () -> actual.collector.withOwnedPlanning(
                        same, wrong, Instant.now().plusSeconds(20), (request, lease) -> request));
                assertThrows(IllegalArgumentException.class, () -> actual.collector.withOwnedPlanning(
                        same, owner, Instant.now().minusSeconds(1), (request, lease) -> request));
                return null;
            });
            assertEquals(packets, actual.nativePacketReads());
            assertEquals(0, actual.nestedPlanningReads.get());
            assertNull(actual.lastPublishedReady.get());
        }
    }

    @Test void admittedActorIsExplicitOnceBoundAndCannotClearTheCurrentPlayedActorGuard() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("actor-mismatch"), false)) {
            var checks = new AtomicInteger();
            actual.collector.bindAdmittedActorAuthority((same, owner, frame, driver, deadline) -> {
                actual.writer.requireSession(same); assertEquals(actual.observationIdentity(), owner);
                assertEquals(frame.identity().game(), driver.stamp().game());
                assertEquals(frame.identity().frame().identity().player(), driver.driver().session().actorId());
                checks.incrementAndGet(); return BigInteger.valueOf(74);
            });
            assertThrows(IllegalArgumentException.class, () -> actual.collector.bindAdmittedActorAuthority(
                    (same, owner, frame, driver, deadline) -> BigInteger.valueOf(73)));
            actual.writer.locked(same -> {
                String head = same.head().digest();
                assertThrows(IOException.class, () -> actual.collector.withOwnedPlanning(same, actual.observationIdentity(),
                        Instant.now().plusSeconds(20), (request, lease) -> { fail("mismatched admitted actor cannot become public Ready"); return null; }));
                assertEquals(head, same.head().digest()); return null;
            });
            assertEquals(1, checks.get()); assertEquals(0, actual.nestedPlanningReads.get());
            assertNull(actual.lastPublishedReady.get()); assertEquals(0, actual.nativeActionWrites());
        }
    }
}
