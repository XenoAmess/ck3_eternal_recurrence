package org.xar.ck3.research.m3.lookup221;

import org.xar.ck3.research.m3.abort220.TerminalAbort220Api;
import org.xar.ck3.research.m3.tail217.TerminalTailTarget217Api;

/** Wiring for abort220 ports: only call42422d0@42422C0 active; others exact fallback. */
public final class ModuleLookupFromAbortBinding221 {
    private ModuleLookupFromAbortBinding221() { }

    public static TerminalAbort220Api.Ports bind(
            TerminalAbort220Api.Memory captured,
            long moduleBase,
            ModuleLookup221Api algorithm,
            ModuleLookup221Api.Ports child,
            TerminalAbort220Api.Ports fallback) {
        return new TerminalAbort220Api.Ports() {
            @Override
            public int call42591f8(TerminalAbort220Api.Memory memory, long siteRva, int entryEcx) {
                return fallback.call42591f8(memory, siteRva, entryEcx);
            }

            @Override
            public int call42591f8(TerminalAbort220Api.Memory memory, long siteRva, int entryEcx, long childEntryRsp) {
                return fallback.call42591f8(memory, siteRva, entryEcx, childEntryRsp);
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
                if (memory != captured || siteRva != 0x42422C0L) {
                    throw new IllegalArgumentException("Wrong memory or site for active call42422d0");
                }
                ModuleLookup221Api.Input input = new ModuleLookup221Api.Input(moduleBase, ecx, new ModuleLookup221Api.Scratch(childEntryRsp));
                algorithm.execute(captured, child, input);
            }

            @Override
            public void call43da558(TerminalAbort220Api.Memory memory, long siteRva, long actualTarget, int ecx) {
                fallback.call43da558(memory, siteRva, actualTarget, ecx);
            }
        };
    }
}