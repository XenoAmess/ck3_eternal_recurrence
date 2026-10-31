package org.xar.ck3.research.m3.hash209;

import org.xar.ck3.research.m3.CapacityIndex179;
import org.xar.ck3.research.m3.hash188.HashInsert188Api;

public final class HashCapacityBinding209 {

    public static HashInsert188Api.Ports bind(HashInsert188Api.Ports fallback) {
        return new HashInsert188Api.Ports() {
            @Override
            public int equal3f6d2b0(HashInsert188Api.Memory memory, long siteRva, long rcx, long rdx) {
                return fallback.equal3f6d2b0(memory, siteRva, rcx, rdx);
            }

            @Override
            public void copy855f00(HashInsert188Api.Memory memory, long siteRva, long rcx, long rdx) {
                fallback.copy855f00(memory, siteRva, rcx, rdx);
            }

            @Override
            public void assign855db0(HashInsert188Api.Memory memory, long siteRva, long rcx, long rdx, long r8) {
                fallback.assign855db0(memory, siteRva, rcx, rdx, r8);
            }

            @Override
            public void rehashC3a400(HashInsert188Api.Memory memory, long siteRva, long map) {
                fallback.rehashC3a400(memory, siteRva, map);
            }

            @Override
            public void insertC3b960(HashInsert188Api.Memory memory, long siteRva, long map, long result, int hash, long descriptor) {
                fallback.insertC3b960(memory, siteRva, map, result, hash, descriptor);
            }

            @Override
            public void destroy856050(HashInsert188Api.Memory memory, long siteRva, long descriptor) {
                fallback.destroy856050(memory, siteRva, descriptor);
            }

            @Override
            public int capacity86e160(HashInsert188Api.Memory memory, long siteRva, int ecx, int edx) {
                return CapacityIndex179.select(ecx, edx);
            }

            @Override
            public void reserveC3b700(HashInsert188Api.Memory memory, long siteRva, long map, int edx) {
                fallback.reserveC3b700(memory, siteRva, map, edx);
            }

            @Override
            public void overflow86f210(HashInsert188Api.Memory memory, long siteRva, long rcx, long rdx) {
                fallback.overflow86f210(memory, siteRva, rcx, rdx);
            }

            @Override
            public void terminal4232cf4(HashInsert188Api.Memory memory, long siteRva) {
                fallback.terminal4232cf4(memory, siteRva);
            }
        };
    }
}