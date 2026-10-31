package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
public final class ContextCopyScenario195 {
    private ContextCopyScenario195() { }
    public enum Op { R32, R64, W32, W64, R128, W128, C373, C105, CBCB, C250 }
    public record Step(Op op, long a, long b, long c, long d) { }
    public record Scene(String name, long destination, long source, List<Step> steps) { }
}
