package org.xar.ck3.research.m3;

import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower61.Lower61Inputs;

public final class MapRehashCleanupContextBinding199 implements MapRehashApi190.Ports {
    public interface Memory extends MapRehashApi190.Memory, CleanupContext197Api.Memory { }

    private final long moduleBase;
    private final Memory capturedMemory;
    private final Lower61Inputs.Calls lowerCalls;
    private final MapRehashApi190.Ports delegate;

    private MapRehashCleanupContextBinding199(long moduleBase, Memory capturedMemory,
            Lower61Inputs.Calls lowerCalls, MapRehashApi190.Ports delegate) {
        this.moduleBase = moduleBase;
        this.capturedMemory = capturedMemory;
        this.lowerCalls = lowerCalls;
        this.delegate = delegate;
    }

    public static MapRehashCleanupContextBinding199 bind(long moduleBase, Memory capturedMemory,
            Lower61Inputs.Calls lowerCalls, MapRehashApi190.Ports delegate) {
        return new MapRehashCleanupContextBinding199(moduleBase, capturedMemory, lowerCalls, delegate);
    }

    @Override
    public long gs58(C3e150Api180.Memory memory) {
        return delegate.gs58(memory);
    }

    @Override
    public void call4223a84(C3e150Api180.Memory memory, long guard) {
        delegate.call4223a84(memory, guard);
    }

    @Override
    public void call4223a24(C3e150Api180.Memory memory, long guard) {
        delegate.call4223a24(memory, guard);
    }

    @Override
    public long allocatorSlot08(MapRehashApi190.Memory memory, long code, long allocator, long bytes, int alignment) {
        return delegate.allocatorSlot08(memory, code, allocator, bytes, alignment);
    }

    @Override
    public void allocatorSlot10(MapRehashApi190.Memory memory, long code, long allocator, long block, int alignment) {
        delegate.allocatorSlot10(memory, code, allocator, block, alignment);
    }

    @Override
    public void callc3b960(MapRehashApi190.Memory memory, long map, long output, int hash, long descriptor, long flagAddress) {
        delegate.callc3b960(memory, map, output, hash, descriptor, flagAddress);
    }

    @Override
    public void call856050(MapRehashApi190.Memory memory, long descriptor) {
        if (memory != capturedMemory) {
            throw new IllegalArgumentException("Memory identity mismatch");
        }
        CleanupContext197Api.Result result = CleanupContext197.execute(moduleBase, descriptor, capturedMemory, lowerCalls);
        if (result.completion() == CleanupContext197Api.Completion.UNSUPPORTED_ERROR_BRANCH) {
            throw new IllegalStateException("UNSUPPORTED_ERROR_BRANCH");
        }
    }

    @Override
    public void call86f210(MapRehashApi190.Memory memory, long output, long map) {
        delegate.call86f210(memory, output, map);
    }

    @Override
    public void call4232cf4(MapRehashApi190.Memory memory) {
        delegate.call4232cf4(memory);
    }
}