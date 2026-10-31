package org.xar.ck3.control.g2.m2.nativecode;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

final class PendingSlotWithContextCopies2A32770Test {
    @Test void closesTwoKnownContextCopyCallLayers() {
        assertEquals(1, ProducerCompositionWitness207.verify());
    }
}
