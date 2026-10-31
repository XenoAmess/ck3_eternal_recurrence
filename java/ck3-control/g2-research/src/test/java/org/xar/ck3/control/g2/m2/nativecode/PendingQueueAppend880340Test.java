package org.xar.ck3.control.g2.m2.nativecode;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

final class PendingQueueAppend880340Test {
    @Test void fourActualAppendBranches() {
        assertEquals(4, QueueAppendHost344.verify());
    }
}
