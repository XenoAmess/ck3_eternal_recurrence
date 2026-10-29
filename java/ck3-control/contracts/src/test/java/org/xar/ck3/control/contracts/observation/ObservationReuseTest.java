package org.xar.ck3.control.contracts.observation;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.index.OrderedCandidateIndex;

final class ObservationReuseTest {
    private record Source(String machine, String build, String sha) { }
    private record Frame(String snapshot, int publicRevision, int nativeRevision, String episode, int actor) { }
    private record Value(int count) { }
    private static final Source SOURCE = new Source("machine", "exact-build", "a".repeat(64));
    private static final Frame FRAME = new Frame("native:7", 42, 7, "episode-1", 29829);
    private static ObservationReuse.WriterVersion version(int value) {
        return new ObservationReuse.WriterVersion("sole-writer", BigInteger.valueOf(value));
    }
    private static ObservationReuse.Scope<Source, Frame> scope(Source source, Frame frame, int version) {
        return new ObservationReuse.Scope<>(source, frame, version(version));
    }
    private static ObservationReuse.InputKey key(String sha) { return new ObservationReuse.InputKey("whole-input", sha.repeat(64)); }
    private static ObservationReuse<Source, Frame, Value> owner() { return new ObservationReuse<>("sole-writer", 2); }

    @Test void exactCompleteInputReusesAndSameLabelsDifferentContentDoNotAlias() {
        var owner = owner(); var token = owner.bindFresh(scope(SOURCE, FRAME, 1)); var calls = new AtomicInteger();
        var first = owner.read(token, key("a"), () -> new ObservationReuse.Complete<>(new Value(calls.incrementAndGet())));
        var hit = owner.read(token, key("a"), () -> { fail("completed observation was recomputed"); return new ObservationReuse.Complete<>(new Value(99)); });
        var changed = owner.read(token, key("b"), () -> new ObservationReuse.Complete<>(new Value(calls.incrementAndGet())));
        assertFalse(first.reused()); assertTrue(hit.reused()); assertEquals(first.outcome(), hit.outcome());
        assertEquals(2, calls.get()); assertEquals(new Value(2), changed.outcome().value());
    }

    @Test void sourceFrameEpisodeAndActorChangesRevokePriorLeases() {
        var owner = owner(); var token = owner.bindFresh(scope(SOURCE, FRAME, 1));
        var changedSource = new Source("other-machine", SOURCE.build(), SOURCE.sha());
        var next = owner.bindFresh(scope(changedSource, FRAME, 1));
        assertThrows(IllegalStateException.class, () -> owner.requireCurrent(token));
        assertEquals(ObservationReuse.Invalidation.SOURCE_CHANGED, owner.lastInvalidation());
        for (Frame frame : java.util.List.of(new Frame("native:7", 43, 7, "episode-1", 29829),
                new Frame("native:8", 43, 8, "episode-1", 29829),
                new Frame("native:8", 43, 8, "episode-2", 29829),
                new Frame("native:8", 43, 8, "episode-2", 30000))) {
            var old = next; next = owner.bindFresh(scope(changedSource, frame, 1));
            assertThrows(IllegalStateException.class, () -> owner.requireCurrent(old));
            assertEquals(ObservationReuse.Invalidation.FRAME_CHANGED, owner.lastInvalidation());
        }
    }

    @Test void submissionRequiresNewExternalVersionAndPoststateCanBindItsActualNewVersion() {
        var owner = owner(); var original = owner.bindFresh(scope(SOURCE, FRAME, 1));
        owner.beforeSubmit(version(1));
        assertThrows(IllegalStateException.class, () -> owner.requireCurrent(original));
        assertThrows(IllegalStateException.class, () -> owner.bindFresh(scope(SOURCE, FRAME, 1)));
        var next = owner.bindFresh(scope(SOURCE, FRAME, 2));
        owner.afterPoststateVersionChange(version(2), version(3));
        assertThrows(IllegalStateException.class, () -> owner.requireCurrent(next));
        assertDoesNotThrow(() -> owner.bindFresh(scope(SOURCE, FRAME, 3)));
        assertThrows(IllegalArgumentException.class, () -> owner.bindFresh(scope(SOURCE, FRAME, 2)));
    }

    @Test void unknownActionCannotBeReplayedOrResolvedByFreshReadAlone() {
        var owner = owner(); var token = owner.bindFresh(scope(SOURCE, FRAME, 1));
        owner.unknownOutcome(version(1));
        assertThrows(IllegalStateException.class, () -> owner.requireCurrent(token));
        assertThrows(IllegalStateException.class, () -> owner.bindFresh(scope(SOURCE, FRAME, 2)));
        assertThrows(IllegalStateException.class, () -> owner.ownerSettledUnknown(version(1)));
        owner.ownerSettledUnknown(version(2));
        assertDoesNotThrow(() -> owner.bindFresh(scope(SOURCE, FRAME, 2)));
    }

