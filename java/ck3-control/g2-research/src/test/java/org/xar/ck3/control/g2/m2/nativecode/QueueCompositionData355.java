package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
public final class QueueCompositionData355 {
    private QueueCompositionData355() { }
    public enum Op { R8,R32,R64,W8,W32,W64,CAS,PAUSE,ALLOC,FREE,COPY }
    public record Step(Op op,List<Long> values,long returned) { }
    public record Scene(String name,long receiver,long moduleBase,long stackSlot,List<Step> steps) { }
}
