package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.file.Path;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;

/** Real writer/archive/receipt decoder; the archive decorator counts calls and delegates all DATA. */
final class ContinuityActionSnapshotScopeTest {
    @TempDir Path temporary;

    @Test void freezeAndCurrentAssertionDecodeTheRealRecordOnceInsteadOfTwice() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("same-head"), false)) {
            var command = fixture.command("same-head-intent");
            var receipt = fixture.journal.locked(held -> held.append(command, ActionCodec.bodySha256(command), new ActionState.IntentDurable()));
            var counts = new Counts();
            var journal = new ContinuityActionJournal(fixture.writer, new CountingArchive(fixture.archive, counts));
            fixture.writer.locked(same -> {
                new ActionSnapshotReader(journal).withFrozen(same, lease -> {
                    assertEquals(java.util.List.of(receipt), lease.snapshot().actions());
                    lease.assertCurrent();
                    return null;
                });
                return null;
            });
            assertEquals(1, counts.records.get(), "freeze + assertCurrent must decode this real one-record chain once");
            assertEquals(0, fixture.nativeActionWrites());
        }
    }

    @Test void fiveSnapshotCallsInOneWriterViewShareOneDecodedChain() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("five"), false)) {
            var command = fixture.command("five-intent");
            fixture.journal.locked(held -> held.append(command, ActionCodec.bodySha256(command), new ActionState.IntentDurable()));
            var counts = new Counts();
            var journal = new ContinuityActionJournal(fixture.writer, new CountingArchive(fixture.archive, counts));
            journal.locked(held -> {
                var reader = new ActionSnapshotReader(journal);
                reader.withFrozen(held.writerSession(), lease -> { lease.assertCurrent(); lease.assertCurrent(); return null; });
                reader.withFrozen(held.writerSession(), lease -> { lease.assertCurrent(); return null; });
                return null;
            });
            assertEquals(1, counts.records.get(), "two actual freezes and three current assertions share the original view/head");
        }
    }

    @Test void realAppendInvalidatesTheSnapshotAndTheEarlierFreeze() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("append"), false)) {
            var command = fixture.command("append-intent");
            var journal = fixture.journal;
            journal.locked(held -> {
                var before = held.snapshot();
                assertTrue(before.actions().isEmpty());
                new ActionSnapshotReader(journal).withFrozen(held.writerSession(), lease -> {
                    var receipt = held.append(command, ActionCodec.bodySha256(command), new ActionState.IntentDurable());
                    var after = held.snapshot();
                    assertTrue(after.ledgerSequence() > before.ledgerSequence());
                    assertNotEquals(before.headSha256(), after.headSha256());
                    assertEquals(java.util.List.of(receipt), after.actions());
                    assertThrows(IllegalArgumentException.class, lease::assertCurrent);
                    return null;
                });
                return null;
            });
            assertEquals(0, fixture.nativeActionWrites());
        }
    }

    @Test void aNewScopeReadsAgainAndAnEscapedClosedSessionCannotUseTheCache() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("closed"), false)) {
            var command = fixture.command("scope-intent");
            fixture.journal.locked(held -> held.append(command, ActionCodec.bodySha256(command), new ActionState.IntentDurable()));
            var counts = new Counts();
            var journal = new ContinuityActionJournal(fixture.writer, new CountingArchive(fixture.archive, counts));
            var escaped = new AtomicReference<ActionJournal.LockedJournal>();
            var lease = new AtomicReference<ActionSnapshotReader.Lease>();
            journal.locked(held -> {
                escaped.set(held);
                new ActionSnapshotReader(journal).withFrozen(held.writerSession(), frozen -> { lease.set(frozen); return null; });
                return null;
            });
            assertEquals(1, counts.records.get());
            assertThrows(RuntimeException.class, () -> escaped.get().snapshot());
            assertThrows(IllegalStateException.class, () -> lease.get().assertCurrent());
            assertEquals(1, counts.records.get(), "a closed session fails before accessing cached archive DATA");
            journal.locked(held -> { held.snapshot(); return null; });
            assertEquals(2, counts.records.get(), "new original writer scope cannot inherit the prior cache");
        }
    }

    @Test void aFailedDecodeDoesNotPopulateTheSnapshotCache() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("failure"), false)) {
            var command = fixture.command("failure-intent");
            fixture.journal.locked(held -> held.append(command, ActionCodec.bodySha256(command), new ActionState.IntentDurable()));
            var counts = new Counts(); counts.failNext.set(true);
            var journal = new ContinuityActionJournal(fixture.writer, new CountingArchive(fixture.archive, counts));
            journal.locked(held -> {
                assertThrows(IllegalStateException.class, held::snapshot);
                assertEquals(1, held.snapshot().actions().size());
                held.snapshot();
                return null;
            });
            assertEquals(2, counts.records.get(), "one failed call and one successful full decode, then one cache hit");
        }
    }

    private static final class Counts {
        final AtomicInteger records = new AtomicInteger();
        final AtomicBoolean failNext = new AtomicBoolean();
    }

    private record CountingArchive(ActionPorts.OutcomeArchive actual, Counts counts) implements ActionPorts.OutcomeArchive {
        @Override public <T> T inSession(ContinuityStorePort.Session same, Function<ActionPorts.OutcomeArchive, T> work) {
            return actual.inSession(same, bound -> work.apply(new CountingArchive(bound, counts)));
        }
        @Override public ActionRecord loadRecord(ExactRef original) {
            counts.records.incrementAndGet();
            if (counts.failNext.getAndSet(false)) throw new IllegalStateException("controlled archive decode failure before a complete snapshot");
            return actual.loadRecord(original);
        }
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome value) { return actual.preserve(value); }
        @Override public NativeActionPort.DispatchOutcome load(ExactRef value) { return actual.load(value); }
        @Override public ExactRef preserveRequest(NativeRequest value) { return actual.preserveRequest(value); }
        @Override public NativeRequest loadRequest(ExactRef value) { return actual.loadRequest(value); }
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome value) { return actual.referenceOf(value); }
        @Override public ExactRef requestReferenceOf(NativeRequest value) { return actual.requestReferenceOf(value); }
        @Override public ExactRef preserveRead(PlanningReadReceipt value) { return actual.preserveRead(value); }
        @Override public PlanningReadReceipt loadRead(ExactRef value) { return actual.loadRead(value); }
        @Override public ExactRef readReferenceOf(PlanningReadReceipt value) { return actual.readReferenceOf(value); }
        @Override public ExactRef preserveRecord(ActionRecord value) { return actual.preserveRecord(value); }
        @Override public ExactRef recordReferenceOf(ActionRecord value) { return actual.recordReferenceOf(value); }
        @Override public ExactRef preserveReceipt(ActionReceipt value) { return actual.preserveReceipt(value); }
        @Override public ActionReceipt loadReceipt(ExactRef value) { return actual.loadReceipt(value); }
        @Override public ExactRef receiptReferenceOf(ActionReceipt value) { return actual.receiptReferenceOf(value); }
        @Override public ExactRef preserveMaterial(RawJson value) { return actual.preserveMaterial(value); }
        @Override public RawJson loadMaterial(ExactRef value) { return actual.loadMaterial(value); }
        @Override public ExactRef materialReferenceOf(RawJson value) { return actual.materialReferenceOf(value); }
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value) { return actual.preserveNativeFrame(value); }
        @Override public byte[] loadNativeFrame(ExactRef value) { return actual.loadNativeFrame(value); }
    }
}
