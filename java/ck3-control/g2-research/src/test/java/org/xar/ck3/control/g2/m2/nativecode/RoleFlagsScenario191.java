package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
/** Data-only frozen strict-script shape, no expected values supplied. */
public final class RoleFlagsScenario191 {
    private RoleFlagsScenario191() { }
    public enum Op { R8, R32, R64, W8, CALL }
    public record Step(Op op, long address, long value) { }
    public record Scene(String name, long component, long context, long r14,
            long r15, long rdi, List<Step> steps) { }
}
