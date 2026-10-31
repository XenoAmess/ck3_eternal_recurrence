package org.xar.ck3.control.g2.m2.nativecode;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

final class PendingPageTableReserve2A32620Test {
    @Test void preservesBufferTransferAndFreshVirtualDispatch() {
        assertEquals(3, TableReserveWitness223.verify());
    }
}
