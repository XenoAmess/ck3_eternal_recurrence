package org.xar.ck3.control.g2.m2.nativecode;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;

public final class QueueAppendNonGrowthBoundary599Test {
    @Test
    void verifiesSixOriginalQueueNonGrowthBoundaries() {
        assertEquals(6, QueueAppendNonGrowthBoundary599.verify());
    }
}
