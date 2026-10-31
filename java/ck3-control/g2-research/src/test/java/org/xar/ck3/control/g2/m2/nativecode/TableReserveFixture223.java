package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
public final class TableReserveFixture223 {
    private TableReserveFixture223() { }
    public enum Kind { R32,R64,W32,W64,ALLOC,RELEASE,FREE }
    public record Step(Kind kind,long address,long value,long a,long b,long c) { }
    public record Scene(String name,long table,int desired,List<Step> steps) { }
}
