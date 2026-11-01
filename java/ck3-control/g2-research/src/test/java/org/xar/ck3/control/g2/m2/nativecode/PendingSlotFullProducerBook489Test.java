package org.xar.ck3.control.g2.m2.nativecode;
import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;
final class PendingSlotFullProducerBook489Test {
    @Test void earlyExitAndFourFullCallsPreserveActualState() {
        assertEquals(2, PendingSlotFullProducerBook489.verify());
    }
}
