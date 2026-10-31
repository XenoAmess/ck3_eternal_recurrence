package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
/** Frozen pure DATA, before witness proposals; global trace only. */
public final class SlotKnownCompositionData286 {
    private SlotKnownCompositionData286() { }
    public enum Op { R8,R32,R64,R128,W8,W16,W32,W64,W128,C889,C37282,C260,C37271,
        INIT10,INIT20,RANGEALLOC,RANGERELEASE,COPY,FINALIZE,REGISTRY,TAIL10,PAGE,SLOTALLOC,SLOTRELEASE,SET,
        PREP_ELEMENTS,ALLOC_ELEMENTS,REPLACE_ELEMENTS,DESTROY_ELEMENTS,COPY16_HEAD,COPY4_HEAD,COPY16_RANGE,COPY4_RANGE,ALLOC24,RELEASE24 }
    public record Step(Op op,List<Long> values,long returned) { }
    public record Scene(String name,PendingSlotProducer2A32770.Input input,List<Step> steps,long expectedReturn) { }
}