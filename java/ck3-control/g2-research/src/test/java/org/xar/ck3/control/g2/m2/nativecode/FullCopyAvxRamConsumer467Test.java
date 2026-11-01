package org.xar.ck3.control.g2.m2.nativecode;
import java.io.IOException;
import java.io.InputStream;
import java.util.zip.GZIPInputStream;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import org.junit.jupiter.api.Test;
final class FullCopyAvxRamConsumer467Test {
    @Test void originalCachedAndStreamingAvxRamMatchesTheFullCopy() throws IOException {
        try (InputStream source = getClass().getResourceAsStream("copy-avx467-471.bin.gz")) {
            assertNotNull(source);
            try (GZIPInputStream decoded = new GZIPInputStream(source)) {
                assertEquals(2, FullCopyAvxRamConsumer467.verify(decoded));
            }
        }
    }
}
