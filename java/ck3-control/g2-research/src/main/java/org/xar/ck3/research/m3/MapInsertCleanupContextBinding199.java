package org.xar.ck3.research.m3;

import org.xar.ck3.research.m3.map191.MapInsert191Api;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower61.Lower61Inputs;

public final class MapInsertCleanupContextBinding199 implements MapInsert191Api.Ports {
    public interface Memory extends MapInsert191Api.Memory, CleanupContext197Api.Memory { }

    private final long moduleBase;
    private final Memory capturedMemory;
    private final Lower61Inputs.Calls lowerCalls;
    private final MapInsert191Api.Ports delegate;

    private MapInsertCleanupContextBinding199(long moduleBase, Memory capturedMemory,
            Lower61Inputs.Calls lowerCalls, MapInsert191Api.Ports delegate) {
        this.moduleBase = moduleBase;
        this.capturedMemory = capturedMemory;
        this.lowerCalls = lowerCalls;
        this.delegate = delegate;
    }

    public static MapInsertCleanupContextBinding199 bind(long moduleBase, Memory capturedMemory,
            Lower61Inputs.Calls lowerCalls, MapInsert191Api.Ports delegate) {
        return new MapInsertCleanupContextBinding199(moduleBase, capturedMemory, lowerCalls, delegate);
    }

    @Override
    public int equal3f6d2b0(MapInsert191Api.Memory memory, long siteRva, long rcx, long rdx) {
        return delegate.equal3f6d2b0(memory, siteRva, rcx, rdx);
    }

    @Override
    public int equal3f6d2b0(MapInsert191Api.Memory memory, long siteRva, long rcx, long rdx, long sourceEntryRsp) {
        return delegate.equal3f6d2b0(memory, siteRva, rcx, rdx, sourceEntryRsp);
    }

    @Override
    public void insertSlotC3cf10(MapInsert191Api.Memory memory, long siteRva, long bucket, int probe, int hash, long descriptor) {
        delegate.insertSlotC3cf10(memory, siteRva, bucket, probe, hash, descriptor);
    }

    @Override
    public void rehashC3a400(MapInsert191Api.Memory memory, long siteRva, long map) {
        delegate.rehashC3a400(memory, siteRva, map);
    }

    @Override
    public void insertC3a5f0(MapInsert191Api.Memory memory, long siteRva, long map, long result, int hash, long descriptor) {
        delegate.insertC3a5f0(memory, siteRva, map, result, hash, descriptor);
    }

    @Override
    public void destroy856050(MapInsert191Api.Memory memory, long siteRva, long descriptor) {
        if (memory != capturedMemory) {
            throw new IllegalArgumentException("Identity mismatch");
        }
        if (siteRva != 0xC3BC15L && siteRva != 0xC3BBCAL) {
            throw new IllegalArgumentException("Invalid site");
        }
        CleanupContext197Api.Result result = CleanupContext197.execute(moduleBase, descriptor, capturedMemory, lowerCalls);
        if (result.completion() == CleanupContext197Api.Completion.UNSUPPORTED_ERROR_BRANCH) {
            throw new IllegalStateException("UNSUPPORTED_ERROR_BRANCH");
        }
    }

    @Override
    public int capacity86e160(MapInsert191Api.Memory memory, long siteRva, int ecx, int edx) {
        return delegate.capacity86e160(memory, siteRva, ecx, edx);
    }

    @Override
    public void reserveC3b700(MapInsert191Api.Memory memory, long siteRva, long map, int edx) {
        delegate.reserveC3b700(memory, siteRva, map, edx);
    }

    @Override
    public void reserveC3b700(MapInsert191Api.Memory memory, long siteRva, long map, int edx, long sourceEntryRsp) {
        delegate.reserveC3b700(memory, siteRva, map, edx, sourceEntryRsp);
    }

    @Override
    public void overflow86f210(MapInsert191Api.Memory memory, long siteRva, long rcx, long rdx) {
        delegate.overflow86f210(memory, siteRva, rcx, rdx);
    }

    @Override
    public void terminal4232cf4(MapInsert191Api.Memory memory, long siteRva) {
        delegate.terminal4232cf4(memory, siteRva);
    }
}