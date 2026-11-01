package org.xar.ck3.control.g2.m2.nativecode;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;

final class PendingSlotFullKnownWitness434Test {
    @Test
    void fullKnownReserveAndSetPreserveSourceState() {
        assertEquals(1, PendingSlotFullKnownWitness434.verify());
    }
}
