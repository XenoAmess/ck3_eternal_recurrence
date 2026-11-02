package org.xar.ck3.control.g2.m2.nativecode;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;

public final class PageAllocateFpBoundary622Test {
    @Test
    void verifiesFourPageAllocateFpGroups() {
        assertEquals(4, PageAllocateFpBoundary622.verify());
    }
}
