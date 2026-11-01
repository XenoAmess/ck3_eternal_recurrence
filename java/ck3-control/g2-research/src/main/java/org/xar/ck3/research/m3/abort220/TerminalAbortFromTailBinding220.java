package org.xar.ck3.research.m3.abort220;

import org.xar.ck3.research.m3.tail217.TerminalTailTarget217Api;
import org.xar.ck3.research.m3.abort220.TerminalAbort220Api;

/** Actual217 binder: only call4242284@424227E active; other ports exact fallback. */
public final class TerminalAbortFromTailBinding220 {
    private TerminalAbortFromTailBinding220() { }

    public static TerminalTailTarget217Api.Ports bind(TerminalAbort220Api.Memory captured, long moduleBase, TerminalAbort220Api.Ports child, TerminalTailTarget217Api.Ports fallback) {
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
            public void call42422d0(TerminalTailTarget217Api.Memory memory, long siteRva, int ecx, long calleeEntryRsp) {
                fallback.call42422d0(memory, siteRva, ecx, calleeEntryRsp);
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
            public void call4242284(TerminalTailTarget217Api.Memory memory, long siteRva, int ecx, long calleeEntryRsp) {
                if (memory != captured || siteRva != 0x424227EL) {
                    throw new IllegalArgumentException("Wrong memory or site for active call4242284");
                }
                TerminalAbort220Api.Input input = new TerminalAbort220Api.Input(moduleBase, ecx, new TerminalAbort220Api.Scratch(calleeEntryRsp));
                TerminalAbort220Api.Trap trap = TerminalAbort4242284.execute(captured, child, input);
                throw new UnsupportedOperationException("TerminalAbort4242284 returned softwareTrap");
            }
        };
    }
}