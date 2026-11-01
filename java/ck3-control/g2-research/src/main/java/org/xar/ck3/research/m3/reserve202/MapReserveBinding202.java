package org.xar.ck3.research.m3.reserve202;

import org.xar.ck3.research.m3.map191.MapInsert191Api;
import org.xar.ck3.research.m3.MapRehashApi190;
import org.xar.ck3.research.m3.MapRehash190;

public final class MapReserveBinding202 {
    private MapReserveBinding202() { }

    public interface Memory extends MapInsert191Api.Memory, MapRehashApi190.Memory { }

    public static MapInsert191Api.Ports bind(Memory memory, long moduleBase, MapRehashApi190.Ports rehashPorts, MapInsert191Api.Ports fallback) {
        if (memory == null) throw new NullPointerException("memory");
        if (rehashPorts == null) throw new NullPointerException("rehashPorts");
        if (fallback == null) throw new NullPointerException("fallback");

        final Memory capturedMemory = memory;

        return new MapInsert191Api.Ports() {
            @Override
            public int equal3f6d2b0(MapInsert191Api.Memory memory, long siteRva, long rcx, long rdx) {
                return fallback.equal3f6d2b0(memory, siteRva, rcx, rdx);
            }

            @Override
            public int equal3f6d2b0(MapInsert191Api.Memory memory, long siteRva, long rcx, long rdx, long sourceEntryRsp) {
                return fallback.equal3f6d2b0(memory, siteRva, rcx, rdx, sourceEntryRsp);
            }

            @Override
            public void insertSlotC3cf10(MapInsert191Api.Memory memory, long siteRva, long bucket, int probe, int hash, long descriptor) {
                fallback.insertSlotC3cf10(memory, siteRva, bucket, probe, hash, descriptor);
            }

            @Override
            public void rehashC3a400(MapInsert191Api.Memory memory, long siteRva, long map) {
                fallback.rehashC3a400(memory, siteRva, map);
            }

            @Override
            public void rehashC3a400(MapInsert191Api.Memory memory, long siteRva, long map, long sourceEntryRsp) {
                fallback.rehashC3a400(memory, siteRva, map, sourceEntryRsp);
            }

            @Override
            public void insertC3a5f0(MapInsert191Api.Memory memory, long siteRva, long map, long result, int hash, long descriptor) {
                fallback.insertC3a5f0(memory, siteRva, map, result, hash, descriptor);
            }

            @Override
            public void destroy856050(MapInsert191Api.Memory memory, long siteRva, long descriptor) {
                fallback.destroy856050(memory, siteRva, descriptor);
            }

            @Override
            public int capacity86e160(MapInsert191Api.Memory memory, long siteRva, int ecx, int edx) {
                return fallback.capacity86e160(memory, siteRva, ecx, edx);
            }

            @Override
            public void reserveC3b700(MapInsert191Api.Memory memory, long siteRva, long map, int edx) {
                fallback.reserveC3b700(memory, siteRva, map, edx);
            }

            @Override
            public void reserveC3b700(MapInsert191Api.Memory memory, long siteRva, long map, int edx, long sourceEntryRsp) {
                if (memory != capturedMemory) {
                    throw new IllegalArgumentException("foreign Memory");
                }
                if (siteRva != 0xC3BC3EL) {
                    throw new IllegalArgumentException("invalid site");
                }
                MapRehash190.rehash(capturedMemory, rehashPorts, moduleBase, map, edx, new MapRehashApi190.Scratch(sourceEntryRsp));
            }

            @Override
            public void overflow86f210(MapInsert191Api.Memory memory, long siteRva, long rcx, long rdx) {
                fallback.overflow86f210(memory, siteRva, rcx, rdx);
            }

            @Override
            public void terminal4232cf4(MapInsert191Api.Memory memory, long siteRva) {
                fallback.terminal4232cf4(memory, siteRva);
            }

            @Override
            public void terminal4232cf4(MapInsert191Api.Memory memory, long siteRva, long terminalEntryRsp) {
                fallback.terminal4232cf4(memory, siteRva, terminalEntryRsp);
            }
        };
    }
}