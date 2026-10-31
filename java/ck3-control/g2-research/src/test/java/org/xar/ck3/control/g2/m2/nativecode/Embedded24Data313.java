package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
/** Frozen pureDATA before target/literal proposals; strictglobaltrace only. */
public final class Embedded24Data313 {
    private Embedded24Data313() { }
    public enum Op { R32,R64,R128,W32,W64,W128,ALLOC,RELEASE }
    public record Step(Op op,List<Long> values,long returned) { }
    public record Scene(String name,long destination,long source,List<Step> steps,long expectedReturn) { }
}
