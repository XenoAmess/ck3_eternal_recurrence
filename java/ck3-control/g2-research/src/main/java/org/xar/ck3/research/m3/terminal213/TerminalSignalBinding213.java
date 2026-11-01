package org.xar.ck3.research.m3.terminal213;

import org.xar.ck3.research.m3.terminal207.Terminal207Api;
import org.xar.ck3.research.m3.terminal213.TerminalSignal213Api;

public final class TerminalSignalBinding213 {
    private TerminalSignalBinding213() { }

    public static Terminal207Api.Ports bind(Terminal207Api.Memory capturedMemory, TerminalSignal213Api.Ports childPorts, Terminal207Api.Ports fallback, long moduleBase) {
        if (capturedMemory == null) throw new IllegalArgumentException("capturedMemory");
        if (childPorts == null) throw new IllegalArgumentException("childPorts");
        if (fallback == null) throw new IllegalArgumentException("fallback");

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
                fallback.call4247004(memory, siteRva, ecx, calleeEntryRsp);
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
                if (memory != capturedMemory) {
                    throw new IllegalArgumentException("Memory identity mismatch");
                }
                if (siteRva != 0x4232D3AL) {
                    throw new IllegalArgumentException("Site mismatch");
                }
                capturedMemory.writeInt64(calleeEntryRsp, moduleBase + 0x4232D3FL);
                TerminalSignal423283C.execute(capturedMemory, childPorts, new TerminalSignal213Api.Input(moduleBase, calleeEntryRsp, ecx, edx, r8d));
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