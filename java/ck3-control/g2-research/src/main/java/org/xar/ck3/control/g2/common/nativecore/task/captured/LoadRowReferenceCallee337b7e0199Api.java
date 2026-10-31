package org.xar.ck3.control.g2.common.nativecore.task.captured;

/** Narrow SSE ports required by the source; no native FP environment is inferred. */
public final class LoadRowReferenceCallee337b7e0199Api {
    private LoadRowReferenceCallee337b7e0199Api() { }

    /** Current floating environment is supplied by the owner. Methods may reject or raise.
     * Normal returns must match the actual signed conversion, DIVSS and COMISS semantics.
     * No default rounding mode, MXCSR exception handling, or native provider is supplied.
     */
    public interface Float32 {
        int convertSignedDwordToFloatBits(int signedDwordBits);
        int divideScalarFloatBits(int dividendFloatBits, int divisorFloatBits);
        /** COMISS followed by JA: false for unordered or equal/less on a normal compare. */
        boolean orderedAbove(int leftFloatBits, int rightFloatBits);
    }
}
