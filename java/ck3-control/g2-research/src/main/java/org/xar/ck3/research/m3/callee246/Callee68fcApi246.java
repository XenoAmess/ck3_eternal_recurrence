package org.xar.ck3.research.m3.callee246;

import org.xar.ck3.research.m3.f8a8242.F8a8Api242;

/** Supplied-storage business effects of 42568FC; physical CPU and EH excluded. */
public final class Callee68fcApi246 {
    private Callee68fcApi246() { }

    /** All inherited widths and this single update observe the same backing bytes. */
    public interface Memory extends F8a8Api242.Memory {
        /** One 32-bit wrapping add effect; callers must not split it into reads/writes. */
        void atomicAddInt32(long address, int deltaBits);
    }

    public record Input(long moduleBase, long entryRcx) { }

    public interface Ports {
        /** Five established full64 values immediately before the opaque source CALL. */
        void call42568d4(Memory memory, long siteRva, long knownRcx, long knownRdx,
                long liveRax, long knownR8, long knownR9);
    }
}
