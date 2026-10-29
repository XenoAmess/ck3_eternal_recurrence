package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;

final class OriginalIntentHistoryWriterTest {
    @TempDir Path temporary;

    @Test void originalChildPrefixRetainsRunningParentBeforeItsLaterUnknownAndExcludesSelf() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("prefix-parent"), false, false, true)) {
            var command = fixture.command("prefix-parent"); var latestParent = fixture.coordinator.execute(command);
            assertInstanceOf(ActionState.CompositeUnknown.class, latestParent.state());
            String childId = fixture.childActionId.get(); int writes = fixture.nativeActionWrites();
            fixture.writer.locked(same -> {
                var archive = fixture.archive.withSession(same); var actual = same.head();
                var prior = ContinuityActionJournal.receiptsBeforeIntent(actual.state(), childId, archive);
                assertEquals(1, prior.size()); assertEquals(command, prior.getFirst().command());
                var oldParent = assertInstanceOf(ActionState.CompositeRunning.class, prior.getFirst().state());
                assertEquals(childId, oldParent.execution().children().getFirst().actionId());
                assertTrue(prior.getFirst().sequence() < latestParent.sequence());
                assertTrue(ContinuityActionJournal.receiptsBeforeIntent(actual.state(), command.actionId(), archive).isEmpty());
                assertEquals(actual.digest(), same.head().digest()); return null;
            });
            assertEquals(writes, fixture.nativeActionWrites());
        }
    }

    @Test void laterActionAdmissionSeesTheActualPriorZeroDispatchAndNeverItsOwnAttempt() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("prefix-ordinary"), true)) {
            var first = fixture.command("prior-zero"); fixture.stopAtIntentBarrier.set(4);
            var stopped = assertThrows(ReadPublicationRequiredException.class, () -> fixture.coordinator.execute(first));
            var original = stopped.zeroDispatchReceipt().orElseThrow(); fixture.stopAtIntentBarrier.set(0);
            var second = fixture.command("later-unknown"); var unknown = fixture.coordinator.execute(second);
            assertInstanceOf(ActionState.Unknown.class, unknown.state());
            fixture.writer.locked(same -> {
                var prior = ContinuityActionJournal.receiptsBeforeIntent(same.head().state(), second.actionId(), fixture.archive.withSession(same));
                assertEquals(List.of(original), prior); return null;
            });
            assertEquals(1, fixture.nativeActionWrites());
        }
    }

    @Test void detachedCorruptHistoryDataCannotInventMissingDuplicateOrConflictingOriginalIntent() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("bad-prefix-data"), false)) {
            var command = fixture.command("bad-prefix"); byte[] actualLedger = fixture.ledgerBytes();
            fixture.writer.locked(same -> {
                var archive = fixture.archive.withSession(same); var actual = same.head().state();
                var intent = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.IntentDurable());
                var first = archive.preserveRecord(new ActionRecord(intent, Optional.empty()));
                var duplicate = new ActionReceipt(1, 2, command, intent.bodySha256(), new ActionState.IntentDurable());
                var duplicateHead = archive.preserveRecord(new ActionRecord(duplicate, Optional.of(first)));
                assertThrows(IllegalArgumentException.class, () -> ContinuityActionJournal.receiptsBeforeIntent(detached(actual, 2, duplicateHead), command.actionId(), archive));
                var absent = new ActionReceipt(1, 1, command, intent.bodySha256(), new ActionState.Unknown(Optional.empty(), Optional.empty(), "detached malformed data", List.of()));
                var absentHead = archive.preserveRecord(new ActionRecord(absent, Optional.empty()));
                assertThrows(IllegalArgumentException.class, () -> ContinuityActionJournal.receiptsBeforeIntent(detached(actual, 1, absentHead), command.actionId(), archive));
                var changed = new ActionCommand(command.actionId(), command.before(), command.source(), command.sessionId(), command.operation(), command.arguments(), command.expected(), command.claims(), command.deadline().plusSeconds(1));
                var conflict = new ActionReceipt(1, 2, changed, ActionCodec.bodySha256(changed), new ActionState.Unknown(Optional.empty(), Optional.empty(), "conflicting detached body", List.of()));
                var conflictHead = archive.preserveRecord(new ActionRecord(conflict, Optional.of(first)));
                assertThrows(IllegalArgumentException.class, () -> ContinuityActionJournal.receiptsBeforeIntent(detached(actual, 2, conflictHead), command.actionId(), archive));
                assertThrows(IllegalArgumentException.class, () -> ContinuityActionJournal.receiptsBeforeIntent(actual, "missing-original", archive));
                return null;
            });
            assertArrayEquals(actualLedger, fixture.ledgerBytes()); assertEquals(0, fixture.nativeActionWrites());
        }
    }
    /** Deliberately invalid DATA for negative tests, never installed in the actual writer or accepted as a Head. */
    private static ContinuityState detached(ContinuityState original, long sequence, org.xar.ck3.control.contracts.ExactRef record) {
        var row = original.toJson(); row.put("sequence", sequence); row.set(ContinuityActionJournal.STATE_FIELD, record.toJson());
        return ContinuityState.fromJson(row, original.machineId());
    }
}
