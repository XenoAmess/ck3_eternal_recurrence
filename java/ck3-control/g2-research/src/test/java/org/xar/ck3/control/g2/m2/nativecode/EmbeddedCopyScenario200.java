package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
public final class EmbeddedCopyScenario200 {
    private EmbeddedCopyScenario200() { }
    public enum Op { W8, W16, W32, W64, R32, R128, W128, C889, C37282, C260, C37271 }
    public record Step(Op op, long a, long b, long c) { }
    public record Scene(String name, long destination, long source, long moduleBase,
            List<Step> steps) { }
}
