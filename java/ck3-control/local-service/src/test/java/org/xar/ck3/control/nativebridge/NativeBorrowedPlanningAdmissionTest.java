package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.file.Path;
import java.time.Instant;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Actual collector/Driver freeze admission; missing scope is never permission to sample another frame. */
final class NativeBorrowedPlanningAdmissionTest {
    @TempDir Path temporary;

    @Test void optionalActiveBorrowRetainsTheActualLeaseAcrossFrozenActionPreparationWithoutNativeIo() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("optional-active"), false)) {
            actual.writer.locked(same -> actual.collector.withOwnedPlanning(same, actual.observationIdentity(),
                    Instant.now().plusSeconds(20), (request, lease) -> actual.driverAuthority().withFrozenFacts(same, frozen -> {
                        int packets = actual.nativePacketReads(), queries = actual.nativeReadWrites();
                        String head = same.head().digest();
                        var borrowed = actual.collector.withActiveCurrent(same, request.before(), request.deadline(), current -> current);
                        assertSame(lease, borrowed.orElseThrow()); assertSame(lease.frame(), borrowed.orElseThrow().frame());
                        assertSame(lease.driver(), borrowed.orElseThrow().driver());
                        assertSame(lease.executableSteps(), borrowed.orElseThrow().executableSteps());
                        assertThrows(NullPointerException.class, () -> actual.collector.withActiveCurrent(
                                same, request.before(), request.deadline(), current -> null));
                        assertThrows(IllegalArgumentException.class, () -> actual.collector.withActiveCurrent(
                                same, request.before(), Instant.EPOCH, current -> current));
                        assertEquals(packets, actual.nativePacketReads()); assertEquals(queries, actual.nativeReadWrites());
                        assertEquals(head, same.head().digest()); return null;
                    })));
        }
    }

    @Test void onlyActuallyAbsentCollectorAndDriverScopesReturnEmptyAndNeverCallTheMapper() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("optional-inactive"), false)) {
            var ready = actual.ready();
            var escaped = new AtomicReference<org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session>();
            actual.writer.locked(same -> {
                escaped.set(same); int packets = actual.nativePacketReads(), queries = actual.nativeReadWrites();
                String head = same.head().digest();
                assertTrue(actual.collector.withActiveCurrent(same, ready.request().before(), Instant.now().plusSeconds(20),
                        current -> { fail("inactive collector called the mapper"); return current; }).isEmpty());
                actual.driverAuthority().withFrozenFacts(same, frozen -> {
                    assertThrows(IllegalArgumentException.class, () -> actual.collector.withActiveCurrent(
                            same, ready.request().before(), Instant.now().plusSeconds(20), current -> current)); return null;
                });
                assertEquals(packets, actual.nativePacketReads()); assertEquals(queries, actual.nativeReadWrites());
                assertEquals(head, same.head().digest()); return null;
            });
            assertThrows(IllegalArgumentException.class, () -> actual.collector.withActiveCurrent(
                    escaped.get(), ready.request().before(), Instant.now().plusSeconds(20), current -> current));
            assertEquals(0, actual.nativeActionWrites());
        }
    }

    @Test void cleanupPhysicalOriginalsReuseActualCachedNativeAndFrozenDriverWithoutOrdinaryReadinessCapture() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("physical-cleanup-originals"), false)) {
            var ready = actual.ready();
            actual.writer.locked(same -> {
                int packets = actual.nativePacketReads(), queries = actual.nativeReadWrites();
                String head = same.head().digest();
                actual.collector.currentDerivedCleanup(same, ready.request().before(), Instant.now().plusSeconds(20), physical -> {
                    assertEquals(ready.request().before(), physical.frame().identity());
                    assertEquals(physical.frame().identity(), physical.semantic().frame());
                    assertNotNull(physical.originalHello()); assertNotNull(physical.originalHeartbeat());
                    assertNotNull(physical.originalSourceQualification());
                    assertThrows(IllegalArgumentException.class, () -> actual.collector.withActiveCurrent(
                            same, physical.frame().identity(), Instant.now().plusSeconds(20), ordinary -> ordinary));
                    assertEquals(head, same.head().digest()); return null;
                });
                assertEquals(packets, actual.nativePacketReads()); assertEquals(queries, actual.nativeReadWrites());
                assertEquals(head, same.head().digest()); return null;
            });
            assertEquals(0, actual.nativeActionWrites());
        }
    }

    @Test void anActualOuterCollectorLeaseCanBeBorrowedInsideTheSameImmutableDriverFactsScope() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("borrowed-facts"), false)) {
            actual.writer.locked(same -> actual.collector.withOwnedPlanning(same, actual.observationIdentity(),
                    Instant.now().plusSeconds(20), (request, lease) -> actual.driverAuthority().withFrozenFacts(same, frozen -> {
                        int packets = actual.nativePacketReads(), queries = actual.nativeReadWrites();
                        String head = same.head().digest();
                        assertSame(lease, actual.collector.borrowCurrent(same, request.before(), request.deadline(), borrowed -> borrowed));
                        assertEquals(lease.driver().stamp(), ((org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known) frozen.state()).stamp());
                        assertEquals(packets, actual.nativePacketReads()); assertEquals(queries, actual.nativeReadWrites());
                        assertEquals(head, same.head().digest()); return null;
                    })));
        }
    }

    @Test void missingOrEscapedCollectorScopeFailsBeforeNativeIoEvenWhileTheDriverHistoryIsFrozen() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("missing-facts-scope"), false)) {
            var ready = actual.ready();
            var escaped = new AtomicReference<org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session>();
            actual.writer.locked(same -> actual.driverAuthority().withFrozenFacts(same, frozen -> {
                escaped.set(same); int packets = actual.nativePacketReads(), queries = actual.nativeReadWrites();
                String head = same.head().digest();
                assertThrows(IllegalArgumentException.class, () -> actual.collector.borrowCurrent(
                        same, ready.request().before(), Instant.now().plusSeconds(20), lease -> lease));
                assertEquals(packets, actual.nativePacketReads()); assertEquals(queries, actual.nativeReadWrites());
                assertEquals(head, same.head().digest()); return null;
            }));
            int packets = actual.nativePacketReads();
            assertThrows(IllegalArgumentException.class, () -> actual.collector.borrowCurrent(
                    escaped.get(), ready.request().before(), Instant.now().plusSeconds(20), lease -> lease));
            assertEquals(packets, actual.nativePacketReads()); assertEquals(0, actual.nativeActionWrites());
        }
    }
}
