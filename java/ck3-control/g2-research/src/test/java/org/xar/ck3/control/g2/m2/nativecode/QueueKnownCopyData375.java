package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
public final class QueueKnownCopyData375 {
    private QueueKnownCopyData375() { }
    public enum Op { R8,R16,R32,R64,R128,R256,W8,W16,W32,W64,W128,W256,FENCE,ALLOC,FREE }
    public record Step(Op op,List<Long> values,long returned) { }
    public record Scene(String name,long container,long elementPointer,long moduleBase,List<Step> steps,long expectedReturn) { }
}
