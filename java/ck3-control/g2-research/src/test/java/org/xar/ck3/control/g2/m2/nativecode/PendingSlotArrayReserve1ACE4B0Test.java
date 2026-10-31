package org.xar.ck3.control.g2.m2.nativecode;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

final class PendingSlotArrayReserve1ACE4B0Test {
    @Test void preservesAllocationCopyAndFreshRelease() {
        assertEquals(3, SlotArrayReserveWitness244.verify());
    }
}
