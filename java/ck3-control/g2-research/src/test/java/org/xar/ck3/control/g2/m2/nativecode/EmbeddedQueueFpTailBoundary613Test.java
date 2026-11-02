package org.xar.ck3.control.g2.m2.nativecode;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;

public final class EmbeddedQueueFpTailBoundary613Test {
    @Test
    void verifiesSixFpCopyAndTailGroups() {
        assertEquals(6, EmbeddedQueueFpTailBoundary613.verify());
    }
}
