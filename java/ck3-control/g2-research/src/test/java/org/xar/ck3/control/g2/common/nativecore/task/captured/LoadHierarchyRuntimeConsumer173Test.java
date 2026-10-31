package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.ArrayDeque;
import java.util.OptionalLong;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

/** Newly assembled actual three-callee paths over strictly supplied literal reads. */
public final class LoadHierarchyRuntimeConsumer173Test {
    private static final long B = 0x100000000L;
    private static final long COL = B + 0x3000L;
    private static final long OBJECT = B + 0x10000L;
    private static final long COMPLETE = B + 0xFF00L;
    private static final long TARGET = B + 0x400L;
    private static final long SOURCE = B + 0x500L;
    private static final long DT = B + 0x1000L;
    private static final long DS = B - 0x1000L;
    private record Read(int width, long address, long value) { }

    private static final class Fixture implements LoadHierarchySearch173.Memory {
        private final ArrayDeque<Read> reads = new ArrayDeque<>();
        private Fixture d(long address, int value) { reads.add(new Read(32, address, value)); return this; }
        private Fixture b(long address, int value) { reads.add(new Read(8, address, value)); return this; }
        private Fixture q(long address, long value) { reads.add(new Read(64, address, value)); return this; }
        private long read(int width, long address) {
            Read r = reads.remove();
            assertEquals(r.width(), width, "read width");
            assertEquals(r.address(), address, "read address");
            return r.value();
        }
        @Override public long readPointer(long address) { return read(64, address); }
        @Override public int readInt32(long address) { return (int) read(32, address); }
        @Override public int readUnsigned8(long address) { return (int) read(8, address); }
        @Override public void writeInt32(long address, int value) { throw new AssertionError("write32"); }
        @Override public void writeInt64(long address, long value) { throw new AssertionError("write64"); }
        private void done() { assertEquals(0, reads.size(), "unconsumed literal reads"); }
    }

    private static Fixture runtimePrefix(int flags) {
        return new Fixture().q(OBJECT, B + 0x2000L).q(B + 0x1FF8L, COL)
                .d(COL + 4L, 0x100).d(COL + 8L, 0).d(OBJECT, 0x2000)
                .d(COL, 1).d(COL + 0x14L, 0x3000).d(COL + 0x10L, 0x100)
                .d(B + 0x104L, flags);
    }

    private static Fixture header(Fixture f) {
        return f.d(COL + 0x10L, 0x100).d(B + 0x10CL, 0x200).d(B + 0x108L, 2);
    }

    private static Fixture hierarchy968(Fixture f, int sourceFlags) {
        return header(f).d(B + 0x200L, 0x1000).d(DT, 0x400).d(DT + 4L, 1)
                .d(DT, 0x400).b(TARGET + 0x10L, 'T').b(SOURCE + 0x10L, 'S')
                .d(B + 0x204L, -0x1000).d(DS, 0x500)
                .d(DS + 0xCL, -1).d(DS + 8L, -7)
                .b(DT + 0x14L, 0).b(DS + 0x14L, sourceFlags);
    }

    private static long execute(Fixture memory) {
        LoadRuntime4260e74.Ports ports = LoadHierarchyRuntimeConsumer.ports(memory,
                (pc, slot) -> { throw new AssertionError("nonlegacy path invoked Windows API"); });
        return LoadRuntime4260e74.execute(B, OBJECT, 0x107, SOURCE, TARGET, 0, memory, ports);
    }

    @Test public void allThreeActualCalleesReturnDescriptorThenFinalSignedPmd() {
        Fixture af0 = header(runtimePrefix(0))
                .d(B + 0x200L, 0x1000).d(DT, 0x400)
                .d(B + 0x204L, -0x1000).b(DS + 0x14L, 0).d(DS, 0x500)
                .d(DT + 0xCL, -1).d(DT + 8L, -11);
        assertEquals(B + 0xFEF5L, execute(af0));
        af0.done();
        Fixture f968 = hierarchy968(runtimePrefix(1), 0)
                .d(DT + 0xCL, -1).d(DT + 8L, -11);
        assertEquals(B + 0xFEF5L, execute(f968));
        f968.done();
        Fixture c28 = header(runtimePrefix(3))
                .d(B + 0x200L, 0x1000).d(DT, 0x400).b(DT + 0x14L, 0).d(DT + 4L, 1)
                .d(DT, 0x400).b(TARGET + 0x10L, 'T').b(SOURCE + 0x10L, 'S')
                .d(B + 0x204L, -0x1000).d(DS, 0x500).d(DS + 0xCL, -1).d(DS + 8L, -7)
                .b(DT + 0x14L, 0).b(DS + 0x14L, 0)
                .d(DT + 0xCL, -1).d(DT + 8L, -11)
                .d(DT + 0xCL, -1).d(DT + 8L, -11);
        assertEquals(B + 0xFEF5L, execute(c28));
        c28.done();
    }

    @Test public void actual968RejectionReturnsZeroWithoutFinalPmdOrOtherRoute() {
        Fixture rejected = hierarchy968(runtimePrefix(1), 1);
        assertEquals(0L, execute(rejected));
        rejected.done();
    }

    @Test public void sourceVirtualPmdUsesTwoCReadsFullPointerThenSignedCorrection() {
        Fixture f = header(new Fixture())
                .d(B + 0x200L, 0x1000).d(DT, 0x400).b(DT + 0x14L, 0).d(DT + 4L, 1)
                .d(DT, 0x400).b(TARGET + 0x10L, 'T').b(SOURCE + 0x10L, 'S')
                .d(B + 0x204L, -0x1000).d(DS, 0x500)
                .d(DS + 0xCL, 8).d(DS + 0xCL, 8).d(DS + 0x10L, -4)
                .q(COMPLETE + 8L, B + 0x9000L).d(B + 0x8FFCL, -12).d(DS + 8L, -3)
                .b(DT + 0x14L, 0).b(DS + 0x14L, 0).d(DT + 0xCL, -1).d(DT + 8L, -11);
        LoadRuntime4260e74.SearchCall call = new LoadRuntime4260e74.SearchCall(
                COMPLETE, COL, SOURCE, -7L, 0L, OptionalLong.of(TARGET), OptionalLong.of(B));
        assertEquals(DT, LoadHierarchySearch173.findC28(call, f));
        f.done();
    }
}
