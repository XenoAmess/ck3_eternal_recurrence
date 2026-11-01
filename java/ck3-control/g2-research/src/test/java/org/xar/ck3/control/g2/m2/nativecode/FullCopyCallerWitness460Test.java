package org.xar.ck3.control.g2.m2.nativecode;
import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;
final class FullCopyCallerWitness460Test {
    @Test void actualCopyPreservesTheFullCallerSequence() {
        assertEquals(1, FullCopyCallerWitness460.verify());
    }
}
