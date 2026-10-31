package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
/** PureDATA before modelPOST; strict global trace only, no target-generated expected or completeRAM claim. */
public final class ContextCompositionData282 {
    private ContextCompositionData282() { }
    public enum Op { R8,R32,R64,R128,W8,W16,W32,W64,W128,C889,C37282,C260,C37271,
        INIT10,INIT20,RANGEALLOC,RANGERELEASE,COPY,FINALIZE,REGISTRY,TAIL10 }
    public record Step(Op op,List<Long> values,long returned) { }
    public record Scene(String name,long destination,long source,long moduleBase,
            List<Step> steps,long expectedReturn) { }
}
