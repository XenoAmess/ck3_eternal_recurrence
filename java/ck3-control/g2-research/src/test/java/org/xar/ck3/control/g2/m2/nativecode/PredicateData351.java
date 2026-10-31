package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
public final class PredicateData351 {
    private PredicateData351() { }
    public enum Op { R8,R32,R64 }
    public record Step(Op op,List<Long> values,long returned) { }
    public record Scene(String name,long receiver,List<Step> steps,int expectedAL) { }
}
