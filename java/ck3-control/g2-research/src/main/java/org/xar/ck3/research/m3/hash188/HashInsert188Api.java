package org.xar.ck3.research.m3.hash188;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Explicit normal storage/known-argument projection of complete C39C60; not a CPU/ABI/EH emulator. */
public final class HashInsert188Api {
    private HashInsert188Api() { }
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
        default int equal3f6d2b0(Memory memory, long siteRva, long rcx, long rdx, long sourceEntryRsp) {
            return equal3f6d2b0(memory, siteRva, rcx, rdx);
        }
        void copy855f00(Memory memory, long siteRva, long rcx, long rdx);
        void assign855db0(Memory memory, long siteRva, long rcx, long rdx, long r8);
        void rehashC3a400(Memory memory, long siteRva, long map);
        void insertC3b960(Memory memory, long siteRva, long map, long result, int hash, long descriptor);
        void destroy856050(Memory memory, long siteRva, long descriptor);
        int capacity86e160(Memory memory, long siteRva, int ecx, int edx);
        void reserveC3b700(Memory memory, long siteRva, long map, int edx);
        void overflow86f210(Memory memory, long siteRva, long rcx, long rdx);
        void terminal4232cf4(Memory memory, long siteRva);
        default void terminal4232cf4(Memory memory, long siteRva, long terminalEntryRsp) {
            terminal4232cf4(memory, siteRva);
        }
    }
    /** Actual INT3 boundary reached only if the source's terminal call returns; no invented noreturn proof. */
    public static final class UnprojectedInt3 extends RuntimeException {
        private static final long serialVersionUID = 1L;
        public UnprojectedInt3() { super("C39F8D INT3 is outside the normal projection"); }
    }
}
