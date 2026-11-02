package org.xar.ck3.control.g2.m2.nativecode;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;

public final class Embedded32ClearQueueBoundary593Test {
    @Test
    void verifiesFourOriginalEmbedded32ClearQueueBoundaries() {
        assertEquals(4, Embedded32ClearQueueBoundary593.verify());
    }
}
