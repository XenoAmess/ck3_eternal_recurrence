package org.xar.ck3.control.g2.m2.nativecode;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;

public final class QueueGrowthCvttBoundary607Test {
    @Test
    void verifiesThirteenOriginalQueueGrowthCvttGroups() {
        assertEquals(13, QueueGrowthCvttBoundary607.verify());
    }
}
