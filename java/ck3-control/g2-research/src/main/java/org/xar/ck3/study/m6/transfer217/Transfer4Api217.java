package org.xar.ck3.study.m6.transfer217;

/** Normal logical RAM and explicit call arguments only; not a complete native ABI or authority. */
public final class Transfer4Api217 {
    private Transfer4Api217() { }
    /** frameRaw64 is this selected body's post-prologue RSP, not its caller's RSP. */
    public record Input(long destinationRaw64, long sourceRaw64, long imageBaseRaw64, long frameRaw64) { }
    public interface Memory extends org.xar.ck3.study.m6.element150.Element150Inputs.Memory { }
    /** Bodies of these callees, their other registers/flags, exceptions and natural effects stay unknown. */
    public interface Calls {
        long allocate08(long functionRaw64, long allocatorRaw64, long bytesRaw64, int alignment, int callsiteRva);
        void release16(long functionRaw64, long allocatorRaw64, long pointerRaw64, int alignment, int callsiteRva);
        void copy4226860(long destinationRaw64, long sourceRaw64, long bytesRaw64, int callsiteRva);
        void reverse4220aa4(long beginRaw64, long endRaw64, int callsiteRva);
    }
    @FunctionalInterface public interface Budget { void step(); }
    /** Nominal dispatch to these two supplied bodies. A binder must route to their actual implementations. */
    public interface Operations {
        long move(Input input, Memory memory, Calls calls, Budget budget);
        void swap(Input input, Memory memory, Calls calls, Budget budget);
    }
}
