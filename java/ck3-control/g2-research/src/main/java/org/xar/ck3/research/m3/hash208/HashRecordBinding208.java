package org.xar.ck3.research.m3.hash208;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.hash188.HashInsert188Api;
import org.xar.ck3.research.m3.record206.MapRecord86F210206;

/**
 * Source-only binding for HashInsert188Api.Ports.overflow86f210.
 * Binds only site 0xC39F83 with captured memory identity check before effects.
 * Delegates all other 9 callbacks exactly to the provided fallback.
 */
public final class HashRecordBinding208 {

    public static HashInsert188Api.Ports bind(HashInsert188Api.Memory capturedMemory, HashInsert188Api.Ports fallback) {
        if (capturedMemory == null) throw new NullPointerException("capturedMemory");
        if (fallback == null) throw new NullPointerException("fallback");

        final long SITE_RVA = 0xC39F83L;

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
                if (m != capturedMemory) {
                    throw new IllegalArgumentException("Foreign memory instance passed to overflow86f210");
                }
                if (siteRva != SITE_RVA) {
                    throw new IllegalArgumentException("Wrong site RVA passed to overflow86f210: " + Long.toHexString(siteRva));
                }
                // Call actual provided 206 record method. Discard long return as port is void.
                MapRecord86F210206.store(m, rcx, rdx);
            }

            @Override
            public void terminal4232cf4(HashInsert188Api.Memory m, long siteRva) {
                fallback.terminal4232cf4(m, siteRva);
            }
        };
    }
}