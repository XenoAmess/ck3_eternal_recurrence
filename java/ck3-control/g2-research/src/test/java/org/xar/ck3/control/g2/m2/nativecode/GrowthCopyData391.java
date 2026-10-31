package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
/** Pure DATA only. */
public final class GrowthCopyData391 {
 private GrowthCopyData391() { }
 public enum Op { R8,R16,R32,R64,R128,R256,W8,W16,W32,W64,W128,W256,FENCE,ALLOC,FREE,SET }
 public record Step(Op op,List<Long> values,long returned) { }
 public record Scene(String name,long table,int requested,long moduleBase,boolean expected,List<Step> steps) { }
}
