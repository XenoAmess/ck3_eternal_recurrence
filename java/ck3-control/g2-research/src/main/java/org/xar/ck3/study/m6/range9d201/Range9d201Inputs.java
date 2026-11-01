package org.xar.ck3.study.m6.range9d201;

public final class Range9d201Inputs {
    private Range9d201Inputs() { }
    public record Input(long beginRaw64, long middleRaw64, long endRaw64, long entryR9Raw64) { }
    public interface Calls {
        /** First call: all four original argument registers have source-qualified values. */
        void first4220aa4(long rcxRaw64, long rdxRaw64, long r8Raw64, long r9Raw64);
        /** Later calls qualify only RCX/RDX; other call state is unknown, not a full two-argument ABI. */
        void later4220aa4(long rcxRaw64, long rdxRaw64);
    }
}
