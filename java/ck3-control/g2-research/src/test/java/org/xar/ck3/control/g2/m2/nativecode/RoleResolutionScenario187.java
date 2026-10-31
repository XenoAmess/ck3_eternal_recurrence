package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;

/** Frozen data-only witness protocol. Values and expected results are not supplied here. */
public final class RoleResolutionScenario187 {
    private RoleResolutionScenario187() { }
    public enum Op { R32, R64, W32 }
    public record Step(Op op, long address, long value) { }
    public record Scene(String name, long component, long context, long moduleBase,
            List<Step> steps, long r14, long r15, long rdi) { }
}
