package org.xar.ck3.control.g2.context;

import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;

/** No genuine Native/Root token is fabricated to make the software test positive. */
final class RootM7ObservationProducerTest {
    @Test void absentActualTokensFailBeforeAnyOwnerGameOrFileOperation() {
        assertThrows(NullPointerException.class,()->RootM7ObservationProducer.project(null,null));
    }
    @Test void actualResultAndNativeCompletionHaveNoPublicMintingConstructor() {
        assertEquals(0,RootM7ObservationProducer.Observed.class.getConstructors().length);
        assertEquals(0,RootMcpSemanticClient.NativeObservation.class.getConstructors().length);
        assertEquals(0,RootMcpSemanticClient.OwnedCompletion.class.getConstructors().length);
    }
}
