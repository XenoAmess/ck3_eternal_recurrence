package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
public final class ProducerCompositionScenario207 {
    private ProducerCompositionScenario207() { }
    public enum Op { R8,R32,R64,R128,W8,W16,W32,W64,W128,GROW,PAGE,C889,C37282,C260,C37271,C105,CBCB,C250 }
    public record Step(Op op,long a,long b,long c,long d) { }
    public record Scene(String name,PendingSlotProducer2A32770.Input input,
            List<Step> steps,long expected) { }
}
