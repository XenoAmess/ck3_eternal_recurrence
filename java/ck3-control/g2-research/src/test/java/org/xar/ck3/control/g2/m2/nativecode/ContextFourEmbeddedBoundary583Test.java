package org.xar.ck3.control.g2.m2.nativecode;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;

public final class ContextFourEmbeddedBoundary583Test {
    @Test
    void verifiesFourOriginalContextEmbeddedBoundaries() {
        assertEquals(4, ContextFourEmbeddedBoundary583.verify());
    }
}
