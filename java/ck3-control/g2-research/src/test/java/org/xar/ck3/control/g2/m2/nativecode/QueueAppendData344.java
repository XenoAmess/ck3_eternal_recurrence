package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
public final class QueueAppendData344 {
    private QueueAppendData344() { }
    public enum Op { R32,R64,W32,W64,ALLOC,FREE,COPY }
    public record Step(Op op,List<Long> values,long returned) { }
    public record Scene(String name,long container,long elementPointer,long moduleBase,List<Step> steps,long expectedReturn) { }
}
