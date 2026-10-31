package org.xar.ck3.control.g2.m2.nativecode;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

final class PendingSlotCapacity1ACDFB0Test {
    @Test void preservesReverseSlotsAndExistingTailLink() {
        assertEquals(4, PendingSlotCapacityWitnessHost237.verify(PendingSlotCapacityWitnessBook237.scenes()));
    }
}
