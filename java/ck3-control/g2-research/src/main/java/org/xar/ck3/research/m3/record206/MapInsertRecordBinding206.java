package org.xar.ck3.research.m3.record206;
import org.xar.ck3.research.m3.map191.MapInsert191Api;

public final class MapInsertRecordBinding206 {
    private MapInsertRecordBinding206() { }

    public static MapInsert191Api.Ports bind(MapInsert191Api.Memory memory, MapInsert191Api.Ports fallback) {
        return new MapInsert191Api.Ports() {
            @Override
            public int equal3f6d2b0(MapInsert191Api.Memory m, long siteRva, long rcx, long rdx) {
                return fallback.equal3f6d2b0(m, siteRva, rcx, rdx);
            }

            @Override
            public int equal3f6d2b0(MapInsert191Api.Memory m, long siteRva, long rcx, long rdx, long sourceEntryRsp) {
                return fallback.equal3f6d2b0(m, siteRva, rcx, rdx, sourceEntryRsp);
            }

            @Override
            public void insertSlotC3cf10(MapInsert191Api.Memory m, long siteRva, long bucket, int probe, int hash, long descriptor) {
                fallback.insertSlotC3cf10(m, siteRva, bucket, probe, hash, descriptor);
            }

            @Override
            public void rehashC3a400(MapInsert191Api.Memory m, long siteRva, long map) {
                fallback.rehashC3a400(m, siteRva, map);
            }

            @Override
            public void rehashC3a400(MapInsert191Api.Memory m, long siteRva, long map, long sourceEntryRsp) {
                fallback.rehashC3a400(m, siteRva, map, sourceEntryRsp);
            }

            @Override
            public void insertC3a5f0(MapInsert191Api.Memory m, long siteRva, long map, long result, int hash, long descriptor) {
                fallback.insertC3a5f0(m, siteRva, map, result, hash, descriptor);
            }

            @Override
            public void destroy856050(MapInsert191Api.Memory m, long siteRva, long descriptor) {
                fallback.destroy856050(m, siteRva, descriptor);
            }

            @Override
            public int capacity86e160(MapInsert191Api.Memory m, long siteRva, int ecx, int edx) {
                return fallback.capacity86e160(m, siteRva, ecx, edx);
            }

            @Override
            public void reserveC3b700(MapInsert191Api.Memory m, long siteRva, long map, int edx) {
                fallback.reserveC3b700(m, siteRva, map, edx);
            }

            @Override
            public void reserveC3b700(MapInsert191Api.Memory m, long siteRva, long map, int edx, long sourceEntryRsp) {
                fallback.reserveC3b700(m, siteRva, map, edx, sourceEntryRsp);
            }

            @Override
            public void overflow86f210(MapInsert191Api.Memory m, long siteRva, long rcx, long rdx) {
                if (m != memory) {
                    throw new IllegalArgumentException("callback memory mismatch");
                }
                if (siteRva != 0xC3BC83L) {
                    throw new IllegalArgumentException("unexpected siteRva");
                }
                MapRecord86F210206.store(m, rcx, rdx);
            }

            @Override
            public void terminal4232cf4(MapInsert191Api.Memory m, long siteRva) {
                fallback.terminal4232cf4(m, siteRva);
            }
        };
    }
}