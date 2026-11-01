package org.xar.ck3.control.g2.m2.nativecode;
import java.io.IOException;
import java.io.InputStream;
import java.util.zip.GZIPInputStream;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import org.junit.jupiter.api.Test;
final class FullCopyOriginalRamConsumer455Test {
    @Test void newFullCopyConsumesCapturedOriginalRam() throws IOException {
        try (InputStream source = getClass().getResourceAsStream("copy-original381-389.bin.gz")) {
            assertNotNull(source);
            try (GZIPInputStream decoded = new GZIPInputStream(source)) {
                assertEquals(7, FullCopyOriginalRamConsumer455.verify(decoded));
            }
        }
    }
}
