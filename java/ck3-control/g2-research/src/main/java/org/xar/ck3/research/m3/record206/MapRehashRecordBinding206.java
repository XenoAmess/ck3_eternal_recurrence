package org.xar.ck3.research.m3.record206;
import org.xar.ck3.research.m3.MapRehashApi190;
import org.xar.ck3.research.m3.C3e150Api180;

public final class MapRehashRecordBinding206 {
    private MapRehashRecordBinding206() { }

    public static MapRehashApi190.Ports bind(MapRehashApi190.Memory memory, MapRehashApi190.Ports fallback) {
        return new MapRehashApi190.Ports() {
            @Override
            public long gs58(C3e150Api180.Memory m) {
                return fallback.gs58(m);
            }

            @Override
            public void call4223a84(C3e150Api180.Memory m, long guard) {
                fallback.call4223a84(m, guard);
            }

            @Override
            public void call4223a24(C3e150Api180.Memory m, long guard) {
                fallback.call4223a24(m, guard);
            }

            @Override
            public long allocatorSlot08(MapRehashApi190.Memory m, long code, long allocator, long bytes, int alignment) {
                return fallback.allocatorSlot08(m, code, allocator, bytes, alignment);
            }

            @Override
            public void allocatorSlot10(MapRehashApi190.Memory m, long code, long allocator, long block, int alignment) {
                fallback.allocatorSlot10(m, code, allocator, block, alignment);
            }

            @Override
            public void callc3b960(MapRehashApi190.Memory m, long map, long output, int hash, long descriptor, long flagAddress) {
                fallback.callc3b960(m, map, output, hash, descriptor, flagAddress);
            }

            @Override
            public void call856050(MapRehashApi190.Memory m, long descriptor) {
                fallback.call856050(m, descriptor);
            }

            @Override
            public void call86f210(MapRehashApi190.Memory m, long output, long map) {
                if (m != memory) {
                    throw new IllegalArgumentException("callback memory must be identical to captured memory");
                }
                MapRecord86F210206.store(m, output, map);
            }

            @Override
            public void call4232cf4(MapRehashApi190.Memory m) {
                fallback.call4232cf4(m);
            }

            @Override
            public void call4232cf4(MapRehashApi190.Memory m, long terminalEntryRsp) {
                fallback.call4232cf4(m, terminalEntryRsp);
            }
        };
    }
}