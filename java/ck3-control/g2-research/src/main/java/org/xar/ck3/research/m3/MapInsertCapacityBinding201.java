package org.xar.ck3.research.m3;
import org.xar.ck3.research.m3.map191.MapInsert191Api;

public final class MapInsertCapacityBinding201 implements MapInsert191Api.Ports {
    private final MapInsert191Api.Ports delegate;

    private MapInsertCapacityBinding201(MapInsert191Api.Ports delegate) {
        this.delegate = delegate;
    }

    public static MapInsertCapacityBinding201 bind(MapInsert191Api.Ports delegate) {
        return new MapInsertCapacityBinding201(delegate);
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
        delegate.destroy856050(memory, siteRva, descriptor);
    }

    @Override
    public int capacity86e160(MapInsert191Api.Memory memory, long siteRva, int ecx, int edx) {
        return CapacityIndex179.select(ecx, edx);
    }

    @Override
    public void reserveC3b700(MapInsert191Api.Memory memory, long siteRva, long map, int edx) {
        delegate.reserveC3b700(memory, siteRva, map, edx);
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