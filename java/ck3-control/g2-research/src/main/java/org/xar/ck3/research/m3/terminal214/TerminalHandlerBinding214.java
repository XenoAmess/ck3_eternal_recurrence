package org.xar.ck3.research.m3.terminal214;

import org.xar.ck3.research.m3.terminal207.Terminal207Api;
import org.xar.ck3.research.m3.terminal214.Terminal4247004Api214;

public final class TerminalHandlerBinding214 {
    private TerminalHandlerBinding214() { }

    public static Terminal207Api.Ports bind(
            Terminal4247004Api214.Memory capturedMemory,
            Terminal4247004Api214.Ports childPorts,
            Terminal207Api.Ports fallback,
            long moduleBase) {
        return new Terminal207Api.Ports() {
            @Override
            public long call4246fb4(Terminal207Api.Memory memory, long siteRva) {
                return fallback.call4246fb4(memory, siteRva);
            }

            @Override
            public long call4246fb4(Terminal207Api.Memory memory, long siteRva, long calleeEntryRsp) {
                return fallback.call4246fb4(memory, siteRva, calleeEntryRsp);
            }

            @Override
            public void call4247004(Terminal207Api.Memory memory, long siteRva, int ecx) {
                fallback.call4247004(memory, siteRva, ecx);
            }

            @Override
            public void call4247004(Terminal207Api.Memory memory, long siteRva, int ecx, long calleeEntryRsp) {
                if (memory != capturedMemory) {
                    throw new IllegalArgumentException("Memory mismatch");
                }
                if (siteRva != 0x4232D07L) {
                    throw new IllegalArgumentException("Site mismatch");
                }
                Terminal4247004Api214.Input input = new Terminal4247004Api214.Input(
                        moduleBase,
                        ecx,
                        new Terminal4247004Api214.Scratch(calleeEntryRsp));
                Terminal4247004Api214.Outcome outcome = TerminalHandler4247004.execute(
                        capturedMemory, childPorts, input);
                if (outcome instanceof Terminal4247004Api214.Trap) {
                    throw new UnsupportedOperationException("Trap.INT3_424726D");
                }
            }

            @Override
            public int call43da258(Terminal207Api.Memory memory, long siteRva, long code, int ecx) {
                return fallback.call43da258(memory, siteRva, code, ecx);
            }

            @Override
            public void call423283c(Terminal207Api.Memory memory, long siteRva, int ecx, int edx, int r8d) {
                fallback.call423283c(memory, siteRva, ecx, edx, r8d);
            }

            @Override
            public void call423283c(Terminal207Api.Memory memory, long siteRva, int ecx, int edx, int r8d, long calleeEntryRsp) {
                fallback.call423283c(memory, siteRva, ecx, edx, r8d, calleeEntryRsp);
            }

            @Override
            public void call4242354(Terminal207Api.Memory memory, long siteRva, int ecx) {
                fallback.call4242354(memory, siteRva, ecx);
            }

            @Override
            public void call4242354(Terminal207Api.Memory memory, long siteRva, int ecx, long calleeEntryRsp) {
                fallback.call4242354(memory, siteRva, ecx, calleeEntryRsp);
            }
        };
    }
}