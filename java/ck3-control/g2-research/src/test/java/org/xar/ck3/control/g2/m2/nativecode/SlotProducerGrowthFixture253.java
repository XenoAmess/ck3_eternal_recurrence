package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
public final class SlotProducerGrowthFixture253 {
    private SlotProducerGrowthFixture253() { }
    public enum Kind { R8,W8,R32,R64,W32,W64,ALLOC,RELEASE,COPY,SET,PAGE }
    public record Step(Kind kind,long address,long value,long a,long b,long c) { }
    public record Scene(String name,PendingSlotProducer2A32770.Input input,
            long expectedReturn,List<Step> steps) { }
}
