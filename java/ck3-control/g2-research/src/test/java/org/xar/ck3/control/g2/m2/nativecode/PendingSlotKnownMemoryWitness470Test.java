package org.xar.ck3.control.g2.m2.nativecode;
import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;
final class PendingSlotKnownMemoryWitness470Test {
    @Test void fullGrowthUsesBothKnownMemoryPrimitives() {
        assertEquals(1, PendingSlotKnownMemoryWitness470.verify());
    }
}
