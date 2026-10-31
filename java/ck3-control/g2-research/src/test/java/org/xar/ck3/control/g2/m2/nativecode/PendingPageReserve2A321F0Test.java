package org.xar.ck3.control.g2.m2.nativecode;

import java.io.IOException;
import java.io.InputStream;
import java.util.Objects;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

final class PendingPageReserve2A321F0Test {
    @Test void matchesOriginal381ControlledNativeRam() throws IOException {
        try (InputStream raw = Objects.requireNonNull(getClass().getResourceAsStream(
                "pending-page-reserve-native216.bin.gz"));
                InputStream input = new GZIPInputStream(raw)) {
            assertEquals(6, PendingPageReserveNativeConsumer216.verify(input));
        }
    }
}
