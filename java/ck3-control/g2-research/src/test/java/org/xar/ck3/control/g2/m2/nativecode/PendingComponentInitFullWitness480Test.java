package org.xar.ck3.control.g2.m2.nativecode;
import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;
final class PendingComponentInitFullWitness480Test {
    @Test void fullInitializerPreservesProjectionAndReadsFreshReturnSlot() {
        assertEquals(2, PendingComponentInitFullWitness480.verify());
    }
}
