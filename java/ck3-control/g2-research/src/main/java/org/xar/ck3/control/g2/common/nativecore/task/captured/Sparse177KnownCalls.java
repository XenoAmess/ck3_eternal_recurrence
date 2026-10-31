package org.xar.ck3.control.g2.common.nativecore.task.captured;

/** Known direct software edges only. Supplied memory and unresolved native-frame/external-call projections remain explicit. */
public final class Sparse177KnownCalls implements SparseIntCells177.Ports, SparseIntCells1783480.Ports, SparseIntCells17836d0.Ports {
    @FunctionalInterface public interface LocalPairCalls {
        SparseIntCells177.Raw128 call(SparseIntCells177.Known17836d0 known);
    }

    private final SparseIntCells177.Memory memory;
    private final SparseIntCells177Growth.Ports growthPorts;
    private final LocalPairCalls localPairCalls;

    public Sparse177KnownCalls(SparseIntCells177.Memory memory, SparseIntCells177Growth.Ports growthPorts, LocalPairCalls localPairCalls) {
        this.memory = memory;
        this.growthPorts = growthPorts;
        this.localPairCalls = localPairCalls;
    }

    @Override
    public void call177fbd0(long table) {
        SparseIntCells177Growth.apply(table, memory, growthPorts);
    }

    @Override
    public void call1783480(SparseIntCells177.Known1783480 known) {
        SparseIntCells1783480.put(known.rcx(), known.rdx(), known.r8d(), known.r9(), known.stack28(), memory, this);
    }

    @Override
    public SparseIntCells177.Raw128 call17836d0(SparseIntCells177.Known17836d0 known) {
        return localPairCalls.call(known);
    }

    @Override
    public void retry1783480(long table, long output, int rawHash, long keyAddress, long valueAddress) {
        SparseIntCells1783480.put(table, output, rawHash, keyAddress, valueAddress, memory, this);
    }

    @Override
    public void retry17836d0(long table, long output, int rawHash, long pairAddress) {
        SparseIntCells17836d0.put(table, output, rawHash, pairAddress, memory, this);
    }

    @Override
    public SparseIntCells177.Raw128 carry17836d0(long table, int rawHash, int key, int value) {
        SparseIntCells177.Known17836d0 known = new SparseIntCells177.Known17836d0(
            table,
            SparseIntCells177.FrameAddress.LOCAL_OUTPUT_RBP_MINUS10,
            rawHash,
            SparseIntCells177.FrameAddress.LOCAL_PAIR_RBP_MINUS1C,
            key,
            value
        );
        return localPairCalls.call(known);
    }
}
