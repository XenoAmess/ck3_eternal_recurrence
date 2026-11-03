package org.xar.ck3.control.g2.m2.nativecode;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

final class DefaultRetryCombinedBoundary649Test {
    @Test void verifiesEightDefaultRetryCombinedGroups() throws Exception {
        assertEquals(8, DefaultRetryCombinedBoundary649.verify());
    }
}
