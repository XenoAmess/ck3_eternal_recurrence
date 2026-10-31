package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
public final class CopyWitnessData370 {
    private CopyWitnessData370() { }
    public enum Target { SMALL,REP,DISPATCH,SSE,AVX,BACKWARD }
    public enum Op { R8,R16,R32,R64,R128,R256,W8,W16,W32,W64,W128,W256,FENCE }
    public record Step(Op op,List<Long> values,long returned) {
        public Step { values=List.copyOf(values); }
    }
    public record Scene(String name,Target target,long destination,long source,long bytes,long moduleBase,List<Step> steps,long expectedReturn) {
        public Scene { steps=List.copyOf(steps); }
    }
}
