package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
public final class RangeKnownData416 {
 private RangeKnownData416() { }
 public enum Op { R8,R16,R32,R64,R128,R256,W8,W16,W32,W64,W128,W256,FENCE,STEP }
 public record Step(Op op,List<Long> values,long returned) { }
 public record Scene(PendingContextRangeInsertBCB7C0.Input input,List<Step> steps) { }
}
