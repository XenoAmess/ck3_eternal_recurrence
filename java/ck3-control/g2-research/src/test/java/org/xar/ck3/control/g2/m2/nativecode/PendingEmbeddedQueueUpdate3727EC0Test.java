package org.xar.ck3.control.g2.m2.nativecode;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

final class PendingEmbeddedQueueUpdate3727EC0Test {
    @Test void fourNormalGuardsAndContendedAcquire() {
        assertEquals(4, QueueUpdateHost337.verify());
    }
}
