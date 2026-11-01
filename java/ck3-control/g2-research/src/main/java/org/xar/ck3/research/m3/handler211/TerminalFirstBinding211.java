package org.xar.ck3.research.m3.handler211;

import org.xar.ck3.research.m3.terminal207.Terminal207Api;
import org.xar.ck3.research.m3.handler211.Wrapper4246FB4Api211;

public final class TerminalFirstBinding211 {

    public static Terminal207Api.Ports bind(
            Terminal207Api.Memory capturedMemory,
            Wrapper4246FB4Api211.Ports childPorts,
            Terminal207Api.Ports fallback) {
        if (capturedMemory == null) throw new NullPointerException("capturedMemory");
        if (childPorts == null) throw new NullPointerException("childPorts");
        if (fallback == null) throw new NullPointerException("fallback");

        return new Terminal207Api.Ports() {
            @Override
            public long call4246fb4(Terminal207Api.Memory m, long siteRva) {
                return fallback.call4246fb4(m, siteRva);
            }

            @Override
            public long call4246fb4(Terminal207Api.Memory m, long siteRva, long calleeEntryRsp) {
                if (m != capturedMemory) {
                    throw new IllegalArgumentException("Foreign memory instance passed to call4246fb4");
                }
                if (siteRva != 0x4232CF8L) {
                    throw new IllegalArgumentException("Wrong site RVA passed to call4246fb4: " + Long.toHexString(siteRva));
                }
                return HandlerWrapper4246FB4.execute(m, childPorts, calleeEntryRsp);
            }

            @Override
            public void call4247004(Terminal207Api.Memory m, long siteRva, int ecx) {
                fallback.call4247004(m, siteRva, ecx);
            }

            @Override
            public void call4247004(Terminal207Api.Memory m, long siteRva, int ecx, long calleeEntryRsp) {
                fallback.call4247004(m, siteRva, ecx, calleeEntryRsp);
            }

            @Override
            public int call43da258(Terminal207Api.Memory m, long siteRva, long code, int ecx) {
                return fallback.call43da258(m, siteRva, code, ecx);
            }

            @Override
            public void call423283c(Terminal207Api.Memory m, long siteRva, int ecx, int edx, int r8d) {
                fallback.call423283c(m, siteRva, ecx, edx, r8d);
            }

            @Override
            public void call423283c(Terminal207Api.Memory m, long siteRva, int ecx, int edx, int r8d, long calleeEntryRsp) {
                fallback.call423283c(m, siteRva, ecx, edx, r8d, calleeEntryRsp);
            }

            @Override
            public void call4242354(Terminal207Api.Memory m, long siteRva, int ecx) {
                fallback.call4242354(m, siteRva, ecx);
            }
        };
    }
}