    @Test void unknownAndUnavailableObservationsPreserveTheirValueButNeverReplay() {
        for (boolean unknown : new boolean[] {true, false}) {
            var owner = owner(); var scope = scope(SOURCE, FRAME, 1); var token = owner.bindFresh(scope);
            ObservationReuse.Outcome<Value> result = unknown
                ? new ObservationReuse.Unknown<>(new Value(-1), "missing observation")
                : new ObservationReuse.Unavailable<>(new Value(-2), "provider unavailable");
            assertEquals(result, owner.read(token, key("a"), () -> result).outcome());
            assertEquals(0, owner.retainedEntryCount());
            assertThrows(IllegalStateException.class, () -> owner.read(token, key("a"), () -> { fail("unknown replay"); return result; }));
            assertThrows(IllegalStateException.class, () -> owner.bindFresh(scope));
        }
    }

    @Test void staleCompletionCannotRepopulateAfterOriginalWriterInvalidation() throws Exception {
        var owner = owner(); var token = owner.bindFresh(scope(SOURCE, FRAME, 1));
        var entered = new CountDownLatch(1); var finish = new CountDownLatch(1);
        try (var executor = Executors.newSingleThreadExecutor()) {
            var future = executor.submit(() -> owner.read(token, key("a"), () -> {
                entered.countDown();
                try { if (!finish.await(5, TimeUnit.SECONDS)) throw new IllegalStateException("test deadline"); }
                catch (InterruptedException exception) { Thread.currentThread().interrupt(); throw new IllegalStateException(exception); }
                return new ObservationReuse.Complete<>(new Value(1));
            }));
            assertTrue(entered.await(5, TimeUnit.SECONDS)); owner.beforeSubmit(version(1)); finish.countDown();
            var failure = assertThrows(java.util.concurrent.ExecutionException.class, () -> future.get(5, TimeUnit.SECONDS));
            assertInstanceOf(IllegalStateException.class, failure.getCause()); assertEquals(0, owner.retainedEntryCount());
        } finally { finish.countDown(); }
    }

    @Test void ownerIdentityAndClosedLeasesCannotBeSubstituted() {
        var owner = owner(); var other = owner(); var token = owner.bindFresh(scope(SOURCE, FRAME, 1));
        other.bindFresh(scope(SOURCE, FRAME, 1));
        assertThrows(IllegalStateException.class, () -> other.requireCurrent(token));
        assertThrows(IllegalArgumentException.class, () -> owner.bindFresh(new ObservationReuse.Scope<>(SOURCE, FRAME,
            new ObservationReuse.WriterVersion("another-writer", BigInteger.TEN))));
        owner.close(); assertThrows(IllegalStateException.class, () -> owner.requireCurrent(token));
        assertThrows(IllegalStateException.class, () -> owner.bindFresh(scope(SOURCE, FRAME, 2)));
    }

    @Test void capacityEvictsOnlyMemoizedValueAndNeverDropsProjectionResults() {
        var owner = owner(); var token = owner.bindFresh(scope(SOURCE, FRAME, 1)); var calls = new AtomicInteger();
        for (String sha : java.util.List.of("a", "b", "c", "a")) {
            var read = owner.read(token, key(sha), () -> new ObservationReuse.Complete<>(new Value(calls.incrementAndGet())));
            assertFalse(read.reused());
        }
        assertEquals(4, calls.get()); assertEquals(2, owner.retainedEntryCount());
    }

    @Test void completeOrderedCandidateIndexConsumesActualOwnerGuardAndCannotSurviveSubmission() {
        var owner = owner(); var token = owner.bindFresh(scope(SOURCE, FRAME, 1));
        var complete = java.util.List.of(new Value(7), new Value(7), new Value(8));
        var index = OrderedCandidateIndex.build(token, owner::requireCurrent, complete,
            value -> new OrderedCandidateIndex.Present<>(value.count()));
        assertEquals(3, index.slots().size());
        assertEquals(java.util.List.of(0, 1), index.matching(new OrderedCandidateIndex.Present<>(7))
            .stream().map(OrderedCandidateIndex.Slot::position).toList());
        owner.beforeSubmit(version(1));
        assertThrows(IllegalStateException.class, index::slots);
        assertThrows(IllegalStateException.class, () -> index.matching(new OrderedCandidateIndex.Present<>(7)));
    }

    @Test void failedProjectionCannotBeRetriedThroughTheSameReadLease() {
        var owner = owner(); var token = owner.bindFresh(scope(SOURCE, FRAME, 1));
        assertThrows(IllegalArgumentException.class, () -> owner.read(token, key("a"), () -> { throw new IllegalArgumentException("failed boundary"); }));
        assertThrows(IllegalStateException.class, () -> owner.read(token, key("a"), () -> { fail("failed projection retry"); return new ObservationReuse.Complete<>(new Value(1)); }));
    }
}
