package org.xar.ck3.control.g2.m2.nativecode;

import java.io.IOException;
import java.io.InputStream;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

final class PendingPageWithTableReserve2A321F0Test {
    @Test void originalPageAndTableReserveRamAgree() throws IOException {
        InputStream raw = getClass().getResourceAsStream("pending-page-table-native250.bin.gz");
        assertNotNull(raw);
        try (InputStream input = new GZIPInputStream(raw)) {
            assertEquals(2, PendingPageTableNativeConsumer250.verify(input));
        }
    }
}
