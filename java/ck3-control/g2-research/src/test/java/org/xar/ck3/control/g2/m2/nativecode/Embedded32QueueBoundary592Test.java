package org.xar.ck3.control.g2.m2.nativecode;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;

public final class Embedded32QueueBoundary592Test {
    @Test
    void verifiesFiveOriginalEmbedded32QueueBoundaries() {
        assertEquals(5, Embedded32QueueBoundary592.verify());
    }
}
