package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;

/** Actual immutable action-record chain membership. An orphan archive entry never grants parent/child authority. */
final class HistoricalActionReceiptWriterTest {
    @TempDir Path temporary;
    @Test void originalAckIsStillCanonicalAfterUnknownAndAnOrphanWithTheSameSequenceIsRejected() throws Exception {
        try (var f = new ActionWriterIntegrationFixture(temporary.resolve("membership"), false)) {
            var command = f.command("historical-parent"); var retained = f.coordinator.execute(command);
            assertInstanceOf(ActionState.Unknown.class, retained.state()); assertEquals(1, f.nativeActionWrites());
            f.writer.locked(same -> f.archive.inSession(same, archive -> {
                var head = assertDoesNotThrow(same::head);
                var currentRef = ContinuityActionJournal.recordHead(head.state()).orElseThrow(); var current = archive.loadRecord(currentRef);
                var originalRef = current.previous().orElseThrow(); var original = archive.loadRecord(originalRef).receipt();
                assertInstanceOf(ActionState.AckReceived.class, original.state());
                assertEquals(originalRef, ContinuityActionJournal.requireHistoricalReceipt(head.state(), original, archive));
                assertEquals(original, archive.loadReceipt(archive.receiptReferenceOf(original)));
                var foreignCommand = new ActionCommand("unrelated-orphan", command.origin(), command.source(), command.sessionId(), command.operation(), command.arguments(), command.expectation(), command.claims(), command.deadline());
                var orphan = new ActionReceipt(1, original.sequence(), foreignCommand, ActionCodec.bodySha256(foreignCommand), original.state());
                var orphanRef = archive.preserveReceipt(orphan); assertEquals(orphan, archive.loadReceipt(orphanRef));
                assertThrows(IllegalArgumentException.class, () -> ContinuityActionJournal.requireHistoricalReceipt(head.state(), orphan, archive));
                assertEquals(currentRef, ContinuityActionJournal.recordHead(assertDoesNotThrow(same::head).state()).orElseThrow()); return null;
            }));
            assertEquals(1, f.nativeActionWrites());
        }
    }
}
