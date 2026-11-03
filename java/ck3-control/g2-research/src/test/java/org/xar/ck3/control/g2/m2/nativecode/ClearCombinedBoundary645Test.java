package org.xar.ck3.control.g2.m2.nativecode;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

final class ClearCombinedBoundary645Test {
    @Test void verifiesEightClearCombinedGroups() throws Exception {
        assertEquals(8, ClearCombinedBoundary645.verify());
    }
}
