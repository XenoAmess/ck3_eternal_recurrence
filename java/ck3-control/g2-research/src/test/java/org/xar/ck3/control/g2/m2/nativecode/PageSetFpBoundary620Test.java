package org.xar.ck3.control.g2.m2.nativecode;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;

public final class PageSetFpBoundary620Test {
    @Test
    void verifiesFourPageSetFpGroups() {
        assertEquals(4, PageSetFpBoundary620.verify());
    }
}
