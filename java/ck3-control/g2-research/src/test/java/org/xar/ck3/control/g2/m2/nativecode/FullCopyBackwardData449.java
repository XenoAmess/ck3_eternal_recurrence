package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
/** Input seeds and pure expected DATA shapes only. No backward algorithm or expected trace. */
public final class FullCopyBackwardData449 {
 private FullCopyBackwardData449() { }
 public static final long E=0x8100000000009008L, M=0x3300000000L, B=0x8100000000001000L, D=B+3L, RET=0xAABBCCDD11223344L;
 public enum Op { R64, R128, W128, STEP }
 /** R64=[address,bits]; R128/W128=[address,low64,high64]; STEP=[headerRVA,currentRCX]. */
 public record Step(Op op,List<Long> values) {
  public Step { Objects.requireNonNull(op);values=List.copyOf(values); }
 }
 public record Scene(long count,List<Step> steps,FullCopy437Api.CallResult expected) {
  public Scene { steps=List.copyOf(steps);Objects.requireNonNull(expected); }
 }
 private static Bits128 x(long n) { return new Bits128(n,~n); }
 public static VolatileBits incoming(long count) {
  return new VolatileBits(D,D,B,count,B+count,M,0x100BL,x(0x1010),x(0x1020),x(0x1030),x(0x1040),x(0x1050),x(0x1060));
 }
 public static NonvolatileBits nonvolatile() {
  return new NonvolatileBits(0x2001,0x2002,0x2003,0x2004,0x2005,0x2006,0x2007,0x2008,x(0x2060));
 }
}
