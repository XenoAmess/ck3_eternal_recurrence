package org.xar.ck3.control.g2.m2.nativecode;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;

public final class AllocateIndexedFpBoundary632Test {
    @Test
    void verifiesTwoAllocateIndexedFpGroups() {
        assertEquals(2, AllocateIndexedFpBoundary632.verify());
    }
}
