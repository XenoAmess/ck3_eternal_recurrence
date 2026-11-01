package org.xar.ck3.research.m3.tail212;

import org.xar.ck3.research.m3.terminal207.Terminal207Api;
import org.xar.ck3.research.m3.tail212.TerminalTail212Api;

public final class TerminalTailBinding212 {
    private TerminalTailBinding212() { }

    public static Terminal207Api.Ports bind(Terminal207Api.Memory capturedMemory, TerminalTail212Api.Ports tailPorts, Terminal207Api.Ports fallback) {
        if (capturedMemory == null || tailPorts == null || fallback == null) {
            throw new IllegalArgumentException("Null binding component");
        }

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
            public int call43da258(Terminal207Api.Memory memory, long siteRva, long code, int ecx) {
                return fallback.call43da258(memory, siteRva, code, ecx);
            }

            @Override
            public void call423283c(Terminal207Api.Memory memory, long siteRva, int ecx, int edx, int r8d) {
                fallback.call423283c(memory, siteRva, ecx, edx, r8d);
            }

            @Override
            public void call4242354(Terminal207Api.Memory memory, long siteRva, int ecx) {
                if (memory != capturedMemory) {
                    throw new IllegalArgumentException("Memory identity mismatch");
                }
                if (siteRva != 0x4232D44L) {
                    throw new IllegalArgumentException("Site mismatch");
                }
                long rcx = Integer.toUnsignedLong(ecx);
                Tail4242354.execute(memory, tailPorts, rcx);
            }
        };
    }
}