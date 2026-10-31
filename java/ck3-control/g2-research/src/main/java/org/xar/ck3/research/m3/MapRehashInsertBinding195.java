package org.xar.ck3.research.m3;
import org.xar.ck3.research.m3.map191.MapInsert191Api;
import org.xar.ck3.research.m3.map191.MapInsertC3B960;

public final class MapRehashInsertBinding195 implements MapRehashApi190.Ports {
    public interface SharedMemory extends MapRehashApi190.Memory, MapInsert191Api.Memory { }

    private final long moduleBase;
    private final MapRehashApi190.Ports delegate;
    private final MapInsert191Api.Ports insertPorts;

    public MapRehashInsertBinding195(long moduleBase, MapRehashApi190.Ports delegate,
                                    MapInsert191Api.Ports insertPorts) {
        this.moduleBase = moduleBase;
        this.delegate = delegate;
        this.insertPorts = insertPorts;
    }

    public long gs58(C3e150Api180.Memory memory) {
        return delegate.gs58(memory);
    }

    public void call4223a84(C3e150Api180.Memory memory, long guard) {
        delegate.call4223a84(memory, guard);
    }

    public void call4223a24(C3e150Api180.Memory memory, long guard) {
        delegate.call4223a24(memory, guard);
    }

    public long allocatorSlot08(MapRehashApi190.Memory memory, long code, long allocator,
                                long bytes, int alignment) {
        return delegate.allocatorSlot08(memory, code, allocator, bytes, alignment);
    }

    public void allocatorSlot10(MapRehashApi190.Memory memory, long code, long allocator,
                                long block, int alignment) {
        delegate.allocatorSlot10(memory, code, allocator, block, alignment);
    }

    public void callc3b960(MapRehashApi190.Memory memory, long map, long output,
                          int hash, long descriptor, long flagAddress) {
        if (!(memory instanceof SharedMemory)) {
            throw new IllegalArgumentException("SharedMemory required");
        }
        SharedMemory shared = (SharedMemory) memory;
        long bodyRsp = output - 0xE0L;
        MapInsert191Api.Scratch scratch = new MapInsert191Api.Scratch(bodyRsp);
        MapInsert191Api.Input input = new MapInsert191Api.Input(
            moduleBase, map, output, hash, descriptor, scratch
        );
        MapInsertC3B960.execute(input, shared, insertPorts);
    }

    public void call856050(MapRehashApi190.Memory memory, long descriptor) {
        delegate.call856050(memory, descriptor);
    }

    public void call86f210(MapRehashApi190.Memory memory, long output, long map) {
        delegate.call86f210(memory, output, map);
    }

    public void call4232cf4(MapRehashApi190.Memory memory) {
        delegate.call4232cf4(memory);
    }
}