package org.xar.ck3.control.g2.m2.nativecode;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;

public final class AllocateErrorFpBoundary625Test {
    @Test
    void verifiesFourAllocateErrorFpGroups() {
        assertEquals(4, AllocateErrorFpBoundary625.verify());
    }
}
