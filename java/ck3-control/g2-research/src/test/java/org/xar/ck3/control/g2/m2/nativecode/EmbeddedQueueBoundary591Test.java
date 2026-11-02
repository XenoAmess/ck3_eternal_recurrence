package org.xar.ck3.control.g2.m2.nativecode;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;

public final class EmbeddedQueueBoundary591Test {
    @Test
    void verifiesFiveOriginalEmbeddedQueueBoundaries() {
        assertEquals(5, EmbeddedQueueBoundary591.verify());
    }
}
