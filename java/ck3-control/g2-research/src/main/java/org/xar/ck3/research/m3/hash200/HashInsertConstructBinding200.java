package org.xar.ck3.research.m3.hash200;

import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestConstruct855f00;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestE92780;
import org.xar.ck3.research.m3.hash188.HashInsert188Api;

public final class HashInsertConstructBinding200 {

    public interface Memory extends HashInsert188Api.Memory, RequestE92780.Memory {
    }

    public static HashInsert188Api.Ports bind(Memory memory, RequestConstruct855f00.Ports constructPorts, HashInsert188Api.Ports fallback) {
        if (memory == null) throw new NullPointerException("memory");
        if (constructPorts == null) throw new NullPointerException("constructPorts");
        if (fallback == null) throw new NullPointerException("fallback");

        final long SITE_RVA = 0xC39D27L;

        return new HashInsert188Api.Ports() {
            @Override
            public int equal3f6d2b0(HashInsert188Api.Memory m, long siteRva, long rcx, long rdx) {
                return fallback.equal3f6d2b0(m, siteRva, rcx, rdx);
            }

            @Override
            public void copy855f00(HashInsert188Api.Memory m, long siteRva, long rcx, long rdx) {
                if (m != memory) {
                    throw new IllegalArgumentException("Foreign memory instance passed to copy855f00");
                }
                if (siteRva != SITE_RVA) {
                    throw new IllegalArgumentException("Wrong site RVA passed to copy855f00: " + Long.toHexString(siteRva));
                }
                RequestConstruct855f00.construct(rcx, rdx, memory, constructPorts);
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
                fallback.terminal4232cf4(m, siteRva);
            }
        };
    }
}