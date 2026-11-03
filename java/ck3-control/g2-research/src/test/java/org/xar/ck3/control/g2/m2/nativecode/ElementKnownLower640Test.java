package org.xar.ck3.control.g2.m2.nativecode;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

final class ElementKnownLower640Test {
    @Test void verifiesThreeElementKnownLowerGroups() throws Exception {
        assertEquals(3, ElementKnownLowerBoundary640.verify());
    }
}
