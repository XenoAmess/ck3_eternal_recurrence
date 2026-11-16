package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.PrintStream;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverCapabilityRuntime;
import org.xar.ck3.control.application.driver.DriverPersistentPlanningState;
import org.xar.ck3.control.continuity.writer.ArchiveOriginalEvidencePort;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Real Root private token, physical archive, borrowed writer and retained read scope.
 * Empty auxiliary is a legal full DATA replay with no dependencies; it grants no Core/Game/Native authority. */
final class RootReservedRetirementDataReplayMemoTest {
    private static final Obj EMPTY = new Obj(Map.of());
    private static final ActionPorts.HistoricalReadLimits LIMITS = new ActionPorts.HistoricalReadLimits(16, 1L << 20, 64);
    @TempDir Path root;

    @Test void actualRestrictedTokenMemoizesACompleteEmptyAuxiliaryOnlyWithinItsRetainedScope() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("memo"), false)) {
            int actions = fixture.nativeActionWrites(), reads = fixture.nativeReadWrites();
            String metrics = captureMetrics(() -> fixture.writer.locked(same -> {
                try (var owner = owner(fixture, same)) {
                    var source = owner.dataReplaySource(); var data = owner.archive();
                    return data.inHistoricalReadScope(same, LIMITS, scoped -> {
                        assertSame(data, scoped); assertNull(scoped.scopedDriverDecoder());
                        assertNotNull(source.openAccess(scoped, same));
                        DriverPersistentPlanningState.replay(EMPTY, scoped);
                        DriverPersistentPlanningState.replay(new Obj(Map.of()), scoped);
                        return true;
                    });
                }
            }));
            assertMetrics(metrics, 1, 1, 1, 0);
            assertEquals(actions, fixture.nativeActionWrites()); assertEquals(reads, fixture.nativeReadWrites());
        }
    }

    @Test void nullForeignFacadeSessionAndThreadCannotBorrowThePrivateRootToken() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("owner"), false);
                var other = new ActionWriterIntegrationFixture(root.resolve("other-writer"), false)) {
            var foreignSession = new CompletableFuture<ContinuityStorePort.Session>();
            var releaseForeign = new CountDownLatch(1);
            var holdingForeign = CompletableFuture.runAsync(() -> {
                try {
                    other.writer.locked(foreign -> {
                        foreignSession.complete(foreign);
                        try {
                            if (!releaseForeign.await(30, TimeUnit.SECONDS))
                                throw new IOException("foreign session test did not release its owning writer");
                        } catch (InterruptedException interrupted) {
                            Thread.currentThread().interrupt(); throw new IOException("foreign writer interrupted", interrupted);
                        }
                        return null;
                    });
                } catch (IOException | RuntimeException failure) {
                    foreignSession.completeExceptionally(failure); throw new CompletionException(failure);
                }
            });
            try {
                var foreign = foreignSession.get(10, TimeUnit.SECONDS);
                fixture.writer.locked(same -> {
                    try (var owner = owner(fixture, same); var otherView = owner(fixture, same)) {
                        var source = owner.dataReplaySource(); var data = owner.archive(); var calls = new AtomicInteger();
                        ActionPorts.CheckedArchiveRead<Boolean> operation = ignored -> { calls.incrementAndGet(); return true; };
                        assertThrows(Exception.class, () -> DriverCapabilityRuntime.inRetainedDataReplay(null, data, same, operation));
                        assertThrows(Exception.class, () -> DriverCapabilityRuntime.inRetainedDataReplay(source, null, same, operation));
                        assertThrows(Exception.class, () -> DriverCapabilityRuntime.inRetainedDataReplay(source, data, null, operation));
                        assertThrows(Exception.class, () -> DriverCapabilityRuntime.inRetainedDataReplay(source, fixture.archive, same, operation));
                        assertThrows(Exception.class, () -> DriverCapabilityRuntime.inRetainedDataReplay(source, otherView.archive(), same, operation));
                        assertNotSame(same, foreign);
                        assertFalse(holdingForeign.isDone(), "the foreign session remains held by its actual owning thread");
                        assertThrows(Exception.class, () -> DriverCapabilityRuntime.inRetainedDataReplay(source, data, foreign, operation));
                        var foreignThread = CompletableFuture.supplyAsync(() -> {
                            try { return DriverCapabilityRuntime.inRetainedDataReplay(source, data, same, operation); }
                            catch (IOException failure) { throw new CompletionException(failure); }
                        });
                        assertThrows(java.util.concurrent.ExecutionException.class, () -> foreignThread.get(10, TimeUnit.SECONDS));
                        assertEquals(0, calls.get(), "a caller cannot turn a token from another facade/session/thread into a replay permit");
                        return null;
                    }
                });
            } finally {
                releaseForeign.countDown(); holdingForeign.get(10, TimeUnit.SECONDS);
            }
        }
    }

    @Test void closedOwnerAndAnOldNativeReadScopeCannotReuseAnAccessOrMemoCell() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("scope"), false)) {
            var sourceAfterClose = new AtomicReference<RootReservedRetirementArchive.DataReplaySource>();
            var viewAfterClose = new AtomicReference<ActionPorts.OutcomeArchive>();
            var sessionAfterClose = new AtomicReference<ContinuityStorePort.Session>();
            fixture.writer.locked(same -> {
                sessionAfterClose.set(same);
                try (var owner = owner(fixture, same)) {
                    var source = owner.dataReplaySource(); var data = owner.archive(); sourceAfterClose.set(source); viewAfterClose.set(data);
                    var access = new AtomicReference<DriverPersistentPlanningState.RetainedDataReplayAccess>();
                    String first = captureMetrics(() -> data.inHistoricalReadScope(same, LIMITS, facade -> {
                        access.set(source.openAccess(facade, same));
                        assertTrue(access.get().accepts(facade));
                        DriverPersistentPlanningState.replay(EMPTY, facade); DriverPersistentPlanningState.replay(EMPTY, facade); return true;
                    }));
                    assertMetrics(first, 1, 1, 1, 0);
                    assertFalse(accepts(access.get(), data), "retained custody ended with the original native read scope");
                    String second = captureMetrics(() -> data.inHistoricalReadScope(same, LIMITS, facade -> {
                        assertFalse(accepts(access.get(), facade), "same head and facade cannot revive an earlier native scope");
                        DriverPersistentPlanningState.replay(EMPTY, facade); DriverPersistentPlanningState.replay(EMPTY, facade); return true;
                    }));
                    assertMetrics(second, 1, 1, 1, 0);
                }
                assertThrows(Exception.class, () -> sourceAfterClose.get().openAccess(viewAfterClose.get(), same));
                return null;
            });
            assertThrows(Exception.class, () -> sourceAfterClose.get().openAccess(viewAfterClose.get(), sessionAfterClose.get()));
        }
    }

    @Test void aRealTokenOutsideRetainedCustodyAndAnEscapingFailureNeverSupplyACrossCallHit() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("fallback"), false)) {
            fixture.writer.locked(same -> {
                try (var owner = owner(fixture, same)) {
                    var source = owner.dataReplaySource(); var data = owner.archive();
                    assertNull(source.openAccess(data, same));
                    String full = captureMetrics(() -> DriverCapabilityRuntime.inRetainedDataReplay(source, data, same, scoped -> {
                        DriverPersistentPlanningState.replay(EMPTY, scoped); DriverPersistentPlanningState.replay(EMPTY, scoped); return true;
                    }));
                    assertTrue(full.lines().filter(line -> line.startsWith("DATA_REPLAY_MEMO_METRICS "))
                                    .allMatch(line -> line.contains("hits=0 ") && line.contains("entries=0 ")),
                            "null access cannot borrow or publish a memo entry, independently of diagnostic rows");
                    String failure = captureMetrics(() -> {
                        assertThrows(IllegalStateException.class, () -> data.inHistoricalReadScope(same, LIMITS, scoped -> {
                            DriverPersistentPlanningState.replay(EMPTY, scoped); throw new IllegalStateException("original callback failed");
                        }));
                        return null;
                    });
                    String fresh = captureMetrics(() -> data.inHistoricalReadScope(same, LIMITS, scoped -> {
                        DriverPersistentPlanningState.replay(EMPTY, scoped); DriverPersistentPlanningState.replay(EMPTY, scoped); return true;
                    }));
                    assertMetrics(fresh, 1, 1, 1, 0);
                    assertTrue(failure.contains("scope_callback_succeeded=0"));
                    return null;
                }
            });
        }
    }

    @Test void actualNativeDependencyCaptureIsNonemptyAndVerifyPropagatesItIntoANewTrace() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("nonempty-dependencies"), false)) {
            int actions = fixture.nativeActionWrites(), reads = fixture.nativeReadWrites();
            var body = new RawJson("[1]".getBytes(StandardCharsets.UTF_8));
            fixture.writer.locked(same -> {
                ExactRef original = fixture.archive.preserveMaterial(body);
                try (var owner = owner(fixture, same)) {
                    var source = owner.dataReplaySource(); var data = owner.archive();
                    return data.inHistoricalReadScope(same, LIMITS, scoped -> {
                        var access = source.openAccess(scoped, same);
                        assertNotNull(access); assertTrue(access.accepts(scoped)); access.requireCurrent();
                        Set<ExactRef> dependencies;
                        Object first = access.beginCapture();
                        try {
                            assertEquals(body, scoped.loadMaterial(original));
                            dependencies = access.dependencies(first).orElseThrow();
                            assertFalse(dependencies.isEmpty()); assertTrue(dependencies.contains(original));
                        } finally { access.closeCapture(first); }
                        // This fresh trace starts after the original read trace closed. Its only
                        // dependency-producing operation is verification of the retained originals.
                        Object second = access.beginCapture();
                        try {
                            assertTrue(access.verify(dependencies));
                            Set<ExactRef> propagated = access.dependencies(second).orElseThrow();
                            assertEquals(dependencies, propagated); assertTrue(propagated.contains(original));
                        } finally { access.closeCapture(second); }
                        access.requireCurrent(); assertTrue(access.accepts(scoped));
                        assertTrue(access.verify(dependencies));
                        return true;
                    });
                }
            });
            assertEquals(actions, fixture.nativeActionWrites()); assertEquals(reads, fixture.nativeReadWrites());
        }
    }

    private static boolean accepts(DriverPersistentPlanningState.RetainedDataReplayAccess access, ActionPorts.OutcomeArchive facade) {
        try { return access.accepts(facade); } catch (IOException | RuntimeException ended) { return false; }
    }
    private static RootReservedRetirementArchive owner(ActionWriterIntegrationFixture fixture, ContinuityStorePort.Session same) {
        return RootReservedRetirementArchive.create(fixture.archive, same, new ArchiveOriginalEvidencePort(fixture.archive), () -> {
            try { fixture.writer.requireSession(same); } catch (IOException failure) { throw new UncheckedIOException(failure); }
        }, "software-parent", "1".repeat(64));
    }
    @FunctionalInterface private interface Work<T> { T run() throws IOException; }
    private static <T> String captureMetrics(Work<T> operation) throws IOException {
        synchronized (RootReservedRetirementDataReplayMemoTest.class) {
            var buffer = new ByteArrayOutputStream(); PrintStream original = System.err;
            try (var captured = new PrintStream(buffer, true, StandardCharsets.UTF_8)) {
                System.setErr(captured); try { operation.run(); } finally { System.setErr(original); }
            }
            String result = buffer.toString(StandardCharsets.UTF_8); original.print(result); return result;
        }
    }
    private static void assertMetrics(String output, long full, long hits, long entries, long dependencies) {
        List<String> rows = output.lines().filter(line -> line.startsWith("DATA_REPLAY_MEMO_METRICS ")).toList();
        assertEquals(1, rows.size(), output); String row = rows.getFirst();
        assertTrue(row.contains("full_replays=" + full + " "), row); assertTrue(row.contains("hits=" + hits + " "), row);
        assertTrue(row.contains("entries=" + entries + " "), row); assertTrue(row.contains("dependency_memberships=" + dependencies + " "), row);
    }
}
