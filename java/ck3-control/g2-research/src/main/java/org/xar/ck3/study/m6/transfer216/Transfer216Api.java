package org.xar.ck3.study.m6.transfer216;

/** Normal-body logical RAM contract. No full ABI, native authority or exception-language claim. */
public final class Transfer216Api {
    private Transfer216Api() { }
    /** frameRaw64 is RSP after this body's prologue. Recursive child frame is parent-0x480. */
    public record Input(long destinationRaw64, long sourceRaw64, long imageBaseRaw64, long frameRaw64) { }
    public record Bits128(long low, long high) { }
    public interface Memory extends org.xar.ck3.study.m6.element150.Element150Inputs.Memory {
        default Bits128 read128(long address) { return new Bits128(read64(address), read64(address + 8)); }
        default void write128(long address, Bits128 value) { write64(address, value.low()); write64(address + 8, value.high()); }
    }
    /** Actual vtable+8/+16 call boundaries remain opaque. Callbacks may change this same RAM. */
    public interface Calls {
        long allocate08(long functionRaw64, long allocatorRaw64, long bytesRaw64, int alignment, int callsiteRva);
        void release16(long functionRaw64, long allocatorRaw64, long pointerRaw64, int alignment, int callsiteRva);
    }
    /** Owner supplies a finite execution bound; exhaustion is a software boundary, not a native exception. */
    @FunctionalInterface public interface Budget { void step(); }
    @FunctionalInterface public interface Operation {
        long run(Input input, Memory memory, Calls calls, Budget budget);
    }
}
