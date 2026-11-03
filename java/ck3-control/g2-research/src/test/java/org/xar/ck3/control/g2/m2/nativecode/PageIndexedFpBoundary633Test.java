package org.xar.ck3.control.g2.m2.nativecode;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;

public final class PageIndexedFpBoundary633Test {
    @Test
    void verifiesTwoPageIndexedFpGroups() {
        assertEquals(2, PageIndexedFpBoundary633.verify());
    }
}
