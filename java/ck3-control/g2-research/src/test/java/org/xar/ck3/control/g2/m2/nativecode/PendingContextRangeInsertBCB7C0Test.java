package org.xar.ck3.control.g2.m2.nativecode;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

final class PendingContextRangeInsertBCB7C0Test {
    @Test void threeSourceBranchesAndSseOverflow() {
        var scenes = PendingContextRangeWitnessBook265.scenes();
        assertEquals(3, scenes.size());
        scenes.forEach(PendingContextRangeWitnessHost265::verify);
    }
}
