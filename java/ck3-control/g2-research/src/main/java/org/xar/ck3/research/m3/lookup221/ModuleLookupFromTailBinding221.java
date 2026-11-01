package org.xar.ck3.research.m3.lookup221;

import org.xar.ck3.research.m3.tail217.TerminalTailTarget217Api;
import org.xar.ck3.research.m3.abort220.TerminalAbort220Api;
import org.xar.ck3.research.m3.lookup221.ModuleLookup221Api;

/** Lookup-from-tail binding: active call42422d0@424222A delegates to algorithm; others fallback. */
public final class ModuleLookupFromTailBinding221 {
    private ModuleLookupFromTailBinding221() { }

    public static TerminalTailTarget217Api.Ports bind(
            TerminalAbort220Api.Memory captured,
            long moduleBase,
            ModuleLookup221Api algorithm,
            ModuleLookup221Api.Ports child,
            TerminalTailTarget217Api.Ports fallback) {
        return new TerminalTailTarget217Api.Ports() {
            @Override
            public long call43da620(TerminalTailTarget217Api.Memory memory, long siteRva, long actualTarget, int ecx) {
                return fallback.call43da620(memory, siteRva, actualTarget, ecx);
            }

            @Override
            public void call42422d0(TerminalTailTarget217Api.Memory memory, long siteRva, int ecx) {
                fallback.call42422d0(memory, siteRva, ecx);
            }

            @Override
            public long call42420c0(TerminalTailTarget217Api.Memory memory, long siteRva, long rcx, long rdx, long r8, long r9) {
                return fallback.call42420c0(memory, siteRva, rcx, rdx, r8, r9);
            }

            @Override
            public void call4242284(TerminalTailTarget217Api.Memory memory, long siteRva, int ecx) {
                fallback.call4242284(memory, siteRva, ecx);
            }

            @Override
            public void call42422d0(TerminalTailTarget217Api.Memory memory, long siteRva, int ecx, long calleeEntryRsp) {
                if (memory != captured || siteRva != 0x424222AL) {
                    throw new IllegalArgumentException("Wrong memory or site for active call42422d0");
                }
                ModuleLookup221Api.Input input = new ModuleLookup221Api.Input(moduleBase, ecx, new ModuleLookup221Api.Scratch(calleeEntryRsp));
                algorithm.execute(captured, child, input);
            }

            @Override
            public void call4242284(TerminalTailTarget217Api.Memory memory, long siteRva, int ecx, long calleeEntryRsp) {
                fallback.call4242284(memory, siteRva, ecx, calleeEntryRsp);
            }
        };
    }
}