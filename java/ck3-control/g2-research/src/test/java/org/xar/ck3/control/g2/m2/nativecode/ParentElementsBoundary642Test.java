package org.xar.ck3.control.g2.m2.nativecode;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

final class ParentElementsBoundary642Test {
    @Test void verifiesSixParentElementsGroups() throws Exception {
        assertEquals(6, ParentElementsBoundary642.verify());
    }
}
