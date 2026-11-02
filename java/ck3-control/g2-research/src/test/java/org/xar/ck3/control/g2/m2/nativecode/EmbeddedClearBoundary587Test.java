package org.xar.ck3.control.g2.m2.nativecode;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;

public final class EmbeddedClearBoundary587Test {
    @Test
    void verifiesFiveOriginalEmbeddedClearBoundaries() {
        assertEquals(5, EmbeddedClearBoundary587.verify());
    }
}
