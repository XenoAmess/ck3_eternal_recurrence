package org.xar.ck3.control.g2.m2.nativecode;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;

public final class QueueAppendFpWholeBoundary608Test {
    @Test
    void verifiesEightOriginalFpAwareQueueEntryGroups() {
        assertEquals(8, QueueAppendFpWholeBoundary608.verify());
    }
}
