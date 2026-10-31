package org.xar.ck3.control.g2.m2.nativecode;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

final class PendingQueueAppendWithKnownCopy880340Test {
    @Test void positiveGrowthConsumesActualKnownCopy() {
        assertEquals(1, KnownQueueCopyHost375.verify());
    }
}
