package org.xar.ck3.research.m3.f800244;

import java.util.Objects;
import org.xar.ck3.research.m3.f8a8242.F8a8Api242.Memory;

/** Normal supplied-storage business projection; physical NV, CPU and EH excluded. */
public final class F800Api244 {
    private F800Api244() { }

    /** Actual post-CALL entry RSP, without a synthesized physical frame. */
    public record Scratch(long entryRsp) { }

    public record Input(long rdxAddress, long r8Address, long r9Address, Scratch scratch) {
        public Input { Objects.requireNonNull(scratch, "scratch"); }
    }

    public interface Ports {
        void call4247ffc(Memory memory, long siteRva, int ecxBits);
        void call4248050(Memory memory, long siteRva, int ecxBits, long liveRbx);
        void call424fa90(Memory memory, long siteRva, long knownRcx, long knownRdx, long liveRax);
    }
}
