package org.xar.ck3.research.m3.dispatch218;

import org.xar.ck3.research.m3.tail217.TerminalTailTarget217Api;
import org.xar.ck3.research.m3.dispatch218.DispatchHelper218Api;

/** Actual217 binder: only call42420c0@4242266 active; other ports exact fallback. */
public final class DispatchHelperBinding218 {
    private DispatchHelperBinding218() { }

    public static TerminalTailTarget217Api.Ports bind(TerminalTailTarget217Api.Memory captured, DispatchHelper218Api.Ports child, TerminalTailTarget217Api.Ports fallback) {
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
                if (memory != captured || siteRva != 0x4242266L) {
                    throw new IllegalArgumentException("Wrong memory or site for active call42420c0");
                }
                DispatchHelper218Api.Input input = new DispatchHelper218Api.Input(rdx, r8, r9);
                return DispatchHelper42420C0.execute(captured, child, input);
            }

            @Override
            public long call42420c0(TerminalTailTarget217Api.Memory memory, long siteRva, long rcx, long rdx, long r8, long r9, long calleeEntryRsp) {
                if (memory != captured || siteRva != 0x4242266L) {
                    throw new IllegalArgumentException("Wrong memory or site for active call42420c0");
                }
                DispatchHelper218Api.Input input = new DispatchHelper218Api.Input(rdx, r8, r9);
                return DispatchHelper42420C0.execute(captured, child, input, calleeEntryRsp);
            }

            @Override
            public void call4242284(TerminalTailTarget217Api.Memory memory, long siteRva, int ecx) {
                fallback.call4242284(memory, siteRva, ecx);
            }

            @Override
            public void call4242284(TerminalTailTarget217Api.Memory memory, long siteRva, int ecx, long calleeEntryRsp) {
                fallback.call4242284(memory, siteRva, ecx, calleeEntryRsp);
            }
        };
    }
}