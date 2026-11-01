package org.xar.ck3.research.m3.abort220;

import org.xar.ck3.research.m3.tail217.TerminalTailTarget217Api;
import org.xar.ck3.research.m3.lookup221.ModuleLookup221Api;

/** Supplied-storage 74B business boundary only; no full CPU or hardware trap promise. */
public interface TerminalAbort220Api {
    /** Actual same storage is compatible with the outer217 and nested91B business interfaces. */
    interface Memory extends TerminalTailTarget217Api.Memory, ModuleLookup221Api.Memory { }
    record Scratch(long entryRsp) { }
    record Input(long moduleBase, int ecx, Scratch scratch) { }
    interface Ports {
        int call42591f8(Memory memory, long siteRva, int entryEcx);
        default int call42591f8(Memory memory, long siteRva, int entryEcx, long childEntryRsp) {
            return call42591f8(memory, siteRva, entryEcx);
        }
        /** Exact GS-relative offset0x60 observation at the named instruction; not GS0x58. */
        long readGs60(Memory memory, long siteRva);
        long call43da798(Memory memory, long siteRva, long actualTarget, long liveRax, int liveEdx);
        void call43da778(Memory memory, long siteRva, long actualTarget, long rcx, int edx);
        void call42422d0(Memory memory, long siteRva, int ecx, long childEntryRsp);
        void call43da558(Memory memory, long siteRva, long actualTarget, int ecx);
    }
    enum Trap { INT3_42422CD }
}
