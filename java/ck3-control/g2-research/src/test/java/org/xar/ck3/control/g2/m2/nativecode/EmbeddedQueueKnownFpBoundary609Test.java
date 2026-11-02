package org.xar.ck3.control.g2.m2.nativecode;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;

public final class EmbeddedQueueKnownFpBoundary609Test {
    @Test
    void verifiesFourOriginalFpAwareQueueCompositionGroups() {
        assertEquals(4, EmbeddedQueueKnownFpBoundary609.verify());
    }
}
