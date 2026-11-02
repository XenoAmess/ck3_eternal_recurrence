package org.xar.ck3.control.g2.m2.nativecode;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;

public final class EmbeddedQueueKnownNonGrowthBoundary600Test {
    @Test
    void verifiesFourOriginalKnownQueueNonGrowthBoundaries() {
        assertEquals(4, EmbeddedQueueKnownNonGrowthBoundary600.verify());
    }
}
