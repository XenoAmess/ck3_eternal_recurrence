package org.xar.ck3.research.m3;

/** Supplied-storage normal projection of C3A400 and the complete C3B700 CFG. */
public final class MapRehashApi190 {
    private MapRehashApi190() { }

    public interface Memory extends C3e150Api180.Memory { }

    /** Entry RSP for C3A400 and for its tail-entered C3B700; caller owns all bytes. */
    public record Scratch(long entryRsp) { }

    /** Inherited static-table ports retain their exact C3e150Api180.Memory parameter type. */
    public interface Ports extends C3e150Api180.Ports {
        long allocatorSlot08(Memory memory, long code, long allocator, long bytes, int alignment);
        void allocatorSlot10(Memory memory, long code, long allocator, long block, int alignment);
        /** Known RCX/RDX/R8D/R9 and actual fifth pointer; all effects remain opaque. */
        void callc3b960(Memory memory, long map, long output, int hash, long descriptor, long flagAddress);
        void call856050(Memory memory, long descriptor);
        void call86f210(Memory memory, long output, long map);
        /** No newly established argument register is invented after 86F210. */
        void call4232cf4(Memory memory);
    }

    public enum Completion {
        RETURNED,
        /** The preceding two error calls returned; the source next reaches INT3. */
        UNSUPPORTED_INT3_AFTER_ERROR_CALLS_RETURNED
    }
}
