package org.xar.ck3.control.g2.m2.nativecode;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;

public final class HeapAllocateFpBoundary623Test {
    @Test
    void verifiesFourHeapAllocateFpGroups() {
        assertEquals(4, HeapAllocateFpBoundary623.verify());
    }
}
