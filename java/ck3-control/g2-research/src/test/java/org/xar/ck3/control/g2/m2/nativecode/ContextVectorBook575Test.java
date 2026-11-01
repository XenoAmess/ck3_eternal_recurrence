package org.xar.ck3.control.g2.m2.nativecode;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;

final class ContextVectorBook575Test {
    @Test
    void wholeContextEmbeddedAndVector() {
        assertEquals(1, ContextVectorBook575.verify());
    }

    @Test
    void growthCopiesBothVectorLoops() {
        assertEquals(1, ContextVectorBook575.verifyGrowth());
    }
}
