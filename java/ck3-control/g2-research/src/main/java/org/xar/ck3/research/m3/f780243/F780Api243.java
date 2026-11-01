package org.xar.ck3.research.m3.f780243;

import java.util.Objects;
import org.xar.ck3.research.m3.f8a8242.F8a8Api242;

/** Explicit supplied-storage business projection; physical NV, CPU and EH excluded. */
public final class F780Api243 {
    private F780Api243() { }

    /** Same backing bytes at every width; one supplied atomic DWORD increment effect. */
    public interface Memory extends F8a8Api242.Memory {
        void atomicIncrementInt32(long address);
    }

    /** Actual post-CALL entry RSP, without validation or synthesized frame values. */
    public record Scratch(long entryRsp) { }

    public record Input(long rdxAddress, long r8Address, long r9Address, Scratch scratch) {
        public Input { Objects.requireNonNull(scratch, "scratch"); }
    }

    public interface Ports {
        void call4247ffc(Memory memory, long siteRva, int ecxBits);
        void call4248050(Memory memory, long siteRva, int ecxBits, long liveRbx);
    }
}
