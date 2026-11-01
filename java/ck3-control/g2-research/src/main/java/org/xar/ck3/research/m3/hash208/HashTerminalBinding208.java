package org.xar.ck3.research.m3.hash208;

import org.xar.ck3.research.m3.hash188.HashInsert188Api;
import org.xar.ck3.research.m3.terminal207.Terminal207Api;
import org.xar.ck3.research.m3.terminal207.Terminal4232CF4;

public final class HashTerminalBinding208 {

    public interface SharedMemory extends HashInsert188Api.Memory, Terminal207Api.Memory {
    }

    public static HashInsert188Api.Ports bind(SharedMemory capturedMemory, long moduleBase, Terminal207Api.Ports terminalPorts, HashInsert188Api.Ports fallback) {
        if (capturedMemory == null) throw new NullPointerException("capturedMemory");
        if (terminalPorts == null) throw new NullPointerException("terminalPorts");
        if (fallback == null) throw new NullPointerException("fallback");

        final long SITE_RVA = 0xC39F88L;

        return new HashInsert188Api.Ports() {
            @Override
            public int equal3f6d2b0(HashInsert188Api.Memory m, long siteRva, long rcx, long rdx) {
                return fallback.equal3f6d2b0(m, siteRva, rcx, rdx);
            }

            @Override
            public void copy855f00(HashInsert188Api.Memory m, long siteRva, long rcx, long rdx) {
                fallback.copy855f00(m, siteRva, rcx, rdx);
            }

            @Override
            public void assign855db0(HashInsert188Api.Memory m, long siteRva, long rcx, long rdx, long r8) {
                fallback.assign855db0(m, siteRva, rcx, rdx, r8);
            }

            @Override
            public void rehashC3a400(HashInsert188Api.Memory m, long siteRva, long map) {
                fallback.rehashC3a400(m, siteRva, map);
            }

            @Override
            public void insertC3b960(HashInsert188Api.Memory m, long siteRva, long map, long result, int hash, long descriptor) {
                fallback.insertC3b960(m, siteRva, map, result, hash, descriptor);
            }

            @Override
            public void destroy856050(HashInsert188Api.Memory m, long siteRva, long descriptor) {
                fallback.destroy856050(m, siteRva, descriptor);
            }

            @Override
            public int capacity86e160(HashInsert188Api.Memory m, long siteRva, int ecx, int edx) {
                return fallback.capacity86e160(m, siteRva, ecx, edx);
            }

            @Override
            public void reserveC3b700(HashInsert188Api.Memory m, long siteRva, long map, int edx) {
                fallback.reserveC3b700(m, siteRva, map, edx);
            }

            @Override
            public void overflow86f210(HashInsert188Api.Memory m, long siteRva, long rcx, long rdx) {
                fallback.overflow86f210(m, siteRva, rcx, rdx);
            }

            @Override
            public void terminal4232cf4(HashInsert188Api.Memory m, long siteRva) {
                if (m != capturedMemory) {
                    throw new IllegalArgumentException("Foreign memory instance passed to terminal4232cf4");
                }
                if (siteRva != SITE_RVA) {
                    throw new IllegalArgumentException("Wrong site RVA passed to terminal4232cf4: " + Long.toHexString(siteRva));
                }
                Terminal207Api.Stop stop = Terminal4232CF4.trace(capturedMemory, terminalPorts, moduleBase);
                throw new UnsupportedOperationException("Terminal stop: " + stop);
            }
        };
    }
}