package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
public final class SlotGrowthComposedFixture247 {
    private SlotGrowthComposedFixture247() { }
    public enum Kind { R8,R32,R64,W32,W64,ALLOC,RELEASE,COPY,SET }
    public record Step(Kind kind,long address,long value,long a,long b,long c) { }
    public record Scene(String name,long table,int requested,boolean expectedAl,List<Step> steps) { }
}
