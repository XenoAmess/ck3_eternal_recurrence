package org.xar.ck3.research.m3;

public final class FreeEffectsApi170 {
    private FreeEffectsApi170() {}
    public enum Kind { SKIPPED_INLINE, SKIPPED_NULL, UNSUPPORTED_SELECTOR, UNSUPPORTED_RELEASE, CALLEE_RETURNED }
    public record Targets(long selectorCode,long globalReleaseCode) {}
    public record Outcome(Kind kind,long observedCode) {}
}
