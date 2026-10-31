package org.xar.ck3.control.g2.m2.nativecode;
import java.io.IOException;
import java.io.InputStream;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
/** Six original385 rows plus sole corrected actual389 scene4; no Native execution here. */
final class CopyOriginalRamConsumer381Test {
 @Test void consumesActualCompositeNativeRam() throws IOException {
  InputStream raw = getClass().getResourceAsStream("copy-original381-389.bin.gz");
  assertNotNull(raw);
  try (InputStream input = new GZIPInputStream(raw)) { assertEquals(7, CopyOriginalRamConsumer381.verify(input)); }
 }
}
