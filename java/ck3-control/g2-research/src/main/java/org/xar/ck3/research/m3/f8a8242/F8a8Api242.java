package org.xar.ck3.research.m3.f8a8242;

import java.util.Objects;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Supplied-storage normal business projection of 424F8A8; no CPU or EH contract. */
public final class F8a8Api242 {
    private F8a8Api242() { }

    /** Same backing bytes as the inherited widths; store exactly the low 16 bits. */
    public interface Memory extends NativeTaskMemory {
        void writeInt16(long address, int valueBits);
    }

    /** Actual post-CALL entry E; source RBP is E minus 8. */
    public record Scratch(long entryRsp) {
        public long frameRbp() { return entryRsp - 8L; }
    }

    public record Input(long moduleBase, long blockBits, Scratch scratch) {
        public Input { Objects.requireNonNull(scratch, "scratch"); }
    }

    public interface Ports {
        void call424f780(Memory memory, long siteRva, long rcx, long rdx, long r8, long r9);
        void call424f800(Memory memory, long siteRva, long rcx, long rdx, long r8, long r9);
        default void call424f780(Memory memory, long siteRva, long rcx, long rdx, long r8, long r9, long calleeEntryRsp) {
            call424f780(memory, siteRva, rcx, rdx, r8, r9);
        }
        default void call424f800(Memory memory, long siteRva, long rcx, long rdx, long r8, long r9, long calleeEntryRsp) {
            call424f800(memory, siteRva, rcx, rdx, r8, r9);
        }
    }
}
