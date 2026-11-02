package org.xar.ck3.control.g2.m2.nativecode;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;

public final class SlotReserveFpBoundary615Test {
    @Test
    void verifiesSixSlotReserveFpGroups() {
        assertEquals(6, SlotReserveFpBoundary615.verify());
    }
}
