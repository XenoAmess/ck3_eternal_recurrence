package org.xar.ck3.control.g2.m2.nativecode;
import java.io.InputStream;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
final class RangeOriginalConsumer419Test {
 @Test void consumesFourOriginalRamObservations() throws Exception {
  InputStream resource=getClass().getResourceAsStream("range-original419.bin.gz");
  assertNotNull(resource);
  try (InputStream input=new GZIPInputStream(resource)) { assertEquals(4,RangeOriginalConsumer419.verify(input)); }
 }
}
