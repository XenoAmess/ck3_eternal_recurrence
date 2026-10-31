package org.xar.ck3.control.g2.m2.nativecode;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

final class PendingContextTailCopy2503880Test {
    @Test void shortCircuitAndCapturedPointer() {
        var scenes = PendingContextTailWitnessBook271.scenes();
        assertEquals(2, scenes.size());
        scenes.forEach(PendingContextTailWitnessHost271::verify);
    }
}
