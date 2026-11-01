package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
/** Pure DATA. */
public final class RangeOrderData410 {
 private RangeOrderData410() { }
 public enum Op { R8,R32,R128,R256,W8,W128,W256,STEP }
 public record Step(Op op,List<Long> values,long returned) { }
 public record Scene(String name,boolean composition,long first,long middle,long last,long moduleBase,long expectedReturn,List<Step> steps) { }
}
