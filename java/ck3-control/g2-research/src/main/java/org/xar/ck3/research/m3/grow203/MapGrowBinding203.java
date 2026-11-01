package org.xar.ck3.research.m3.grow203;

import org.xar.ck3.research.m3.map191.MapInsert191Api;
import org.xar.ck3.research.m3.MapRehashApi190;
import org.xar.ck3.research.m3.MapRehash190;

public final class MapGrowBinding203 {

    public interface Memory extends MapInsert191Api.Memory, MapRehashApi190.Memory {
    }

    public static MapInsert191Api.Ports bind(Memory memory, long moduleBase, MapRehashApi190.Ports growPorts, MapInsert191Api.Ports fallback) {
        return new MapInsert191Api.Ports() {
            @Override
            public int equal3f6d2b0(MapInsert191Api.Memory mem, long siteRva, long rcx, long rdx) {
                return fallback.equal3f6d2b0(mem, siteRva, rcx, rdx);
            }

            @Override
            public int equal3f6d2b0(MapInsert191Api.Memory mem, long siteRva, long rcx, long rdx, long sourceEntryRsp) {
                return fallback.equal3f6d2b0(mem, siteRva, rcx, rdx, sourceEntryRsp);
            }

            @Override
            public void insertSlotC3cf10(MapInsert191Api.Memory mem, long siteRva, long bucket, int probe, int hash, long descriptor) {
                fallback.insertSlotC3cf10(mem, siteRva, bucket, probe, hash, descriptor);
            }

            @Override
            public void rehashC3a400(MapInsert191Api.Memory mem, long siteRva, long map) {
                fallback.rehashC3a400(mem, siteRva, map);
            }

            @Override
            public void rehashC3a400(MapInsert191Api.Memory mem, long siteRva, long map, long sourceEntryRsp) {
                if (mem != memory) {
                    throw new IllegalArgumentException("Memory mismatch");
                }
                if (siteRva != 0xC3BBADL) {
                    throw new IllegalArgumentException("Site mismatch");
                }
                MapRehashApi190.Scratch scratch = new MapRehashApi190.Scratch(sourceEntryRsp);
                MapRehashApi190.Completion completion = MapRehash190.grow(memory, growPorts, moduleBase, map, scratch);
                if (completion == MapRehashApi190.Completion.UNSUPPORTED_INT3_AFTER_ERROR_CALLS_RETURNED) {
                    throw new UnsupportedOperationException("C3A43B INT3: the two real error calls have returned and the source next traps.");
                }
            }

            @Override
            public void insertC3a5f0(MapInsert191Api.Memory mem, long siteRva, long map, long result, int hash, long descriptor) {
                fallback.insertC3a5f0(mem, siteRva, map, result, hash, descriptor);
            }

            @Override
            public void destroy856050(MapInsert191Api.Memory mem, long siteRva, long descriptor) {
                fallback.destroy856050(mem, siteRva, descriptor);
            }

            @Override
            public int capacity86e160(MapInsert191Api.Memory mem, long siteRva, int ecx, int edx) {
                return fallback.capacity86e160(mem, siteRva, ecx, edx);
            }

            @Override
            public void reserveC3b700(MapInsert191Api.Memory mem, long siteRva, long map, int edx) {
                fallback.reserveC3b700(mem, siteRva, map, edx);
            }

            @Override
            public void reserveC3b700(MapInsert191Api.Memory mem, long siteRva, long map, int edx, long sourceEntryRsp) {
                fallback.reserveC3b700(mem, siteRva, map, edx, sourceEntryRsp);
            }

            @Override
            public void overflow86f210(MapInsert191Api.Memory mem, long siteRva, long rcx, long rdx) {
                fallback.overflow86f210(mem, siteRva, rcx, rdx);
            }

            @Override
            public void terminal4232cf4(MapInsert191Api.Memory mem, long siteRva) {
                fallback.terminal4232cf4(mem, siteRva);
            }

            @Override
            public void terminal4232cf4(MapInsert191Api.Memory mem, long siteRva, long terminalEntryRsp) {
                fallback.terminal4232cf4(mem, siteRva, terminalEntryRsp);
            }
        };
    }
}