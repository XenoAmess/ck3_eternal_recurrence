package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
public final class Embedded32Data325 {
    private Embedded32Data325() { }
    public enum Op { R32,R64,R128,W32,W64,W128,PREP,ALLOC,REPLACE,DESTROY,COPY37282,FINALIZE }
    public record Step(Op op,List<Long> values,long returned) { }
    public record Scene(String name,long destination,long source,long moduleBase,List<Step> steps,long expectedReturn) { }
}
