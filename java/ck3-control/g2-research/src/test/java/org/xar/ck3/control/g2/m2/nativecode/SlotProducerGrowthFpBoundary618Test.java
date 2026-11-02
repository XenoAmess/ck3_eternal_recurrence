package org.xar.ck3.control.g2.m2.nativecode;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;

public final class SlotProducerGrowthFpBoundary618Test {
    @Test
    void verifiesFourSlotProducerGrowthFpGroups() {
        assertEquals(4, SlotProducerGrowthFpBoundary618.verify());
    }
}
