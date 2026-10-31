package org.xar.ck3.control.g2.m2.nativecode;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

final class PendingSlotWithGrowthAndCopies2A32770Test {
    @Test void actualGrowthCallComposesBeforePageFalse() {
        assertEquals(1, SlotProducerGrowthWitness253.verify());
    }
}
