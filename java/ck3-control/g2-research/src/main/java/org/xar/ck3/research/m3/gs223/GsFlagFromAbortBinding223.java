package org.xar.ck3.research.m3.gs223;

import org.xar.ck3.research.m3.abort220.TerminalAbort220Api;
import org.xar.ck3.research.m3.gs223.GsFlag223Api;

/** Wiring for abort220 ports: only call42591f8@424228C active via new4; others exact fallback. */
public final class GsFlagFromAbortBinding223 {
    private GsFlagFromAbortBinding223() { }

    public static TerminalAbort220Api.Ports bind(
            TerminalAbort220Api.Memory captured,
            GsFlag223Api.Ports child,
            TerminalAbort220Api.Ports fallback) {
        return new TerminalAbort220Api.Ports() {
            @Override
            public int call42591f8(TerminalAbort220Api.Memory memory, long siteRva, int entryEcx) {
                return fallback.call42591f8(memory, siteRva, entryEcx);
            }

            @Override
            public long readGs60(TerminalAbort220Api.Memory memory, long siteRva) {
                return fallback.readGs60(memory, siteRva);
            }

            @Override
            public long call43da798(TerminalAbort220Api.Memory memory, long siteRva, long actualTarget, long liveRax, int liveEdx) {
                return fallback.call43da798(memory, siteRva, actualTarget, liveRax, liveEdx);
            }

            @Override
            public void call43da778(TerminalAbort220Api.Memory memory, long siteRva, long actualTarget, long rcx, int edx) {
                fallback.call43da778(memory, siteRva, actualTarget, rcx, edx);
            }

            @Override
            public void call42422d0(TerminalAbort220Api.Memory memory, long siteRva, int ecx, long childEntryRsp) {
                fallback.call42422d0(memory, siteRva, ecx, childEntryRsp);
            }

            @Override
            public void call43da558(TerminalAbort220Api.Memory memory, long siteRva, long actualTarget, int ecx) {
                fallback.call43da558(memory, siteRva, actualTarget, ecx);
            }

            @Override
            public int call42591f8(TerminalAbort220Api.Memory memory, long siteRva, int entryEcx, long childEntryRsp) {
                if (memory != captured || siteRva != 0x424228CL) {
                    throw new IllegalArgumentException("Wrong memory or site for active call42591f8");
                }
                GsFlag223Api.Scratch scratch = new GsFlag223Api.Scratch(childEntryRsp);
                return GsFlag42591F8.execute(captured, child, scratch);
            }
        };
    }
}