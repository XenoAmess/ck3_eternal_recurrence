package org.xar.ck3.control.g2.common.nativecore.task.captured;

/** Wires only the supplied static-object getter; all other typed callbacks and exceptions are forwarded unchanged. */
public final class StaticObjectB15000GrowthPorts implements SparseIntCells177Growth.Ports {
    private final long moduleBase;
    private final SparseIntCells177.Memory memory;
    private final StaticObjectB15000.Ports staticPorts;
    private final SparseIntCells177Growth.Ports other;

    public StaticObjectB15000GrowthPorts(long moduleBase, SparseIntCells177.Memory memory, StaticObjectB15000.Ports staticPorts, SparseIntCells177Growth.Ports other) {
        this.moduleBase = moduleBase;
        this.memory = memory;
        this.staticPorts = staticPorts;
        this.other = other;
    }

    @Override
    public long callVirtual8(SparseIntCells177Growth.KnownVirtual8 known) {
        return other.callVirtual8(known);
    }

    @Override
    public void callVirtual16(SparseIntCells177Growth.KnownVirtual16 known) {
        other.callVirtual16(known);
    }

    @Override
    public long callB15000() {
        return StaticObjectB15000.get(moduleBase, memory, staticPorts);
    }

    @Override
    public void call17836d0(SparseIntCells177Growth.Known17836d0 known) {
        other.call17836d0(known);
    }

    @Override
    public void call86f210(SparseIntCells177Growth.FrameAddress rcx, long rdx) {
        other.call86f210(rcx, rdx);
    }

    @Override
    public void call4232cf4() {
        other.call4232cf4();
    }
}
