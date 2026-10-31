package org.xar.ck3.research.m3.map191;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Explicit normal storage/known-argument projection of complete C3B960; not a CPU/ABI/EH emulator. */
public final class MapInsert191Api {
    private MapInsert191Api() { }
    public record Bytes16(long low, long high) { }
    public interface Memory extends NativeTaskMemory {
        int readUnsigned8(long address);
        void write8(long address, int value);
        Bytes16 read128(long address);
        void write128(long address, Bytes16 value);
    }
    /** Original post-prologue RSP; RBP=bodyRsp+0x70 and entryRSP=bodyRsp+0xA8. */
    public record Scratch(long bodyRsp) { }
    public record Input(long moduleBase, long map, long output, int hash, long descriptor, Scratch scratch) { }
    /** Every callback receives the identical Memory. Only source-established arguments are projected. */
    public interface Ports {
        int equal3f6d2b0(Memory memory, long siteRva, long rcx, long rdx);
        /** Actual source-entry RSP after the caller CALL push; old ports remain source-compatible. */
        default int equal3f6d2b0(Memory memory, long siteRva, long rcx, long rdx, long sourceEntryRsp) {
            return equal3f6d2b0(memory, siteRva, rcx, rdx);
        }
        void insertSlotC3cf10(Memory memory, long siteRva, long bucket, int probe, int hash, long descriptor);
        void rehashC3a400(Memory memory, long siteRva, long map);
        default void rehashC3a400(Memory memory, long siteRva, long map, long sourceEntryRsp) {
            rehashC3a400(memory, siteRva, map);
        }
        void insertC3a5f0(Memory memory, long siteRva, long map, long result, int hash, long descriptor);
        void destroy856050(Memory memory, long siteRva, long descriptor);
        int capacity86e160(Memory memory, long siteRva, int ecx, int edx);
        void reserveC3b700(Memory memory, long siteRva, long map, int edx);
        default void reserveC3b700(Memory memory, long siteRva, long map, int edx, long sourceEntryRsp) {
            reserveC3b700(memory, siteRva, map, edx);
        }
        void overflow86f210(Memory memory, long siteRva, long rcx, long rdx);
        void terminal4232cf4(Memory memory, long siteRva);
    }
    /** Actual INT3 boundary reached only if the source's terminal call returns; no invented noreturn proof. */
    public static final class UnprojectedInt3 extends RuntimeException {
        private static final long serialVersionUID = 1L;
        public UnprojectedInt3() { super("C3BC8D INT3 is outside the normal projection"); }
    }
}
