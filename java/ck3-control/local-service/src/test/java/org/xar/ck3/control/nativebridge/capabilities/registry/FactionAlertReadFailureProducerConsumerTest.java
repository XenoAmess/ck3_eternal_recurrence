package org.xar.ck3.control.nativebridge.capabilities.registry;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Executes the real per-read evidence producer and source carrier; protocol tests reuse the same original producer. */
final class FactionAlertReadFailureProducerConsumerTest {
    @TempDir Path temporary;
    @Test void originalNativeRejectedReadRetainsItsExactTypeMessageAndArchivedRequestResult()throws Exception {
        var actual=FactionAlertFailureProducerFixture.actualNativeRejected(temporary.resolve("native-rejected"));
        assertNotNull(actual.failure());assertEquals(1,actual.nativeReads());assertEquals(0,actual.nativeActions());
    }
    @Test void originalPreflightMismatchUsesTheActualCurrentFrameAndSendsNoRead()throws Exception {
        var actual=FactionAlertFailureProducerFixture.actualRevisionMismatch(temporary.resolve("revision"));
        assertTrue(actual.originalCandidate().isEmpty());
    }
    @Test void originalPostWriteUnknownIsNotClassifiedFromAReasonAndIsNotReplayed()throws Exception {
        FactionAlertFailureProducerFixture.actualUnknownIsNeverGuessedToBeARejectedCommandOrTimeout(temporary.resolve("unknown"));
    }
    @Test void successfulNativeBusinessUnavailableUsesTheUnchangedResultCodec()throws Exception {
        FactionAlertFailureProducerFixture.actualBusinessUnavailableRemainsANormalCodecReply(temporary.resolve("business-unavailable"));
    }
    @Test void laterPublicationFailureKeepsItsOriginalDiagnosticAndDoesNotAcquireTheOldNativeClass()throws Exception {
        FactionAlertFailureProducerFixture.actualPublicationFailureDoesNotReuseAnEarlierNativeClassification(temporary.resolve("publication"));
    }
}
