package org.xar.ck3.control.g2.m2.nativecode;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;

public final class EmbeddedQueueKnownBothBoundary601Test {
    @Test
    void verifiesThreeOriginalKnownQueueBothBoundaries() {
        assertEquals(3, EmbeddedQueueKnownBothBoundary601.verify());
    }
}
