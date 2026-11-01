package org.xar.ck3.research.m3.tail249;

import org.xar.ck3.research.m3.callee246.Callee68fcApi246.Memory;

/** Normal139 business effects through an opaque tail; no RF, UW, CPU or EH claim. */
public final class Tail6670Api249 {
    private Tail6670Api249() { }

    public record Input(long moduleBase, long entryRcx) { }

    public interface Ports {
        /** Four established full64 values; incoming R9 remains unknown and is not invented. */
        void tail4256874(Memory memory, long siteRva, long knownRcx, long knownRdx,
                long liveRax, long knownR8);
    }
}
